#!/usr/bin/env python3
"""numbers_check.py — 官網影響力數字的位置表、基線與黑數檢查（部署前閘門）。

依據：_source/SOP-數據更新與部署索引.md 第二節。
2026-09-06 依 Codex 盲審 C-01～C-04 加固（報告：_source/審查_Codex盲審_數據SOP_20260906.md）。

做六件事：
  1. 真源自檢：欄位齊全、id 不重複、`value` 與 `display` 對得上（近似值要明寫
     `display_approx`）、`status` 合法；`draft` 指標不得出現在頁面上。
  2. 掃 public/**/*.html ＋ llms.txt ＋ humans.txt，列出每個 data-metric 標記的
     檔案:行號與顯示值，與 numbers.json 的 `display`（或 data-metric-field 指定的
     欄位）比對。
  3. 位置基線：比對 `_source/numbers_manifest.json`——標記整個被刪、卡片被刪、
     數量變少、id 從未上站，都要報錯（C-01：沒有基線就等於「刪掉就沒事」）。
  4. 黑數掃描：把已知數值正規化成別名表（逗號／全形／萬千量級／約逾超過近／
     `previous_values` 殘留舊值），未標記處出現＝黑數。
  5. 黑數 allowlist 綁「檔案＋id＋筆數＋每處語境雜湊」，同檔換位置或換句子都要
     重新核准（C-04）。
  6. 任一不符 → exit 1，擋住部署。

用法：
    python3 _source/deploy-automation/numbers_check.py
    python3 _source/deploy-automation/numbers_check.py --report _source/數字位置表_20260906.md
    python3 _source/deploy-automation/numbers_check.py --check-report _source/數字位置表_20260906.md
    python3 _source/deploy-automation/numbers_check.py --update-allowlist   # 人工覆核後才跑
    python3 _source/deploy-automation/numbers_check.py --update-manifest    # 人工覆核後才跑
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_NUMBERS = REPO / "_source" / "numbers.json"
DEFAULT_ALLOWLIST = REPO / "_source" / "numbers_allowlist.json"
DEFAULT_MANIFEST = REPO / "_source" / "numbers_manifest.json"
DEFAULT_ROOT = REPO / "public"
EXTRA_TEXT_FILES = ("llms.txt", "humans.txt")

REQUIRED_FIELDS = ("id", "value", "display", "unit", "label", "period", "method",
                   "source", "last_verified", "cadence", "owner", "status")
VALID_STATUS = ("approved", "provisional", "draft")
FIELD_KEYS = ("display", "value", "unit", "label", "period", "method", "source",
              "last_verified")

# 這些區塊裡的數字不是給人看的內容（樣式、腳本、向量圖、註解），不掃
_BLANK_BLOCKS = re.compile(
    r"<style\b[^>]*>.*?</style>"
    r"|<svg\b[^>]*>.*?</svg>"
    r"|<!--.*?-->"
    r"|<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>",
    re.S | re.I,
)
_TAG = re.compile(r"<[^>]*>", re.S)
_META_CONTENT = re.compile(r'^<meta\b[^>]*\bcontent=(?:"([^"]*)"|\'([^\']*)\')', re.S | re.I)
# 屬性可用單引號或雙引號、順序不拘（縱深建議 1）
_OPEN_WITH_METRIC = re.compile(
    r'<(?P<tag>[a-zA-Z][\w-]*)\b[^>]*?\bdata-metric=(?:"(?P<id>[^"]+)"|\'(?P<id2>[^\']+)\')[^>]*>')
_METRIC_FIELD = re.compile(r'\bdata-metric-field=(?:"([^"]+)"|\'([^\']+)\')', re.I)

# 全形數字／逗號／加號 → 半形（1:1 對應，位移不變）
_WIDE = {ord(c): ord(h) for c, h in zip("０１２３４５６７８９，＋", "0123456789,+")}

# 別名表：近似前綴（黑數常見寫法，C-03）
APPROX_PREFIXES = ("約", "逾", "超過", "破", "近", "達", "上看", "已達")


# ── 資料結構 ────────────────────────────────────────────────
@dataclass
class Marked:
    metric_id: str
    shown: str
    line: int
    start: int
    end: int
    field_key: str = "display"


@dataclass
class Row:
    metric_id: str
    location: str       # 檔案:行號
    shown: str
    kind: str           # marked / prose
    ok: bool
    note: str = ""
    context: str = ""   # prose 專用：語境雜湊（C-04）
    field_key: str = "display"


@dataclass
class Result:
    rows: list[Row] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


# ── 文字抽取 ────────────────────────────────────────────────
def _blank(match: re.Match) -> str:
    """把整段換成等長空白（保留換行），行號才不會位移。"""
    return re.sub(r"[^\n]", " ", match.group(0))


def condense(src: str, mask: Iterable[tuple[int, int]] = ()) -> tuple[str, list[int]]:
    """回傳 (可讀文字, 每個字元在原始碼中的位移)。

    標籤本身被丟掉，讓 `168<span>+</span>` 併回 `168+`；<meta> 的 content 會被
    留下來（meta description 也是對外文案）；mask 內的區間（已標記的數字）挖空，
    才不會被自己的黑數掃描抓到。全形數字／逗號／加號逐字轉半形（1:1，位移不變）。
    """
    s = _BLANK_BLOCKS.sub(_blank, src)
    masked = [(a, b) for a, b in mask]
    out: list[str] = []
    pos: list[int] = []
    i, n = 0, len(s)
    while i < n:
        skip = next((b for a, b in masked if a <= i < b), None)
        if skip is not None:
            i = skip
            continue
        if s[i] == "<":
            m = _TAG.match(s, i)
            if m:
                mc = _META_CONTENT.match(m.group(0))
                if mc:
                    group = 1 if mc.group(1) is not None else 2
                    base = i + mc.start(group)
                    for j, ch in enumerate(mc.group(group)):
                        out.append(ch.translate(_WIDE))
                        pos.append(base + j)
                    out.append(" ")
                    pos.append(i)
                i = m.end()
                continue
        out.append(s[i].translate(_WIDE))
        pos.append(i)
        i += 1
    return "".join(out), pos


def _line_starts(src: str) -> list[int]:
    starts = [0]
    for m in re.finditer("\n", src):
        starts.append(m.end())
    return starts


def _line_of(starts: list[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def _strip_tags(html: str) -> str:
    return re.sub(r"\s+", "", _TAG.sub("", html)).translate(_WIDE)


def find_marked(src: str) -> list[Marked]:
    """找出所有 data-metric 標記，回傳 id、顯示文字（去標籤去空白）、行號與內文區間。"""
    starts = _line_starts(src)
    found: list[Marked] = []
    for m in _OPEN_WITH_METRIC.finditer(src):
        tag = m.group("tag")
        metric_id = m.group("id") or m.group("id2")
        fm = _METRIC_FIELD.search(m.group(0))
        field_key = (fm.group(1) or fm.group(2)) if fm else "display"
        closer = re.compile(r"</?" + re.escape(tag) + r"\b[^>]*>", re.I)
        depth, cursor, inner_end = 1, m.end(), None
        while depth:
            t = closer.search(src, cursor)
            if not t:
                break
            if t.group(0).startswith("</"):
                depth -= 1
                if depth == 0:
                    inner_end = t.start()
            elif not t.group(0).endswith("/>"):
                depth += 1
            cursor = t.end()
        if inner_end is None:
            raise ValueError(f'data-metric="{metric_id}" 的 <{tag}> 缺少收尾標籤')
        found.append(Marked(
            metric_id=metric_id,
            shown=_strip_tags(src[m.end():inner_end]),
            line=_line_of(starts, m.start()),
            start=m.end(),
            end=inner_end,
            field_key=field_key,
        ))
    return found


# ── 別名表（C-03）────────────────────────────────────────────
def _comma(v: int) -> str:
    return f"{v:,}"


def _magnitude_forms(v: int) -> list[str]:
    """量級寫法：66247 → 6.6萬／6萬／7萬；3017 → 3.0千／3千。"""
    forms: list[str] = []
    for div, word in ((10000, "萬"), (1000, "千")):
        if v < div:
            continue
        q = v / div
        if q >= 1000:                     # 6 萬寫成 66.2 千沒人用，跳過
            continue
        # 留一個空白：`_pattern_regex` 會把它放寬成「可有可無的空白」，
        # 這樣「6.6萬份」與「6.6 萬份」兩種寫法都抓得到。
        cands = {f"{q:.1f}".rstrip("0").rstrip(".") + " " + word,
                 f"{int(q)} {word}", f"{round(q)} {word}"}
        forms += sorted(cands)
    return forms


def alias_patterns(metric: dict) -> list[tuple[str, bool, str]]:
    """回傳 [(字串, 是否需要接單位, 說明)]。

    需要接單位的（量級寫法、四捨五入的整數寫法）才不會把日期、金額誤判成黑數；
    帶逗號的完整數值（≥1,000）本身夠獨特，不必接單位。
    """
    out: list[tuple[str, bool, str]] = []
    value = int(metric["value"])
    exact = {_comma(value), str(value)}
    display_base = re.sub(r"[^0-9,]", "", str(metric["display"]))
    if display_base:
        exact.add(display_base)
        exact.add(display_base.replace(",", ""))

    for s in sorted(exact):
        strong = "," in s or int(s.replace(",", "") or 0) >= 1000
        out.append((s, not strong, "完整數值"))
    for s in _magnitude_forms(value):
        out.append((s, True, "量級寫法"))

    # 人工補充（numbers.json 的 scan_patterns，例「約 66,000」這類四捨五入）
    for s in metric.get("scan_patterns", []):
        out.append((s, False, "人工登記寫法"))

    # 殘留舊值（縱深建議 3）：改過的數字若舊值還留在頁面上，要抓得到
    for old in metric.get("previous_values", []):
        ov = int(old["value"])
        for s in sorted({_comma(ov), str(ov)}):
            strong = "," in s or ov >= 1000
            out.append((s, not strong, f"殘留舊值（{old.get('note', '已更新')}）"))
        for s in _magnitude_forms(ov):
            out.append((s, True, "殘留舊值量級寫法"))

    # 近似前綴 × 完整數值
    for prefix in APPROX_PREFIXES:
        for s in sorted(exact):
            out.append((prefix + s, False, "近似前綴"))

    seen: set[str] = set()
    uniq: list[tuple[str, bool, str]] = []
    for s, need_unit, why in out:
        key = f"{s}|{need_unit}"
        if key in seen:
            continue
        seen.add(key)
        uniq.append((s, need_unit, why))
    return uniq


def _pattern_regex(pattern: str, units: list[str] | None = None) -> re.Pattern:
    """字串裡的空白放寬成任意空白（HTML 常被換行切開）；前後不得再接數字。

    units 有值時，數字後面必須接其中一個單位詞（可有空白），才算命中。
    """
    body = r"\s*".join(re.escape(part) for part in pattern.split())
    tail = ""
    if units:
        tail = r"\s*(?:" + "|".join(re.escape(u) for u in units) + r")"
    return re.compile(r"(?<![0-9])" + body + tail + r"(?![0-9])")


_RANGE_DASH = "-–—~～〜"


def in_numeric_range(text: str, start: int, end: int) -> bool:
    """命中字串是數值區間的一端（例「3,000-8,000 字」）就不算黑數。

    區間是「多少到多少」的敘述，不是在報這個指標的值；當成黑數會逼人把
    無關句子登記進 allowlist，反而稀釋登記表的意義。
    """
    after = text[end:end + 12]
    m = re.match(r"\s*[" + _RANGE_DASH + r"]\s*[0-9]", after)
    if m:
        return True
    before = text[max(0, start - 12):start]
    return bool(re.search(r"[0-9][0-9,]*\s*[" + _RANGE_DASH + r"]\s*$", before))


def metric_units(metric: dict) -> list[str]:
    units = [metric["unit"]] + list(metric.get("unit_aliases", []))
    return sorted(set(units), key=len, reverse=True)


# ── 掃描 ────────────────────────────────────────────────────
def iter_files(root: Path) -> list[Path]:
    files = sorted(p for p in root.rglob("*.html") if p.is_file())
    files += [root / name for name in EXTRA_TEXT_FILES if (root / name).exists()]
    return files


_SENT_BOUND = "。！？；!?;\n"


def context_hash(text: str, start: int, end: int, window: int = 60) -> str:
    """語境雜湊：命中字串所在的那一句（去空白）的短雜湊。

    同檔案裡把一處合格文案刪掉、另一處新增同值宣稱，筆數不變但雜湊會變——
    C-04 就是這個漏洞。取「整句」而不是固定字數視窗：前後段落增刪不該吵，
    句子本身被改寫（換單位、換語境）才要重新核准。
    """
    left = start
    while left > 0 and start - left < window and text[left - 1] not in _SENT_BOUND:
        left -= 1
    right = end
    while right < len(text) and right - end < window and text[right] not in _SENT_BOUND:
        right += 1
    sentence = re.sub(r"\s+", "", text[left:right])
    return hashlib.sha1(sentence.encode("utf-8")).hexdigest()[:10]


def scan_file(path: Path, rel: str, metrics: dict) -> tuple[list[Row], list[str]]:
    src = path.read_text(encoding="utf-8")
    starts = _line_starts(src)
    rows: list[Row] = []
    problems: list[str] = []

    marked = find_marked(src) if path.suffix == ".html" else []
    for mk in marked:
        loc = f"{rel}:{mk.line}"
        metric = metrics.get(mk.metric_id)
        if metric is None:
            problems.append(f"{loc} 用了 numbers.json 沒有的 id：{mk.metric_id}")
            rows.append(Row(mk.metric_id, loc, mk.shown, "marked", False, "id 不存在於真源"))
            continue
        if mk.field_key not in FIELD_KEYS:
            problems.append(f"{loc} data-metric-field=\"{mk.field_key}\" 不是可投影欄位"
                            f"（可用：{'、'.join(FIELD_KEYS)}）")
            rows.append(Row(mk.metric_id, loc, mk.shown, "marked", False, "欄位名不合法",
                            field_key=mk.field_key))
            continue
        want = str(metric[mk.field_key])
        shown = mk.shown if mk.field_key == "display" else re.sub(r"\s+", " ", mk.shown).strip()
        ok = shown == (want if mk.field_key == "display" else re.sub(r"\s+", " ", want).strip())
        if not ok:
            problems.append(
                f"{loc} {mk.metric_id}.{mk.field_key} 顯示「{shown}」，真源是「{want}」")
        if metric.get("status") == "draft":
            problems.append(f"{loc} {mk.metric_id} 的 status 是 draft，未經裁決不得上站")
        rows.append(Row(mk.metric_id, loc, mk.shown, "marked", ok,
                        "" if ok else f"應為 {want}", field_key=mk.field_key))

    text, offsets = condense(src, [(mk.start, mk.end) for mk in marked])
    for mid, metric in metrics.items():
        units = metric_units(metric)
        hits = []
        for pattern, need_unit, why in alias_patterns(metric):
            rx = _pattern_regex(pattern, units if need_unit else None)
            hits += [(h.start(), h.end(), h.group(0), why) for h in rx.finditer(text)
                     if not in_numeric_range(text, h.start(), h.end())]
        # 同一處會被多個寫法命中（例：`7,917+` 同時中 `7,917+` 與 `7,917`），
        # 依「起點在前、越長越優先」排序後去重，一處只算一筆黑數。
        kept: list[tuple[int, int, str, str]] = []
        for start, end, shown, why in sorted(hits, key=lambda h: (h[0], -h[1])):
            if any(start < k_end and end > k_start for k_start, k_end, _, _ in kept):
                continue
            kept.append((start, end, shown, why))
        for start, end, shown, why in kept:
            line = _line_of(starts, offsets[start])
            rows.append(Row(mid, f"{rel}:{line}", re.sub(r"\s+", " ", shown.strip()),
                            "prose", False, f"未標記（{why}）",
                            context=context_hash(text, start, end)))
    return rows, problems


# ── 真源自檢（C-02）──────────────────────────────────────────
def check_source(metrics: dict) -> list[str]:
    problems: list[str] = []
    for mid, m in metrics.items():
        for key in REQUIRED_FIELDS:
            if key not in m or m[key] in (None, ""):
                problems.append(f"numbers.json 的 {mid} 缺欄位 `{key}`")
        if m.get("status") not in VALID_STATUS:
            problems.append(f"numbers.json 的 {mid} status「{m.get('status')}」不合法"
                            f"（可用：{'、'.join(VALID_STATUS)}）")
        digits = re.sub(r"[^0-9]", "", str(m.get("display", "")))
        if digits and "value" in m:
            same = digits == str(int(m["value"]))
            if not same and not m.get("display_approx"):
                problems.append(
                    f"numbers.json 的 {mid}：display「{m['display']}」與 value {m['value']} 不一致，"
                    f"若是刻意的近似對外值，請加 \"display_approx\": true 並在 notes 說明")
            if same and m.get("display_approx"):
                problems.append(f"numbers.json 的 {mid} 標了 display_approx，但 display 就是精確值")
    return problems


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_metrics(path: Path) -> dict:
    data = load_json(Path(path))
    metrics: dict = {}
    for m in data["metrics"]:
        if m["id"] in metrics:
            raise ValueError(f"numbers.json 有重複 id：{m['id']}")
        metrics[m["id"]] = m
    return metrics


def load_allowlist(path: Path) -> list:
    p = Path(path)
    if not p.exists():
        return []
    return load_json(p)["allow"]


def load_manifest(path: Path) -> list:
    p = Path(path)
    if not p.exists():
        return []
    return load_json(p)["marked"]


# ── 主檢查 ──────────────────────────────────────────────────
def check(root: Path, metrics: dict, allowlist: list, manifest: list | None = None,
          ) -> tuple[list[Row], list[str]]:
    root = Path(root)
    rows: list[Row] = []
    problems: list[str] = check_source(metrics)
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        r, p = scan_file(path, rel, metrics)
        rows.extend(r)
        problems.extend(p)

    problems += check_manifest(rows, metrics, manifest)
    problems += check_allowlist(rows, allowlist)

    rows.sort(key=lambda r: (r.location.rsplit(":", 1)[0],
                            int(r.location.rsplit(":", 1)[1]), r.metric_id))
    return rows, problems


def marked_counts(rows: list[Row]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        if row.kind != "marked":
            continue
        key = (row.location.rsplit(":", 1)[0], row.metric_id)
        counts[key] = counts.get(key, 0) + 1
    return counts


def check_manifest(rows: list[Row], metrics: dict, manifest: list | None) -> list[str]:
    """位置基線（C-01）：標記整片消失、卡片被刪、數量變少，都要擋下來。"""
    problems: list[str] = []
    counts = marked_counts(rows)

    on_site = {mid for mid, m in metrics.items() if m.get("on_site", True)}
    present = {mid for (_f, mid) in counts}
    for mid in sorted(on_site - present):
        problems.append(f"位置基線：{mid} 宣告會上站（on_site），但全站找不到任何 data-metric 標記"
                        f"——標記被刪或頁面被改掉了？")
    for mid in sorted(present - on_site):
        problems.append(f"位置基線：{mid} 在 numbers.json 標了 on_site=false，卻出現在頁面上")

    if manifest is None:
        return problems
    expected = {(e["file"], e["id"]): e["count"] for e in manifest}
    for key in sorted(expected):
        want, got = expected[key], counts.get(key, 0)
        if got < want:
            problems.append(
                f"位置基線：{key[0]} 的 {key[1]} 標記應有 {want} 處、實際 {got} 處"
                f"——被刪掉了？確認是刻意的再跑 --update-manifest")
        elif got > want:
            problems.append(
                f"位置基線：{key[0]} 的 {key[1]} 標記應有 {want} 處、實際 {got} 處"
                f"——新增標記請跑 --update-manifest 登記")
    for key in sorted(set(counts) - set(expected)):
        problems.append(
            f"位置基線：{key[0]} 的 {key[1]} 有 {counts[key]} 處標記但基線沒登記"
            f"——請跑 --update-manifest")
    return problems


def check_allowlist(rows: list[Row], allowlist: list) -> list[str]:
    """黑數 allowlist（C-04）：綁檔案＋id＋筆數＋每處語境雜湊。"""
    problems: list[str] = []
    registered = {(a["id"], a["file"]): a for a in allowlist}
    seen: dict[tuple[str, str], list[Row]] = {}
    for row in rows:
        if row.kind != "prose":
            continue
        key = (row.metric_id, row.location.rsplit(":", 1)[0])
        seen.setdefault(key, []).append(row)

    for key, hits in sorted(seen.items()):
        entry = registered.get(key)
        if entry is None:
            problems.append(
                f"黑數：{key[1]} 有 {len(hits)} 處未標記的 {key[0]} 數值"
                f"（{', '.join(h.location for h in hits[:6])}）"
                f"——請改用 data-metric 標記，或登記到 numbers_allowlist.json")
            continue
        if entry["count"] != len(hits):
            problems.append(
                f"黑數筆數變動：{key[1]} 的 {key[0]} 登記 {entry['count']} 處、"
                f"實際 {len(hits)} 處（{', '.join(h.location for h in hits[:6])}）"
                f"——請覆核後更新 numbers_allowlist.json")
            continue
        want = sorted(entry.get("contexts", []))
        got = sorted(h.context for h in hits)
        if want != got:
            missing = sorted(set(want) - set(got))
            added = sorted(set(got) - set(want))
            problems.append(
                f"黑數語境變動：{key[1]} 的 {key[0]} 筆數沒變（{len(hits)} 處）但句子或位置變了"
                f"（消失 {missing or '無'}／新增 {added or '無'}）"
                f"——請逐處覆核語意與單位後跑 --update-allowlist 重新核准")
            continue
        for h in hits:
            h.ok = True
            h.note = f"已登記文案：{entry['reason']}"

    for key, entry in sorted(registered.items()):
        if key not in seen:
            problems.append(
                f"allowlist 有登記但掃不到：{key[1]} 的 {key[0]} 登記 {entry['count']} 處、實際 0 處"
                f"——文案已改？請刪除該筆登記")
    return problems


# ── 更新輔助（人工覆核後才跑）────────────────────────────────
def build_manifest(rows: list[Row]) -> dict:
    counts = marked_counts(rows)
    return {
        "version": 1,
        "purpose": "標記位置基線：每個檔案應有幾處 data-metric。整卡刪除／標記消失／"
                   "數量變少都會被 numbers_check.py 擋下（Codex 盲審 C-01）。",
        "how_to_update": "確認頁面改動是刻意的之後，跑 "
                         "`python3 _source/deploy-automation/numbers_check.py --update-manifest`。",
        "marked": [{"file": f, "id": i, "count": c}
                   for (f, i), c in sorted(counts.items())],
    }


def build_allowlist(rows: list[Row], previous: list) -> dict:
    old = {(a["id"], a["file"]): a for a in previous}
    seen: dict[tuple[str, str], list[Row]] = {}
    for row in rows:
        if row.kind != "prose":
            continue
        seen.setdefault((row.metric_id, row.location.rsplit(":", 1)[0]), []).append(row)
    allow = []
    for (mid, f), hits in sorted(seen.items()):
        prev = old.get((mid, f), {})
        allow.append({
            "id": mid,
            "file": f,
            "count": len(hits),
            "lines_20260906": sorted(int(h.location.rsplit(":", 1)[1]) for h in hits),
            "contexts": sorted(h.context for h in hits),
            "reason": prev.get("reason",
                               "文案、meta 描述或 JSON-LD 中的引用；數字改動時須人工一併更新"),
        })
    return {
        "version": 2,
        "purpose": "登記「未用 data-metric 標記、但確實顯示已知數值」的文案位置。"
                   "contexts 是每一處前後各 30 字的語境雜湊：同檔案換位置或換句子都會"
                   "被擋下來重新核准（Codex 盲審 C-04）。",
        "limits": "本掃描只找得到別名表涵蓋的寫法。全新的換句方式仍需季度冷讀；"
                  "改過的舊值請登記到 numbers.json 的 previous_values。",
        "how_to_update": "逐處覆核語意與單位無誤後，跑 "
                         "`python3 _source/deploy-automation/numbers_check.py --update-allowlist`。",
        "allow": allow,
    }


# ── 輸出 ────────────────────────────────────────────────────
def report_text(rows: list[Row], metrics: dict, root: Path) -> str:
    lines = [
        "# 官網影響力數字位置表",
        "",
        "> 由 `_source/deploy-automation/numbers_check.py --report` 產生；",
        "> 真源 `_source/numbers.json`，規則見 `_source/SOP-數據更新與部署索引.md`。",
        f"> 掃描根目錄：`{Path(root).name}/`（表中路徑皆相對於此）。",
        "",
        f"標記處 {sum(1 for r in rows if r.kind == 'marked')} 處、"
        f"已登記文案處 {sum(1 for r in rows if r.kind == 'prose')} 處。",
        "",
        "## 一、標記位置（data-metric，apply_numbers.py 會自動改）",
        "",
        "| id | 欄位 | 檔案:行號 | 顯示值 | 是否相符 |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        if r.kind == "marked":
            lines.append(f"| `{r.metric_id}` | {r.field_key} | `{r.location}` | {r.shown} | "
                         f"{'✅ 相符' if r.ok else '❌ ' + r.note} |")
    lines += [
        "",
        "## 二、文案位置（未標記但已登記；數字改動時要人工一起改）",
        "",
        "| id | 檔案:行號 | 顯示值 | 語境雜湊 | 是否相符 |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        if r.kind == "prose":
            lines.append(f"| `{r.metric_id}` | `{r.location}` | {r.shown} | `{r.context}` | "
                         f"{'✅ 已登記' if r.ok else '❌ 黑數'} |")
    lines += ["", "## 三、真源摘要", "",
              "| id | display | 單位 | 資料期間 | status | last_verified |",
              "|---|---|---|---|---|---|"]
    for mid, m in metrics.items():
        lines.append(f"| `{mid}` | {m['display']} | {m['unit']} | {m['period']} | "
                     f"{m.get('status', '—')} | {m['last_verified']} |")
    lines.append("")
    return "\n".join(lines)


def write_report(path: Path, rows: list[Row], metrics: dict, root: Path) -> None:
    Path(path).write_text(report_text(rows, metrics, root), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="官網影響力數字位置表與黑數檢查")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="要掃的網站目錄（預設 public/）")
    ap.add_argument("--numbers", default=str(DEFAULT_NUMBERS), help="單一真源 numbers.json")
    ap.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST), help="文案位置登記檔")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="標記位置基線檔")
    ap.add_argument("--report", help="把位置表寫成 markdown")
    ap.add_argument("--check-report", help="比對既有位置表是否過期（不寫檔）")
    ap.add_argument("--update-allowlist", action="store_true",
                    help="人工覆核後重新核准所有文案位置（會覆寫 allowlist）")
    ap.add_argument("--update-manifest", action="store_true",
                    help="人工覆核後重新登記標記位置基線（會覆寫 manifest）")
    args = ap.parse_args(argv)

    metrics = load_metrics(Path(args.numbers))
    allowlist = load_allowlist(Path(args.allowlist))
    manifest = load_manifest(Path(args.manifest))

    if args.update_allowlist or args.update_manifest:
        rows, _ = check(Path(args.root), metrics, [], None)
        if args.update_allowlist:
            Path(args.allowlist).write_text(
                json.dumps(build_allowlist(rows, allowlist), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            print(f"已重新核准文案位置：{args.allowlist}")
        if args.update_manifest:
            Path(args.manifest).write_text(
                json.dumps(build_manifest(rows), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            print(f"已重新登記標記基線：{args.manifest}")
        return 0

    rows, problems = check(Path(args.root), metrics, allowlist, manifest)

    print(f"=== 數字位置表（真源 {Path(args.numbers).name}，{len(metrics)} 筆指標）===")
    width = max([len(r.location) for r in rows] + [20]) + 2
    print(f"{'id':<16}{'檔案:行號':<{width}}{'顯示值':<14}是否相符")
    for r in rows:
        state = ("✅ 相符" if r.kind == "marked" else "✅ 已登記文案") if r.ok else \
                ("❌ " + r.note if r.kind == "marked" else "❌ 黑數")
        print(f"{r.metric_id:<16}{r.location:<{width}}{r.shown:<14}{state}")

    marked = [r for r in rows if r.kind == "marked"]
    prose = [r for r in rows if r.kind == "prose"]
    print(f"\n標記處 {len(marked)} 處（相符 {sum(1 for r in marked if r.ok)}）、"
          f"文案處 {len(prose)} 處（已登記 {sum(1 for r in prose if r.ok)}）")

    provisional = [mid for mid, m in metrics.items() if m.get("status") == "provisional"]
    if provisional:
        print(f"⚠️  來源鏈待補（status=provisional，須秘書處／理事長拍板）："
              f"{'、'.join(provisional)}")

    if args.report:
        write_report(Path(args.report), rows, metrics, Path(args.root))
        print(f"位置表已寫入：{args.report}")

    if args.check_report:
        p = Path(args.check_report)
        want = report_text(rows, metrics, Path(args.root))
        got = p.read_text(encoding="utf-8") if p.exists() else ""
        if want != got:
            problems.append(f"位置表過期：{args.check_report} 與現況不符，請跑 --report 重生後 commit")

    if problems:
        print(f"\n❌ 檢查未通過，{len(problems)} 個問題：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n✅ 全部相符：標記與真源一致、位置基線無缺、沒有未登記的黑數。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

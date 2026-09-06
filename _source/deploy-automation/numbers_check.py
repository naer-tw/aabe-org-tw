#!/usr/bin/env python3
"""numbers_check.py — 官網影響力數字的位置表與黑數檢查（部署前閘門）。

依據：_source/SOP-數據更新與部署索引.md 第二節。

做三件事：
  1. 掃 public/**/*.html ＋ llms.txt ＋ humans.txt，列出每個 data-metric 標記的
     檔案:行號與顯示值，與 _source/numbers.json 的 display 比對。
  2. 掃「未標記處」出現的已知數值字串（numbers.json 的 scan_patterns，含帶逗號／
     不帶逗號／逾約前綴）＝黑數；黑數必須登記在 _source/numbers_allowlist.json
     （文案敘述類，附理由與筆數），否則報錯。
  3. 任一不符或未登記黑數 → exit 1，擋住部署。

用法：
    python3 _source/deploy-automation/numbers_check.py
    python3 _source/deploy-automation/numbers_check.py --report _source/數字位置表_20260906.md
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_NUMBERS = REPO / "_source" / "numbers.json"
DEFAULT_ALLOWLIST = REPO / "_source" / "numbers_allowlist.json"
DEFAULT_ROOT = REPO / "public"
EXTRA_TEXT_FILES = ("llms.txt", "humans.txt")

# 這些區塊裡的數字不是給人看的內容（樣式、腳本、向量圖、註解），不掃
_BLANK_BLOCKS = re.compile(
    r"<style\b[^>]*>.*?</style>"
    r"|<svg\b[^>]*>.*?</svg>"
    r"|<!--.*?-->"
    r"|<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>",
    re.S | re.I,
)
_TAG = re.compile(r"<[^>]*>", re.S)
_META_CONTENT = re.compile(r'^<meta\b[^>]*\bcontent="([^"]*)"', re.S | re.I)
_OPEN_WITH_METRIC = re.compile(
    r'<(?P<tag>[a-zA-Z][\w-]*)\b[^>]*\bdata-metric="(?P<id>[^"]+)"[^>]*>')


# ── 資料結構 ────────────────────────────────────────────────
@dataclass
class Marked:
    metric_id: str
    shown: str
    line: int
    start: int
    end: int


@dataclass
class Row:
    metric_id: str
    location: str       # 檔案:行號
    shown: str
    kind: str           # marked / prose
    ok: bool
    note: str = ""


# ── 文字抽取 ────────────────────────────────────────────────
def _blank(match: re.Match) -> str:
    """把整段換成等長空白（保留換行），行號才不會位移。"""
    return re.sub(r"[^\n]", " ", match.group(0))


def condense(src: str, mask: Iterable[tuple[int, int]] = ()) -> tuple[str, list[int]]:
    """回傳 (可讀文字, 每個字元在原始碼中的位移)。

    標籤本身被丟掉，讓 `168<span>+</span>` 併回 `168+`；<meta> 的 content 會被
    留下來（meta description 也是對外文案）；mask 內的區間（已標記的數字）挖空，
    才不會被自己的黑數掃描抓到。
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
                    base = i + mc.start(1)
                    for j, ch in enumerate(mc.group(1)):
                        out.append(ch)
                        pos.append(base + j)
                    out.append(" ")
                    pos.append(i)
                i = m.end()
                continue
        out.append(s[i])
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
    return re.sub(r"\s+", "", _TAG.sub("", html))


def find_marked(src: str) -> list[Marked]:
    """找出所有 data-metric 標記，回傳 id、顯示文字（去標籤去空白）、行號與內文區間。"""
    starts = _line_starts(src)
    found: list[Marked] = []
    for m in _OPEN_WITH_METRIC.finditer(src):
        tag = m.group("tag")
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
            raise ValueError(f'data-metric="{m.group("id")}" 的 <{tag}> 缺少收尾標籤')
        found.append(Marked(
            metric_id=m.group("id"),
            shown=_strip_tags(src[m.end():inner_end]),
            line=_line_of(starts, m.start()),
            start=m.end(),
            end=inner_end,
        ))
    return found


# ── 掃描 ────────────────────────────────────────────────────
def _pattern_regex(pattern: str) -> re.Pattern:
    """字串裡的空白放寬成任意空白（HTML 常被換行切開）；前後不得再接數字。"""
    body = r"\s*".join(re.escape(part) for part in pattern.split())
    return re.compile(r"(?<![0-9])" + body + r"(?![0-9])")


def iter_files(root: Path) -> list[Path]:
    files = sorted(p for p in root.rglob("*.html") if p.is_file())
    files += [root / name for name in EXTRA_TEXT_FILES if (root / name).exists()]
    return files


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
        ok = mk.shown == metric["display"]
        if not ok:
            problems.append(
                f"{loc} {mk.metric_id} 顯示「{mk.shown}」，真源 display 是「{metric['display']}」")
        rows.append(Row(mk.metric_id, loc, mk.shown, "marked", ok,
                        "" if ok else f"應為 {metric['display']}"))

    text, offsets = condense(src, [(mk.start, mk.end) for mk in marked])
    for mid, metric in metrics.items():
        hits = []
        for pattern in metric["scan_patterns"]:
            hits += [(h.start(), h.end(), h.group(0)) for h in _pattern_regex(pattern).finditer(text)]
        # 同一處會被多個寫法命中（例：`7,917+` 同時中 `7,917+` 與 `7,917`），
        # 依「起點在前、越長越優先」排序後去重，一處只算一筆黑數。
        kept: list[tuple[int, int, str]] = []
        for start, end, shown in sorted(hits, key=lambda h: (h[0], -h[1])):
            if any(start < k_end and end > k_start for k_start, k_end, _ in kept):
                continue
            kept.append((start, end, shown))
        for start, _, shown in kept:
            line = _line_of(starts, offsets[start])
            rows.append(Row(mid, f"{rel}:{line}", shown.strip(), "prose", False, "未標記"))
    return rows, problems


def check(root: Path, metrics: dict, allowlist: list) -> tuple[list[Row], list[str]]:
    root = Path(root)
    rows: list[Row] = []
    problems: list[str] = []
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        r, p = scan_file(path, rel, metrics)
        rows.extend(r)
        problems.extend(p)

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
        for h in hits:
            h.ok = True
            h.note = f"已登記文案：{entry['reason']}"

    for key, entry in sorted(registered.items()):
        if key not in seen:
            problems.append(
                f"allowlist 有登記但掃不到：{key[1]} 的 {key[0]} 登記 {entry['count']} 處、實際 0 處"
                f"——文案已改？請刪除該筆登記")

    rows.sort(key=lambda r: (r.location.rsplit(":", 1)[0],
                            int(r.location.rsplit(":", 1)[1]), r.metric_id))
    return rows, problems


# ── 輸出 ────────────────────────────────────────────────────
def write_report(path: Path, rows: list[Row], metrics: dict, root: Path) -> None:
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
        "| id | 檔案:行號 | 顯示值 | 是否相符 |",
        "|---|---|---|---|",
    ]
    for r in rows:
        if r.kind == "marked":
            lines.append(f"| `{r.metric_id}` | `{r.location}` | {r.shown} | "
                         f"{'✅ 相符' if r.ok else '❌ ' + r.note} |")
    lines += [
        "",
        "## 二、文案位置（未標記但已登記；數字改動時要人工一起改）",
        "",
        "| id | 檔案:行號 | 顯示值 | 是否相符 |",
        "|---|---|---|---|",
    ]
    for r in rows:
        if r.kind == "prose":
            lines.append(f"| `{r.metric_id}` | `{r.location}` | {r.shown} | "
                         f"{'✅ 已登記' if r.ok else '❌ 黑數'} |")
    lines += ["", "## 三、真源摘要", "",
              "| id | display | 單位 | 資料期間 | last_verified |", "|---|---|---|---|---|"]
    for mid, m in metrics.items():
        lines.append(f"| `{mid}` | {m['display']} | {m['unit']} | {m['period']} | "
                     f"{m['last_verified']} |")
    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def load_metrics(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {m["id"]: m for m in data["metrics"]}


def load_allowlist(path: Path) -> list:
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))["allow"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="官網影響力數字位置表與黑數檢查")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="要掃的網站目錄（預設 public/）")
    ap.add_argument("--numbers", default=str(DEFAULT_NUMBERS), help="單一真源 numbers.json")
    ap.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST), help="文案位置登記檔")
    ap.add_argument("--report", help="把位置表寫成 markdown")
    args = ap.parse_args(argv)

    metrics = load_metrics(Path(args.numbers))
    allowlist = load_allowlist(Path(args.allowlist))
    rows, problems = check(Path(args.root), metrics, allowlist)

    print(f"=== 數字位置表（真源 {Path(args.numbers).name}，{len(metrics)} 筆指標）===")
    print(f"{'id':<16}{'檔案:行號':<44}{'顯示值':<12}是否相符")
    for r in rows:
        state = ("✅ 相符" if r.kind == "marked" else "✅ 已登記文案") if r.ok else \
                ("❌ " + r.note if r.kind == "marked" else "❌ 黑數")
        print(f"{r.metric_id:<16}{r.location:<44}{r.shown:<12}{state}")

    marked = [r for r in rows if r.kind == "marked"]
    prose = [r for r in rows if r.kind == "prose"]
    print(f"\n標記處 {len(marked)} 處（相符 {sum(1 for r in marked if r.ok)}）、"
          f"文案處 {len(prose)} 處（已登記 {sum(1 for r in prose if r.ok)}）")

    if args.report:
        write_report(Path(args.report), rows, metrics, Path(args.root))
        print(f"位置表已寫入：{args.report}")

    if problems:
        print(f"\n❌ 檢查未通過，{len(problems)} 個問題：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n✅ 全部相符，且沒有未登記的黑數。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""apply_events.py — 把 _source/events.json 的 badge／cta 一次寫回全站標記處。

依據：規劃書「官網UIUX_改善規劃_20260914.md」第三批工作項 3（同一來源 events.json
驅動首頁最新倡議卡、活動總表、行動頁、活動專頁多頁，取代手工同步）。

流程：改清單 → 改 events.json → 跑本腳本 → 跑 events_check.py → 分支／盲審／上線。

只動 `data-event-field="badge"` 標記的可見文字、`data-event-field="cta"` 標記的可見
文字與（該元素本身若有 href 屬性時的）連結；不新增／刪除任何卡片、不動版面與其他文
案——這不是整站產生器，是窄欄位回填（指揮部裁決：規劃書「不一定要改成產生器」）。

`data-event-id="<id>"` 只用來標定「這張卡片屬於哪一場活動」，本身不會被改寫。

用法：
    python3 _source/deploy-automation/apply_events.py --dry-run
    python3 _source/deploy-automation/apply_events.py
"""
from __future__ import annotations

import argparse
import bisect
import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_EVENTS = REPO / "_source" / "events.json"
DEFAULT_ROOT = REPO / "public"

_EVENT_ID_OPEN = re.compile(
    r'<(?P<tag>[a-zA-Z][\w-]*)\b[^>]*?\bdata-event-id=(?:"(?P<id>[^"]+)"|\'(?P<id2>[^\']+)\')[^>]*>')
_FIELD_OPEN = re.compile(
    r'<(?P<tag>[a-zA-Z][\w-]*)\b[^>]*?\bdata-event-field=(?:"(?P<field>[^"]+)"|\'(?P<field2>[^\']+)\')[^>]*>')
_HREF_DQ = re.compile(r'\bhref="([^"]*)"')
_HREF_SQ = re.compile(r"\bhref='([^']*)'")
_TAG = re.compile(r"<[^>]*>", re.S)

FIELD_KEYS = ("badge", "cta")


class ApplyError(RuntimeError):
    """版面改不動、或標記與真源對不上時丟出——寧可停下來要人工看，也不默默改壞。"""


@dataclass
class Change:
    event_id: str
    field: str
    old: str
    new: str
    location: str = ""


def _line_starts(src: str) -> list[int]:
    starts = [0]
    for m in re.finditer("\n", src):
        starts.append(m.end())
    return starts


def _line_of(starts: list[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def _strip_tags(html: str) -> str:
    return _TAG.sub("", html).strip()


def _find_inner_end(src: str, tag: str, after: int) -> int:
    """從 after 開始找 <tag> 的收尾位置（處理同名巢狀標籤），回傳內文結束位移。"""
    closer = re.compile(r"</?" + re.escape(tag) + r"\b[^>]*>", re.I)
    depth, cursor, inner_end = 1, after, None
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
        raise ApplyError(f"<{tag}> 缺少收尾標籤，標記附近版面可能損毀")
    return inner_end


@dataclass
class IdMark:
    event_id: str
    pos: int
    line: int


@dataclass
class FieldMark:
    field: str
    line: int
    open_start: int
    open_end: int
    inner_start: int
    inner_end: int
    shown: str
    href_start: int | None
    href_end: int | None


def find_event_ids(src: str) -> list[IdMark]:
    starts = _line_starts(src)
    out: list[IdMark] = []
    for m in _EVENT_ID_OPEN.finditer(src):
        eid = m.group("id") or m.group("id2")
        out.append(IdMark(eid, m.start(), _line_of(starts, m.start())))
    return out


def find_fields(src: str) -> list[FieldMark]:
    starts = _line_starts(src)
    out: list[FieldMark] = []
    for m in _FIELD_OPEN.finditer(src):
        field = m.group("field") or m.group("field2")
        tag = m.group("tag")
        inner_start = m.end()
        inner_end = _find_inner_end(src, tag, inner_start)
        shown = _strip_tags(src[inner_start:inner_end])
        open_tag = src[m.start():m.end()]
        href_start = href_end = None
        hm = _HREF_DQ.search(open_tag) or _HREF_SQ.search(open_tag)
        if hm:
            href_start = m.start() + hm.start(1)
            href_end = m.start() + hm.end(1)
        out.append(FieldMark(field, _line_of(starts, m.start()), m.start(), m.end(),
                              inner_start, inner_end, shown, href_start, href_end))
    return out


def _default_badge(ev: dict) -> str:
    status = ev.get("status")
    if status == "cancelled":
        return "活動取消"
    if status == "ended":
        return "已結束"
    return "即將舉辦"


def _owning_event(ids: list[IdMark], pos: int, path_hint: str) -> str:
    """field 標記歸屬哪一場活動：同檔內位移在它之前、離它最近的 data-event-id。"""
    candidates = [im for im in ids if im.pos <= pos]
    if not candidates:
        raise ApplyError(f"{path_hint}：data-event-field 標記找不到對應的 data-event-id"
                          f"（該標記前沒有任何 data-event-id）")
    return max(candidates, key=lambda im: im.pos).event_id


def apply_html(src: str, events: dict, path_hint: str) -> tuple[str, list[Change], set[str]]:
    """回傳 (改好的 HTML, 改動清單, 檔案內出現過的 event id 集合)。"""
    ids = find_event_ids(src)
    fields = find_fields(src)
    starts = _line_starts(src)

    for im in ids:
        if im.event_id not in events:
            raise ApplyError(f"{path_hint} 行 {im.line}：版面上的 data-event-id="
                              f"\"{im.event_id}\" 不在 events.json 裡")

    edits: list[tuple[int, int, str]] = []   # (start, end, replacement)
    changes: list[Change] = []
    for fm in fields:
        if fm.field not in FIELD_KEYS:
            raise ApplyError(f"{path_hint} 行 {fm.line}：data-event-field=\"{fm.field}\""
                              f" 不是可投影欄位（僅 badge/cta）")
        eid = _owning_event(ids, fm.open_start, f"{path_hint} 行 {fm.line}")
        ev = events[eid]

        if fm.field == "badge":
            want_text = ev.get("badge") or _default_badge(ev)
        else:
            cta = ev.get("cta") or {}
            want_text = cta.get("label")
            if want_text is None:
                raise ApplyError(f"{path_hint} 行 {fm.line}：{eid} 的 events.json 缺少"
                                  f" cta.label")
            want_url = cta.get("url")
            if fm.href_start is not None:
                if want_url is None:
                    raise ApplyError(
                        f"{path_hint} 行 {fm.line}：{eid} 的 cta.url 是 null（純文字狀態），"
                        f"但版面上這個標記是帶 href 的連結——標記與真源對不上，需人工確認")
                current_href = src[fm.href_start:fm.href_end]
                if current_href != want_url:
                    edits.append((fm.href_start, fm.href_end, want_url))
                    changes.append(Change(eid, "cta.url", current_href, want_url,
                                           f"{path_hint} 行 {fm.line}"))

        if fm.shown != want_text:
            if "<" in src[fm.inner_start:fm.inner_end]:
                raise ApplyError(f"{path_hint} 行 {fm.line}：{eid} 的 "
                                  f"data-event-field=\"{fm.field}\" 區塊含巢狀標籤，"
                                  f"請人工處理")
            edits.append((fm.inner_start, fm.inner_end, want_text))
            changes.append(Change(eid, fm.field, fm.shown, want_text,
                                   f"{path_hint} 行 {fm.line}"))

    out = src
    for start, end, replacement in sorted(edits, key=lambda e: e[0], reverse=True):
        out = out[:start] + replacement + out[end:]

    file_ids = {im.event_id for im in ids}
    return out, changes, file_ids


def _page_to_file(root: Path, page: str) -> Path:
    rel = page.strip("/")
    if not rel:
        return root / "index.html"
    return root / rel / "index.html"


def check_coverage(root: Path, events: dict, file_ids: dict[str, set[str]]) -> None:
    """events.json 每個 id 的 pages[] 都要能在對應頁面找到 data-event-id 標記。"""
    missing: list[str] = []
    for eid, ev in events.items():
        for page in ev.get("pages", []):
            target = _page_to_file(root, page)
            rel = target.relative_to(root).as_posix() if target.exists() else f"({page} 對應檔不存在：{target})"
            found = eid in file_ids.get(str(target), set())
            if not found:
                missing.append(f"{eid} 的 pages[] 列了 {page!r}，但 {rel} 找不到 "
                                f"data-event-id=\"{eid}\" 標記")
    if missing:
        raise ApplyError("位置基線：" + "；".join(missing))


def run(root: Path, events_data: dict, dry_run: bool) -> list[Change]:
    root = Path(root)
    events = {ev["id"]: ev for ev in events_data["events"]}
    changes: list[Change] = []
    pending: list[tuple[Path, str, str]] = []
    file_ids: dict[str, set[str]] = {}

    for path in sorted(p for p in root.rglob("*.html") if p.is_file()):
        src = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
        out, file_changes, ids_found = apply_html(src, events, rel)
        file_ids[str(path)] = ids_found
        if file_changes:
            changes.extend(file_changes)
            pending.append((path, src, out))

    check_coverage(root, events, file_ids)

    for path, src, out in pending:
        if dry_run:
            sys.stdout.writelines(difflib.unified_diff(
                src.splitlines(keepends=True), out.splitlines(keepends=True),
                fromfile=f"a/{path.name}", tofile=f"b/{path.name}", n=1))
        else:
            path.write_text(out, encoding="utf-8")
    return changes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="把 events.json 的 badge／cta 寫回全站標記處")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--events", default=str(DEFAULT_EVENTS))
    ap.add_argument("--dry-run", action="store_true", help="只印 diff，不寫檔")
    args = ap.parse_args(argv)

    events_data = json.loads(Path(args.events).read_text(encoding="utf-8"))
    try:
        changes = run(Path(args.root), events_data, args.dry_run)
    except ApplyError as e:
        print(f"❌ 停手：{e}")
        return 1

    if not changes:
        print("✅ 無變動：版面上的標記處已與 _source/events.json 一致。")
        return 0
    print(("（dry-run）" if args.dry_run else "") + f"共 {len(changes)} 處標記更新：")
    for c in changes:
        print(f"  - {c.event_id} {c.field}：{c.old} → {c.new}（{c.location}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

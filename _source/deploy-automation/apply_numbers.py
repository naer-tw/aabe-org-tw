#!/usr/bin/env python3
"""apply_numbers.py — 把 _source/numbers.json 的 display 一次寫回全站標記處。

依據：_source/SOP-數據更新與部署索引.md 第二節。

流程：改清單 → 改 numbers.json → 跑本腳本 → 跑 numbers_check.py → 分支／盲審／上線。

只動 `data-metric` 標記裡的數字本體，樣式標籤（例 `<span class="plus">+</span>`）
原封不動；改完會在 /methodology/ 的「最近更新」欄與 Changelog 留一行痕跡。
文案裡的數字（numbers_allowlist.json 登記的 158 處）本腳本不會動，請照
`_source/數字位置表_20260906.md` 人工更新——這是刻意的：文案要順句子改，不是換數字。

用法：
    python3 _source/deploy-automation/apply_numbers.py --dry-run
    python3 _source/deploy-automation/apply_numbers.py
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numbers_check as nc

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_NUMBERS = REPO / "_source" / "numbers.json"
DEFAULT_ROOT = REPO / "public"

# /methodology/「更新頻率」表的列標題 → 這一列涵蓋哪些指標
ROW_LABEL_TO_IDS = {
    "新聞稿、倡議行動": ("press_releases", "actions"),
    "媒體聲量": ("buzz_3y", "buzz_1y"),
    "合作組織數": ("partners",),
    "問卷類數字（有效樣本、觸及人次）": ("valid_surveys", "single_reach"),
    "問卷類數字": ("valid_surveys", "single_reach"),
    "政策深度分析": ("policy_briefs",),
    "媒體露出": ("press_coverage",),
    "跨黨派合作立委": ("legislators",),
}

_NUMBER_TOKEN = re.compile(r"(?<![0-9])[0-9][0-9,]*")
_MONTH_CELL = re.compile(r"(<td[^>]*>)(\d{4}-\d{2})(</td>)")


class ApplyError(RuntimeError):
    """版面改不動、或真源與版面對不上時丟出——寧可停下來要人工看，也不默默改壞。"""


@dataclass
class Change:
    metric_id: str
    old: str
    new: str
    location: str = ""


def _split_display(display: str) -> tuple[str, str]:
    """把 display 拆成「數字本體」與「後綴」，例 `168+` → (`168`, `+`)。"""
    m = _NUMBER_TOKEN.search(display)
    if not m:
        raise ApplyError(f"display 找不到數字：{display}")
    return m.group(0), display[m.end():]


def apply_html(src: str, metrics: dict) -> tuple[str, list[Change]]:
    """回傳 (改好的 HTML, 改動清單)。由後往前改，才不會動到還沒處理的位移。"""
    marked = nc.find_marked(src)
    changes: list[Change] = []
    out = src
    for mk in reversed(marked):
        metric = metrics.get(mk.metric_id)
        if metric is None:
            raise ApplyError(f"版面上的 data-metric=\"{mk.metric_id}\"（行 {mk.line}）"
                             f"不在 numbers.json 裡")
        if mk.shown == metric["display"]:
            continue
        core, _ = _split_display(metric["display"])
        inner = out[mk.start:mk.end]
        if not _NUMBER_TOKEN.search(inner):
            raise ApplyError(f"{mk.metric_id}（行 {mk.line}）標記裡找不到可替換的數字")
        new_inner = _NUMBER_TOKEN.sub(core, inner, count=1)
        shown = re.sub(r"\s+", "", re.sub(r"<[^>]*>", "", new_inner))
        if shown != metric["display"]:
            raise ApplyError(
                f"{mk.metric_id}（行 {mk.line}）改完會顯示「{shown}」，真源是"
                f"「{metric['display']}」——版面上的後綴（例 + 號 span）需要人工調整")
        out = out[:mk.start] + new_inner + out[mk.end:]
        changes.append(Change(mk.metric_id, mk.shown, metric["display"], f"行 {mk.line}"))
    return out, list(reversed(changes))


def update_methodology(src: str, changes: list[Change], today: str) -> str:
    """更新「最近更新」月份（只動有改到的指標那幾列）並在 Changelog 追加一行。"""
    if not changes:
        return src
    changed_ids = {c.metric_id for c in changes}
    month = today[:7]

    lines = src.splitlines(keepends=True)
    for i, line in enumerate(lines):
        for label, ids in ROW_LABEL_TO_IDS.items():
            if label in line and changed_ids & set(ids):
                lines[i] = _MONTH_CELL.sub(lambda m: m.group(1) + month + m.group(3), line)
                break
    src = "".join(lines)

    summary = "、".join(
        f"{cid} {old} → {new}" for cid, old, new in sorted(
            {(c.metric_id, c.old, c.new) for c in changes}))
    entry = (f'      <div class="cl-row">\n'
             f'        <time>{today}</time>\n'
             f'        <div class="what">數字更新（單一真源 _source/numbers.json 套用）：'
             f'{summary}。</div>\n'
             f'      </div>\n')
    marker = '<div class="changelog">'
    idx = src.find(marker)
    if idx == -1:
        raise ApplyError("方法頁找不到 <div class=\"changelog\">，無法留痕")
    cut = src.index("\n", idx) + 1
    return src[:cut] + entry + src[cut:]


def run(root: Path, metrics: dict, today: str, dry_run: bool) -> list[Change]:
    root = Path(root)
    changes: list[Change] = []
    pending: list[tuple[Path, str, str]] = []   # (檔案, 原內容, 新內容)

    for path in sorted(p for p in root.rglob("*.html") if p.is_file()):
        src = path.read_text(encoding="utf-8")
        out, file_changes = apply_html(src, metrics)
        if file_changes:
            rel = path.relative_to(root).as_posix()
            for c in file_changes:
                c.location = f"{rel} {c.location}"
            changes.extend(file_changes)
            pending.append((path, src, out))

    methodology = root / "methodology" / "index.html"
    if changes and methodology.exists():
        for i, (path, src, out) in enumerate(pending):
            if path == methodology:
                pending[i] = (path, src, update_methodology(out, changes, today))
                break
        else:
            src = methodology.read_text(encoding="utf-8")
            pending.append((methodology, src, update_methodology(src, changes, today)))

    for path, src, out in pending:
        if dry_run:
            sys.stdout.writelines(difflib.unified_diff(
                src.splitlines(keepends=True), out.splitlines(keepends=True),
                fromfile=f"a/{path.name}", tofile=f"b/{path.name}", n=1))
        else:
            path.write_text(out, encoding="utf-8")
    return changes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="把 numbers.json 的 display 寫回全站標記處")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--numbers", default=str(DEFAULT_NUMBERS))
    ap.add_argument("--today", default=_dt.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true", help="只印 diff，不寫檔")
    args = ap.parse_args(argv)

    metrics = nc.load_metrics(Path(args.numbers))
    try:
        changes = run(Path(args.root), metrics, args.today, args.dry_run)
    except ApplyError as e:
        print(f"❌ 停手：{e}")
        return 1

    if not changes:
        print("✅ 無變動：版面上的標記處已與 _source/numbers.json 一致。")
        return 0
    print(("（dry-run）" if args.dry_run else "") + f"共 {len(changes)} 處標記更新：")
    for c in changes:
        print(f"  - {c.metric_id}：{c.old} → {c.new}（{c.location}）")
    if not args.dry_run:
        print("方法頁「最近更新」與 Changelog 已留痕。")
    print("提醒：文案裡的數字（numbers_allowlist.json 登記處）本腳本不會動，"
          "請照 _source/數字位置表_20260906.md 人工更新，再跑 numbers_check.py。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

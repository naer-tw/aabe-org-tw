#!/usr/bin/env python3
"""build_reports.py — 把 _source/reports/<slug>.md 轉成「工作報告」專區網頁。

依據：理事長 2026-09-20 裁決官網新開「工作報告」專區，指揮部裁定第一天就建輕量管線
（真源 → 產生腳本 → 閘），不手工放頁。設計仿 build_briefs.py 架構（parse_frontmatter／
render 邏輯／查無即中止不產半成品），但工作報告是多章節敘事報告，不是七欄固定格式，
改用「弱制約」：只要求文首有 `## 摘要`、文末有 `## 本期數字一覽`＋`## 參考資料`三個
錨點小節，中間內容自由（章節數、表格、清單皆可）。

流程：
    _source/reports/<slug>.md
        → 解析 front-matter（slug/title/report_no/period_start/period_end/
          published/summary/status）＋ 前言區塊（H1 標題＋**粗體**中繼資料行）
          ＋ 依 `## ` 切分的章節（含 `### ` 子標題、表格、清單、引言）
        → 治理內部字樣掃描（決議／表決／理監事／社團法人／財團法人，
          綁語境 allowlist，見 GOVERNANCE_ALLOWLIST）；內部代號掃描（B\\d+／CMT／A\\d+）
          → 命中即中止，不產半成品頁（同 build_briefs.py 的 fail-closed 原則）
        → 「【…待補…】」渲染成「（出處補充中）」
        → 寫 public/reports/<slug>/index.html（單篇）
        → 重新掃描 _source/reports/*.md 全部，寫 public/reports/index.html（列表，
          按 report_no 倒序）

用法：
    python3 _source/deploy-automation/build_reports.py            # 全部 *.md
    python3 _source/deploy-automation/build_reports.py 2026-03    # 單一報告（仍會重建列表頁）
    python3 _source/deploy-automation/build_reports.py --dry-run 2026-03
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
REPORTS_DIR = REPO / "_source" / "reports"
PUBLIC_DIR = REPO / "public"
OUT_DIR = PUBLIC_DIR / "reports"

REQUIRED_FRONTMATTER = (
    "slug", "title", "report_no", "period_start", "period_end",
    "published", "summary", "status",
)

# 文首必有「摘要」、文末必有「本期數字一覽」＋「參考資料」（比對用 startswith，
# 因為實際標題常帶後綴，例如本站第一篇是「參考資料｜供查證」）。
REQUIRED_ANCHOR_PREFIXES = ("摘要", "本期數字一覽", "參考資料")

# 「資料來源」閘門即檢查「參考資料」錨點是否存在——本站報告一律以「參考資料」
# 作為來源節標題（採訪／查證用途與「資料來源」同義），派工單原文寫「資料來源」，
# 此處對齊真源實際章節命名，理由見交付回報「取捨」欄。
SOURCE_SECTION_PREFIX = "參考資料"

# 治理內部字樣：AABE 絕對紀律禁止自稱「社團法人」「財團法人」，新聞稿正文不得出現
# 「決議」「表決」「理監事」等內部運作字樣外流。但本報告合法引用了外部機關
# 「財團法人厚生基金會」的正式全銜（立法院厚生會兒青心智健康委員會敦聘單位之一），
# 這是第三方的真實法定名稱，不是本聯盟自稱——逐字禁詞會誤殺，因此比照
# numbers_allowlist.json 的「綁語境」精神，先遮蔽白名單詞組再掃描。
GOVERNANCE_FORBIDDEN = re.compile(r"決議|表決|理監事|社團法人|財團法人")
GOVERNANCE_ALLOWLIST = (
    "財團法人厚生基金會",  # 立法院厚生會兒青心智健康委員會敦聘單位之一，外部機關法定全銜
)
# 不加 \b：Python re 把 CJK 字元也算進 \w，內部代號常常緊貼中文（例如「見B12附件」
# 沒有空格），加 \b 會在這種最常見的寫法上失效、反而漏抓。CMT 額外要求邊界，避免誤中
# 英文詞彙內夾帶的字母序列（B\d+／A\d+ 本身數字後綴已經是很窄的形狀，誤判機率低）。
INTERNAL_CODE_PATTERN = re.compile(r"B\d+|A\d+|\bCMT\b")

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_URL = re.compile(r"https?://[^\s<>「」『』\)\]】]+")
_TODO_BRACKET = re.compile(r"【[^】]*待補[^】]*】")
_META_LINE = re.compile(r"^\*\*(.+?)\*\*[：:]\s*(.+)$")
_BULLET = re.compile(r"^-\s+")
_NUMBERED = re.compile(r"^\d+\.\s+")


class ReportError(RuntimeError):
    """來源 markdown 有問題（缺欄位、缺錨點、內部字樣外流等）時丟出，中止產出。"""


@dataclass
class Report:
    slug: str
    title: str
    report_no: int
    period_start: str
    period_end: str
    published: str
    summary: str
    status: str
    h1: str
    meta_lines: list[tuple[str, str]]
    sections: list[tuple[str, str]] = field(default_factory=list)  # (標題, 原始 markdown)


# ── 解析 ────────────────────────────────────────────────────
def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ReportError("檔案開頭必須是 front-matter（--- 開頭）")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ReportError("front-matter 沒有正確用 --- 結束")
    fm_raw, body = parts[1], parts[2]
    meta: dict = {}
    for line in fm_raw.strip("\n").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue  # 註解行（例：標記某欄位是佔位值，發布當日要改），允許存在、不參與解析
        if ":" not in line:
            raise ReportError(f"front-matter 這行不是 key: value：{line!r}")
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip()
    missing = [k for k in REQUIRED_FRONTMATTER if k not in meta or not meta[k]]
    if missing:
        raise ReportError(f"front-matter 缺欄位：{missing}")
    if not re.fullmatch(r"\d{4}-\d{2}", meta["slug"]):
        raise ReportError(f"slug 格式不對（要 YYYY-NN）：{meta['slug']!r}")
    try:
        meta["report_no"] = int(meta["report_no"])
    except ValueError:
        raise ReportError(f"report_no 必須是整數：{meta['report_no']!r}")
    if len(meta["summary"]) > 120:
        raise ReportError(f"summary 超過 120 字（現 {len(meta['summary'])} 字）")
    # 2026-09-20 指揮部目視手機版單篇頁抓到：published 曾經比 period_end 還早
    # （period_end 誤填季度尾日 2026-09-30，published 佔位 2026-09-24），邏輯上
    # 「發布日期早於資料涵蓋期間結束」講不通——加一道結構性檢查擋住。
    if meta["published"] < meta["period_end"]:
        raise ReportError(
            f"published（{meta['published']!r}）不得早於 period_end"
            f"（{meta['period_end']!r}）——發布日期不能比資料涵蓋期間的結束日還早")
    return meta, body.lstrip("\n")


def _split_preamble(body: str) -> tuple[str, str]:
    """把文首（H1 標題＋粗體中繼資料行）跟第一個 `## ` 之前的部分切出來。"""
    m = re.search(r"(?m)^##\s+", body)
    if not m:
        raise ReportError("找不到任何 `## ` 章節標題")
    return body[: m.start()], body[m.start():]


def parse_preamble(preamble: str) -> tuple[str, list[tuple[str, str]]]:
    lines = [ln.rstrip() for ln in preamble.strip("\n").splitlines()]
    if not lines or not lines[0].startswith("# "):
        raise ReportError("文首第一行必須是 `# 報告標題`")
    h1 = lines[0][2:].strip()
    meta_lines: list[tuple[str, str]] = []
    for ln in lines[1:]:
        ln = ln.strip()
        if not ln or ln == "---":
            continue
        m = _META_LINE.match(ln)
        if m:
            meta_lines.append((m.group(1).strip(), m.group(2).strip()))
    return h1, meta_lines


def parse_sections(body: str) -> list[tuple[str, str]]:
    """依 `## 標題` 切段（`### ` 子標題保留在段落內容裡由渲染器處理）。"""
    chunks = re.split(r"(?m)^##\s+(.+?)\s*$", body)
    sections: list[tuple[str, str]] = []
    seen: set[str] = set()
    for i in range(1, len(chunks), 2):
        title = chunks[i].strip()
        content = chunks[i + 1].strip("\n")
        if title in seen:
            raise ReportError(f"段落標題重複：{title}")
        seen.add(title)
        sections.append((title, content))
    have_prefixes = {p for p in REQUIRED_ANCHOR_PREFIXES
                     for title, _ in sections if title.startswith(p)}
    missing = [p for p in REQUIRED_ANCHOR_PREFIXES if p not in have_prefixes]
    if missing:
        raise ReportError(f"缺少必要錨點小節（比對章節標題開頭）：{missing}")
    return sections


def scan_governance_terms(full_text: str) -> list[str]:
    masked = full_text
    for allowed in GOVERNANCE_ALLOWLIST:
        masked = masked.replace(allowed, "")
    return GOVERNANCE_FORBIDDEN.findall(masked)


def scan_internal_codes(full_text: str) -> list[str]:
    return INTERNAL_CODE_PATTERN.findall(full_text)


def check_numbers_table_has_sources(sections: list[tuple[str, str]]) -> None:
    """「本期數字一覽」表格每一列「出處」欄不可空白。"""
    for title, content in sections:
        if not title.startswith("本期數字一覽"):
            continue
        rows = [ln.strip() for ln in content.splitlines() if ln.strip().startswith("|")]
        data_rows = [r for r in rows if not re.match(r"^\|[\s:-]+\|", r)][1:]  # 去表頭＋分隔列
        for row in data_rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) < 3 or not cells[2]:
                raise ReportError(f"「本期數字一覽」表格有一列缺「出處」：{row!r}")
        return
    raise ReportError("找不到「本期數字一覽」表格可供出處檢查")


def parse_report(md_path: Path) -> Report:
    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    if meta["slug"] != md_path.stem:
        raise ReportError(f"front-matter slug={meta['slug']!r} 與檔名 {md_path.stem!r} 不一致")
    preamble, rest = _split_preamble(body)
    h1, meta_lines = parse_preamble(preamble)
    sections = parse_sections(rest)

    full_text = preamble + rest
    bad_governance = scan_governance_terms(full_text)
    if bad_governance:
        raise ReportError(
            f"正文出現治理內部字樣（{sorted(set(bad_governance))}），"
            f"工作報告是公開文件，這類字樣不得外流；若是合法引用的第三方法定全銜，"
            f"加進 GOVERNANCE_ALLOWLIST 並附理由")
    bad_codes = scan_internal_codes(full_text)
    if bad_codes:
        raise ReportError(f"正文出現內部代號（{sorted(set(bad_codes))}），公開頁不得殘留")
    check_numbers_table_has_sources(sections)

    return Report(
        slug=meta["slug"], title=meta["title"], report_no=meta["report_no"],
        period_start=meta["period_start"], period_end=meta["period_end"],
        published=meta["published"], summary=meta["summary"], status=meta["status"],
        h1=h1, meta_lines=meta_lines, sections=sections,
    )


# ── markdown 片段 → HTML ─────────────────────────────────────
def _todo_bracket(text: str) -> str:
    return _TODO_BRACKET.sub("（出處補充中）", text)


def _inline(text: str) -> str:
    text = _todo_bracket(text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _URL.sub(lambda m: f'<a href="{m.group(0)}" target="_blank" rel="noopener">{m.group(0)}</a>', text)
    return text


def _render_table(rows: list[str]) -> str:
    cell_rows = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
    header, sep, *data = cell_rows
    if not all(re.fullmatch(r":?-{2,}:?", c) for c in sep):
        data = [sep] + data  # 沒有分隔列（理論上不會發生，防呆）
    out = ['<table class="report-table"><thead><tr>']
    out.extend(f"<th>{_inline(c)}</th>" for c in header)
    out.append("</tr></thead><tbody>")
    for row in data:
        out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped or stripped == "---":
            i += 1
            continue
        if stripped.startswith("### "):
            out.append(f"<h3>{_inline(stripped[4:].strip())}</h3>")
            i += 1
            continue
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f'<blockquote><p>{_inline(" ".join(buf))}</p></blockquote>')
            continue
        if stripped.startswith("|"):
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i].strip())
                i += 1
            out.append(_render_table(buf))
            continue
        if _BULLET.match(stripped):
            buf = []
            while i < n and _BULLET.match(lines[i].strip()):
                buf.append(_BULLET.sub("", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in buf) + "</ul>")
            continue
        if _NUMBERED.match(stripped):
            buf = []
            while i < n and _NUMBERED.match(lines[i].strip()):
                buf.append(_NUMBERED.sub("", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{_inline(x)}</li>" for x in buf) + "</ol>")
            continue
        # 一般段落：吃到空行或下一個區塊起始為止
        buf = [stripped]
        i += 1
        while i < n and lines[i].strip() and not (
            lines[i].strip().startswith(("#", ">", "|", "---")) or
            _BULLET.match(lines[i].strip()) or _NUMBERED.match(lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(buf))}</p>")
    return "\n".join(out)


META_ICONS = {
    "發布日期": '<svg class="ic" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
    "涵蓋期間": '<svg class="ic" viewBox="0 0 24 24"><path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/></svg>',
    "發布單位": '<svg class="ic" viewBox="0 0 24 24"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h2"/><path d="M18 14h-8M15 18h-5M10 6h8v4h-8z"/></svg>',
}


def _zh_date(iso: str) -> str:
    """YYYY-MM-DD → 「YYYY 年 M 月 D 日」（月/日不補零，對齊本站草稿一貫寫法）。"""
    y, m, d = iso.split("-")
    return f"{int(y)} 年 {int(m)} 月 {int(d)} 日"


def _release_span(label: str, value: str) -> str:
    icon = META_ICONS.get(label, "")
    return f"<span>{icon} {label}：<strong>{value}</strong></span>"


def render_release_info(meta_lines: list[tuple[str, str]], published: str) -> str:
    """「發布日期」一律用 frontmatter `published` 渲染，不用正文自己那行。

    2026-09-20 指揮部目視手機版單篇頁抓到：正文前言區塊常帶著草稿當天寫的
    「**發布日期**：2026 年 9 月 18 日」，跟 frontmatter `published`（正式發布日，
    可能因審稿延後）不一致，兩者都顯示會讓讀者看到兩個互相矛盾的發布日期。
    正文那行原樣留在真源裡（不改內容），但 build 時略過、一律改插入
    frontmatter `published` 換算的日期，插在原本「發布日期」出現的位置
    （通常是第一條），確保頁面上只有一個、且是權威來源的發布日期。
    """
    spans: list[str] = []
    injected = False
    for label, value in meta_lines:
        if label == "發布日期":
            if not injected:
                spans.append(_release_span("發布日期", _zh_date(published)))
                injected = True
            continue  # 正文重複的發布日期行：略過，不渲染
        spans.append(_release_span(label, _inline(value)))
    if not injected:
        spans.insert(0, _release_span("發布日期", _zh_date(published)))
    return '<div class="release-info">' + "".join(spans) + "</div>"


def render_sections(sections: list[tuple[str, str]]) -> str:
    out = []
    for title, content in sections:
        out.append(f'<section class="report-sec"><h2 class="section-h">{_inline(title)}</h2>')
        out.append(markdown_to_html(content))
        out.append("</section>")
    return "\n".join(out)


# ── HTML 模板（沿用站內新聞稿單篇頁 CSS／nav／footer 慣例，不新寫一套樣式） ──
SINGLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{{TITLE}}｜國教行動聯盟 工作報告</title>
<meta name="description" content="{{SUMMARY}}">
<meta name="keywords" content="國教行動聯盟,AABE,工作報告,倡議成果,{{TITLE}}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{{CANONICAL}}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/wp-content/uploads/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/wp-content/uploads/apple-touch-icon.png">
<meta name="theme-color" content="#0a0a0a">

<meta property="og:title" content="{{TITLE}}｜國教行動聯盟 工作報告">
<meta property="og:description" content="{{SUMMARY}}">
<meta property="og:image" content="https://aabe.org.tw/wp-content/uploads/og-about.jpg">
<meta property="og:type" content="article">
<meta property="og:url" content="{{CANONICAL}}">
<meta property="og:site_name" content="國教行動聯盟">
<meta property="og:locale" content="zh_TW">
<meta property="article:published_time" content="{{PUBLISHED}}T09:00:00+08:00">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{TITLE}}">
<meta name="twitter:description" content="{{SUMMARY}}">
<meta name="twitter:image" content="https://aabe.org.tw/wp-content/uploads/og-about.jpg">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800;900&family=Noto+Sans+TC:wght@400;500;700;900&family=Noto+Serif+TC:wght@400;500;700;900&display=swap" rel="stylesheet">

<style>
* { box-sizing: border-box; }
body {
  font-family: "Noto Serif TC", "PingFang TC", "Microsoft JhengHei", "Songti TC", serif;
  line-height: 1.85;
  color: #1a1a1a;
  background: #f4f4f0;
  margin: 0;
  -webkit-font-smoothing: antialiased;
}
.press-topbar { background: #0a0a0a; color: #f4f4f0; padding: 14px 28px; border-bottom: 4px solid #9A5A0C; }
.press-topbar-inner { max-width: 920px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.press-topbar .org { font-weight: 800; font-size: 1rem; letter-spacing: 1px; }
.press-topbar .org-en { font-size: 0.78rem; color: #9ca3af; font-family: Georgia, serif; font-style: italic; }
.press-topbar .meta { font-size: 0.85rem; color: #d1d5db; letter-spacing: 1px; }
article { max-width: 760px; margin: 0 auto; background: #ffffff; padding: 48px 56px 64px; box-shadow: 0 0 24px rgba(0,0,0,0.06); position: relative; }
.doc-mark { display: inline-block; background: #9A5A0C; color: #fff; padding: 5px 14px; font-size: 0.8rem; letter-spacing: 2px; font-weight: 700; margin-bottom: 18px; }
.title-group { border-bottom: 3px double #1a1a1a; padding-bottom: 24px; margin-bottom: 28px; }
h1.headline { font-size: 2.1rem; font-weight: 800; line-height: 1.4; margin: 8px 0 14px; color: #0a0a0a; letter-spacing: -0.5px; }
.subheadline { font-size: 1.15rem; font-weight: 700; color: #1a1a1a; margin: 6px 0; line-height: 1.6; }
.title-group .kicker { display: block; font-size: 0.85rem; font-weight: 700; color: #9A5A0C; letter-spacing: 1px; margin: 0 0 8px; }
.release-info { display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 28px; padding: 14px 0; border-bottom: 1px solid #e5e7eb; font-size: 0.92rem; color: #4b5563; }
.release-info span { display: inline-flex; align-items: center; gap: 6px; }
.release-info strong { color: #0a0a0a; }
p { font-size: 1rem; line-height: 1.95; margin: 18px 0; color: #1a1a1a; text-align: justify; }
h2.section-h { font-size: 1.4rem; font-weight: 800; color: #0a0a0a; margin: 40px 0 14px; padding-bottom: 8px; border-bottom: 2px solid #9A5A0C; letter-spacing: -0.3px; }
h3 { font-size: 1.1rem; font-weight: 800; color: #0a0a0a; margin: 26px 0 10px; }
strong { color: #0a0a0a; }
ul, ol { padding-left: 26px; }
li { margin: 6px 0; }
blockquote { margin: 28px 0; padding: 18px 22px; border-left: 4px solid #9A5A0C; background: #fff7ed; color: #7c2d12; line-height: 1.8; }
blockquote p { margin: 0; font-style: italic; font-size: 1.02rem; }
table.report-table { width: 100%; border-collapse: collapse; margin: 18px 0; font-size: 0.92rem; }
table.report-table th, table.report-table td { border: 1px solid #e5e7eb; padding: 8px 10px; text-align: left; vertical-align: top; }
table.report-table th { background: #f4f4f0; font-weight: 800; }
.report-sec a { color: #1d4ed8; text-decoration: none; word-break: break-all; }
.report-sec a:hover { text-decoration: underline; }
.contact-section { margin-top: 48px; padding: 22px 26px; background: #f4f4f0; border: 1px solid #d1d5db; }
.contact-section h3 { margin: 0 0 12px; font-size: 1rem; font-weight: 800; color: #0a0a0a; letter-spacing: 1px; }
.contact-section ul { list-style: none; padding: 0; margin: 0; }
.contact-section li { padding: 6px 0; font-size: 0.95rem; color: #1a1a1a; }
.contact-section li strong { color: #9A5A0C; }
.press-footer { max-width: 760px; margin: 0 auto; padding: 28px 56px 40px; text-align: center; font-size: 0.82rem; color: #6b7280; letter-spacing: 1px; }
.press-footer .line { display: block; margin: 4px 0; }
.press-footer a { color: #4b5563; text-decoration: underline; text-underline-offset: 2px; }
.ic { display: inline-block; width: 1em; height: 1em; vertical-align: -0.125em; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; margin-right: .35em; }
@media (max-width: 768px) {
  article { padding: 32px 20px 48px; }
  h1.headline { font-size: 1.5rem; }
  .subheadline { font-size: 1.05rem; }
  .press-footer { padding: 24px 16px 32px; }
  table.report-table { font-size: 0.82rem; }
  table.report-table th, table.report-table td { padding: 6px 6px; }
}
</style>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NGO",
  "@id": "https://aabe.org.tw/#organization",
  "name": "國教行動聯盟",
  "alternateName": ["國教盟", "AABE", "Action Alliance on Basic Education"],
  "url": "https://aabe.org.tw/",
  "logo": {"@type": "ImageObject", "url": "https://aabe.org.tw/wp-content/uploads/logo-naer.png", "width": 600, "height": 600},
  "description": "成立於 2012 年的台灣兒少與教育倡議民間團體，長期關注校園安全、兒少保護、教育改革、青少年身心健康，並推動以家庭與學校為核心的兒少政策與整合治理。",
  "foundingDate": "2012-06-26",
  "sameAs": ["https://www.facebook.com/twedumove/", "https://zh.wikipedia.org/wiki/國教行動聯盟"],
  "areaServed": {"@type": "Country", "name": "TW"}
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Report",
  "@id": "{{CANONICAL}}",
  "name": "{{TITLE}}",
  "description": "{{SUMMARY}}",
  "author": {"@type": "Organization", "@id": "https://aabe.org.tw/#organization", "name": "國教行動聯盟"},
  "publisher": {"@type": "Organization", "name": "國教行動聯盟", "logo": {"@type": "ImageObject", "url": "https://aabe.org.tw/wp-content/uploads/logo-naer.png"}},
  "datePublished": "{{PUBLISHED}}",
  "temporalCoverage": "{{PERIOD_START}}/{{PERIOD_END}}",
  "mainEntityOfPage": {"@type": "WebPage", "@id": "{{CANONICAL}}"},
  "inLanguage": "zh-TW"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "首頁", "item": "https://aabe.org.tw/"},
    {"@type": "ListItem", "position": 2, "name": "工作報告", "item": "https://aabe.org.tw/reports/"},
    {"@type": "ListItem", "position": 3, "name": "{{TITLE}}", "item": "{{CANONICAL}}"}
  ]
}
</script>
</head>
<body data-pagefind-body>
<span data-pagefind-filter="type:工作報告" hidden></span>
<span data-pagefind-meta="date:{{PUBLISHED}}" hidden></span>

<header class="press-topbar" data-pagefind-ignore>
  <div class="press-topbar-inner">
    <div>
      <div class="org"><a href="https://aabe.org.tw/" style="color:inherit;text-decoration:none" aria-label="回國教行動聯盟官網">國教行動聯盟</a></div>
      <div class="org-en">Action Alliance on Basic Education (AABE)</div>
    </div>
    <div class="meta">WORK REPORT　│　{{PUBLISHED}}</div>
  </div>
</header>

<article>
  <div class="doc-mark">工作報告</div>
  <div class="title-group">
    <p class="kicker">國教行動聯盟 工作報告專區</p>
    <h1 class="headline">{{TITLE}}</h1>
    <p class="subheadline">{{H1}}</p>
  </div>

  {{RELEASE_INFO}}

  {{SECTIONS}}

  <section class="contact-section">
    <h3><svg class="ic" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg> 聯絡窗口</h3>
    <ul>
      <li>國教行動聯盟理事長 <strong>王瀚陽</strong>　電話 0983-097-165</li>
    </ul>
  </section>
</article>

<footer class="press-footer" data-pagefind-ignore>
  <span class="line"><a href="https://aabe.org.tw/">國教行動聯盟官網</a>　·　<a href="https://aabe.org.tw/reports/">更多工作報告</a></span>
  <span class="line">© 2026 國教行動聯盟 ‧ Action Alliance on Basic Education（民間團體）</span>
  <span class="line">本報告可於註明出處後自由引用</span>
</footer>

</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>工作報告｜國教行動聯盟 Work Reports</title>
  <meta name="description" content="國教行動聯盟定期公開工作報告：出席場次、新聞稿與聲明、發函陳情、階段性成果，逐季彙整，供夥伴組織、媒體與公眾查閱。">
  <meta name="keywords" content="國教行動聯盟,AABE,工作報告,倡議成果,季報,work reports">
  <meta name="robots" content="index,follow,max-image-preview:large">

  <link rel="canonical" href="https://aabe.org.tw/reports/">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="/wp-content/uploads/favicon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/wp-content/uploads/apple-touch-icon.png">
  <meta name="theme-color" content="#0a0a0a">

  <meta property="og:title" content="工作報告｜國教行動聯盟">
  <meta property="og:description" content="出席場次、新聞稿與聲明、發函陳情、階段性成果，逐季彙整公開。">
  <meta property="og:image" content="https://aabe.org.tw/wp-content/uploads/og-about.jpg">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://aabe.org.tw/reports/">
  <meta property="og:site_name" content="國教行動聯盟">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="工作報告｜國教行動聯盟">
  <meta name="twitter:description" content="出席場次、新聞稿與聲明、發函陳情、階段性成果，逐季彙整公開。">
  <meta name="twitter:image" content="https://aabe.org.tw/wp-content/uploads/og-about.jpg">

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "工作報告｜國教行動聯盟",
    "description": "國教行動聯盟定期公開工作報告，逐季彙整出席場次、新聞稿與聲明、發函陳情、階段性成果。",
    "url": "https://aabe.org.tw/reports/",
    "inLanguage": "zh-TW"
  }
  </script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800;900&family=Noto+Sans+TC:wght@400;500;700;900&family=Noto+Serif+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/aabe.css?v=20260518">

  <style>
    .reports-hero { padding: 64px 24px 24px; max-width: 1040px; margin: 0 auto; }
    .reports-grid {
      max-width: 1040px; margin: 0 auto 80px; padding: 0 24px;
      display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 24px;
    }
    .report-card {
      border: 1px solid #e5e7eb; border-radius: 4px; padding: 24px;
      display: flex; flex-direction: column; gap: 10px; background: #fff;
    }
    .report-card h3 { font-family: 'Noto Serif TC', serif; font-size: 1.2rem; font-weight: 900; line-height: 1.4; margin: 0; }
    .report-card .rc-period { font-size: 0.82rem; color: var(--ink-2, #6b7280); }
    .report-card .rc-summary { font-size: 0.92rem; color: #374151; line-height: 1.7; margin: 0; }
    .report-card .rc-links { margin-top: auto; display: flex; gap: 14px; font-size: 0.88rem; font-weight: 700; }
    .report-card .rc-links a { color: #9A5A0C; }
  </style>
</head>
<body data-pagefind-body>

<header class="topbar">
  <div class="topbar-inner">
    <a href="/" class="topbar-logo">
      <picture>
        <source media="(max-width: 768px)" srcset="/wp-content/uploads/logo-naer-icon-only.png">
        <img src="/wp-content/uploads/logo-naer.png" alt="國教行動聯盟｜Action Alliance on Basic Education">
      </picture>
    </a>
    <button type="button" class="nav-toggle-btn" aria-label="開啟選單" aria-expanded="false" aria-controls="topbar-nav"><span></span></button>
    <nav class="topbar-nav" id="topbar-nav" aria-label="Primary">
      <a href="/about/">關於我們</a>
      <a href="/issues/">我們關注的議題</a>
      <a href="/events/" class="nav-events">活動公告<span class="nav-dot"></span></a>
      <a href="/chronicle/">大事紀</a>
      <a href="/act/">行動與參與</a>
      <a href="/press/">媒體與資料</a>
      <a href="/contact/">聯絡我們</a>
    </nav>
  </div>
</header>

<main id="main">

  <section class="reports-hero">
    <span class="kicker">Work Reports · 工作報告</span>
    <h1>工作報告</h1>
    <p class="lead">國教行動聯盟定期公開工作報告：出席場次、新聞稿與聲明、發函陳情、階段性成果，逐季彙整，供夥伴組織、媒體與公眾查閱。</p>
  </section>

  <section class="reports-grid">
{{CARDS}}
  </section>

</main>

<footer>
  <div class="footer-inner">
    <div class="footer-cols">
      <div class="footer-col">
        <h4>國教行動聯盟</h4>
        <p style="color:#b8bcc3;font-size:0.92rem;line-height:1.7;">成立於 2012 年的台灣兒少與教育倡議組織（家長 × 青年共構），由內政部人民團體立案。</p>
      </div>
      <div class="footer-col">
        <h4>議題</h4>
        <a href="/issues/">我們關注的議題</a>
        <a href="/chronicle/">大事紀</a>
        <a href="/events/">活動公告</a>
      </div>
      <div class="footer-col">
        <h4>給專業用戶</h4>
        <a href="/press/">媒體中心</a>
        <a href="/reports/">工作報告</a>
        <a href="https://policy.aabe.org.tw/">政策資料庫</a>
        <a href="https://advocacy.aabe.org.tw/">倡議成果資料庫</a>
      </div>
      <div class="footer-col">
        <h4>聯絡</h4>
        <a href="/contact/">聯絡我們</a>
        <a href="mailto:Action.A.E0626@gmail.com">Action.A.E0626@gmail.com</a>
        <a href="https://www.facebook.com/twedumove/" target="_blank" rel="noopener">Facebook</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 國教行動聯盟｜統編 41142910｜立案字號 1030182063</span>
      <span><a href="/methodology/" style="color:#b8bcc3;border-bottom:1px solid #2a2a2a;">資料方法</a> · <a href="/llms.txt" style="color:#b8bcc3;border-bottom:1px solid #2a2a2a;">llms.txt</a></span>
    </div>
  </div>
</footer>

</body>
</html>
"""


def render_single(report: Report) -> str:
    canonical = f"https://aabe.org.tw/reports/{report.slug}/"
    html = SINGLE_TEMPLATE
    html = html.replace("{{TITLE}}", report.title)
    html = html.replace("{{SUMMARY}}", report.summary)
    html = html.replace("{{CANONICAL}}", canonical)
    html = html.replace("{{PUBLISHED}}", report.published)
    html = html.replace("{{PERIOD_START}}", report.period_start)
    html = html.replace("{{PERIOD_END}}", report.period_end)
    html = html.replace("{{H1}}", _inline(report.h1))
    html = html.replace("{{RELEASE_INFO}}", render_release_info(report.meta_lines, report.published))
    html = html.replace("{{SECTIONS}}", render_sections(report.sections))
    return html


def render_card(report: Report) -> str:
    period = f"{report.period_start} ～ {report.period_end}"
    return (
        '    <article class="report-card">\n'
        f'      <h3><a href="/reports/{report.slug}/">{report.title}</a></h3>\n'
        f'      <span class="rc-period">涵蓋期間 {period}　·　發布 {report.published}</span>\n'
        f'      <p class="rc-summary">{_inline(report.summary)}</p>\n'
        '      <div class="rc-links">\n'
        f'        <a href="/reports/{report.slug}/">閱讀全文</a>\n'
        '      </div>\n'
        '    </article>'
    )


def render_index(reports: list[Report]) -> str:
    ordered = sorted(reports, key=lambda r: r.report_no, reverse=True)
    cards = "\n".join(render_card(r) for r in ordered)
    return INDEX_TEMPLATE.replace("{{CARDS}}", cards)


# ── 主流程 ───────────────────────────────────────────────────
def load_all_reports() -> list[Report]:
    md_paths = sorted(REPORTS_DIR.glob("*.md"))
    return [parse_report(p) for p in md_paths]


def build_one(md_path: Path, *, dry_run: bool = False) -> Path:
    report = parse_report(md_path)
    html = render_single(report)
    out_dir = OUT_DIR / report.slug
    out_html = out_dir / "index.html"
    if dry_run:
        print(f"[dry-run] 會寫 {out_html}")
        return out_html
    out_dir.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    print(f"已產生：{out_html}")
    return out_html


def build_index(*, dry_run: bool = False) -> Path:
    reports = load_all_reports()
    if not reports:
        raise ReportError("_source/reports/ 下沒有任何 *.md，無法產生列表頁")
    html = render_index(reports)
    out_html = OUT_DIR / "index.html"
    if dry_run:
        print(f"[dry-run] 會寫 {out_html}（{len(reports)} 篇）")
        return out_html
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    print(f"已產生：{out_html}（{len(reports)} 篇）")
    return out_html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*", help="要產生的報告 slug（不帶副檔名）；不給就全部")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.slugs:
        md_paths = [REPORTS_DIR / f"{slug}.md" for slug in args.slugs]
        missing = [p for p in md_paths if not p.exists()]
        if missing:
            print(f"找不到檔案：{missing}", file=sys.stderr)
            return 1
    else:
        md_paths = sorted(REPORTS_DIR.glob("*.md"))

    if not md_paths:
        print("沒有要產生的報告（_source/reports/ 下沒有 *.md）", file=sys.stderr)
        return 1

    try:
        for md_path in md_paths:
            build_one(md_path, dry_run=args.dry_run)
        # 單篇或全部，一律重建列表頁（列表頁要涵蓋 _source/reports/ 下全部報告）
        build_index(dry_run=args.dry_run)
    except ReportError as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

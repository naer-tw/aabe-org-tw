#!/usr/bin/env python3
"""build_briefs.py — 把 _source/briefs/<issue>.md 轉成一頁 A4 政策摘要 PDF＋HTML。

依據：交接包 `MAC的技能與工具中心/shared/HANDOFFS/2026-09-14_官網第三批_交接包.md`
第三批②；格式說明見 `_source/briefs/README.md`。

流程：
    _source/briefs/<issue>.md
        → 解析 front-matter（issue/title/updated/contact）＋ 七個固定 `## ` 段落
        → 數字 `{{metric:<id>}}` 對照 _source/numbers.json，查無即中止（不生半成品）
        → 套 _source/briefs/_template.html
        → 寫 public/briefs/<issue>/index.html
        → 用 Playwright（本機 venv `~/.venvs/aabe-pw`，缺套件時自動 os.execv 切換過去；
          都不可用才退回 WeasyPrint）輸出 public/briefs/<issue>.pdf

用法：
    python3 _source/deploy-automation/build_briefs.py               # 全部 *.md
    python3 _source/deploy-automation/build_briefs.py school-lunch  # 單一議題
    python3 _source/deploy-automation/build_briefs.py --dry-run school-lunch
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BRIEFS_DIR = REPO / "_source" / "briefs"
TEMPLATE_PATH = BRIEFS_DIR / "_template.html"
NUMBERS_PATH = REPO / "_source" / "numbers.json"
PUBLIC_DIR = REPO / "public"
LOGO_FILE = PUBLIC_DIR / "wp-content" / "uploads" / "logo-naer.png"

SECTION_ORDER = [
    "問題",
    "具體建議",
    "需協作機關",
    "國教盟已做",
    "原始來源",
    "更新日期",
    "合作窗口",
]
REQUIRED_FRONTMATTER = ("issue", "title", "updated", "contact")

_METRIC_TOKEN = re.compile(r"\{\{\s*metric:([a-zA-Z0-9_]+)\s*\}\}")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_HTML_COMMENT = re.compile(r"^<!--.*-->$")
_SRC_LINE = re.compile(r"^-\s*(.+?)：\s*(https?://\S+)\s*$")


class BriefError(RuntimeError):
    """來源 markdown 有問題（缺欄位、metric 查無、段落標題不對）時丟出，中止產出。"""


@dataclass
class Brief:
    issue: str
    title: str
    updated: str
    contact: str
    sections: dict  # 標題 -> 原始 markdown 內容（含 HTML 註解）


# ── logo ─────────────────────────────────────────────────────
def logo_data_uri(path: Path = LOGO_FILE) -> str:
    """把 logo 內嵌成 base64 data URI。

    緣由（2026-09-15 理事長回饋）：模板原本用絕對路徑 `/wp-content/uploads/
    logo-naer.png`——這條路徑在正式站（served from https://aabe.org.tw/）
    解得到，但 build_briefs.py 是用 `page.goto(html_path.as_uri())` 直接開
    file:// 本機檔案來產 PDF／HTML，`/wp-content/...` 在 file:// 底下會被
    解成檔案系統根目錄，logo 讀不到、只剩 alt 文字。內嵌 base64 後，HTML／
    PDF 兩種輸出都自帶圖檔，不依賴用什麼方式開頁面，之後也不用另外跑
    http.server。
    """
    if not path.exists():
        raise BriefError(f"logo 檔案不存在：{path}")
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ── 解析 ────────────────────────────────────────────────────
def load_metrics(path: Path = NUMBERS_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {m["id"]: m for m in data["metrics"]}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise BriefError("檔案開頭必須是 front-matter（--- 開頭）")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise BriefError("front-matter 沒有正確用 --- 結束")
    fm_raw, body = parts[1], parts[2]
    meta: dict = {}
    for line in fm_raw.strip("\n").splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise BriefError(f"front-matter 這行不是 key: value：{line!r}")
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip()
    missing = [k for k in REQUIRED_FRONTMATTER if k not in meta or not meta[k]]
    if missing:
        raise BriefError(f"front-matter 缺欄位：{missing}")
    return meta, body.lstrip("\n")


def parse_sections(body: str) -> dict:
    """依 `## 標題` 切段，標題必須逐字等於 SECTION_ORDER 全部七個、順序不限但不可缺漏或多餘。"""
    chunks = re.split(r"(?m)^##\s+(.+?)\s*$", body)
    # re.split 帶捕獲群組時回傳 [前段, 標題1, 內容1, 標題2, 內容2, ...]
    if chunks[0].strip():
        raise BriefError(f"第一個 `## ` 標題之前不該有內容：{chunks[0].strip()[:40]!r}")
    sections: dict[str, str] = {}
    for i in range(1, len(chunks), 2):
        title = chunks[i].strip()
        content = chunks[i + 1].strip("\n")
        if title in sections:
            raise BriefError(f"段落標題重複：{title}")
        sections[title] = content
    missing = [t for t in SECTION_ORDER if t not in sections]
    extra = [t for t in sections if t not in SECTION_ORDER]
    if missing:
        raise BriefError(f"缺少固定段落：{missing}")
    if extra:
        raise BriefError(f"出現不在七項固定欄位裡的段落：{extra}")
    return sections


def parse_brief(md_path: Path) -> Brief:
    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    if meta["issue"] != md_path.stem:
        raise BriefError(f"front-matter issue={meta['issue']!r} 與檔名 {md_path.stem!r} 不一致")
    sections = parse_sections(body)
    # 「更新日期」「合作窗口」段落是給人看的正文，但真值以 front-matter 為單一來源，
    # 兩邊必須一致，避免之後各自被改而分岔。
    plain_updated = strip_markup(sections["更新日期"]).strip()
    plain_contact = strip_markup(sections["合作窗口"]).strip()
    if plain_updated != meta["updated"]:
        raise BriefError(
            f"「更新日期」段落寫的是 {plain_updated!r}，與 front-matter updated="
            f"{meta['updated']!r} 不一致")
    if plain_contact != meta["contact"]:
        raise BriefError(
            f"「合作窗口」段落寫的是 {plain_contact!r}，與 front-matter contact="
            f"{meta['contact']!r} 不一致")
    return Brief(issue=meta["issue"], title=meta["title"], updated=meta["updated"],
                 contact=meta["contact"], sections=sections)


def strip_markup(text: str) -> str:
    text = _HTML_COMMENT.sub("", text)
    text = _METRIC_TOKEN.sub(lambda m: m.group(1), text)
    text = re.sub(r"<[^>]+>", "", text)
    text = _BOLD.sub(r"\1", text)
    return text.strip()


# ── 數字代換 ─────────────────────────────────────────────────
def render_metrics(text: str, metrics: dict) -> str:
    def sub(m: re.Match) -> str:
        metric_id = m.group(1)
        metric = metrics.get(metric_id)
        if metric is None:
            raise BriefError(
                f"{{{{metric:{metric_id}}}}} 在 _source/numbers.json 裡查無此 id"
                f"（禁止憑記憶填數字，查不到就是不能上稿）")
        return f'<span data-metric="{metric_id}">{metric["display"]}</span>'
    return _METRIC_TOKEN.sub(sub, text)


# ── markdown 片段 → HTML（只支援本專案實際用到的最小子集） ─────
def _inline(text: str) -> str:
    return _BOLD.sub(r"<strong>\1</strong>", text)


def md_block_to_html(md: str, *, as_sources: bool = False) -> str:
    """把一個段落的 markdown 轉 HTML；保留 HTML 註解（出處標記）在輸出碼裡。"""
    lines = [ln for ln in md.split("\n")]
    out: list[str] = []
    buf_list: list[str] = []

    def flush_list():
        if not buf_list:
            return
        cls = ' class="src-list"' if as_sources else ""
        out.append(f"<ul{cls}>")
        out.extend(buf_list)
        out.append("</ul>")
        buf_list.clear()

    buf_para: list[str] = []

    def flush_para():
        if not buf_para:
            return
        out.append(f"<p>{_inline(' '.join(buf_para))}</p>")
        buf_para.clear()

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_list()
            flush_para()
            continue
        if _HTML_COMMENT.match(line):
            flush_list()
            flush_para()
            out.append(line)  # 出處註解原樣保留，供之後回溯
            continue
        if line.startswith("- "):
            flush_para()
            item = line[2:].strip()
            if as_sources:
                m = _SRC_LINE.match(line)
                if not m:
                    raise BriefError(f"原始來源這行格式不對（要「- 標籤：https://…」）：{line!r}")
                label, url = m.group(1), m.group(2)
                buf_list.append(f"<li><b>{_inline(label)}</b><a href=\"{url}\" "
                                 f"target=\"_blank\" rel=\"noopener\">{url}</a></li>")
            else:
                buf_list.append(f"<li>{_inline(item)}</li>")
            continue
        flush_list()
        buf_para.append(line)
    flush_list()
    flush_para()
    return "\n".join(out)


def render_section(title: str, raw_md: str, metrics: dict) -> str:
    substituted = render_metrics(raw_md, metrics)
    if title == "原始來源":
        return md_block_to_html(substituted, as_sources=True)
    if title == "國教盟已做":
        # 第一段（如果不是列表）當成帶 metric 的引言句，套較淡的樣式
        parts = substituted.split("\n\n", 1)
        if len(parts) == 2 and not parts[0].lstrip().startswith("-") \
                and not _HTML_COMMENT.match(parts[0].strip()):
            intro_html = md_block_to_html(parts[0]).replace("<p>", '<p class="sec-metric-line">', 1)
            rest_html = md_block_to_html(parts[1])
            return intro_html + "\n" + rest_html
        return md_block_to_html(substituted)
    return md_block_to_html(substituted)


# ── PDF 引擎 ─────────────────────────────────────────────────
def render_pdf_playwright(html_path: Path, pdf_path: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        venv_python = Path.home() / ".venvs" / "aabe-pw" / "bin" / "python3"
        if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        raise
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri())
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        finally:
            browser.close()


def render_pdf_weasyprint(html_path: Path, pdf_path: Path) -> None:
    try:
        import weasyprint
    except ImportError as e:
        raise BriefError(
            "Playwright 不可用，且系統沒裝 WeasyPrint。"
            "請跑 `pip install weasyprint`（或修好 ~/.venvs/aabe-pw 的 playwright）"
        ) from e
    weasyprint.HTML(filename=str(html_path)).write_pdf(str(pdf_path))


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    try:
        render_pdf_playwright(html_path, pdf_path)
    except ImportError:
        render_pdf_weasyprint(html_path, pdf_path)


# ── 主流程 ───────────────────────────────────────────────────
def build_one(md_path: Path, *, metrics: dict, template: str, dry_run: bool = False) -> Path:
    brief = parse_brief(md_path)
    html = template
    html = html.replace("{{TITLE}}", brief.title)
    html = html.replace("{{CANONICAL}}", f"https://aabe.org.tw/briefs/{brief.issue}/")
    html = html.replace("{{LOGO_SRC}}", logo_data_uri())
    html = html.replace("{{SEC_PROBLEM}}", render_section("問題", brief.sections["問題"], metrics))
    html = html.replace("{{SEC_RECOMMEND}}", render_section("具體建議", brief.sections["具體建議"], metrics))
    html = html.replace("{{SEC_AGENCIES}}", render_section("需協作機關", brief.sections["需協作機關"], metrics))
    html = html.replace("{{SEC_DONE}}", render_section("國教盟已做", brief.sections["國教盟已做"], metrics))
    html = html.replace("{{SEC_SOURCES}}", render_section("原始來源", brief.sections["原始來源"], metrics))
    html = html.replace("{{SEC_UPDATED}}", brief.updated)
    html = html.replace("{{SEC_CONTACT}}", brief.contact)

    out_dir = PUBLIC_DIR / "briefs" / brief.issue
    out_html = out_dir / "index.html"
    out_pdf = PUBLIC_DIR / "briefs" / f"{brief.issue}.pdf"

    if dry_run:
        print(f"[dry-run] 會寫 {out_html} 與 {out_pdf}")
        return out_html

    out_dir.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    render_pdf(out_html, out_pdf)
    print(f"已產生：{out_html}")
    print(f"已產生：{out_pdf}")
    return out_html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("issues", nargs="*", help="要產生的議題 slug（不帶副檔名）；不給就全部")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    metrics = load_metrics()
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    if args.issues:
        md_paths = [BRIEFS_DIR / f"{issue}.md" for issue in args.issues]
        missing = [p for p in md_paths if not p.exists()]
        if missing:
            print(f"找不到檔案：{missing}", file=sys.stderr)
            return 1
    else:
        md_paths = sorted(BRIEFS_DIR.glob("*.md"))
        md_paths = [p for p in md_paths if p.name != "README.md"]

    if not md_paths:
        print("沒有要產生的議題（_source/briefs/ 下沒有 *.md）", file=sys.stderr)
        return 1

    try:
        for md_path in md_paths:
            build_one(md_path, metrics=metrics, template=template, dry_run=args.dry_run)
    except BriefError as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

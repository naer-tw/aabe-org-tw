"""build_reports.py 驗收：frontmatter 必填、三錨點小節齊、治理內部字樣＝0、
內部代號＝0、「本期數字一覽」出處欄不可空白、slug 格式、列表頁含每篇、
產出 HTML 無「【」殘留。

跟 test_briefs.py 同一套模式：純解析/掃描邏輯不需要 Playwright，一律跑；
端對端（真的跑一次 build_reports.py 子行程）需要 Playwright，缺套件時 SKIP。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import build_reports as br


# ── 純解析／掃描邏輯：不需要 Playwright ─────────────────────────
def test_parse_frontmatter_requires_all_fields():
    text = "---\nslug: 2026-01\ntitle: t\n---\n# H\n## 摘要\nx\n"
    with pytest.raises(br.ReportError, match="缺欄位"):
        br.parse_frontmatter(text)


def test_parse_frontmatter_rejects_bad_slug():
    text = ("---\nslug: 2026q1\ntitle: t\nreport_no: 1\nperiod_start: 2026-01-01\n"
            "period_end: 2026-03-31\npublished: 2026-04-01\nsummary: s\nstatus: draft\n---\n"
            "# H\n## 摘要\nx\n## 本期數字一覽\n| a | b | c |\n|---|---|---|\n| x | y | z |\n"
            "## 參考資料\nx\n")
    with pytest.raises(br.ReportError, match="slug 格式不對"):
        br.parse_frontmatter(text)


def test_parse_frontmatter_rejects_summary_over_120_chars():
    long_summary = "字" * 121
    text = (f"---\nslug: 2026-01\ntitle: t\nreport_no: 1\nperiod_start: 2026-01-01\n"
            f"period_end: 2026-03-31\npublished: 2026-04-01\nsummary: {long_summary}\nstatus: draft\n---\n"
            "# H\n## 摘要\nx\n")
    with pytest.raises(br.ReportError, match="超過 120 字"):
        br.parse_frontmatter(text)


def test_parse_sections_requires_three_anchor_prefixes():
    body = "## 摘要\nx\n## 一、亮點\ny\n"
    with pytest.raises(br.ReportError, match="缺少必要錨點小節"):
        br.parse_sections(body)


def test_parse_sections_accepts_free_middle_sections_and_anchor_suffix():
    body = ("## 摘要\nx\n## 一、亮點\ny\n## 二、細節\nz\n"
            "## 本期數字一覽\nw\n## 參考資料｜供查證\nv\n")
    sections = br.parse_sections(body)
    titles = [t for t, _ in sections]
    assert titles == ["摘要", "一、亮點", "二、細節", "本期數字一覽", "參考資料｜供查證"]


def test_governance_forbidden_words_are_caught():
    bad = br.scan_governance_terms("本會理監事決議通過此案，經表決一致同意。")
    assert set(bad) >= {"理監事", "決議", "表決"}


def test_governance_allowlist_masks_third_party_legal_name():
    """財團法人厚生基金會是立法院厚生會敦聘單位的真實法定全銜（外部機關），
    不是本聯盟自稱「財團法人」，allowlist 遮蔽後不應誤判。"""
    text = "敦聘單位為委員會召集人與財團法人厚生基金會董事長詹火生。"
    assert br.scan_governance_terms(text) == []


def test_governance_allowlist_does_not_blanket_exempt_bare_term():
    """allowlist 只遮蔽整段「財團法人厚生基金會」，若本聯盟自己被寫成「財團法人」
    （不接厚生基金會），仍要抓到——防止 allowlist 設計成誤殺免死金牌。"""
    text = "國教行動聯盟為財團法人，依法辦理年度決算。"
    assert "財團法人" in br.scan_governance_terms(text)


def test_internal_code_pattern_is_caught():
    bad = br.scan_internal_codes("本案對應 B12 與 CMT 決議，另見 A7 附件。")
    assert set(bad) >= {"B12", "CMT", "A7"}


def test_internal_code_pattern_is_caught_when_flush_against_chinese_text():
    """真實寫法常見「見B12附件」這種代號緊貼中文、沒有空格——Python re 把 CJK
    字元也算進 \\w，若用 \\b 邊界會在這種最常見寫法上失效，因此代號本身不能靠 \\b。"""
    bad = br.scan_internal_codes("詳見B12附件與相關決議，另查A7六輪攻防紀錄。")
    assert set(bad) >= {"B12", "A7"}


def test_internal_code_pattern_does_not_false_positive_on_ordinary_text():
    """常見中英夾雜或代碼（如 ADHD、114 萬元）不該被 B\\d+/A\\d+ 誤判。"""
    assert br.scan_internal_codes("ADHD 盛行率、114 萬元、兒少未來帳戶條例") == []


def test_check_numbers_table_rejects_empty_source_cell():
    sections = [("本期數字一覽", "| 項目 | 數值 | 出處 |\n|---|---|---|\n| a | 1 | |\n")]
    with pytest.raises(br.ReportError, match="缺「出處」"):
        br.check_numbers_table_has_sources(sections)


def test_check_numbers_table_accepts_filled_source_cell():
    sections = [("本期數字一覽", "| 項目 | 數值 | 出處 |\n|---|---|---|\n| a | 1 | 秘書處紀錄 |\n")]
    br.check_numbers_table_has_sources(sections)  # 不丟例外即通過


def test_todo_bracket_renders_as_source_pending_note():
    out = br._inline("已出版【出處待補：待補充】")
    assert out == "已出版（出處補充中）"
    assert "【" not in out


def test_markdown_to_html_renders_table_list_blockquote_and_h3():
    md = (
        "### 子標題\n\n"
        "- 項目一\n- 項目二\n\n"
        "1. 第一點\n2. 第二點\n\n"
        "> 引言句\n\n"
        "| 欄一 | 欄二 |\n|---|---|\n| a | b |\n\n"
        "一般段落 **粗體** 文字，含連結 https://example.com/page 。\n"
    )
    html = br.markdown_to_html(md)
    assert "<h3>子標題</h3>" in html
    assert "<ul><li>項目一</li><li>項目二</li></ul>" in html
    assert "<ol><li>第一點</li><li>第二點</li></ol>" in html
    assert "<blockquote><p>引言句</p></blockquote>" in html
    assert '<table class="report-table">' in html
    assert "<th>欄一</th>" in html and "<td>a</td>" in html
    assert "<strong>粗體</strong>" in html
    assert '<a href="https://example.com/page"' in html


def test_2026_03_report_parses_and_matches_frontmatter(repo_root: Path):
    report = br.parse_report(repo_root / "_source" / "reports" / "2026-03.md")
    assert report.slug == "2026-03"
    assert report.report_no == 3
    assert report.period_start == "2026-06-01"
    assert report.period_end == "2026-09-30"
    assert len(report.summary) <= 120
    titles = [t for t, _ in report.sections]
    assert any(t.startswith("摘要") for t in titles)
    assert any(t.startswith("本期數字一覽") for t in titles)
    assert any(t.startswith("參考資料") for t in titles)


# ── 端對端：需要 Playwright 環境（缺套件則 SKIP，見 conftest 的 sync_playwright fixture）──
@pytest.fixture()
def built_reports(repo_root: Path, sync_playwright):
    """真的跑一次 build_reports.py（子行程，跟指揮部手動跑的路徑一致）。"""
    script = repo_root / "_source" / "deploy-automation" / "build_reports.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, f"build_reports.py 失敗：\n{proc.stdout}\n{proc.stderr}"
    single_path = repo_root / "public" / "reports" / "2026-03" / "index.html"
    index_path = repo_root / "public" / "reports" / "index.html"
    assert single_path.exists()
    assert index_path.exists()
    return single_path, index_path


def test_built_single_page_has_no_bracket_residue(built_reports):
    single_path, _index_path = built_reports
    html = single_path.read_text(encoding="utf-8")
    assert "【" not in html, "產出 HTML 不得殘留全形方括號（待補標記未渲染完成）"
    assert html.count("（出處補充中）") == 4


def test_built_single_page_has_three_anchor_headings(built_reports):
    single_path, _index_path = built_reports
    html = single_path.read_text(encoding="utf-8")
    assert ">摘要<" in html
    assert ">本期數字一覽<" in html
    assert "參考資料" in html


def test_built_single_page_has_no_governance_or_internal_code_leak(built_reports):
    """掃描的是渲染出的『內文』，不含裝飾用 <svg> 圖示（icon path 的弧線指令，
    例如 `d="...A2 2 0 0 1..."`，是站台既有 icon 樣板，不是報告內容，第一次
    實跑就踩到這個假陽性：SVG 弧線命令剛好長得像內部代號 A2）。"""
    single_path, _index_path = built_reports
    html = single_path.read_text(encoding="utf-8")
    body = html.split("<body", 1)[1]
    body_no_svg = re.sub(r"<svg\b.*?</svg>", "", body, flags=re.S)
    masked = body_no_svg
    for allowed in br.GOVERNANCE_ALLOWLIST:
        masked = masked.replace(allowed, "")
    assert not br.GOVERNANCE_FORBIDDEN.search(masked), "頁面殘留治理內部字樣"
    assert not br.INTERNAL_CODE_PATTERN.search(body_no_svg), "頁面殘留內部代號"


def test_built_index_page_has_no_governance_leak(built_reports):
    """列表頁（/reports/index.html）是手刻的模板文案，不是從 _source/reports/*.md
    解析出來的，build_reports.py 的治理字樣掃描不會自動涵蓋它——這條測試補這個
    缺口。首次實跑時真的抓到一個真事故：模板文案寫了「供理監事、夥伴組織與公眾
    查閱」，逐字踩中禁詞表，已改寫為「供夥伴組織、媒體與公眾查閱」修正。"""
    _single_path, index_path = built_reports
    html = index_path.read_text(encoding="utf-8")
    assert not br.GOVERNANCE_FORBIDDEN.search(html), "列表頁模板文案殘留治理內部字樣"


def test_built_index_page_lists_every_report(built_reports):
    _single_path, index_path = built_reports
    html = index_path.read_text(encoding="utf-8")
    reports = br.load_all_reports()
    for report in reports:
        assert f'href="/reports/{report.slug}/"' in html, f"列表頁缺 {report.slug}"
        assert report.title in html


def test_build_missing_anchor_aborts_without_writing(repo_root: Path, sync_playwright):
    """缺必要錨點（例如漏掉「參考資料」）要整份中止，不能寫出半成品頁。

    測試用 slug 一律用 9999-XX（本規則要求 slug 格式必須是 \\d{4}-\\d{2}，
    不能沿用 build_briefs.py 測試那種 `_test_bad_*` 命名，否則會先被 slug
    格式檢查擋下、蓋掉本測試真正要驗的那個錯誤訊息）。
    """
    reports_dir = repo_root / "_source" / "reports"
    bad_path = reports_dir / "9999-01.md"
    bad_out_dir = repo_root / "public" / "reports" / "9999-01"
    try:
        bad_path.write_text(
            "---\nslug: 9999-01\ntitle: t\nreport_no: 99\n"
            "period_start: 2026-01-01\nperiod_end: 2026-03-31\npublished: 2026-04-01\n"
            "summary: s\nstatus: draft\n---\n"
            "# 測試標題\n**發布日期**：2026 年 4 月 1 日\n\n---\n\n"
            "## 摘要\nx\n\n## 一、亮點\ny\n",  # 故意漏掉「本期數字一覽」「參考資料」
            encoding="utf-8",
        )
        script = repo_root / "_source" / "deploy-automation" / "build_reports.py"
        proc = subprocess.run(
            [sys.executable, str(script), "9999-01"],
            cwd=repo_root, capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode != 0
        assert "缺少必要錨點小節" in proc.stderr
        assert not bad_out_dir.exists(), "缺錨點卻還是寫出了半成品頁"
    finally:
        bad_path.unlink(missing_ok=True)
        shutil.rmtree(bad_out_dir, ignore_errors=True)


def test_build_governance_leak_aborts_without_writing(repo_root: Path, sync_playwright):
    """治理內部字樣外流要整份中止，不能寫出半成品頁。"""
    reports_dir = repo_root / "_source" / "reports"
    bad_path = reports_dir / "9999-02.md"
    bad_out_dir = repo_root / "public" / "reports" / "9999-02"
    try:
        bad_path.write_text(
            "---\nslug: 9999-02\ntitle: t\nreport_no: 98\n"
            "period_start: 2026-01-01\nperiod_end: 2026-03-31\npublished: 2026-04-01\n"
            "summary: s\nstatus: draft\n---\n"
            "# 測試標題\n**發布日期**：2026 年 4 月 1 日\n\n---\n\n"
            "## 摘要\n本會理監事決議通過本報告。\n\n"
            "## 本期數字一覽\n| 項目 | 數值 | 出處 |\n|---|---|---|\n| a | 1 | b |\n\n"
            "## 參考資料\nx\n",
            encoding="utf-8",
        )
        script = repo_root / "_source" / "deploy-automation" / "build_reports.py"
        proc = subprocess.run(
            [sys.executable, str(script), "9999-02"],
            cwd=repo_root, capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode != 0
        assert "治理內部字樣" in proc.stderr
        assert not bad_out_dir.exists(), "治理字樣外流卻還是寫出了半成品頁"
    finally:
        bad_path.unlink(missing_ok=True)
        shutil.rmtree(bad_out_dir, ignore_errors=True)


def test_build_empty_source_cell_aborts_without_writing(repo_root: Path, sync_playwright):
    """「本期數字一覽」出處欄空白要整份中止，不能寫出半成品頁。"""
    reports_dir = repo_root / "_source" / "reports"
    bad_path = reports_dir / "9999-03.md"
    bad_out_dir = repo_root / "public" / "reports" / "9999-03"
    try:
        bad_path.write_text(
            "---\nslug: 9999-03\ntitle: t\nreport_no: 97\n"
            "period_start: 2026-01-01\nperiod_end: 2026-03-31\npublished: 2026-04-01\n"
            "summary: s\nstatus: draft\n---\n"
            "# 測試標題\n**發布日期**：2026 年 4 月 1 日\n\n---\n\n"
            "## 摘要\nx\n\n"
            "## 本期數字一覽\n| 項目 | 數值 | 出處 |\n|---|---|---|\n| a | 1 | |\n\n"
            "## 參考資料\nx\n",
            encoding="utf-8",
        )
        script = repo_root / "_source" / "deploy-automation" / "build_reports.py"
        proc = subprocess.run(
            [sys.executable, str(script), "9999-03"],
            cwd=repo_root, capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode != 0
        assert "缺「出處」" in proc.stderr
        assert not bad_out_dir.exists(), "出處欄空白卻還是寫出了半成品頁"
    finally:
        bad_path.unlink(missing_ok=True)
        shutil.rmtree(bad_out_dir, ignore_errors=True)

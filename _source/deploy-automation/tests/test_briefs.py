"""build_briefs.py 驗收：一頁 A4 PDF、七個固定段落齊、未知 metric key 報錯。

PDF 產生依賴 Playwright（本機 venv ~/.venvs/aabe-pw）；系統 python 沒裝時
optional-skip，不讓整套 pytest 變紅（跟 test_menu_a11y.py 等同一套模式）。
純解析邏輯（parse_frontmatter/parse_sections/render_metrics）不需要 Playwright，
一律跑。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import build_briefs as bb


@pytest.fixture()
def metrics(numbers_path: Path) -> dict:
    return bb.load_metrics(numbers_path)


# ── 純解析邏輯：不需要 Playwright ──────────────────────────────
def test_parse_frontmatter_requires_four_fields():
    text = "---\nissue: x\ntitle: t\n---\n## 問題\nfoo\n"
    with pytest.raises(bb.BriefError, match="缺欄位"):
        bb.parse_frontmatter(text)


def test_parse_sections_rejects_missing_and_extra():
    body = "\n".join(f"## {t}\n內容" for t in bb.SECTION_ORDER[:-1])  # 少一項
    with pytest.raises(bb.BriefError, match="缺少固定段落"):
        bb.parse_sections(body)

    body_extra = "\n".join(f"## {t}\n內容" for t in bb.SECTION_ORDER) + "\n## 多餘段落\nx\n"
    with pytest.raises(bb.BriefError, match="不在七項固定欄位"):
        bb.parse_sections(body_extra)


def test_render_metrics_unknown_key_raises(metrics):
    with pytest.raises(bb.BriefError, match="not_a_real_metric_id"):
        bb.render_metrics("本聯盟推動 {{metric:not_a_real_metric_id}} 項行動", metrics)


def test_render_metrics_known_key_ok(metrics):
    out = bb.render_metrics("共 {{metric:press_releases}} 篇", metrics)
    assert 'data-metric="press_releases"' in out
    assert metrics["press_releases"]["display"] in out


def test_school_lunch_brief_parses_and_matches_frontmatter(repo_root: Path):
    brief = bb.parse_brief(repo_root / "_source" / "briefs" / "school-lunch.md")
    assert brief.issue == "school-lunch"
    assert set(brief.sections) == set(bb.SECTION_ORDER)
    assert brief.updated == "2026-09-15"
    assert "王瀚陽" in brief.contact
    assert len(brief.sections["原始來源"].strip().splitlines()) >= 3 or \
        brief.sections["原始來源"].count("http") >= 3


# ── 第四批②（batch4-briefs2）：五個新議題＋既有 school-lunch，共六篇參數化跑 ──
ALL_ISSUES = [
    "school-lunch",
    "child-protection",
    "campus-safety",
    "youth-mental-health",
    "teacher-affairs",
    "education-reform",
]


@pytest.mark.parametrize("issue", ALL_ISSUES)
def test_all_briefs_parse_and_have_three_plus_sources(repo_root: Path, issue: str):
    brief = bb.parse_brief(repo_root / "_source" / "briefs" / f"{issue}.md")
    assert brief.issue == issue
    assert set(brief.sections) == set(bb.SECTION_ORDER)
    assert "王瀚陽" in brief.contact
    assert brief.sections["原始來源"].count("http") >= 3, \
        f"{issue}：原始來源少於 3 個 URL"


# ── 端對端：需要 Playwright（無則 SKIP，見 conftest 的 sync_playwright fixture）──
@pytest.fixture(params=ALL_ISSUES)
def built_brief(request, repo_root: Path, sync_playwright):
    """真的跑一次 build_briefs.py（子行程，確保跟指揮部手動跑的路徑一致），對六篇議題各參數化跑一次。"""
    issue = request.param
    script = repo_root / "_source" / "deploy-automation" / "build_briefs.py"
    proc = subprocess.run(
        [sys.executable, str(script), issue],
        cwd=repo_root, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, f"build_briefs.py 失敗（{issue}）：\n{proc.stdout}\n{proc.stderr}"
    html_path = repo_root / "public" / "briefs" / issue / "index.html"
    pdf_path = repo_root / "public" / "briefs" / f"{issue}.pdf"
    assert html_path.exists()
    assert pdf_path.exists()
    return issue, html_path, pdf_path


def test_pdf_is_exactly_one_page(built_brief):
    issue, _html_path, pdf_path = built_brief
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo is None:
        pytest.skip("pdfinfo 未安裝（poppler-utils）")
    proc = subprocess.run([pdfinfo, str(pdf_path)], capture_output=True, text=True, check=True)
    pages_line = next(l for l in proc.stdout.splitlines() if l.startswith("Pages:"))
    pages = int(pages_line.split(":", 1)[1].strip())
    assert pages == 1, f"{issue} 的 PDF 不是一頁：{proc.stdout}"


def test_html_has_all_seven_section_headings(built_brief):
    issue, html_path, _pdf_path = built_brief
    html = html_path.read_text(encoding="utf-8")
    for title in bb.SECTION_ORDER:
        assert f">{title}<" in html, f"{issue} 的 HTML 裡找不到段落標題 {title}"


def test_html_metrics_are_marked_for_numbers_check(built_brief):
    issue, html_path, _pdf_path = built_brief
    html = html_path.read_text(encoding="utf-8")
    assert 'data-metric="press_releases"' in html, issue
    assert 'data-metric="actions"' in html, issue


def test_build_unknown_metric_key_aborts_without_writing(repo_root: Path, sync_playwright):
    """未知 metric key 要整份中止，不能寫出半成品頁。"""
    briefs_dir = repo_root / "_source" / "briefs"
    bad_path = briefs_dir / "_test_bad_metric.md"
    bad_out_dir = repo_root / "public" / "briefs" / "_test_bad_metric"
    try:
        bad_path.write_text(
            "---\nissue: _test_bad_metric\ntitle: t\nupdated: 2026-09-15\n"
            "contact: 理事長 王瀚陽 0983-097-165\n---\n"
            "## 問題\n{{metric:definitely_not_a_real_id}}\n\n"
            "## 具體建議\n- x\n\n## 需協作機關\nx\n\n## 國教盟已做\n- x\n\n"
            "## 原始來源\n- a：https://example.com\n- b：https://example.com\n- c：https://example.com\n\n"
            "## 更新日期\n2026-09-15\n\n## 合作窗口\n理事長 王瀚陽 0983-097-165\n",
            encoding="utf-8",
        )
        script = repo_root / "_source" / "deploy-automation" / "build_briefs.py"
        proc = subprocess.run(
            [sys.executable, str(script), "_test_bad_metric"],
            cwd=repo_root, capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode != 0
        assert "definitely_not_a_real_id" in proc.stderr
        assert not bad_out_dir.exists(), "查無 metric 卻還是寫出了半成品頁"
    finally:
        bad_path.unlink(missing_ok=True)
        shutil.rmtree(bad_out_dir, ignore_errors=True)
        (repo_root / "public" / "briefs" / "_test_bad_metric.pdf").unlink(missing_ok=True)

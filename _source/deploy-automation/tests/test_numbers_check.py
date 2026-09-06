"""③ numbers_check.py：位置表、顯示值比對、黑數掃描。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

import numbers_check as nc

METRIC = {
    "id": "valid_surveys", "value": 66247, "display": "66,247", "unit": "份",
    "label": "有效問卷", "period": "x", "method": "x", "source": "x",
    "last_verified": "2026-09-05", "cadence": "event", "owner": "指揮部",
    "status": "approved", "notes": "x", "scan_patterns": ["66,247", "66247"],
}
METRICS = {"valid_surveys": METRIC}

GOOD = ('<html><body><div class="m-num">'
        '<span data-metric="valid_surveys">66,247</span><span>份</span></div></body></html>')


def build(tmp_path: Path, name: str, html: str) -> Path:
    root = tmp_path / "public"
    root.mkdir(exist_ok=True)
    (root / name).write_text(html, encoding="utf-8")
    return root


# ── 文字抽取 ───────────────────────────────────────────────
def test_condense_joins_across_tags():
    text, _ = nc.condense('<div class="n">168<span class="plus">+</span></div>')
    assert "168+" in text


def test_condense_keeps_meta_description():
    text, _ = nc.condense('<meta name="description" content="與 168+ 組織合作">')
    assert "168+" in text


def test_condense_drops_style_script_svg_and_comments():
    src = ('<style>.a{width:168px}</style>'
           '<script>var n=168;</script>'
           '<svg><path d="M168 0"/></svg>'
           '<!-- 168+ 註解 -->'
           '<p>168+ 組織</p>')
    text, _ = nc.condense(src)
    assert text.count("168") == 1


def test_condense_keeps_ld_json():
    text, _ = nc.condense('<script type="application/ld+json">{"d":"168+ 組織"}</script>')
    assert "168+" in text


def test_condense_offsets_map_back_to_source():
    src = '<p>abc</p>\n<p>66,247</p>'
    text, offsets = nc.condense(src)
    i = text.index("66,247")
    assert src[offsets[i]:offsets[i] + 6] == "66,247"


# ── 標記解析 ───────────────────────────────────────────────
def test_find_marked_reads_id_display_and_line():
    marked = nc.find_marked("\n\n" + GOOD)
    assert [(m.metric_id, m.shown, m.line) for m in marked] == [("valid_surveys", "66,247", 3)]


def test_find_marked_handles_nested_same_tag():
    marked = nc.find_marked('<span data-metric="partners">168<span class="p">+</span></span>')
    assert marked[0].shown == "168+"


# ── 位置表與比對 ───────────────────────────────────────────
def test_matching_page_passes(tmp_path):
    rows, problems = nc.check(build(tmp_path, "index.html", GOOD), METRICS, [])
    assert problems == []
    assert [(r.metric_id, r.kind, r.shown, r.ok) for r in rows] == [
        ("valid_surveys", "marked", "66,247", True)]
    assert rows[0].location.endswith("index.html:1")


def test_mismatched_display_is_reported(tmp_path):
    bad = GOOD.replace("66,247", "66,000")
    rows, problems = nc.check(build(tmp_path, "index.html", bad), METRICS, [])
    assert any("66,000" in p and "valid_surveys" in p for p in problems)
    assert rows[0].ok is False


def test_unknown_metric_id_is_reported(tmp_path):
    bad = GOOD.replace("valid_surveys", "ghost_metric")
    _, problems = nc.check(build(tmp_path, "index.html", bad), METRICS, [])
    assert any("ghost_metric" in p for p in problems)


# ── 黑數 ───────────────────────────────────────────────────
def test_unmarked_number_is_black(tmp_path):
    html = GOOD + "<p>累計 66,247 份問卷</p>"
    rows, problems = nc.check(build(tmp_path, "index.html", html), METRICS, [])
    assert any("黑數" in p for p in problems)
    assert any(r.kind == "prose" for r in rows)


def test_unmarked_number_without_comma_is_black(tmp_path):
    rows, problems = nc.check(build(tmp_path, "index.html", GOOD + "<p>66247</p>"), METRICS, [])
    assert any(r.kind == "prose" and r.shown == "66247" for r in rows)
    assert problems


def test_overlapping_patterns_count_once(tmp_path):
    """`7,917+` 同時命中 `7,917+` 與 `7,917` 兩個寫法，同一處只能算一筆黑數。"""
    metrics = {"buzz_3y": dict(METRIC, id="buzz_3y", display="7,917+",
                               scan_patterns=["7,917+", "7,917", "7917"])}
    rows, _ = nc.check(build(tmp_path, "index.html", "<p>累計 7,917+ 則</p>"), metrics, [])
    assert [(r.kind, r.shown) for r in rows] == [("prose", "7,917+")]


def test_shown_value_is_single_line(tmp_path):
    """`113 新聞稿` 在 HTML 裡可能被換行切開，位置表的顯示值欄不能夾帶換行
    （會把 markdown 表格撐破）。"""
    metrics = {"press_releases": dict(METRIC, id="press_releases", display="113",
                                      scan_patterns=["113 新聞稿"])}
    html = "<p>113\n        新聞稿</p>"
    rows, _ = nc.check(build(tmp_path, "index.html", html), metrics, [])
    assert [r.shown for r in rows] == ["113 新聞稿"]


def approve(root, metrics):
    """跑一次掃描、把現況核准成 allowlist（等同人工覆核後跑 --update-allowlist）。"""
    rows, _ = nc.check(root, metrics, [], None)
    return nc.build_allowlist(rows, [])["allow"]


def test_registered_prose_is_allowed(tmp_path):
    html = GOOD + "<p>累計 66,247 份問卷</p>"
    root = build(tmp_path, "index.html", html)
    allow = approve(root, METRICS)
    rows, problems = nc.check(root, METRICS, allow)
    assert problems == []
    assert [r.kind for r in rows] == ["marked", "prose"]
    assert rows[1].ok is True


def test_allowlist_count_must_match(tmp_path):
    html = GOOD + "<p>66,247</p><p>又一處 66,247</p>"
    allow = [{"id": "valid_surveys", "file": "index.html", "count": 1,
              "contexts": ["x"], "reason": "文案敘述"}]
    _, problems = nc.check(build(tmp_path, "index.html", html), METRICS, allow)
    assert any("登記 1" in p and "實際 2" in p for p in problems)


def test_scans_llms_and_humans_txt(tmp_path):
    root = build(tmp_path, "index.html", GOOD)
    (root / "llms.txt").write_text("有效問卷 66,247 份", encoding="utf-8")
    rows, problems = nc.check(root, METRICS, [])
    assert any(r.location.endswith("llms.txt:1") for r in rows)
    assert problems


def test_marked_value_not_counted_as_black(tmp_path):
    rows, _ = nc.check(build(tmp_path, "index.html", GOOD), METRICS, [])
    assert all(r.kind == "marked" for r in rows)


# ── 報表與 CLI ─────────────────────────────────────────────
def test_write_report(tmp_path):
    root = build(tmp_path, "index.html", GOOD)
    rows, _ = nc.check(root, METRICS, [])
    out = tmp_path / "位置表.md"
    nc.write_report(out, rows, METRICS, root)
    md = out.read_text(encoding="utf-8")
    assert "| id | 欄位 | 檔案:行號 | 顯示值 | 是否相符 |" in md
    assert "valid_surveys" in md and "index.html:1" in md
    assert "掃描根目錄" in md and "public" in md


def test_cli_on_real_site_exits_zero(repo_root, tmp_path):
    script = repo_root / "_source" / "deploy-automation" / "numbers_check.py"
    report = tmp_path / "r.md"
    r = subprocess.run([sys.executable, str(script), "--report", str(report)],
                       capture_output=True, text=True, cwd=repo_root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert report.exists()
    md = report.read_text(encoding="utf-8")
    assert "掃描根目錄：`public/`" in md
    assert "`index.html:" in md and "`methodology/index.html:" in md


def test_cli_exits_one_on_mismatch(repo_root, tmp_path):
    """把真源改壞，腳本必須擋下來（exit 1）。"""
    script = repo_root / "_source" / "deploy-automation" / "numbers_check.py"
    data = json.loads((repo_root / "_source" / "numbers.json").read_text(encoding="utf-8"))
    for m in data["metrics"]:
        if m["id"] == "legislators":
            m["display"] = "20"
            m["scan_patterns"] = ["20 位"]
    broken = tmp_path / "numbers.json"
    broken.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script), "--numbers", str(broken)],
                       capture_output=True, text=True, cwd=repo_root)
    assert r.returncode == 1
    assert "legislators" in r.stdout + r.stderr


# ══════════════════════════════════════════════════════════════
# Codex 盲審 2026-09-06 的回歸測試
# 報告：_source/審查_Codex盲審_數據SOP_20260906.md
# ══════════════════════════════════════════════════════════════

# ── C-01：位置基線（整卡刪除／標記消失／數量變少要被擋下）──────
def test_c01_deleted_marker_is_caught_by_manifest(tmp_path):
    """整張卡被刪掉，舊版 rows=0、problems=[] 靜默放行。"""
    root = build(tmp_path, "index.html", GOOD)
    rows, _ = nc.check(root, METRICS, [], None)
    manifest = nc.build_manifest(rows)["marked"]

    (root / "index.html").write_text("<html><body><p>卡片沒了</p></body></html>",
                                     encoding="utf-8")
    rows2, problems = nc.check(root, METRICS, [], manifest)
    assert rows2 == [] or all(r.kind != "marked" for r in rows2)
    assert any("位置基線" in p and "valid_surveys" in p for p in problems)


def test_c01_metric_never_on_site_is_caught(tmp_path):
    """numbers.json 新增一個指標卻沒放上任何頁面，也要報錯。"""
    metrics = dict(METRICS, ghost=dict(METRIC, id="ghost", value=555, display="555",
                                       scan_patterns=["555 份"]))
    _, problems = nc.check(build(tmp_path, "index.html", GOOD), metrics, [], [])
    assert any("ghost" in p and "找不到任何 data-metric 標記" in p for p in problems)


def test_c01_on_site_false_opts_out(tmp_path):
    metrics = dict(METRICS, ghost=dict(METRIC, id="ghost", value=555, display="555",
                                       on_site=False, scan_patterns=["555 份"]))
    rows, _ = nc.check(build(tmp_path, "index.html", GOOD), metrics, [], None)
    manifest = nc.build_manifest(rows)["marked"]
    _, problems = nc.check(build(tmp_path, "index.html", GOOD), metrics, [], manifest)
    assert problems == []


def test_c01_extra_marker_needs_registration(tmp_path):
    root = build(tmp_path, "index.html", GOOD)
    rows, _ = nc.check(root, METRICS, [], None)
    manifest = nc.build_manifest(rows)["marked"]
    (root / "index.html").write_text(GOOD + GOOD, encoding="utf-8")
    _, problems = nc.check(root, METRICS, [], manifest)
    assert any("應有 1 處、實際 2 處" in p for p in problems)


# ── C-02：真源自檢（value/display、status、欄位）──────────────
def test_c02_display_value_mismatch_needs_display_approx():
    metrics = {"m": dict(METRIC, id="m", value=3017, display="3,000+")}
    problems = nc.check_source(metrics)
    assert any("display_approx" in p for p in problems)
    metrics["m"]["display_approx"] = True
    assert nc.check_source(metrics) == []


def test_c02_status_must_be_valid():
    assert any("status" in p for p in nc.check_source({"m": dict(METRIC, status="ok")}))
    m = dict(METRIC)
    m.pop("status")
    assert any("缺欄位 `status`" in p for p in nc.check_source({"m": m}))


def test_c02_draft_metric_must_not_be_on_a_page(tmp_path):
    metrics = {"valid_surveys": dict(METRIC, status="draft")}
    _, problems = nc.check(build(tmp_path, "index.html", GOOD), metrics, [], None)
    assert any("draft" in p and "不得上站" in p for p in problems)


def test_c02_metric_field_projection_is_checked(tmp_path):
    html = ('<p><span data-metric="valid_surveys">66,247</span>'
            '<span data-metric="valid_surveys" data-metric-field="unit">人</span></p>')
    _, problems = nc.check(build(tmp_path, "index.html", html), METRICS, [], None)
    assert any("unit" in p and "份" in p for p in problems)

    good = html.replace(">人<", ">份<")
    rows, problems = nc.check(build(tmp_path, "index.html", good), METRICS, [], None)
    assert problems == []
    assert [r.field_key for r in rows] == ["display", "unit"]


# ── C-03：黑數別名表（量級、近似、全形、殘留舊值）─────────────
@pytest.mark.parametrize("prose,why", [
    ("問卷累計 6.6 萬份", "萬（一位小數）"),
    ("問卷累計 6.6萬份", "萬（沒空白）"),
    ("問卷累計 7 萬份", "萬（四捨五入）"),
    ("問卷累計 逾 66,247 份", "近似前綴"),
    ("問卷累計 超過66,247份", "近似前綴（沒空白）"),
    ("問卷累計 ６６，２４７ 份", "全形數字與全形逗號"),
])
def test_c03_alias_forms_are_caught(tmp_path, prose, why):
    rows, problems = nc.check(build(tmp_path, "index.html", GOOD + f"<p>{prose}</p>"),
                              METRICS, [], None)
    assert any(r.kind == "prose" for r in rows), f"漏抓：{why}"
    assert any("黑數" in p for p in problems), f"漏抓：{why}"


def test_c03_magnitude_needs_the_unit(tmp_path):
    """量級寫法要接單位才算命中，否則「7 萬元」這種無關句子會被誤判。"""
    rows, problems = nc.check(build(tmp_path, "index.html", GOOD + "<p>募款 7 萬元</p>"),
                              METRICS, [], None)
    assert all(r.kind == "marked" for r in rows)
    assert problems == []


def test_c03_numeric_range_is_not_a_black_number(tmp_path):
    """「長度通常 3,000-8,000 字」是字數區間，不是在報媒體露出篇數。"""
    metrics = {"press_coverage": dict(METRIC, id="press_coverage", value=3017,
                                      display="3,000+", display_approx=True, unit="篇",
                                      scan_patterns=["3,000+", "逾 3,000"])}
    html = "<p>每篇長度通常 3,000-8,000 字。</p>"
    rows, problems = nc.check(build(tmp_path, "index.html", html), metrics, [], None)
    assert [r for r in rows if r.kind == "prose"] == []
    assert all("黑數" not in p for p in problems)


def test_c03_previous_value_residue_is_caught(tmp_path):
    """舊值 33 還留在頁面上要抓得到——這正是方法頁漏改半年的那一型。"""
    metrics = {"policy_briefs": dict(METRIC, id="policy_briefs", value=47, display="47",
                                     unit="篇", scan_patterns=["47 篇"],
                                     previous_values=[{"value": 33, "note": "舊值"}])}
    html = ('<p><span data-metric="policy_briefs">47</span> 篇</p>'
            '<p>另有政策深度分析 33 篇</p>')
    rows, problems = nc.check(build(tmp_path, "index.html", html), metrics, [], None)
    assert any(r.kind == "prose" and r.shown == "33 篇" for r in rows)
    assert any("黑數" in p for p in problems)


# ── C-04：allowlist 綁語境（同檔換位置／換句子要重新核准）──────
def test_c04_moved_prose_breaks_the_allowlist(tmp_path):
    """同檔案刪掉一處合格文案、另一處新增同值宣稱：筆數不變，舊版靜默通過。"""
    ok_html = GOOD + '<p>八項調查累計 66,247 份有效問卷。</p>'
    root = build(tmp_path, "index.html", ok_html)
    allow = approve(root, METRICS)
    _, problems = nc.check(root, METRICS, allow)
    assert problems == []

    swapped = GOOD + '<p>本會會員人數已達 66,247 人。</p>'
    (root / "index.html").write_text(swapped, encoding="utf-8")
    _, problems = nc.check(root, METRICS, allow)
    assert any("黑數語境變動" in p for p in problems)


def test_c04_same_sentence_moving_line_is_still_ok(tmp_path):
    """只是整頁往下移（行號變、句子沒變）不該吵——語境雜湊不含行號。"""
    ok_html = GOOD + '<p>八項調查累計 66,247 份有效問卷。</p>'
    root = build(tmp_path, "index.html", ok_html)
    allow = approve(root, METRICS)
    (root / "index.html").write_text("<p>前言</p>\n" * 5 + ok_html, encoding="utf-8")
    _, problems = nc.check(root, METRICS, allow)
    assert problems == []


# ── 縱深建議 1／4：屬性寫法與位置表過期 ───────────────────────
def test_single_quoted_attribute_is_parsed():
    marked = nc.find_marked("<span data-metric='partners'>168+</span>")
    assert [(m.metric_id, m.shown) for m in marked] == [("partners", "168+")]


def test_check_report_detects_a_stale_position_table(repo_root, tmp_path):
    script = repo_root / "_source" / "deploy-automation" / "numbers_check.py"
    stale = tmp_path / "stale.md"
    stale.write_text("# 舊的位置表\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(script), "--check-report", str(stale)],
                       capture_output=True, text=True, cwd=repo_root)
    assert r.returncode == 1
    assert "位置表過期" in r.stdout


def test_committed_position_table_is_current(repo_root):
    """倉庫裡的位置表要跟現況一致，否則等於拿舊表當證據。"""
    script = repo_root / "_source" / "deploy-automation" / "numbers_check.py"
    report = repo_root / "_source" / "數字位置表_20260906.md"
    r = subprocess.run([sys.executable, str(script), "--check-report", str(report)],
                       capture_output=True, text=True, cwd=repo_root)
    assert r.returncode == 0, r.stdout + r.stderr

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
    "notes": "x", "scan_patterns": ["66,247", "66247"],
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


def test_registered_prose_is_allowed(tmp_path):
    html = GOOD + "<p>累計 66,247 份問卷</p>"
    allow = [{"id": "valid_surveys", "file": "index.html", "count": 1, "reason": "文案敘述"}]
    rows, problems = nc.check(build(tmp_path, "index.html", html), METRICS, allow)
    assert problems == []
    assert [r.kind for r in rows] == ["marked", "prose"]
    assert rows[1].ok is True


def test_allowlist_count_must_match(tmp_path):
    html = GOOD + "<p>66,247</p><p>又一處 66,247</p>"
    allow = [{"id": "valid_surveys", "file": "index.html", "count": 1, "reason": "文案敘述"}]
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
    assert "| id | 檔案:行號 | 顯示值 | 是否相符 |" in md
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

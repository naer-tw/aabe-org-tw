"""④ apply_numbers.py：把真源的 display 一次寫回全站標記處，並在方法頁留痕。"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import apply_numbers as ap

CARD = ('<div class="m-num"><span data-metric="partners">168'
        '<span class="plus">+</span></span></div>')

METHODOLOGY = """<html><body>
<span class="def-num" data-metric="partners">168<span class="plus">+</span></span>
<table>
  <tr><td style="padding:12px;">合作組織數</td><td>每季更新</td><td>2026-09</td></tr>
  <tr><td style="padding:12px;">政策深度分析</td><td>每季更新</td><td>2026-09</td></tr>
</table>
<h2>變更紀錄 Changelog</h2>
<div class="changelog">
  <div class="cl-row">
    <time>2026-09-05</time>
    <div class="what">既有紀錄。</div>
  </div>
</div>
</body></html>
"""


def metrics(display="168+"):
    return {"partners": {"id": "partners", "display": display, "unit": "個",
                         "label": "合作組織", "value": 168,
                         "scan_patterns": [display]}}


def build_site(tmp_path: Path, index=CARD, methodology=METHODOLOGY) -> Path:
    root = tmp_path / "public"
    (root / "methodology").mkdir(parents=True)
    (root / "index.html").write_text(f"<html><body>{index}</body></html>", encoding="utf-8")
    (root / "methodology" / "index.html").write_text(methodology, encoding="utf-8")
    return root


# ── 單處替換 ───────────────────────────────────────────────
def test_replaces_digits_and_keeps_markup():
    out, changes = ap.apply_html(f"<html>{CARD}</html>", metrics("175+"))
    assert '<span class="plus">+</span>' in out, "加號的樣式 span 不可被吃掉"
    assert "175" in out and "168" not in out
    assert [(c.metric_id, c.old, c.new) for c in changes] == [("partners", "168+", "175+")]


def test_no_change_returns_empty_changes():
    out, changes = ap.apply_html(f"<html>{CARD}</html>", metrics("168+"))
    assert changes == []
    assert out == f"<html>{CARD}</html>"


def test_refuses_when_markup_cannot_show_new_display():
    """新 display 去掉了加號，但版面上還有 <span class="plus">+</span>：
    改下去會變成 175+，與真源不符——必須擋下來要人工處理，不能默默改壞。"""
    with pytest.raises(ap.ApplyError) as e:
        ap.apply_html(f"<html>{CARD}</html>", metrics("175"))
    assert "partners" in str(e.value)


def test_unknown_id_raises():
    html = '<span data-metric="ghost">1</span>'
    with pytest.raises(ap.ApplyError):
        ap.apply_html(html, metrics())


# ── 方法頁留痕 ─────────────────────────────────────────────
def test_methodology_changelog_and_recent_update(tmp_path):
    root = build_site(tmp_path)
    changes = ap.run(root, metrics("175+"), today="2026-09-06", dry_run=False)
    md = (root / "methodology" / "index.html").read_text(encoding="utf-8")
    assert md.count("<div class=\"cl-row\">") == 2, "Changelog 應追加一行"
    assert "2026-09-06" in md
    assert "partners" in md and "168+" in md and "175+" in md
    # 最近更新只動有關的那一列
    assert "合作組織數" in md
    rows = [r for r in md.splitlines() if "合作組織數" in r][0]
    assert "2026-09" in rows
    assert len(changes) == 2  # 首頁與方法頁各一處


def test_recent_update_month_follows_today(tmp_path):
    root = build_site(tmp_path)
    ap.run(root, metrics("175+"), today="2026-10-01", dry_run=False)
    md = (root / "methodology" / "index.html").read_text(encoding="utf-8")
    assert [r for r in md.splitlines() if "合作組織數" in r][0].endswith("<td>2026-10</td></tr>")
    assert [r for r in md.splitlines() if "政策深度分析" in r][0].endswith("<td>2026-09</td></tr>"), \
        "沒改到的指標不應被動到最近更新"


def test_idempotent(tmp_path):
    root = build_site(tmp_path)
    ap.run(root, metrics("175+"), today="2026-09-06", dry_run=False)
    before = (root / "methodology" / "index.html").read_text(encoding="utf-8")
    changes = ap.run(root, metrics("175+"), today="2026-09-06", dry_run=False)
    assert changes == []
    assert (root / "methodology" / "index.html").read_text(encoding="utf-8") == before


def test_dry_run_prints_diff_without_writing(tmp_path, capsys):
    root = build_site(tmp_path)
    before = (root / "index.html").read_text(encoding="utf-8")
    changes = ap.run(root, metrics("175+"), today="2026-09-06", dry_run=True)
    out = capsys.readouterr().out
    assert "--- " in out and "+++ " in out and "175" in out
    assert changes
    assert (root / "index.html").read_text(encoding="utf-8") == before


# ── CLI 與真站 ─────────────────────────────────────────────
def test_cli_dry_run_on_real_site_is_clean(repo_root):
    """真站現況已與真源同步，dry-run 應該報「無變動」。"""
    script = repo_root / "_source" / "deploy-automation" / "apply_numbers.py"
    r = subprocess.run([sys.executable, str(script), "--dry-run"],
                       capture_output=True, text=True, cwd=repo_root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "無變動" in r.stdout


def test_cli_applies_new_value_on_a_copy(repo_root, tmp_path):
    """複製一份真站，改真源 partners 168+ → 999+，跑 apply 後全站標記處都要變，
    且 numbers_check 對這份複本仍要 exit 0。"""
    site = tmp_path / "public"
    shutil.copytree(repo_root / "public", site)
    data = json.loads((repo_root / "_source" / "numbers.json").read_text(encoding="utf-8"))
    for m in data["metrics"]:
        if m["id"] == "partners":
            m["display"] = "999+"
            m["scan_patterns"] = ["999+", "999 個"]
    numbers = tmp_path / "numbers.json"
    numbers.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    script = repo_root / "_source" / "deploy-automation" / "apply_numbers.py"
    r = subprocess.run([sys.executable, str(script), "--root", str(site),
                        "--numbers", str(numbers), "--today", "2026-09-06"],
                       capture_output=True, text=True, cwd=repo_root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (site / "index.html").read_text(encoding="utf-8").count(
        '<span data-metric="partners">999') == 1
    md = (site / "methodology" / "index.html").read_text(encoding="utf-8")
    assert "999+" in md and "168+" in md  # 新值上版、Changelog 記下舊值

    check = repo_root / "_source" / "deploy-automation" / "numbers_check.py"
    r2 = subprocess.run([sys.executable, str(check), "--root", str(site),
                         "--numbers", str(numbers)], capture_output=True, text=True)
    assert "❌" in r2.stdout or r2.returncode == 1, "文案處還寫著 168+，check 應該要抓到"


# ══════════════════════════════════════════════════════════════
# Codex 盲審 2026-09-06 C-02 的回歸測試
# ══════════════════════════════════════════════════════════════

MULTILINE_METHODOLOGY = """<html><body>
<span class="def-num" data-metric="partners">168<span class="plus">+</span></span>
<table>
  <tr style="border-bottom:1px solid var(--line);">
    <td style="padding:12px;">合作組織數</td>
    <td style="padding:12px;">每季更新</td>
    <td style="padding:12px;">2026-05</td>
  </tr>
</table>
<h2>變更紀錄 Changelog</h2>
<div class="changelog">
</div>
</body></html>
"""


def test_month_cell_updated_when_label_and_month_are_on_different_lines():
    """真實版面上標題與月份分屬不同行；舊版逐行取代永遠換不到月份（靜默漏改）。"""
    changes = [ap.Change("partners", "168+", "173+")]
    out = ap.update_methodology(MULTILINE_METHODOLOGY, changes, "2026-09-06")
    assert "<td style=\"padding:12px;\">2026-09</td>" in out
    assert "2026-05" not in out


def test_apply_stops_when_month_cell_cannot_be_updated():
    """表格版型改掉、月份欄不見了：不可以只寫 Changelog 就當成功。"""
    broken = MULTILINE_METHODOLOGY.replace(
        '<td style="padding:12px;">2026-05</td>', '<td style="padding:12px;">—</td>')
    with pytest.raises(ap.ApplyError, match="最近更新"):
        ap.update_methodology(broken, [ap.Change("partners", "168+", "173+")], "2026-09-06")


def test_metric_field_projection_is_applied():
    """data-metric-field 讓單位／期間等欄位也吃單一真源，不再只有 display。"""
    html = ('<p><span data-metric="partners">168<span class="plus">+</span></span>'
            '<span data-metric="partners" data-metric-field="unit">家</span></p>')
    m = metrics()
    m["partners"]["unit"] = "個"
    out, changes = ap.apply_html(html, m)
    assert ">個<" in out
    assert [(c.metric_id, c.old, c.new) for c in changes] == [("partners", "家", "個")]


def test_metric_without_methodology_row_does_not_abort():
    """不在「更新頻率」表裡的指標（他方組織規模引用值）更新時不得整批中止。

    2026-09-21：family_resilience_orgs／mental_health_alliance_orgs 納入管轄後，
    /methodology/ 沒有對應列。少了 NO_METHODOLOGY_ROW 豁免，這裡會噴
    「找不到對應列」ApplyError，等於這兩個數字永遠套不進去。
    """
    changes = [ap.Change("mental_health_alliance_orgs", "76", "79")]
    out = ap.update_methodology(MULTILINE_METHODOLOGY, changes, "2026-10-01")
    assert "2026-10" not in out.split("變更紀錄")[0], "不該去動「更新頻率」表的月份"
    assert "mental_health_alliance_orgs 76 → 79" in out, "Changelog 仍要留痕"


def test_unknown_metric_still_aborts_when_row_is_missing():
    """豁免表只豁免名單內的 id：名單外的指標找不到對應列，仍要停手。"""
    with pytest.raises(ap.ApplyError, match="ROW_LABEL_TO_IDS"):
        ap.update_methodology(MULTILINE_METHODOLOGY,
                              [ap.Change("legislators", "19", "20")], "2026-10-01")

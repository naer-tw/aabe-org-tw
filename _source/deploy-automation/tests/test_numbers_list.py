"""⑦ 清單型真源（numbers.json 的 surveys ＋ 頁面上的 data-metric-list）。

歷年調查表有 18 案、每案兩格數字，不適合每案各開一個 metric（apply_numbers.py 會
把它們當成可季度更新的指標）。清單型走另一條路：值一樣要等於真源、一樣進位置基線，
但 apply_numbers.py 不碰——所以第一條測試就是「find_marked 不准看到 data-metric-list」。
"""
import json

import pytest

import numbers_check as nc

SURVEY = {
    "slug": "cannabis-2023", "name": "台灣大麻合法化知識及態度意見調查", "year": "2023",
    "period": "2023-02-15 ~ 03-01", "partner": "台灣共善促進協會（合辦）", "role": "合辦",
    "valid_samples": "38,502 份", "reach": "104,000 人次",
    "published": "記者會 2023-11-13", "source": "清單 表一第 1 列",
    "last_verified": "2026-09-05", "status": "approved", "notes": "",
}
LISTS = {"survey:cannabis-2023": SURVEY}

METRIC = {
    "id": "single_reach", "value": 104000, "display": "104,000", "unit": "人次",
    "label": "單場調查最高觸及", "period": "x", "method": "x", "source": "x",
    "last_verified": "2026-09-05", "cadence": "event", "owner": "指揮部",
    "status": "approved", "notes": "x", "scan_patterns": ["104,000"],
}
METRICS = {"single_reach": METRIC}


def build(tmp_path, name: str, html: str):
    root = tmp_path / "public"
    root.mkdir(exist_ok=True)
    (root / name).write_text(html, encoding="utf-8")
    return root


# ── 兩種標記互不干擾 ────────────────────────────────────────
def test_find_marked_ignores_list_marks():
    """apply_numbers.py／postdeploy_verify.py 都吃 find_marked()，看到不認得的 id
    會直接 ApplyError。清單型標記絕不能漏進去。"""
    src = '<td data-metric-list="survey:cannabis-2023">38,502 份</td>'
    assert nc.find_marked(src) == []


def test_find_marked_lists_reads_default_field():
    src = '<td data-metric-list="survey:cannabis-2023">38,502 份</td>'
    marks = nc.find_marked_lists(src)
    assert len(marks) == 1
    assert marks[0].metric_id == "survey:cannabis-2023"
    assert marks[0].field_key == nc.LIST_DEFAULT_FIELD == "valid_samples"


def test_find_marked_lists_reads_explicit_field():
    src = ('<td data-metric-list="survey:cannabis-2023" '
           'data-metric-field="reach">104,000 人次</td>')
    assert nc.find_marked_lists(src)[0].field_key == "reach"


def test_find_marked_lists_ignores_plain_metric_marks():
    assert nc.find_marked_lists('<span data-metric="single_reach">104,000</span>') == []


# ── 值比對 ──────────────────────────────────────────────────
def test_matching_list_value_passes(tmp_path):
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:cannabis-2023">38,502 份</td>')
    rows, problems = nc.check(root, {}, [], None, LISTS)
    assert problems == []
    assert [(r.metric_id, r.ok) for r in rows] == [("survey:cannabis-2023", True)]


def test_wrong_list_value_is_reported(tmp_path):
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:cannabis-2023">38,500 份</td>')
    _rows, problems = nc.check(root, {}, [], None, LISTS)
    assert any("38,502 份" in p and "a.html:1" in p for p in problems), problems


def test_unknown_slug_is_reported(tmp_path):
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:nope-2099">1 份</td>')
    _rows, problems = nc.check(root, {}, [], None, LISTS)
    assert any("沒有的清單項目" in p for p in problems), problems


def test_illegal_list_field_is_reported(tmp_path):
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:cannabis-2023" '
                 'data-metric-field="display">38,502 份</td>')
    _rows, problems = nc.check(root, {}, [], None, LISTS)
    assert any("不是清單可投影欄位" in p for p in problems), problems


def test_draft_list_entry_must_not_ship(tmp_path):
    draft = {"survey:cannabis-2023": dict(SURVEY, status="draft")}
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:cannabis-2023">38,502 份</td>')
    _rows, problems = nc.check(root, {}, [], None, draft)
    assert any("draft" in p for p in problems), problems


def test_list_mark_masks_black_number_scan(tmp_path):
    """104,000 是 single_reach 的值，但它包在清單標記裡（該案的觸及人次），
    不該再被當成未標記黑數重複報一次。"""
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:cannabis-2023" '
                 'data-metric-field="reach">104,000 人次</td>')
    rows, problems = nc.check(root, METRICS, [], None, LISTS)
    assert [r.kind for r in rows] == ["marked"]
    assert not [p for p in problems if "黑數" in p], problems


def test_unmarked_value_next_to_a_list_mark_is_still_caught(tmp_path):
    """遮蔽只作用在標記內部：同一頁其他地方裸寫 104,000 仍要被抓。"""
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:cannabis-2023" '
                 'data-metric-field="reach">104,000 人次</td><p>觸及 104,000 人次</p>')
    _rows, problems = nc.check(root, METRICS, [], None, LISTS)
    assert any("黑數" in p for p in problems), problems


# ── 位置基線涵蓋清單型 ──────────────────────────────────────
def test_manifest_covers_list_marks(tmp_path):
    root = build(tmp_path, "a.html",
                 '<td data-metric-list="survey:cannabis-2023">38,502 份</td>')
    rows, _ = nc.check(root, {}, [], None, LISTS)
    manifest = nc.build_manifest(rows)["marked"]
    assert {"file": "a.html", "id": "survey:cannabis-2023", "count": 1} in manifest


def test_deleting_a_list_mark_breaks_the_baseline(tmp_path):
    """整張歷年調查表被刪掉時要擋下來（C-01 的清單型版本）。"""
    root = build(tmp_path, "a.html", "<p>沒有任何標記</p>")
    manifest = [{"file": "a.html", "id": "survey:cannabis-2023", "count": 1}]
    _rows, problems = nc.check(root, {}, [], manifest, LISTS)
    assert any("實際 0 處" in p for p in problems), problems
    assert any("宣告會上站" in p for p in problems), problems


def test_on_site_false_list_entry_is_not_required(tmp_path):
    off = {"survey:cannabis-2023": dict(SURVEY, on_site=False)}
    root = build(tmp_path, "a.html", "<p>沒有任何標記</p>")
    _rows, problems = nc.check(root, {}, [], [], off)
    assert problems == []


# ── 真源自檢與載入 ──────────────────────────────────────────
def test_check_lists_requires_fields_and_status():
    bad = {"survey:x": dict(SURVEY, reach="", status="unknown")}
    problems = nc.check_lists(bad)
    assert any("缺欄位 `reach`" in p for p in problems), problems
    assert any("status" in p for p in problems), problems


def test_load_lists_rejects_duplicate_slug(tmp_path):
    p = tmp_path / "numbers.json"
    p.write_text(json.dumps({"metrics": [], "surveys": [SURVEY, SURVEY]},
                            ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="重複"):
        nc.load_lists(p)


def test_load_lists_tolerates_missing_surveys_key(tmp_path):
    p = tmp_path / "numbers.json"
    p.write_text(json.dumps({"metrics": []}), encoding="utf-8")
    assert nc.load_lists(p) == {}


# ── 真實真源與真實頁面 ──────────────────────────────────────
@pytest.fixture(scope="module")
def real_lists(numbers_path):
    return nc.load_lists(numbers_path)


def test_real_surveys_are_complete(real_lists):
    assert len(real_lists) == 18, "歷年調查 13 筆＋夥伴主辦協力 5 筆"
    assert nc.check_lists(real_lists) == []
    for key, entry in real_lists.items():
        assert entry["status"] == "approved", key
        assert entry["source"].endswith("列"), f"{key} 的 source 要指到清單的某一列"
        assert "20260905_清單_國教盟調查與觸及數據.md" in entry["source"], key


def test_partner_surveys_are_marked_as_support_role(real_lists):
    """夥伴主辦的五案角色必須是「協力」——寫成自辦或合辦就是把別人的成績當自己的。"""
    partners = [k for k in real_lists if k.startswith("survey:partner-")]
    assert len(partners) == 5
    for key in partners:
        assert real_lists[key]["role"] == "協力", key


def test_reach_page_list_marks_match_source(public_dir, real_lists):
    src = (public_dir / "impact" / "reach" / "index.html").read_text(encoding="utf-8")
    marks = nc.find_marked_lists(src)
    assert len(marks) == 36, "一句話 1＋數字卡 4＋歷年調查 13×2＋協力 5"
    seen = set()
    for mk in marks:
        entry = real_lists[mk.metric_id]
        want = str(entry[mk.field_key]).replace(" ", "")
        assert mk.shown == want, f"{mk.metric_id}.{mk.field_key} 行 {mk.line}"
        seen.add(mk.metric_id)
    assert seen == set(real_lists), "每一筆調查都要出現在頁面上"

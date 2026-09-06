"""① _source/numbers.json 單一真源的結構檢查（SOP-數據更新與部署索引.md 第一節）。"""
import json
import re

import pytest

REQUIRED_FIELDS = [
    "id", "value", "display", "unit", "label", "period",
    "method", "source", "last_verified", "cadence", "owner", "notes", "status",
]

# 來源鏈可由看板清單一手重算的＝approved；只回指官網下游頁面的＝provisional，
# 待秘書處／理事長拍板（Codex 盲審 C-05）。
APPROVED = ["valid_surveys", "single_reach", "press_coverage", "buzz_1y", "buzz_3y"]
PROVISIONAL = ["partners", "actions", "press_releases", "policy_briefs", "legislators"]

# SOP 第一節「首批 id（2026-09-06）」
FIRST_BATCH = ["valid_surveys", "single_reach", "partners",
               "press_coverage", "buzz_1y", "actions"]

# CH 05 舊數字帶與 /methodology/、/impact/ 既有影響力數字
LEGACY_IDS = ["press_releases", "policy_briefs", "buzz_3y", "legislators"]

EXPECTED_DISPLAY = {
    "valid_surveys": "66,247",
    "single_reach": "104,000",
    "partners": "168+",
    "press_coverage": "3,000+",
    "buzz_1y": "2,889",
    "actions": "286",
    "press_releases": "113",
    "policy_briefs": "47",
    "buzz_3y": "7,917+",
    "legislators": "19",
}


@pytest.fixture(scope="module")
def numbers(numbers_path):
    assert numbers_path.exists(), f"缺少單一真源檔：{numbers_path}"
    return json.loads(numbers_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def metrics(numbers):
    return {m["id"]: m for m in numbers["metrics"]}


def test_top_level_shape(numbers):
    assert numbers["version"] == 2
    assert numbers["updated"] == "2026-09-06"
    assert isinstance(numbers["metrics"], list)


def test_all_ids_present(metrics):
    for mid in FIRST_BATCH + LEGACY_IDS:
        assert mid in metrics, f"numbers.json 缺 id：{mid}"


def test_no_duplicate_ids(numbers):
    ids = [m["id"] for m in numbers["metrics"]]
    assert len(ids) == len(set(ids)), f"id 重複：{ids}"


def test_required_fields(metrics):
    for mid, m in metrics.items():
        for field in REQUIRED_FIELDS:
            assert field in m, f"{mid} 缺欄位 {field}"
            assert m[field] not in (None, ""), f"{mid}.{field} 不得留空"


def test_display_matches_expected(metrics):
    for mid, want in EXPECTED_DISPLAY.items():
        assert metrics[mid]["display"] == want


def test_value_consistent_with_display(metrics):
    """display 去掉逗號、加號與前綴後，須等於 value（press_coverage 例外，見 notes）。"""
    for mid, m in metrics.items():
        digits = re.sub(r"[^\d]", "", m["display"])
        if mid == "press_coverage":
            # 對外保守表述「逾 3,000 篇」，value 為列管範圍內實計 3,017
            assert m["value"] == 3017
            assert "3,017" in m["notes"]
            # 近似對外值必須明寫，才不會靜默分岐（Codex 盲審 C-02）
            assert m["display_approx"] is True
            continue
        assert not m.get("display_approx"), f"{mid} display 就是精確值，不該標 display_approx"
        assert int(digits) == m["value"], f"{mid} display/value 不一致"


def test_last_verified_and_cadence(metrics):
    for mid, m in metrics.items():
        assert m["last_verified"] in ("2026-09-05", "2026-09-06"), mid
        assert m["cadence"] in ("quarterly", "event", "yearly"), mid
        assert m["owner"] in ("指揮部", "秘書處", "指揮部＋秘書處"), mid


def test_source_traceable(metrics):
    """每筆 source 要嘛指向看板清單原件，要嘛指向官網方法頁既有出處。"""
    for mid, m in metrics.items():
        src = m["source"]
        assert ("20260905_清單_國教盟調查與觸及數據.md" in src
                or "public/methodology/index.html" in src
                or "影響力報告" in src), f"{mid} source 無法回溯：{src}"


def test_period_difference_noted_for_legacy(metrics):
    """舊數字帶與新區期間不同，notes 必須註明，避免被相加。"""
    for mid in ("buzz_3y", "press_releases", "policy_briefs", "legislators"):
        assert "期間" in metrics[mid]["notes"], f"{mid} notes 未註明期間差異"
    assert "不可相加" in metrics["buzz_3y"]["notes"]
    assert "不可相加" in metrics["buzz_1y"]["notes"]


def test_scan_patterns_present(metrics):
    """黑數掃描用的已知數值字串：每筆至少一組，且都錨在 display 的數字本體上。"""
    for mid, m in metrics.items():
        pats = m["scan_patterns"]
        assert isinstance(pats, list) and pats, mid
        core = m["display"].rstrip("+")
        assert any(core in p for p in pats), f"{mid} scan_patterns 未錨在 {core}"


def test_short_numbers_require_unit_context(metrics):
    """113／47／19／286 這種 2-3 位數，裸掃全站會被日期、法條、色碼淹沒；
    規定短數字的掃描字串必須帶單位或加號等脈絡，否則等於沒有掃描價值。"""
    for mid, m in metrics.items():
        core = m["display"].rstrip("+")
        if len(core.replace(",", "")) > 3:
            continue
        for p in m["scan_patterns"]:
            assert p != core, f"{mid} 不得用裸數字 {core} 當掃描字串（噪音過高）"


def test_status_is_declared_and_valid(metrics):
    """每筆都要標 status；draft 不得上站，provisional 要留待拍板的紀錄。"""
    for mid in APPROVED:
        assert metrics[mid]["status"] == "approved", mid
    for mid in PROVISIONAL:
        assert metrics[mid]["status"] == "provisional", mid
        assert metrics[mid]["source_status"] == "downstream_only", mid
    assert set(APPROVED + PROVISIONAL) == set(metrics)


def test_changed_values_keep_previous_values(metrics):
    """改過的數字要留舊值，殘留舊值才掃得到（Codex 盲審 C-03 / 縱深 3）。"""
    olds = {p["value"] for p in metrics["policy_briefs"]["previous_values"]}
    assert {33, 36} <= olds, "policy_briefs 曾是 33（方法頁）與 36（媒體中心頁）"

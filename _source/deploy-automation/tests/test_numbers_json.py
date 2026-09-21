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
# 2026-09-06 理事長裁決：partners/actions/press_releases/policy_briefs/legislators
# 五筆口徑 OK（屬 2023–2026 年區間口徑，2026 年底需再整理），status 改 approved。
APPROVED = ["valid_surveys", "single_reach", "press_coverage", "buzz_1y", "buzz_3y",
            "partners", "actions", "press_releases", "policy_briefs", "legislators"]
# 2026-09-21 理事長裁決：連署頁引用的兩個「他方組織規模」納入管轄，但出處薄弱、
# 現況未確認（秘書處已被交辦向兩位召集人各要一份書面現況數字），故一律 provisional。
# 值是各自的 source_status：兩筆都不是「可由看板清單一手重算」，但薄弱的方式不同——
#   downstream_only ＝ 來源鏈只回指官網下游頁面（等於引用自己）
#   external_dated  ＝ 來源是外部單一媒體報導，且是舊日期（非現況）
PROVISIONAL = {
    "family_resilience_orgs": "external_dated",
    "mental_health_alliance_orgs": "downstream_only",
}

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
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", m["last_verified"]), (
            f"{mid}.last_verified 要寫成 YYYY-MM-DD：{m['last_verified']}")
        if mid in EXPECTED_DISPLAY:
            # 首批十筆是同一次盤點產生的，日期凍結在那兩天
            assert m["last_verified"] in ("2026-09-05", "2026-09-06"), mid
        assert m["cadence"] in ("quarterly", "event", "yearly"), mid
        assert m["owner"] in ("指揮部", "秘書處", "指揮部＋秘書處"), mid


def test_source_traceable(metrics):
    """每筆 source 都要能回溯：看板清單原件、官網方法頁、外部 URL，或 repo 內「檔:行」。

    2026-09-21 放寬兩種寫法（引用他方組織規模時，出處不在看板清單裡）：
    `https://…` 的外部原件、以及 `public/…/index.html:488` 這種可 grep 的行級指向。
    放寬的是「出處長什麼樣」，不是「可不可以沒有出處」——三種都對不上仍然 fail。
    """
    for mid, m in metrics.items():
        src = m["source"]
        traceable = ("20260905_清單_國教盟調查與觸及數據.md" in src
                     or "public/methodology/index.html" in src
                     or "影響力報告" in src
                     or re.search(r"https?://\S+", src)
                     or re.search(r"\bpublic/\S+\.html:\d+", src))
        assert traceable, f"{mid} source 無法回溯：{src}"


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
    for mid, want_source_status in PROVISIONAL.items():
        assert metrics[mid]["status"] == "provisional", mid
        assert metrics[mid]["source_status"] == want_source_status, mid
        # 待拍板的紀錄要留在 notes 裡，換人接手才知道在等什麼
        assert "待秘書處" in metrics[mid]["notes"], f"{mid} notes 未寫待補的書面現況數字"
        assert "並存的其他數值" in metrics[mid]["notes"], f"{mid} notes 未列並存數值"
    assert set(APPROVED) | set(PROVISIONAL) == set(metrics)


def test_changed_values_keep_previous_values(metrics):
    """改過的數字要留舊值，殘留舊值才掃得到（Codex 盲審 C-03 / 縱深 3）。"""
    olds = {p["value"] for p in metrics["policy_briefs"]["previous_values"]}
    assert {33, 36} <= olds, "policy_briefs 曾是 33（方法頁）與 36（媒體中心頁）"

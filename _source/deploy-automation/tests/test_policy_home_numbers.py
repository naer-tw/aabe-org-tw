"""政策站首頁（_policy-deploy/index.html）數字單一真源檢查。

2026-10-18 理事長核可：hero 篇數／類別數、五張分類卡篇數都改掛 data-metric，值住 numbers.json。
numbers_check.py 預設只掃本 repo 的 public/，掃不到兄弟 repo `_policy-deploy`，所以這裡用同一套
find_marked 對政策首頁逐個標記比對真源，並核對「五卡合計＝policy_briefs」。
兄弟 repo 不在（例如 CI）就整檔 skip。
"""
import re
from pathlib import Path

import pytest

import numbers_check as nc

CAT_IDS = ["policy_cat_campus_safety", "policy_cat_child_protection", "policy_cat_youth_health",
           "policy_cat_education_reform", "policy_cat_teacher_affairs"]


@pytest.fixture(scope="module")
def policy_index(repo_root: Path) -> str:
    p = repo_root.parent / "_policy-deploy" / "index.html"
    if not p.exists():
        pytest.skip("兄弟 repo _policy-deploy 不在本機")
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def metrics(numbers_path):
    return nc.load_metrics(numbers_path)


def test_markers_match_source(policy_index, metrics):
    marked = nc.find_marked(policy_index)
    assert marked, "政策首頁找不到任何 data-metric 標記"
    for mk in marked:
        assert mk.metric_id in metrics, f"行 {mk.line} 的 {mk.metric_id} 不在 numbers.json"
        assert mk.shown == metrics[mk.metric_id]["display"], \
            f"行 {mk.line} {mk.metric_id} 顯示 {mk.shown}，真源 {metrics[mk.metric_id]['display']}"


def test_every_card_and_hero_is_marked(policy_index):
    ids = [mk.metric_id for mk in nc.find_marked(policy_index)]
    for mid in CAT_IDS:
        assert ids.count(mid) == 1, f"{mid} 應在分類卡出現 1 次，實際 {ids.count(mid)}"
    assert ids.count("policy_briefs") == 1
    assert ids.count("policy_topic_areas") == 2   # hero ＋「N TOPICS」


def test_card_sum_equals_policy_briefs(metrics):
    assert sum(int(metrics[m]["value"]) for m in CAT_IDS) == int(metrics["policy_briefs"]["value"])


def test_topic_areas_equals_card_count(policy_index, metrics):
    cards = re.findall(r'<a href="[^"]+" class="cat"', policy_index)
    assert len(cards) == int(metrics["policy_topic_areas"]["value"]) == len(CAT_IDS)


def test_scan_prose_false_skips_black_number_scan(tmp_path, metrics):
    f = tmp_path / "x.html"
    f.write_text("<p>約7 篇、近15 篇、01 7 篇</p>", encoding="utf-8")
    rows, _ = nc.scan_file(f, "x.html", {k: metrics[k] for k in CAT_IDS})
    assert rows == []

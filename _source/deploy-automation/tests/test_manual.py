"""⑦ 官網維護手冊 §③「我要更新數據」必須指向本 SOP 的四步流程。"""
import re

import pytest


@pytest.fixture(scope="module")
def section(repo_root):
    text = (repo_root / "官網維護手冊.md").read_text(encoding="utf-8")
    m = re.search(r"## ③ 我要更新數據.*?(?=\n## ④ )", text, re.S)
    assert m, "找不到 §③ 我要更新數據"
    return m.group(0)


def test_points_to_sop_and_single_source(section):
    assert "SOP-數據更新與部署索引.md" in section
    assert "_source/numbers.json" in section


def test_lists_the_four_steps(section):
    for step in ("改清單", "改 numbers.json", "apply_numbers.py", "numbers_check.py"):
        assert step in section, f"§③ 缺步驟：{step}"


def test_mentions_branch_blind_review_live_and_postdeploy(section):
    for word in ("分支", "盲審", "上線", "postdeploy.sh"):
        assert word in section, f"§③ 缺環節：{word}"


def test_warns_against_hand_editing_pages(section):
    """舊版寫「Claude 找出全站所有顯示這些數字的地方、一次改完」——正是漏改的來源。"""
    assert "手" in section or "不要" in section or "禁止" in section
    assert "找出全站所有顯示這些數字的地方、一次改完、push" not in section


def test_no_absolute_claim_that_scripts_change_every_number(section):
    """Codex 盲審 C-09：前段寫「頁面上不手改數字」的全稱句，後段又要人工改
    158 處文案——操作者只讀前半段就會漏掉。"""
    assert "頁面上不手改數字" not in section
    assert "158" in section, "要講清楚還有多少處文案要人工改"


def test_postdeploy_is_described_as_verify_plus_manual_followup(section):
    """C-08：postdeploy 不是「一鍵全做完」，收據裡還有 pending 的人工項。"""
    assert "POSTDEPLOY_OK" in section
    assert "pending" in section or "收據" in section

"""行動頁（/act/）內容閘（2026-10-18 官網第二輪，Codex 健檢第 5 件）。

三件事：
  1. 不再出現「上半年」這類停在年初的優先追蹤標籤。
  2. 「N 種身份 · N 種行動」標題的 N ＝ 頁面實際的身份入口卡數（.action-card）。
  3. 「最新活動」區的活動卡（data-event-id，id 以日期開頭）依日期新→舊，第一筆為最新。
"""
import re

import pytest


@pytest.fixture(scope="module")
def act_html(public_dir):
    return (public_dir / "act" / "index.html").read_text(encoding="utf-8")


def test_act_has_no_stale_first_half_label(act_html):
    assert "上半年" not in act_html, "/act/ 仍有「上半年」字樣（優先追蹤標籤過期）"


def test_act_identity_heading_matches_card_count(act_html):
    m = re.search(r"<h2>(\d+) 種身份 · (\d+) 種行動</h2>", act_html)
    assert m, "找不到「N 種身份 · N 種行動」標題"
    cards = len(re.findall(r'<div class="action-card\b', act_html))
    assert int(m.group(1)) == int(m.group(2)) == cards, (
        f"標題寫 {m.group(1)}／{m.group(2)}，實際身份入口卡 {cards} 張"
    )


def test_act_latest_events_sorted_newest_first(act_html):
    start = act_html.index("<h2>最新活動</h2>")
    end = act_html.index("</section>", start)
    ids = re.findall(r'data-event-id="(\d{4}-\d{2}-\d{2})-[^"]+"', act_html[start:end])
    assert len(ids) >= 2, f"最新活動區活動卡不足：{ids!r}"
    assert ids == sorted(ids, reverse=True), f"最新活動未依日期新→舊：{ids!r}"

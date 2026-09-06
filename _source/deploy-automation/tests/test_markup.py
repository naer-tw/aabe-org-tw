"""② 位置標記檢查：頁面上的數字必須包在 data-metric 裡，且顯示值等於 numbers.json 的 display。

本檔刻意不 import numbers_check，改用獨立的小解析器——驗證者與生產者共用同一支解析器時，
解析器本身的錯誤會同時騙過兩邊。
"""
import json
import re

import pytest

OPEN_TAG = re.compile(r'<(?P<tag>[a-zA-Z][\w-]*)\b[^>]*\bdata-metric="(?P<id>[^"]+)"[^>]*>')

# 每頁預期的標記數（id -> 次數）
EXPECTED = {
    "index.html": {
        "valid_surveys": 1, "single_reach": 1, "partners": 2, "press_coverage": 1,
        "buzz_1y": 1, "actions": 2, "press_releases": 1, "policy_briefs": 1, "buzz_3y": 1,
    },
    "methodology/index.html": {
        "partners": 1, "press_releases": 1, "actions": 1,
        "buzz_3y": 1, "policy_briefs": 1, "legislators": 1,
    },
    "impact/index.html": {
        "partners": 1, "press_releases": 1, "actions": 1,
        "buzz_3y": 1, "legislators": 1,
    },
}


def strip_tags(html: str) -> str:
    """只留讀者看得到的文字：<style>／<script> 內容不算文案。"""
    body = re.sub(r"<(style|script)\b.*?</\1>", "", html, flags=re.S | re.I)
    return re.sub(r"\s+", "", re.sub(r"<[^>]*>", "", body))


def find_marked(src: str):
    """回傳 [(id, 顯示文字, 行號)]，用深度計數找對應的收尾標籤（可含巢狀同名標籤）。"""
    out = []
    for m in OPEN_TAG.finditer(src):
        tag, mid = m.group("tag"), m.group("id")
        pat = re.compile(r"</?" + re.escape(tag) + r"\b[^>]*>", re.I)
        depth, pos, end = 1, m.end(), None
        while depth:
            t = pat.search(src, pos)
            if not t:
                break
            if t.group(0).startswith("</"):
                depth -= 1
                if depth == 0:
                    end = t.start()
            elif not t.group(0).endswith("/>"):
                depth += 1
            pos = t.end()
        assert end is not None, f"{mid} 的 <{tag}> 沒有收尾"
        out.append((mid, strip_tags(src[m.end():end]), src[:m.start()].count("\n") + 1))
    return out


@pytest.fixture(scope="module")
def display(numbers_path):
    data = json.loads(numbers_path.read_text(encoding="utf-8"))
    return {m["id"]: m["display"] for m in data["metrics"]}


@pytest.mark.parametrize("page", sorted(EXPECTED))
def test_marked_counts(public_dir, page):
    marked = find_marked((public_dir / page).read_text(encoding="utf-8"))
    got = {}
    for mid, _, _ in marked:
        got[mid] = got.get(mid, 0) + 1
    assert got == EXPECTED[page], f"{page} 標記數不符"


@pytest.mark.parametrize("page", sorted(EXPECTED))
def test_marked_display_matches_source_of_truth(public_dir, page, display):
    for mid, shown, line in find_marked((public_dir / page).read_text(encoding="utf-8")):
        assert mid in display, f"{page}:{line} 用了 numbers.json 沒有的 id：{mid}"
        assert shown == display[mid], f"{page}:{line} {mid} 顯示 {shown}，真源是 {display[mid]}"


@pytest.mark.parametrize("page", sorted(EXPECTED))
def test_copy_text_untouched(public_dir, page, repo_root):
    """只包數字本體、不動文案：去掉所有標籤後的純文字，必須與改標記前完全一致。"""
    backup = repo_root.parent.parent.parent / "Backups" / "20260906_官網數據真源" / (
        "index.html" if page == "index.html" else page.replace("/index.html", "_index.html"))
    if not backup.exists():
        pytest.skip(f"找不到改前備份：{backup}")
    now = strip_tags((public_dir / page).read_text(encoding="utf-8"))
    before = strip_tags(backup.read_text(encoding="utf-8"))
    assert now == before, f"{page} 的可見文字被改動了（標記只能包數字，不得改文案）"


def test_wrapper_span_does_not_become_a_flex_item(public_dir):
    """首頁 .m-num 是 flex 容器（gap:5px）。data-metric 包一層 span 會讓數字與
    「+／份／篇」擠在一起——必須用 display:contents 讓殼退出版面。
    移掉這條 CSS 會讓六張卡片的排版悄悄變樣，所以鎖在測試裡。"""
    css = (public_dir / "index.html").read_text(encoding="utf-8")
    assert ".m-num [data-metric] { display: contents; }" in css

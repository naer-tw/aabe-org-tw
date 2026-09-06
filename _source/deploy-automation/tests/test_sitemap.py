"""⑥ sitemap.xml：本次上線的四頁 lastmod 要改成 2026-09-06。"""
import re

import pytest

DEPLOY_DATE = "2026-09-06"
UPDATED = [
    "https://aabe.org.tw/",
    "https://aabe.org.tw/methodology/",
    "https://aabe.org.tw/contact/",
    "https://aabe.org.tw/press/",
]

URL_BLOCK = re.compile(r"<url>(.*?)</url>", re.S)


@pytest.fixture(scope="module")
def entries(public_dir):
    xml = (public_dir / "sitemap.xml").read_text(encoding="utf-8")
    out = {}
    for block in URL_BLOCK.findall(xml):
        loc = re.search(r"<loc>(.*?)</loc>", block).group(1).strip()
        mod = re.search(r"<lastmod>(.*?)</lastmod>", block)
        out[loc] = mod.group(1).strip() if mod else None
    return out


@pytest.mark.parametrize("loc", UPDATED)
def test_lastmod_updated(entries, loc):
    assert loc in entries, f"sitemap 沒有 {loc}"
    assert entries[loc] == DEPLOY_DATE


def test_other_pages_untouched(entries):
    """沒改內容的頁面不動 lastmod——謊報更新日期會讓搜尋引擎降低信任。"""
    others = {loc: mod for loc, mod in entries.items() if loc not in UPDATED}
    assert others, "sitemap 應該還有其他頁"
    assert all(mod != DEPLOY_DATE for mod in others.values()), \
        f"這些頁沒改內容卻標了 {DEPLOY_DATE}：" \
        f"{[l for l, m in others.items() if m == DEPLOY_DATE]}"


def test_all_lastmod_are_iso_dates(entries):
    for loc, mod in entries.items():
        if mod is not None:
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", mod), f"{loc} lastmod 格式怪：{mod}"

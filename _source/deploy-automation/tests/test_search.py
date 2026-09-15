"""⑧ 站內搜尋（Pagefind，第三批②，2026-09-15）。

驗兩件事：
  1. `public/pagefind/` 索引檔存在且非空（`npm run search:index` 或
     `_source/deploy-automation/build_search_index.sh` 產出，gitignore 排除、
     不進 repo——本機沒跑過 build 就會直接 SKIP，不算失敗）。
  2. `/press/all/` 頁面有搜尋框，輸入「營養午餐」後能看到 ≥1 筆結果卡片。

注意：`local_site` fixture 是純 `http.server`，不會附加 `src/index.js` 的
CSP header（該檔對「所有」回應都加 CSP，含 pagefind.js／wasm）。這裡驗的是
「搜尋 UI 邏輯」本身；CSP 是否真的放行 WebAssembly.instantiate（Pagefind
用 WASM 編譯索引，需要 script-src 含 'wasm-unsafe-eval'，否則瀏覽器直接
CompileError、搜尋完全無法用）只有實際跑 Worker（`wrangler dev`）才會套用
真實 CSP header，這裡的 http.server 測不到。2026-09-15 已用 `wrangler dev`
手動驗證過：加 'wasm-unsafe-eval' 前 WebAssembly.instantiate 100% 被 CSP
擋下（CompileError），加了之後四個查詢（營養午餐／特教／兒少權／霸凌）
皆 ≥1 筆結果，詳見改動摘要 `_source/審查/官網第三批_②搜尋_改動摘要_20260915.md`。
"""
from pathlib import Path

import pytest


def test_pagefind_index_exists(public_dir: Path):
    index_dir = public_dir / "pagefind"
    if not (index_dir / "pagefind.js").exists():
        pytest.skip(
            "public/pagefind/ 索引未建置——先跑 `npm run search:index` "
            "或 `_source/deploy-automation/build_search_index.sh`"
        )
    assert (index_dir / "pagefind-entry.json").exists(), "缺 pagefind-entry.json"
    # 索引目錄不能是空殼
    files = list(index_dir.rglob("*"))
    assert len(files) > 5, f"public/pagefind/ 檔案數異常少（{len(files)}），像是建置失敗的半成品"


def test_search_all_page_has_search_box(page, local_site):
    page.goto(local_site + "/press/all/")
    box = page.locator("#siteSearchInput")
    assert box.count() == 1, "/press/all/ 找不到 #siteSearchInput 搜尋框"
    btn = page.locator("#siteSearchForm button[type=submit]")
    assert btn.count() == 1, "/press/all/ 找不到搜尋送出按鈕"


def test_homepage_has_search_box_linking_to_press_all(page, local_site):
    page.goto(local_site + "/")
    box = page.locator("#lqSearchInput")
    assert box.count() == 1, "首頁「依生活問題找議題」區塊找不到 #lqSearchInput 搜尋框"
    form = page.locator("form:has(#lqSearchInput)")
    assert form.get_attribute("action") == "/press/all/", "首頁搜尋框沒有導向 /press/all/"


@pytest.mark.parametrize("query", ["營養午餐", "特教", "兒少權", "霸凌"])
def test_search_query_returns_results(page, local_site, public_dir: Path, query):
    if not (public_dir / "pagefind" / "pagefind.js").exists():
        pytest.skip("public/pagefind/ 索引未建置，無法實測搜尋結果")

    page.goto(local_site + "/press/all/")
    page.fill("#siteSearchInput", query)
    page.click("#siteSearchForm button[type=submit]")
    page.wait_for_selector("#searchStatus:not([hidden])", timeout=5000)
    page.wait_for_timeout(500)

    status_text = page.locator("#searchStatus").inner_text()
    assert query in status_text, f"搜尋狀態列沒有回顯查詢字「{query}」：{status_text!r}"
    assert "沒有找到" not in status_text, f"「{query}」搜尋不到任何結果：{status_text!r}"

    cards = page.locator("#searchResults .article-card")
    assert cards.count() >= 1, f"「{query}」結果卡片數為 0"

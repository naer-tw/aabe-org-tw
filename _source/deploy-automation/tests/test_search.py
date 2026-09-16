"""⑧ 站內搜尋（Pagefind，第三批②，2026-09-15；第四輪納入政策站，2026-09-16）。

驗幾件事：
  1. `public/pagefind/` 索引檔存在且非空（`npm run search:index` 或
     `_source/deploy-automation/build_search_index.sh` 產出——已納入版控，
     本機沒跑過 build 才會 SKIP，不算失敗）。
  2. `/press/all/` 頁面有搜尋框，輸入「營養午餐」後能看到 ≥1 筆結果卡片。
  3.（第四輪）`public/pagefind-policy/` 索引存在且頁數 ≥40（47 篇政策站文章，
     見 `_source/deploy-automation/build_policy_search_staging.py`）。
  4.（第四輪）搜「霸凌」能在合併結果裡找到至少一筆 policy.aabe.org.tw 連結，
     且點擊卡片標題連結的 href 以 https://policy.aabe.org.tw/ 開頭。

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


def test_policy_pagefind_index_exists(public_dir: Path):
    index_dir = public_dir / "pagefind-policy"
    if not (index_dir / "pagefind.js").exists():
        pytest.skip(
            "public/pagefind-policy/ 索引未建置——先跑 "
            "`_source/deploy-automation/build_search_index.sh`"
            "（需要 sibling repo `_policy-deploy`，或設環境變數 POLICY_SITE_DIR）"
        )
    entry = index_dir / "pagefind-entry.json"
    assert entry.exists(), "缺 pagefind-policy/pagefind-entry.json"
    import json
    data = json.loads(entry.read_text(encoding="utf-8"))
    page_count = sum(v.get("page_count", 0) for v in data.get("languages", {}).values())
    assert page_count >= 40, f"政策站索引頁數 {page_count} < 40（預期 47 篇左右）"


@pytest.mark.parametrize(
    "query,expected_url_fragment",
    [
        ("營養午餐", "/press/2026-08-28-school-lunch-100day-check/"),
        ("營養午餐", "/press/2026-07-09-school-lunch-law-toxic-oil/"),
        ("校園安全", "/press/2026-07-09-school-lunch-law-toxic-oil/"),
    ],
)
def test_search_cjk_bigram_fallback_recovers_press_pages(
    page, local_site, public_dir: Path, query, expected_url_fragment
):
    """2026-09-16 中文分詞退化修法驗收（見 _source/審查/官網_搜尋分詞退化_診斷_20260916.md）。

    修法前：新增 `/briefs/*` 政策摘要頁後，Pagefind 對「營養午餐」「校園安全」
    這類剛好等於摘要頁標題起手片語的查詢，會用精確詞比對整個蓋掉模糊比對，
    讓原本查得到的新聞稿從結果中消失（命中數從 5／21 坍縮到 1，且首筆換成
    `/briefs/*` 頁）。修法：整詞結果 <3 筆時加開 2 字滑窗子查詢、分數打 5 折
    後與整詞結果合併去重。本測試驗證新聞稿頁重新出現在結果卡片清單中。
    """
    if not (public_dir / "pagefind" / "pagefind.js").exists():
        pytest.skip("public/pagefind/ 索引未建置，無法實測搜尋結果")

    page.goto(local_site + "/press/all/")
    page.fill("#siteSearchInput", query)
    page.click("#siteSearchForm button[type=submit]")
    page.wait_for_selector("#searchStatus:not([hidden])", timeout=5000)
    page.wait_for_timeout(500)

    links = page.locator("#searchResults .article-card h3 a")
    hrefs = [links.nth(i).get_attribute("href") for i in range(links.count())]
    matches = [h for h in hrefs if h and expected_url_fragment in h]
    assert matches, (
        f"「{query}」搜尋結果沒有找到 {expected_url_fragment}（新聞稿被政策摘要頁"
        f"擠出結果，中文分詞退化修法未生效）：目前結果 {hrefs!r}"
    )


@pytest.mark.parametrize(
    "query,min_count",
    [
        ("特教", 16),
        ("兒少權", 20),
        ("霸凌", 10),
        ("免費營養午餐", 2),
    ],
)
def test_search_regression_counts_not_below_prefix(
    page, local_site, public_dir: Path, query, min_count
):
    """回歸檢查：中文分詞退化修法（2 字滑窗 fallback）不能讓修法前本來就正常的
    查詢結果數變少。門檻值取自本檔套 patch 前，對真實 `/press/all/` 頁面（本站
    ＋政策站鏡射合併後）用 Playwright 實跑量到的卡片數（非診斷檔對照表的單一
    索引 `pf.search()` 數字——那是不同量測口徑，UI 是本站＋政策站合併＋slice
    top 20，單索引數字不能直接套用）：特教 16、兒少權 20、霸凌 10、免費營養
    午餐 2。fallback 邏輯只在整詞結果 <3 筆時「加開」子查詢並與整詞結果合併
    去重（byUrl map 只增不減），理論上結果數只增不減，本測試確認這個假設
    成立（即使「免費營養午餐」本身整詞結果 <3 筆會觸發 fallback，也不該低於
    修法前的 2 筆）。
    """
    if not (public_dir / "pagefind" / "pagefind.js").exists():
        pytest.skip("public/pagefind/ 索引未建置，無法實測搜尋結果")

    page.goto(local_site + "/press/all/")
    page.fill("#siteSearchInput", query)
    page.click("#siteSearchForm button[type=submit]")
    page.wait_for_selector("#searchStatus:not([hidden])", timeout=5000)
    page.wait_for_timeout(1200)

    cards = page.locator("#searchResults .article-card")
    assert cards.count() >= min_count, (
        f"「{query}」結果卡片數 {cards.count()} < 修法前門檻 {min_count}"
        "（回歸：修法可能誤傷了原本正常的查詢）"
    )


BASE_30_CHARS = "國家教育政策兒少權益福利醫療衛生司法勞動環境保護能源交通建設科技文化體育"
assert len(set(BASE_30_CHARS)) >= 30, "BASE_30_CHARS 唯一字數不足 30，量不到 C1 的 8-bigram 上限"
LONG_CJK_QUERY = (BASE_30_CHARS * 7)[:200]
assert len(LONG_CJK_QUERY) == 200


def test_search_long_cjk_query_bounds_search_calls(page, local_site, public_dir: Path):
    """C1 資源耗盡修法驗收（同源補審 PR2）。

    修法前：N 字全漢字查詢會對每個索引發 N-1 次未去重、無上限的 `pf.search()`
    （196 字查詢實量 196 次、唯一 bigram 只有 28 個，約 85% 重複；四段長度
    196／600／1200／2000 字耗時 5.06／14.31／26.68／43.56 秒，線性成長無上限）。
    修法：查詢先截到前 30 字元、滑窗結果 Set 去重、唯一 bigram 最多取前 8 個。
    本測試用 200 字全漢字查詢（前 30 字全不重複，確保撞到 8 的上限而非因為
    重複字提早收斂），驗證兩個索引合計 `pf.search()` 呼叫數不超過
    2 索引 ×（1 次整詞＋8 次子查詢）＝18 次，且在 3 秒內完成。
    """
    if not (public_dir / "pagefind" / "pagefind.js").exists():
        pytest.skip("public/pagefind/ 索引未建置，無法實測搜尋結果")

    page.goto(local_site + "/press/all/")
    calls_before = page.evaluate("window.__pfSearchCalls || 0")
    assert calls_before == 0, f"計數器初始值應為 0，實際 {calls_before}（頁面載入時就有查詢？）"

    import time
    t0 = time.monotonic()
    page.fill("#siteSearchInput", LONG_CJK_QUERY)
    page.click("#siteSearchForm button[type=submit]")
    page.wait_for_selector("#searchStatus:not([hidden])", timeout=5000)
    page.wait_for_function(
        "document.getElementById('searchStatus').textContent.indexOf('搜尋中') === -1",
        timeout=10000,
    )
    elapsed = time.monotonic() - t0

    calls_after = page.evaluate("window.__pfSearchCalls || 0")
    assert calls_after <= 18, (
        f"200 字全漢字查詢觸發 pf.search() {calls_after} 次，超過兩索引合計上限 18 次"
        "（每索引 1 次整詞＋最多 8 次子查詢）——bigram 去重／上限可能失效"
    )
    assert elapsed < 3.0, f"200 字查詢耗時 {elapsed:.2f}s，超過 3 秒上限（資源耗盡修法可能失效）"


CROSSCHECK_QUERIES = [
    "營養午餐", "校園安全", "實驗教育", "神經多樣性",
    "少子女化", "特教", "兒少權", "霸凌",
]


def _search_result_hrefs(pg, site, query):
    pg.goto(site + "/press/all/")
    pg.fill("#siteSearchInput", query)
    pg.click("#siteSearchForm button[type=submit]")
    pg.wait_for_selector("#searchStatus:not([hidden])", timeout=5000)
    pg.wait_for_function(
        "document.getElementById('searchStatus').textContent.indexOf('搜尋中') === -1",
        timeout=10000,
    )
    links = pg.locator("#searchResults .article-card h3 a")
    return [links.nth(i).get_attribute("href") for i in range(links.count())]


@pytest.mark.parametrize("query", CROSSCHECK_QUERIES)
def test_search_branch_results_superset_of_main_ordered(
    page, browser, local_site, local_site_main, public_dir: Path, query
):
    """C2 擠出既有結果修法驗收（同源補審 PR2）：main 版（修法前）查得到的
    結果，分支版（修法後）一筆都不能少（集合斷言），且分支版前 N 筆
    （N＝main 版筆數）順序需與 main 版一致——因為本修法沒有改動整詞查詢
    本身的算分與排序，只改「要不要／怎麼補 fallback」，main 版原本查得到
    的整詞結果理應原封不動出現在分支版結果最前面。
    """
    if not (public_dir / "pagefind" / "pagefind.js").exists():
        pytest.skip("public/pagefind/ 索引未建置，無法實測搜尋結果")

    main_ctx = browser.new_context()
    main_page = main_ctx.new_page()
    try:
        main_hrefs = _search_result_hrefs(main_page, local_site_main, query)
    finally:
        main_ctx.close()

    branch_hrefs = _search_result_hrefs(page, local_site, query)

    missing = [h for h in main_hrefs if h not in branch_hrefs]
    assert not missing, (
        f"「{query}」main 版查得到、分支版消失：{missing!r}\n"
        f"main={main_hrefs!r}\nbranch={branch_hrefs!r}"
    )

    n = len(main_hrefs)
    assert branch_hrefs[:n] == main_hrefs, (
        f"「{query}」分支版前 {n} 筆順序與 main 版不一致：\n"
        f"main={main_hrefs!r}\nbranch={branch_hrefs[:n]!r}"
    )


def test_search_bullying_includes_policy_site_result(page, local_site, public_dir: Path):
    if not (public_dir / "pagefind" / "pagefind.js").exists():
        pytest.skip("public/pagefind/ 索引未建置")
    if not (public_dir / "pagefind-policy" / "pagefind.js").exists():
        pytest.skip("public/pagefind-policy/ 索引未建置，無法驗證政策站合併結果")

    page.goto(local_site + "/press/all/")
    page.fill("#siteSearchInput", "霸凌")
    page.click("#siteSearchForm button[type=submit]")
    page.wait_for_selector("#searchStatus:not([hidden])", timeout=5000)
    page.wait_for_timeout(500)

    links = page.locator("#searchResults .article-card h3 a")
    hrefs = [links.nth(i).get_attribute("href") for i in range(links.count())]
    policy_hrefs = [h for h in hrefs if h and h.startswith("https://policy.aabe.org.tw/")]
    assert policy_hrefs, f"「霸凌」合併結果沒有任何 policy.aabe.org.tw 連結：{hrefs!r}"

"""⑥ sitemap：改過的頁面 lastmod 要是部署日，沒改的不准動；子 sitemap 動了，
父索引 sitemap_index.xml 也要跟著動。

2026-09-06 依 Codex 盲審 C-06 改寫：舊版把「本次上線的四頁」寫死在測試裡，
結果這次真的改過的 /impact/ 被排除在外，漏更新 lastmod 卻仍判綠。
現在改成從 `git diff <base>...HEAD -- public/**/*.html` 反推應更新的 URL。

2026-09-06 再修一次「同一天第二次部署」的假警報：基準原本寫死 `main`，當天第一批
頁面併進 main 之後，同一天的第二個分支跑起來會把那些頁面算成「沒改卻標了今天」
（實測誤報 /、/press/、/methodology/、/impact/ 四頁，而且 `changed_urls` 在 main
上是空的，第一條測試必定紅）。基準改成「DEPLOY_DATE 當天之前的最後一次 commit」，
語意即「本次部署日以來改過的頁面」，同一天開幾個分支都成立；取不到就退回 main。

2026-09-14 官網 UIUX 第一批修法錯（分兩步才穩定）：`_url_of` 原本只處理了
`.../index.html` 這種目錄型頁面，第一次改到非 index 的 `.html` 檔
（`act/cwa-reform/hearing-speeches.html`）就把 `.html` 也算進網址，跟
sitemap.xml 裡登記的無副檔名網址對不上。改成一律去掉 `.html` 後，另一批
非 index 頁（研討會逐場紀錄 `records/sessions/S01.html` 等）又露餡——這批
sitemap 裡登記的偏偏是「帶 .html」的原始形式，全站對這件事沒有統一規則。
改成 `_url_candidates()` 兩種形式都算，哪個在 sitemap 裡就認哪個，不再
用單一寫死的轉換規則賭全站一致。另外 `404.html` 是錯誤頁，本來就不、也
不該進 sitemap（sitemap.xml 裡本來就沒有它），改動它不代表要新增一筆
sitemap 條目，明確排除。
"""
import re
import subprocess

import pytest

DEPLOY_DATE = "2026-09-25"
FALLBACK_BASE_REF = "main"   # 取不到日期基準時的退路
SITE = "https://aabe.org.tw"
EXCLUDED_FROM_SITEMAP = {"public/404.html"}  # 錯誤頁，本來就不進 sitemap

URL_BLOCK = re.compile(r"<url>(.*?)</url>", re.S)
SITEMAP_BLOCK = re.compile(r"<sitemap>(.*?)</sitemap>", re.S)


def _url_candidates(rel: str) -> list[str]:
    """回傳這個檔案在 sitemap 裡『可能』對應的網址：
    public/about/index.html → [https://aabe.org.tw/about/]
    public/act/cwa-reform/hearing-speeches.html →
        [.../act/cwa-reform/hearing-speeches, .../act/cwa-reform/hearing-speeches.html]
    （順序即優先序：先試無副檔名，因為那是多數非 index 頁的慣例；
    呼叫端會挑「真的出現在 sitemap 裡」的那一個，兩個都沒有才算 missing。）
    """
    path = rel[len("public"):]
    if path.endswith("/index.html"):
        return [SITE + path[: -len("index.html")]]
    if path.endswith(".html"):
        return [SITE + path[: -len(".html")], SITE + path]
    return [SITE + path]


def _base_ref(repo_root) -> str:
    """本次部署日之前的最後一次 commit；取不到就退回 main。

    `--before=2026-09-06` 會被 git 的 approxidate 補上「現在的時分秒」，等於把當天
    稍早的 commit 也算進去——那正是要排除的東西，所以時間要寫滿 T00:00:00。
    """
    r = subprocess.run(
        ["git", "rev-list", "-1", f"--before={DEPLOY_DATE}T00:00:00", "main"],
        capture_output=True, text=True, cwd=repo_root)
    ref = r.stdout.strip()
    return ref if r.returncode == 0 and ref else FALLBACK_BASE_REF


@pytest.fixture(scope="module")
def entries(public_dir):
    xml = (public_dir / "sitemap.xml").read_text(encoding="utf-8")
    out = {}
    for block in URL_BLOCK.findall(xml):
        loc = re.search(r"<loc>(.*?)</loc>", block).group(1).strip()
        mod = re.search(r"<lastmod>(.*?)</lastmod>", block)
        out[loc] = mod.group(1).strip() if mod else None
    return out


@pytest.fixture(scope="module")
def changed_urls(repo_root, entries):
    # 用兩點 diff（含工作區未 commit 的改動）：部署上去的是工作區的內容，
    # 不是只有已 commit 的部分。新增的頁面在 commit 前是 untracked，diff 看不到，
    # 要另外把它們撈進來——否則「新頁忘了寫進 sitemap」這種漏法測不出來。
    base = _base_ref(repo_root)
    r = subprocess.run(["git", "diff", "--name-only", base, "--", "public"],
                       capture_output=True, text=True, cwd=repo_root)
    if r.returncode != 0:
        pytest.skip(f"取不到 git diff（{r.stderr.strip()}）")
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "public"],
        capture_output=True, text=True, cwd=repo_root)
    files = [
        f for f in (r.stdout + "\n" + untracked.stdout).split()
        if f.endswith(".html") and f not in EXCLUDED_FROM_SITEMAP
    ]
    resolved = set()
    for f in files:
        candidates = _url_candidates(f)
        match = next((c for c in candidates if c in entries), None)
        resolved.add(match or candidates[0])  # 兩種形式都沒有 → 用第一個候選讓它顯示成 missing
    return sorted(resolved)


@pytest.fixture(scope="module")
def index_entries(public_dir):
    xml = (public_dir / "sitemap_index.xml").read_text(encoding="utf-8")
    out = {}
    for block in SITEMAP_BLOCK.findall(xml):
        loc = re.search(r"<loc>(.*?)</loc>", block).group(1).strip()
        mod = re.search(r"<lastmod>(.*?)</lastmod>", block)
        out[loc] = mod.group(1).strip() if mod else None
    return out


def test_every_changed_page_has_todays_lastmod(entries, changed_urls):
    assert changed_urls, "這個分支沒改任何 public/*.html？測試基準要檢查"
    missing = [u for u in changed_urls if u not in entries]
    assert not missing, f"改過的頁面不在 sitemap 裡：{missing}"
    stale = [(u, entries[u]) for u in changed_urls if entries[u] != DEPLOY_DATE]
    assert not stale, f"改過卻沒更新 lastmod：{stale}"


def test_unchanged_pages_keep_their_lastmod(entries, changed_urls):
    """沒改內容的頁面不動 lastmod——謊報更新日期會讓搜尋引擎降低信任。"""
    others = {loc: mod for loc, mod in entries.items() if loc not in changed_urls}
    assert others, "sitemap 應該還有其他頁"
    lied = [loc for loc, mod in others.items() if mod == DEPLOY_DATE]
    assert not lied, f"這些頁沒改內容卻標了 {DEPLOY_DATE}：{lied}"


def test_sitemap_index_follows_the_main_site(index_entries, changed_urls):
    """主站子 sitemap 有變動時，父索引的 lastmod 也要更新，否則搜尋引擎看不到新鮮度。"""
    main_sitemap = f"{SITE}/sitemap.xml"
    assert main_sitemap in index_entries, "sitemap_index.xml 缺主站 sitemap"
    if changed_urls:
        assert index_entries[main_sitemap] == DEPLOY_DATE, \
            "主站 sitemap 改了，sitemap_index.xml 的 lastmod 沒跟著改"


def test_all_lastmod_are_iso_dates(entries, index_entries):
    for loc, mod in {**entries, **index_entries}.items():
        if mod is not None:
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", mod), f"{loc} lastmod 格式怪：{mod}"

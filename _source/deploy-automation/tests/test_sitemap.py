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
"""
import re
import subprocess

import pytest

DEPLOY_DATE = "2026-09-11"
FALLBACK_BASE_REF = "main"   # 取不到日期基準時的退路
SITE = "https://aabe.org.tw"

URL_BLOCK = re.compile(r"<url>(.*?)</url>", re.S)
SITEMAP_BLOCK = re.compile(r"<sitemap>(.*?)</sitemap>", re.S)


def _url_of(rel: str) -> str:
    """public/about/index.html → https://aabe.org.tw/about/"""
    path = rel[len("public"):]
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return SITE + path


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
def changed_urls(repo_root):
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
    files = [f for f in (r.stdout + "\n" + untracked.stdout).split() if f.endswith(".html")]
    return sorted({_url_of(f) for f in files})


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

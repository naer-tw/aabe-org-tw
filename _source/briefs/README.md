# 可下載政策摘要（briefs）── 格式與新增議題方法

依據：`~/Documents/Claude/MAC的技能與工具中心/shared/HANDOFFS/2026-09-14_官網第三批_交接包.md` 第三批②。

## 這是什麼

每個重點議題一頁 A4 PDF，欄位固定七項：**問題、具體建議、需協作機關、國教盟已做、
原始來源、更新日期、合作窗口**。單一來源＝本目錄的 `<issue>.md`，經
`_source/deploy-automation/build_briefs.py` 產生：

```
_source/briefs/<issue>.md  →  public/briefs/<issue>/index.html（HTML 版，供搜尋引擎索引）
                            →  public/briefs/<issue>.pdf（可下載 PDF，A4 一頁）
```

## 新增一個議題

1. 複製 `school-lunch.md` 為 `<issue>.md`，issue 用英文 slug（例：`teacher-affairs`）。
2. 填 front-matter 四欄：
   - `issue`：slug，須與檔名一致
   - `title`：頁面標題（會出現在 `<title>`／頁首）
   - `updated`：`YYYY-MM-DD`
   - `contact`：合作窗口（固定「理事長 王瀚陽 0983-097-165」，除非理事長另指定）
3. 正文用 `## ` 開七個固定標題（順序與文字須逐字一致，程式用標題比對）：
   ```
   ## 問題
   ## 具體建議
   ## 需協作機關
   ## 國教盟已做
   ## 原始來源
   ## 更新日期
   ## 合作窗口
   ```
4. 內文只能寫**既有頁面/新聞稿已發布過的句子**（改寫可、不新創立場），每段/每條
   上方用 HTML 註解 `<!-- 出處：public/... 行N -->` 標明出處檔案與行號，出處註解
   會被保留在產出 HTML 原始碼裡（瀏覽器不顯示），供之後查證回溯。
5. 數字一律寫 `{{metric:<numbers.json 的 id>}}`，不可手打阿拉伯數字（黑數）。
   產生器會查 `_source/numbers.json`，找不到該 id 直接報錯中止，不會生出半成品頁。
   metric 值渲染時會包一層 `<span data-metric="<id>">`，讓 `numbers_check.py` 能守住
   之後任何人手改跑掉的風險。
6. 「原始來源」至少列 3 個 URL；「合作窗口」固定聯絡人（見 AABE 組織身分規則）。

## 產生

```bash
python3 _source/deploy-automation/build_briefs.py school-lunch
# 或不帶參數＝跑 _source/briefs/ 底下全部 *.md
python3 _source/deploy-automation/build_briefs.py
```

引擎優先用本機 Playwright Chromium（`~/.venvs/aabe-pw`）；若目前的 Python 沒裝
playwright，腳本會自動用 `os.execv` 切換到該 venv 的直譯器重跑一次，不需要手動
切換環境。若該 venv 也不可用，改用 WeasyPrint（需另外 `pip install weasyprint`）。

## 部署前檢核

新增或改動 briefs 後，兩件事都要跑：

```bash
# 1. 一頁限制（pypdf 或 pdfinfo 二擇一，CI 用 pdfinfo）
pdfinfo public/briefs/<issue>.pdf | grep '^Pages:'   # 必須是 1

# 2. 黑數/標記守門（新增 data-metric 標記第一次要 --update-manifest 登記，
#    之後改動只要沒改標記數量，一般跑法即可）
python3 _source/deploy-automation/numbers_check.py --root public
```

## 超過一頁怎麼辦

不准刪欄位。依序：① 精簡句子（既有句子摘要，不新創論點）② 縮小
`_template.html` 的 `font-size`／`line-height`／`margin`（單位 mm/px 集中在檔頭
方便統一調）③ 減少「國教盟已做」條列則數（最舊的先減，不減最近 100 日內事件）。

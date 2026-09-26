# 官網內容生命週期總表（真源，隨 repo 走）

> 建檔：2026-09-16（理事長裁「照建議」落地；提案原文＝看板 議題_指揮部運作/3_工作檔/2026-09-16_制度提案_官網內容生命週期與session分工.md）。
> 一句話原理：**官網不是一頁一頁改，是「幾份資料檔」改了之後，全站由腳本跟著變。** 每個 session 動內容前先查這張表：這件內容動哪份資料檔、跑哪支腳本、驗哪道閘。

## 內容型 → 真源 → 連動頁 → 腳本 → 閘

| 內容型 | 真源（改這裡） | 跟著變的頁面 | 要跑的腳本 | 閘（不過不准推） |
|---|---|---|---|---|
| 新聞稿 | `Projects/新聞稿/YYYY-MM-DD_主題/`（SOP v1.3 信頭版）→ `aabe-publish` 技能上架 | 首頁最新六則、/press/all/ 卡（含議題標籤）、sitemap、搜尋索引 | aabe-publish 管線 → `build_search_index.sh` | lint、numbers_check、sitemap lastmod、test_search |
| 活動（發布／結束） | `_source/events.json`（狀態、徽章、CTA、紀錄連結） | 首頁活動卡、/events/ 總表、/act/、活動專頁 | `apply_events.py` → 索引重建 | events_check、test_apply_events、涵蓋率 |
| 會議／研討會紀錄 | 各研討會全紀錄站 repo（如 2026神經多樣性）＋ events.json 的 `record_url` | 活動專頁「看紀錄」按鈕、搜尋索引（若在官網網域） | apply_events → 索引 | 同上 |
| 數字（人次、篇數、場次） | `_source/numbers.json`（唯一真源） | 全站 `data-metric` 標記處、六篇政策摘要 | `apply_numbers.py`、`build_briefs.py` | numbers_check（黑數＝擋） |
| 政策摘要 PDF | `_source/briefs/<議題>.md` | `/briefs/`、PDF、搜尋索引 | `build_briefs.py` → 索引 | test_briefs（1 頁、七節、metric 全在真源） |
| 政策站文章 | `_policy-deploy`（另一 repo） | 官網卡摘要（sync-policy-articles）、官網搜尋第二索引 | `sync-policy-articles.py`、`build_search_index.sh` | test_search（政策站 ≥40 頁） |
| 工作報告 | `_source/reports/<slug>.md`（季度／半年度組織工作彙整，slug 格式 `YYYY-NN`＝該年度第 N 次報告） | `/reports/` 列表頁、`/reports/<slug>/` 單篇、首頁頁尾「工作報告」入口、搜尋索引 | `build_reports.py` → 索引重建 | test_reports（摘要／本期數字一覽／參考資料三錨點齊、治理內部字樣＝0、內部代號＝0、本期數字一覽出處欄不可空白、slug 格式合規、列表頁含每篇、產出 HTML 無「【」殘留） |

## 固定收尾（每次 push 後）

`postdeploy.sh --receipt`（線上數字比對＋IndexNow）→ GSC 請求索引（理事長 Chrome，指揮部可代操作）→ 看板日誌一行 → STATE 重生。

## 三條紅線

1. 新聞稿正文一字不改。
2. 數字只從 `numbers.json`。
3. 推上線由指揮部執行，但每次推之前必須先問理事長一句，理事長回「推」才動；說「部署」不等於「推」。（2026-09-25 理事長裁定，取代「理事長按」）

## 索引重建提醒

任何內容型改動（上表六型任一）落地後，都要跑 `_source/deploy-automation/build_search_index.sh --check`；兩份索引（官網＋政策站）都在版控內，**必須隨內容一起 push**，否則正式站搜尋會停在舊索引。

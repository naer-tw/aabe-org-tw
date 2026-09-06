# 官網數據更新與部署索引 SOP v1（2026-09-06）

> 理事長 2026-09-06 指示：上線的同時設計規則，讓以後每次部署都把「每個位置、每個數字」更新好，並把部署後的索引一起做完；規則由 fable 起草、Codex 盲審、合併後兩邊共同遵守。
> 原則：**單一真源、腳本檢查、部署即索引、經驗回寫**。人記不住十幾個位置，腳本記得住。

## 一、單一真源：`_source/numbers.json`
- 全站每一個「影響力數字」只在這個檔定義一次。每筆欄位：
  `id`（英文代號）、`value`（原始數值）、`display`（顯示字串，例 `66,247`）、`unit`（份／人次／篇／則／場／個）、`label`（中文標籤）、`period`（資料期間）、`method`（怎麼算，一句）、`source`（出處：看板清單路徑或原件）、`last_verified`（YYYY-MM-DD）、`cadence`（quarterly／event／yearly）、`owner`（指揮部／秘書處）、`notes`。
- 首批 id（2026-09-06）：`valid_surveys`（66,247 份）、`single_reach`（104,000 人次）、`partners`（168+）、`press_coverage`（3,000+ 篇，精確 3,017）、`buzz_1y`（2,889 則）、`actions`（286 場）；CH 05 舊數字帶與 `/methodology/`、`/impact/` 既有數字（113、47、7,917+ 等）也各建一筆，並註明與新區的期間差異。
- 數字的上游：`~/Desktop/國教盟指揮看板/議題_官網影響力數據/1_最新/20260905_清單_國教盟調查與觸及數據.md`（每筆附出處，經獨立核對）。改 numbers.json 前先改清單，並附出處。

## 二、位置登記：`data-metric` 標記（腳本掃得到才算存在）
- 頁面上每一處顯示這些數字的元素都要包 `<span data-metric="<id>">66,247</span>`（或 `data-metric="<id>" data-format="display"`）。沒有標記的數字＝黑數，腳本會抓出來報錯。
- `deploy-automation/numbers_check.py`：掃 `public/**/*.html`，列出每個 id 出現的檔案與行號（＝位置表），比對顯示值是否等於 numbers.json 的 `display`；另掃已知數值字串（例 `66,247`、`104,000`）出現在**未標記**處的情形。任一不符或黑數＝exit 1，擋部署。
- `deploy-automation/apply_numbers.py`：改了 numbers.json 後跑一次，把所有標記處的顯示值改成新值（一次改全站），並更新 `/methodology/` 表格的「最近更新」與 Changelog 一行。

## 三、更新節奏與責任
| 觸發 | 動作 | 誰 |
|---|---|---|
| 每季第一週（1／4／7／10 月） | 更新六數字＋方法頁「最近更新」；社群人數若秘書處給後台截圖則補上 | 指揮部（秘書處供數） |
| 每次調查、記者會、新聞稿發布 | 清單加一筆 → numbers.json 增量（例 `valid_surveys` 累加）→ apply → 部署 | 指揮部 |
| 每年 1 月 | 與影響力報告對帳，所有 `last_verified` 重驗 | 指揮部＋秘書處 |
- 不上網站的數字：社群人數（無後台截圖）、非本盟發起的附議數、兩份年度報告互打未拍板的數、夥伴主辦調查的樣本。

## 四、部署前檢查（缺一不推 main）
1. `python3 _source/deploy-automation/numbers_check.py` exit 0（位置表附在輸出）。
2. 改了規則或數字的頁面：`sitemap.xml` 對應 `<lastmod>` 改當天。
3. 對外數字改動 → 先過 Codex 盲審（照 `MAC的技能與工具中心/docs/codex-crosscheck-playbook.md`），再過人類閘（理事長一句「上線」）。
4. 分支上做、快轉併入 main；push main ＝ Cloudflare 自動部署，約 30–60 秒。

## 五、部署後索引（推完 main 五分鐘內做完，`deploy-automation/postdeploy.sh` 一鍵）
1. **實地驗證**：curl 線上首頁、方法頁、聯絡頁、媒體中心，比對 numbers.json 的 display 值與窗口電話；不符＝回報，不宣告完成。
2. **搜尋引擎**：`_source/indexnow-ping.sh` 推改動頁面（Bing／Yandex／Naver）；Google 由 `.github/workflows/indexnow.yml` 與 Search Console 既有流程處理（首頁與方法頁改動時到 GSC 請求索引一次）。
3. **AI 可讀層**：`public/llms.txt` 與 `humans.txt` 若含數字或窗口，同步（納入 numbers_check 掃描範圍）。
4. **看板**：`議題_官網影響力數據/_狀態.md` 最新交付行改當天＋當天日誌加一列（含 main commit hash、部署時間、驗證結果）。
5. **知識庫／清單**：清單檔的「已上官網」欄勾選日期；若數字源自知識庫卡片，卡片 caveat 加「已上官網 YYYY-MM-DD」。
6. **經驗回寫**：這次部署踩到的坑寫進本檔檔尾「經驗紀錄」，同型坑第二次出現升成腳本檢查。

## 六、Codex 與 fable 的分工
- fable（指揮部）：起草與維護本 SOP、numbers.json、看板同步；每次部署跑第四、五節。
- Codex：對外數字改動前的盲審（威脅模型固定：數字回源、單位混用、歸屬、內部互打、位置漏改、索引未更新）；每季一次冷讀官網三頁（首頁、方法頁、影響力頁）。
- 兩邊共用的檔：本 SOP、numbers.json、`codex-crosscheck-playbook.md`；改本 SOP 要同步 `官網維護手冊.md` §③ 的指引與 `~/.codex/AGENTS.md` 協作協定的「官網數字」一句。

## 七、經驗紀錄（append-only）
- 2026-09-06｜首次上線民意與聲量區（main acd6bbf）｜部署 30 秒內生效（curl 輪詢 15 秒一次首輪即 LIVE）｜坑：此前數字散在首頁、方法頁、影響力頁三處手改，方法頁 33 漏改半年未被發現；168 vs 173 兩個定義並存｜→ 本 SOP 建立單一真源與位置標記

## 變更紀錄
- 2026-09-06 v1 建檔｜指揮部（fable）起草，待 Codex 盲審

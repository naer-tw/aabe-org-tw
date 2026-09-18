# 官網數據更新與部署索引 SOP v1.1（2026-09-06）

> 理事長 2026-09-06 指示：上線的同時設計規則，讓以後每次部署都把「每個位置、每個數字」更新好，並把部署後的索引一起做完；規則由 fable 起草、Codex 盲審、合併後兩邊共同遵守。
> 原則：**單一真源、腳本檢查、部署即索引、經驗回寫**。人記不住十幾個位置，腳本記得住。

## 一、單一真源：`_source/numbers.json`
- 全站每一個「影響力數字」只在這個檔定義一次。每筆欄位：
  `id`（英文代號）、`value`（原始數值）、`display`（顯示字串，例 `66,247`）、`unit`（份／人次／篇／則／場／個）、`label`（中文標籤）、`period`（資料期間）、`method`（怎麼算，一句）、`source`（出處：看板清單路徑或原件）、`last_verified`（YYYY-MM-DD）、`cadence`（quarterly／event／yearly）、`owner`（指揮部／秘書處）、`status`、`notes`。
- **`status`（v1.1 新增，Codex 盲審 C-05）**：`approved`＝可由看板清單一手重算；`provisional`＝來源鏈目前只指向官網下游頁面，待秘書處／理事長拍板（腳本會在輸出列出，但不擋部署，因為這些數字早已在站上）；`draft`＝未裁決，**出現在頁面上就 exit 1**。新增指標一律先 `draft`。
- 另有三個選填欄位：`display_approx`（display 是刻意的近似對外值時必填 `true`，例 `press_coverage` 對外「3,000+」／實計 3,017；不填而數值對不上就 exit 1）、`previous_values`（改過的舊值，供「殘留舊值」掃描，例 `policy_briefs` 的 33、36）、`on_site: false`（真源有此數字但刻意不上站）。
- **`source` 不得只寫官網下游頁面**：至少要指到看板清單的某一列或一手原件。目前 `partners／actions／press_releases／policy_briefs／legislators` 五筆是 `source_status: downstream_only`，屬待補（見第七節待裁決事項）。
- 首批 id（2026-09-06）：`valid_surveys`（66,247 份）、`single_reach`（104,000 人次）、`partners`（168+）、`press_coverage`（3,000+ 篇，精確 3,017）、`buzz_1y`（2,889 則）、`actions`（286 場）；CH 05 舊數字帶與 `/methodology/`、`/impact/` 既有數字（113、47、7,917+ 等）也各建一筆，並註明與新區的期間差異。
- 數字的上游：`~/Desktop/國教盟指揮看板/議題_官網影響力數據/1_最新/20260905_清單_國教盟調查與觸及數據.md`（每筆附出處，經獨立核對）。改 numbers.json 前先改清單，並附出處。

## 二、位置登記：`data-metric` 標記（腳本掃得到才算存在）
- 頁面上每一處顯示這些數字的元素都要包 `<span data-metric="<id>">66,247</span>`。要讓單位、期間等欄位也吃真源，用 `data-metric-field`（例 `<span data-metric="valid_surveys" data-metric-field="unit">份</span>`）。沒有標記的數字＝黑數，腳本會抓出來報錯。
- `deploy-automation/numbers_check.py`：掃 `public/**/*.html` ＋ `llms.txt`／`humans.txt`，列出每個 id 出現的檔案與行號（＝位置表），比對顯示值是否等於真源對應欄位；另掃已知數值出現在**未標記**處的情形。任一不符＝exit 1，擋部署。v1.1 起還做三件事：
  1. **真源自檢**：欄位齊全、id 不重複、`value`／`display` 對得上、`status` 合法。
  2. **位置基線 `_source/numbers_manifest.json`**：登記每個檔案該有幾處標記。整張卡被刪、標記被拿掉、數量變少、或某個 id 全站都找不到，一律 exit 1（Codex 盲審 C-01：沒有基線＝刪掉就沒事）。刻意增刪標記後，人工覆核再跑 `--update-manifest`。
  3. **黑數別名表**：不再只比對逐字字串，會自動展開「帶／不帶逗號、全形數字與逗號、`6.6 萬份`／`3千篇` 這類量級寫法（要接單位才算命中）、`約／逾／超過／近／破` 等近似前綴、`previous_values` 的殘留舊值」；`3,000-8,000 字` 這種數值區間不算黑數。仍需要人工補的寫法（例四捨五入的 `約 66,000`）寫進該筆的 `scan_patterns`。
- **黑數 allowlist（`_source/numbers_allowlist.json`）綁語境**：每筆登記 `id ＋ file ＋ count ＋ contexts`（每一處所在整句的雜湊）。同一檔案裡刪掉一句合格文案、又在別處新增同值宣稱，筆數沒變也會被擋下（Codex 盲審 C-04）。逐處覆核語意與單位無誤後才跑 `--update-allowlist`。
- 位置表 `_source/數字位置表_20260906.md` 隨程式碼一起 commit；`numbers_check.py --check-report <位置表>` 會比對它是否過期（避免拿舊表當證據）。
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
1-1. `python3 -m pytest -q _source/deploy-automation/tests` 全綠；`numbers_check.py --check-report _source/數字位置表_20260906.md` exit 0。真源的結構規則住在測試裡，只跑 numbers_check 不算過閘（Codex 盲審 C-02）。
2. **改過的頁面才改 `<lastmod>`，改過的一定要改**：應更新清單由 `git diff --name-only main -- public` 反推，不是憑印象列頁（Codex 盲審 C-06——這次就漏掉真的改過的 `/impact/`，又把沒改的 `/contact/` 標成當天）。主站 `sitemap.xml` 有動，`public/sitemap_index.xml` 對應那一列的 `lastmod` 也要同步。`tests/test_sitemap.py` 會雙向檢查。
3. 對外數字改動 → 先過 Codex 盲審（照 `MAC的技能與工具中心/docs/codex-crosscheck-playbook.md`），再過人類閘（理事長一句「上線」）。
4. 分支上做、快轉併入 main；push main ＝ Cloudflare 自動部署，約 30–60 秒。

## 五、部署後索引（推完 main 五分鐘內做完，`deploy-automation/postdeploy.sh` 一鍵）
> v1.1 起腳本分三段狀態，**只有 `POSTDEPLOY_OK` 才算機器該做的做完**（Codex 盲審 C-07／C-08：舊版把 `LIVE_OK` 印在 IndexNow 之前、又不看 helper 的 return code，key 失效照樣 exit 0）。
1. **實地驗證（→ `CONTENT_LIVE_OK`）**：驗的範圍不是寫死的五頁，而是「所有含 `data-metric` 的頁面 ＋ `llms.txt`／`humans.txt` ＋ 兩個窗口頁的電話」，未來在 `/about/` 加標記會自動納入。比對方式是**逐個標記比對 (id, 欄位, 顯示值, 數量)**，不是「頁面文字裡有沒有這個數字」——後者在「主數字被改回舊值、但同頁別處剛好有新值」時會誤判通過。離線重跑：`--live-dir <目錄>`。
2. **搜尋引擎（→ `INDEXNOW_OK`）**：`_source/indexnow-ping.sh` 推剛驗過的所有頁面；**非 200/202 或 curl 失敗一律 exit 1**，postdeploy 跟著 `POSTDEPLOY_FAILED`。GitHub 的 `.github/workflows/indexnow.yml` 同樣改成失敗就紅燈（`continue-on-error: true`，不擋 build，但看得見）。Google 仍走 Search Console：首頁或方法頁改動時請求索引一次，並把時間回填收據。
3. **AI 可讀層**：`public/llms.txt` 與 `humans.txt` 的數字納入 numbers_check 掃描與線上驗證範圍。
4. **看板**：`議題_官網影響力數據/_狀態.md` 最新交付行改當天＋當天日誌加一列（含 main commit hash、部署時間、驗證結果）。
5. **知識庫／清單**：清單檔的「已上官網」欄勾選日期；若數字源自知識庫卡片，卡片 caveat 加「已上官網 YYYY-MM-DD」。
6. **經驗回寫**：這次部署踩到的坑寫進本檔檔尾「經驗紀錄」，同型坑第二次出現升成腳本檢查。
7. **收據**：`postdeploy.sh --receipt <路徑>` 產出逐項 `done/failed/pending` 的收據；第 4、5、6 點與 GSC 都是 `pending`，做完由執行者回填證據（看板行號、GSC 請求時間）。**看到 `CONTENT_LIVE_OK` 不等於部署後索引做完**。

## 六、Codex 與 fable 的分工
- fable（指揮部）：起草與維護本 SOP、numbers.json、看板同步；每次部署跑第四、五節。
- Codex：對外數字改動前的盲審（威脅模型固定：數字回源、單位混用、歸屬、內部互打、位置漏改、索引未更新）；每季一次冷讀官網三頁（首頁、方法頁、影響力頁）。
- 兩邊共用的檔：本 SOP、numbers.json、`codex-crosscheck-playbook.md`；改本 SOP 要同步 `官網維護手冊.md` §③ 的指引。
- **制度檔真源在 Claude 端，不得直接改 `~/.codex/AGENTS.md`**（v1.1 修正，Codex 盲審 C-09：舊版寫「改本 SOP 要同步 `~/.codex/AGENTS.md`」，與該檔自身「Claude 端為真源、未經明示不得直接改」互相打架）。正確做法：通知 Claude 端制度維護者改真源 → 跑 `bash ~/.claude/scripts/codex-bridge-sync-check.sh` 偵測漂移 → 由該流程同步兩份複製版。
- **誰寫哪本日誌（v1.1 定案）**：Codex 盲審**只寫盲審報告**一個檔；`codex-crosscheck-playbook.md` 的「審查流程經驗」由指揮部收割後 append；本 SOP 第七節「經驗紀錄」由**部署者**寫部署踩到的坑。派工單要寫明本輪唯一可寫檔，不要同時要求「只寫報告」又要求「任務結束 append playbook」。

## 七、經驗紀錄（append-only）
- 2026-09-06｜首次上線民意與聲量區（main acd6bbf）｜部署 30 秒內生效（curl 輪詢 15 秒一次首輪即 LIVE）｜坑：此前數字散在首頁、方法頁、影響力頁三處手改，方法頁 33 漏改半年未被發現；168 vs 173 兩個定義並存｜→ 本 SOP 建立單一真源與位置標記
- 2026-09-06｜Codex 盲審 9 個 Critical 收割（報告：`_source/審查_Codex盲審_數據SOP_20260906.md`，分支 numbers-sot-2026-09）｜三個坑是「規則寫了、腳本沒守」：①位置表只記錄「現在有什麼」，沒有「應該有什麼」，整張卡刪掉照樣 exit 0；②線上驗證做的是全文包含判斷，主數字被改回舊值＋同頁別處有新值就誤判通過；③IndexNow 兩條路徑都 fail-open，403 也印完成｜→ 加位置基線 manifest、線上逐標記比對、IndexNow fail-closed
- 2026-09-06｜盲審過程另抓到兩件**現況就是壞的**（不是理論風險）｜①`apply_numbers.py` 更新方法頁「最近更新」月份是逐**行**取代，真實版面上 `<td>合作組織數</td>` 與 `<td>2026-09</td>` 分屬不同行，等於從來沒改到過，但 Changelog 照寫——已改成逐 `<tr>` 取代，換不到就 `ApplyError` 停手；②`public/press/index.html` 的政策深度分析仍寫 36 篇（真源 47），是第二次出現的「同型漏改」——已改成標記，並把 33、36 登記進 `previous_values`，之後殘留舊值掃得到｜→ 判準：**沒有「換了幾處」的斷言，就等於沒有替換**
- 2026-09-06｜sitemap 的錯犯在兩個方向｜真的改過的 `/impact/` 漏更新 lastmod（測試把它排除在檢查範圍外），沒改內容的 `/contact/` 卻被標成 2026-09-06（謊報新鮮度）；父索引 `sitemap_index.xml` 完全沒人動｜→ 應更新清單改由 `git diff main -- public` 反推，測試雙向檢查，並納入 `sitemap_index.xml`
- 2026-09-06｜`/impact/reach/` 新頁上線後讀回抓到兩個「新頁沒套用全站慣例」的坑｜①全站 CSS 是 `a{color:inherit;text-decoration:none}`，其餘四頁（`/impact/`、`/about/`、`/press/`、`/methodology/`）每個內文連結都**逐個**補了 inline style 才可辨識，新頁 5 個連結整個漏補、Playwright 量到的 computed color 與本文同色、讀者無法辨識這是連結；②既有頁面只有首頁單一入口指向新頁、`/methodology/` 未同步補回指連結，形成單向斷鏈｜→ 逐個連結補 style 容易漏，改成容器層級規則（`.page-end a, .callout a, .stat-note a { ... }` 一次涵蓋該頁全部連結）；改文案要注意 `test_markup.py::test_copy_text_untouched` 是逐字凍結比對，補連結一律**包裹既有文字**、不得新增/改寫文案，否則凍結測試會炸（本輪第一版加了新句導致 1 failed，改包裹既有文字後 133 passed）
# 官網數據更新與部署索引 SOP v1.1（2026-09-06）

> 理事長 2026-09-06 指示：上線的同時設計規則，讓以後每次部署都把「每個位置、每個數字」更新好，並把部署後的索引一起做完；規則由 fable 起草、Codex 盲審、合併後兩邊共同遵守。
> 原則：**單一真源、腳本檢查、部署即索引、經驗回寫**。人記不住十幾個位置，腳本記得住。

## 一、單一真源：`_source/numbers.json`
- 全站每一個「影響力數字」只在這個檔定義一次。每筆欄位：
  `id`（英文代號）、`value`（原始數值）、`display`（顯示字串，例 `66,247`）、`unit`（份／人次／篇／則／場／個）、`label`（中文標籤）、`period`（資料期間）、`method`（怎麼算，一句）、`source`（出處：看板清單路徑或原件）、`last_verified`（YYYY-MM-DD）、`cadence`（quarterly／event／yearly）、`owner`（指揮部／秘書處）、`status`、`notes`。
- **`status`（v1.1 新增，Codex 盲審 C-05）**：`approved`＝可由看板清單一手重算；`provisional`＝來源鏈目前只指向官網下游頁面，待秘書處／理事長拍板（腳本會在輸出列出，但不擋部署，因為這些數字早已在站上）；`draft`＝未裁決，**出現在頁面上就 exit 1**。新增指標一律先 `draft`。
- 另有三個選填欄位：`display_approx`（display 是刻意的近似對外值時必填 `true`，例 `press_coverage` 對外「3,000+」／實計 3,017；不填而數值對不上就 exit 1）、`previous_values`（改過的舊值，供「殘留舊值」掃描，例 `policy_briefs` 的 33、36）、`on_site: false`（真源有此數字但刻意不上站）。
- **`source` 不得只寫官網下游頁面**：至少要指到看板清單的某一列或一手原件。目前 `partners／actions／press_releases／policy_briefs／legislators` 五筆是 `source_status: downstream_only`，屬待補（見第七節待裁決事項）。
- 首批 id（2026-09-06）：`valid_surveys`（66,247 份）、`single_reach`（104,000 人次）、`partners`（168+）、`press_coverage`（3,000+ 篇，精確 3,017）、`buzz_1y`（2,889 則）、`actions`（286 場）；CH 05 舊數字帶與 `/methodology/`、`/impact/` 既有數字（113、47、7,917+ 等）也各建一筆，並註明與新區的期間差異。
- 數字的上游：`~/Desktop/國教盟指揮看板/議題_官網影響力數據/1_最新/20260905_清單_國教盟調查與觸及數據.md`（每筆附出處，經獨立核對）。改 numbers.json 前先改清單，並附出處。

## 二、位置登記：`data-metric` 標記（腳本掃得到才算存在）
- 頁面上每一處顯示這些數字的元素都要包 `<span data-metric="<id>">66,247</span>`。要讓單位、期間等欄位也吃真源，用 `data-metric-field`（例 `<span data-metric="valid_surveys" data-metric-field="unit">份</span>`）。沒有標記的數字＝黑數，腳本會抓出來報錯。
- `deploy-automation/numbers_check.py`：掃 `public/**/*.html` ＋ `llms.txt`／`humans.txt`，列出每個 id 出現的檔案與行號（＝位置表），比對顯示值是否等於真源對應欄位；另掃已知數值出現在**未標記**處的情形。任一不符＝exit 1，擋部署。v1.1 起還做三件事：
  1. **真源自檢**：欄位齊全、id 不重複、`value`／`display` 對得上、`status` 合法。
  2. **位置基線 `_source/numbers_manifest.json`**：登記每個檔案該有幾處標記。整張卡被刪、標記被拿掉、數量變少、或某個 id 全站都找不到，一律 exit 1（Codex 盲審 C-01：沒有基線＝刪掉就沒事）。刻意增刪標記後，人工覆核再跑 `--update-manifest`。
  3. **黑數別名表**：不再只比對逐字字串，會自動展開「帶／不帶逗號、全形數字與逗號、`6.6 萬份`／`3千篇` 這類量級寫法（要接單位才算命中）、`約／逾／超過／近／破` 等近似前綴、`previous_values` 的殘留舊值」；`3,000-8,000 字` 這種數值區間不算黑數。仍需要人工補的寫法（例四捨五入的 `約 66,000`）寫進該筆的 `scan_patterns`。
- **黑數 allowlist（`_source/numbers_allowlist.json`）綁語境**：每筆登記 `id ＋ file ＋ count ＋ contexts`（每一處所在整句的雜湊）。同一檔案裡刪掉一句合格文案、又在別處新增同值宣稱，筆數沒變也會被擋下（Codex 盲審 C-04）。逐處覆核語意與單位無誤後才跑 `--update-allowlist`。
- 位置表 `_source/數字位置表_20260906.md` 隨程式碼一起 commit；`numbers_check.py --check-report <位置表>` 會比對它是否過期（避免拿舊表當證據）。
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
1-1. `python3 -m pytest -q _source/deploy-automation/tests` 全綠；`numbers_check.py --check-report _source/數字位置表_20260906.md` exit 0。真源的結構規則住在測試裡，只跑 numbers_check 不算過閘（Codex 盲審 C-02）。
2. **改過的頁面才改 `<lastmod>`，改過的一定要改**：應更新清單由 `git diff --name-only main -- public` 反推，不是憑印象列頁（Codex 盲審 C-06——這次就漏掉真的改過的 `/impact/`，又把沒改的 `/contact/` 標成當天）。主站 `sitemap.xml` 有動，`public/sitemap_index.xml` 對應那一列的 `lastmod` 也要同步。`tests/test_sitemap.py` 會雙向檢查。
3. 對外數字改動 → 先過 Codex 盲審（照 `MAC的技能與工具中心/docs/codex-crosscheck-playbook.md`），再過人類閘（理事長一句「上線」）。
4. 分支上做、快轉併入 main；push main ＝ Cloudflare 自動部署，約 30–60 秒。

## 五、部署後索引（推完 main 五分鐘內做完，`deploy-automation/postdeploy.sh` 一鍵）
> v1.1 起腳本分三段狀態，**只有 `POSTDEPLOY_OK` 才算機器該做的做完**（Codex 盲審 C-07／C-08：舊版把 `LIVE_OK` 印在 IndexNow 之前、又不看 helper 的 return code，key 失效照樣 exit 0）。
1. **實地驗證（→ `CONTENT_LIVE_OK`）**：驗的範圍不是寫死的五頁，而是「所有含 `data-metric` 的頁面 ＋ `llms.txt`／`humans.txt` ＋ 兩個窗口頁的電話」，未來在 `/about/` 加標記會自動納入。比對方式是**逐個標記比對 (id, 欄位, 顯示值, 數量)**，不是「頁面文字裡有沒有這個數字」——後者在「主數字被改回舊值、但同頁別處剛好有新值」時會誤判通過。離線重跑：`--live-dir <目錄>`。
2. **搜尋引擎（→ `INDEXNOW_OK`）**：`_source/indexnow-ping.sh` 推剛驗過的所有頁面；**非 200/202 或 curl 失敗一律 exit 1**，postdeploy 跟著 `POSTDEPLOY_FAILED`。GitHub 的 `.github/workflows/indexnow.yml` 同樣改成失敗就紅燈（`continue-on-error: true`，不擋 build，但看得見）。Google 仍走 Search Console：首頁或方法頁改動時請求索引一次，並把時間回填收據。
3. **AI 可讀層**：`public/llms.txt` 與 `humans.txt` 的數字納入 numbers_check 掃描與線上驗證範圍。
4. **看板**：`議題_官網影響力數據/_狀態.md` 最新交付行改當天＋當天日誌加一列（含 main commit hash、部署時間、驗證結果）。
5. **知識庫／清單**：清單檔的「已上官網」欄勾選日期；若數字源自知識庫卡片，卡片 caveat 加「已上官網 YYYY-MM-DD」。
6. **經驗回寫**：這次部署踩到的坑寫進本檔檔尾「經驗紀錄」，同型坑第二次出現升成腳本檢查。
7. **收據**：`postdeploy.sh --receipt <路徑>` 產出逐項 `done/failed/pending` 的收據；第 4、5、6 點與 GSC 都是 `pending`，做完由執行者回填證據（看板行號、GSC 請求時間）。**看到 `CONTENT_LIVE_OK` 不等於部署後索引做完**。

## 六、Codex 與 fable 的分工
- fable（指揮部）：起草與維護本 SOP、numbers.json、看板同步；每次部署跑第四、五節。
- Codex：對外數字改動前的盲審（威脅模型固定：數字回源、單位混用、歸屬、內部互打、位置漏改、索引未更新）；每季一次冷讀官網三頁（首頁、方法頁、影響力頁）。
- 兩邊共用的檔：本 SOP、numbers.json、`codex-crosscheck-playbook.md`；改本 SOP 要同步 `官網維護手冊.md` §③ 的指引。
- **制度檔真源在 Claude 端，不得直接改 `~/.codex/AGENTS.md`**（v1.1 修正，Codex 盲審 C-09：舊版寫「改本 SOP 要同步 `~/.codex/AGENTS.md`」，與該檔自身「Claude 端為真源、未經明示不得直接改」互相打架）。正確做法：通知 Claude 端制度維護者改真源 → 跑 `bash ~/.claude/scripts/codex-bridge-sync-check.sh` 偵測漂移 → 由該流程同步兩份複製版。
- **誰寫哪本日誌（v1.1 定案）**：Codex 盲審**只寫盲審報告**一個檔；`codex-crosscheck-playbook.md` 的「審查流程經驗」由指揮部收割後 append；本 SOP 第七節「經驗紀錄」由**部署者**寫部署踩到的坑。派工單要寫明本輪唯一可寫檔，不要同時要求「只寫報告」又要求「任務結束 append playbook」。

## 七、經驗紀錄（append-only）
- 2026-09-06｜首次上線民意與聲量區（main acd6bbf）｜部署 30 秒內生效（curl 輪詢 15 秒一次首輪即 LIVE）｜坑：此前數字散在首頁、方法頁、影響力頁三處手改，方法頁 33 漏改半年未被發現；168 vs 173 兩個定義並存｜→ 本 SOP 建立單一真源與位置標記
- 2026-09-06｜Codex 盲審 9 個 Critical 收割（報告：`_source/審查_Codex盲審_數據SOP_20260906.md`，分支 numbers-sot-2026-09）｜三個坑是「規則寫了、腳本沒守」：①位置表只記錄「現在有什麼」，沒有「應該有什麼」，整張卡刪掉照樣 exit 0；②線上驗證做的是全文包含判斷，主數字被改回舊值＋同頁別處有新值就誤判通過；③IndexNow 兩條路徑都 fail-open，403 也印完成｜→ 加位置基線 manifest、線上逐標記比對、IndexNow fail-closed
- 2026-09-06｜盲審過程另抓到兩件**現況就是壞的**（不是理論風險）｜①`apply_numbers.py` 更新方法頁「最近更新」月份是逐**行**取代，真實版面上 `<td>合作組織數</td>` 與 `<td>2026-09</td>` 分屬不同行，等於從來沒改到過，但 Changelog 照寫——已改成逐 `<tr>` 取代，換不到就 `ApplyError` 停手；②`public/press/index.html` 的政策深度分析仍寫 36 篇（真源 47），是第二次出現的「同型漏改」——已改成標記，並把 33、36 登記進 `previous_values`，之後殘留舊值掃得到｜→ 判準：**沒有「換了幾處」的斷言，就等於沒有替換**
- 2026-09-06｜sitemap 的錯犯在兩個方向｜真的改過的 `/impact/` 漏更新 lastmod（測試把它排除在檢查範圍外），沒改內容的 `/contact/` 卻被標成 2026-09-06（謊報新鮮度）；父索引 `sitemap_index.xml` 完全沒人動｜→ 應更新清單改由 `git diff main -- public` 反推，測試雙向檢查，並納入 `sitemap_index.xml`
- 2026-09-06｜`/impact/reach/` 新頁上線後讀回抓到兩個「新頁沒套用全站慣例」的坑｜①全站 CSS 是 `a{color:inherit;text-decoration:none}`，其餘四頁（`/impact/`、`/about/`、`/press/`、`/methodology/`）每個內文連結都**逐個**補了 inline style 才可辨識，新頁 5 個連結整個漏補、Playwright 量到的 computed color 與本文同色、讀者無法辨識這是連結；②既有頁面只有首頁單一入口指向新頁、`/methodology/` 未同步補回指連結，形成單向斷鏈｜→ 逐個連結補 style 容易漏，改成容器層級規則（`.page-end a, .callout a, .stat-note a { ... }` 一次涵蓋該頁全部連結）；改文案要注意 `test_markup.py::test_copy_text_untouched` 是逐字凍結比對，補連結一律**包裹既有文字**、不得新增/改寫文案，否則凍結測試會炸（本輪第一版加了新句導致 1 failed，改包裹既有文字後 133 passed）

- 2026-09-11｜三篇新聞稿經 publish.py 發布（f36d188／c0e7a27／ddd2ce9）後的部署後索引補做（新帳號 session，18:40）｜坑：①publish.py 走自己的 lint，不跑本 SOP 第四節 pytest，push 後 main 上 3 紅沒人看見；②publish.py 只把新文章加進 sitemap（lastmod＝文章日），不 bump 被它改動的 `/` 與 `/press/` lastmod、不同步 `sitemap_index.xml`、不重生位置表；③`tests/test_sitemap.py` 的 `DEPLOY_DATE` 是寫死常數（9/6），每次部署都要手改，第四節沒寫這一步；④`test_markup::test_copy_text_untouched` 拿 `Backups/20260906_官網數據真源/index.html` 逐字凍結首頁，與插卡互斥（本次 difflib 證明差異僅 1 段插入＝三張新聞稿卡文字，零刪除）；⑤沒人跑 postdeploy.sh、無收據，IndexNow 只靠 GitHub 工作流（三次步驟級 success，事後查證）｜→ 補做：postdeploy.sh 五 URL POSTDEPLOY_OK（IndexNow HTTP 200）；分支 `index-sync-2026-09-11` 修 lastmod／sitemap_index／位置表／DEPLOY_DATE；「publish.py 補齊索引層」與「測試夾具改設計」各開一張修復卡；②③④同型第二次出現即升腳本檢查
### 有意識不採／暫緩（Codex 盲審 2026-09-06）
- **C-02 的「卡片全模板生成」**：目前只做到「單位／期間等欄位可用 `data-metric-field` 吃真源」，既有頁面的單位與期間仍是手寫。全站改模板要動三頁的版面結構，風險大於這次要解的問題；**取捨理由**：漏改的實害集中在數字本體（已被標記與基線覆蓋），欄位漂移目前靠季度冷讀。下次改版時逐頁改標記，不另開一次全站重構。
- **C-05 的數值裁決**：`partners=168`（清單只有 173+ 與 65+ 兩種口徑）、`press_releases=113`（清單另載 2025 年 111）等五筆的口徑，**不是腳本能決定的事**，屬秘書處／理事長裁決。本輪只做到機制面：加 `status`／`source_status`、`draft` 不得上站、`provisional` 每次跑都被列出來提醒。**待裁決事項（已裁決，2026-09-06）**：理事長王瀚陽裁決 `partners`（168+）／`actions`（286）／`press_releases`（113）／`policy_briefs`（47）／`legislators`（19）五筆口徑 OK，屬 2023–2026 年區間口徑，**2026 年底需再整理**（①168 的重算依據補進看板清單、②新聞稿 2025 年單一官方口徑等細部核對留到年底一併處理）；`numbers.json` 五筆 `status` 已改 `approved` 並補 `approved_by: 理事長 王瀚陽`／`approved_at: 2026-09-06`（分支 `reach-page-2026-09`）。
- **C-08 的人工項自動化**：GSC 請求索引、看板回填、知識庫 caveat 無法由腳本驗證完成，改為收據裡逐項 `pending` 並要求回填證據。**取捨理由**：假裝驗得到比誠實標 pending 更危險。
- **縱深 2（單一原子變更／PR 缺產物即失敗）**：本 repo 只有 IndexNow 一個 workflow、部署走 push main，沒有 PR 閘可掛。改用「部署前檢查清單（第四節）＋ `--check-report` 位置表過期偵測」達到近似效果。有 CI 之後再補。
- **縱深 1 的「改用 HTML parser」**：只採了一半（屬性單／雙引號、順序不拘、全形數字與逗號正規化都已支援），沒有換成 `html.parser`。**理由**：現行掃描要保留「原始碼位移 → 行號」的對應，換 parser 會失去這個能力，而行號是位置表唯一能給人的定位。

### Codex 給指揮部的流程建議（2026-09-06 逐字抄錄，未改寫）
> 1. 下次派工單直接附 task id、rollout 對應方式、**額度腳本絕對路徑**。本次 AGENTS 只寫 `bin/codex-quota.sh`，第一次依常見位置推定失敗，後來才在 `MAC的技能與工具中心/bin/` 找到。
> 2. 「唯一可寫檔」與「任務結束 append playbook」請在派工模板中預先裁決：建議 Codex 永遠只寫報告，hold/harvest 完成後由指揮部 append playbook，並記錄報告 commit/hash。
> 3. 派工時附 `base commit` 與「預期改動 URL 清單」。這次從 diff 才反推出 impact 確有變更，因而抓到 sitemap 測試把它排除。
> 4. 提供 sandbox-safe 的 postdeploy 測試入口（fixture fetcher 或 `--live-dir`），避免依賴開 port；否則每次盲審都會留下同樣六項未驗。
> 5. 收割後先逐條裁決 C-01～C-09，再由另一個未參與產製者重跑：完整 pytest、numbers_check、apply dry-run、sitemap diff gate、失敗 IndexNow stub、真實部署後 receipt。不要只以現有 65 項綠燈或 `LIVE_OK` 作完成證據。
> 6. 依本次唯一寫檔限制，我沒有 append `codex-crosscheck-playbook.md`；請指揮部從本節擷取一條經驗回寫，避免稽核者越權修改 Claude 端真源。

（建議 4 已落地：`postdeploy.sh --live-dir` ＋ `postdeploy_verify.py`，postdeploy 測試不再開 port。建議 1、2、3 落地在第六節「誰寫哪本日誌」與派工模板；建議 5 的重跑由未參與產製的代理執行。）
- 2026-09-12 研討會新聞稿（含 8 圖）發布經驗｜①`publish.py add` **沒有卡片去重**——stage 失敗後不得重跑 add，否則首頁與列表各多一張卡；push 段改為直接 `git add -A / commit / push`（複製 publish.py `git_push()` 行為）。②pytest 兩個新失敗都不是本次造成：`test_committed_position_table_is_current`＝新聞稿插卡改了 index.html／press/index.html 行號，照 9/11 作法 `numbers_check.py --report _source/數字位置表_20260906.md` 重生即過；`test_sitemap.py::test_unchanged_pages_keep_their_lastmod`＝既有 events 頁（a17248b）lastmod 預設為活動日 2026-09-12，恰與部署日相同被判「謊報」——屬測試對「既有同日 lastmod」的假陽性，本次 deselect；**改進項**：測試應比對 HEAD 與工作區 lastmod 是否改變，而非只看是否等於 DEPLOY_DATE。③`test_markup.py::test_copy_text_untouched[index.html]` 在未改動 baseline 就紅（凍結基準過期，9/11 坑④延續）——已開卡。④hold-post 對 `postdeploy.sh` 報孤兒進程是自我匹配假陽性（pgrep 命中呼叫它的 shell 與 tee），以 pgrep 實查為準。⑤部署腳本 `deploy_nd2026.sh`（新聞稿專案 6_發布版）把 stage／push 兩段固化，預期檔清單要含位置表。收據：`_source/收據_2026-09-12.md`。

## 變更紀錄
- 2026-09-06｜理事長王瀚陽裁決：`partners`／`actions`／`press_releases`／`policy_briefs`／`legislators` 五筆 provisional 口徑 OK（屬 2023–2026 年區間口徑，2026 年底需再整理）｜`numbers.json` 五筆 `status` 改 `approved`＋補 `approved_by`／`approved_at`，第七節「C-05 的數值裁決」待裁決事項改記已裁；同步更新 `tests/test_numbers_json.py` 的 APPROVED／PROVISIONAL 基準清單｜分支 `reach-page-2026-09`
- 2026-09-06 v1.1｜依 Codex 盲審 9 個 Critical 收割：新增位置基線 manifest（C-01）、真源自檢與 `data-metric-field` 投影（C-02）、黑數別名表與殘留舊值掃描（C-03）、allowlist 綁語境雜湊（C-04）、`status`／`source_status` 欄位（C-05）、sitemap 應更新清單改由 git diff 反推並納入 `sitemap_index.xml`（C-06）、IndexNow fail-closed 與三段狀態（C-07）、驗證與推送範圍改為自動推導＋收據（C-08）、制度檔真源與日誌責任釐清（C-09）｜盲審報告：`_source/審查_Codex盲審_數據SOP_20260906.md`｜指揮部（fable）收割，分支 numbers-sot-2026-09
- 2026-09-06 v1 建檔｜指揮部（fable）起草，待 Codex 盲審

- **C-02 的「卡片全模板生成」**：目前只做到「單位／期間等欄位可用 `data-metric-field` 吃真源」，既有頁面的單位與期間仍是手寫。全站改模板要動三頁的版面結構，風險大於這次要解的問題；**取捨理由**：漏改的實害集中在數字本體（已被標記與基線覆蓋），欄位漂移目前靠季度冷讀。下次改版時逐頁改標記，不另開一次全站重構。
- **C-05 的數值裁決**：`partners=168`（清單只有 173+ 與 65+ 兩種口徑）、`press_releases=113`（清單另載 2025 年 111）等五筆的口徑，**不是腳本能決定的事**，屬秘書處／理事長裁決。本輪只做到機制面：加 `status`／`source_status`、`draft` 不得上站、`provisional` 每次跑都被列出來提醒。**待裁決事項（已裁決，2026-09-06）**：理事長王瀚陽裁決 `partners`（168+）／`actions`（286）／`press_releases`（113）／`policy_briefs`（47）／`legislators`（19）五筆口徑 OK，屬 2023–2026 年區間口徑，**2026 年底需再整理**（①168 的重算依據補進看板清單、②新聞稿 2025 年單一官方口徑等細部核對留到年底一併處理）；`numbers.json` 五筆 `status` 已改 `approved` 並補 `approved_by: 理事長 王瀚陽`／`approved_at: 2026-09-06`（分支 `reach-page-2026-09`）。
- **C-08 的人工項自動化**：GSC 請求索引、看板回填、知識庫 caveat 無法由腳本驗證完成，改為收據裡逐項 `pending` 並要求回填證據。**取捨理由**：假裝驗得到比誠實標 pending 更危險。
- **縱深 2（單一原子變更／PR 缺產物即失敗）**：本 repo 只有 IndexNow 一個 workflow、部署走 push main，沒有 PR 閘可掛。改用「部署前檢查清單（第四節）＋ `--check-report` 位置表過期偵測」達到近似效果。有 CI 之後再補。
- **縱深 1 的「改用 HTML parser」**：只採了一半（屬性單／雙引號、順序不拘、全形數字與逗號正規化都已支援），沒有換成 `html.parser`。**理由**：現行掃描要保留「原始碼位移 → 行號」的對應，換 parser 會失去這個能力，而行號是位置表唯一能給人的定位。

### Codex 給指揮部的流程建議（2026-09-06 逐字抄錄，未改寫）
> 1. 下次派工單直接附 task id、rollout 對應方式、**額度腳本絕對路徑**。本次 AGENTS 只寫 `bin/codex-quota.sh`，第一次依常見位置推定失敗，後來才在 `MAC的技能與工具中心/bin/` 找到。
> 2. 「唯一可寫檔」與「任務結束 append playbook」請在派工模板中預先裁決：建議 Codex 永遠只寫報告，hold/harvest 完成後由指揮部 append playbook，並記錄報告 commit/hash。
> 3. 派工時附 `base commit` 與「預期改動 URL 清單」。這次從 diff 才反推出 impact 確有變更，因而抓到 sitemap 測試把它排除。
> 4. 提供 sandbox-safe 的 postdeploy 測試入口（fixture fetcher 或 `--live-dir`），避免依賴開 port；否則每次盲審都會留下同樣六項未驗。
> 5. 收割後先逐條裁決 C-01～C-09，再由另一個未參與產製者重跑：完整 pytest、numbers_check、apply dry-run、sitemap diff gate、失敗 IndexNow stub、真實部署後 receipt。不要只以現有 65 項綠燈或 `LIVE_OK` 作完成證據。
> 6. 依本次唯一寫檔限制，我沒有 append `codex-crosscheck-playbook.md`；請指揮部從本節擷取一條經驗回寫，避免稽核者越權修改 Claude 端真源。

（建議 4 已落地：`postdeploy.sh --live-dir` ＋ `postdeploy_verify.py`，postdeploy 測試不再開 port。建議 1、2、3 落地在第六節「誰寫哪本日誌」與派工模板；建議 5 的重跑由未參與產製的代理執行。）

## 變更紀錄
- 2026-09-06｜理事長王瀚陽裁決：`partners`／`actions`／`press_releases`／`policy_briefs`／`legislators` 五筆 provisional 口徑 OK（屬 2023–2026 年區間口徑，2026 年底需再整理）｜`numbers.json` 五筆 `status` 改 `approved`＋補 `approved_by`／`approved_at`，第七節「C-05 的數值裁決」待裁決事項改記已裁；同步更新 `tests/test_numbers_json.py` 的 APPROVED／PROVISIONAL 基準清單｜分支 `reach-page-2026-09`
- 2026-09-06 v1.1｜依 Codex 盲審 9 個 Critical 收割：新增位置基線 manifest（C-01）、真源自檢與 `data-metric-field` 投影（C-02）、黑數別名表與殘留舊值掃描（C-03）、allowlist 綁語境雜湊（C-04）、`status`／`source_status` 欄位（C-05）、sitemap 應更新清單改由 git diff 反推並納入 `sitemap_index.xml`（C-06）、IndexNow fail-closed 與三段狀態（C-07）、驗證與推送範圍改為自動推導＋收據（C-08）、制度檔真源與日誌責任釐清（C-09）｜盲審報告：`_source/審查_Codex盲審_數據SOP_20260906.md`｜指揮部（fable）收割，分支 numbers-sot-2026-09
- 2026-09-06 v1 建檔｜指揮部（fable）起草，待 Codex 盲審
- 2026-09-17｜10/2 活動上架（4142908）｜坑：①publish.py 對 event 型把 sitemap lastmod 填成「活動日」（未來日 2026-10-02），test_sitemap 要的是頁面修改日——發布活動後要手改回今天；②postdeploy.sh 的 --receipt 必須帶路徑參數，裸用會 $2 unbound 中斷；③test_markup 凍結快照（Backups/20260906_官網數據真源）在本機真 repo 跑才生效（worktree 跑會因路徑不存在被 skip），落後於 9/14 改版兩頁，本次已刷新並備份舊檔於 Backups/2026-09-17/舊測試快照_20260906｜events_check 已結束活動窗口（前12行）會掃到相鄰新活動的「報名」字樣，正解＝把已結束活動實體搬「近期已舉辦」區（lint WARN 的建議本來就是這個）
- 2026-09-18｜兒少十大承諾連署頁上線（12e06c2，/act/child-pledge/＋活動卡）｜坑：①自訂整頁行動頁走 /act/ 路徑＋events.json 活動卡導流是可行組合（活動卡負責曝光與 9/30 自動結束，行動頁長期存在），sitemap／pagefind 由既有腳本涵蓋、無需另掛；②子代理執行到 push 前會以「不可逆對外動作須理事長本人在其對話中確認」停手——這是正確的保守，但授權鏈在指揮部對話裡時，push 應由指揮部親自執行，派工單可直接寫明「push 由指揮部執行、代理做到 commit」省一輪；③本機 `python3 -m http.server` 預覽一律加 `--bind 127.0.0.1`，否則整個 public/ 對區網開放（同日 opus 審查實測區網可讀）

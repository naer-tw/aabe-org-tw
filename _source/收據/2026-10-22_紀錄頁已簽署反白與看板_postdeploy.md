# 部署後索引收據 2026-10-22

- commit：81f28d8
- 基底：https://aabe.org.tw
- content_live：done
- indexnow：done
- sitemap_lastmod：pending（改動頁與 sitemap_index.xml 由 numbers_check／pytest 擋，部署後請確認線上 sitemap 已更新）
- gsc_request_index：pending（首頁或方法頁有改動時，到 Search Console 請求索引一次，回填請求時間）
- board_status：pending（~/Desktop/國教盟指揮看板/議題_官網影響力數據/_狀態.md 最新交付行改 2026-10-22）
- board_log：done（看板 2026-10-22 日誌第 111 行）
- list_checkbox：pending（清單檔「已上官網」欄勾 2026-10-22）
- kb_caveat：pending（數字若源自知識庫卡片，卡片 caveat 加「已上官網 2026-10-22」）
- sop_experience：pending（本次踩到的坑寫進 SOP 第七節「經驗紀錄」）

## 本次內容（兒少承諾線補記）
- 推送授權：理事長 2026-10-22 21:5x（本線對話原話）「照示意做：已簽署反白＋統計下方靜態看板，名字卡那句一併改，做好就推。」
- 內容：紀錄頁首頁八張已簽署名字卡淡綠底＋左側青綠粗邊；全國統計下方新增「已簽署的參選人」看板（八位，依縣市順序，連到各縣市頁）；名字卡說明句改為「每張名字卡一樣大；已簽署者以淡綠底標示，其餘差別只在圖示與文字。…」；八個縣市頁的已簽署卡同樣反白。
- 推送：官網 main 6aab72e → 81f28d8（推前 fetch 確認遠端未前進、待推只此一筆、50 檔全在 record／pagefind／數字位置表範圍；按完整 SHA 推、ls-remote 核對）。
- 線上：十檔（九頁＋record.css）逐位元與 commit 相符（推後約 30 秒）；首頁與高雄頁 200。
- 閘：真源全套 pytest 抓到兩處（320 寬長姓名橫向捲動、看板小字低於 14px），修後相關檔重跑 336＋651 綠；deploy_site DEPLOY_SITE_OK（官網 pytest 191 綠／125 skip）；fresh read-back 八項全符。
- 真源：mayoral-pledges-watch a90dc6a。

# 部署後索引收據 2026-10-22

- commit：1d0f1f6
- 基底：https://aabe.org.tw
- content_live：done
- indexnow：done
- sitemap_lastmod：pending（改動頁與 sitemap_index.xml 由 numbers_check／pytest 擋，部署後請確認線上 sitemap 已更新）
- gsc_request_index：pending（首頁或方法頁有改動時，到 Search Console 請求索引一次，回填請求時間）
- board_status：pending（~/Desktop/國教盟指揮看板/議題_官網影響力數據/_狀態.md 最新交付行改 2026-10-22）
- board_log：done（議題_縣市長政見 2026-10-22 日誌第 104 行起）
- list_checkbox：pending（清單檔「已上官網」欄勾 2026-10-22）
- kb_caveat：pending（數字若源自知識庫卡片，卡片 caveat 加「已上官網 2026-10-22」）
- sop_experience：pending（本次踩到的坑寫進 SOP 第七節「經驗紀錄」）

## 本次內容（兒少承諾線補記）
- 推送授權：理事長 2026-10-22 20:5x（本線對話原話）「先不管項數，紀錄頁八位直接顯示「已簽署」，項數之後再補，做好就推。」
- 內容：record/ 首頁統計 73 已寄送／8 已簽署；新北、新竹市、臺中、雲林、嘉義市、臺南、高雄、金門八頁各一位「已簽署」（李四川、高虹安、江啟臣、張嘉郡、張啓楷、葉人文、柯志恩、李文良）；勾選項待原件補登（資料 items_pending: true），不產個人頁。
- 推送：官網 main 5396a19 → 1d0f1f6（推前 fetch 確認遠端未前進、待推只此一筆、101 檔全在 record／pagefind 範圍；按完整 SHA 推、ls-remote 核對）。
- 線上：九頁逐位元與 commit 相符（推後約 1 分鐘內）；紀錄頁 200、核對中 0。
- 閘：真源全套 pytest 1667 綠；deploy_site DEPLOY_SITE_OK（官網 pytest 191 綠／125 skip）；fresh read-back 全符。
- 真源：mayoral-pledges-watch 6fa9166。

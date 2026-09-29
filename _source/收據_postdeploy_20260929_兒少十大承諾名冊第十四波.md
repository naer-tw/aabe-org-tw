# 部署後索引收據 2026-09-29

- commit：c760f3d
- 基底：https://aabe.org.tw
- content_live：done
- indexnow：done
- sitemap_lastmod：done（線上 sitemap.xml 連署頁、活動頁 lastmod 皆 2026-09-29；sitemap_index 主 sitemap 同日，閘代理隨 c760f3d 一併改並過 test_sitemap 4 passed）｜原提示（改動頁與 sitemap_index.xml 由 numbers_check／pytest 擋，部署後請確認線上 sitemap 已更新）
- gsc_request_index：N/A（連署頁與活動頁 9/21 已請求索引，同頁一天多次請求無意義；IndexNow 已送 HTTP 200）｜原提示（首頁或方法頁有改動時，到 Search Console 請求索引一次，回填請求時間）
- board_status：改由本線看板 議題_縣市長政見/_狀態.md 回填（名冊線慣例）｜原提示（~/Desktop/國教盟指揮看板/議題_官網影響力數據/_狀態.md 最新交付行改 2026-09-29）
- board_log：done（看板 20260929 日誌，指揮部接手 session）｜原提示（當天日誌加一列：部署時間、main commit c760f3d、驗證結果）
- list_checkbox：N/A（名冊無清單檔）｜原提示（清單檔「已上官網」欄勾 2026-09-29）
- kb_caveat：N/A（名冊非知識庫數字）｜原提示（數字若源自知識庫卡片，卡片 caveat 加「已上官網 2026-09-29」）
- sop_experience：done（本波新坑寫進 shared/LESSONS_inbox：build_search_index.sh --check 並非只檢查、iCloud 衝突目錄卡住政策站暫存區重建）｜原提示（本次踩到的坑寫進 SOP 第七節「經驗紀錄」）

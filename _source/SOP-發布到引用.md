# 國教行動聯盟｜議題發布到 AI 引用 SOP
**版本 1.0 / 2026-04-28**

> 從一份新聞稿草稿，到被 ChatGPT / Perplexity / Claude / Google AI Overview 引用，需要哪些步驟？這份 SOP 一次說清楚。

---

## 整體流程鳥瞰

```
（1）撰寫       （2）部署        （3）索引       （4）驗證       （5）推廣
   ↓              ↓               ↓              ↓              ↓
新聞稿草稿  →  GEO HTML 上線  →  搜尋引擎收錄  →  品質檢測  →  外部引用累積
（30 分）     （30 秒自動化）   （5 分到 7 天）  （月度）       （持續）
```

---

## 第一階段：撰寫（30 分鐘）

### 1.1 內容素材準備
- 新聞稿原文 / 政策聲明
- 相關數據（最重要）
- 國際比較案例（可選但有助 AI 引用）
- 名人引述（含理事長王瀚陽 + 合作學者）
- 參考來源 5-10 筆

### 1.2 用 Claude + GEO Skill 產文章
**指令範例**：
```
@2026-04-22-兒少權法草稿.docx 幫我用 GEO Skill 產政策分析文章，
分類放在「兒少保護」（child-rights），加 FAQ 6 題。
```

Claude 會產出符合 GEO 規範的 HTML（含 4 段 Schema、FAQ、執行摘要、3 大支柱、來源）。

### 1.3 套用文章模板
若 Claude 沒有自動套，使用：
`aabe-deploy/sample-templates/news-release-template.html`

把 `{{...}}` 全部替換為內容。

---

## 第二階段：部署（30 秒）

### 2.1 一鍵部署腳本

```bash
# 設定 IndexNow key（一次設定即可）
export INDEXNOW_KEY=41565caff1994461bfbbb0aaadd9c0cc

# 執行部署
python3 aabe-deploy/deploy-automation/deploy.py 路徑/到/草稿.html
```

**腳本會自動完成**：
- 套對應分類色
- 注入 favicon + manifest + a11y CSS + reading progress
- 加 alternate type="text/markdown" link
- 產生 .md 對應檔
- 更新 sitemap.xml
- git add + commit + push
- IndexNow 即時通知 Bing
- Google sitemap 通知（已棄用，已改 Search Console）

### 2.2 GitHub Pages 部署
- Push 後 ~ 2 分鐘自動部署
- 驗證：`curl -I https://policy.aabe.org.tw/{category}/{slug}.html` 回 200

---

## 第三階段：搜尋引擎索引（5 分鐘 — 7 天）

### 3.1 Bing（透過 IndexNow，5 分鐘內）
deploy.py 已自動 ping IndexNow：
- 提交 endpoint: `https://api.indexnow.org/indexnow`
- 通知 Bing、Yandex、Seznam.cz、Naver
- 預期 5-30 分鐘內出現在 Bing 搜尋

驗證 Bing：
```
搜尋: site:policy.aabe.org.tw "新文章標題"
```

### 3.2 Google（透過 Search Console，48 小時內）
**手動步驟（每篇都要做一次）**：
1. 前往 https://search.google.com/search-console
2. 選擇 `policy.aabe.org.tw` 屬性
3. 上方搜尋框貼新文章 URL
4. 點「請求索引」
5. 等 24-48 小時

**首次設定 Google Search Console**：
- 加 property: `policy.aabe.org.tw`、`advocacy.aabe.org.tw`、`aabe.org.tw`
- 驗證方式選「DNS TXT 記錄」（最穩定）
- 提交 sitemap：`https://policy.aabe.org.tw/sitemap.xml`

### 3.3 Bing Webmaster Tools
- 註冊 https://www.bing.com/webmasters
- 同樣加 property + 提交 sitemap
- 從 Google Search Console 一鍵 import 設定

### 3.4 Perplexity / ChatGPT / Claude
- 不需主動提交（會自動爬 Google index 或自己爬）
- llms.txt 是最重要的 AI 友善索引
- 一般索引時程：1-4 週

---

## 第四階段：驗證（每月）

### 4.1 自動化技術檢測
```bash
cd geo-checker && python3 geo_checker.py --check
```
**期望全綠**：頁面可達性、Schema.org、內部連結、Sitemap

### 4.2 AI 引用實測（每月跑一次）
```bash
PERPLEXITY_API_KEY=pplx-xxxxx python3 geo_checker.py --ai-test --report
```
- 21 組提示語跑 Perplexity
- 看引用率趨勢（目前基準 29%）
- 報告存在 `geo-checker/reports/`

### 4.3 Agent-Readiness 季度檢測
- 季度跑一次 https://isitagentready.com/aabe.org.tw
- 看分數（目前 75，目標 85+）

### 4.4 Google Search Console 監控
- 每週看 Performance：印象次數、點擊、平均位置
- Coverage：是否有索引錯誤
- Schema 報告：Article / FAQPage 是否被識別

---

## 第五階段：推廣（持續累積）

### 5.1 高槓桿動作（依 ROI 排序）

#### 🔥 1. Wikipedia 引用（最高 ROI）
- 在 zh.wikipedia 條目補連結，例如：
  - 「兒童權利公約」→ 連結到 policy/child-rights/
  - 「校園霸凌」→ 連結到 campus-safety/
  - 「少年事件處理法」→ 連結到 child-rights/2026-04-01-少事法...html
- Wikipedia 是 AI 訓練最高權重來源
- 預估 3-6 個月後引用率倍增

#### 💪 2. 主流媒體合作
每次發新聞稿時，**明確要求記者引用 policy.aabe.org.tw 連結**：
- 報導者、端傳媒、天下雜誌、聯合報、自由時報
- 每個媒體引用 = AI 訓練權重 +1
- 累積 10+ 引用 → 域名權威性顯著提升

#### 📣 3. 社群同步發布
每篇新文章發布後同時：
- FB 粉專貼文 + 連結
- Threads / IG 摘要
- 立委辦公室 LINE 群
- 媒體記者群組

範本：
```
【國教盟新政策分析】
{{標題}}

{{30 秒重點 1}}
{{30 秒重點 2}}

完整分析：{{policy_url}}
資料庫：{{advocacy_url}}
```

#### 🎓 4. 學術合作
- 與政大、台大、中央等公共行政、教育、社工系所合作
- 邀請學者參與政策圓桌
- 提供 .md 版資料給研究者直接引用

### 5.2 月度推廣節奏
- 每月 1 日：發布月度倡議報告連結
- 每月 15 日：跑 Perplexity AI 引用測試
- 每季：寫一篇「議題年度回顧」聚合文，含 5+ 內部連結

---

## 月度檢查清單

```
[ ] 跑 geo_checker.py --check 全綠
[ ] 跑 geo_checker.py --ai-test 看引用率變化
[ ] Google Search Console 看 Performance 趨勢
[ ] Bing Webmaster Tools 看 Crawl 狀態
[ ] 確認所有 sitemap 還是最新
[ ] 確認新文章都有對應 .md
[ ] 看 isitagentready 分數（季度）
[ ] Wikipedia 補引用（每月找 1-2 個條目）
```

---

## 故障排除

### Q1：deploy.py 失敗怎麼辦？
1. 確認 `INDEXNOW_KEY` 環境變數已設
2. 確認 git 還有 push 權限
3. 確認 BeautifulSoup 已裝：`pip install beautifulsoup4`
4. 看錯誤訊息，通常是路徑問題

### Q2：IndexNow 回 422 / 4xx？
- 檢查 keyLocation URL 是否能直接訪問
- 檢查 host 是否和 keyLocation 同 domain
- 檢查 URL 是否在 sitemap 內

### Q3：Google 沒收錄？
- 等 48 小時
- 還沒有就到 Search Console 「網址檢查」→「請求索引」
- 確認 robots.txt 沒擋
- 確認 canonical 指向自己

### Q4：Perplexity 沒引用？
- 給時間（新文章要 1-4 週）
- 確認 llms.txt 有列入
- 確認 Schema.org 有效（用 https://validator.schema.org/）
- 推廣 backlink（這是長期工程）

---

## 長期維護建議

### 半年期
- [ ] Schema.org 規範可能更新，跟進新版
- [ ] 重新檢視 llms.txt 是否還對齊內容
- [ ] 檢查 robots.txt 的 AI bot 列表（新 bot 出現）

### 年度
- [ ] 重新跑 isitagentready 看分數變化
- [ ] 文章清理（過時的 archive 標記）
- [ ] sitemap 重新生成
- [ ] domain 續費 + DNS 健康檢查

---

## 連結速查

| 工具 | URL |
|---|---|
| 政策知識庫 | https://policy.aabe.org.tw/（待 DNS）|
| 倡議資料庫 | https://advocacy.aabe.org.tw/（待 DNS） |
| 官網 | https://aabe.org.tw/ |
| GitHub policy repo | https://github.com/naer-tw/policy |
| GitHub advocacy repo | https://github.com/naer-tw/advocacy-database |
| Google Search Console | https://search.google.com/search-console |
| Bing Webmaster | https://www.bing.com/webmasters |
| IndexNow | https://www.indexnow.org/ |
| isitagentready | https://isitagentready.com/ |
| Schema validator | https://validator.schema.org/ |
| FB Debugger | https://developers.facebook.com/tools/debug/ |

---

**作者**：Claude + 王瀚陽
**最後更新**：2026-04-28
**License**：CC BY 4.0

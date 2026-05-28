# 國教行動聯盟 — 三站完整結構地圖

> **產出日期**：2026-05-27
> **用途**：官網檢視 / 改版 / 維護 / SEO audit / 跨站關係釐清

---

## 🌐 1. 三站總覽

| 站別 | 網域 | Local 路徑 | GitHub Repo | 部署平台 |
|---|---|---|---|---|
| **主站** | https://aabe.org.tw | `aabe-deploy/public/` | [naer-tw/aabe-org-tw](https://github.com/naer-tw/aabe-org-tw) | Cloudflare Pages |
| **政策知識庫** | https://policy.aabe.org.tw | `_policy-deploy/` | [naer-tw/policy](https://github.com/naer-tw/policy) | Cloudflare Pages |
| **倡議成果資料庫** | https://advocacy.aabe.org.tw | （未 clone local）| [naer-tw/advocacy-database](https://github.com/naer-tw/advocacy-database) | Cloudflare Pages |

**統一 NGO Schema @id**：`https://aabe.org.tw/#organization`（主站為單一 entity，子站連回主站）

---

## 📁 2. 主站 aabe.org.tw 完整結構

### 統計
- **40 HTML 頁面** | 410 圖片 | 3 影片 | 3 PDF | 3 CSS | 2 JS
- **40 URL 收錄 sitemap.xml**

### 目錄樹

```
aabe-deploy/public/
│
├── 🏠 核心頁面（10 個固定主頁）
│   ├── index.html               主站首頁（最新倡議 + 6 個主題卡）
│   ├── about/index.html         關於我們
│   ├── issues/index.html        兒少與教育議題
│   ├── chronicle/index.html     大事紀
│   ├── events/index.html        活動公告
│   ├── press/index.html         新聞稿索引
│   ├── act/index.html           參與行動
│   ├── methodology/index.html   研究方法論
│   ├── impact/index.html        2023-2025 影響力報告
│   └── contact/index.html       聯絡我們
│
├── 📰 press/ ─── 新聞稿（4 篇）
│   ├── index.html               索引
│   ├── 2026-05-21-drug-abuse-conference-day1/    Day 1 兩會聯合新聞稿
│   ├── 2026-05-22-drug-abuse-conference-full-report/    雙稿並列完整報導
│   └── 2026-05-26-drug-driving-advocacy/    ★ 5/26 毒駕新聞稿（陳情書版）
│
├── 🗓 events/ ─── 活動專頁（21 個 URL）
│   └── 2026-05-20-drug-abuse-conference/
│       ├── index.html            主活動頁
│       ├── moments/              活動花絮（7 圖 + 1 影片 + 1 字幕）
│       └── notes/
│           ├── index.html        全紀錄首頁（兩日入口 + 議程目錄）
│           ├── styles.css        notes 專用樣式
│           ├── 01-saliva-screening/    Day 1 第 1 場（郭鐘隆 唾液篩檢）
│           ├── 02-fraud-crime/         Day 1 第 2 場（張榮興 詐欺）
│           ├── 03-juvenile-drug-gang-fraud/    Day 1 第 3 場（楊士隆 少年涉毒）
│           ├── 04-drug-sex-trafficking/    Day 1 第 4 場（Xin Ren 毒品性拐賣）
│           ├── 05-epidemiology/        Day 1 第 5 場（陳為堅 流行病學）
│           ├── 06-california-paradox/  Day 1 第 6 場（Shih Lung Huang 加州悖論）
│           ├── 07-thailand-cannabis/   Day 1 第 7 場（Rasmon 泰國大麻）
│           ├── 08-hong-kong-drug/      Day 1 第 8 場（Zhong Hua 香港）
│           ├── 09-japan-drug/          Day 1 第 9 場（戴伸峰 日本）
│           ├── img/                    各場投影片截圖
│           └── day2/
│               ├── index.html          Day 2 總覽
│               ├── 01-sem-machine-learning/    Day 2 第 1 場
│               ├── 02-ketamine-health/         Day 2 第 2 場
│               ├── 03-hong-kong-invisible-minority/    Day 2 第 3 場
│               ├── 04-holistic-recovery/       Day 2 第 4 場 ★國教盟主場
│               ├── 05-etomidate/               Day 2 第 5 場
│               ├── 06-systematic-review/       Day 2 第 6 場
│               ├── 07-juvenile-counseling/     Day 2 第 7 場 ★兒童健康聯盟主場
│               ├── 08-juvenile-fraud-life-course/    Day 2 第 8 場
│               ├── 09-three-inmate-comparison/      Day 2 第 9 場
│               └── panel/                       綜合座談
│
├── 📋 act/ ─── 參與行動（5 個 URL）
│   ├── index.html
│   └── cwa-reform/  ★ 兒少權法 165 條修法深度頁（2026-05-19 新增）
│       ├── index.html
│       ├── hearing-speeches/index.html
│       ├── child-worker-management/index.html
│       ├── mental-health-digital-safety/index.html
│       ├── assets/
│       ├── downloads/
│       └── images/
│
├── 🖼 wp-content/uploads/ ─── 圖片資源
│   ├── logo-naer.png / logo-naer-icon-only.png    NGO logo
│   ├── og-2026-conference.png                     研討會通用 OG
│   ├── og-2026-drug-driving-trilogy-1200x630.jpg ★ 5/26 三部曲 OG（132x 記者會照）
│   ├── og-2026-drug-driving-trilogy.jpg           （原比例 976x590）
│   ├── press-2025-0311-vape-as-drug-132x.jpg     5/26 inline 132x 記者會
│   ├── favicon-32.png / apple-touch-icon.png      icon 系列
│   └── （其他 400+ 議題相關圖檔）
│
├── 🎨 assets/aabe.css                共用樣式（topbar / 字級 / 配色）
│
├── 📊 SEO / 結構化資料
│   ├── sitemap.xml                  40 URL（首頁 + 6 大頁 + events 23 + press 4 + act 5）
│   ├── sitemap_index.xml            sitemap 索引（指向 main + policy + advocacy）
│   ├── robots.txt                   爬蟲規則（含 20+ AI bot allow）
│   ├── llms.txt                     AI 引擎 markdown 索引
│   ├── humans.txt                   人類友善資訊
│   ├── feed.xml                     Atom feed
│   ├── _redirects                   Cloudflare Pages 301 重導（5/26 兩 URL 搬 policy）
│   ├── 404.html                     錯誤頁
│   ├── cf7b84e6b78b446bd75fd7e04b9c06b7.txt    IndexNow API key
│   └── .well-known/security.txt     RFC 9116 安全聯絡
│
└── _source/ ─── 內部文件（Cloudflare 不部署）
    ├── SOP-發布到引用.md
    ├── SOP-output覆蓋檢查表.md      5/22+5/26 教訓
    ├── SITE-STRUCTURE-2026-05-27.md  ← 本檔
    ├── （其他 SOP / playbook / migration scripts）
```

### sitemap.xml URL 分類
- /events/ : 23 URL（5/20-21 研討會所有專頁）
- /act/ : 5 URL（cwa-reform 兒少權法）
- /press/ : 4 URL（5/21、5/22、5/26 新聞稿 + 索引）
- 6 個核心固定頁：about/issues/chronicle/contact/methodology/impact

---

## 📚 3. policy.aabe.org.tw 完整結構

### 統計
- **118 HTML 檔案**（含 cwa-reform 75 個歷史 archive）
- **40 URL 收錄 sitemap.xml**（精選政策深度文 + 8 分類索引頁 + 首頁）

### 目錄樹

```
_policy-deploy/
│
├── index.html                       政策知識庫首頁（最新專題 + 8 分類）
├── sitemap.xml                      40 URL
├── llms.txt                         AI 引擎 markdown 索引
├── robots.txt
├── manifest.json                    PWA 配置
├── 404.html
├── CNAME                            policy.aabe.org.tw
├── 41565caff1994461bfbbb0aaadd9c0cc.txt    IndexNow key
│
├── 📂 8 大政策主軸（每個含 index.html 分類索引）
│   ├── child-rights/      兒少權益 — 16 篇（最多，含剴剴案、兒童家庭部、CRC 等）
│   ├── child-health/      兒童健康 — 3 篇
│   ├── campus-safety/     校園安全 — 6 篇（含霸凌、轉介教育）
│   ├── education-reform/  教育改革 — 6 篇（含性平法、實驗教育）
│   ├── youth-health/      ★ 青少年健康 — 4 篇（含 5/26 兩篇毒駕深度文）
│   ├── health/            健康 — 3 篇（含 2026 無菸品世代、無菸城市）
│   ├── school-lunch/      校園午餐 — 3 篇
│   └── teacher-affairs/   教師事務 — 2 篇
│
├── 📂 cwa-reform/          兒少權法 165 條修法（75 HTML，歷史 archive，未進 sitemap）
│   ├── articles/
│   ├── policies/
│   ├── intl-benchmarks/
│   ├── reform-proposals/
│   └── css/
│
└── images/                  分類 OG 圖 + logo
    ├── logo-naer.png
    └── og-*.jpg            各篇文章 OG 圖
```

### sitemap.xml URL 分類（40 URL）
- /child-rights/ : 12 URL
- /campus-safety/ : 6 URL
- /education-reform/ : 6 URL
- /youth-health/ : 4 URL ★（5/26 新增 2 = 第 30+31 篇）
- /school-lunch/ : 3 URL
- /health/ : 3 URL
- /child-health/ : 3 URL
- /teacher-affairs/ : 2 URL
- 首頁 : 1 URL

### 累計政策深度文
- 全站 sitemap = 40 URL
- 扣掉 9 個分類索引頁與首頁 = **31 篇政策深度文**（與描述「31 篇深度分析」一致）

---

## 🏛 4. advocacy.aabe.org.tw 完整結構（2026-05-27 已 clone）

### 統計
- **Local 路徑**：`_advocacy-deploy/`
- **內容類型**：純 Markdown / JSON / CSV 機器可讀資料庫（**0 個內容 HTML**，僅 index.html + 404.html）
- **首頁 H1**：「倡議成果資料庫」
- **用途**：AI 引擎友善的倡議行動資料庫（給 LLM / GPT 等檢索用）

### 目錄樹

```
_advocacy-deploy/
│
├── index.html                       靜態首頁（內嵌 JS 動態渲染）
├── 404.html
├── sitemap.xml                      39 URL（96% 指向 knowledge-base/）
├── llms.txt                         AI 引擎索引
├── manifest.json
├── robots.txt
├── humans.txt
├── advocacy-summary.md              ⚠ 含過時/錯誤資訊（見下）
├── CNAME                            advocacy.aabe.org.tw
├── 41565caff1994461bfbbb0aaadd9c0cc.txt    IndexNow key（與 policy 共用同一把）
│
└── knowledge-base/                  AI 資料庫（純 markdown / JSON / CSV）
    ├── about/         （2 md）      組織自介
    ├── api/           （3 json）    機器可讀 API（organization / topics / actions）
    ├── faq/           （7 md）      常見問題
    ├── google-sheets/ （5 csv）     匯出 Google Sheets 原始資料
    ├── positions/     （5 md）      立場文件
    ├── press/         （68 md）     ★ 新聞稿 v1（68 篇）
    ├── press-v2/      （10 md + 1 json）  ★ 新聞稿 v2 重整版（11 個）
    ├── press-complete/（124 md）    ★ 新聞稿完整版（124 篇）
    ├── reports/       （6 md）      年度／議題報告
    └── schema/        （2 json）    schema.org 定義
```

### sitemap.xml URL 分類（39 URL）
- /knowledge-base/ : 36 URL（含 3 個版本的 press 索引）
- 首頁 : 1
- advocacy-summary.md : 1
- llms.txt : 1

### ⚠⚠⚠ Critical Issues（**3 個必修**，違反 user memory rule）

| # | 問題 | 出現位置 | 影響 |
|---|---|---|---|
| **1** | **英文名錯誤**：「National Alliance for Education Action, NAER」 | `advocacy-summary.md` + `knowledge-base/api/organization.json` | 違反 user memory「英文正式名 Action Alliance on Basic Education / AABE，**非 NAER**」 |
| **2** | **計數過時**：「25 篇政策深度分析」 | `advocacy-summary.md` 3 處 | Policy 站實際 **31 篇**（已加 5/26 兩篇）|
| **3** | **連結過時**：`naer-tw.github.io/policy/` | `advocacy-summary.md` 多處 | 應為 `policy.aabe.org.tw/`（CNAME 早已設好）|

### 多版本 press 之謎
- `press/`：68 篇（v1 原版）
- `press-v2/`：11 個（重整中）
- `press-complete/`：124 篇（**最完整版本**？）
- ❓ 未來應該整合到單一版本（避免讀者／AI 混淆）

---

## 🔗 5. naer-tw GitHub 組織內所有相關 repo（部分）

| Repo | 用途 | 部署網域 |
|---|---|---|
| `aabe-org-tw` | 主站 | aabe.org.tw |
| `policy` | 政策知識庫 | policy.aabe.org.tw |
| `advocacy-database` | 倡議成果 | advocacy.aabe.org.tw |
| `naer-tw.github.io` | 組織根 landing | naer-tw.github.io |
| `child-rights-watch` | 兒少人權監督平台 | （別站）|
| `cedaw-watch` | CEDAW 監督 | （別站）|
| `covenants-watch` | 兩公約監督 | （別站）|
| `disability-rights-watch` | CRPD 監督 | （別站）|
| `daily-news` | 每日新聞摘要 | （內部）|
| `crc-prep-2026` | CRC 第 2 輪審查準備 | （內部）|
| `evidence-pipeline` | 三公約共用證據 pipeline | （內部）|
| `debate-registration` | 北北基桃青年發聲盃報名 | （內部）|

---

## 🧭 6. 跨站關係圖

```
        ┌──────────────────────────────────────────────────────┐
        │                  aabe.org.tw 主站                     │
        │  （NGO 主要對外窗口、新聞稿、活動、議題、聯絡）        │
        └─────────────────────┬─────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
   │ policy.aabe   │  │ advocacy.aabe │  │ events 子頁    │
   │ 政策深度 31 篇 │  │ 大事紀資料庫   │  │ 5/20-21 研討會│
   │  6 大主軸     │  │ 113 篇新聞稿  │  │  全紀錄 18 場 │
   └───────────────┘  └───────────────┘  └───────────────┘
            ▲
            │ 301 redirect from
            │ /press/2026-05-26-vape-device-research/
            │ /press/2026-05-26-drug-driving-policy/
            └─── (5/26 GEO 深度文搬遷到此 = 第 30+31 篇)
```

---

## 📊 7. 跨站 SEO 統計（5/27 抓取）

| 站別 | sitemap URL | 收錄頁數 | OG 圖數 | Schema blocks/page |
|---|---|---|---|---|
| 主站 | 40 | 40 HTML | 5+ 主要 | 4-6 blocks |
| Policy | 40 | 118 HTML（部分 archive 未收）| 30+ | 4 blocks |
| Advocacy | （未 audit）| - | - | - |

---

## 📝 8. 維護注意事項

### 部署觸發
- 主站：`git push origin main` to `naer-tw/aabe-org-tw` → Cloudflare Pages auto-deploy（通常 30-60 秒，偶爾 5-10 分鐘）
- Policy：`git push origin main` to `naer-tw/policy` → 同上
- Advocacy：需 clone repo 後操作

### 部署後必做
1. IndexNow push（Bing + Hub）— Python script 已有
2. GSC URL Inspection（每天上限）
3. Schema.org Rich Results Test
4. Production curl 驗證

### SOP 文件
- `_source/SOP-output覆蓋檢查表.md` — output 整批覆蓋的 4+ 步檢查（含 emoji / 設計統一 / 事實校正）
- `_source/SOP-發布到引用.md` — 新聞稿/政策文發布到引用 SOP
- `_source/SITE-STRUCTURE-2026-05-27.md` — 本檔（結構地圖）
- `_wikipedia-vfd-defense/HANDOFF-2026-05-25.md` — Wikipedia vfd 防禦戰

---

**最後更新**：2026-05-27 by Claude

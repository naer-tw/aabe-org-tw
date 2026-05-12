# aabe-org-tw

社團法人國教行動聯盟（Action Alliance on Basic Education）官方網站原始碼。

> **網址**：https://aabe.org.tw
> **部署**：Cloudflare Pages
> **架構**：靜態網站（HTML + CSS）
> **License**：CC BY 4.0（內容）/ MIT（程式碼）

---

## 📁 資料夾結構

```
aabe-org-tw/
├── README.md           ← 本檔案
├── .gitignore
├── public/             ← Cloudflare Pages serve 這個資料夾
│   ├── index.html       (首頁)
│   ├── about/index.html (關於我們)
│   ├── issues/index.html (兒少與教育議題)
│   ├── chronicle/index.html (大事紀)
│   ├── events/index.html (活動公告)
│   ├── contact/index.html (聯絡我們)
│   ├── assets/aabe.css  (共用樣式)
│   ├── wp-content/uploads/ (logo + favicon 圖檔)
│   ├── llms.txt         (AI 引擎索引清單)
│   ├── robots.txt       (含 20+ AI bot allow)
│   ├── humans.txt
│   └── .well-known/security.txt (RFC 9116)
└── _source/            ← 內部文件，Cloudflare 不部署
    ├── SUMMARY-2026-04-28.md
    ├── SOP-發布到引用.md
    ├── 更新說明-2026-04-28.md
    ├── wordpress-snippets/ (WP 時代遺留，已不使用)
    ├── migration-scripts/
    ├── deploy-automation/
    └── sample-templates/
```

---

## 🚀 Cloudflare Pages 部署設定

| 項目 | 值 |
|---|---|
| Production branch | `main` |
| Build command | （留空，靜態網站） |
| **Build output directory** | **`public`** |
| Root directory | `/` |

---

## 🌐 網域

- **正式**：`aabe.org.tw`
- **暫時**：`aabe-org-tw.pages.dev`（Cloudflare 自動分配）

---

## 🤖 AI 友善設計（GEO 優化）

- 6 頁皆含完整 Schema.org JSON-LD（NGO / WebSite / CollectionPage / Event / ContactPage）
- 全站連線至 NGO `@id` (`https://aabe.org.tw/#organization`)
- robots.txt 明確 allow 20+ AI bots（GPTBot / ClaudeBot / PerplexityBot / Google-Extended 等）
- llms.txt 提供 AI 引擎 markdown 索引
- 每頁 OG + Twitter Card 完整

---

## 📦 相關 Repos

- [naer-tw/policy](https://github.com/naer-tw/policy)：政策知識庫（policy.aabe.org.tw）
- [naer-tw/advocacy-database](https://github.com/naer-tw/advocacy-database)：倡議成果資料庫（advocacy.aabe.org.tw）
- [naer-tw/naer-tw.github.io](https://github.com/naer-tw/naer-tw.github.io)：組織根網域 landing

---

## 📞 聯絡

- Email: Action.A.E0626@gmail.com
- Facebook: https://www.facebook.com/twedumove/
- 立案字號：1030182063
- 統一編號：41142910
- 成立日期：2012-06-26

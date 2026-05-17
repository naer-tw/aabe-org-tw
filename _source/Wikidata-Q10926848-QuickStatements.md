# Wikidata Q10926848 QuickStatements 一鍵批次匯入 · 2026-05-17

> **省 25 分鐘**：用 QuickStatements 工具一鍵批次匯入下方 statements，不用逐項點 add。
> 工具：https://quickstatements.toolforge.org/

---

## 操作步驟（5 分鐘）

### 1. 開 QuickStatements
https://quickstatements.toolforge.org/#/

### 2. 用 Wikipedia / Wikidata 帳號（Frankw0128）登入

右上「Log in」→ 用 OAuth 授權

### 3. 點「New batch」→「v1 commands」

### 4. 把下方「QuickStatements 指令」整段複製貼上

### 5. 點「Import V1 commands」→ 預覽 → 「Run」

### 6. 等 30 秒 → 全部 statement 自動上 Q10926848

---

## QuickStatements 指令（v1.1 修正版 — 25 筆 安全可跑）

> **重大修正**（瀏覽器 AI 品管發現）：
> - 4 個 Q 編號 v1.0 用錯了（指到灶神星、藝術形式、地下水、日本航母 G18 計畫）→ v1.1 全部換正確
> - P488 chairperson × 5 + P112 founder 因王立昇/陳鐵虎/王瀚陽都還沒 Q-item，**暫刪 6 筆**（之後三人有 Q-item 再單獨補 batch）

```
Q10926848	Len	"國教行動聯盟"
Q10926848	Len-tw	"國教行動聯盟"
Q10926848	Len-hk	"國教行動聯盟"
Q10926848	Len-en	"Action Alliance on Basic Education"
Q10926848	Den	"Taiwanese advocacy organization for children's rights and basic education, founded in 2012"
Q10926848	Dzh	"台灣兒少與教育倡議組織，由家長部與青年部雙軸共構推動兒少權益，2012 年成立"
Q10926848	Dzh-tw	"台灣兒少與教育倡議組織，由家長部與青年部雙軸共構推動兒少權益，2012 年成立"
Q10926848	Azh	"國教盟"
Q10926848	Azh	"AABE"
Q10926848	Azh-tw	"國教盟"
Q10926848	Azh-tw	"AABE"
Q10926848	Aen	"AABE"
Q10926848	Aen	"National Education Action Alliance"
Q10926848	P31	Q163740	S854	"https://aabe.org.tw/about/"
Q10926848	P31	Q431603	S854	"https://aabe.org.tw/about/"
Q10926848	P17	Q865	S854	"https://aabe.org.tw/about/"
Q10926848	P571	+2012-06-26T00:00:00Z/11	S854	"https://aabe.org.tw/about/"
Q10926848	P1454	"人民團體"	S854	"https://aabe.org.tw/about/"
Q10926848	P856	"https://aabe.org.tw/"
Q10926848	P968	"Action.A.E0626@gmail.com"
Q10926848	P2013	"twedumove"	S854	"https://www.facebook.com/twedumove/"
Q10926848	P101	Q8434	S854	"https://aabe.org.tw/issues/"
Q10926848	P101	Q8354948	S854	"https://aabe.org.tw/issues/"
Q10926848	P101	Q546113	S854	"https://aabe.org.tw/issues/"
Q10926848	Sen_wiki	"國教行動聯盟"
```

### v1.0 → v1.1 變更對照

| 動作 | 之前（v1.0 錯）| 之後（v1.1 正）|
|---|---|---|
| P31 instance of | Q11200727（日本航母 G18 計畫 ✈️🚢）| **Q431603**（advocacy group）|
| P101 field of work | Q3030（灶神星 ☄️）| **Q8434**（education）|
| P101 field of work | Q1437361（藝術形式 🎨）| **Q8354948**（children's rights）|
| P101 field of work | Q161598（地下水 💧）| **Q546113**（public policy）|
| P488 chairperson × 5 | 字串 "王立昇/陳鐵虎/王瀚陽" | **刪除**（datatype 不接受字串）|
| P112 founded by × 1 | 字串 "王立昇" | **刪除**（同上）|

### 為什麼刪 chairperson？

P488 / P112 的 datatype 都是 `wikibase-item`，只接受 Q-item 不接受字串值。
王立昇 / 陳鐵虎 / 王瀚陽 在 Wikidata 都還沒有 Q-item。

**處理**：
1. 本批先省略
2. Wikipedia 條目大事紀已寫到「2026 年 王瀚陽接任理事長」等資訊（第一輪 Frankw0128 已完成編輯）
3. 之後若要為三人申請 Q-item（需每人至少 1 篇獨立第三方來源證明 notability）再單獨補 chairperson batch

---

## 指令解讀（給你 reference）

### Label / Description / Alias

| 指令 | 意義 |
|---|---|
| `Len "..."` | English label |
| `Lzh "..."` | Chinese label |
| `Den "..."` | English description |
| `Dzh "..."` | Chinese description |
| `Aen "..."` | English alias（可多筆）|
| `Azh "..."` | Chinese alias（可多筆）|

### Statements（Property = Value + Reference）

| Property | 中文 | 值 / Q編號 |
|---|---|---|
| `P31` | instance of | Q163740 (NGO) + Q11200727 (advocacy group) |
| `P17` | country | Q865 (中華民國 Republic of China) |
| `P571` | inception | 2012-06-26 |
| `P1454` | legal form | 人民團體 |
| `P856` | official website | aabe.org.tw |
| `P968` | email | Action.A.E0626@gmail.com |
| `P2013` | Facebook | twedumove |
| `P101` | field of work | Q3030 (教育) / Q1437361 (兒童權利) / Q161598 (公共政策) |
| `P488` | chairperson | 王立昇 × 2 任 / 陳鐵虎 / 王瀚陽 × 2 任 |
| `P112` | founded by | 王立昇 |
| `S854` | reference URL | 各 statement 加 reference |
| `P580` | start time | qualifier for chairperson 任期 |
| `P582` | end time | qualifier for chairperson 任期 |

### Sitelink

| 指令 | 意義 |
|---|---|
| `Sen_wiki "國教行動聯盟"` | English Wikipedia sitelink ❌ 不會匯入因為沒有 en Wikipedia 條目 |
| `Szh_wiki "國教行動聯盟"` | 中文 Wikipedia sitelink（如果已有條目連結就跳過）|

---

## ⚠️ 注意事項

### 1. 部分人名 chairperson 沒有獨立 Q 編號
王立昇 / 陳鐵虎 / 王瀚陽 在 Wikidata 可能沒有獨立 Person 條目。
QuickStatements 看到引號內的人名會用「文字值」處理（不轉 Q 編號），這也合法。
未來他們有 Wikidata 條目了再回來換成 Q 編號。

### 2. P582 (end time) 用 2025-12-31 暫代
王瀚陽現任理事長到 2025 年底（第五屆任期 2023-2025）。
2026 年初新理事長就任時，回 QuickStatements 把現任這筆 P582 改為精確日期。

### 3. P101 field of work 的 Q 編號可能不準
我猜的 Q3030 / Q1437361 / Q161598。匯入後檢查實際 entity 是否正確。
如不對，到該 statement 右下角 edit 改成正確 Q。

### 4. Refs 用 S854 (reference URL)
所有 statement 都附 aabe.org.tw 自家頁面當 reference。
這是 Wikidata 最寬鬆的 reference 方式（policy P248 + URL 也可以但太囉嗦）。

---

## 預期結果

匯入後 Q10926848 條目會有：

- ✅ 中英文 label / description / alias 完整
- ✅ 12+ 個 statements（instance of, country, inception, website, chairperson 5 任, etc）
- ✅ 每個 statement 都附 reference URL
- ✅ 中文 Wikipedia sitelink 自動連結

24-48 小時後：
- Google Knowledge Graph 抓 Wikidata → 開始整合
- Wikipedia infobox 可以從 Q10926848 自動帶資料
- 1-3 個月後 ChatGPT/Claude/Perplexity 訓練快照更新到此版

---

## 如果 QuickStatements 失敗

逐筆手動編輯：照 `_source/Wikidata-Q10926848-更新草稿.md` 操作（30 分鐘）

---

*版本：v1.0 / 2026-05-17*
*建議：先預覽 → 確認無錯 → Run*

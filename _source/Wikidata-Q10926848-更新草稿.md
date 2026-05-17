# Wikidata 國教行動聯盟 Q10926848 更新草稿 · 2026-05-17

> **重大發現**：條目 Q10926848 已存在但完全空白（0 聲明，最後編輯 2013-04-14）
> URL: https://www.wikidata.org/wiki/Q10926848
> 影響：填上後，Google Knowledge Graph、ChatGPT、Claude、Perplexity 都能用 Wikidata 認 entity

---

## 為什麼 Wikidata 比 Wikipedia 更關鍵

| 項目 | Wikipedia | Wikidata |
|---|---|---|
| 形式 | 自然語言文章 | 結構化資料（property = value）|
| AI 讀取 | 需要 NLP 解析 | **直接結構化讀取** |
| 多語言 | 各語言獨立 | **一份資料、所有語言共用** |
| Knowledge Graph | 主要來源 | **核心 backbone** |
| 編輯難度 | 高（要寫好文章）| 低（填表格）|

→ **30 分鐘填好可換來 AI 認知大幅提升**。

---

## 操作步驟

1. 開 https://www.wikidata.org/wiki/Q10926848
2. 用 Wikipedia 同帳號（Frankw0128）登入即可
3. 編輯方式：點每個 property 旁的「+ add statement」
4. 完成後在右上「Move to top」可以調整顯示順序

---

## 標籤與描述（最上方）

```
中文 (zh):       國教行動聯盟
中文（台灣）(zh-tw): 國教行動聯盟
英文 (en):       Action Alliance on Basic Education
日文 (ja):       国教行動連盟（如要支援日本 AI）

描述 中文:    台灣兒少與教育倡議組織
描述 英文:    Taiwanese advocacy organization for children's rights and basic education

別名 (Also known as):
  zh: 國教盟, AABE
  en: AABE, National Education Action Alliance（舊名，留歷史紀錄）
```

---

## Statements（屬性與值）

### 基本識別

| Property | 中文 | 值 | 備註 |
|---|---|---|---|
| `P31` | instance of | Q163740（非政府組織）<br>+ Q11200727（教育倡議組織）| 多重 instance |
| `P17` | country | Q865（中華民國）| |
| `P571` | inception (成立日) | 2012-06-26 | 精度：日 |
| `P1448` | official name | 國教行動聯盟 | 中文 |
| `P1448` | official name | Action Alliance on Basic Education | 英文 |
| `P1454` | legal form | 人民團體 | 文字值 |

### 聯絡與身份

| Property | 中文 | 值 |
|---|---|---|
| `P856` | official website | https://aabe.org.tw |
| `P968` | email | Action.A.E0626@gmail.com |
| `P2013` | Facebook ID | twedumove |
| `P159` | headquarters location | Q174 (台北市) 或留空 |
| `P1297` | Taiwan unified business no. | 41142910 |

### 領導人物（時序很重要）

新增多個 chairperson (P488)，每個都加 start time / end time qualifier：

| Chairperson | 期間 | Qualifier |
|---|---|---|
| 王立昇 | 2012-06-26 ~ 2015 | start time P580 + end time P582 |
| 王立昇 | 2015 ~ 2018 | （連任第二屆）|
| 陳鐵虎 | 2018 ~ 2021 | |
| 王瀚陽 | 2021 ~ 2023 | （第四屆）|
| 王瀚陽 | 2023-11 ~ 2025 | （第五屆，連任）|

如果這些人 Wikidata 有條目可連 Q 編號；沒有就用文字值。

### 組織結構

| Property | 中文 | 值 |
|---|---|---|
| `P112` | founded by | 王立昇（如有 Q 編號連 Q 編號）|

### 識別碼 / 跨平台連結

| Property | 中文 | 值 |
|---|---|---|
| `P1296` | Encyclopedia of Taiwan ID | （如有）|

### 主題關注（讓 AI 知道這組織做什麼）

新增多個 `P101` (field of work)：

| 值 | 中文 |
|---|---|
| Q3023 | 教育 |
| Q1078500 | 兒少權益 / 兒童權利 |
| Q6453831 | 公共政策 |
| Q11707 | 倡議活動 / advocacy |

新增多個 `P527` (has part)，列出組織內部架構：
- 家長部
- 青年部
- 理監事會

### 跨語言條目連結

頁面下方「Sitelinks」區：

| 語言 | 連結 |
|---|---|
| zhwiki | 國教行動聯盟 |
| zhwikiquote | （如有）|

---

## 填寫順序建議

**急（5 分鐘做完）：**
1. 中英文 label / description / aliases（最上面）
2. P31 instance of（NGO + 教育倡議組織）
3. P17 country（中華民國）
4. P571 inception（2012-06-26）
5. P856 official website
6. P488 chairperson 三任理事長
7. P2013 Facebook
8. Sitelinks → zhwiki: 國教行動聯盟

**緩（之後再填）：**
9. P101 field of work
10. P527 has part
11. P159 headquarters location

---

## 完成後驗證

1. 進 https://www.wikidata.org/wiki/Q10926848 看自己編輯結果
2. 24-48 小時後 Google Knowledge Graph 抓 Wikidata 同步
3. 1-3 個月 ChatGPT/Claude/Perplexity 訓練快照更新到此版

---

## 連動效果

Wikidata 填好後：
- ✅ Google 搜「國教行動聯盟」右側 Knowledge Panel 出現完整資訊（不需 GBP 也可能跳）
- ✅ ChatGPT 問「AABE founded year」答對 2012-06-26
- ✅ Claude 問「Action Alliance on Basic Education chairperson」答對王瀚陽
- ✅ Perplexity 引用時直接帶 official website 連結
- ✅ Wikipedia infobox 可以連 Wikidata 自動帶資料

---

## ⚠️ Wikidata 編輯禁忌

| ❌ 別做 | ✅ 改做 |
|---|---|
| 加 `most influential` 之類主觀標籤 | 只填客觀屬性 |
| 在 description 寫「最大」「重要」 | description 寫短中性事實 |
| 重複新增同樣 chairperson 而沒分期間 | 用 P580 start time + P582 end time 區分各任期 |
| 用組織自家網站當所有資料 source | 各 statement 加 reference（媒體 / 政府公告）|

---

## Reference 添加方式

每個重要 statement（如 chairperson、inception）右下角點「+ add reference」：

| Statement | Reference URL |
|---|---|
| inception 2012-06-26 | https://aabe.org.tw/about/ |
| chairperson 王瀚陽 | https://aabe.org.tw/about/ |
| official website | （無需 ref，自己就是）|

policy P248 (stated in) + URL 即可，Wikidata 對 reference 寬鬆。

---

*版本：v1.0 / 2026-05-17*
*Q10926848 是 Wikidata 給 國教行動聯盟 的永久 ID*
*影響：填完後 1-3 個月內 AI 認知大幅提升*

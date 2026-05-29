# 國教行動聯盟三站 — Audit 校正紀錄(2026-05-27 補)

> **產出**:2026-05-27 by Half Second(對標 Phase 6.3 視覺治理視角)
> **用途**:給負責官網修正的下一個 session 使用,避免從過時的 SITE-STRUCTURE 文件出發
> **配對檔**:`SITE-STRUCTURE-2026-05-27.md`(原描述,部分過時)

---

## ⚠️ 重要提醒:`SITE-STRUCTURE-2026-05-27.md` 該文件已部分過時

原文件在 §4 列「Advocacy 站 Critical Issues 3 個必修」:
1. ❌ advocacy-summary.md 英文名錯誤 「NAER」
2. ❌ 計數過時 25 篇
3. ❌ 舊連結 `naer-tw.github.io/policy/`

**實際 2026-05-27 掃描結果**:

| 原文件聲稱 | 實際狀態 |
|---|---|
| advocacy-summary.md 含 NAER | **0 次**(已修)|
| organization.json 含「National Alliance for Education Action」| **0 次**(已修,改為 `Action Alliance on Basic Education / AABE`)|
| advocacy-summary.md 舊連結 `naer-tw.github.io/policy/` | **0 次**(已修)|
| 計數 25 篇 | 主站 llms.txt + index.html 寫 **29**;Policy + Advocacy 寫 **31** |

**結論**:Advocacy 站已被前一輪修過,但 SITE-STRUCTURE 描述沒同步更新。

---

## ✅ 校正後的真實 P0(2026-05-27 重新掃描)

### P0-1 · Schema NGO `@id` 三站統一

```
現況(三站三個 entity):
  主站      → @id: https://aabe.org.tw/#organization
  Policy    → @id: https://policy.aabe.org.tw/#organization      ⚠️ 第二 entity
  Advocacy  → publisher: policy.aabe.org.tw/#organization        ⚠️ 跟著 policy 而非主站

修法:
  Policy + Advocacy 站所有 NGO @id 改為 https://aabe.org.tw/#organization
  Policy + Advocacy 站可保留自己的 #website @id(那是 WebSite 不是 NGO)
```

**範圍清單**(實際 grep 結果):

| 檔案 | `@id: https://policy...#organization` 出現次數 |
|---|---|
| `_policy-deploy/index.html` | 5 次(NGO + creator + publisher 多處)|
| `_policy-deploy/[各分類]/index.html` | 各分類索引頁可能各 1-2 次,待掃 |
| `_advocacy-deploy/index.html` | 4 次 |

**注意**:不要動 `#website`、`#dataset` 這些 — 它們是該站獨有的 entity,不該共用。**只動 `#organization`**。

### P0-2 · 主站自己內部「29 / 31 篇」矛盾

```
主站 index.html  → 同一頁出現:
  「29 篇政策論述」(meta description)
  「29 篇政策深度」(2023-2025 三年累計)
  「31 篇政策深度分析專題」(知識庫卡片)
  「31 篇政策深度分析」(知識庫描述)

主站 llms.txt   → 寫:
  「29 篇政策深度分析」(2 處)
  「policy.aabe.org.tw 政策深度分析(29 篇)」

Policy 站      → 全部寫 31 篇 ✓
Advocacy 站    → 全部寫 31 篇 ✓
```

**修法**:Policy 站為 source of truth,主站 index.html + llms.txt 統一改為 **31 篇**。

**檔案清單**:
- `aabe-deploy/public/index.html`(4 處 29 改 31)
- `aabe-deploy/public/llms.txt`(2 處 29 改 31)

**注意 llms.txt 優先級**:LLM 引擎(GPTBot / ClaudeBot / PerplexityBot)會優先讀 llms.txt 取得官方數據。**這個檔比 HTML 還重要**,因為 RAG 引擎會把它當作 ground truth。

### P0-3 · 「社團法人」分流處理(關鍵 — 不是全刪)

實際 grep 結果有 **兩種情境**,不可粗暴 sed 全刪:

**✅ 教學說明用法(保留 — 是正確使用)**:

```
主站 methodology/index.html (line 343-344):
  <dt>AABE vs NAER vs 社團法人</dt>
  <dd>...請勿使用「NAER」(舊內部簡稱已棄用)或「社團法人國教行動聯盟」
      (國教盟為內政部立案的人民團體,非社團法人)。</dd>

主站 llms.txt (line 10):
  - 立案:2014 年 3 月 9 日由內政部立案為人民團體(非社團法人)

→ 這些是教學對照,讓 AI 與讀者知道「應該怎麼稱呼」,要保留
```

**❌ 實際污染(需逐一判斷後修)**:

主站 9 個檔案含「社團法人」:
- ✅ methodology/index.html(教學,保留)
- ✅ llms.txt(教學對照,保留)
- ⚠️ press/index.html(待查 context)
- ⚠️ press/2026-05-21-drug-abuse-conference-day1/index.html
- ⚠️ press/2026-05-22-drug-abuse-conference-full-report/index.html
- ⚠️ events/2026-05-20-drug-abuse-conference/index.html
- ⚠️ events/2026-05-20-drug-abuse-conference/notes/index.html
- ⚠️ events/2026-05-20-drug-abuse-conference/notes/day2/index.html
- ⚠️ events/2026-05-20-drug-abuse-conference/notes/day2/01-sem-machine-learning/index.html

Advocacy 8 個 Markdown(新聞稿原檔):
- ⚠️ press-complete/2025/114.05.26台灣拒菸聯盟記者會新聞稿OK.md
- ⚠️ press-complete/2025/12月/20251206「生育·養育·教育—兒童成長需求總體檢」論壇新聞稿.md
- ⚠️ press-complete/2025/07月/20250711打造「兒少家庭部」藍圖論壇新聞稿V1.md
- ⚠️ press-complete/2025/08月/20250818新聞稿ok.md
- ⚠️ press-complete/2024/07月/20240705.md
- ⚠️ press/2025/05月/114.05.26台灣拒菸聯盟記者會新聞稿OK.md
- ⚠️ press/2025/08月/20250818新聞稿ok.md
- ⚠️ reports/國教盟2025合作單位與專家學者.md

**修法建議**:

```python
# 簡版 pseudo-code
for file in candidates:
    if grep "請勿使用「社團法人」" or grep "非社團法人":
        # 教學對照,SKIP
        continue
    elif grep "社團法人國教行動聯盟" or grep "本社團法人" or grep "我社團法人":
        # 真實污染自稱,改為「國教行動聯盟」or「本聯盟」or「人民團體國教行動聯盟」
        sed replace
    else:
        # 灰色地帶,人工判斷
        flag for manual review
```

**範圍**:主站 7 個 HTML + Advocacy 8 個 Markdown ≈ 15 檔
**預估**:1-2 小時(因為需要 case-by-case 判斷)

---

## 🟡 P1(校正後 — 視覺一致性層級)

| 項目 | 範圍 | 工時 |
|---|---|---|
| Advocacy 橙色 `#E89143` → `#EB9B31`(對齊主站)| `_advocacy-deploy/index.html` inline `<style>` 5 處 | 15 分鐘 |
| 抽出 `aabe-tokens.css` 三站共享(色彩 / 字級 / spacing / radius / button / card-radius / schema 慣例)| 新建檔 + 3 站各 link 一行 | 1 天 |
| Logo SVG 化 `logo-aabe.svg` + 保留 `logo-naer.png` 為 redirect / alias | 1 個 SVG + 部署設定 | 2-3 小時 |
| 三站 OG 圖統一 1200×630 規格 | Policy + Advocacy 各做 1 張 | 2 小時 |

---

## 🟢 P2(後續可做)

| 項目 | 備註 |
|---|---|
| 三站 hero grammar 整理(不必同版型,但共用底層 token)| 範圍大,排在最後 |
| Press 三版本(`press/` v1 / `press-v2/` / `press-complete/`)整合 | 跨人決策,影響 sitemap |
| Events 子站化評估(`events.aabe.org.tw`)| 跨人決策,影響 sitemap 與部署 |
| GitHub org rename `naer-tw` → `aabe-tw` | 跨人決策,要評估 301 redirect |

---

## 🚫 我之前在 SITE-STRUCTURE 文件裡看到、但實際不存在的問題

| 原文件聲稱 | 實際 |
|---|---|
| 「Policy 首頁 4 處引用 naer-tw.github.io」 | **0 次**,全站搜不到 |
| 「Advocacy advocacy-summary.md 含 NAER」 | **0 次** |
| 「Advocacy organization.json 含『National Alliance for Education Action』」 | **0 次** |

**結論**:這些都被前面的 session 修過了,但 SITE-STRUCTURE 文件本身沒更新。

---

## 📋 給負責修正的 session 的建議

1. **不要從 SITE-STRUCTURE-2026-05-27.md 出發**,從本檔(SITE-STRUCTURE-AUDIT-2026-05-27.md)出發
2. 動手前**重新 grep 一次自己關注的字串**,確認檔案狀態
3. **按 P0-2 → P0-1 → P0-3 順序**(風險遞增,從機械化到判斷化)
4. P0-2(計數)做完後**立刻 push** — llms.txt 變更會被 AI 引擎優先抓取,越早改越好
5. P0-3 處理「社團法人」時**保留教學對照用法**(`methodology/index.html` 與 `llms.txt` 的「非社團法人」說明)
6. 改完更新 `SITE-STRUCTURE-2026-05-27.md` 為 v2,避免下次 audit 又從過時文件出發

---

**最後更新**:2026-05-27 by Half Second(Phase 6.3 視覺治理 audit 視角)

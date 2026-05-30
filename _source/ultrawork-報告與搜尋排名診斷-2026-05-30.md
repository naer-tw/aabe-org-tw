# ultrawork 全站稽核報告 + 品牌搜尋排名診斷

> 日期：2026-05-30
> 範圍：aabe.org.tw（主站）+ policy / advocacy 子站 + naer-tw.github.io
> 方法：9-agent 並行深度稽核（67 finding，證據化）+ 實際 SERP 搜尋驗證

---

## Part 1 — ultrawork 修復總成績

### 規模
- **9-agent 稽核**：67 原始 finding → 5 P0 + 19 P1 + 19 P2 + 5 假警報剔除
- **修復**：全 P0 + 全 P1 + P2 emoji 批次（87 檔）
- **commits**：跨 4 repo 共 14 個

### P0（5，全清）
| 問題 | 規模 |
|---|---|
| cwa-reform 75 檔 `/policy/cwa-reform/` 雙前綴 → 全 404 | 75 檔 |
| 5/26 兩篇 FAQPage JSON-LD 被 `<span class="sn">` 破壞解析 | 2 檔→4/4 valid |
| 5/26 兩篇 nav 主站路徑在 policy 站 404 + 無樣式 | 2 檔絕對化 |
| og-aabe-1200x630.jpg 不存在 → 75 頁破圖 | 建圖+75 頁 |
| github.io humans.txt 錯英文名 NAER | 修 |

### P1（19，全清）重點
- **「非法非法電子煙」10 處**（我先前 sweep 造成的重複錯字，在 title/meta/schema 高權重欄位）
- 3 站計數器 29→33（HTML 拆標籤的 stat-num/def-num/impact-num，先前純文字 grep 全漏）
- cwa-reform 75 檔：@id 統一 + 捏造別名「全國教育行動聯盟」清除 + 雙 H1 修 + **接入 sitemap（隱形→可發現）**
- 主站死連結 → policy canonical / 研討會機構數 18→16 / naer.org.tw 舊 schema → twedumove / 菸防法第 27 條→15 條 / 4 重複頁 cross-canonical

### P2（emoji 已清，其餘觀察）
- ✅ cwa-reform 73 檔 + events 14 檔 emoji/圈號清除
- ⏭️ 剩：meta description >160 字（32 頁）、缺 twitter card（部分）、press 三版本整併、advocacy 統計灌水

### 假警報剔除（9-agent 自動過濾，避免報告誤導）
1. 「人民團體」立案事實陳述（非自稱違規）
2. 英國語境「電子煙合法」（描述他國，非台灣主張）
3. 第三方拒菸聯盟存檔「第 29 條」（不可竄改歷史存檔）
4. naer-tw GitHub slug（固定路徑識別碼）
5. 主站 10 核心頁單 H1（deep-research 報告誤報的「多 H1」實不存在）

---

## Part 2 — 品牌搜尋排名診斷（核心）

### 實測 SERP（2026-05-30）

**搜「國教盟」前 10**：
1. Facebook 官方（twedumove）2. Wikipedia 3. YouTube（@國教盟）4. 中央社 CNA 5. Linktree（aabe0626）6. CRC 政府網 7. 全國家長會長聯盟 8. 原視新聞 9. 大紀元 10. Yahoo 新聞
→ **aabe.org.tw 未進前 10**

**搜「國教行動聯盟」前 10**：
1. Wikipedia 2. Facebook 官方 3. CNA 4. YouTube 5. TNL 關鍵評論網 6. 自由時報 7. CRC 8. YouTube channel 9. 聯合報 UDN 10. Facebook 青年部
→ **aabe.org.tw 未進前 10**

### 關鍵洞察：問題不是「沒被看見」，是「沒被認出是官方總部」

SERP 前 10 **全是國教盟自己的資產**（Facebook、YouTube、Linktree）+ Wikipedia + 新聞。
官方網站 aabe.org.tw 是唯一缺席的「自己人」。

### 是標題問題嗎？——部分是，但不是主因

| 因素 | 診斷 | 權重 |
|---|---|---|
| **新網域**（2026-05-14 上線，~2 週）| Google 對新站信任度需 3-6 個月累積 | 🔴 主因 |
| **零權威 backlinks** | Facebook/YouTube/Linktree 排前是因坐落高權重平台；aabe.org.tw 幾乎無外部連入 | 🔴 主因 |
| **品牌實體未串連** | 首頁 Schema sameAs 原只列 2 個（FB+Wiki），漏 YouTube/Linktree → Google 無法把分散帳號認成同一實體叢集 | 🟠 次因（已修）|
| **標題缺「國教盟」縮寫** | 原 title 只有全名「國教行動聯盟」，無 3 字縮寫「國教盟」（多數人搜這個）| 🟡 小因（已修）|
| 標題已含全名 | title 已有「國教行動聯盟」✓ — 非缺關鍵字問題 | — |

**結論**：標題本身沒寫錯（已含全名），但 (a) 漏縮寫 (b) Schema 實體串連不全 是可修的；真正的天花板是**網域年齡 + backlinks + 品牌整併**。

---

## Part 3 — 行動清單

### A. 已做（本次，技術端我能改的）
- ✅ 首頁 title 加「國教盟」+「官方網站」：`國教行動聯盟（國教盟）官方網站｜為孩子的教育權發聲`
- ✅ og:title / twitter:title 同步
- ✅ meta description 加「簡稱國教盟」+「本站為國教盟唯一官方網站」
- ✅ NGO Schema sameAs：2 個 → 5 個（補 YouTube @國教盟 + Linktree + 青年部 FB）

### B. 你必須做（我無權限，但影響最大）★最高 ROI
| 動作 | 為何關鍵 | 難度 |
|---|---|---|
| **各社群「網站」欄位 → aabe.org.tw** | Facebook 關於頁、YouTube 頻道連結、Linktree 第一順位、IG bio 全指官網 → 把已排名的自家資產的權重導回官網 | 低（5 分鐘）|
| **Wikipedia 外部連結 → aabe.org.tw** | Wikipedia 排第 1-2，外連是最強權威 backlink（待 vfd 存活後，由中立編者加）| 中 |
| **Google Business Profile 建立** | 觸發 Knowledge Panel + sitelinks，品牌詞直接霸版 | 中 |
| **記者/夥伴 hyperlink 官網** | 新聞稿被引用時請加官網超連結（非純文字提及）| 中 |

### C. 時間 + 持續性（已在做）
- 持續發 GEO 專頁（已到第 33 篇）→ Google 看見「活躍站」
- 每篇新內容提交 GSC + IndexNow

### 預期時程
| 通路 | aabe.org.tw 進品牌詞前 10 |
|---|---|
| 若只靠技術修 + 時間 | 2-3 個月 |
| 若 + 社群網站欄位導回（B 第 1 項）| 加速到 4-6 週 |
| 若 + Wikipedia 外連 + GBP | 可望 1-2 個月內前 5 |

---

## 核心一句話

> **aabe.org.tw 不是「Google 看不到」，是「Google 還沒把它認成國教盟的官方家」。**
> 技術端（標題、Schema sameAs）我已補強；真正的勝負手是**把已經排在前面的自家社群帳號，網站欄位全部導回 aabe.org.tw** —— 這是你 5 分鐘能做、但影響最大的一步。

---

**最後更新**：2026-05-30

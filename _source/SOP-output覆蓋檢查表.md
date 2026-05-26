# SOP：把 output/ 整批覆蓋主站時的必跑檢查

> 適用情境：用戶提供一個 output/ 資料夾，要求把裡面 HTML 整批覆蓋主站對應路徑（最近一次：2026-05-22 commit `8d2eb93`）
> 為什麼有這份 SOP：那次覆蓋把 5/22 commit `cceba64` 修好的「活動照片 → moments/」路徑映射打回原形，導致 8 張照片＋影片全 404。下次必須擋下。

---

## 🔥 第一原則：output/ 是「素材」，不是「最終版」

output/ 的 HTML 通常由設計師／生成器產出，不會自動套用主站的：
- 內部路徑改名（中文 → 英文）
- 媒體檔重命名（原檔名 → SEO friendly）
- 跨檔事實校正（5/22 三盟 / 8 位學者 / 圓滿落幕等）
- SEO meta 升級（OG / Twitter Card / Schema.org）

**因此：output 覆蓋 ≠ 部署完成，後面還有 4 個必跑檢查。**

---

## ✅ 4 步必跑檢查（events/2026-05-20-drug-abuse-conference/ 特化版）

### Step 1：路徑映射（cross-folder rename）
```bash
# notes/index.html 路徑映射
grep -nE "活動照片|moments/" public/events/2026-05-20-drug-abuse-conference/notes/index.html
```
若發現 `../活動照片/` → 全部改為 `../moments/`，並映射檔名：

| 舊（中文檔名） | 新（英文檔名）|
|---|---|
| 楊士隆獲得終身成就獎.mp4 | lifetime-achievement-award.mp4 |
| 研討會好友會場合照.jpg | group-photo-friends.jpg |
| 左到右王瀚陽張安慈陳尚仁曾品傑教授張文昌唐仙美.jpg | group-photo-experts.jpg |
| 第一天晚宴.jpg | day1-dinner.jpg |
| S__1271235*_0.jpg | （同名，只改資料夾）|

**並記得補回 video 的 `<track>` 字幕標籤**：
```html
<track kind="subtitles" srclang="zh-Hant" label="繁體中文"
       src="../moments/lifetime-achievement-award.zh-Hant.vtt" default>
```

### Step 2：媒體檔存在性驗證
```bash
cd aabe-deploy
for f in S__127123559_0.jpg S__127123565_0.jpg S__127123561_0.jpg \
         S__127123566_0.jpg group-photo-friends.jpg \
         group-photo-experts.jpg day1-dinner.jpg \
         lifetime-achievement-award.mp4 lifetime-achievement-award.zh-Hant.vtt; do
  test -f "public/events/2026-05-20-drug-abuse-conference/moments/$f" \
    && echo "✓ $f" || echo "✗ MISSING: $f"
done
```

### Step 3：跨檔事實校正（5/22 校正必須重套）
| 項目 | 對／錯 |
|---|---|
| 三盟 | 國教盟 + 共善促進協會 + **中華民國兒童健康聯盟**（NOT 台灣藥物濫用防治學會、NOT 兒少健盟）|
| 國際學者人數 | **8 位**（US 5 + HK 2 + TH 1），NOT 5 位 |
| 國際講者國別 | **美、港、泰 3 國**，NOT「美澳泰港」、NOT「跨越十餘國」|
| 楊士隆場次 | Day 1 第 3 場（少年涉毒）+ **Day 1 第 5 場（與陳為堅，流行病學）**，NOT Day 2 第 2 場 |
| 研討會狀態 | **「圓滿落幕」**，NOT「即將舉辦」 |

跑 cross-file grep 確認：
```bash
grep -rn "兒少健盟\|台灣藥物濫用防治學會\|美、澳、泰、港\|十餘國\|5 位國際\|五位國際" \
  public/events/2026-05-20-drug-abuse-conference/ public/press/
```
回傳必須空。

### Step 3.5：**Emoji 違規 grep（強制紀律 — 違反 user memory feedback_visual_svg_over_emoji.md）**

> 教訓：5/26 三部曲首次部署用了 104 個 emoji（① 📚 ❓ 等），違反「對外 HTML 不用 emoji,改 inline SVG」明文紀律。第二次部署才修齊。

每次 output 整批覆蓋後必跑：
```bash
python3 -c "
import re, sys, glob
pattern = re.compile(r'[\U0001F300-\U0001FFFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001FA00-\U0001FAFF]|[①②③④⑤⑥⑦⑧⑨❓📚📅📋📂🔗📞📢●★●○◆■]')
for f in glob.glob(sys.argv[1] + '/**/*.html', recursive=True):
    html = open(f).read()
    emo = pattern.findall(html)
    if emo:
        from collections import Counter
        c = Counter(emo)
        print(f'⚠ {f}: {sum(c.values())} emoji ({len(c)} 種) — {dict(c.most_common(5))}')
" public/press/2026-05-26-vape-device-research
```
若有任何 emoji 殘留 → 替換 SOP：
- ①-⑨ → `<span class="sn">N</span>`（CSS 圓徽）
- 📚 → BookOpen inline SVG（Heroicons style）
- 📅 → Calendar SVG
- 📋 → Clipboard SVG
- 📂 → Folder SVG
- ❓ → QuestionMarkCircle SVG
- 🔗 → Link SVG
- 📞 → Phone SVG
- 📢 → Megaphone SVG
- ● → 移除或 CSS `list-style-type:disc`

CSS 必補進 `<style>`：
```css
.sn{display:inline-flex;width:1.5em;height:1.5em;border-radius:50%;background:#1a3a52;color:#fff;font-size:.65em;font-weight:700;align-items:center;justify-content:center;margin-right:.45em;vertical-align:2px}
.ic{display:inline-block;width:1em;height:1em;vertical-align:-0.125em;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;margin-right:.35em}
```

### Step 3.6：**設計統一化檢查（5/26 教訓）**

每個 output HTML 必須引入主站 design：
```bash
grep -l 'aabe\.css' public/press/2026-05-26-*/index.html | wc -l
# 必須等於該批檔案數
```

若無 → 在 `<head>` 加：
```html
<link rel="stylesheet" href="/assets/aabe.css">
```

並在 `<body>` 頂端加主站統一 topbar（從 `public/index.html` 複製 `<header class="topbar">` 區塊）。

### Step 4：SEO meta 不重複
```bash
# 若 output/ 已含 SEO meta block，主站再加一層會重複
grep -c '<meta property="og:image"' public/events/2026-05-20-drug-abuse-conference/notes/index.html
```
應該 **= 1**。若 = 2 或更多，用 sed 移除整段 `<!-- SEO & Open Graph -->` 到 `<meta name="twitter:image">`。

OG 圖片必須是 **絕對 URL**（output 預設可能是相對路徑）：
```
content="https://aabe.org.tw/wp-content/uploads/og-2026-conference.png"  ✓
content="og_image.png"                                                   ✗
```

---

## 🚀 部署後 production 驗證

```bash
# 1. notes 頁回應碼 + 媒體計數
curl -s -o /tmp/p.html -w "%{http_code} %{size_download}\n" \
  https://aabe.org.tw/events/2026-05-20-drug-abuse-conference/notes/
grep -c -E "(\\.jpg|\\.mp4|<img|<video)" /tmp/p.html
# 預期：200 47000+ bytes，媒體計數 ≥ 18

# 2. 抽 1 張照片實際載入
curl -sI https://aabe.org.tw/events/2026-05-20-drug-abuse-conference/moments/day1-dinner.jpg | head -1
# 預期：HTTP/2 200

# 3. 影片實際載入
curl -sI https://aabe.org.tw/events/2026-05-20-drug-abuse-conference/moments/lifetime-achievement-award.mp4 | head -1
# 預期：HTTP/2 200
```

任何一步出錯 → 不可回報「已部署」，必須先修。
（記憶位置：`feedback_fact_check_discipline.md` SOURCE → TEXT → GREP → **PRODUCTION CURL**）

---

## 📅 歷史教訓

| 日期 | commit | 教訓 |
|---|---|---|
| 2026-05-22 | `cceba64` | 第一次修活動花絮（中→英路徑＋字幕）|
| 2026-05-22 | `8d2eb93` | output → 主站全量更新（A 選項）— **打回 cceba64** |
| 2026-05-23 | （本次）| 用戶發現「照片影片又不見了」→ 寫這份 SOP 永久存證 |

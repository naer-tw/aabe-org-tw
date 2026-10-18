#!/usr/bin/env python3
"""build_policy_search_staging.py — 官網第四輪：把政策站 47 篇文章複製到暫存目錄，
加上 Pagefind 索引屬性，供 build_search_index.sh 另外建一份 public/pagefind-policy/ 索引。

範圍：複製 _policy-deploy 底下已對照 topic 的議題分類目錄「第一層」的 *.html
（排除各分類自己的 index.html），**以及這些分類底下的巢狀專題頁**
（2026-10-18 補：teacher-affairs/school-affairs-meeting-position/index.html 這類
「一個專題一個資料夾」的頁，原先因只收第一層而完全不在索引，站內搜尋
「校事會議改了」找不到對應專題；巢狀專題頁的 topic 沿用所屬分類）。
未對照 topic 的分類（如頂層 cwa-reform/ 的 74 頁知識庫條文、國際對標
卡）仍刻意不收——那是資料庫式頁面，收進來會稀釋政策分析的搜尋結果。
（實測：對 h1 加 data-pagefind-weight=10 對分數幾乎無影響〔3.805→3.752〕，
所以不加；題名優先改在前端 press/all 的合併排序處理。）

議題分類（topic）取法：category → topic 的預設對照表（與既有
sync-policy-articles.py 的 TOPIC_MAPPING、及 press/all/index.html 現有
19 張政策頁的 data-topic 標記一致），不是逐篇重新讀 JSON-LD about[] 手動比對
——這是刻意的範圍縮小（47 篇 vs 官網第三批②只手動比對 23 篇），已記錄在
改動摘要「取捨掉」欄。

用法：
  python3 build_policy_search_staging.py <policy_deploy_dir> <staging_dir>
"""
import json
import re
import sys
from pathlib import Path

CATEGORY_TOPIC = {
    "campus-safety": "校園安全",
    "child-rights": "兒少保護",
    "child-health": "兒少保護",
    "education-reform": "教育政策與改革",
    "school-lunch": "教育政策與改革",
    "teacher-affairs": "教師與校務",
    "health": "青少年身心健康",
    "youth-health": "青少年身心健康",
    # cwa-reform: 目前分類目錄第一層沒有文章（0 篇，2026-09-16 現況），不列預設值。
}

# 巢狀專題頁的排除清單（相對 policy_dir 的資料夾前綴）。
# child-rights/cwa-reform/：兒少權法修法專題子頁（4 頁），與頂層 cwa-reform/ 資料庫同性質；
# 2026-10-18 實測納入後「營養午餐」查詢的政策站整詞結果由 <20 變滿，既有的
# test_search_cjk_bigram_fallback_recovers_press_pages 從綠翻紅（毒油新聞稿被擠出
# top 20），且與本次「校事會議」目標無關——另案評估，不在本輪範圍。
NESTED_EXCLUDE = ("child-rights/cwa-reform/",)

DATE_RE_FROM_JSONLD = re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})')
DATE_RE_FROM_FILENAME = re.compile(r'(\d{4})[-]?(\d{2})[-]?(\d{2})')


def extract_date(html: str, filename: str) -> str:
    m = DATE_RE_FROM_JSONLD.search(html)
    if m:
        return m.group(1)
    m = DATE_RE_FROM_FILENAME.search(filename)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return "0000-00-00"


def tag_html(html: str, topic: str, date: str) -> str:
    """在 <body ...> 後插入 pagefind 屬性 span；<body> 本身補上 data-pagefind-body。"""
    marker = (
        f'<span data-pagefind-filter="type:政策分析" hidden></span>'
        f'<span data-pagefind-filter="topic:{topic}" hidden></span>'
        f'<span data-pagefind-meta="date:{date}" hidden></span>'
    )

    def repl(m):
        tag = m.group(0)
        if "data-pagefind-body" in tag:
            new_tag = tag
        else:
            new_tag = tag[:-1] + ' data-pagefind-body>'
        return new_tag + marker

    new_html, n = re.subn(r"<body\b[^>]*>", repl, html, count=1)
    if n == 0:
        raise ValueError("找不到 <body> 標籤")
    return new_html


def main():
    if len(sys.argv) != 3:
        print("用法：build_policy_search_staging.py <policy_deploy_dir> <staging_dir>", file=sys.stderr)
        sys.exit(2)
    policy_dir = Path(sys.argv[1]).resolve()
    staging_dir = Path(sys.argv[2]).resolve()

    if not policy_dir.is_dir():
        print(f"[build_policy_search_staging] 找不到政策站目錄：{policy_dir}", file=sys.stderr)
        sys.exit(1)

    if staging_dir.exists():
        import shutil
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    count = 0
    skipped = []
    manifest = []
    for cat_dir in sorted(policy_dir.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith('.'):
            continue
        topic = CATEGORY_TOPIC.get(cat_dir.name)
        # 第一層 *.html（排除分類自己的 index.html）＋巢狀專題頁（任何深度）。
        candidates = []
        for f in sorted(cat_dir.rglob("*.html")):
            rel = f.relative_to(cat_dir)
            if rel.parts == ("index.html",):
                continue
            if any(f.relative_to(policy_dir).as_posix().startswith(x) for x in NESTED_EXCLUDE):
                continue
            candidates.append((f, rel))
        for f, rel in candidates:
            if topic is None:
                skipped.append(str(f.relative_to(policy_dir)))
                continue
            html = f.read_text(encoding="utf-8")
            date = extract_date(html, f.name)
            try:
                tagged = tag_html(html, topic, date)
            except ValueError as e:
                skipped.append(f"{f.relative_to(policy_dir)}（{e}）")
                continue
            out_path = staging_dir / cat_dir.name / rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(tagged, encoding="utf-8")
            # index.html 的對外網址是目錄（結尾 /），其餘維持檔名。
            if rel.name == "index.html":
                url_path = "/".join(rel.parts[:-1]) + "/"
            else:
                url_path = "/".join(rel.parts)
            manifest.append({
                "category": cat_dir.name,
                "filename": rel.as_posix(),
                "topic": topic,
                "date": date,
                "url": f"https://policy.aabe.org.tw/{cat_dir.name}/{url_path}",
            })
            count += 1

    (staging_dir / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[build_policy_search_staging] 已標記 {count} 篇政策文章 → {staging_dir}")
    if skipped:
        print(f"[build_policy_search_staging] 跳過 {len(skipped)} 篇（無對應 topic 或找不到 <body>）：", file=sys.stderr)
        for s in skipped:
            print(f"  - {s}", file=sys.stderr)


if __name__ == "__main__":
    main()

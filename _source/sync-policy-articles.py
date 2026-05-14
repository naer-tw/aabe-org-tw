#!/usr/bin/env python3
"""
同步 policy.aabe.org.tw 文章資料到主站 aabe.org.tw

每次政策站有新文章時跑這個腳本：
  cd aabe-deploy
  python3 _source/sync-policy-articles.py

會做：
1. 從 GitHub 抓 naer-tw/policy 所有文章
2. 解析每篇 title + description + date
3. 更新主站 public/index.html「最新倡議 6 篇」
4. 更新主站 public/issues/index.html「每分類最新 3 篇」
5. 更新「N 篇政策深度分析」數字
6. 顯示變更摘要、提示是否 commit

需要：gh CLI 已登入有 naer-tw 權限
"""

import subprocess, json, re, base64, sys, os
from html import unescape
from pathlib import Path

CATEGORIES = ['campus-safety', 'child-health', 'child-rights', 'cwa-reform',
              'education-reform', 'health', 'school-lunch', 'teacher-affairs', 'youth-health']

ROOT = Path(__file__).parent.parent
PUBLIC = ROOT / 'public'
INDEX_HTML = PUBLIC / 'index.html'
ISSUES_HTML = PUBLIC / 'issues' / 'index.html'

# 議題卡 → 對應的 category（可能合併多個）
TOPIC_MAPPING = {
    'campus-safety': ['campus-safety'],
    'child-rights': ['child-rights', 'child-health'],
    'youth-health': ['youth-health', 'health'],
    'education-reform': ['education-reform', 'school-lunch'],
    'teacher-affairs': ['teacher-affairs'],
    'digital-safety': []  # 沒對應分類（用單篇文章）
}


def clean_title(t):
    """清理文章標題的後綴"""
    t = re.sub(r'\s*[—－－]+\s*國教行動聯盟政策分析\s*$', '', t)
    t = re.sub(r'\s*[—－－]+\s*全國婦兒團體聯盟政策分析\s*$', '', t)
    t = re.sub(r'\s*\|\s*國教行動聯盟[^|]*$', '', t)
    t = re.sub(r'\s*\|\s*國教行動聯盟政策知識庫\s*$', '', t)
    return t.strip()


def fetch_all_articles():
    """從 GitHub 抓 policy repo 所有文章"""
    articles = []
    for cat in CATEGORIES:
        try:
            r = subprocess.run(['gh', 'api', f'repos/naer-tw/policy/contents/{cat}'],
                               capture_output=True, text=True, timeout=20)
            items = json.loads(r.stdout)
            for x in items:
                if x.get('name','').endswith('.html') and x['name'] != 'index.html':
                    m = re.match(r'(\d{4})[-]?(\d{2})[-]?(\d{2})[-_]?(.+)\.html', x['name'])
                    date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else '????-??-??'
                    articles.append({
                        'category': cat,
                        'filename': x['name'],
                        'date': date,
                        'url': f"https://policy.aabe.org.tw/{cat}/{x['name']}"
                    })
        except Exception as e:
            print(f"  ⚠️ {cat}: {e}", file=sys.stderr)
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles


def enrich_with_titles(articles):
    """用 GitHub API 拉每篇 title + description"""
    for i, a in enumerate(articles, 1):
        try:
            r = subprocess.run(['gh', 'api',
                                f"repos/naer-tw/policy/contents/{a['category']}/{a['filename']}"],
                               capture_output=True, text=True, timeout=30)
            data = json.loads(r.stdout)
            html = base64.b64decode(data['content']).decode('utf-8')
            m = re.search(r'<title>([^<]+)</title>', html)
            a['title'] = clean_title(unescape(m.group(1))) if m else a['filename']
            m2 = re.search(r'<meta[^>]+property="og:description"\s+content="([^"]+)"', html)
            if not m2:
                m2 = re.search(r'<meta[^>]+name="description"\s+content="([^"]+)"', html)
            desc = unescape(m2.group(1)) if m2 else ''
            a['description'] = desc[:78] + '…' if len(desc) > 80 else desc
            print(f"  [{a['date']}] {a['title'][:40]}")
        except Exception as e:
            print(f"  ⚠️ {a['filename']}: {e}", file=sys.stderr)
            a['title'] = a['filename']
            a['description'] = ''
    return articles


def gen_homepage_cards(articles):
    """產生首頁最新 6 篇 HTML"""
    cards = []
    for a in articles[:6]:
        date = a['date'].replace('-', '.')
        cards.append(f'''        <article class="article-card">
          <div class="date">{date}</div>
          <h3><a href="{a['url']}">{a['title']}</a></h3>
          <p>{a['description']}</p>
        </article>''')
    return '\n'.join(cards)


def gen_topic_recent_list(articles, cats, limit=3):
    """產生某議題的最新 N 篇 li 清單"""
    matched = [a for a in articles if a['category'] in cats][:limit]
    if not matched:
        return ''
    lis = []
    for a in matched:
        date = a['date'].replace('-', '.')
        lis.append(f'            <li><a href="{a["url"]}"><span class="recent-date">{date}</span>{a["title"]}</a></li>')
    return '\n'.join(lis)


def update_homepage(articles):
    """更新首頁的最新 6 篇文章"""
    html = INDEX_HTML.read_text(encoding='utf-8')
    new_cards = gen_homepage_cards(articles)
    pattern = re.compile(
        r'(<div class="article-grid">\n)(.*?)(\n      </div>)',
        re.DOTALL
    )
    new_html, count = pattern.subn(rf'\1{new_cards}\3', html)
    if count == 0:
        print("  ⚠️ 找不到 .article-grid 區塊")
        return False
    INDEX_HTML.write_text(new_html, encoding='utf-8')
    print(f"  ✅ 首頁更新（最新 6 篇）")
    return True


def update_article_count(articles):
    """更新「N 篇政策深度分析」數字"""
    n = len(articles)
    files = [INDEX_HTML, ISSUES_HTML,
             PUBLIC / 'about' / 'index.html',
             PUBLIC / 'contact' / 'index.html',
             PUBLIC / 'llms.txt',
             PUBLIC / 'humans.txt']
    changed = 0
    for f in files:
        if not f.exists(): continue
        content = f.read_text(encoding='utf-8')
        new = re.sub(r'\d+ 篇政策深度分析', f'{n} 篇政策深度分析', content)
        new = re.sub(r'\d+ 篇深度分析', f'{n} 篇深度分析', new)
        new = re.sub(r'\d+ 篇政策論述', f'{n} 篇政策論述', new)
        new = re.sub(r'（\d+ 篇）', f'（{n} 篇）', new)
        if new != content:
            f.write_text(new, encoding='utf-8')
            changed += 1
    print(f"  ✅ 文章數更新為 {n}（{changed} 個檔案）")


def main():
    print("═══ 同步 policy.aabe.org.tw 到 aabe.org.tw ═══\n")
    print("Step 1: 抓所有文章 metadata...")
    articles = fetch_all_articles()
    print(f"  找到 {len(articles)} 篇\n")

    print("Step 2: 用 GitHub API 拉真實標題...")
    enrich_with_titles(articles)
    print()

    print("Step 3: 更新主站...")
    update_homepage(articles)
    update_article_count(articles)
    print()

    print("✅ 同步完成。建議：")
    print(f"   git diff   # 看改了什麼")
    print(f"   git add public/ && git commit -m 'Sync {len(articles)} policy articles'")
    print(f"   git push   # Cloudflare 30 秒後自動部署\n")

    # 順便存最新 metadata 到 _source
    meta_file = ROOT / '_source' / 'articles-meta.json'
    with meta_file.open('w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"   articles metadata 已存 {meta_file.relative_to(ROOT)}")


if __name__ == '__main__':
    main()

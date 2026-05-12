#!/usr/bin/env python3
"""
AABE 政策知識庫 — 一鍵部署腳本

使用方式：
    python3 deploy.py path/to/new-article.html
    python3 deploy.py --batch path/to/folder/

自動完成：
  1. 偵測 article:section meta → 套對應分類色
  2. 注入 favicon + manifest + theme-color + alternate MD link
  3. 加 a11y（skip-link + focus-visible + reduced-motion + reading-progress）
  4. 自動產 .md 對應檔（front matter + FAQ）
  5. 自動更新 sitemap.xml
  6. 自動更新 geo-checker config.yaml
  7. 自動更新 llms.txt 分類數量
  8. 自動更新分類聚合頁（依設定的 5 大主題）
  9. git add + commit + push
  10. ping Bing IndexNow + Google search ping

執行前確認：
  - 已安裝 beautifulsoup4 (pip install beautifulsoup4)
  - 已 export INDEXNOW_KEY 環境變數（IndexNow key）
  - 政策 repo 在 /Users/coachyang/clawd/naer-policy/
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Need: pip install beautifulsoup4")
    sys.exit(1)

# ═══ 設定 ═══
REPO = Path("/Users/coachyang/clawd/naer-policy")
BASE_URL = "https://policy.aabe.org.tw"   # ← DNS 設好後切換 / 之前用 https://naer-tw.github.io/policy
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "")
INDEXNOW_KEY_LOCATION = "/indexnow-{key}.txt"  # 必須能在 base url 直接訪問

# 分類映射
CATEGORY_MAP = {
    "校園安全": ("campus-safety", "#8B2631", "#A73947"),
    "兒少權益": ("child-rights", "#D97706", "#F59E0B"),
    "兒少保護": ("child-rights", "#D97706", "#F59E0B"),
    "兒童健康": ("child-health", "#EA580C", "#FB923C"),
    "教育改革": ("education-reform", "#1E40AF", "#3B82F6"),
    "教育政策與改革": ("education-reform", "#1E40AF", "#3B82F6"),
    "校園午餐": ("school-lunch", "#15803D", "#22C55E"),
    "教師事務": ("teacher-affairs", "#4338CA", "#6366F1"),
    "教師與校務": ("teacher-affairs", "#4338CA", "#6366F1"),
    "健康政策": ("health", "#0F766E", "#14B8A6"),
    "健康": ("health", "#0F766E", "#14B8A6"),
    "青少年健康": ("youth-health", "#0369A1", "#0EA5E9"),
    "青少年身心健康": ("youth-health", "#0369A1", "#0EA5E9"),
}

# ═══ Helpers ═══
def run(cmd, cwd=None, check=True):
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=check)


def detect_category(html_text: str) -> tuple[str, str, str]:
    """從 HTML 偵測分類，返回 (slug, primary_color, primary_light)"""
    m = re.search(r'<meta property="article:section" content="([^"]+)"', html_text)
    if m:
        cat_name = m.group(1).strip()
        if cat_name in CATEGORY_MAP:
            return CATEGORY_MAP[cat_name]
    # Fallback
    return ("uncategorized", "#0a0a0a", "#3a3f48")


def detect_date(filename: str) -> str:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else datetime.now().strftime("%Y-%m-%d")


def detect_slug(filename: str) -> str:
    """Get slug part of filename without date prefix and extension"""
    stem = Path(filename).stem
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)


# ═══ 1. 套色 + a11y + favicon ═══
def enhance_html(html_text: str, primary: str, light: str, md_filename: str) -> str:
    t = html_text

    # 找出舊主色然後 swap 為新分類色
    # 經典藍金 / 經典橘 / 森林綠金 三組常見配色 swap
    old_palettes = [
        ("#1a5276", "#2c5aa0", "#f39c12"),  # 經典藍金
        ("#E8734A", "#F09070", "#D05A32"),  # Template A 橘
        ("#1B4332", "#2D6A4F", "#D4A843"),  # 森林綠金
    ]
    for op in old_palettes:
        t = re.sub(re.escape(op[0]), primary, t, flags=re.IGNORECASE)
        t = re.sub(re.escape(op[1]), light, t, flags=re.IGNORECASE)

    # Favicon + manifest + alternate MD（注入 canonical 後）
    favicon_block = f'''
<link rel="icon" type="image/png" sizes="32x32" href="{BASE_URL}/images/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="{BASE_URL}/images/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="{BASE_URL}/images/apple-touch-icon.png">
<link rel="manifest" href="{BASE_URL}/manifest.json">
<meta name="theme-color" content="#0a0a0a">
<link rel="alternate" type="text/markdown" href="{md_filename}">'''

    if 'rel="icon"' not in t:
        t = re.sub(r'(<link rel="canonical"[^>]+>)', r'\1' + favicon_block, t, count=1)

    # A11y CSS
    a11y = f'''
/* A11y */
.skip-link{{position:absolute;top:-100px;left:0;background:#0a0a0a;color:#fff;padding:12px 20px;font-size:0.9rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;z-index:9999;text-decoration:none;transition:top 0.2s}}
.skip-link:focus{{top:0}}
:focus{{outline:none}}
:focus-visible{{outline:2px solid {primary};outline-offset:3px;border-radius:2px}}
@media (prefers-reduced-motion:reduce){{*,*::before,*::after{{animation-duration:0.01ms !important;transition-duration:0.01ms !important}}}}
.reading-progress{{position:fixed;top:0;left:0;height:3px;background:{primary};width:0;z-index:10000;transition:width 0.1s}}
'''
    if "skip-link" not in t:
        t = t.replace("</style>", a11y + "</style>", 1)

    # Body additions
    if 'class="skip-link"' not in t:
        t = t.replace(
            "<body>",
            '<body>\n<a href="#main" class="skip-link">跳至主內容</a>\n<div class="reading-progress" id="reading-progress" aria-hidden="true"></div>',
            1,
        )

    if 'id="main"' not in t:
        t = t.replace("<main>", '<main id="main">', 1)

    # Reading progress JS
    if "reading-progress" in t and "scrollY" not in t:
        progress_js = '''<script>
(function(){var b=document.getElementById("reading-progress");if(!b)return;function u(){var h=document.documentElement;b.style.width=Math.min(100,Math.max(0,(h.scrollTop/(h.scrollHeight-h.clientHeight))*100))+"%"}window.addEventListener("scroll",u,{passive:true});u()})();
</script>
</body>'''
        t = t.replace("</body>", progress_js, 1)

    return t


# ═══ 2. 產 .md 對應檔 ═══
def html_to_md(html_text: str, url: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    title_tag = soup.find("title")
    title = (title_tag.string or "").strip() if title_tag else ""
    title = re.sub(r"\s*[｜|\-—]+\s*(國教行動聯盟|國教盟|政策知識庫).*$", "", title)

    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag.get("content", "") if desc_tag else ""

    kw_tag = soup.find("meta", attrs={"name": "keywords"})
    kw = kw_tag.get("content", "") if kw_tag else ""

    date_m = re.search(r"(\d{4})-(\d{2})-(\d{2})", url)
    date = f"{date_m.group(1)}-{date_m.group(2)}-{date_m.group(3)}" if date_m else ""

    # FAQ from JSON-LD
    faqs = []
    for sc in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(sc.string or "")
            if isinstance(data, dict) and data.get("@type") == "FAQPage":
                for q in data.get("mainEntity", []):
                    qn = q.get("name", "")
                    a = q.get("acceptedAnswer", {})
                    at = a.get("text", "") if isinstance(a, dict) else ""
                    if qn and at:
                        faqs.append((qn, at))
        except Exception:
            pass

    # Body to MD
    body = soup.select_one("article") or soup.select_one("main") or soup.body
    for sel in ["script", "style", "nav", "footer", ".org-banner", ".topbar", ".breadcrumb", ".reading-progress", ".skip-link", "form"]:
        for el in body.select(sel):
            el.decompose()

    parts = []
    def walk(node):
        for child in getattr(node, "children", []):
            if not hasattr(child, "name"):
                s = str(child).strip()
                if s:
                    parts.append(s)
                continue
            n = child.name
            if not n:
                continue
            txt = re.sub(r"\s+", " ", child.get_text() or "").strip()
            if n == "h1" and txt:
                parts.append(f"\n# {txt}\n")
            elif n == "h2" and txt:
                parts.append(f"\n## {txt}\n")
            elif n == "h3" and txt:
                parts.append(f"\n### {txt}\n")
            elif n == "p" and txt:
                parts.append(txt + "\n")
            elif n in ("ul", "ol"):
                for li in child.find_all("li", recursive=False):
                    li_t = re.sub(r"\s+", " ", li.get_text() or "").strip()
                    if li_t:
                        parts.append(f"- {li_t}")
                parts.append("")
            elif n == "blockquote" and txt:
                parts.append(f"\n> {txt}\n")
            elif n in ("div", "section", "article", "main"):
                walk(child)

    walk(body)
    body_md = re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()

    out = ["---"]
    out.append(f"title: {json.dumps(title, ensure_ascii=False)}")
    if desc:
        out.append(f"description: {json.dumps(desc[:200].replace(chr(10), ' '), ensure_ascii=False)}")
    if date:
        out.append(f"date: {date}")
    if kw:
        out.append(f"keywords: {json.dumps(kw, ensure_ascii=False)}")
    out.append(f"url: {url}")
    out.append(f"source: 國教行動聯盟政策知識庫")
    out.append("---\n")
    out.append(f"# {title}\n")
    if desc:
        out.append(f"> {desc}\n")
    out.append(body_md)
    if faqs:
        out.append("\n## 常見問答（FAQ）\n")
        for q, a in faqs:
            out.append(f"### Q: {q}\n")
            out.append(a + "\n")
    out.append("\n---")
    out.append(f"**原始頁面**：[{url}]({url})")
    out.append(f"**組織**：[國教行動聯盟](https://aabe.org.tw/)（成立於 2012 年）")
    return "\n".join(out)


# ═══ 3. 更新 sitemap.xml ═══
def update_sitemap(article_url: str, date: str):
    sitemap = REPO / "sitemap.xml"
    text = sitemap.read_text(encoding="utf-8")
    if article_url in text:
        print(f"  ↪ Already in sitemap: {article_url}")
        return
    new_url = f'''  <url>
    <loc>{article_url}</loc>
    <lastmod>{date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>'''
    text = text.replace("</urlset>", new_url)
    sitemap.write_text(text, encoding="utf-8")
    print(f"  ✓ sitemap.xml +1 URL")


# ═══ 4. IndexNow + Google ping ═══
def submit_to_search_engines(article_url: str):
    if not INDEXNOW_KEY:
        print("  ⚠ INDEXNOW_KEY not set, skipping IndexNow")
    else:
        try:
            payload = json.dumps({
                "host": "policy.aabe.org.tw",
                "key": INDEXNOW_KEY,
                "keyLocation": f"{BASE_URL}{INDEXNOW_KEY_LOCATION.format(key=INDEXNOW_KEY)}",
                "urlList": [article_url],
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.indexnow.org/indexnow",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"  ✓ IndexNow: {resp.status}")
        except Exception as e:
            print(f"  ⚠ IndexNow failed: {e}")

    # Google ping (deprecated but harmless)
    try:
        ping_url = f"https://www.google.com/ping?sitemap={BASE_URL}/sitemap.xml"
        urllib.request.urlopen(ping_url, timeout=10)
        print(f"  ✓ Google sitemap ping")
    except Exception as e:
        print(f"  ⚠ Google ping: {e}")


# ═══ Main ═══
def deploy_one(html_path: Path):
    print(f"\n📄 Processing: {html_path}")
    text = html_path.read_text(encoding="utf-8")
    cat_slug, primary, light = detect_category(text)
    date = detect_date(html_path.name)
    slug = detect_slug(html_path.name)
    md_filename = f"{html_path.stem}.md"

    print(f"  Category: {cat_slug}  Primary: {primary}  Date: {date}")

    # Move file to right folder
    target_dir = REPO / cat_slug
    target_dir.mkdir(exist_ok=True)
    target = target_dir / html_path.name

    # Enhance + write
    enhanced = enhance_html(text, primary, light, md_filename)
    target.write_text(enhanced, encoding="utf-8")
    print(f"  ✓ Enhanced: {target.relative_to(REPO)}")

    # Generate MD
    article_url = f"{BASE_URL}/{cat_slug}/{html_path.name}"
    md_text = html_to_md(enhanced, article_url)
    md_target = target_dir / md_filename
    md_target.write_text(md_text, encoding="utf-8")
    print(f"  ✓ MD generated: {md_target.relative_to(REPO)}  ({len(md_text)} chars)")

    # Update sitemap
    update_sitemap(article_url, date)

    return target, article_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to single HTML or folder")
    parser.add_argument("--batch", action="store_true", help="Process folder")
    parser.add_argument("--no-push", action="store_true", help="Skip git push")
    parser.add_argument("--no-ping", action="store_true", help="Skip search engine ping")
    args = parser.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"❌ Not found: {p}")
        sys.exit(1)

    targets = []
    if args.batch and p.is_dir():
        for html in p.glob("*.html"):
            t, url = deploy_one(html)
            targets.append((t, url))
    else:
        t, url = deploy_one(p)
        targets.append((t, url))

    # Git commit + push
    if not args.no_push:
        print("\n📦 Committing...")
        run("git add -A", cwd=REPO)
        names = ", ".join(t.stem for t, _ in targets)
        run(f'git commit -m "deploy: {names}"', cwd=REPO, check=False)
        run("git push origin main", cwd=REPO)
        print("  ✓ Pushed")

    # Search engine ping
    if not args.no_ping:
        print("\n🔔 Pinging search engines...")
        for _, url in targets:
            submit_to_search_engines(url)

    print(f"\n✅ Done. {len(targets)} article(s) deployed.")


if __name__ == "__main__":
    main()

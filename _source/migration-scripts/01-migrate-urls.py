#!/usr/bin/env python3
"""
URL 大遷移腳本 — naer-tw.github.io/policy → policy.aabe.org.tw
                  naer-tw.github.io/advocacy-database → advocacy.aabe.org.tw

⚠️ 執行前提：
  1. DNS CNAME 已設好（policy.aabe.org.tw → naer-tw.github.io；同樣 advocacy）
  2. GitHub Pages 已自動偵測 CNAME 檔（每 repo root 有 CNAME）
  3. HTTPS 憑證已自動發行（GH 通常 5-10 分鐘）
  4. 確認新域名可訪問（curl https://policy.aabe.org.tw/ 回 200）

執行方式：
  python3 01-migrate-urls.py --check     # 只列出將要替換的內容（dry run）
  python3 01-migrate-urls.py --execute   # 實際替換
  python3 01-migrate-urls.py --rollback  # 還原（如有需要）

替換範圍：
  - naer-tw.github.io/policy → policy.aabe.org.tw
  - naer-tw.github.io/advocacy-database → advocacy.aabe.org.tw

範圍涵蓋：
  - HTML 檔的 canonical / og:url / Schema @id / 內部連結
  - .md 檔的 url frontmatter
  - sitemap.xml
  - llms.txt
  - robots.txt 的 sitemap 行
  - manifest.json scope/start_url
  - Naer-tw root repo 的所有引用
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

# ═══ 替換規則（順序很重要：先長後短，避免部分替換）═══
REPLACEMENTS = [
    # advocacy 站
    ("https://naer-tw.github.io/advocacy-database/", "https://advocacy.aabe.org.tw/"),
    ("https://naer-tw.github.io/advocacy-database",  "https://advocacy.aabe.org.tw"),
    ("naer-tw.github.io/advocacy-database/",         "advocacy.aabe.org.tw/"),
    ("naer-tw.github.io/advocacy-database",          "advocacy.aabe.org.tw"),
    # policy 站
    ("https://naer-tw.github.io/policy/", "https://policy.aabe.org.tw/"),
    ("https://naer-tw.github.io/policy",  "https://policy.aabe.org.tw"),
    ("naer-tw.github.io/policy/",         "policy.aabe.org.tw/"),
    ("naer-tw.github.io/policy",          "policy.aabe.org.tw"),
    # 注意：root repo（naer-tw.github.io 本身）保持不變，因為那是組織主頁
]

# 處理副檔名範圍
EXTENSIONS = {".html", ".md", ".xml", ".txt", ".json"}

# 不處理目錄
SKIP_DIRS = {".git", "node_modules", "images", ".cache", "_site"}

# 處理範圍
TARGET_REPOS = [
    Path("/Users/coachyang/clawd/naer-policy"),
    Path("/Users/coachyang/clawd/projects/npo-consulting/advocacy-database-repo"),
]

# Backup dir
BACKUP_ROOT = Path("/tmp/url-migration-backup")


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def find_files(repo: Path):
    for fp in repo.rglob("*"):
        if not fp.is_file():
            continue
        if fp.suffix not in EXTENSIONS:
            continue
        if should_skip(fp):
            continue
        yield fp


def process_file(fp: Path, dry_run: bool, backup_dir: Path) -> tuple[int, list[str]]:
    """Returns (count, changed_lines_preview)"""
    try:
        text = fp.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0, []

    new_text = text
    total = 0
    samples = []
    for old, new in REPLACEMENTS:
        count = new_text.count(old)
        if count:
            total += count
            if len(samples) < 3:
                # Find a sample line containing this string
                for line in new_text.split("\n"):
                    if old in line:
                        samples.append(line.strip()[:120])
                        break
            new_text = new_text.replace(old, new)

    if total > 0 and not dry_run:
        # Backup
        rel = fp.relative_to(fp.anchor)
        bk = backup_dir / rel
        bk.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fp, bk)
        # Write
        fp.write_text(new_text, encoding="utf-8")
    return total, samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Dry run — only list what will change")
    parser.add_argument("--execute", action="store_true", help="Execute replacements")
    parser.add_argument("--rollback", action="store_true", help="Restore from backup")
    args = parser.parse_args()

    if not any([args.check, args.execute, args.rollback]):
        parser.print_help()
        sys.exit(0)

    if args.rollback:
        if not BACKUP_ROOT.exists():
            print(f"❌ Backup not found: {BACKUP_ROOT}")
            sys.exit(1)
        print(f"⏪ Restoring from {BACKUP_ROOT}")
        for f in BACKUP_ROOT.rglob("*"):
            if f.is_file():
                target = Path("/") / f.relative_to(BACKUP_ROOT)
                shutil.copy2(f, target)
                print(f"  ✓ {target}")
        print("Rollback complete.")
        return

    dry_run = args.check
    if not dry_run:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        print(f"💾 Backup dir: {BACKUP_ROOT}")

    grand_total = 0
    files_changed = 0

    for repo in TARGET_REPOS:
        if not repo.exists():
            print(f"⚠️  Skip missing repo: {repo}")
            continue
        print(f"\n📂 {repo}")
        for fp in find_files(repo):
            count, samples = process_file(fp, dry_run, BACKUP_ROOT)
            if count:
                grand_total += count
                files_changed += 1
                rel = fp.relative_to(repo)
                marker = "🔍" if dry_run else "✓"
                print(f"  {marker} {rel}  ({count} replacements)")
                for s in samples[:2]:
                    print(f"      | {s}")

    print(f"\n{'═'*60}")
    if dry_run:
        print(f"  DRY RUN: {grand_total} replacements across {files_changed} files")
        print(f"  Run again with --execute to apply.")
    else:
        print(f"  EXECUTED: {grand_total} replacements across {files_changed} files")
        print(f"  Backup: {BACKUP_ROOT}")
        print(f"  Rollback if needed: python3 01-migrate-urls.py --rollback")


if __name__ == "__main__":
    main()

#!/bin/bash
# build_search_index.sh — 部署前產生 Pagefind 站內搜尋索引（第三批②搜尋）
#
# 用法：
#   ./build_search_index.sh              # 對 public/ 建索引到 public/pagefind/
#   ./build_search_index.sh --check      # 建完後檢查索引檔存在＋非空（部署閘用）
#
# 依賴：devDependencies 的 pagefind（package.json 已 pin 版本；npm i 後才有 npx pagefind）。
#
# 範圍（2026-09-15 現況）：
#   只索引本 repo 的 aabe.org.tw（public/ 底下 93 個 HTML 頁）。
#   **policy.aabe.org.tw（47 篇政策分析）未納入**——原因：
#     1. 那是另一個 repo（_policy-deploy，本任務唯讀），部署管線分開，
#        這支腳本沒有它的原始檔可以本機建索引。
#     2. 即使兩邊都各自建了 Pagefind 索引，要在瀏覽器端合併查詢
#        （Pagefind 的 mergeIndex 功能）需要跨網域 fetch 對方的索引檔，
#        而 src/index.js 的 CSP connect-src 只開 'self'，同源以外的
#        fetch 會被瀏覽器擋下——除非放寬 connect-src 允許
#        https://policy.aabe.org.tw，但那超出本任務「不動 CSP 的
#        host 白名單」的授權範圍，需要指揮部/理事長另外裁決。
#   若之後要做「兩站合併搜尋」，建議方向：policy 站也建一份 Pagefind
#   索引，兩邊在各自站內各自搜尋（現況），或申請放寬 connect-src 後
#   用 mergeIndex 做真正合併查詢——兩者都需要另外派工。
#
# 部署管線串接建議：在 postdeploy.sh 的「git push 之前」呼叫本腳本，
# 確保 public/pagefind/（gitignore 排除，不進 repo）在每次部署前重建、
# 不會用到舊索引。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PUBLIC_DIR="$REPO_DIR/public"
INDEX_DIR="$PUBLIC_DIR/pagefind"

CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
  esac
done

cd "$REPO_DIR"

if [ ! -d node_modules/pagefind ]; then
  echo "[build_search_index] node_modules/pagefind 不存在，先跑 npm install" >&2
  npm install
fi

echo "[build_search_index] 對 $PUBLIC_DIR 建 Pagefind 索引 → $INDEX_DIR"
npx pagefind --site "$PUBLIC_DIR" --output-path "$INDEX_DIR"

# ── 檢查（部署閘用）──────────────────────────────────────
FAIL=0
if [ ! -f "$INDEX_DIR/pagefind.js" ]; then
  echo "[build_search_index] FAIL：找不到 $INDEX_DIR/pagefind.js" >&2
  FAIL=1
fi
if [ ! -f "$INDEX_DIR/pagefind-entry.json" ]; then
  echo "[build_search_index] FAIL：找不到 $INDEX_DIR/pagefind-entry.json" >&2
  FAIL=1
fi
PAGE_COUNT=$(python3 -c "
import json
try:
    d = json.load(open('$INDEX_DIR/pagefind-entry.json'))
    print(sum(v.get('page_count', 0) for v in d.get('languages', {}).values()))
except Exception:
    print(0)
")
if [ "${PAGE_COUNT:-0}" -lt 1 ]; then
  echo "[build_search_index] FAIL：索引頁數為 0（pagefind-entry.json 讀不到 page_count）" >&2
  FAIL=1
else
  echo "[build_search_index] 索引頁數：$PAGE_COUNT"
fi

INDEX_SIZE=$(du -sh "$INDEX_DIR" 2>/dev/null | cut -f1)
echo "[build_search_index] 索引大小：${INDEX_SIZE:-未知}"

if [ "$FAIL" -ne 0 ]; then
  echo "[build_search_index] 索引建置檢查未通過，中止部署" >&2
  exit 1
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
  echo "[build_search_index] --check 通過"
fi

echo "[build_search_index] 完成。注意：public/pagefind/ 已 gitignore，不進 repo——"
echo "  部署到 Cloudflare Workers 前，這支腳本必須在 wrangler deploy 之前對「即將部署的那份 public/」跑一次，"
echo "  否則線上只有 HTML 沒有索引檔，搜尋會 404。"

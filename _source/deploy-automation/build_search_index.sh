#!/bin/bash
# build_search_index.sh — 部署前產生 Pagefind 站內搜尋索引
# （第三批②搜尋建立本站索引；第四輪 2026-09-16 加上政策站合併索引）
#
# 用法：
#   ./build_search_index.sh              # 建 public/pagefind/（本站）＋ public/pagefind-policy/（政策站，若找得到來源）
#   ./build_search_index.sh --check      # 建完後檢查兩個索引存在＋非空（部署閘用）
#
# 依賴：devDependencies 的 pagefind（package.json 已 pin 版本；npm i 後才有 npx pagefind）。
#
# 範圍與方案（2026-09-16 第四輪）：
#   本站（aabe.org.tw，public/ 底下）與政策站（policy.aabe.org.tw，
#   47 篇政策分析，來源 repo `_policy-deploy`，本任務唯讀）分別建置
#   **兩個獨立的 Pagefind 索引**：
#     - public/pagefind/         ← 本站 93 個 HTML 頁
#     - public/pagefind-policy/  ← 政策站 47 篇文章（複製到暫存目錄後
#       用 build_policy_search_staging.py 補上 data-pagefind-* 屬性）
#   兩個索引都**同源放在 aabe.org.tw**，前端用兩次 `import()` 各自
#   載入、各自 `search()`，在 JS 裡把兩邊結果依分數合併排序——
#   完全不需要 Pagefind 的 `mergeIndex()`（那個功能官方文件明講
#   「跨網域索引要對方伺服器開 CORS」，且瀏覽器端等於一次跨網域
#   fetch，會被 src/index.js 的 CSP `connect-src 'self'` 擋下）。
#   政策站結果的網址在前端渲染時手動補上 `https://policy.aabe.org.tw`
#   前綴（Pagefind 記錄的 url 是相對於建索引時的 --site 根目錄，本來
#   就不含網域）。**因此完全不需要放寬 CSP、不需要新增任何外部網域
#   白名單**——兩個索引檔、渲染邏輯都在 aabe.org.tw 自己的
#   public/ 底下。
#
#   政策站來源目錄預設抓 sibling repo `../_policy-deploy`（可用環境變數
#   POLICY_SITE_DIR 覆寫）。**找不到就跳過政策站索引並印警告，不中止
#   本站索引的建置**——因為正式部署環境（CI）不一定會 checkout 到這個
#   sibling repo，政策站索引目前只在有該 repo 的本機環境建置。
#
# 部署管線串接建議：在 postdeploy.sh 的「git push 之前」呼叫本腳本，
# 確保 public/pagefind*/（已納入版控：正式站直接取用 repo 內 public/）
# 在每次內容變更後重建、不會用到舊索引。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PUBLIC_DIR="$REPO_DIR/public"
INDEX_DIR="$PUBLIC_DIR/pagefind"
POLICY_INDEX_DIR="$PUBLIC_DIR/pagefind-policy"
POLICY_SITE_DIR="${POLICY_SITE_DIR:-$REPO_DIR/../_policy-deploy}"
POLICY_STAGING_DIR="$REPO_DIR/.policy-search-staging"

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

# ── 政策站索引（第四輪，2026-09-16）──────────────────────
POLICY_BUILT=0
if [ -d "$POLICY_SITE_DIR" ]; then
  echo "[build_search_index] 找到政策站來源 $POLICY_SITE_DIR，建立暫存標記目錄"
  python3 "$SCRIPT_DIR/build_policy_search_staging.py" "$POLICY_SITE_DIR" "$POLICY_STAGING_DIR"
  echo "[build_search_index] 對 $POLICY_STAGING_DIR 建 Pagefind 索引 → $POLICY_INDEX_DIR"
  npx pagefind --site "$POLICY_STAGING_DIR" --output-path "$POLICY_INDEX_DIR"
  POLICY_BUILT=1
else
  echo "[build_search_index] 警告：找不到政策站來源目錄 $POLICY_SITE_DIR，略過政策站索引" \
    "（本機若要建，設環境變數 POLICY_SITE_DIR 指到 _policy-deploy 的 checkout 路徑）" >&2
fi

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
  echo "[build_search_index] 本站索引頁數：$PAGE_COUNT"
fi

INDEX_SIZE=$(du -sh "$INDEX_DIR" 2>/dev/null | cut -f1)
echo "[build_search_index] 本站索引大小：${INDEX_SIZE:-未知}"

if [ "$POLICY_BUILT" -eq 1 ]; then
  if [ ! -f "$POLICY_INDEX_DIR/pagefind.js" ]; then
    echo "[build_search_index] FAIL：找不到 $POLICY_INDEX_DIR/pagefind.js" >&2
    FAIL=1
  fi
  POLICY_PAGE_COUNT=$(python3 -c "
import json
try:
    d = json.load(open('$POLICY_INDEX_DIR/pagefind-entry.json'))
    print(sum(v.get('page_count', 0) for v in d.get('languages', {}).values()))
except Exception:
    print(0)
")
  if [ "${POLICY_PAGE_COUNT:-0}" -lt 40 ]; then
    echo "[build_search_index] FAIL：政策站索引頁數 ${POLICY_PAGE_COUNT:-0} < 40（預期 47 篇左右）" >&2
    FAIL=1
  else
    echo "[build_search_index] 政策站索引頁數：$POLICY_PAGE_COUNT"
  fi
  POLICY_INDEX_SIZE=$(du -sh "$POLICY_INDEX_DIR" 2>/dev/null | cut -f1)
  echo "[build_search_index] 政策站索引大小：${POLICY_INDEX_SIZE:-未知}"
fi

if [ "$FAIL" -ne 0 ]; then
  echo "[build_search_index] 索引建置檢查未通過，中止部署" >&2
  exit 1
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
  echo "[build_search_index] --check 通過"
fi

echo "[build_search_index] 完成。注意：public/pagefind*/ 已納入版控——"
echo "  部署到 Cloudflare Workers 前，這支腳本必須在 wrangler deploy 之前對「即將部署的那份 public/」跑一次，"
echo "  否則線上索引可能是舊的（漏掉最新內容或政策站新文章）。"

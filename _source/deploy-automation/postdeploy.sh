#!/bin/bash
# postdeploy.sh — 部署後索引一鍵（SOP-數據更新與部署索引.md 第五節）
#
# 做三件事：
#   1. 實地驗證：curl 線上五頁，逐一比對 _source/numbers.json 的 display 與窗口電話。
#      全對印 LIVE_OK；有一處不符就 exit 1（不宣告完成）。
#   2. 搜尋引擎：呼叫 ../indexnow-ping.sh 推有改動的 URL（可用參數指定，預設推驗過的五頁）。
#   3. 印出「看板待做」提醒（狀態檔最新交付行＋當天日誌一列）。
#
# 用法：
#   ./postdeploy.sh                                  # 驗證＋推預設五頁
#   ./postdeploy.sh https://aabe.org.tw/ https://aabe.org.tw/impact/   # 只推指定 URL
#   ./postdeploy.sh --skip-ping                      # 只驗證不推（測試／重跑驗證用）
#   ./postdeploy.sh --base http://127.0.0.1:8000     # 換基底網址（本機預覽用）
#
# 註：線上比對是「去標籤後的文字」，不是原始 HTML——版面上的 `3,000+` 實際是
#     `3,000<span class="m-plus">+</span>`，硬 grep 原始碼會假性失敗。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
NUMBERS="$REPO_DIR/_source/numbers.json"
PUBLIC_DIR="$REPO_DIR/public"
INDEXNOW_SCRIPT="${INDEXNOW_SCRIPT:-$SCRIPT_DIR/../indexnow-ping.sh}"
BASE="https://aabe.org.tw"
PHONE="0983-097-165"
SKIP_PING=0
PING_URLS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --base) BASE="${2%/}"; shift 2 ;;
    --skip-ping) SKIP_PING=1; shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) PING_URLS+=("$1"); shift ;;
  esac
done

# 要驗的頁面：路徑｜本地對照檔（決定這頁該有哪些數字）｜是否要驗窗口電話
PAGES=(
  "/|index.html|no"
  "/methodology/|methodology/index.html|no"
  "/contact/|contact/index.html|yes"
  "/press/|press/index.html|yes"
  "/impact/|impact/index.html|no"
)

DEFAULT_PING_URLS=(
  "https://aabe.org.tw/"
  "https://aabe.org.tw/methodology/"
  "https://aabe.org.tw/contact/"
  "https://aabe.org.tw/press/"
  "https://aabe.org.tw/impact/"
)

TMP="$(mktemp -t aabe-postdeploy)"
trap 'rm -f "$TMP"' EXIT
fail=0

echo "=== 部署後實地驗證（基底 ${BASE}，真源 _source/numbers.json）==="

for entry in "${PAGES[@]}"; do
  IFS='|' read -r path local_file want_phone <<< "$entry"
  url="$BASE$path"
  if ! curl -sS --max-time 20 "$url" -o "$TMP"; then
    echo "  ❌ $url 取不到內容"
    fail=1
    continue
  fi
  if ! python3 - "$SCRIPT_DIR" "$TMP" "$PUBLIC_DIR/$local_file" "$NUMBERS" \
                 "$want_phone" "$PHONE" "$path" <<'PY'
import sys
from pathlib import Path

script_dir, live, local, numbers, want_phone, phone, path = sys.argv[1:8]
sys.path.insert(0, script_dir)
import numbers_check as nc                                    # noqa: E402

metrics = nc.load_metrics(Path(numbers))
text, _ = nc.condense(Path(live).read_text(encoding="utf-8", errors="replace"))
ids = sorted({m.metric_id for m in nc.find_marked(Path(local).read_text(encoding="utf-8"))})

bad = 0
for mid in ids:
    want = metrics[mid]["display"]
    if want in text:
        print(f"  ✅ {path} {mid} = {want}")
    else:
        print(f"  ❌ {path} {mid} 線上找不到真源值「{want}」")
        bad += 1
if want_phone == "yes":
    if phone in text:
        print(f"  ✅ {path} 窗口電話 {phone}")
    else:
        print(f"  ❌ {path} 找不到窗口電話 {phone}（理事長 王瀚陽，全站唯一具名窗口）")
        bad += 1
sys.exit(1 if bad else 0)
PY
  then
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "❌ 線上內容與真源不符，未通過驗證——不要宣告完成，先查是部署未生效還是漏改。"
  exit 1
fi

echo ""
echo "LIVE_OK"
echo ""

# ── 2. IndexNow ────────────────────────────────────────────
if [ "$SKIP_PING" -eq 1 ]; then
  echo "（--skip-ping：略過 IndexNow 推送）"
else
  if [ "${#PING_URLS[@]}" -eq 0 ]; then
    PING_URLS=("${DEFAULT_PING_URLS[@]}")
  fi
  echo "=== IndexNow 推送 ==="
  bash "$INDEXNOW_SCRIPT" "${PING_URLS[@]}"
fi

# ── 3. 看板待做 ────────────────────────────────────────────
TODAY="$(date +%Y-%m-%d)"
COMMIT="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo '（取不到 commit）')"
cat <<EOF

=== 看板待做（腳本做不了、需要人動手的兩件事）===
看板：~/Desktop/國教盟指揮看板/議題_官網影響力數據/
  1. 狀態檔 _狀態.md：最新交付行改成 ${TODAY}（本次部署 main commit ${COMMIT}）
  2. 當天日誌加一列：部署時間、main commit ${COMMIT}、驗證結果 LIVE_OK
另提醒：清單檔「已上官網」欄勾 ${TODAY}；首頁與方法頁有改動時，到 Google Search Console 請求索引一次。
EOF

#!/bin/bash
# postdeploy.sh — 部署後索引一鍵驗證＋有證據的人工收尾（SOP-數據更新與部署索引.md 第五節）
#
# 2026-09-06 依 Codex 盲審 C-07／C-08 改寫（報告：_source/審查_Codex盲審_數據SOP_20260906.md）：
#   舊版把 `LIVE_OK` 印在 IndexNow 之前、且不看 helper 的 return code，
#   key 失效或 helper 路徑壞掉照樣 exit 0——索引失敗被包裝成「一鍵完成」。
#
# 現在分三段狀態，全過才有 POSTDEPLOY_OK：
#   1. CONTENT_LIVE_OK ── 線上逐個 data-metric 標記比對真源（含所有含標記的頁面、
#      llms.txt／humans.txt、窗口電話）。詳見 postdeploy_verify.py。
#   2. INDEXNOW_OK     ── IndexNow 推送真的被接受（非 200/202 或 helper 失敗＝失敗）。
#   3. 人工收尾         ── 看板、清單、GSC、知識庫、經驗回寫，逐項列在 receipt 裡標 pending。
#
# 用法：
#   ./postdeploy.sh                                   # 驗證＋推所有含標記的頁面
#   ./postdeploy.sh https://aabe.org.tw/ https://aabe.org.tw/impact/   # 只推指定 URL
#   ./postdeploy.sh --skip-ping                       # 只驗證不推（重跑驗證用）
#   ./postdeploy.sh --base http://127.0.0.1:8000      # 換基底網址（本機預覽用）
#   ./postdeploy.sh --live-dir public --skip-ping     # 完全離線驗證（測試用）
#   ./postdeploy.sh --receipt /tmp/receipt.md         # 另存機器可讀收據

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
NUMBERS="$REPO_DIR/_source/numbers.json"
PUBLIC_DIR="$REPO_DIR/public"
INDEXNOW_SCRIPT="${INDEXNOW_SCRIPT:-$SCRIPT_DIR/../indexnow-ping.sh}"
BASE="https://aabe.org.tw"
PHONE="0983-097-165"
SKIP_PING=0
LIVE_DIR=""
RECEIPT=""
PING_URLS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --base) BASE="${2%/}"; shift 2 ;;
    --live-dir) LIVE_DIR="$2"; shift 2 ;;
    --receipt) RECEIPT="$2"; shift 2 ;;
    --skip-ping) SKIP_PING=1; shift ;;
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
    *) PING_URLS+=("$1"); shift ;;
  esac
done

CONTENT_STATE="failed"
INDEXNOW_STATE="skipped"

# ── 1. 線上內容驗證 ────────────────────────────────────────
VERIFY_ARGS=(--base "$BASE" --public "$PUBLIC_DIR" --numbers "$NUMBERS")
[ -n "$LIVE_DIR" ] && VERIFY_ARGS+=(--live-dir "$LIVE_DIR")

if python3 "$SCRIPT_DIR/postdeploy_verify.py" "${VERIFY_ARGS[@]}"; then
  CONTENT_STATE="done"
else
  CONTENT_STATE="failed"
fi

if [ "$CONTENT_STATE" != "done" ]; then
  echo ""
  echo "POSTDEPLOY_FAILED（內容驗證未過）"
  exit 1
fi

echo ""

# ── 2. IndexNow ────────────────────────────────────────────
if [ "$SKIP_PING" -eq 1 ]; then
  INDEXNOW_STATE="skipped"
  echo "（--skip-ping：略過 IndexNow 推送；本次不算完整部署後索引）"
else
  if [ "${#PING_URLS[@]}" -eq 0 ]; then
    # 推的範圍＝驗過的範圍（不再寫死五頁）
    while IFS= read -r u; do
      [ -n "$u" ] && PING_URLS+=("$u")
    done < <(python3 "$SCRIPT_DIR/postdeploy_verify.py" --base "$BASE" \
               --public "$PUBLIC_DIR" --numbers "$NUMBERS" --print-urls)
  fi
  echo "=== IndexNow 推送 ==="
  if bash "$INDEXNOW_SCRIPT" "${PING_URLS[@]}"; then
    INDEXNOW_STATE="done"
    echo "INDEXNOW_OK"
  else
    INDEXNOW_STATE="failed"
    echo "❌ IndexNow 推送失敗（helper 回非零）——索引沒完成，不可當成部署已收尾。"
  fi
fi

# ── 3. 收據：人工收尾逐項標 pending ────────────────────────
TODAY="$(date +%Y-%m-%d)"
COMMIT="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo '（取不到 commit）')"

emit_receipt() {
  cat <<EOF
# 部署後索引收據 ${TODAY}

- commit：${COMMIT}
- 基底：${LIVE_DIR:-$BASE}
- content_live：${CONTENT_STATE}
- indexnow：${INDEXNOW_STATE}
- sitemap_lastmod：pending（改動頁與 sitemap_index.xml 由 numbers_check／pytest 擋，部署後請確認線上 sitemap 已更新）
- gsc_request_index：pending（首頁或方法頁有改動時，到 Search Console 請求索引一次，回填請求時間）
- board_status：pending（~/Desktop/國教盟指揮看板/議題_官網影響力數據/_狀態.md 最新交付行改 ${TODAY}）
- board_log：pending（當天日誌加一列：部署時間、main commit ${COMMIT}、驗證結果）
- list_checkbox：pending（清單檔「已上官網」欄勾 ${TODAY}）
- kb_caveat：pending（數字若源自知識庫卡片，卡片 caveat 加「已上官網 ${TODAY}」）
- sop_experience：pending（本次踩到的坑寫進 SOP 第七節「經驗紀錄」）
EOF
}

echo ""
emit_receipt
[ -n "$RECEIPT" ] && emit_receipt > "$RECEIPT" && echo "" && echo "收據已寫入：$RECEIPT"

echo ""
if [ "$CONTENT_STATE" = "done" ] && [ "$INDEXNOW_STATE" = "done" ]; then
  echo "POSTDEPLOY_OK（機器能做的兩項都過；上列 pending 是人要做的，做完請回填收據）"
  exit 0
fi
if [ "$INDEXNOW_STATE" = "skipped" ]; then
  echo "CONTENT_LIVE_OK（但 IndexNow 略過，尚未完成部署後索引）"
  exit 0
fi
echo "POSTDEPLOY_FAILED（IndexNow 未完成）"
exit 1

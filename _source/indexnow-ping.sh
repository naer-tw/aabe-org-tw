#!/bin/bash
# IndexNow 推送 script
# 用法：./indexnow-ping.sh [url1] [url2] ...
# 不帶參數：推送整站主要頁面
#
# IndexNow 是 Bing / Yandex / Naver / Seznam 共同支持的標準
# 一次推送，多家搜尋引擎同步索引（Google 不支援但可從 GSC 個別推）

KEY="cf7b84e6b78b446bd75fd7e04b9c06b7"
KEY_LOC="https://aabe.org.tw/cf7b84e6b78b446bd75fd7e04b9c06b7.txt"
HOST="aabe.org.tw"

# 預設要推的主要頁面（不帶參數時用）
DEFAULT_URLS=(
  "https://aabe.org.tw/"
  "https://aabe.org.tw/about/"
  "https://aabe.org.tw/issues/"
  "https://aabe.org.tw/chronicle/"
  "https://aabe.org.tw/events/"
  "https://aabe.org.tw/events/2026-05-20-drug-abuse-conference/"
  "https://aabe.org.tw/act/"
  "https://aabe.org.tw/press/"
  "https://aabe.org.tw/methodology/"
  "https://aabe.org.tw/impact/"
  "https://aabe.org.tw/contact/"
)

if [ $# -eq 0 ]; then
  URLS=("${DEFAULT_URLS[@]}")
else
  URLS=("$@")
fi

# 組 JSON
URLS_JSON=$(printf '"%s",' "${URLS[@]}")
URLS_JSON="[${URLS_JSON%,}]"

PAYLOAD=$(cat <<EOF
{
  "host": "$HOST",
  "key": "$KEY",
  "keyLocation": "$KEY_LOC",
  "urlList": $URLS_JSON
}
EOF
)

echo "=== IndexNow 推送 ${#URLS[@]} 個 URL ==="
printf '  • %s\n' "${URLS[@]}"
echo ""

# 推到 Bing（也會分發給 Yandex / Naver 等）
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "https://api.indexnow.org/IndexNow" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$PAYLOAD")

BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -1)

echo "Bing/IndexNow response: HTTP $STATUS"
[ -n "$BODY" ] && echo "Body: $BODY"

case "$STATUS" in
  200|202) echo "✅ 成功送出（200=已接受、202=排隊中）" ;;
  400) echo "⚠️  Bad request（檢查 JSON 格式）" ;;
  403) echo "❌ Forbidden（key 不存在於 keyLocation）" ;;
  422) echo "⚠️  URL 不屬於 host（檢查 host 設定）" ;;
  429) echo "⚠️  Too many requests（一天上限約 10,000）" ;;
  *) echo "⚠️  未預期狀態：$STATUS" ;;
esac

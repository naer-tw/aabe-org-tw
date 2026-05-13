#!/bin/bash
# NS 切換後驗證腳本
# 用法：./post-ns-switch-check.sh

echo "═══════════════════════════════════════════"
echo " aabe.org.tw NS 切換後驗證 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════"
echo ""

# 1. NS 是否切過來
echo "🔵 Step 1: 確認 NS 已切換到我們的 Cloudflare"
NS=$(/usr/bin/dig aabe.org.tw NS +short)
echo "目前 NS:"
echo "$NS" | sed 's/^/  /'
if echo "$NS" | grep -q "bowen\|danica"; then
  echo "  ✅ NS 已切換到我們帳號"
else
  echo "  ⚠️ NS 還沒切過來（仍在原 CF 帳號或傳播中）"
fi
echo ""

# 2. A 紀錄解析
echo "🔵 Step 2: aabe.org.tw A 紀錄"
/usr/bin/dig aabe.org.tw +short | sed 's/^/  /'
echo ""
echo "🔵 Step 3: www.aabe.org.tw A 紀錄"
/usr/bin/dig www.aabe.org.tw +short | sed 's/^/  /'
echo ""
echo "🔵 Step 4: demo.aabe.org.tw A 紀錄（保留官網公司）"
/usr/bin/dig demo.aabe.org.tw +short | sed 's/^/  /'
echo ""

# 3. HTTPS 連線測試
echo "🔵 Step 5: HTTPS 連線 + SSL 憑證"
for host in aabe.org.tw www.aabe.org.tw; do
  echo "  https://${host}/"
  /usr/bin/curl -sLo /dev/null -w "    HTTP %{http_code} | SSL ${host} | %{time_total}s\n" \
    "https://${host}/"
done
echo ""

# 4. 6 頁全測
echo "🔵 Step 6: 6 頁 HTTP 狀態"
for path in / /about/ /issues/ /chronicle/ /events/ /contact/; do
  code=$(/usr/bin/curl -sLo /dev/null -w "%{http_code}" "https://aabe.org.tw${path}")
  echo "  ${path} → ${code}"
done
echo ""

# 5. 靜態檔
echo "🔵 Step 7: AI 索引檔"
for path in /llms.txt /robots.txt /humans.txt /.well-known/security.txt; do
  code=$(/usr/bin/curl -sLo /dev/null -w "%{http_code}" "https://aabe.org.tw${path}")
  size=$(/usr/bin/curl -sLo /dev/null -w "%{size_download}" "https://aabe.org.tw${path}")
  echo "  ${path} → ${code} | ${size}b"
done
echo ""

# 6. CDN 確認
echo "🔵 Step 8: Cloudflare CDN headers"
/usr/bin/curl -sI https://aabe.org.tw/ 2>&1 | /usr/bin/grep -iE "server|cf-ray|cf-cache" | sed 's/^/  /'
echo ""

# 7. Schema.org 抽樣
echo "🔵 Step 9: 首頁 Schema.org JSON-LD 數量"
count=$(/usr/bin/curl -sL https://aabe.org.tw/ | /usr/bin/grep -c "application/ld+json")
echo "  ${count} 個 JSON-LD 區塊"
echo ""

echo "═══════════════════════════════════════════"
echo "驗證完成。如果都是 ✅ 200 + Cloudflare server，"
echo "新版 aabe.org.tw 已正式上線！"
echo "═══════════════════════════════════════════"

/**
 * AABE 官網 Worker — Static Assets + Routing + Security Headers
 *
 * 處理：
 *  1. 舊版 URL → 新版 301 redirect（保住 SEO 排名）
 *  2. 對所有回應補上安全標頭（HSTS / CSP / X-CTO / Referrer-Policy / Permissions-Policy）
 *  3. 對靜態資源（uploads / assets）設長快取 (1 年 + immutable)
 *  4. 其他靜態資源透過 ASSETS binding 服務
 *
 * Wrangler 配置依賴：
 *  - [assets] directory = "./public", binding = "ASSETS", not_found_handling = "404-page"
 */

// ───────────────────────────────────────────
// 1. 舊 URL → 新 URL 301 對應表
// ───────────────────────────────────────────
const REDIRECTS = {
  '/introduction_aabe': '/about/',
  '/introduction_aabe/': '/about/',
  '/event-announcement': '/events/',
  '/event-announcement/': '/events/',
  '/contact-us': '/contact/',
  '/contact-us/': '/contact/',
};

// ───────────────────────────────────────────
// 2. 安全標頭（套用所有 HTML 回應）
// ───────────────────────────────────────────
const SECURITY_HEADERS = {
  // 1 年強制 HTTPS（包含子網域，可送 preload list）
  'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',

  // 禁止 MIME-sniffing
  'X-Content-Type-Options': 'nosniff',

  // 跨來源 referrer 只傳 origin
  'Referrer-Policy': 'strict-origin-when-cross-origin',

  // 阻擋 iframe 嵌入（避免 clickjacking）
  'X-Frame-Options': 'DENY',

  // 預設禁用瀏覽器強權限
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',

  // CSP — 容許目前站上實際使用的資源
  // 白名單：Google Fonts、Cloudflare Insights、自家圖片、inline style/script
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com",
    "script-src-elem 'self' 'unsafe-inline' https://static.cloudflareinsights.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "media-src 'self'",
    "connect-src 'self' https://cloudflareinsights.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; '),
};

// ───────────────────────────────────────────
// 3. 長快取路徑（檔名不變才可開）
// ───────────────────────────────────────────
const LONG_CACHE_PREFIXES = ['/wp-content/uploads/', '/assets/'];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 1) 301 redirects
    const redirectTo = REDIRECTS[url.pathname];
    if (redirectTo) {
      return Response.redirect(url.origin + redirectTo + url.search, 301);
    }

    // 1.5) /robots.txt — 直接從 ASSETS 回傳純文字（覆寫 Cloudflare AI Audit 注入）
    //      Cloudflare AI Audit 預設會 prepend Disallow 各 AI bot，跟我們的 Allow 衝突。
    //      Worker 攔截後直接回我們的版本，並用 no-transform 阻止後續修改。
    if (url.pathname === '/robots.txt') {
      const robotsRes = await env.ASSETS.fetch(new Request(url.origin + '/robots.txt'));
      const body = await robotsRes.text();
      return new Response(body, {
        status: 200,
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'public, max-age=3600, no-transform',
          'X-Robots-Tag': 'noai-policy: see-content-signals-header',
        },
      });
    }

    // 2) 從 ASSETS 取靜態資源
    const response = await env.ASSETS.fetch(request);

    // 3) clone 出可變的 headers
    const headers = new Headers(response.headers);

    // 4) 加安全標頭
    for (const [k, v] of Object.entries(SECURITY_HEADERS)) {
      headers.set(k, v);
    }

    // 5) 對靜態資源開長快取（uploads / assets 內檔名都帶版本意義，可 immutable）
    if (LONG_CACHE_PREFIXES.some((p) => url.pathname.startsWith(p))) {
      headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    }

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};

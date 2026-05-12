<?php
/**
 * AABE GEO/AI Optimization Snippet
 *
 * 把這段程式碼貼到 WordPress 主題的 functions.php 末尾
 * 路徑：wp-content/themes/soledad/functions.php
 *
 * 或建議：
 * 1. 在 wp-content/themes/ 下建一個 child theme（避免主題更新時被覆蓋）
 * 2. 用 Code Snippets 外掛安全管理（推薦）
 *
 * @author 國教行動聯盟
 * @version 1.0
 * @date 2026-04-28
 */

// ─────────────────────────────────────────────────────────
// 1. 修正 og:title「HOME」問題
// ─────────────────────────────────────────────────────────
function aabe_fix_og_title( $title ) {
    if ( is_front_page() || is_home() ) {
        return '國教行動聯盟｜為孩子的教育權發聲';
    }
    return $title;
}
add_filter( 'pre_get_document_title', 'aabe_fix_og_title', 9999 );
add_filter( 'wpseo_title', 'aabe_fix_og_title', 9999 ); // Yoast 相容
add_filter( 'rank_math/frontend/title', 'aabe_fix_og_title', 9999 ); // Rank Math 相容

// ─────────────────────────────────────────────────────────
// 2. 修正 og:description（首頁應該寫完整版本）
// ─────────────────────────────────────────────────────────
function aabe_fix_og_description() {
    if ( is_front_page() || is_home() ) {
        $desc = '國教行動聯盟（AABE / NAER）成立於 2012 年，是台灣推動兒童及青少年權益的家長倡議組織。長期關注校園安全、兒少保護、教育改革、青少年身心健康四大議題，與 168+ 跨領域組織合作，2023-2025 累計發布 113 篇政策論述、舉辦 286 場倡議活動。';
        echo '<meta name="description" content="' . esc_attr( $desc ) . '">' . "\n";
    }
}
add_action( 'wp_head', 'aabe_fix_og_description', 1 );

// ─────────────────────────────────────────────────────────
// 3. 注入完整 Schema.org JSON-LD（Organization + WebSite + Dataset + ItemList）
// ─────────────────────────────────────────────────────────
function aabe_inject_schema_jsonld() {
    if ( ! is_front_page() && ! is_home() ) return;

    // ── Organization (NGO) ──
    $org = [
        '@context' => 'https://schema.org',
        '@type' => 'NGO',
        '@id' => 'https://aabe.org.tw/#organization',
        'name' => '國教行動聯盟',
        'alternateName' => [ '國教盟', '社團法人國教行動聯盟', 'Action Alliance on Basic Education', 'AABE', 'NAER' ],
        'url' => 'https://aabe.org.tw/',
        'logo' => 'https://aabe.org.tw/wp-content/uploads/logo-naer.png', // 請替換為實際 logo URL
        'foundingDate' => '2012-06-26',
        'description' => '台灣推動兒童及青少年權益的家長倡議組織，關注校園安全、兒少保護、教育改革、青少年身心健康四大議題。',
        'areaServed' => [ '@type' => 'Country', 'name' => 'TW' ],
        'sameAs' => [
            'https://www.facebook.com/twedumove/',
            'https://zh.wikipedia.org/wiki/國教行動聯盟',
        ],
        'knowsAbout' => [
            '台灣教育政策', '校園安全', '兒少權益', '兒少保護',
            '少年司法', '教育改革', '兒童健康', '青少年身心健康',
            '菸害防制', '性別平等教育', '家長參與', '教師事務',
        ],
        'taxID' => '41142910', // 統一編號
        'contactPoint' => [
            '@type' => 'ContactPoint',
            'url' => 'https://www.facebook.com/twedumove/',
            'contactType' => 'public relations',
            'availableLanguage' => [ 'zh-TW', 'en' ],
        ],
    ];

    // ── WebSite + SearchAction ──
    $website = [
        '@context' => 'https://schema.org',
        '@type' => 'WebSite',
        '@id' => 'https://aabe.org.tw/#website',
        'url' => 'https://aabe.org.tw/',
        'name' => '國教行動聯盟',
        'description' => '從倡議到改變・我們為孩子發聲',
        'inLanguage' => 'zh-TW',
        'publisher' => [ '@id' => 'https://aabe.org.tw/#organization' ],
        'potentialAction' => [
            '@type' => 'SearchAction',
            'target' => [
                '@type' => 'EntryPoint',
                'urlTemplate' => 'https://aabe.org.tw/?s={search_term_string}',
            ],
            'query-input' => 'required name=search_term_string',
        ],
    ];

    // ── ItemList（6 大主題）──
    $itemlist = [
        '@context' => 'https://schema.org',
        '@type' => 'ItemList',
        'name' => '國教行動聯盟核心議題',
        'description' => '六大政策主軸',
        'itemListElement' => [
            [ '@type' => 'ListItem', 'position' => 1, 'name' => '校園安全', 'url' => 'https://aabe.org.tw/category/campus-safety/' ],
            [ '@type' => 'ListItem', 'position' => 2, 'name' => '兒少保護', 'url' => 'https://aabe.org.tw/category/child-protection/' ],
            [ '@type' => 'ListItem', 'position' => 3, 'name' => '青少年身心健康', 'url' => 'https://aabe.org.tw/category/youth-health/' ],
            [ '@type' => 'ListItem', 'position' => 4, 'name' => '教育政策與改革', 'url' => 'https://aabe.org.tw/category/education-reform/' ],
            [ '@type' => 'ListItem', 'position' => 5, 'name' => '教師與校務', 'url' => 'https://aabe.org.tw/category/teacher-affairs/' ],
            [ '@type' => 'ListItem', 'position' => 6, 'name' => '數位與性別安全', 'url' => 'https://aabe.org.tw/category/digital-safety/' ],
        ],
    ];

    // ── Dataset（cross-reference 政策知識庫 + 倡議資料庫）──
    $dataset = [
        '@context' => 'https://schema.org',
        '@type' => 'Dataset',
        '@id' => 'https://aabe.org.tw/#combined-knowledge-dataset',
        'name' => '國教行動聯盟政策論述與倡議成果資料集',
        'description' => '結合政策知識庫（27 篇深度分析）與倡議資料庫（113 篇新聞稿、286 場活動、7,917+ 媒體聲量、168+ 合作組織）的整合資料集。',
        'url' => 'https://aabe.org.tw/',
        'keywords' => [ '教育政策', '兒少權益', '校園安全', '少年司法', '台灣 NGO' ],
        'creator' => [ '@id' => 'https://aabe.org.tw/#organization' ],
        'publisher' => [ '@id' => 'https://aabe.org.tw/#organization' ],
        'license' => 'https://creativecommons.org/licenses/by/4.0/',
        'temporalCoverage' => '2012-06/..',
        'spatialCoverage' => [ '@type' => 'Place', 'name' => '台灣' ],
        'inLanguage' => 'zh-TW',
        'distribution' => [
            [
                '@type' => 'DataDownload',
                'encodingFormat' => 'text/markdown',
                'contentUrl' => 'https://aabe.org.tw/llms.txt',
                'name' => 'AI-friendly llms.txt index',
            ],
        ],
        'isRelatedTo' => [
            [ '@type' => 'Dataset', 'name' => '政策知識庫', 'url' => 'https://policy.aabe.org.tw/' ],
            [ '@type' => 'Dataset', 'name' => '倡議成果資料庫', 'url' => 'https://advocacy.aabe.org.tw/' ],
        ],
    ];

    // 輸出 JSON-LD
    foreach ( [ $org, $website, $itemlist, $dataset ] as $schema ) {
        echo "\n" . '<script type="application/ld+json">' . "\n";
        echo wp_json_encode( $schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT );
        echo "\n" . '</script>' . "\n";
    }
}
add_action( 'wp_head', 'aabe_inject_schema_jsonld', 5 );

// ─────────────────────────────────────────────────────────
// 4. 注入 AI agent discovery <link> tags
// ─────────────────────────────────────────────────────────
function aabe_inject_agent_links() {
    echo "\n";
    echo '<link rel="alternate" type="text/markdown" href="/llms.txt">' . "\n";
    echo '<link rel="author" href="/humans.txt">' . "\n";
    echo '<meta name="theme-color" content="#0a0a0a">' . "\n";
}
add_action( 'wp_head', 'aabe_inject_agent_links', 6 );

// ─────────────────────────────────────────────────────────
// 5. HTTP Link response header（RFC 8288 — 給 AI agent 發現用）
// ─────────────────────────────────────────────────────────
function aabe_add_link_headers() {
    if ( headers_sent() ) return;
    $links = [
        '</llms.txt>; rel="alternate"; type="text/markdown"',
        '</humans.txt>; rel="author"',
        '</.well-known/security.txt>; rel="security-policy"',
        '<https://policy.aabe.org.tw/>; rel="related"; title="政策知識庫"',
        '<https://advocacy.aabe.org.tw/>; rel="related"; title="倡議資料庫"',
    ];
    header( 'Link: ' . implode( ', ', $links ), false );
}
add_action( 'send_headers', 'aabe_add_link_headers' );

// ─────────────────────────────────────────────────────────
// 6. Markdown content negotiation（Accept: text/markdown 回 MD）
// ─────────────────────────────────────────────────────────
function aabe_markdown_negotiation() {
    if ( ! isset( $_SERVER['HTTP_ACCEPT'] ) ) return;
    if ( strpos( $_SERVER['HTTP_ACCEPT'], 'text/markdown' ) === false ) return;
    if ( ! is_singular() ) return;

    global $post;
    if ( ! $post ) return;

    header( 'Content-Type: text/markdown; charset=UTF-8' );
    header( 'X-Markdown-Source: WordPress' );

    echo "---\n";
    echo "title: " . wp_json_encode( get_the_title( $post ), JSON_UNESCAPED_UNICODE ) . "\n";
    echo "url: " . get_permalink( $post ) . "\n";
    echo "date: " . get_the_date( 'Y-m-d', $post ) . "\n";
    if ( has_excerpt( $post ) ) {
        echo "description: " . wp_json_encode( get_the_excerpt( $post ), JSON_UNESCAPED_UNICODE ) . "\n";
    }
    echo "source: 國教行動聯盟\n";
    echo "---\n\n";

    echo "# " . get_the_title( $post ) . "\n\n";

    // 簡單 HTML→Markdown：去 HTML tag、保留段落結構
    $content = apply_filters( 'the_content', $post->post_content );
    $content = preg_replace( '/<h2[^>]*>(.*?)<\/h2>/i', "\n## $1\n", $content );
    $content = preg_replace( '/<h3[^>]*>(.*?)<\/h3>/i', "\n### $1\n", $content );
    $content = preg_replace( '/<p[^>]*>(.*?)<\/p>/is', "$1\n\n", $content );
    $content = preg_replace( '/<a [^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)<\/a>/i', '[$2]($1)', $content );
    $content = strip_tags( $content );
    $content = html_entity_decode( $content, ENT_QUOTES, 'UTF-8' );
    $content = preg_replace( "/\n{3,}/", "\n\n", $content );
    echo trim( $content );

    echo "\n\n---\n";
    echo "**原始頁面**：" . get_permalink( $post ) . "\n";
    echo "**組織**：[國教行動聯盟](https://aabe.org.tw/)（成立於 2012 年）\n";

    exit;
}
add_action( 'template_redirect', 'aabe_markdown_negotiation', 1 );

// ─────────────────────────────────────────────────────────
// 7. IndexNow 自動 ping（新文章發布即通知 Bing）
// ─────────────────────────────────────────────────────────
function aabe_indexnow_ping( $post_id ) {
    if ( wp_is_post_revision( $post_id ) ) return;
    if ( get_post_status( $post_id ) !== 'publish' ) return;

    $key = '【請先建立 IndexNow key 並填這裡】'; // 詳見 indexnow-setup.md
    if ( strpos( $key, '【' ) === 0 ) return;

    $url = get_permalink( $post_id );
    $endpoint = 'https://api.indexnow.org/indexnow';
    $body = [
        'host' => 'aabe.org.tw',
        'key' => $key,
        'urlList' => [ $url ],
    ];

    wp_remote_post( $endpoint, [
        'body' => wp_json_encode( $body ),
        'headers' => [ 'Content-Type' => 'application/json' ],
        'timeout' => 10,
        'blocking' => false,
    ] );
}
add_action( 'publish_post', 'aabe_indexnow_ping' );
add_action( 'publish_page', 'aabe_indexnow_ping' );

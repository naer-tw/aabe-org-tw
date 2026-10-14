#!/usr/bin/env python3
"""10/14 兒少十大承諾起跑記者會「完整記錄」專頁產生器。

用法：
  python3 -I _source/events-record-1014/build.py            # 產 public/events/2026-10-14-child-pledge-launch/index.html（正式版）
  python3 -I _source/events-record-1014/build.py --preview OUT.html   # 另產自含圖片的本機預覽（含預覽橫幅與待補標示）

真源：
  - 發言全文  _source/events-record-1014/src_speeches.md（md5 154bd687…，與 新聞稿/2026-10-14_兒少十大承諾起跑記者會/raw/ 同檔）
  - 新聞稿正文 public/press/2026-10-14-child-pledge-launch/index.html（v6.2 會後版，直接複用正文段，不重排）
  - 人物照   新聞稿頁既有六張（不重裁、直接引用）＋ images/ 內五張（crop_photos.py）
發言只在此轉成 HTML，不改字；每段發言附「原檔出處」。
"""
import base64
import html
import mimetypes
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PAGE_DIR = os.path.join(ROOT, "public", "events", "2026-10-14-child-pledge-launch")
PRESS_HTML = os.path.join(ROOT, "public", "press", "2026-10-14-child-pledge-launch", "index.html")
SPEECHES = os.path.join(HERE, "src_speeches.md")

SITE = "https://aabe.org.tw"
PAGE_URL = SITE + "/events/2026-10-14-child-pledge-launch/"
PRESS_REL = "../../press/2026-10-14-child-pledge-launch/"
PRESS_URL = SITE + "/press/2026-10-14-child-pledge-launch/"
LIVE_URL = "https://youtube.com/live/gcj19AY5LHU"
DRIVE_URL = "https://drive.google.com/drive/folders/1XlaEUJJnRsw9OGUy7aJdmNvK_9p6CnKQ"
PUBLISHED = "2026-10-16"
LEGIS_NOTE = "以下為各立法委員於記者會現場的發言，屬其個人立場；本聯盟對所有參選人適用一致規則，不評分、不排名、不推薦任何人。"

E = lambda s: html.escape(s, quote=True)

# ---------------------------------------------------------------- 發言全文
def load_speeches():
    lines = open(SPEECHES, encoding="utf-8").read().split("\n")
    secs, cur = {}, None
    for ln in lines:
        m = re.match(r"^## (\d+)\. ", ln)
        if m:
            cur = int(m.group(1))
            secs[cur] = []
        elif ln.startswith("## 附錄"):
            cur = None
        elif cur is not None:
            secs[cur].append(ln)
    out = {}
    for n, body in secs.items():
        i = body.index("#### 全文")
        block = []
        for ln in body[i + 1:]:
            if ln.strip() == "---":
                break
            block.append(ln)
        out[n] = block
    return out


def bold(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def render_said(block):
    """把彙整檔的「全文」區塊轉成 HTML：空行分段、段內換行保留、** 轉粗體、### 轉小標。不改字。"""
    paras, cur = [], []
    for ln in block + [""]:
        if ln.strip() == "":
            if cur:
                paras.append(cur)
                cur = []
        else:
            cur.append(ln.strip())
    out = []
    for k, p in enumerate(paras):
        if p[0].startswith("### "):
            out.append("<h5>%s</h5>" % E(p[0][4:]))
            continue
        txt = "<br>\n".join(bold(E(x)) for x in p)
        if k == 0 and re.search(r"致詞稿", p[0]) and len(p) == 1:
            out.append('<p class="orig-title">%s</p>' % txt)
        else:
            out.append("<p>%s</p>" % txt)
    return "\n".join(out)


SRC_NEWS = "本人提供之第三人稱書面稿（新聞稿用），非現場逐字稿；文字與新聞稿頁相同。"
# (序, id, 姓名, 職稱, 群組, 狀態, 照片, alt, 原檔出處)
P = lambda f: ("press", f)
M = lambda f: ("mine", f)
SPEAKERS = [
    (1, "wang-hanyang", "王瀚陽", "國教行動聯盟理事長", "host", "全文（開場與收尾）", P("photo-wang-hanyang.jpg"),
     "國教行動聯盟理事長王瀚陽發言",
     "理事長提供之發言稿（2026-10-14）。本頁收錄開場與收尾兩段。"),
    (2, "chang-chueh", "張珏", "臺灣心理健康聯盟召集人", "host", "發言要點稿", P("photo-chang-chueh.jpg"),
     "臺灣心理健康聯盟召集人張珏發言",
     "張珏召集人提供之發言要點稿。原稿為要點式，含「(見附件 會後新聞稿)」「(p2)」「(p7-9)」等投影片頁碼註記，照登。"),
    (3, "chen-jing-hui", "陳菁徽", "立法委員", "legis", "全文", P("photo-chen-jing-hui.jpg"),
     "立法委員陳菁徽發言",
     "出席者提供之談話稿（談參 v2）。原文「我也要特別調」「每天生的環境」疑有漏字，照原文登出。"),
    (4, "wang-cheng-hsu", "王正旭", "立法委員", "legis", "全文", P("photo-wang-cheng-hsu.jpg"),
     "立法委員王正旭發言",
     "出席者提供之致詞稿（2026-10-14）。"),
    (5, "fan-yun", "范雲", "立法委員", "legis", "依新聞稿", P("photo-fan-yun.jpg"),
     "立法委員范雲發言",
     "理事長 10 月 14 日提供之新聞稿段。無發言稿原件，本段為第三人稱新聞稿文字，與新聞稿頁相同。"),
    (6, "liu-shu-pin", "劉書彬", "立法委員", "legis", "全文", P("photo-liu-shu-pin.jpg"),
     "立法委員劉書彬發言",
     "出席者提供之致詞稿（PDF）。原檔以「**」標示的粗體，本頁改以粗體顯示，文字照登。"),
    (7, "tao-lian-sheng", "陶蓮生", "全國家長會長聯盟理事長", "ngo", "依新聞稿", M("photo-tao-lian-sheng.jpg"),
     "全國家長會長聯盟理事長陶蓮生發言", SRC_NEWS),
    (8, "lin-jia-hui", "林嘉慧", "家庭韌性行動聯盟召集人", "ngo", "依新聞稿", M("photo-lin-jia-hui.jpg"),
     "家庭韌性行動聯盟召集人林嘉慧發言", SRC_NEWS + "原文「任林」照登。"),
    (9, "jian-xin-bin", "簡信斌", "中華民國中小學校長協會副理事長", "ngo", "依新聞稿", M("photo-jian-xin-bin.jpg"),
     "中華民國中小學校長協會副理事長簡信斌發言", SRC_NEWS + "原稿第一行職稱姓名與「表示」分行，照登。"),
    (10, "lin-ling-hua", "林玲華", "財團法人赤子心教育基金會董事長", "ngo", "依新聞稿", None,
     "", SRC_NEWS),
    (11, "zhen-rui-xing", "甄瑞興", "台灣青少年神經多樣性行動協會理事長", "ngo", "依新聞稿", M("photo-zhen-rui-xing.jpg"),
     "台灣青少年神經多樣性行動協會理事長甄瑞興發言", SRC_NEWS),
    (12, "cai-pei-hua", "蔡沛華", "中華公民人權協會理事長", "ngo", "依新聞稿", M("photo-cai-pei-hua.jpg"),
     "中華公民人權協會理事長蔡沛華發言", SRC_NEWS),
]
GROUPS = [
    ("host", "共同發起團體：主辦方開場與心理健康城市說明", "預排 10:02–10:08"),
    ("legis", "立法委員發言", "預排 10:08–10:14（依採訪通知列名順序）"),
    ("ngo", "共同發起團體代表發言", "預排 10:14–10:22"),
]
FLOW = [
    ("10:00–10:02", "主持人開場與介紹"),
    ("10:02–10:05", "王瀚陽：兒少十大承諾與公開追蹤"),
    ("10:05–10:08", "張珏：心理健康城市六項與跨局處治理"),
    ("10:08–10:14", "三黨立委回應，每人約 2 分鐘（依實際到場調整）"),
    ("10:14–10:16", "陶蓮生：家長及教育需求"),
    ("10:16–10:18", "林嘉慧：家庭韌性與社區支持"),
    ("10:18–10:22", "共同發起團體代表：簡信斌、林玲華、甄瑞興、蔡沛華"),
    ("10:22–10:27", "兩份承諾書交付、邀請立委協助轉達、展示合影"),
    ("10:27–10:30", "宣布回覆期限及後續公開時程"),
    ("10:30–10:40", "媒體提問與採訪"),
]
LEGIS = ["陳菁徽", "王正旭", "范雲", "劉書彬"]
SLOGANS = [
    "有人教、有人幫、有人顧、有人護！",
    "友善縣市，說到做到！",
    "心理健康，從小到老都要顧！",
]
GALLERY = [
    ("live-8664.jpg", "會議室內，出席者手持手舉板站立合影（遠景）"),
    ("live-8668.jpg", "出席者站成一排，手持寫有承諾項目的展示板合影"),
    ("live-8674.jpg", "出席者並排坐在會議桌後，背後是記者會主視覺背板"),
    ("live-8687.jpg", "一位發言者站立持麥克風，旁邊一人舉著一張圖卡"),
    ("live-8690.jpg", "主桌出席者並排就座，其中一人手持圖牌"),
    ("live-8696.jpg", "主桌出席者並排就座，後方為記者會背板"),
    ("live-8700.jpg", "會議室一角，出席者圍坐會議桌"),
    ("live-8710.jpg", "會議桌旁一位出席者持麥克風發言，其餘人坐在桌邊"),
]
MEDIA = []  # 10/15–16 聲量盤點後補：[(媒體, 標題, 連結, 日期)]

# ---------------------------------------------------------------- 新聞稿正文（複用官網頁）
def press_body():
    src = open(PRESS_HTML, encoding="utf-8").read()
    a = src.index('<p class="lead">')
    b = src.index('<section class="contact-section platform"')
    body = src[a:b]
    body = re.sub(r'\s*<figure class="photo portrait">.*?</figure>', "", body, flags=re.S)
    body = re.sub(r'\s*<div class="person-card">.*?</div>', "", body, flags=re.S)
    body = body.replace('<h2 class="section-h">', "<h3>").replace("</h2>", "</h3>")
    # 前兩段（lead + 第二段）預設展開，其餘收合
    ends = [m.end() for m in re.finditer(r"</p>", body)]
    head, rest = body[:ends[1]], body[ends[1]:]
    return head, rest


# ---------------------------------------------------------------- 區塊
def photo_src(ph):
    kind, f = ph
    return (PRESS_REL if kind == "press" else "images/") + f


def speaker_section(sp, said):
    n, sid, name, role, grp, status, ph, alt, src = sp
    if ph:
        fig = ('<figure class="pf"><img src="%s" width="480" height="640" alt="%s" loading="lazy">'
               '<figcaption>%s　%s</figcaption></figure>') % (photo_src(ph), E(alt), E(name), E(role))
    else:
        fig = ('<figure class="pf"><div class="pf-ph" aria-hidden="true">%s</div>'
               '<figcaption>%s　%s</figcaption></figure>') % (E(name[0]), E(name), E(role))
    return ('<article class="seg spk" id="spk-%s"><div class="segh"><span class="code">發言 %d</span>'
            '<span class="st">%s</span></div><div class="spkgrid">%s<div class="spkbody"><h4>%s<small>%s</small></h4>'
            '<div class="said">%s</div></div></div><p class="srcline"><b>原檔出處：</b>%s</p></article>'
            ) % (sid, n, E(status), fig, E(name), E(role), said, E(src))


def build(preview=False):
    speeches = load_speeches()
    head, rest = press_body()

    # ---- 流程與出席名單
    flow = "".join("<tr><th scope=\"row\">%s</th><td>%s</td></tr>" % (E(t), E(x)) for t, x in FLOW)
    att = (
        "<h3>共同發起民間團體發言代表</h3><ul class=\"people\">"
        + "".join("<li><b>%s</b><span>%s</span></li>" % (E(s[2]), E(s[3])) for s in SPEAKERS if s[4] != "legis")
        + "</ul><h3>出席立法委員（依採訪通知列名順序，同字級並列）</h3><ul class=\"people\">"
        + "".join("<li><b>%s</b><span>立法委員</span></li>" % E(x) for x in LEGIS)
        + "</ul><h3>共同發起團體出席（不發言）</h3><ul class=\"people\">"
        "<li><b>劉倩伃</b><span>中華民國兒童健康聯盟執行秘書</span></li>"
        "<li><b>莊凱仲</b><span>中華公民人權協會榮譽理事長</span></li></ul>"
    )

    # ---- 發言記錄
    sp_html = []
    for g, gtitle, gtime in GROUPS:
        sp_html.append('<h3 class="grp">%s<small>%s</small></h3>' % (E(gtitle), E(gtime)))
        if g == "legis":
            sp_html.append('<p class="note legisnote">%s</p>' % E(LEGIS_NOTE))
        for sp in SPEAKERS:
            if sp[4] == g:
                sp_html.append(speaker_section(sp, render_said(speeches[sp[0]])))
    chips = "".join('<a href="#spk-%s">%s</a>' % (s[1], E(s[2])) for s in SPEAKERS)

    # ---- 臉書
    fb = "".join(
        '<div class="fbcard"><b>%s</b><span class="who">立法委員</span>'
        '<p class="pending">貼文日期：待補<br>摘要：待補</p>'
        '<p class="pending">到臉書看原文：連結待補</p></div>' % E(x) for x in LEGIS)

    # ---- 口號
    slog = ('<p class="opener">孩子的事，縣市的事！</p><ol class="slogans">%s</ol>'
            '<p class="closer">候選人請回應！簽署要公開，承諾要追蹤！</p>'
            % "".join("<li>%s</li>" % E(s) for s in SLOGANS))
    phs = ('<div class="phs"><figure><img src="images/live-8711.jpg" width="1200" height="800" loading="lazy" '
           'alt="出席者手持手舉板、部分人舉起手合影（一）"><figcaption>現場出席者手持手舉板合影（一）</figcaption></figure>'
           '<figure><img src="images/live-8713.jpg" width="1200" height="800" loading="lazy" '
           'alt="出席者手持手舉板排成一列合影（二）"><figcaption>現場出席者手持手舉板合影（二）</figcaption></figure></div>')

    # ---- 相簿
    gal = "".join(
        '<a href="images/%s" target="_blank" rel="noopener"><img src="images/%s" width="1200" height="800" loading="lazy" alt="%s"></a>'
        % (f, f, E(a)) for f, a in GALLERY)

    # ---- 媒體
    if MEDIA:
        media = "".join('<li>%s｜<a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>' % (E(m), E(u), E(t), E(d))
                        for m, t, u, d in MEDIA)
        media_sec = ('<h3>媒體報導</h3><ul class="plain">%s</ul>' % media)
    elif preview:
        media_sec = '<h3>媒體報導</h3><p class="pending">（預覽專用）10/15–16 聲量盤點後補，正式版沒有資料就整段不放。</p>'
    else:
        media_sec = ""

    toc_items = [
        ("schedule", "記者會流程與出席名單"), ("speeches", "發言記錄（12 位）"), ("facebook", "立法委員臉書貼文"),
        ("slogans", "口號與合影"), ("gallery", "現場相簿"), ("press-release", "新聞稿正文"),
        ("documents", "文件與追蹤入口"), ("context", "脈絡與延伸"),
    ]
    toc = "".join('<li><a href="#%s"><b>%02d</b> %s</a></li>' % (i, k + 1, t) for k, (i, t) in enumerate(toc_items))

    preview_bar = ('<div class="previewbar">本機預覽（未上線）｜人物照與四位立委臉書連結仍待確認，不代表正式版。</div>' if preview else "")

    ld_event = """{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "兒少十大承諾起跑記者會",
  "description": "72 個民間團體共同發起《兒少十大承諾書》，《心理健康城市六項承諾書》同場發布，四位立法委員出席並接受文件，邀請 22 縣市長參選人逐項回應。",
  "startDate": "2026-10-14T10:00:00+08:00",
  "endDate": "2026-10-14T10:40:00+08:00",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "location": {"@type": "Place", "name": "立法院中興大樓 101 會議室", "address": {"@type": "PostalAddress", "streetAddress": "臺北市濟南路一段 3 之 1 號", "addressCountry": "TW"}},
  "image": ["%(site)s/press/2026-10-14-child-pledge-launch/photo-group.jpg"],
  "organizer": {"@type": "NGO", "name": "國教行動聯盟", "alternateName": "Action Alliance on Basic Education (AABE)", "url": "%(site)s/"},
  "url": "%(page)s"
}""" % {"site": SITE, "page": PAGE_URL}
    ld_article = """{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "@id": "%(page)s",
  "name": "兒少十大承諾起跑記者會 完整記錄",
  "inLanguage": "zh-TW",
  "datePublished": "%(pub)s",
  "primaryImageOfPage": {"@type": "ImageObject", "url": "%(site)s/press/2026-10-14-child-pledge-launch/photo-group.jpg"},
  "isPartOf": {"@type": "WebSite", "name": "國教行動聯盟", "url": "%(site)s/"},
  "about": {"@id": "%(press)s"},
  "mainEntity": {"@type": "Event", "name": "兒少十大承諾起跑記者會"}
}""" % {"site": SITE, "page": PAGE_URL, "pub": PUBLISHED, "press": PRESS_URL}

    page = TEMPLATE
    rep = {
        "%%PREVIEW_BAR%%": preview_bar,
        "%%FLOW%%": flow, "%%ATT%%": att, "%%CHIPS%%": chips, "%%SPEECHES%%": "\n".join(sp_html),
        "%%FB%%": fb, "%%SLOG%%": slog, "%%PHS%%": phs, "%%GAL%%": gal,
        "%%PRESS_HEAD%%": head, "%%PRESS_REST%%": rest, "%%MEDIA%%": media_sec, "%%TOC%%": toc,
        "%%LD_EVENT%%": ld_event, "%%LD_PAGE%%": ld_article,
        "%%LIVE%%": LIVE_URL, "%%DRIVE%%": DRIVE_URL, "%%PAGE_URL%%": PAGE_URL, "%%PRESS_URL%%": PRESS_URL,
        "%%PRESS_REL%%": PRESS_REL, "%%PUBLISHED%%": PUBLISHED, "%%SITE%%": SITE,
    }
    for k, v in rep.items():
        page = page.replace(k, v)
    assert "%%" not in page, re.findall(r"%%\w+%%", page)
    return page


def verbatim_check(page):
    """每一份發言全文的每一行（去 ** 記號）都必須原樣出現在頁面文字裡。"""
    plain = re.sub(r"<br>\n?", "\n", page)
    plain = html.unescape(re.sub(r"<[^>]+>", "", plain))
    speeches = load_speeches()
    bad, total = [], 0
    for n, block in speeches.items():
        if n not in [s[0] for s in SPEAKERS]:
            continue
        for ln in block:
            s = ln.strip().replace("**", "")
            if not s or s.startswith("### "):
                continue
            total += 1
            if s not in plain:
                bad.append((n, s[:40]))
    return total, bad


def to_inline(page):
    """預覽用：把頁內本機圖片換成 data URI（自含，可直接傳給理事長）。"""
    def sub(m):
        attr, path = m.group(1), m.group(2)
        fp = os.path.normpath(os.path.join(PAGE_DIR, path))
        if not os.path.exists(fp):
            raise SystemExit("缺圖：" + fp)
        mime = mimetypes.guess_type(fp)[0] or "image/jpeg"
        if attr == "href":
            return 'href="#gallery"'
        return 'src="data:%s;base64,%s"' % (mime, base64.b64encode(open(fp, "rb").read()).decode())
    return re.sub(r'(src|href)="((?:images/|\.\./\.\./press/)[^"]+\.(?:jpg|png|webp))"', sub, page)


# ---------------------------------------------------------------- 模板
TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>兒少十大承諾起跑記者會 完整記錄｜活動｜國教行動聯盟</title>
<meta name="description" content="2026 年 10 月 14 日兒少十大承諾起跑記者會完整記錄：12 位發言人的發言原文與照片、四位立法委員、口號與合影、現場相簿、新聞稿全文，以及兩份承諾書與各縣市簽署回覆入口。">
<link rel="canonical" href="%%PAGE_URL%%">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:title" content="兒少十大承諾起跑記者會 完整記錄｜國教行動聯盟">
<meta property="og:description" content="72 團體邀 22 縣市打造友善城市：發言原文、現場照片、新聞稿與兩份承諾書入口">
<meta property="og:image" content="%%SITE%%/press/2026-10-14-child-pledge-launch/photo-group.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="72 個民間團體代表與出席立委手持「簽了就公開、不評分不排名」「少子化不只中央的事」等手舉板合影，2026 年 10 月 14 日於立法院">
<meta property="og:type" content="website">
<meta property="og:url" content="%%PAGE_URL%%">
<meta property="og:site_name" content="國教行動聯盟">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="兒少十大承諾起跑記者會 完整記錄">
<meta name="twitter:image" content="%%SITE%%/press/2026-10-14-child-pledge-launch/photo-group.jpg">
<style>
:root{--paper:#FBF6EC;--paper-2:#F1E8D6;--ink:#22302B;--ink-2:#5E6E67;--pine:#1B4D3E;--pine-d:#123B30;--blue:#3D6B84;--blue-d:#2C4F63;--gold:#D9A441;--line:#E6DCC6;--line-2:#D6C9A9}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:-apple-system,"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;color:var(--ink);background:var(--paper);line-height:1.78;overflow-wrap:anywhere}
.previewbar{background:#B91C1C;color:#fff;text-align:center;font-size:.85rem;padding:6px 12px;font-weight:700}
.topbar{background:linear-gradient(135deg,#1B4D3E,#123B30);color:#fff;border-bottom:3px solid var(--gold)}
.topbar-inner{max-width:920px;margin:0 auto;padding:14px 20px}
.org{font-weight:800}.org a{color:inherit;text-decoration:none}.org-en{font-size:.72rem;opacity:.85}
.wrap{max-width:920px;margin:0 auto;padding:0 20px}
nav.breadcrumb{font-size:.84rem;color:var(--ink-2);padding:16px 0 4px}nav.breadcrumb a{color:var(--blue-d)}
.hero{margin:14px 0;border-radius:18px;padding:34px 32px;background:linear-gradient(150deg,#1B4D3E,#0E2E26);color:#F3F8F4}
.hero .kicker{font-size:.9rem;font-weight:800;color:#FDEBCB;letter-spacing:.06em;margin:0 0 8px}
.hero h1{font-size:1.9rem;line-height:1.35;margin:0 0 12px;font-weight:900}
.hero .sub{font-size:1.05rem;margin:0 0 12px;color:#E8F1EC}
.hero .meta{font-size:.92rem;color:#FDEBCB;margin:2px 0}
.hero .lead{margin:14px 0 0;font-size:.98rem;color:#F3F8F4}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.btn{display:inline-block;padding:11px 22px;border-radius:9px;font-weight:800;text-decoration:none;min-height:44px}
.btn.p{background:var(--gold);color:#3a2a06}.btn.g{border:1px solid rgba(255,255,255,.55);color:#fff}
.btn.d{background:var(--pine);color:#fff}.btn.o{border:1px solid var(--pine);color:var(--pine-d);background:#fff}
.note{background:#fff;border:1px solid var(--line);border-left:5px solid var(--gold);border-radius:12px;padding:16px 20px;margin:14px 0;font-size:.95rem}
.toc{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:14px 0}
.toc h2{font-size:1.1rem;margin:0 0 8px;border:0}
.toc ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:4px 18px}
.toc a{color:var(--blue-d);text-decoration:none;display:block;padding:7px 0}.toc b{color:var(--pine);margin-right:6px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;padding-top:10px;border-top:1px dashed var(--line)}
.chips a{font-size:.85rem;padding:6px 12px;border-radius:999px;background:var(--paper-2);color:var(--pine-d);text-decoration:none;font-weight:700;min-height:32px}
.seg{background:#fff;border:1px solid var(--line);border-top:5px solid var(--pine);border-radius:12px;padding:20px 24px;margin:16px 0;scroll-margin-top:12px}
.segh{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:.82rem}
.code{background:var(--pine);color:#fff;font-weight:900;padding:2px 10px;border-radius:6px}
.st{background:var(--paper-2);border-radius:999px;padding:1px 10px;font-weight:700;color:var(--pine-d)}
.seg h2,h2.sec{font-size:1.3rem;margin:8px 0 10px}
h2.sec{margin:34px 0 4px;scroll-margin-top:12px}
.seg h3{font-size:1.02rem;margin:18px 0 6px;color:var(--pine)}
h3.grp{font-size:1.15rem;margin:30px 0 4px;padding-left:12px;border-left:5px solid var(--gold);color:var(--pine-d)}
h3.grp small{display:block;font-size:.8rem;font-weight:500;color:var(--ink-2)}
.spkgrid{display:grid;grid-template-columns:200px minmax(0,1fr);gap:22px;align-items:start;margin-top:10px}
.pf{margin:0}.pf img,.pf-ph{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:10px;background:var(--paper-2)}
.pf-ph{display:flex;align-items:center;justify-content:center;font-size:4rem;font-weight:900;color:var(--pine);border:1px dashed var(--line-2)}
.pf figcaption{font-size:.8rem;color:var(--ink-2);margin-top:6px;line-height:1.5}
.spkbody h4{font-size:1.3rem;margin:0 0 8px;color:var(--pine-d)}.spkbody h4 small{display:block;font-size:.85rem;font-weight:500;color:var(--ink-2);margin-top:2px}
.said h5{font-size:1rem;margin:16px 0 4px;color:var(--pine)}
.said p{margin:0 0 .95em}.said .orig-title{font-size:.85rem;color:var(--ink-2)}
.srcline{font-size:.8rem;color:var(--ink-2);border-top:1px dashed var(--line);margin:14px 0 0;padding-top:8px}
.legisnote{margin:6px 0 4px}
table.flow{width:100%;border-collapse:collapse;font-size:.95rem}
table.flow th{width:7.5em;text-align:left;vertical-align:top;color:var(--pine);font-variant-numeric:tabular-nums;padding:6px 10px 6px 0;white-space:nowrap}
table.flow td{padding:6px 0;border-bottom:1px solid var(--line)}table.flow tr:last-child td{border-bottom:0}
.flowhint{font-size:.82rem;color:var(--ink-2);margin:8px 0 0}
ul.people{list-style:none;margin:0 0 6px;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:4px 18px}
ul.people li{display:flex;flex-direction:column;padding:4px 0}ul.people b{color:var(--pine)}ul.people span{font-size:.84rem;color:var(--ink-2)}
.fbgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}
.fbcard{border:1px solid var(--line);border-radius:10px;padding:12px 16px;background:var(--paper)}
.fbcard b{font-size:1.05rem;color:var(--pine-d);margin-right:8px}.fbcard .who{font-size:.8rem;color:var(--ink-2)}
.pending{color:var(--ink-2);background:var(--paper);border:1px dashed var(--line-2);border-radius:8px;padding:8px 14px;margin:8px 0 0;font-size:.9rem}
.slogans{margin:6px 0;padding-left:1.4em;font-size:1.2rem;font-weight:800;color:var(--pine-d)}.slogans li{margin:4px 0}
.opener,.closer{font-size:1.25rem;font-weight:900;color:var(--pine-d);margin:8px 0}.closer{margin-bottom:0}
.phs{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0 0}
.phs figure{margin:0;min-width:0}.phs img{display:block;width:100%;height:auto;border-radius:8px;background:var(--paper-2)}
.phs figcaption{font-size:.84rem;color:var(--ink-2);margin-top:6px;line-height:1.6}
.gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px;margin:12px 0}
.gal a{display:block;border-radius:8px;overflow:hidden;background:var(--paper-2)}.gal img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover}
details.more{margin-top:8px}details.more summary{cursor:pointer;font-weight:800;color:var(--blue-d);padding:10px 0;min-height:44px}
.presstext p{margin:0 0 1em}.presstext h3{font-size:1.05rem;margin:20px 0 6px;color:var(--pine)}.presstext a{color:var(--blue-d)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}
.card{display:block;border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:var(--paper);text-decoration:none;color:var(--ink)}
.card b{display:block;color:var(--pine-d);margin-bottom:2px}.card span{font-size:.85rem;color:var(--ink-2)}
ul.plain{margin:6px 0;padding-left:1.2em}
.rules{font-size:.95rem;margin:14px 0 0;padding:10px 14px;background:var(--paper);border-radius:8px;border:1px solid var(--line)}
.contact{font-size:.92rem}.contact ul{margin:4px 0;padding-left:1.2em}
.cite{font-size:.82rem;color:var(--ink-2);margin:14px 0}
footer{margin-top:40px;background:#1B2420;color:#c3ccc6;font-size:.86rem}footer .wrap{padding:26px 20px}footer a{color:var(--gold)}
a:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
@media(max-width:680px){.hero{padding:26px 20px}.hero h1{font-size:1.45rem}.toc ul,ul.people,.fbgrid,.cards,.phs{grid-template-columns:minmax(0,1fr)}.seg{padding:16px 16px}.spkgrid{grid-template-columns:minmax(0,1fr)}.pf{max-width:220px}table.flow th{white-space:normal;width:6.5em}}
</style>
<script type="application/ld+json">
%%LD_EVENT%%
</script>
<script type="application/ld+json">
%%LD_PAGE%%
</script>
</head>
<body>
%%PREVIEW_BAR%%
<header class="topbar"><div class="topbar-inner"><div class="org"><a href="https://aabe.org.tw/" aria-label="回國教行動聯盟官網">國教行動聯盟　Action Alliance on Basic Education</a></div><div class="org-en">AABE · 民間團體</div></div></header>
<div class="wrap">
<nav class="breadcrumb" aria-label="麵包屑導航"><a href="https://aabe.org.tw/">首頁</a> / <a href="https://aabe.org.tw/events/">活動</a> / <span>兒少十大承諾起跑記者會 完整記錄</span></nav>
<div class="hero" id="top">
<p class="kicker">2026.10.14　兒少十大承諾起跑記者會　完整記錄</p>
<h1>少子化不只中央的事　72團體邀22縣市打造友善城市</h1>
<p class="sub">兒少十大、全年齡心理健康城市六項承諾同步發布　邀三黨立委協助轉達</p>
<p class="meta"><time datetime="2026-10-14T10:00:00+08:00">2026 年 10 月 14 日（三）上午 10:00</time>　立法院中興大樓 101 會議室</p>
<p class="meta">發起與主辦：國教行動聯盟（民間團體），與臺灣心理健康聯盟同場發布</p>
<p class="lead">72 個民間團體共同發起《兒少十大承諾書》，《心理健康城市六項承諾書》同場發布，四位立法委員出席並接受文件，邀請 22 縣市長參選人逐項回應。兩份承諾書回覆期限為 11 月 11 日下午 6 時，預定 11 月 18 日公布兒少十大承諾書回覆結果。本頁收錄各位發言原文、現場照片與相關連結。</p>
<div class="btns"><a class="btn p" href="%%LIVE%%" target="_blank" rel="noopener">看記者會直播</a><a class="btn g" href="%%PRESS_URL%%">看新聞稿</a><a class="btn g" href="https://aabe.org.tw/act/child-pledge/record/">各縣市簽署與回覆</a></div>
</div>
<div class="note">本頁依出席者提供之講稿、本聯盟新聞稿、採訪通知與現場照片整理。發言全文照原稿登載、不改字；原稿中的「候選人」用語照登，本聯盟稱「參選人」。各位立法委員的發言屬其個人立場；接受文件不代表立委或政黨已簽署或背書。本聯盟對所有參選人適用一致規則：不評分、不排名、不推薦任何人。</div>
<nav class="toc" aria-label="段落目錄"><h2>段落目錄</h2><ul>%%TOC%%</ul><div class="chips" aria-label="直接看某位發言">%%CHIPS%%</div></nav>

<section class="seg" id="schedule"><div class="segh"><span class="code">01</span><span class="st">依採訪通知整理</span></div><h2>記者會流程與出席名單</h2>
<table class="flow"><tbody>%%FLOW%%</tbody></table>
<p class="flowhint">以上為採訪通知預排流程，實際先後與時間以現場為準。</p>
%%ATT%%
</section>

<h2 class="sec" id="speeches"><span class="code" style="font-size:.8rem;margin-right:8px">02</span>發言記錄</h2>
<p style="margin:0 0 4px;color:var(--ink-2);font-size:.92rem">依採訪通知預排順序，一人一段；每段末附「原檔出處」。</p>
%%SPEECHES%%

<section class="seg" id="facebook"><div class="segh"><span class="code">03</span><span class="st">只連結，不轉貼全文</span></div><h2>立法委員臉書貼文</h2>
<p style="margin:0;font-size:.95rem">四位立法委員於記者會當天在個人臉書的貼文，僅提供連結；貼文屬各委員個人，內容與立場由各委員自行負責。</p>
<div class="fbgrid">%%FB%%</div></section>

<section class="seg" id="slogans"><div class="segh"><span class="code">04</span></div><h2>口號與合影</h2>
%%SLOG%%
%%PHS%%</section>

<section class="seg" id="gallery"><div class="segh"><span class="code">05</span></div><h2>現場相簿</h2>
<p style="margin:0;font-size:.95rem">點圖開大圖；更多現場照片放在雲端硬碟，知道連結即可檢視。</p>
<div class="gal">%%GAL%%</div>
<a class="btn o" href="%%DRIVE%%" target="_blank" rel="noopener">更多現場照片（Google 雲端硬碟）</a></section>

<section class="seg" id="press-release"><div class="segh"><span class="code">06</span><span class="st">與新聞稿頁同一正文</span></div><h2>新聞稿正文</h2>
<div class="presstext">%%PRESS_HEAD%%
<details class="more"><summary>展開新聞稿全文</summary>%%PRESS_REST%%</details></div>
<p style="margin:14px 0 0"><a class="btn d" href="%%PRESS_REL%%attachments/07_press-release.pdf">下載新聞稿 PDF</a>　<a class="btn o" href="%%PRESS_URL%%">回新聞稿頁</a></p></section>

<section class="seg" id="documents"><div class="segh"><span class="code">07</span></div><h2>文件與追蹤入口</h2>
<div class="cards">
<a class="card" href="https://aabe.org.tw/act/child-pledge/"><b>兒少十大承諾書</b><span>全文、共同發起團體與回傳方式</span></a>
<a class="card" href="https://aabe.org.tw/act/mental-health-city/"><b>心理健康城市六項承諾書</b><span>臺灣心理健康聯盟與國教盟同場發布</span></a>
<a class="card" href="%%PRESS_URL%%attachments/"><b>記者會文件</b><span>兩份承諾書、四份附件、各團體書面意見與政策資料</span></a>
<a class="card" href="https://aabe.org.tw/act/child-pledge/record/"><b>各縣市簽署與回覆</b><span>兒少十大承諾公開平台</span></a>
</div>
<p class="rules">所有參選人適用一致規則：<strong>不評分、不排名、不推薦任何人</strong>。</p></section>

<section class="seg" id="context"><div class="segh"><span class="code">08</span></div><h2>脈絡與延伸</h2>
<div class="cards"><a class="card" href="../2026-10-02-mental-health-city-forum/record/"><b>10/2 心理健康城市網絡論壇　會後記錄</b><span>臺灣心理健康聯盟主辦；本頁只連結，不複製內容</span></a></div>
%%MEDIA%%
<div class="contact"><h3>聯絡資訊</h3><ul>
<li>新聞聯絡人：國教行動聯盟理事長 王瀚陽　0983-097-165</li>
<li>承諾書回覆窗口：國教行動聯盟秘書長 李睿澤　0921-113-066</li>
<li>回覆信箱：action.a.e0626@gmail.com</li></ul></div>
<p class="cite">引用格式（APA 7）：國教行動聯盟（2026，10 月 14 日）。<i>兒少十大承諾起跑記者會 完整記錄</i>［活動記錄］。<a href="%%PAGE_URL%%">%%PAGE_URL%%</a></p>
</section>
</div>
<footer><div class="wrap"><div>國教行動聯盟（民間團體）· Action Alliance on Basic Education (AABE)</div><p style="margin:6px 0 0"><a href="https://aabe.org.tw/events/">更多活動</a>　·　<a href="https://aabe.org.tw/">aabe.org.tw</a></p></div></footer>
</body>
</html>
"""

if __name__ == "__main__":
    prod = build(preview=False)
    total, bad = verbatim_check(prod)
    print("verbatim lines checked:", total, "missing:", len(bad), bad[:5])
    if bad:
        sys.exit(1)
    open(os.path.join(PAGE_DIR, "index.html"), "w", encoding="utf-8").write(prod)
    print("wrote", os.path.join(PAGE_DIR, "index.html"), len(prod))
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        pv = to_inline(build(preview=True))
        open(out, "w", encoding="utf-8").write(pv)
        print("preview", out, len(pv))

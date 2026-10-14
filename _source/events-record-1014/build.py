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

# ---------------------------------------------------------------- 一句引言（≤40 字；全部取自新聞稿頁正文，逐字）
# 標 B＝新聞稿已加粗句；標 P＝新聞稿正文內非加粗句（該人無加粗句或加粗句超過 40 字，取新聞稿同一段內完整句）
QUOTES = {
    "wang-hanyang": ("一座城市如何對待孩子與家庭，決定了這座城市的未來。", "B"),
    "chang-chueh": ("心理健康城市不是只有兒童、青少年或育兒家庭的議題，而是涵蓋全年齡市民的共同需求。", "P"),
    "chen-jing-hui": ("不能將所有責任與壓力轉嫁給第一線教師", "B"),
    "wang-cheng-hsu": ("沒有資源支撐的承諾只是空頭支票", "B"),
    "fan-yun": ("投資兒少，就是投資台灣的未來", "B"),
    "liu-shu-pin": ("政府不能等到孩子出現憂鬱症狀、家庭陷入困境，才開始提供協助", "B"),
    "tao-lian-sheng": ("讓老師安心教學、家長放心託付、孩子穩定學習", "B"),
    "lin-jia-hui": ("孩子的成長不只是家庭的責任，更需要學校、社區與政府共同支持", "P"),
    "jian-xin-bin": ("政策不能只增加學校責任，更要同步提供人力、經費與專業支持", "P"),
    "lin-ling-hua": ("孩子需要的協助不能等到正式鑑定完成才開始", "B"),
    "zhen-rui-xing": ("支持不能只停在診間或教室，更要延伸到孩子每天的生活", "P"),
    "cai-pei-hua": ("孩子不只是等待被保護的對象，更是城市未來的參與者。", "B"),
}
WALL_ORDER = ["chen-jing-hui", "wang-cheng-hsu", "fan-yun", "liu-shu-pin",
              "wang-hanyang", "chang-chueh", "tao-lian-sheng", "lin-jia-hui",
              "jian-xin-bin", "lin-ling-hua", "zhen-rui-xing", "cai-pei-hua"]
CANDIDATE_NOTE = "本頁依出席者提供之講稿、本聯盟新聞稿、採訪通知與現場照片整理。發言全文照原稿登載、不改字；原稿中的「候選人」用語照登，本聯盟稱「參選人」。各位立法委員的發言屬其個人立場；接受文件不代表立委或政黨已簽署或背書。本聯盟對所有參選人適用一致規則：不評分、不排名、不推薦任何人。"


def press_body():
    """新聞稿頁正文（v6.2 官網版）：只拿掉與本頁重複的人物照與人名卡；文字不動。"""
    src = open(PRESS_HTML, encoding="utf-8").read()
    a = src.index('<p class="lead">')
    b = src.index('<section class="contact-section platform"')
    body = src[a:b]
    body = re.sub(r'\s*<figure class="photo portrait">.*?</figure>', "", body, flags=re.S)
    body = re.sub(r'\s*<div class="person-card">.*?</div>', "", body, flags=re.S)
    body = body.replace('<h2 class="section-h">', "<h3>").replace("</h2>", "</h3>")
    body = body.replace("聯合72個民間團體", '聯合<span data-metric="child_pledge_cosponsor_orgs">72</span>個民間團體')
    return body


def press_plain():
    src = open(PRESS_HTML, encoding="utf-8").read()
    return html.unescape(re.sub(r"<[^>]+>", "", src)), src


def photo_src(ph):
    kind, f = ph
    return (PRESS_REL if kind == "press" else "images/") + f


# 卡片方形窗的臉部中心（占 3:4 原圖的百分比；2026-10-14 對縮圖估），讓人臉居中、背板字少入鏡
FACE = {"chen-jing-hui": (47, 48, 1.25), "wang-cheng-hsu": (50, 55, 1.25), "fan-yun": (50, 46, 1.25),
        "liu-shu-pin": (47, 53, 1.25), "wang-hanyang": (50, 36, 1.5), "chang-chueh": (45, 30, 1.45),
        "tao-lian-sheng": (48, 45, 1.25), "lin-jia-hui": (48, 42, 1.25), "jian-xin-bin": (50, 20, 1.25),
        "zhen-rui-xing": (50, 22, 1.25), "cai-pei-hua": (45, 26, 1.25)}


def face_style(sid):
    fx, fy, sc = FACE[sid]
    start = min(max(fy - 37.5, 0), 25)          # 方形窗佔原圖高 75%，起點 0–25%
    op = start / 25 * 100
    oy = (fy - start) / 75 * 100                # 臉在窗內的縱向位置，當縮放原點
    return "object-position:50%% %.0f%%;transform-origin:%d%% %.0f%%;--zs:%s" % (op, fx, oy, sc)


def card(sp, said):
    n, sid, name, role, grp, status, ph, alt, src = sp
    q, kind = QUOTES[sid]
    if ph:
        fig = ('<figure class="pf"><img src="%s" width="480" height="640" alt="%s" loading="lazy" style="%s"></figure>'
               % (photo_src(ph), E(alt), face_style(sid)))
    else:
        fig = '<figure class="pf"><div class="pf-ph" aria-hidden="true">%s</div></figure>' % E(name[0])
    return (
        '<article class="pcard" id="p-%(sid)s">%(fig)s<div class="pbody">'
        '<button type="button" class="bshare" data-id="p-%(sid)s" aria-label="複製%(name)s發言的網址">'
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M16 6l-4-4-4 4M12 2v13"/></svg>'
        '<span class="vh">分享</span></button>'
        '<h4>%(name)s</h4><p class="prole">%(role)s</p>'
        '<blockquote class="pq">「%(q)s」</blockquote>'
        '<details class="pfull"><summary>完整發言</summary>'
        '<div class="said">%(said)s</div><p class="srcline"><b>原檔出處：</b>%(src)s</p></details>'
        '<p class="pstat">%(status)s</p>'
        '</div></article>'
    ) % {"sid": sid, "fig": fig, "name": E(name), "role": E(role), "q": E(q), "status": E(status), "said": said, "src": E(src)}


def build(preview=False):
    speeches = load_speeches()
    by_id = {s[1]: s for s in SPEAKERS}
    body = press_body()

    cards = {sid: card(by_id[sid], render_said(speeches[by_id[sid][0]])) for sid in WALL_ORDER}
    wall = (
        '<h3 class="grp">出席立法委員（4）<small>依採訪通知列名順序，四位同版面、同字級</small></h3>'
        '<p class="legisnote">%s</p><div class="wall">%s</div>'
        '<h3 class="grp">共同發起團體代表（8）<small>依預排發言順序</small></h3><div class="wall">%s</div>'
    ) % (E(LEGIS_NOTE), "".join(cards[s] for s in WALL_ORDER[:4]), "".join(cards[s] for s in WALL_ORDER[4:]))

    flow = "".join('<tr><th scope="row">%s</th><td>%s</td></tr>' % (E(t), E(x)) for t, x in FLOW)
    att = (
        "<h4>共同發起民間團體發言代表</h4><ul class=\"people\">"
        + "".join("<li><b>%s</b><span>%s</span></li>" % (E(s[2]), E(s[3])) for s in SPEAKERS if s[4] != "legis")
        + "</ul><h4>出席立法委員（依採訪通知列名順序，同字級並列）</h4><ul class=\"people\">"
        + "".join("<li><b>%s</b><span>立法委員</span></li>" % E(x) for x in LEGIS)
        + "</ul><h4>共同發起團體出席（不發言）</h4><ul class=\"people\">"
        "<li><b>劉倩伃</b><span>中華民國兒童健康聯盟執行秘書</span></li>"
        "<li><b>莊凱仲</b><span>中華公民人權協會榮譽理事長</span></li></ul>"
    )
    slog = ('<p class="opener">孩子的事，縣市的事！</p><ol class="slogans">%s</ol>'
            '<p class="closer">候選人請回應！簽署要公開，承諾要追蹤！</p>'
            % "".join("<li>%s</li>" % E(s) for s in SLOGANS))
    phs = ('<div class="phs"><figure><img src="images/live-8711.jpg" width="1200" height="800" loading="lazy" '
           'alt="出席者手持手舉板、部分人舉起手合影（一）"><figcaption>現場出席者手持手舉板合影（一）</figcaption></figure>'
           '<figure><img src="images/live-8713.jpg" width="1200" height="800" loading="lazy" '
           'alt="出席者手持手舉板排成一列合影（二）"><figcaption>現場出席者手持手舉板合影（二）</figcaption></figure></div>')
    gal_items = ['<a href="images/%s" target="_blank" rel="noopener"><img src="images/%s" width="1200" height="800" loading="lazy" alt="%s"></a>'
                 % (f, f, E(a)) for f, a in GALLERY]
    gal = ('<div class="gal">%s</div><details class="sub"><summary>另 %d 張</summary><div class="gal">%s</div></details>'
           % ("".join(gal_items[:6]), len(gal_items) - 6, "".join(gal_items[6:])))

    if MEDIA:
        media = "".join('<li>%s｜<a href="%s" target="_blank" rel="noopener">%s</a>（%s）</li>' % (E(m), E(u), E(t), E(d))
                        for m, t, u, d in MEDIA)
        media_blk = ('<details class="blk" id="media"><summary><span class="ttl">媒體報導</span><span class="cnt">%d</span></summary>'
                     '<div class="inner"><ul class="plain">%s</ul></div></details>' % (len(MEDIA), media))
    elif preview:
        media_blk = ('<details class="blk" id="media"><summary><span class="ttl">媒體報導</span><span class="cnt">上線後補</span></summary>'
                     '<div class="inner"><p class="pending">（預覽專用）10/15–16 聲量盤點後補，正式版沒有資料就整段不放。</p></div></details>')
    else:
        media_blk = ('<details class="blk" id="media"><summary><span class="ttl">媒體報導</span><span class="cnt">10/15–16 補</span></summary>'
                     '<div class="inner"><p class="pending">各媒體報導的連結與標題，10 月 15 至 16 日整理後補上。</p></div></details>')

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
    ld_page = """{
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
        "%%PREVIEW_BAR%%": ('<div class="previewbar">本機預覽（未上線）｜不代表正式版。</div>' if preview else ""),
        "%%WALL%%": wall, "%%FLOW%%": flow, "%%ATT%%": att, "%%SLOG%%": slog, "%%PHS%%": phs,
        "%%GAL%%": gal, "%%PRESS%%": body, "%%MEDIA%%": media_blk, "%%NOTE%%": E(CANDIDATE_NOTE),
        "%%GALN%%": str(len(GALLERY) + 2),
        "%%LD_EVENT%%": ld_event, "%%LD_PAGE%%": ld_page,
        "%%LIVE%%": LIVE_URL, "%%DRIVE%%": DRIVE_URL, "%%PAGE_URL%%": PAGE_URL, "%%PRESS_URL%%": PRESS_URL,
        "%%PRESS_REL%%": PRESS_REL, "%%PUBLISHED%%": PUBLISHED, "%%SITE%%": SITE,
    }
    for k, v in rep.items():
        page = page.replace(k, v)
    assert "%%" not in page, re.findall(r"%%\w+%%", page)
    return page


def verbatim_check(page):
    """① 每份發言全文的每一行（去 ** 記號）必須原樣出現在頁面文字；② 12 句引言必須逐字出現在新聞稿頁，且 ≤40 字（含標點、不含引號）。"""
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
    pp, praw = press_plain()
    qbad = []
    for sid, (q, kind) in QUOTES.items():
        if q not in pp:
            qbad.append((sid, "不在新聞稿"))
        if len(q) > 40:
            qbad.append((sid, "超過 40 字 %d" % len(q)))
        inbold = ("<strong>%s" % q.rstrip("。")) in praw or ("<strong>" in praw and re.search(r"<strong>[^<]*%s" % re.escape(q.rstrip("。")), praw))
        if kind == "B" and not inbold:
            qbad.append((sid, "標 B 但不在加粗句內"))
    return total, bad + qbad


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


# ---------------------------------------------------------------- 模板（一頁三層）
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
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:56px}
body{margin:0;font-family:-apple-system,"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;color:var(--ink);background:var(--paper);line-height:1.75;overflow-wrap:anywhere}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.previewbar{background:#B91C1C;color:#fff;text-align:center;font-size:.85rem;padding:6px 12px;font-weight:700}
.topbar{background:linear-gradient(135deg,#1B4D3E,#123B30);color:#fff;border-bottom:3px solid var(--gold)}
.topbar-inner{max-width:920px;margin:0 auto;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.org{font-weight:800;font-size:.95rem}.org a{color:inherit;text-decoration:none}.org-en{font-size:.7rem;opacity:.85}
.tools{display:flex;gap:8px}
.tb{font:inherit;font-size:.82rem;font-weight:700;padding:6px 12px;min-height:36px;border-radius:8px;border:1px solid rgba(255,255,255,.55);background:transparent;color:#fff;cursor:pointer}
.tb:hover{background:rgba(255,255,255,.12)}
.wrap{max-width:920px;margin:0 auto;padding:0 16px}
.breadcrumb{font-size:.8rem;color:var(--ink-2);padding:8px 0 0;line-height:1.4}.breadcrumb a{color:var(--blue-d)}
.hero{margin:6px 0 0;border-radius:16px;overflow:hidden;background:linear-gradient(150deg,#1B4D3E,#0E2E26);color:#F3F8F4}
.hero img{display:block;width:100%;height:auto;aspect-ratio:1200/470;object-fit:cover;object-position:50% 40%;background:var(--paper-2)}
.hero .in{padding:20px 22px 22px}
.hero .kicker{font-size:.85rem;font-weight:800;color:#FDEBCB;letter-spacing:.05em;margin:0 0 4px}
.hero h1{font-size:1.7rem;line-height:1.35;margin:0 0 6px;font-weight:900}
.hero .sub{font-size:1rem;margin:0 0 6px;color:#E8F1EC}
.hero .meta{font-size:.88rem;color:#FDEBCB;margin:0 0 12px}
.facts{list-style:none;margin:0 0 12px;padding:0;font-size:1.2rem;font-weight:800;line-height:1.5}
.facts li{padding:4px 0;border-top:1px solid rgba(255,255,255,.18)}.facts li:first-child{border-top:0}
.slogan{font-size:1.15rem;font-weight:900;color:var(--gold);margin:0 0 14px}
.btns{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.btn{display:inline-block;padding:11px 20px;border-radius:9px;font-weight:800;text-decoration:none;min-height:44px;font-size:.95rem}
.btn.p{background:var(--gold);color:#3a2a06}.btn.g{border:1px solid rgba(255,255,255,.6);color:#fff}
.btn.d{background:var(--pine);color:#fff}.btn.o{border:1px solid var(--pine);color:var(--pine-d);background:#fff}
.tlink{color:#FDEBCB;font-weight:700;text-decoration:underline;text-underline-offset:3px;padding:10px 4px;min-height:44px;display:inline-flex;align-items:center}
nav.sticky{position:sticky;top:0;z-index:30;background:rgba(251,246,236,.96);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);margin:0 -16px;padding:0 16px}
nav.sticky ul{list-style:none;margin:0;padding:0;display:flex;max-width:920px;margin:0 auto}
nav.sticky li{flex:1}
nav.sticky a{display:block;text-align:center;padding:12px 4px;min-height:48px;color:var(--pine-d);font-weight:800;text-decoration:none;font-size:.95rem}
nav.sticky a:hover{background:var(--paper-2)}
h2.sec{font-size:1.3rem;margin:18px 0 2px;color:var(--pine-d);scroll-margin-top:56px}
h3.grp{font-size:1.1rem;margin:20px 0 4px;padding-left:12px;border-left:5px solid var(--gold);color:var(--pine-d)}
h3.grp small{display:block;font-size:.78rem;font-weight:500;color:var(--ink-2)}
.legisnote{margin:6px 0 10px;font-size:.74rem;line-height:1.5;color:var(--ink-2)}
.wall{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:10px 0 0}
.pcard{position:relative;display:grid;grid-template-columns:minmax(0,1fr);grid-template-rows:auto 1fr;align-content:start;background:#fff;border:1px solid var(--line);border-top:4px solid var(--pine);border-radius:12px;padding:10px;scroll-margin-top:60px}
.pcard .pf{margin:0;overflow:hidden;border-radius:8px}.pf img{transform:scale(var(--zs,1.25))}.pf img,.pf-ph{display:block;width:100%;height:auto;aspect-ratio:1/1;object-fit:cover;object-position:50% 12%;border-radius:8px;background:var(--paper-2)}
.pf-ph{display:flex;align-items:center;justify-content:center;font-size:3.2rem;font-weight:900;color:var(--pine);border:1px dashed var(--line-2)}
.pbody{min-width:0;padding-top:6px}
.pcard h4{font-size:1.05rem;margin:0;color:var(--pine-d)}
.prole{font-size:.8rem;color:var(--ink-2);margin:0 0 4px;line-height:1.4}
.pq{flex:1;margin:0 0 6px;padding:0;font-size:.86rem;line-height:1.5;color:var(--ink)}
.bshare{position:absolute;top:18px;right:18px;width:40px;height:40px;border-radius:50%;border:0;background:rgba(255,255,255,.92);color:var(--pine-d);display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.25)}
.bshare:hover{background:#fff}.bshare.done::after{content:"已複製";position:absolute;top:44px;right:0;font-size:.72rem;background:var(--pine-d);color:#fff;border-radius:6px;padding:2px 8px;white-space:nowrap}
details.pfull summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;white-space:nowrap;min-height:44px;padding:6px 10px;border-radius:9px;background:var(--pine);color:#fff;font-weight:800;font-size:.9rem;text-align:center}
details.pfull summary::-webkit-details-marker{display:none}
details.pfull summary::after{content:"＋";font-weight:900}details.pfull[open] summary::after{content:"－"}
.pbody{display:flex;flex-direction:column}.pbody details.pfull{order:1}.pstat{order:2;font-size:.72rem;color:var(--ink-2);text-align:center;margin:4px 0 0;line-height:1.4}
details.pfull[open]~.pstat{display:none}
.said{margin-top:12px;font-size:1rem}.said h5{font-size:1rem;margin:16px 0 4px;color:var(--pine)}
.said p{margin:0 0 .95em}.said .orig-title{font-size:.85rem;color:var(--ink-2)}
.srcline{font-size:.8rem;color:var(--ink-2);border-top:1px dashed var(--line);margin:10px 0 0;padding-top:8px}
.pcard.open{grid-column:1/-1;grid-template-columns:190px minmax(0,1fr);column-gap:22px;border-top-color:var(--gold)}
.pcard.open .pf{grid-column:1;grid-row:1}.pcard.open .pbody{grid-column:2;grid-row:1;padding-top:0}
.pcard.open .pf img,.pcard.open .pf-ph{aspect-ratio:3/4}.pcard.open .pf img{transform:none}
.pcard.open .bshare{top:14px;right:14px}
.blk{background:#fff;border:1px solid var(--line);border-radius:12px;margin:8px 0;scroll-margin-top:60px}
.blk>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;min-height:52px;padding:10px 16px;font-weight:800;font-size:1.02rem;color:var(--pine-d)}
.blk>summary::-webkit-details-marker{display:none}
.blk>summary::after{content:"＋";margin-left:auto;font-weight:900;color:var(--pine)}.blk[open]>summary::after{content:"－"}
.blk .cnt{font-size:.78rem;font-weight:700;background:var(--paper-2);color:var(--pine-d);border-radius:999px;padding:0 10px}
.blk .inner{padding:2px 16px 16px;border-top:1px dashed var(--line)}
.inner h4{font-size:.98rem;margin:16px 0 4px;color:var(--pine)}
table.flow{width:100%;border-collapse:collapse;font-size:.95rem;margin-top:8px}
table.flow th{width:7.5em;text-align:left;vertical-align:top;color:var(--pine);font-variant-numeric:tabular-nums;padding:6px 10px 6px 0;white-space:nowrap}
table.flow td{padding:6px 0;border-bottom:1px solid var(--line)}table.flow tr:last-child td{border-bottom:0}
.flowhint{font-size:.82rem;color:var(--ink-2);margin:8px 0 0}
ul.people{list-style:none;margin:0 0 6px;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:4px 18px}
ul.people li{display:flex;flex-direction:column;padding:4px 0}ul.people b{color:var(--pine)}ul.people span{font-size:.84rem;color:var(--ink-2)}
.pending{color:var(--ink-2);background:var(--paper);border:1px dashed var(--line-2);border-radius:8px;padding:6px 12px;margin:6px 0 0;font-size:.88rem}
.slogans{margin:6px 0;padding-left:1.4em;font-size:1.15rem;font-weight:800;color:var(--pine-d)}.slogans li{margin:4px 0}
.opener,.closer{font-size:1.2rem;font-weight:900;color:var(--pine-d);margin:8px 0}.closer{margin-bottom:0}
.phs{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0 0}
.phs figure{margin:0;min-width:0}.phs img{display:block;width:100%;height:auto;border-radius:8px;background:var(--paper-2)}
.phs figcaption{font-size:.82rem;color:var(--ink-2);margin-top:6px;line-height:1.55}
.gal{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0}
.gal a{display:block;border-radius:8px;overflow:hidden;background:var(--paper-2)}.gal img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover}
details.sub{margin:4px 0 10px}details.sub summary{cursor:pointer;font-weight:700;color:var(--blue-d);padding:10px 0;min-height:44px}
.presstext p{margin:0 0 1em}.presstext h3{font-size:1.05rem;margin:20px 0 6px;color:var(--pine)}.presstext a{color:var(--blue-d)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
.card{display:block;border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--paper);text-decoration:none;color:var(--ink)}
.card b{display:block;color:var(--pine-d);margin-bottom:2px;font-size:.95rem}.card span{font-size:.82rem;color:var(--ink-2)}
ul.plain{margin:6px 0;padding-left:1.2em}
section.docs{margin:16px 0 0}.docs .btnrow{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
.rules{font-size:.9rem;margin:10px 0 0;color:var(--ink-2)}
footer{margin-top:22px;background:#1B2420;color:#c3ccc6;font-size:.82rem;line-height:1.7}footer .wrap{padding:16px 16px}footer a{color:var(--gold)}
footer .fnote{margin:10px 0}footer .contact ul{margin:4px 0;padding-left:1.2em}
.fbtns{display:flex;gap:8px;margin:12px 0}
a:focus-visible,summary:focus-visible,button:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
@media(min-width:681px){.facts{display:flex;font-size:1.05rem}.facts li{flex:1;border-top:0;border-left:1px solid rgba(255,255,255,.28);padding:4px 14px}.facts li:first-child{border-left:0;padding-left:0}}
@media(max-width:680px){
.hero h1{font-size:1.35rem}.hero .in{padding:16px 16px 18px}.facts{font-size:1.05rem}
.wall{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.pcard{padding:8px}.pq{font-size:.8rem;line-height:1.5}.pcard h4{font-size:1rem}
.pcard.open{grid-template-columns:minmax(0,1fr)}.pcard.open .pf{grid-row:auto}.pcard.open .pf img,.pcard.open .pf-ph{max-width:150px}
.pcard.open .pbody{grid-column:1;grid-row:auto;padding-top:8px}
ul.people,.cards,.phs{grid-template-columns:minmax(0,1fr)}.gal{grid-template-columns:repeat(2,minmax(0,1fr))}
table.flow th{white-space:normal;width:6.5em}.btn{padding:10px 14px}}
@media print{.previewbar,.topbar .tools,nav.sticky,.bshare,.fbtns{display:none!important}
details>*{display:block!important}details.pfull summary,.blk>summary{break-after:avoid}.pcard,.blk{break-inside:avoid-page}.hero{break-after:avoid}body{background:#fff}}
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
<header class="topbar"><div class="topbar-inner"><div><div class="org"><a href="https://aabe.org.tw/" aria-label="回國教行動聯盟官網">國教行動聯盟</a></div><div class="org-en">Action Alliance on Basic Education (AABE) · 民間團體</div></div><div class="tools"><button type="button" class="tb" data-act="expand">全部展開</button><button type="button" class="tb" data-act="print">列印版</button></div></div></header>
<div class="wrap">
<nav class="breadcrumb" aria-label="麵包屑導航"><a href="https://aabe.org.tw/">首頁</a> / <a href="https://aabe.org.tw/events/">活動</a> / <span>兒少十大承諾起跑記者會 完整記錄</span></nav>
<main>
<div class="hero" id="top">
<img src="%%PRESS_REL%%photo-group.jpg" fetchpriority="high" width="1200" height="630" alt="72 個民間團體代表與出席立委手持「簽了就公開、不評分不排名」「少子化不只中央的事」等手舉板合影，2026 年 10 月 14 日於立法院">
<div class="in">
<p class="kicker">兒少十大承諾起跑記者會　完整記錄</p>
<h1>少子化不只中央的事　72團體邀22縣市打造友善城市</h1>
<p class="sub">兒少十大、全年齡心理健康城市六項承諾同步發布　邀三黨立委協助轉達</p>
<p class="meta"><time datetime="2026-10-14T10:00:00+08:00">2026 年 10 月 14 日（三）上午 10:00</time>　立法院中興大樓 101 會議室</p>
<ul class="facts"><li><span data-metric="child_pledge_cosponsor_orgs">72</span> 個民間團體共同發起</li><li>寄送全國 22 縣市長參選人</li><li>11/11 回覆截止・預定 11/18 公布結果</li></ul>
<p class="slogan">孩子的事，縣市的事！</p>
<div class="btns"><a class="btn p" href="https://aabe.org.tw/act/child-pledge/record/">看各縣市簽署與回覆</a><a class="btn g" href="#documents">下載兩份承諾書</a><a class="tlink" href="#press-release">新聞稿全文</a><a class="tlink" href="%%LIVE%%" target="_blank" rel="noopener">看記者會直播</a></div>
</div></div>
<nav class="sticky" aria-label="本頁導覽"><ul><li><a href="#people">人物</a></li><li><a href="#press-release">新聞稿</a></li><li><a href="#gallery">照片</a></li><li><a href="#documents">文件</a></li></ul></nav>

<h2 class="sec" id="people">12 位發言人</h2>
<p style="margin:0;color:var(--ink-2);font-size:.9rem">點「完整發言」就地展開全文，一次開一位；右上角圖示可複製這位的專屬網址。</p>
%%WALL%%

<h2 class="sec" id="more">更多記錄</h2>
<details class="blk" id="press-release"><summary><span class="ttl">新聞稿全文</span><span class="cnt">v6.2 官網版</span></summary><div class="inner presstext">
<p style="margin:12px 0"><a class="btn d" href="%%PRESS_REL%%attachments/07_press-release.pdf">下載新聞稿 PDF</a>　<a class="btn o" href="%%PRESS_URL%%">回新聞稿頁</a></p>
%%PRESS%%</div></details>
<details class="blk" id="schedule"><summary><span class="ttl">記者會流程與出席名單</span><span class="cnt">依採訪通知整理</span></summary><div class="inner">
<table class="flow"><tbody>%%FLOW%%</tbody></table><p class="flowhint">以上為採訪通知預排流程，實際先後與時間以現場為準。</p>
%%ATT%%</div></details>
<details class="blk" id="slogans"><summary><span class="ttl">口號與合影</span><span class="cnt">5 句口號・2 張合影</span></summary><div class="inner">%%SLOG%%%%PHS%%</div></details>
<details class="blk" id="gallery"><summary><span class="ttl">現場相簿</span><span class="cnt">精選 8 張</span></summary><div class="inner">
<p style="margin:12px 0 0;font-size:.92rem">點圖開大圖。</p>%%GAL%%
<a class="btn o" href="%%DRIVE%%" target="_blank" rel="noopener">全部 <span data-metric="child_pledge_launch_photos">47</span> 張（Google Drive）</a></div></details>
<details class="blk" id="context"><summary><span class="ttl">脈絡與延伸</span><span class="cnt">3</span></summary><div class="inner"><div class="cards">
<a class="card" href="../2026-10-02-mental-health-city-forum/record/"><b>10/2 心理健康城市網絡論壇　會後記錄</b><span>臺灣心理健康聯盟主辦；本頁只連結，不複製內容</span></a>
<a class="card" href="https://aabe.org.tw/act/mental-health-city/"><b>心理健康城市六項承諾書</b><span>縣市長參選人簽署與回覆</span></a>
<a class="card" href="https://aabe.org.tw/press/2026-10-07-world-mental-health-day-joint-press-release/"><b>10/7 聯合新聞稿</b><span>心理健康從生活實踐開始（臺灣心理健康聯盟・國教行動聯盟）</span></a></div></div></details>
%%MEDIA%%

<section class="docs" id="documents"><h2 class="sec" style="margin-top:0">文件與追蹤入口</h2>
<div class="btnrow">
<a class="btn d" href="%%PRESS_REL%%attachments/01_child-pledge-10.pdf">兒少十大承諾書 PDF</a>
<a class="btn d" href="%%PRESS_REL%%attachments/02_mental-health-city-6.pdf">心理健康城市六項承諾書 PDF</a>
<a class="btn o" href="%%PRESS_URL%%attachments/">四附件與書面意見</a>
<a class="btn o" href="https://aabe.org.tw/act/child-pledge/record/">各縣市簽署與回覆</a></div>
<p class="rules">所有參選人適用一致規則：<strong>不評分、不排名、不推薦任何人</strong>。</p></section>
</main>
</div>
<footer><div class="wrap">
<div class="fbtns"><button type="button" class="tb" data-act="expand">全部展開</button><button type="button" class="tb" data-act="print">列印版</button></div>
<p class="fnote">%%NOTE%%</p>
<div class="contact">聯絡資訊：<ul>
<li>新聞聯絡人：國教行動聯盟理事長 王瀚陽　0983-097-165</li>
<li>承諾書回覆窗口：國教行動聯盟秘書長 李睿澤　0921-113-066</li>
<li>回覆信箱：action.a.e0626@gmail.com</li></ul></div>
<p class="fnote">引用格式（APA 7）：國教行動聯盟（2026，10 月 14 日）。<i>兒少十大承諾起跑記者會 完整記錄</i>［活動記錄］。<a href="%%PAGE_URL%%">%%PAGE_URL%%</a></p>
<p><a href="https://aabe.org.tw/events/">更多活動</a>　·　<a href="https://aabe.org.tw/">aabe.org.tw</a>　·　國教行動聯盟（民間團體）· AABE</p>
</div></footer>
<script>
(function(){
  var all=false, cards=[].slice.call(document.querySelectorAll('.pcard'));
  function sync(c){c.classList.toggle('open',c.querySelector('details.pfull').open)}
  cards.forEach(function(c){
    var d=c.querySelector('details.pfull');
    d.addEventListener('toggle',function(){
      sync(c);
      if(d.open&&!all){cards.forEach(function(o){if(o!==c){var od=o.querySelector('details.pfull');if(od.open){od.open=false}}})}
    });
  });
  function openFor(el){
    var p=el;
    while(p){ if(p.tagName==='DETAILS'){p.open=true} p=p.parentElement }
    var c=el.closest&&el.closest('.pcard'); if(c){c.querySelector('details.pfull').open=true}
  }
  function fromHash(){
    var id=decodeURIComponent(location.hash.slice(1)); if(!id)return;
    var el=document.getElementById(id); if(!el)return;
    openFor(el); setTimeout(function(){el.scrollIntoView({block:'start'})},60);
  }
  window.addEventListener('hashchange',fromHash); fromHash();
  function setAll(on){
    all=on;
    [].slice.call(document.querySelectorAll('details')).forEach(function(d){d.open=on});
    [].slice.call(document.querySelectorAll('[data-act=expand]')).forEach(function(b){b.textContent=on?'全部收合':'全部展開'});
  }
  [].slice.call(document.querySelectorAll('[data-act]')).forEach(function(b){
    b.addEventListener('click',function(){
      if(b.getAttribute('data-act')==='print'){setAll(true);setTimeout(function(){window.print()},300)}
      else{setAll(!all)}
    });
  });
  [].slice.call(document.querySelectorAll('.bshare')).forEach(function(b){
    b.addEventListener('click',function(){
      var url=location.origin+location.pathname+'#'+b.getAttribute('data-id');
      function ok(){b.classList.add('done');setTimeout(function(){b.classList.remove('done')},1600)}
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(ok,function(){window.prompt('複製這個網址',url)})}
      else{window.prompt('複製這個網址',url)}
    });
  });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    prod = build(preview=False)
    total, bad = verbatim_check(prod)
    print("verbatim lines checked:", total, "problems:", len(bad), bad[:6])
    if bad:
        sys.exit(1)
    open(os.path.join(PAGE_DIR, "index.html"), "w", encoding="utf-8").write(prod)
    print("wrote", os.path.join(PAGE_DIR, "index.html"), len(prod))
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        pv = to_inline(build(preview=True))
        open(out, "w", encoding="utf-8").write(pv)
        print("preview", out, len(pv))

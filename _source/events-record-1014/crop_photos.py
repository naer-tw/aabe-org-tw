#!/usr/bin/env python3
"""10/14 記者會完整記錄專頁：由現場原檔裁出新增的五張發言照（3:4，480x640）與相簿縮圖。
人物與照片對應＝理事長 10/14 確認 12 格核對表（陶蓮生 8692、林嘉慧 8695、簡信斌 8698、甄瑞興 8706、蔡沛華 8709）。
新聞稿頁已有的六張發言照與合照不重裁，頁面直接引用 /press/2026-10-14-child-pledge-launch/ 同一份。"""
from PIL import Image
import os, sys
SRC = "/Users/coachyang/Desktop/10:14照片/"
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "public", "events", "2026-10-14-child-pledge-launch", "images")
os.makedirs(OUT, exist_ok=True)
# (原檔, 輸出檔名, 裁切框 x0,y0,x1,y1；3:4)
PORTRAITS = [
    ("IMG_8692", "photo-tao-lian-sheng.jpg", (30, 100, 600, 860)),
    ("IMG_8695", "photo-lin-jia-hui.jpg", (360, 170, 930, 930)),
    ("IMG_8698", "photo-jian-xin-bin.jpg", (380, 250, 950, 1010)),
    ("IMG_8706", "photo-zhen-rui-xing.jpg", (997, 285, 1567, 1045)),
    ("IMG_8709", "photo-cai-pei-hua.jpg", (830, 270, 1400, 1030)),
]
for src, name, box in PORTRAITS:
    im = Image.open(SRC + src + ".JPG").convert("RGB").crop(box).resize((480, 640), Image.LANCZOS)
    im.save(os.path.join(OUT, name), quality=86, optimize=True)
GALLERY = ["IMG_8664", "IMG_8668", "IMG_8674", "IMG_8687", "IMG_8690", "IMG_8696", "IMG_8700", "IMG_8710", "IMG_8711", "IMG_8713"]
for g in GALLERY:
    im = Image.open(SRC + g + ".JPG").convert("RGB")
    im.thumbnail((1200, 1200), Image.LANCZOS)
    im.save(os.path.join(OUT, "live-" + g[4:] + ".jpg"), quality=82, optimize=True)
print("ok", len(PORTRAITS), len(GALLERY))

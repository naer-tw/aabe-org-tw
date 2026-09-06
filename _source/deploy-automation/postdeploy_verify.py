#!/usr/bin/env python3
"""postdeploy_verify.py — 部署後的線上內容驗證（postdeploy.sh 的驗證核心）。

依據：_source/SOP-數據更新與部署索引.md 第五節。
2026-09-06 依 Codex 盲審 C-01／C-08 建立（報告：_source/審查_Codex盲審_數據SOP_20260906.md）。

跟舊版（postdeploy.sh 內嵌 python）差在三件事：
  1. **要驗哪幾頁不再寫死**：掃 public/ 裡「含 data-metric 的所有頁面」＋
     llms.txt／humans.txt，未來在 /about/ 加標記也會自動納入驗證與推送。
  2. **不再用全文包含判斷**：直接解析線上 HTML 的 data-metric，逐個標記比對
     (id, 欄位, 顯示值)，並比對每頁每個 id 的標記數量。線上主數字被改回舊值、
     但同頁別處剛好有一個相同數字時，舊版會誤判通過（C-01 失效場景 2）。
  3. **可離線跑**：`--live-dir` 直接讀本地目錄當「線上內容」，測試不必開 port。

用法：
    python3 postdeploy_verify.py --base https://aabe.org.tw
    python3 postdeploy_verify.py --live-dir /path/to/site --print-urls
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numbers_check as nc

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_PUBLIC = REPO / "public"
DEFAULT_NUMBERS = REPO / "_source" / "numbers.json"
DEFAULT_ALLOWLIST = REPO / "_source" / "numbers_allowlist.json"
PHONE = "0983-097-165"
PHONE_PAGES = ("contact/index.html", "press/index.html")


def page_url(rel: str) -> str:
    """public/ 的相對路徑 → 網址路徑。about/index.html → /about/。"""
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def targets(public: Path, allowlist: list) -> list[tuple[str, str]]:
    """回傳 [(網址路徑, 本地檔案相對路徑)]：所有含標記的頁面＋兩個 AI 可讀檔。"""
    out: list[tuple[str, str]] = []
    for path in sorted(p for p in public.rglob("*.html") if p.is_file()):
        rel = path.relative_to(public).as_posix()
        # 含標記的頁面一律驗；窗口頁即使沒有數字標記也要驗電話
        if 'data-metric=' not in path.read_text(encoding="utf-8") and rel not in PHONE_PAGES:
            continue
        out.append((page_url(rel), rel))
    known_text = {a["file"] for a in allowlist}
    for name in nc.EXTRA_TEXT_FILES:
        if (public / name).exists() and name in known_text:
            out.append(("/" + name, name))
    return out


def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "aabe-postdeploy/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:      # noqa: S310
        return r.read().decode("utf-8", errors="replace")


def check_page(live_src: str, local_src: str, rel: str, metrics: dict,
               allowlist: list) -> list[tuple[bool, str]]:
    """回傳 [(是否通過, 訊息)]。"""
    out: list[tuple[bool, str]] = []
    path = page_url(rel)

    if rel.endswith(".html"):
        want = nc.find_marked(local_src)
        got = nc.find_marked(live_src)
        want_counts: dict[tuple[str, str], list[str]] = {}
        got_counts: dict[tuple[str, str], list[str]] = {}
        for mk in want:
            want_counts.setdefault((mk.metric_id, mk.field_key), []).append(mk.shown)
        for mk in got:
            got_counts.setdefault((mk.metric_id, mk.field_key), []).append(mk.shown)

        for key in sorted(set(want_counts) | set(got_counts)):
            mid, field_key = key
            w, g = want_counts.get(key, []), got_counts.get(key, [])
            if len(w) != len(g):
                out.append((False, f"{path} {mid}.{field_key} 線上有 {len(g)} 處標記、"
                                   f"本地有 {len(w)} 處——整張卡或標記被刪掉了？"))
                continue
            expect = str(metrics[mid][field_key]) if mid in metrics else None
            if expect is None:
                out.append((False, f"{path} 線上標記 {mid} 不在真源 numbers.json 裡"))
                continue
            norm = expect if field_key == "display" else re.sub(r"\s+", "", expect)
            bad = [s for s in g if s != norm]
            if bad:
                out.append((False, f"{path} {mid}.{field_key} 線上顯示「{'、'.join(bad)}」，"
                                   f"真源是「{expect}」"))
            else:
                out.append((True, f"{path} {mid}.{field_key} = {expect}"
                                  f"（{len(g)} 處標記）"))
    else:
        # llms.txt／humans.txt 沒有標記，改驗 allowlist 登記的 id 值有出現
        text, _ = nc.condense(live_src)
        ids = sorted({a["id"] for a in allowlist if a["file"] == rel})
        for mid in ids:
            want_display = metrics[mid]["display"]
            if want_display in text:
                out.append((True, f"{path} {mid} = {want_display}"))
            else:
                out.append((False, f"{path} {mid} 線上找不到真源值「{want_display}」"))

    if rel in PHONE_PAGES:
        text, _ = nc.condense(live_src)
        if PHONE in text:
            out.append((True, f"{path} 窗口電話 {PHONE}"))
        else:
            out.append((False, f"{path} 找不到窗口電話 {PHONE}"
                               f"（理事長 王瀚陽，全站唯一具名窗口）"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="部署後線上內容驗證")
    ap.add_argument("--base", default="https://aabe.org.tw")
    ap.add_argument("--live-dir", help="改讀本地目錄當「線上內容」（測試／離線用）")
    ap.add_argument("--public", default=str(DEFAULT_PUBLIC))
    ap.add_argument("--numbers", default=str(DEFAULT_NUMBERS))
    ap.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST))
    ap.add_argument("--print-urls", action="store_true", help="只印出要驗／要推的網址")
    args = ap.parse_args(argv)

    public = Path(args.public)
    metrics = nc.load_metrics(Path(args.numbers))
    allowlist = nc.load_allowlist(Path(args.allowlist))
    pairs = targets(public, allowlist)
    base = args.base.rstrip("/")

    if args.print_urls:
        for path, _rel in pairs:
            print(base + path)
        return 0

    print(f"=== 部署後實地驗證（{len(pairs)} 個位置，基底 {args.live_dir or base}，"
          f"真源 {Path(args.numbers).name}）===")
    bad = 0
    for path, rel in pairs:
        local_src = (public / rel).read_text(encoding="utf-8")
        try:
            if args.live_dir:
                live_src = (Path(args.live_dir) / rel).read_text(encoding="utf-8")
            else:
                live_src = fetch(base + path)
        except (OSError, urllib.error.URLError) as e:
            print(f"  ❌ {base + path} 取不到內容：{e}")
            bad += 1
            continue
        for ok, msg in check_page(live_src, local_src, rel, metrics, allowlist):
            print(("  ✅ " if ok else "  ❌ ") + msg)
            bad += 0 if ok else 1

    if bad:
        print(f"\n❌ 線上內容與真源不符（{bad} 項）"
              f"——不要宣告完成，先查是部署未生效還是漏改。")
        return 1
    print("\nCONTENT_LIVE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

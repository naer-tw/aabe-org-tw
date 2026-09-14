#!/usr/bin/env python3
"""活動狀態部署閘（第一批工作項 1）。

讀 `_source/events.json`，掃 `public/**/*.html`。對每一場 end 日期 < 今天
（status 已標 ended／cancelled 的也一併檢查）的活動：在提到該活動的卡片
附近（用活動 id 的路徑片段或標題定位），若出現任一句「即將舉辦」「開放
報名」「立即報名」「填問卷」「報名」，就視為 FAIL 並列出檔案、行號、
匹配到的詞。

這不是完整的靜態網站產生器（規劃書明講「不一定要改成產生器」），是務實
的對表檢查：只要活動資料與頁面文字兜不起來就攔下來，不追求 100% 定位
準確（例如同頁另一個無關段落恰好含有活動 id 字串也會被掃到，屬於刻意
從寬的假陽性，寧可多報不要漏報）。

用法：
    python3 events_check.py [--root ..]

回傳：exit code 0 = 全部通過；1 = 有 FAIL（stdout 逐條列出）。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

BANNED_PATTERNS = ["即將舉辦", "開放報名", "立即報名", "填問卷", "報名"]
BANNED_RE = re.compile("|".join(re.escape(p) for p in BANNED_PATTERNS))

# 卡片搜尋視窗：命中活動識別字串的行，往前後各抓幾行一起檢查
# （手工排版的靜態頁沒有一致的卡片元件邊界，用固定視窗是務實近似）
WINDOW_BEFORE = 12
WINDOW_AFTER = 12

# 只在「連結／按鈕／狀態徽章」的可見文字裡抓禁詞，不掃 <meta>、<!-- 註解 -->、
# JSON-LD 或一般敘述文字——歷史說明句「報名已下架」「原報名平台」不該被攔。
# 對應規劃書原文：「若出現[禁詞]且該連結／按鈕在該活動卡片內，就 FAIL」。
ACTIONABLE_RE = re.compile(
    r"<a\b[^>]*>(.*?)</a>"
    r"|<(?:span|div)\b[^>]*class=\"[^\"]*(?:badge|kicker|status|upcoming-note|nh-badge)[^\"]*\"[^>]*>(.*?)</(?:span|div)>",
    re.IGNORECASE,
)


def actionable_texts(window_text: str) -> list[str]:
    """抓出視窗內所有連結／按鈕／狀態徽章的可見文字（忽略註解與 meta）。"""
    # 先把 HTML 註解整段拿掉，避免註解裡的舊字樣被誤判為可見文字
    no_comments = re.sub(r"<!--.*?-->", "", window_text, flags=re.DOTALL)
    texts = []
    for m in ACTIONABLE_RE.finditer(no_comments):
        texts.append(m.group(1) or m.group(2) or "")
    return texts


def load_events(events_json: Path) -> list[dict]:
    data = json.loads(events_json.read_text(encoding="utf-8"))
    return data["events"]


def event_identifiers(ev: dict) -> list[str]:
    """回傳可用來在頁面中定位這場活動的字串（id 的路徑片段 + 標題）。"""
    ids = [ev["id"]]
    if ev.get("record_url"):
        ids.append(ev["record_url"])
    if ev.get("cta_url"):
        ids.append(ev["cta_url"])
    ids.append(ev["title"])
    return [s for s in ids if s]


def find_html_files(public_dir: Path) -> list[Path]:
    return sorted(public_dir.rglob("*.html"))


def check_file(path: Path, ended_events: list[dict], today: dt.date) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    findings = []
    for ev in ended_events:
        idents = event_identifiers(ev)
        hit_lines = set()
        for i, line in enumerate(lines):
            if any(ident in line for ident in idents):
                hit_lines.add(i)
        for i in hit_lines:
            lo = max(0, i - WINDOW_BEFORE)
            hi = min(len(lines), i + WINDOW_AFTER + 1)
            window_text = "\n".join(lines[lo:hi])
            m = None
            for chunk in actionable_texts(window_text):
                m = BANNED_RE.search(chunk)
                if m:
                    break
            if m:
                findings.append(
                    {
                        "file": str(path),
                        "anchor_line": i + 1,
                        "event_id": ev["id"],
                        "matched": m.group(0),
                    }
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent.parent),
        help="repo 根目錄（預設：自動推得 aabe-deploy 根目錄）",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="覆寫『今天』日期（YYYY-MM-DD），主要供測試使用",
    )
    args = parser.parse_args()

    root = Path(args.root)
    events_json = root / "_source" / "events.json"
    public_dir = root / "public"

    if not events_json.exists():
        print(f"FATAL: 找不到 {events_json}")
        return 1
    if not public_dir.exists():
        print(f"FATAL: 找不到 {public_dir}")
        return 1

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    events = load_events(events_json)

    ended = []
    for ev in events:
        end_date = dt.date.fromisoformat(ev["end"])
        if end_date < today or ev.get("status") in ("ended", "cancelled"):
            ended.append(ev)

    if not ended:
        print("沒有已結束的活動需要檢查。")
        return 0

    all_findings = []
    for html_file in find_html_files(public_dir):
        all_findings.extend(check_file(html_file, ended, today))

    if all_findings:
        print(f"FAIL：{len(all_findings)} 處活動狀態與文字不同步\n")
        for f in all_findings:
            rel = Path(f["file"]).relative_to(root)
            print(f"  {rel}:{f['anchor_line']}  活動={f['event_id']}  命中「{f['matched']}」")
        return 1

    print(f"PASS：{len(ended)} 場已結束活動，全站無殘留「{'|'.join(BANNED_PATTERNS)}」字樣。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

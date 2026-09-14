"""① 活動狀態連動：events_check.py 對 public/**/*.html 的部署閘。

規劃書第一批工作項 1 的驗收條件：「結束日 < 今天的活動，任一頁不得出現
『即將舉辦／開放報名／立即報名／填問卷／報名』」。實際規則見
`_source/deploy-automation/events_check.py`（只掃連結／按鈕／狀態徽章的
可見文字，不誤攔歷史說明句）。
"""
import subprocess
import sys
from pathlib import Path


def test_events_check_passes(repo_root: Path):
    script = repo_root / "_source" / "deploy-automation" / "events_check.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(repo_root)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "events_check.py 回報 FAIL，代表有已結束活動的卡片仍殘留報名/即將舉辦字樣：\n"
        f"{result.stdout}\n{result.stderr}"
    )


def test_events_json_well_formed(repo_root: Path):
    import json

    events_path = repo_root / "_source" / "events.json"
    assert events_path.exists(), "缺少 _source/events.json（活動狀態單一來源）"
    data = json.loads(events_path.read_text(encoding="utf-8"))
    events = data["events"]
    assert len(events) >= 7, "events.json 應至少涵蓋現有 /events/ 子站的活動"

    required = {"id", "title", "start", "end", "status"}
    for ev in events:
        missing = required - ev.keys()
        assert not missing, f"活動 {ev.get('id')} 缺少欄位 {missing}"
        assert ev["status"] in ("upcoming", "ended", "cancelled"), (
            f"活動 {ev['id']} 的 status 值不合法：{ev['status']!r}"
        )


def test_checker_actually_detects_violations(tmp_path: Path, repo_root: Path):
    """驗證 events_check.py 不是空殼 PASS：餵一個已知違規案例必須抓到。

    對應 judgment.md §6「pass + 空 issues = 紅旗」的自我檢查——一個只會
    回傳 0 的檢查腳本毫無意義，這裡逆向證明它真的會抓到問題。
    """
    script = repo_root / "_source" / "deploy-automation" / "events_check.py"

    fake_root = tmp_path / "fake_site"
    (fake_root / "public").mkdir(parents=True)
    (fake_root / "_source").mkdir(parents=True)

    (fake_root / "_source" / "events.json").write_text(
        '{"events": [{"id": "2020-01-01-selftest", "title": "自我測試活動",'
        ' "start": "2020-01-01", "end": "2020-01-01", "status": "ended",'
        ' "record_url": null, "cta_label": null, "cta_url": null, "pages": []}]}',
        encoding="utf-8",
    )
    (fake_root / "public" / "test.html").write_text(
        '<html><body><div class="card"><h3>自我測試活動</h3>'
        '<a href="/register">立即報名 →</a></div></body></html>',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(script), "--root", str(fake_root)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, "檢查腳本沒有抓到刻意植入的違規案例，等同空殼 PASS"
    assert "立即報名" in result.stdout

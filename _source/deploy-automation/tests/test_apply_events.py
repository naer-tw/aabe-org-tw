"""③ apply_events.py：把 events.json 的 badge／cta 一次寫回全站 data-event-id 標記處。

第三批工作項 3（events.json 驅動多頁）驗收：dry-run 不寫檔、跑兩次冪等、
pages[] 列的頁面缺標記要報錯、版面上有標記但 events.json 無此 id 要報錯、
回填後 events_check.py 仍要 PASS（不能修出違規字樣）。
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

import apply_events as ae


def make_events(**overrides):
    ev = {
        "id": "2026-01-01-sample-event",
        "title": "示例活動",
        "display_title": "示例活動（顯示用）",
        "start": "2026-01-01",
        "end": "2026-01-01",
        "status": "ended",
        "record_url": "/events/2026-01-01-sample-event/",
        "badge": "已結束",
        "cta": {"label": "看紀錄 →", "url": "/events/2026-01-01-sample-event/"},
        "pages": ["/events/", "/events/2026-01-01-sample-event/"],
    }
    ev.update(overrides)
    return {"_meta": {"schema": "1.1"}, "events": [ev]}


def build_site(tmp_path: Path, events_index_html: str, own_page_html: str | None = None) -> Path:
    root = tmp_path / "public"
    (root / "events" / "2026-01-01-sample-event").mkdir(parents=True)
    (root / "events" / "index.html").write_text(events_index_html, encoding="utf-8")
    if own_page_html is not None:
        (root / "events" / "2026-01-01-sample-event" / "index.html").write_text(
            own_page_html, encoding="utf-8")
    return root


CARD = (
    '<html><body><div class="event-item" data-event-id="2026-01-01-sample-event">'
    '<span data-event-field="badge">舊徽章</span>'
    '<a href="/events/2026-01-01-sample-event/" data-event-field="cta">舊連結文字</a>'
    '</div></body></html>'
)

OWN_PAGE = '<html><body><div class="hero" data-event-id="2026-01-01-sample-event"></div></body></html>'


# ── apply_html 單元 ─────────────────────────────────────────
def test_replaces_badge_and_cta_text():
    out, changes, ids = ae.apply_html(CARD, {"2026-01-01-sample-event": make_events()["events"][0]}, "events/index.html")
    assert "已結束" in out and "舊徽章" not in out
    assert "看紀錄 →" in out and "舊連結文字" not in out
    fields = sorted(c.field for c in changes)
    assert fields == ["badge", "cta"]
    assert ids == {"2026-01-01-sample-event"}


def test_no_change_when_already_synced():
    synced = (
        '<html><body><div class="event-item" data-event-id="2026-01-01-sample-event">'
        '<span data-event-field="badge">已結束</span>'
        '<a href="/events/2026-01-01-sample-event/" data-event-field="cta">看紀錄 →</a>'
        '</div></body></html>'
    )
    out, changes, ids = ae.apply_html(synced, {"2026-01-01-sample-event": make_events()["events"][0]}, "events/index.html")
    assert changes == []
    assert out == synced


def test_updates_href_when_cta_url_changes():
    ev = make_events()["events"][0]
    ev["cta"]["url"] = "/events/2026-01-01-sample-event/notes/"
    out, changes, ids = ae.apply_html(CARD, {ev["id"]: ev}, "events/index.html")
    assert 'href="/events/2026-01-01-sample-event/notes/"' in out
    assert any(c.field == "cta.url" for c in changes)


def test_unknown_event_id_raises():
    html = '<div data-event-id="ghost-event"></div>'
    with pytest.raises(ae.ApplyError, match="ghost-event"):
        ae.apply_html(html, {}, "fake.html")


def test_field_without_preceding_id_raises():
    html = '<html><body><span data-event-field="badge">已結束</span></body></html>'
    with pytest.raises(ae.ApplyError, match="data-event-field"):
        ae.apply_html(html, {"2026-01-01-sample-event": make_events()["events"][0]}, "fake.html")


def test_cta_url_null_but_markup_has_href_raises():
    ev = make_events()["events"][0]
    ev["cta"]["url"] = None
    with pytest.raises(ae.ApplyError, match="純文字狀態"):
        ae.apply_html(CARD, {ev["id"]: ev}, "events/index.html")


# ── run()：dry-run／冪等／涵蓋率 ───────────────────────────
def test_dry_run_prints_diff_without_writing(tmp_path, capsys):
    events_data = make_events()
    events_data["events"][0]["pages"] = ["/events/", "/events/2026-01-01-sample-event/"]
    root = build_site(tmp_path, CARD, OWN_PAGE)
    before = (root / "events" / "index.html").read_text(encoding="utf-8")
    changes = ae.run(root, events_data, dry_run=True)
    out = capsys.readouterr().out
    assert "--- " in out and "+++ " in out
    assert changes
    assert (root / "events" / "index.html").read_text(encoding="utf-8") == before


def test_idempotent(tmp_path):
    events_data = make_events()
    events_data["events"][0]["pages"] = ["/events/", "/events/2026-01-01-sample-event/"]
    root = build_site(tmp_path, CARD, OWN_PAGE)
    ae.run(root, events_data, dry_run=False)
    after_first = (root / "events" / "index.html").read_text(encoding="utf-8")
    changes = ae.run(root, events_data, dry_run=False)
    assert changes == []
    assert (root / "events" / "index.html").read_text(encoding="utf-8") == after_first


def test_missing_marker_for_declared_page_raises(tmp_path):
    """pages[] 宣稱某頁有這場活動的卡片，但該頁實際找不到 data-event-id 標記。"""
    events_data = make_events()
    events_data["events"][0]["pages"] = ["/events/", "/act/"]
    root = build_site(tmp_path, CARD, OWN_PAGE)
    (root / "act").mkdir(parents=True)
    (root / "act" / "index.html").write_text("<html><body>沒有任何活動標記</body></html>",
                                              encoding="utf-8")
    with pytest.raises(ae.ApplyError, match="/act/"):
        ae.run(root, events_data, dry_run=False)


def test_extra_marker_not_in_events_json_raises(tmp_path):
    """版面上有 data-event-id，但 events.json 完全沒有這個活動（多餘標記）。"""
    events_data = {"_meta": {"schema": "1.1"}, "events": []}
    root = build_site(tmp_path, CARD, OWN_PAGE)
    with pytest.raises(ae.ApplyError, match="2026-01-01-sample-event"):
        ae.run(root, events_data, dry_run=False)


def test_applied_result_still_passes_events_check(tmp_path, repo_root):
    """回填後（badge/cta 文字已同步），events_check.py 針對這份複本仍要 PASS。"""
    events_data = make_events(status="ended")
    events_data["events"][0]["pages"] = ["/events/", "/events/2026-01-01-sample-event/"]
    events_data["events"][0]["end"] = "2020-01-01"  # 早已結束，events_check 會檢查它
    events_data["events"][0]["record_url"] = "/events/2026-01-01-sample-event/"
    root = build_site(tmp_path, CARD, OWN_PAGE)
    ae.run(root, events_data, dry_run=False)

    events_json = tmp_path / "events.json"
    events_json.write_text(json.dumps(events_data, ensure_ascii=False), encoding="utf-8")
    fake_repo = tmp_path
    (fake_repo / "_source").mkdir(exist_ok=True)
    (fake_repo / "_source" / "events.json").write_text(
        json.dumps(events_data, ensure_ascii=False), encoding="utf-8")

    script = repo_root / "_source" / "deploy-automation" / "events_check.py"
    r = subprocess.run([sys.executable, str(script), "--root", str(fake_repo)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# ── CLI 與真站 ─────────────────────────────────────────────
def test_cli_dry_run_on_real_site_is_clean(repo_root):
    """真站現況已與真源同步（本批交付時已手動核對一致），dry-run 應該報「無變動」。"""
    script = repo_root / "_source" / "deploy-automation" / "apply_events.py"
    r = subprocess.run([sys.executable, str(script), "--dry-run"],
                       capture_output=True, text=True, cwd=repo_root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "無變動" in r.stdout

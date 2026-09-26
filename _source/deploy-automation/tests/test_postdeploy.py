"""⑤ postdeploy.sh：線上內容驗證 → IndexNow → 收據，全過才 POSTDEPLOY_OK。

2026-09-06 依 Codex 盲審改寫（C-01／C-07／C-08＋縱深 5）：
  - 不再開本機 HTTP port（沙箱會擋 socket.bind，六項測試以前跑不起來）。
    改用 `--live-dir` 直接讀目錄當「線上內容」。
  - 補上舊版放行的兩個場景：主數字被改回舊值但同頁別處有相同數字、
    IndexNow 明確失敗卻 exit 0。
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def script(repo_root):
    p = repo_root / "_source" / "deploy-automation" / "postdeploy.sh"
    assert p.exists(), f"缺少 {p}"
    return p


def run(script, repo_root, live_dir, *args, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run(["bash", str(script), "--live-dir", str(live_dir), *args],
                          capture_output=True, text=True, cwd=repo_root, env=e, timeout=180)


def site_copy(repo_root, tmp_path) -> Path:
    site = tmp_path / "live"
    shutil.copytree(repo_root / "public", site)
    return site


def ping_stub(tmp_path, exit_code=0):
    stub = tmp_path / "fake-indexnow.sh"
    log = tmp_path / "pinged.txt"
    stub.write_text(f'#!/bin/bash\nprintf "%s\\n" "$@" > "{log}"\nexit {exit_code}\n',
                    encoding="utf-8")
    stub.chmod(0o755)
    return stub, log


# ── 基本 ───────────────────────────────────────────────────
def test_syntax_ok(script):
    assert subprocess.run(["bash", "-n", str(script)]).returncode == 0


def test_is_executable(script):
    assert os.access(script, os.X_OK), "postdeploy.sh 要可執行（chmod +x）"


def test_checks_phone_and_calls_indexnow(script):
    text = script.read_text(encoding="utf-8")
    assert "0983-097-165" in text, "未比對理事長窗口電話"
    assert "../indexnow-ping.sh" in text, "未呼叫 IndexNow 推送"


def test_content_live_ok_on_healthy_site(script, repo_root, public_dir):
    r = run(script, repo_root, public_dir, "--skip-ping")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CONTENT_LIVE_OK" in r.stdout
    assert "0983-097-165" in r.stdout


def test_prints_receipt_with_pending_manual_items(script, repo_root, public_dir, tmp_path):
    receipt = tmp_path / "receipt.md"
    r = run(script, repo_root, public_dir, "--skip-ping", "--receipt", str(receipt))
    text = receipt.read_text(encoding="utf-8")
    for key in ("content_live", "indexnow", "board_status", "board_log",
                "gsc_request_index", "list_checkbox", "kb_caveat", "sop_experience"):
        assert key in text, f"收據缺項：{key}"
    assert "pending" in text and "看板" in r.stdout


# ── C-01：線上內容驗證不能只做全文包含判斷 ────────────────────
def test_exits_one_when_a_number_is_stale(script, repo_root, tmp_path):
    site = site_copy(repo_root, tmp_path)
    idx = site / "index.html"
    idx.write_text(idx.read_text(encoding="utf-8").replace(">66,247<", ">66,000<"),
                   encoding="utf-8")
    r = run(script, repo_root, site, "--skip-ping")
    assert r.returncode == 1
    assert "CONTENT_LIVE_OK" not in r.stdout
    assert "66,247" in r.stdout + r.stderr


def test_stale_main_number_is_caught_even_if_the_page_repeats_the_new_value(
        script, repo_root, tmp_path):
    """C-01 失效場景 2：方法頁主數字被改回 33，但同頁正文另有一個 47。

    舊版做的是「頁面文字裡有沒有 48」→ 誤判通過；現在逐標記比對。
    """
    site = site_copy(repo_root, tmp_path)
    page = site / "methodology" / "index.html"
    src = page.read_text(encoding="utf-8")
    assert 'data-metric="policy_briefs">48<' in src
    page.write_text(src.replace('data-metric="policy_briefs">48<',
                                'data-metric="policy_briefs">33<', 1), encoding="utf-8")
    assert "48 篇政策深度分析" in page.read_text(encoding="utf-8"), "同頁正文仍有另一個 48"
    r = run(script, repo_root, site, "--skip-ping")
    assert r.returncode == 1, r.stdout
    assert "policy_briefs" in r.stdout
    assert "CONTENT_LIVE_OK" not in r.stdout


def test_deleted_marker_is_caught(script, repo_root, tmp_path):
    """整個標記被刪掉：舊版 expected_ids=[] → bad=0 → 放行。"""
    site = site_copy(repo_root, tmp_path)
    page = site / "index.html"
    src = page.read_text(encoding="utf-8")
    page.write_text(src.replace('<span data-metric="valid_surveys">66,247</span>',
                                '<span>66,247</span>', 1), encoding="utf-8")
    r = run(script, repo_root, site, "--skip-ping")
    assert r.returncode == 1, r.stdout
    assert "valid_surveys" in r.stdout


def test_exits_one_when_phone_missing(script, repo_root, tmp_path):
    site = site_copy(repo_root, tmp_path)
    c = site / "contact" / "index.html"
    c.write_text(c.read_text(encoding="utf-8").replace("0983-097-165", "0900-000-000"),
                 encoding="utf-8")
    r = run(script, repo_root, site, "--skip-ping")
    assert r.returncode == 1
    assert "0983-097-165" in r.stdout + r.stderr


# ── C-07：IndexNow 失敗不得被包裝成完成 ───────────────────────
def test_indexnow_failure_fails_the_whole_run(script, repo_root, public_dir, tmp_path):
    stub, _log = ping_stub(tmp_path, exit_code=1)
    r = run(script, repo_root, public_dir, env={"INDEXNOW_SCRIPT": str(stub)})
    assert r.returncode == 1, r.stdout
    assert "POSTDEPLOY_OK" not in r.stdout
    assert "POSTDEPLOY_FAILED" in r.stdout


def test_missing_indexnow_helper_fails(script, repo_root, public_dir, tmp_path):
    r = run(script, repo_root, public_dir,
            env={"INDEXNOW_SCRIPT": str(tmp_path / "does-not-exist.sh")})
    assert r.returncode == 1, r.stdout
    assert "POSTDEPLOY_OK" not in r.stdout


def test_postdeploy_ok_only_when_everything_passed(script, repo_root, public_dir, tmp_path):
    stub, _log = ping_stub(tmp_path, exit_code=0)
    r = run(script, repo_root, public_dir, env={"INDEXNOW_SCRIPT": str(stub)})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "INDEXNOW_OK" in r.stdout and "POSTDEPLOY_OK" in r.stdout


def test_skip_ping_does_not_claim_postdeploy_ok(script, repo_root, public_dir):
    r = run(script, repo_root, public_dir, "--skip-ping")
    assert "POSTDEPLOY_OK" not in r.stdout
    assert "CONTENT_LIVE_OK" in r.stdout


# ── C-08：驗證與推送範圍＝所有含標記的頁面，不是寫死五頁 ───────
def test_pings_given_urls(script, repo_root, public_dir, tmp_path):
    stub, log = ping_stub(tmp_path)
    r = run(script, repo_root, public_dir, "https://aabe.org.tw/",
            "https://aabe.org.tw/impact/", env={"INDEXNOW_SCRIPT": str(stub)})
    assert r.returncode == 0, r.stdout + r.stderr
    assert log.read_text(encoding="utf-8").split() == [
        "https://aabe.org.tw/", "https://aabe.org.tw/impact/"]


def test_default_ping_covers_every_marked_page(script, repo_root, public_dir, tmp_path):
    stub, log = ping_stub(tmp_path)
    run(script, repo_root, public_dir, env={"INDEXNOW_SCRIPT": str(stub)})
    pinged = log.read_text(encoding="utf-8").split()
    for url in ("https://aabe.org.tw/", "https://aabe.org.tw/methodology/",
                "https://aabe.org.tw/impact/", "https://aabe.org.tw/press/"):
        assert url in pinged, f"漏推 {url}"
    assert "https://aabe.org.tw/llms.txt" in pinged


def test_new_marked_page_is_verified_automatically(script, repo_root, tmp_path):
    """未來在 /about/ 加標記，驗證範圍要自動涵蓋（舊版寫死五頁，驗不到）。"""
    work = tmp_path / "repo"
    shutil.copytree(repo_root / "public", work / "public")
    shutil.copytree(repo_root / "_source", work / "_source",
                    ignore=shutil.ignore_patterns("__pycache__"))
    about = work / "public" / "about" / "index.html"
    src = about.read_text(encoding="utf-8")
    about.write_text(src.replace("</body>",
                                 '<p><span data-metric="partners">168+</span></p></body>', 1),
                     encoding="utf-8")
    site = tmp_path / "live"
    shutil.copytree(work / "public", site)
    bad = site / "about" / "index.html"
    bad.write_text(bad.read_text(encoding="utf-8").replace(
        '<span data-metric="partners">168+</span>',
        '<span data-metric="partners">99+</span>', 1), encoding="utf-8")

    r = subprocess.run(["bash", str(work / "_source" / "deploy-automation" / "postdeploy.sh"),
                        "--live-dir", str(site), "--skip-ping"],
                       capture_output=True, text=True, cwd=work, timeout=180)
    assert r.returncode == 1, r.stdout
    assert "/about/" in r.stdout and "partners" in r.stdout

"""⑤ postdeploy.sh：線上實地驗證（LIVE_OK）＋ IndexNow 推送 ＋ 看板待做提醒。"""
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def script(repo_root):
    p = repo_root / "_source" / "deploy-automation" / "postdeploy.sh"
    assert p.exists(), f"缺少 {p}"
    return p


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(directory: Path):
    port = _free_port()
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port),
                             "--bind", "127.0.0.1", "--directory", str(directory)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), 0.1):
                break
        except OSError:
            time.sleep(0.05)
    return proc, f"http://127.0.0.1:{port}"


def run(script, base, repo_root, *args, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run(["bash", str(script), "--base", base, *args],
                          capture_output=True, text=True, cwd=repo_root, env=e, timeout=120)


def test_syntax_ok(script):
    assert subprocess.run(["bash", "-n", str(script)]).returncode == 0


def test_is_executable(script):
    assert os.access(script, os.X_OK), "postdeploy.sh 要可執行（chmod +x）"


def test_checks_all_five_urls_and_phone(script):
    text = script.read_text(encoding="utf-8")
    for path in ("/", "/methodology/", "/contact/", "/press/", "/impact/"):
        assert path in text, f"未涵蓋 {path}"
    assert "0983-097-165" in text, "未比對理事長窗口電話"
    assert "../indexnow-ping.sh" in text, "未呼叫 IndexNow 推送"


def test_live_ok_on_healthy_site(script, repo_root, public_dir):
    proc, base = serve(public_dir)
    try:
        r = run(script, base, repo_root, "--skip-ping")
    finally:
        proc.terminate()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "LIVE_OK" in r.stdout
    assert "0983-097-165" in r.stdout


def test_prints_board_todo_reminder(script, repo_root, public_dir):
    proc, base = serve(public_dir)
    try:
        r = run(script, base, repo_root, "--skip-ping")
    finally:
        proc.terminate()
    assert "看板待做" in r.stdout
    assert "_狀態.md" in r.stdout and "最新交付行" in r.stdout
    assert "日誌" in r.stdout


def test_exits_one_when_a_number_is_stale(script, repo_root, tmp_path):
    site = tmp_path / "public"
    shutil.copytree(repo_root / "public", site)
    idx = site / "index.html"
    idx.write_text(idx.read_text(encoding="utf-8").replace(">66,247<", ">66,000<"),
                   encoding="utf-8")
    proc, base = serve(site)
    try:
        r = run(script, base, repo_root, "--skip-ping")
    finally:
        proc.terminate()
    assert r.returncode == 1
    assert "LIVE_OK" not in r.stdout
    assert "66,247" in r.stdout + r.stderr


def test_exits_one_when_phone_missing(script, repo_root, tmp_path):
    site = tmp_path / "public"
    shutil.copytree(repo_root / "public", site)
    c = site / "contact" / "index.html"
    c.write_text(c.read_text(encoding="utf-8").replace("0983-097-165", "0900-000-000"),
                 encoding="utf-8")
    proc, base = serve(site)
    try:
        r = run(script, base, repo_root, "--skip-ping")
    finally:
        proc.terminate()
    assert r.returncode == 1
    assert "0983-097-165" in r.stdout + r.stderr


def test_pings_given_urls(script, repo_root, public_dir, tmp_path):
    """IndexNow 推送的 URL 可由參數指定；預設推剛驗過的五頁。"""
    stub = tmp_path / "fake-indexnow.sh"
    log = tmp_path / "pinged.txt"
    stub.write_text(f'#!/bin/bash\nprintf "%s\\n" "$@" > "{log}"\n', encoding="utf-8")
    stub.chmod(0o755)
    proc, base = serve(public_dir)
    try:
        r = run(script, base, repo_root, "https://aabe.org.tw/", "https://aabe.org.tw/impact/",
                env={"INDEXNOW_SCRIPT": str(stub)})
    finally:
        proc.terminate()
    assert r.returncode == 0, r.stdout + r.stderr
    assert log.read_text(encoding="utf-8").split() == [
        "https://aabe.org.tw/", "https://aabe.org.tw/impact/"]


def test_default_ping_covers_the_five_verified_pages(script, repo_root, public_dir, tmp_path):
    stub = tmp_path / "fake-indexnow.sh"
    log = tmp_path / "pinged.txt"
    stub.write_text(f'#!/bin/bash\nprintf "%s\\n" "$@" > "{log}"\n', encoding="utf-8")
    stub.chmod(0o755)
    proc, base = serve(public_dir)
    try:
        run(script, base, repo_root, env={"INDEXNOW_SCRIPT": str(stub)})
    finally:
        proc.terminate()
    assert log.read_text(encoding="utf-8").split() == [
        "https://aabe.org.tw/",
        "https://aabe.org.tw/methodology/",
        "https://aabe.org.tw/contact/",
        "https://aabe.org.tw/press/",
        "https://aabe.org.tw/impact/",
    ]

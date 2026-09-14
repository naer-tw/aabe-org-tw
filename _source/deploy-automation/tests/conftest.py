"""pytest 共用設定：讓測試能 import deploy-automation 內的模組，並提供 repo 路徑。"""
import sys
from pathlib import Path

import pytest

AUTOMATION_DIR = Path(__file__).resolve().parent.parent   # _source/deploy-automation
SOURCE_DIR = AUTOMATION_DIR.parent                        # _source
REPO_ROOT = SOURCE_DIR.parent                             # aabe-deploy

if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def public_dir(repo_root: Path) -> Path:
    return repo_root / "public"


@pytest.fixture(scope="session")
def numbers_path(repo_root: Path) -> Path:
    return repo_root / "_source" / "numbers.json"


# ─────────────────────────────────────────────────────────────
# Playwright 共用 fixture（第一批：test_menu_a11y / test_contrast / test_overflow）
#
# 2026-09-14：本機系統 Python 沒裝 playwright（PEP 668 homebrew 鎖住 pip
# 系統安裝），改用獨立 venv `~/.venvs/aabe-pw`（pip install playwright pytest
# && playwright install chromium）執行過，三條測試皆綠（見報告）。系統預設
# pytest 沒有 playwright 套件時，以下 fixture 用 importorskip／try-except
# 讓測試乾淨 SKIP 並印出原因，不會讓整個 pytest run 變紅。
# ─────────────────────────────────────────────────────────────
import functools
import http.server
import threading


@pytest.fixture(scope="session")
def sync_playwright():
    return pytest.importorskip(
        "playwright.sync_api", reason="playwright 套件未安裝（見本檔頭註解的 venv 安裝法）"
    ).sync_playwright


@pytest.fixture(scope="session")
def local_site(public_dir: Path):
    """在 public/ 目錄起一個唯讀本機伺服器，讓根相對路徑（/assets/...）能正確解析。"""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(public_dir))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def browser(sync_playwright):
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # pragma: no cover - 環境沒有瀏覽器執行檔時
            pytest.skip(f"無法啟動 Chromium（{e}）；本機請用 venv 跑："
                        f" ~/.venvs/aabe-pw/bin/python -m playwright install chromium")
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    ctx.close()

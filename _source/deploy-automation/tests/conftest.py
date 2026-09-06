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

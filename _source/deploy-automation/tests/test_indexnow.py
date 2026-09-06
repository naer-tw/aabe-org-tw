"""⑧ indexnow-ping.sh：非 200/202 一律 exit 1（Codex 盲審 C-07）。

舊版只印訊息就 exit 0——key 失效、403、429、甚至沒網路，上游都會當成
「索引已完成」。這裡用假的 curl 驗每一種狀態的 return code。
"""
import subprocess

import pytest


@pytest.fixture(scope="module")
def script(repo_root):
    p = repo_root / "_source" / "indexnow-ping.sh"
    assert p.exists()
    return p


def run_with_fake_curl(script, tmp_path, body: str):
    fake = tmp_path / "bin"
    fake.mkdir(exist_ok=True)
    (fake / "curl").write_text(f"#!/bin/bash\n{body}\n", encoding="utf-8")
    (fake / "curl").chmod(0o755)
    env = {"PATH": f"{fake}:/usr/bin:/bin", "HOME": str(tmp_path)}
    return subprocess.run(["bash", str(script), "https://aabe.org.tw/"],
                          capture_output=True, text=True, env=env, timeout=60)


@pytest.mark.parametrize("status,code", [
    ("200", 0), ("202", 0), ("400", 1), ("403", 1), ("422", 1), ("429", 1), ("500", 1),
])
def test_exit_code_follows_http_status(script, tmp_path, status, code):
    r = run_with_fake_curl(script, tmp_path, f'printf "\\n{status}"')
    assert r.returncode == code, f"HTTP {status} 應該 exit {code}\n{r.stdout}{r.stderr}"


def test_curl_failure_is_not_swallowed(script, tmp_path):
    r = run_with_fake_curl(script, tmp_path, "exit 6")
    assert r.returncode == 1
    assert "curl 失敗" in r.stdout

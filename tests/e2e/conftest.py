"""Playwright e2e 공통 설정.

- 세션마다 Streamlit 서버를 직접 띄운다 (E2E_BASE_URL을 주면 이미 떠 있는 서버를 사용).
- 데이터를 바꿔야 하는 테스트는 임시 폴더에 복사한 데이터로 별도 서버를 띄운다
  (EU_POLICY_DATA_DIR). 실제 data/ 폴더는 절대 수정하지 않는다.
- 스크린샷은 tests/e2e/screenshots/, 측정·수집 결과는 tests/e2e/results/에 저장한다.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

import pytest
import yaml
from playwright.sync_api import Page

from src.loader import load_from_paths

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SHOTS = Path(__file__).parent / "screenshots"
RESULTS = Path(__file__).parent / "results"
SHOTS.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

# 하위 경로(/policies 등)로 바로 접속하면 Streamlit 프런트엔드가 상대 경로로
# <경로>/_stcore/host-config, <경로>/_stcore/health를 먼저 요청해 404가 난 뒤 루트로 재시도한다.
# Streamlit 자체 동작이며 화면에는 영향이 없으므로 이 두 요청만 예외로 둔다 (QA_REPORT 참고).
BENIGN_FAILED_REQUEST = re.compile(r"/[\w-]+/_stcore/(host-config|health)$")

DATA = load_from_paths(DATA_DIR / "policies.yaml", DATA_DIR / "changelog.yaml")
assert not DATA.errors, DATA.errors
BY_ID = {p.id: p for p in DATA.policies}
TODAY = date.today()


def pytest_collection_modifyitems(items):
    for item in items:
        if "tests/e2e" in item.nodeid.replace("\\", "/") or item.nodeid.startswith("e2e"):
            item.add_marker(pytest.mark.e2e)


# ---- 서버 ----

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class StreamlitServer:
    def __init__(self, data_dir: Path | None = None):
        self.port = _free_port()
        self.url = f"http://localhost:{self.port}"
        env = {**os.environ, "PYTHONUTF8": "1"}
        if data_dir:
            env["EU_POLICY_DATA_DIR"] = str(data_dir)
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true",
             "--server.port", str(self.port), "--browser.gatherUsageStats", "false",
             "--server.fileWatcherType", "none"],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                if urllib.request.urlopen(f"{self.url}/_stcore/health", timeout=2).read() == b"ok":
                    return
            except OSError:
                time.sleep(0.5)
        self.stop()
        raise RuntimeError("Streamlit 서버가 60초 안에 시작되지 않았습니다")

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


@pytest.fixture(scope="session")
def app_url():
    if os.environ.get("E2E_BASE_URL"):
        yield os.environ["E2E_BASE_URL"].rstrip("/")
        return
    server = StreamlitServer()
    yield server.url
    server.stop()


@pytest.fixture(scope="module")
def custom_server(tmp_path_factory):
    """mutate(policies:list, changelog:list) -> (policies, changelog) 또는 원시 텍스트로 데이터를 바꿔 서버를 띄운다."""
    servers = []

    def start(mutate=None, raw_policies: str | None = None) -> str:
        d = tmp_path_factory.mktemp("data")
        shutil.copy(DATA_DIR / "changelog.yaml", d / "changelog.yaml")
        if raw_policies is not None:
            (d / "policies.yaml").write_text(raw_policies, encoding="utf-8")
        else:
            policies = yaml.safe_load((DATA_DIR / "policies.yaml").read_text(encoding="utf-8"))
            if mutate:
                policies = mutate(policies)
            (d / "policies.yaml").write_text(yaml.safe_dump(policies, allow_unicode=True, sort_keys=False), encoding="utf-8")
        server = StreamlitServer(d)
        servers.append(server)
        return server.url

    yield start
    for s in servers:
        s.stop()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1440, "height": 900}, "locale": "ko-KR", "accept_downloads": True}


# ---- 페이지 조작 ----

def settle(page: Page, timeout: int = 20000) -> None:
    """Streamlit 재실행이 끝날 때까지 기다린다 (재실행 중인 요소에는 data-stale="true"가 붙는다)."""
    page.wait_for_timeout(250)
    page.wait_for_function("() => !document.querySelector('[data-stale=\"true\"]')", timeout=timeout)
    page.wait_for_timeout(150)


def goto(page: Page, base: str, path: str = "") -> None:
    page.goto(f"{base}/{path}")
    page.locator("h1").first.wait_for(timeout=30000)
    settle(page)


def shot(page: Page, name: str) -> Path:
    path = SHOTS / f"{name}.png"
    page.screenshot(path=path)
    return path


def main_text(page: Page) -> str:
    return " ".join(page.locator("[data-testid=stMain]").inner_text().split())


def sidebar_text(page: Page) -> str:
    return " ".join(page.locator("[data-testid=stSidebar]").inner_text().split())


def norm(text: str) -> str:
    return " ".join(text.split())


def multiselect(page: Page, label: str, options: list[str]) -> None:
    for option in options:
        page.get_by_role("combobox", name=label).click()
        page.get_by_role("option").filter(has_text=re.compile(rf"^{re.escape(option)}$")).click()
        settle(page)
    page.keyboard.press("Escape")
    settle(page)


def selectbox(page: Page, label: str, option: str) -> None:
    page.get_by_role("combobox", name=re.compile(label)).click()
    page.get_by_role("option").filter(has_text=re.compile(rf"^{re.escape(option)}$")).click()
    settle(page)


def type_keyword(page: Page, text: str) -> None:
    box = page.get_by_role("textbox", name="키워드 검색")
    box.fill(text)
    box.press("Enter")
    settle(page)


def nav(page: Page, title: str) -> None:
    page.locator("[data-testid=stSidebarNav] a", has_text=title).click()
    page.locator("h1", has_text=title).first.wait_for(timeout=20000)
    settle(page)


def visible_card_titles(page: Page) -> list[str]:
    return [norm(t) for t in page.locator("[role=tabpanel]:visible .card-title").all_inner_texts()]


def record(name: str, payload) -> None:
    (RESULTS / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

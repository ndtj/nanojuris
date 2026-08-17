"""Shared browser fixtures for the Studio and Workbench E2E suites."""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[2]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Any, call: Any):
    """Expose the test report to the page fixture for failure-only traces."""

    outcome = yield
    setattr(item, f"rep_{call.when}", outcome.get_result())


@pytest.fixture(autouse=True)
def assert_no_browser_errors(page: Any):
    """Fail browser tests when the page emits runtime JavaScript errors."""

    errors: list[str] = []

    def capture_console(message: Any) -> None:
        if message.type == "error":
            errors.append(message.text)

    page.on("console", capture_console)
    page.on("pageerror", lambda error: errors.append(str(error)))
    yield
    assert errors == [], "Browser emitted errors: " + "; ".join(errors)


@pytest.fixture(scope="session")
def browser():
    """Launch one Chromium instance for the browser test session."""

    with playwright_sync.sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Any, request: pytest.FixtureRequest):
    """Create an isolated browser context for each test."""

    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    try:
        yield page
    finally:
        report = getattr(request.node, "rep_call", None)
        if report is not None and report.failed:
            output = Path(os.getenv("NANOJURIS_PLAYWRIGHT_RESULTS", "test-results"))
            output.mkdir(parents=True, exist_ok=True)
            filename = re.sub(r"[^A-Za-z0-9_.-]", "_", request.node.nodeid)[:120]
            context.tracing.stop(path=output / f"{filename}.zip")
        else:
            context.tracing.stop()
        context.close()


@pytest.fixture(scope="session")
def studio_url() -> str:
    """Start the fixture-backed Studio server for the browser session."""

    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "tests.e2e.studio_fixture_app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_server(url)
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{url}/api/health", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Fixture server did not start: {url}")

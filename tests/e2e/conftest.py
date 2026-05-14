"""
E2E browser tests via Playwright.

Requires:
    pip install pytest-playwright
    python -m playwright install chromium

Run with:
    python -m pytest tests/e2e -q
"""

import socket
import subprocess
import sys
import time

import pytest


def get_free_port():
    """Return an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port):
    """Start uvicorn and return the subprocess."""
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


@pytest.fixture(scope="function")
def e2e_base_url():
    """Start uvicorn on a random port and yield its base URL, then shut down.

    Function-scoped to avoid connection reuse issues between browser instances.
    """
    import requests

    port = get_free_port()
    proc = start_server(port)
    base_url = f"http://127.0.0.1:{port}"

    # Wait for the server to be ready
    for _ in range(50):
        try:
            r = requests.get(f"{base_url}/api/voice/capabilities", timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.1)
    else:
        proc.terminate()
        proc.wait(timeout=5)
        raise RuntimeError("E2E server failed to start within 5 seconds")

    yield base_url

    proc.terminate()
    proc.wait(timeout=5)


# Function-scoped browser/page so each test gets a fresh browser context.
# This avoids connection-pool issues where a previous test's pending requests
# block the next test's navigation.
@pytest.fixture(scope="function")
def browser():
    """Launch a fresh Chromium browser for each test."""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    yield browser
    browser.close()
    pw.stop()


@pytest.fixture(scope="function")
def page(browser):
    """Create a new page in the browser for each test."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    page.close()
    context.close()


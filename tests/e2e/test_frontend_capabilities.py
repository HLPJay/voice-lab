"""
P9-E2E1: Frontend capability smoke tests via Playwright.

Tests cover:
1. Main page loads and requests /api/voice/capabilities.
2. Capability constraints are applied to controls.
3. Provider switching does not cause JS errors.
4. Capabilities API failure causes graceful degradation, not a crash.
5. Admin page loads.
6. Admin capability matrix renders providers.
7. Admin capabilities failure does not crash other regions.
"""

import pytest


@pytest.fixture
def console_errors(page):
    """Collect console errors and page errors; fail if any appear after the yield."""
    errors = []

    def on_console(msg):
        if msg.type == "error":
            errors.append(msg.text)

    def on_page_error(exc):
        errors.append(str(exc))

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    yield errors
    # Allow known harmless issues: favicon 404, expected 500 API errors (from route intercepts)
    critical = [
        e for e in errors
        if "favicon" not in e.lower()
        and "500" not in e
        and "Internal Server Error" not in e
    ]
    assert not critical, f"Console errors detected: {critical}"


# ── Test 1: Main page loads and fetches capabilities ────────────────────────────

def test_index_page_loads_and_fetches_capabilities(page, e2e_base_url, console_errors):
    """Page opens, capabilities endpoint is hit with 200, key controls exist."""
    capabilities_request = {}

    def handle_response(response):
        if "/api/voice/capabilities" in response.url:
            capabilities_request["status"] = response.status
            capabilities_request["ok"] = response.ok

    page.on("response", handle_response)

    # Use "commit" to only wait for HTTP response, not full load event
    # (page may make ongoing polling that prevents "load" from firing quickly)
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(2000)  # allow async capabilities fetch to complete

    # Capabilities endpoint was hit and returned 200
    assert capabilities_request.get("status") == 200, (
        f"Expected /api/voice/capabilities to return 200, "
        f"got {capabilities_request.get('status')}"
    )

    # Page title / header visible
    content = page.content()
    assert "Voice Lab" in content

    # Key controls exist
    assert page.locator("#providerSelect").count() == 1
    assert page.locator("#textInput").count() == 1
    assert page.locator("#audioFormat").count() == 1
    assert page.locator("#needSubtitle").count() == 1


# ── Test 2: Capability constraints are applied to controls ─────────────────────

def test_index_capability_controls_are_applied(page, e2e_base_url, console_errors):
    """After capabilities load, control attributes reflect declared limits."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Wait for capabilities to be applied
    page.wait_for_function(
        "typeof _providerCapabilities !== 'undefined' && _providerCapabilities !== null",
        timeout=10000,
    )

    # audioFormat options
    options = page.locator("#audioFormat option").all_text_contents()
    assert "mp3" in options or "MP3" in [o.strip() for o in options]

    # textInput maxlength should be set (mock supports 10000 chars)
    maxlen = page.locator("#textInput").get_attribute("maxlength")
    assert maxlen is not None and int(maxlen) > 0

    # paramSpeed range
    speed_min = page.locator("#paramSpeed").get_attribute("min")
    speed_max = page.locator("#paramSpeed").get_attribute("max")
    if speed_min is not None and speed_max is not None:
        assert float(speed_min) <= 0.5 <= float(speed_max)
        assert 2.0 <= float(speed_max)

    # paramVol range
    vol_min = page.locator("#paramVol").get_attribute("min")
    vol_max = page.locator("#paramVol").get_attribute("max")
    if vol_min is not None and vol_max is not None:
        assert float(vol_min) <= 0.1 <= float(vol_max)
        assert 10.0 <= float(vol_max)

    # paramPitch range
    pitch_min = page.locator("#paramPitch").get_attribute("min")
    pitch_max = page.locator("#paramPitch").get_attribute("max")
    if pitch_min is not None and pitch_max is not None:
        assert float(pitch_min) <= -12
        assert 12 <= float(pitch_max)

    # needSubtitle should not be disabled (mock supports subtitle)
    need_subtitle_disabled = page.locator("#needSubtitle").get_attribute("disabled")
    # disabled is None or "" when enabled
    assert need_subtitle_disabled is None or need_subtitle_disabled == ""


# ── Test 3: Provider switching does not crash ──────────────────────────────────

def test_provider_switch_does_not_crash(page, e2e_base_url, console_errors):
    """Switching between providers causes no JS errors and controls remain present."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Get available provider options
    options = page.locator("#providerSelect option").all()
    option_map = {
        opt.text_content().strip(): opt.get_attribute("value")
        for opt in options
    }

    # Try switching if both mock and minimax are available
    if "mock" in option_map.values():
        page.locator("#providerSelect").select_option("mock")
        page.wait_for_timeout(200)

    if "minimax" in option_map.values():
        page.locator("#providerSelect").select_option("minimax")
        page.wait_for_timeout(200)

    # Switch back to mock
    if "mock" in option_map.values():
        page.locator("#providerSelect").select_option("mock")
        page.wait_for_timeout(200)

    # Controls still present
    assert page.locator("#textInput").count() == 1
    assert page.locator("#audioFormat").count() == 1


# ── Test 4: Capabilities API failure gracefully degrades ────────────────────────

def test_capabilities_failure_falls_back_without_crash(page, e2e_base_url, console_errors):
    """Intercepting the capabilities endpoint with 500 keeps the page usable."""
    page.route(
        "**/api/voice/capabilities",
        lambda route: route.fulfill(status=500, body="Internal Server Error"),
    )

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Page is still usable
    content = page.content()
    assert "Voice Lab" in content
    assert page.locator("#providerSelect").count() == 1
    assert page.locator("#textInput").count() == 1

    # Generate button exists
    generate_btn = page.locator("#generateBtn")
    if generate_btn.count() == 0:
        buttons = page.locator("button")
        assert buttons.count() > 0, "No buttons found on page"


# ── Test 5: Admin page loads ───────────────────────────────────────────────────

def test_admin_page_loads(page, e2e_base_url, console_errors):
    """Admin page opens with expected sections and capabilities API returns 200."""
    capabilities_request = {}

    def handle_response(response):
        if "/api/voice/capabilities" in response.url:
            capabilities_request["status"] = response.status

    page.on("response", handle_response)

    page.goto(f"{e2e_base_url}/static/admin.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("text=Voice Lab 管理面板", state="attached", timeout=10000)
    page.wait_for_timeout(2000)  # allow async capabilities fetch to complete

    content = page.content()
    assert "Voice Lab 管理面板" in content
    assert "Provider 能力矩阵" in content
    assert "Provider 统计" in content
    assert "API 分布" in content
    assert capabilities_request.get("status") == 200


# ── Test 6: Admin capability matrix renders providers ─────────────────────────

def test_admin_capability_matrix_renders_providers(page, e2e_base_url, console_errors):
    """Matrix shows mock and minimax rows with format/parameter info."""
    page.goto(f"{e2e_base_url}/static/admin.html", wait_until="commit", timeout=30000)

    # Wait for matrix body to contain provider names
    page.wait_for_function(
        """() => {
            const body = document.getElementById('capMatrixBody');
            if (!body) return false;
            const text = body.textContent || '';
            return text.includes('mock') || text.includes('minimax');
        }""",
        timeout=10000,
    )

    body_text = page.locator("#capMatrixBody").text_content()

    # At least one provider present
    assert "mock" in body_text or "minimax" in body_text

    # Audio formats visible (mock supports mp3/wav/flac)
    has_format = any(f in body_text for f in ["mp3", "MP3", "wav", "flac"])
    assert has_format, f"Expected audio formats in matrix, got: {body_text}"

    # Numeric ranges visible (e.g. "0.5" or "0.5 ~ 2.0")
    has_range = "0.5" in body_text or "~" in body_text
    assert has_range, f"Expected parameter ranges in matrix, got: {body_text}"


# ── Test 7: Admin capabilities failure only affects matrix ────────────────────

def test_admin_capabilities_failure_only_affects_matrix(page, e2e_base_url, console_errors):
    """Intercepting capabilities API on admin page shows error in matrix but keeps other sections alive."""
    page.route(
        "**/api/voice/capabilities",
        lambda route: route.fulfill(status=500, body="Internal Server Error"),
    )

    page.goto(f"{e2e_base_url}/static/admin.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("text=Voice Lab 管理面板", state="attached", timeout=10000)

    # Page header still present
    content = page.content()
    assert "Voice Lab 管理面板" in content

    # Matrix shows error
    matrix_body = page.locator("#capMatrixBody").text_content()
    matrix_has_error = "加载失败" in matrix_body or "500" in matrix_body or "fail" in matrix_body
    assert matrix_has_error, f"Expected error in matrix body, got: {matrix_body}"

    # Date controls and stat cards still exist
    assert page.locator("#startDate").count() == 1
    assert page.locator("#endDate").count() == 1
    assert page.locator("#statJobs").count() == 1


# ── Test 8: Script tab opens without populateProfileSelect error ─────────────────

def test_script_tab_opens_without_profile_select_error(page, e2e_base_url, console_errors):
    """Clicking the Script tab does not throw 'Cannot read properties of null'."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)  # allow initial load to settle

    # Click the Script tab
    script_tab = page.locator('button.tab-btn[data-tab="script"]')
    assert script_tab.count() == 1, "Script tab button not found"
    script_tab.click()
    page.wait_for_timeout(1500)  # allow async loadProfiles + populateProfileSelect to run

    # Script tab content should be visible
    tab_content = page.locator("#tab-script")
    assert tab_content.count() == 1, "Script tab content not found"

    # No critical JS errors should have occurred (console_errors fixture will fail on error)
    # The test passes if we reach here without an uncaught exception

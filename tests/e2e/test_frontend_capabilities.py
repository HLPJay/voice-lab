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

import json
import re
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
    # Allow known harmless issues: favicon 404, expected 500 API errors, expected 400 from mock intercepts
    critical = [
        e for e in errors
        if "favicon" not in e.lower()
        and "500" not in e
        and "400" not in e
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


# ── Test 9: History module is loaded ─────────────────────────────────────────────

def test_history_module_is_loaded(page, e2e_base_url, console_errors):
    """history.js script tag exists and window global functions are available."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)  # allow scripts to initialize

    # history.js script tag exists
    assert page.evaluate("!!document.querySelector('script[src=\"/static/js/history.js\"]')")

    # window global functions are exposed
    assert page.evaluate("typeof window.loadHistory === 'function'")
    assert page.evaluate("typeof window.refreshHistory === 'function'")
    assert page.evaluate("typeof window.renderHistoryList === 'function'")

    # state variable is initialized
    assert page.evaluate("typeof window._historyJobs !== 'undefined'")


# ── Test 10: History Tab opens and refreshes without error ──────────────────────

def test_history_tab_opens_and_refreshes_without_error(page, e2e_base_url, console_errors):
    """Clicking the History tab, waiting for list, and clicking refresh causes no JS errors."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Click the History tab
    history_tab = page.locator('button.tab-btn[data-tab="history"]')
    assert history_tab.count() == 1, "History tab button not found"
    history_tab.click()

    page.wait_for_selector("#tab-history", state="attached", timeout=10000)
    page.wait_for_selector("#historyList", state="attached", timeout=10000)
    page.wait_for_timeout(1500)  # allow loadHistory to execute

    # historyList must exist
    assert page.locator("#historyList").count() == 1

    # Click refresh button if present
    refresh_btn = page.locator("#historyRefreshBtn")
    if refresh_btn.count() == 1:
        refresh_btn.click()
        page.wait_for_timeout(800)

    # Search input: type and clear if present
    search = page.locator("#historySearch")
    if search.count() == 1:
        search.fill("test")
        page.wait_for_timeout(300)
        search.fill("")
        page.wait_for_timeout(300)

    # Status filter: select 'all' if present
    status_filter = page.locator("#historyStatusFilter")
    if status_filter.count() == 1:
        status_filter.select_option("all")
        page.wait_for_timeout(300)

    # loadMoreHistory button exists but not required to be clicked
    # (test environment may have no more data)

    # No critical JS errors occurred
    # console_errors fixture will fail on real JS errors


# ── Test 11: Audition records module and voices tab open ──────────────────────────

def test_audition_records_module_and_voices_tab_open(page, e2e_base_url, console_errors):
    """audition_records.js is loaded and voices tab opens without JS errors."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)  # allow scripts to initialize

    # audition_records.js script tag exists
    assert page.evaluate("!!document.querySelector('script[src=\"/static/js/audition_records.js\"]')")

    # window global functions are exposed
    assert page.evaluate("typeof window.renderAuditionRecords === 'function'")
    assert page.evaluate("typeof window.deleteAuditionRecord === 'function'")
    assert page.evaluate("typeof window.clearAuditionRecords === 'function'")

    # state variable is initialized
    assert page.evaluate("typeof window._auditionRecords !== 'undefined'")

    # Click the Voices tab
    voices_tab = page.locator('button.tab-btn[data-tab="voices"]')
    assert voices_tab.count() == 1, "Voices tab button not found"
    voices_tab.click()

    page.wait_for_selector("#tab-voices", state="attached", timeout=10000)
    page.wait_for_timeout(2000)  # allow tab switch to settle

    # voiceListResults container exists (defined directly in HTML, always present)
    assert page.locator("#voiceListResults").count() == 1

    # No critical JS errors occurred
    # console_errors fixture will fail on real JS errors


# ── Test 12: Audition records render and delete ──────────────────────────────────

def test_audition_records_render_and_delete(page, e2e_base_url, console_errors):
    """Inject a test record, render it, delete it, verify empty state."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)

    # Inject the auditionRecordsTable container directly into the static #voiceListResults div.
    # (The real #voiceAuditionPanel + #auditionRecordsTable are only created by
    # renderVoiceTable() after a successful loadVoices() call, which requires a
    # real/mock provider API. Injecting the minimal HTML avoids that dependency.)
    page.evaluate("""
        () => {
            const resultsEl = document.getElementById('voiceListResults');
            resultsEl.innerHTML = '<div id="voiceAuditionPanel"><div id="auditionRecordsPanel"><div id="auditionCount"></div><div id="auditionRecordsTable"></div></div></div>';
        }
    """)

    # Wait for the injected container to be present
    page.wait_for_selector("#auditionRecordsTable", state="attached", timeout=5000)

    # Inject a test record and render
    page.evaluate("""
        () => {
            window._auditionRecords = [
                {
                    voiceId: 'test_voice_001',
                    voiceName: '测试音色',
                    text: '这是一段用于试听记录渲染测试的文本',
                    audioUrl: null
                }
            ];
            window.renderAuditionRecords();
        }
    """)

    # Assert record content is visible
    body = page.locator("#auditionRecordsTable").text_content()
    assert "test_voice_001" in body, f"Expected voiceId in table, got: {body}"
    assert "测试音色" in body, f"Expected voiceName in table, got: {body}"
    assert "试听记录渲染测试" in body, f"Expected text preview in table, got: {body}"

    # Delete button exists
    delete_btn = page.locator('#auditionRecordsTable [data-delete="0"]')
    assert delete_btn.count() == 1, "Delete button not found"

    # Click delete button via JS (the delegated event listener from
    # setupAuditionWorkstation is not attached since we bypassed renderVoiceTable,
    # so we call window.deleteAuditionRecord directly)
    page.evaluate("window.deleteAuditionRecord(0)")
    page.wait_for_timeout(300)

    # Assert record was deleted and empty state shown
    assert page.evaluate("window._auditionRecords.length") == 0, "Record should be deleted"
    empty_state = page.locator("#auditionRecordsTable").text_content()
    assert "暂无试听记录" in empty_state, f"Expected empty state, got: {empty_state}"


# ── Test 13: Longtext batch result helpers are exposed ──────────────────────────

def test_batch_longtext_result_helpers_are_exposed(page, e2e_base_url, console_errors):
    """showBatchLongtextResult / clearBatchLongtextResult are window functions and work."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)

    # Click the Longtext tab
    longtext_tab = page.locator('button.tab-btn[data-tab="longtext"]')
    assert longtext_tab.count() == 1, "Longtext tab button not found"
    longtext_tab.click()
    page.wait_for_selector("#tab-longtext", state="attached", timeout=10000)
    page.wait_for_timeout(500)

    # Helper functions are on window
    assert page.evaluate("typeof window.showBatchLongtextResult === 'function'"), \
        "window.showBatchLongtextResult should be a function"
    assert page.evaluate("typeof window.clearBatchLongtextResult === 'function'"), \
        "window.clearBatchLongtextResult should be a function"

    # Calling showBatchLongtextResult with test HTML renders it
    page.evaluate("window.showBatchLongtextResult('<div id=\"testBatchLongtextResultMarker\">测试结果</div>')")
    marker = page.locator("#testBatchLongtextResultMarker")
    assert marker.count() == 1, "Test marker should appear after showBatchLongtextResult"
    assert "测试结果" in marker.text_content()

    # Calling clearBatchLongtextResult clears it
    page.evaluate("window.clearBatchLongtextResult()")
    assert page.locator("#testBatchLongtextResultMarker").count() == 0, \
        "Test marker should be gone after clearBatchLongtextResult"


# ── Test 14: Batch longtext module loaded and validation works ──────────────────

def test_batch_longtext_module_is_loaded_and_submit_validation_works(
    page, e2e_base_url, console_errors
):
    """batch_longtext.js is loaded, window.handleBatchLongtextSubmit exists, and validation works."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)

    # batch_longtext.js script tag exists
    assert page.evaluate(
        "!!document.querySelector('script[src=\"/static/js/batch_longtext.js\"]')"
    ), "batch_longtext.js should be loaded"

    # window.handleBatchLongtextSubmit is a function
    assert page.evaluate(
        "typeof window.handleBatchLongtextSubmit === 'function'"
    ), "window.handleBatchLongtextSubmit should be a function"

    # Click the Longtext tab
    longtext_tab = page.locator('button.tab-btn[data-tab="longtext"]')
    assert longtext_tab.count() == 1, "Longtext tab button not found"
    longtext_tab.click()
    page.wait_for_selector("#tab-longtext", state="attached", timeout=10000)
    page.wait_for_timeout(500)

    # Abort the batch API to ensure validation fires before any network call
    page.route("**/api/voice/batch/submit", lambda route: route.abort())

    # Click submit with empty batchText — validation should fire and show error
    submit_btn = page.locator("#batchLongtextSubmit")
    assert submit_btn.count() == 1, "batchLongtextSubmit button not found"
    submit_btn.click()
    page.wait_for_timeout(500)

    # Error message "请输入待分段文本" should appear
    result_html = page.locator("#batchLongtextResult").inner_html()
    assert "请输入待分段文本" in result_html, (
        f"Expected validation error for empty text, got: {result_html}"
    )


# ── Test 15: Batch longtext mock submit success starts progress ──────────────────

def test_batch_longtext_mock_submit_success_starts_progress(
    page, e2e_base_url, console_errors
):
    """Mock batch/submit + status so handleBatchLongtextSubmit completes without real MiniMax."""
    submit_called = {}

    def handle_submit(route):
        submit_called["yes"] = True
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "batch_id": "e2e_batch_longtext_001",
                "status": "queued"
            }),
        )

    def handle_status(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "batch_id": "e2e_batch_longtext_001",
                "status": "processing",
                "total_segments": 1,
                "completed_segments": 0,
                "failed_segments": 0,
                "segments": [{
                    "index": 0,
                    "text_preview": "test",
                    "status": "processing",
                    "role": None,
                    "duration_ms": None,
                    "error_message": None,
                }]
            }),
        )

    # Register routes BEFORE navigation (routes must be registered before page.goto)
    page.route("**/api/voice/batch/submit", handle_submit)
    page.route("**/api/voice/batch/e2e_batch_longtext_001/status", handle_status)

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="load", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Navigate to Longtext tab
    page.locator('button.tab-btn[data-tab="longtext"]').click()
    page.wait_for_selector("#tab-longtext", state="attached", timeout=10000)
    page.wait_for_timeout(500)

    # Fill in the text field
    page.locator("#batchText").fill("这是一段用于长文本批量提交E2E的测试文本。")

    # Inject profile option and set provider to mock to bypass confirm dialog
    # (provider defaults to 'minimax' which triggers guardedJsonFetch's confirm dialog)
    page.evaluate(""" () => {
        const sel = document.getElementById('batchProfile');
        sel.innerHTML = '<option value="e2e_test_profile">E2E Test Profile</option>';
        sel.value = 'e2e_test_profile';
        const providerSel = document.getElementById('batchProvider');
        if (providerSel) {
            providerSel.value = 'mock';
        }
    } """)

    # Click submit
    page.locator("#batchLongtextSubmit").click()
    page.wait_for_timeout(2000)

    # Verify submit was called
    assert submit_called.get("yes"), f"batch/submit should have been called: {submit_called}"

    # Verify progress panel is shown
    progress_panel = page.locator("#batchProgressPanel")
    assert progress_panel.count() == 1, "batchProgressPanel should exist"

    # Verify button text restored
    btn_text = page.locator("#batchLongtextSubmit").text_content()
    assert "提交批量任务" in btn_text, f"Button should be restored, got: {btn_text}"


# ── Test 16: Script batch submit validation works ──────────────────────────────────

def test_batch_script_submit_validation_works(page, e2e_base_url, console_errors):
    """Script tab shows front-end validation error when submitting with empty lines."""
    # Abort the batch API before navigation to prevent any real calls
    page.route("**/api/voice/batch/submit", lambda route: route.abort())

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)

    # Click the Script tab
    script_tab = page.locator('button.tab-btn[data-tab="script"]')
    assert script_tab.count() == 1, "Script tab button not found"
    script_tab.click()
    page.wait_for_selector("#tab-script", state="attached", timeout=10000)
    page.wait_for_timeout(1000)  # allow addScriptLine() to init default rows

    # Verify key controls exist
    assert page.locator("#batchScriptSubmit").count() == 1, "batchScriptSubmit button not found"
    assert page.locator("#scriptLines").count() == 1, "scriptLines container not found"

    # Page initialises with 3 empty script lines — submit without filling anything
    submit_btn = page.locator("#batchScriptSubmit")
    submit_btn.click()
    page.wait_for_timeout(500)

    # Validation error: "请至少填写一行台词" should appear in the result area
    result_html = page.locator("#batchScriptResult").inner_html()
    assert "请至少填写一行台词" in result_html, (
        f"Expected validation error for empty lines, got: {result_html}"
    )


# ── Test 17: batch_script.js module is loaded and validation still works ────────────

def test_batch_script_module_is_loaded_and_submit_validation_still_works(
    page, e2e_base_url, console_errors
):
    """batch_script.js is loaded, window.handleBatchScriptSubmit exists, and validation works."""
    page.goto(f"{e2e_base_url}/static/index.html", wait_until="commit", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)
    page.wait_for_timeout(1000)

    # batch_script.js script tag exists
    assert page.evaluate(
        "!!document.querySelector('script[src=\"/static/js/batch_script.js\"]')"
    ), "batch_script.js should be loaded"

    # window.handleBatchScriptSubmit is a function
    assert page.evaluate(
        "typeof window.handleBatchScriptSubmit === 'function'"
    ), "window.handleBatchScriptSubmit should be a function"

    # Click the Script tab
    script_tab = page.locator('button.tab-btn[data-tab="script"]')
    assert script_tab.count() == 1, "Script tab button not found"
    script_tab.click()
    page.wait_for_selector("#tab-script", state="attached", timeout=10000)
    page.wait_for_timeout(1000)

    # Abort the batch API to ensure validation fires before any network call
    page.route("**/api/voice/batch/submit", lambda route: route.abort())

    # Click submit with empty lines — validation should fire
    submit_btn = page.locator("#batchScriptSubmit")
    assert submit_btn.count() == 1, "batchScriptSubmit button not found"
    submit_btn.click()
    page.wait_for_timeout(500)

    # Error message "请至少填写一行台词" should appear
    result_html = page.locator("#batchScriptResult").inner_html()
    assert "请至少填写一行台词" in result_html, (
        f"Expected validation error for empty lines, got: {result_html}"
    )


# ── Test 18: batch_script.js mock submit success starts progress ────────────────────

def test_batch_script_mock_submit_success_starts_progress(
    page, e2e_base_url, console_errors
):
    """Mock batch/submit + status so handleBatchScriptSubmit completes without real MiniMax."""
    submit_called = {}

    def handle_submit(route):
        submit_called["yes"] = True
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "batch_id": "e2e_batch_script_001",
                "status": "queued",
                "total_segments": 1,
            }),
        )

    def handle_status(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "batch_id": "e2e_batch_script_001",
                "status": "processing",
                "total_segments": 1,
                "completed_segments": 0,
                "failed_segments": 0,
                "segments": [{
                    "index": 0,
                    "role": "旁白",
                    "text_preview": "这是一句剧本台词",
                    "status": "processing",
                    "duration_ms": None,
                    "error_message": None,
                }]
            }),
        )

    # Register routes BEFORE navigation
    page.route("**/api/voice/batch/submit", handle_submit)
    page.route("**/api/voice/batch/e2e_batch_script_001/status", handle_status)

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="load", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Navigate to Script tab
    page.locator('button.tab-btn[data-tab="script"]').click()
    page.wait_for_selector("#tab-script", state="attached", timeout=10000)
    page.wait_for_timeout(1500)  # allow addScriptLine + loadProfiles to complete

    # Set up valid script row state AND DOM values for all 3 default rows
    # (per-row validation checks ALL _scriptRows entries, not just lines entries)
    page.evaluate(""" () => {
        // Set state and DOM for ALL 3 default rows (per-row validation checks every row)
        for (var i = 0; i < 3; i++) {
            // State
            if (typeof _scriptRows !== 'undefined' && _scriptRows[i]) {
                _scriptRows[i].role = '旁白';
                _scriptRows[i].text = '第' + (i+1) + '句台词';
                _scriptRows[i].profileId = 'e2e_test_profile';
            }
            // DOM - role
            var roleEl = document.getElementById('scriptRole_' + i);
            if (roleEl) roleEl.value = '旁白';
            // DOM - text
            var textEl = document.getElementById('scriptText_' + i);
            if (textEl) textEl.value = '第' + (i+1) + '句台词';
            // DOM - profile
            var sel = document.getElementById('scriptProfile_' + i);
            if (sel) {
                sel.innerHTML = '<option value="e2e_test_profile">E2E Test Profile</option>';
                sel.value = 'e2e_test_profile';
            }
        }

        // Set provider to mock to bypass guardedJsonFetch confirm dialog
        var providerSel = document.getElementById('batchScriptProvider');
        if (providerSel) providerSel.value = 'mock';
    } """)

    # Click submit button — onclick="handleBatchScriptSubmit()" fires in the browser
    page.locator("#batchScriptSubmit").click()

    # Wait for the API call to complete (async operation)
    import time
    start = time.time()
    while time.time() - start < 5:
        if submit_called.get("yes"):
            break
        page.wait_for_timeout(200)

    page.wait_for_timeout(500)  # allow DOM updates to settle

    # Verify submit was called
    assert submit_called.get("yes"), f"batch/submit should have been called: {submit_called}"

    # Verify "批量剧本任务已提交" appears in result area
    result_html = page.locator("#batchScriptResult").inner_html()
    assert "批量剧本任务已提交" in result_html, (
        f"Expected success message, got: {result_html}"
    )
    assert "e2e_batch_script_001" in result_html, (
        f"Expected batch_id in result, got: {result_html}"
    )

    # Verify progress panel is shown
    progress_panel = page.locator("#batchScriptProgressPanel")
    assert progress_panel.count() == 1, "batchScriptProgressPanel should exist"

    # Verify button text restored
    btn_text = page.locator("#batchScriptSubmit").text_content()
    assert "提交批量任务" in btn_text, f"Button should be restored, got: {btn_text}"

    # Clean up: stop any batch poll timer left behind
    page.evaluate("window.stopBatchPoll && window.stopBatchPoll()")


# ── Test 19: Voice clone insufficient balance error display ────────────────────

def test_voice_clone_error_insufficient_balance_is_displayed(
    page, e2e_base_url, console_errors
):
    """Intercept clone/create to return insufficient balance error; verify detail is displayed."""

    clone_called = {}

    # Mock capabilities so mock provider advertises voice_clone support
    def handle_capabilities(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "providers": [{
                    "provider": "mock",
                    "voice_clone": {
                        "supported": True,
                        "preview_text_max": 1000,
                        "voice_id": {"min_length": 8, "max_length": 256}
                    }
                }]
            }),
        )

    # Mock clone/create to return insufficient balance error
    def handle_clone_create(route):
        clone_called["yes"] = True
        route.fulfill(
            status=400,
            content_type="application/json",
            body=json.dumps({
                "error": {
                    "code": "PROVIDER_ERROR",
                    "message": "MiniMax voice clone failed",
                    "detail": "insufficient balance",
                    "job_id": None
                }
            }),
        )

    # Register routes BEFORE navigation
    page.route("**/api/voice/capabilities", handle_capabilities)
    # Use full URL with port to ensure exact match
    page.route(re.compile(r"http://127\.0\.0\.1:\d+/api/voice/clone/create.*"), handle_clone_create)

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="load", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Wait for capabilities to be loaded and applied
    page.wait_for_timeout(1000)

    # Navigate to Advanced tab (contains clone subtab)
    page.locator('button.tab-btn[data-tab="advanced"]').click()
    page.wait_for_selector("#tab-advanced", state="attached", timeout=10000)

    # Clone subtab is active by default; confirm clone form elements exist
    page.wait_for_selector("#cloneProvider", state="attached", timeout=5000)
    page.wait_for_selector("#cloneVoiceId", state="attached", timeout=5000)
    page.wait_for_selector("#cloneFileId", state="attached", timeout=5000)

    # Set provider to mock (bypasses highRisk confirm) and fill valid clone form
    page.evaluate(""" () => {
        document.getElementById('cloneProvider').value = 'mock';
        // Trigger change so capability re-applies
        document.getElementById('cloneProvider').dispatchEvent(new Event('change'));
    } """)

    # Fill required fields; use valid voice_id pattern (min 8 chars, starts with letter)
    page.locator("#cloneVoiceId").fill("e2e_clone_voice_001")
    page.locator("#cloneFileId").fill("123456")
    # previewText and model already have default values; ensure model is set
    page.locator("#cloneModel").fill("speech-2.8-hd")

    # Verify clone button is enabled before clicking
    clone_btn_disabled = page.locator("#cloneBtn").get_attribute("disabled")
    assert not clone_btn_disabled, "cloneBtn should be enabled with valid inputs and mock capability"

    # Click clone via JS click() to ensure the onclick handler fires
    page.evaluate("document.getElementById('cloneBtn').click()")
    page.wait_for_timeout(1500)

    # Verify API was called
    assert clone_called.get("yes"), f"clone/create should have been called: {clone_called}"

    # Verify insufficient balance detail is displayed in cloneResult
    result_html = page.locator("#cloneResult").inner_html()
    assert "insufficient balance" in result_html or "余额不足" in result_html, (
        f"Expected 'insufficient balance' or '余额不足' in cloneResult, got: {result_html}"
    )


# ── Test 20: Voice design mock submit success ─────────────────────────────────

def test_voice_design_mock_submit_success(
    page, e2e_base_url, console_errors
):
    """Mock design/create to return success; verify design success result and button restore."""

    design_called = {}

    # Mock capabilities so mock provider advertises voice_design support
    def handle_capabilities(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "providers": [{
                    "provider": "mock",
                    "voice_design": {
                        "supported": True,
                        "prompt_max": 2000,
                        "preview_text_max": 500
                    }
                }]
            }),
        )

    # Mock design/create to return success
    def handle_design_create(route):
        design_called["yes"] = True
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "voice_id": "e2e_design_voice_001",
                "message": "声音设计成功创建",
                "trial_audio_url": None
            }),
        )

    # Register routes BEFORE navigation
    page.route("**/api/voice/capabilities", handle_capabilities)
    page.route(re.compile(r"http://127\.0\.0\.1:\d+/api/voice/design/create.*"), handle_design_create)

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="load", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Wait for capabilities to be loaded
    page.wait_for_timeout(1000)

    # Navigate to Advanced tab
    page.locator('button.tab-btn[data-tab="advanced"]').click()
    page.wait_for_selector("#tab-advanced", state="attached", timeout=10000)

    # Switch to Design subtab
    page.locator('button.advanced-subtab-btn[data-advanced-subtab="design"]').click()
    page.wait_for_selector("#designResult", state="attached", timeout=5000)

    # Verify design form elements
    page.wait_for_selector("#designProvider", state="attached", timeout=5000)
    page.wait_for_selector("#designPrompt", state="attached", timeout=5000)
    page.wait_for_selector("#designPreviewText", state="attached", timeout=5000)
    page.wait_for_selector("#designBtn", state="attached", timeout=5000)

    # Set provider to mock and trigger capability re-apply
    page.evaluate(""" () => {
        document.getElementById('designProvider').value = 'mock';
        document.getElementById('designProvider').dispatchEvent(new Event('change'));
    } """)

    # Fill design form (prompt and previewText are required; voiceId is optional)
    page.locator("#designPrompt").fill("温暖，自然，适合旁白的男声")
    page.locator("#designPreviewText").fill("这是一段用于声音设计E2E的试听文本")

    # Verify design button is enabled
    design_btn_disabled = page.locator("#designBtn").get_attribute("disabled")
    assert not design_btn_disabled, "designBtn should be enabled with valid inputs and mock capability"

    # Click design button via JS click
    page.evaluate("document.getElementById('designBtn').click()")
    page.wait_for_timeout(1500)

    # Verify API was called
    assert design_called.get("yes"), f"design/create should have been called: {design_called}"

    # Verify success message appears in designResult
    result_html = page.locator("#designResult").inner_html()
    assert "设计成功" in result_html, (
        f"Expected '设计成功' in designResult, got: {result_html}"
    )
    assert "e2e_design_voice_001" in result_html, (
        f"Expected voice_id 'e2e_design_voice_001' in designResult, got: {result_html}"
    )

    # Verify button text is restored
    btn_text = page.locator("#designBtn").text_content()
    assert "生成设计" in btn_text, f"Button should be restored, got: {btn_text}"


# ── Test 21: Voice helper window exports are available ───────────────────────────

def test_voice_helper_window_exports_are_available(
    page, e2e_base_url, console_errors
):
    """Verify that voice clone/design migration helpers are exposed as window.* entries."""

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="load", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Verify all required window helpers are functions
    helpers_ok = page.evaluate(""" () => {
        const required = [
            'isValidVoiceId',
            'loadProfiles',
            'populateProfileSelect',
            'bindVoiceToProfile',
            'renderInlineCreateProfile',
            'hexToBlobUrl'
        ];
        const results = {};
        for (const name of required) {
            results[name] = typeof window[name] === 'function';
        }
        return results;
    } """)

    for name, is_fn in helpers_ok.items():
        assert is_fn, f"window.{name} should be a function, got: {type(window[name]).__name__ if name in globals() else 'undefined'}"

    # Verify isValidVoiceId basic behavior
    voice_id_valid = page.evaluate("window.isValidVoiceId('e2e_clone_voice_001')")
    assert voice_id_valid is True, "isValidVoiceId should return true for valid voice_id 'e2e_clone_voice_001'"

    # Verify invalid voice_ids are rejected
    invalid_cases = page.evaluate(""" () => {
        return [
            window.isValidVoiceId('abc'),           // too short
            window.isValidVoiceId('123abc'),        // starts with number
            window.isValidVoiceId('abc-'),           // ends with hyphen
            window.isValidVoiceId(''),              // empty
        ];
    } """)
    assert not any(invalid_cases), f"isValidVoiceId should return false for invalid IDs: {invalid_cases}"


# ── Test 22: Voice clone module is loaded and exports available ─────────────────

def test_voice_clone_module_is_loaded_and_exports_available(
    page, e2e_base_url, console_errors
):
    """Verify voice_clone.js is loaded and exposes handleUploadAudio / handleCloneAutoId / updateCloneBtnState / handleCloneVoice."""

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="load", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Verify script tag exists
    script_tag = page.locator('script[src="/static/js/voice_clone.js"]')
    assert script_tag.count() == 1, "voice_clone.js script tag should exist"

    # Verify all required window exports are functions
    exports_ok = page.evaluate(""" () => {
        const required = [
            'handleUploadAudio',
            'handleCloneAutoId',
            'updateCloneBtnState',
            'handleCloneVoice'
        ];
        const results = {};
        for (const name of required) {
            results[name] = typeof window[name] === 'function';
        }
        return results;
    } """)

    for name, is_fn in exports_ok.items():
        assert is_fn, "window.%s should be a function" % name


# ── Test 23: Voice clone mock submit success ─────────────────────────────────────

def test_voice_clone_mock_submit_success(
    page, e2e_base_url, console_errors
):
    """Mock clone/create to return success; verify clone success result, audio player, quick bind/preview panels, and button restore."""

    clone_called = {}

    # Mock capabilities so mock provider advertises voice_clone support
    def handle_capabilities(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "providers": [{
                    "provider": "mock",
                    "voice_clone": {
                        "supported": True,
                        "preview_text_max": 1000,
                        "voice_id": {"min_length": 8, "max_length": 256}
                    }
                }]
            }),
        )

    # Mock clone/create to return success
    def handle_clone_create(route):
        clone_called["yes"] = True
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "voice_id": "e2e_clone_voice_success_001",
                "message": "声音克隆成功创建",
                "demo_audio_url": "/static/e2e-clone-demo.mp3"
            }),
        )

    # Mock provider-voices (called by handleListVoices(true) after clone success)
    def handle_provider_voices(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"voices": [], "total": 0}),
        )

    # Register routes BEFORE navigation
    page.route("**/api/voice/capabilities", handle_capabilities)
    page.route(re.compile(r"http://127\.0\.0\.1:\d+/api/voice/clone/create.*"), handle_clone_create)
    page.route(re.compile(r"http://127\.0\.0\.1:\d+/api/voice/provider-voices.*"), handle_provider_voices)

    page.goto(f"{e2e_base_url}/static/index.html", wait_until="load", timeout=30000)
    page.wait_for_selector("#providerSelect", state="attached", timeout=10000)

    # Wait for capabilities to be loaded
    page.wait_for_timeout(1000)

    # Navigate to Advanced tab (contains clone subtab)
    page.locator('button.tab-btn[data-tab="advanced"]').click()
    page.wait_for_selector("#tab-advanced", state="attached", timeout=10000)

    # Clone subtab is active by default; confirm clone form elements exist
    page.wait_for_selector("#cloneProvider", state="attached", timeout=5000)
    page.wait_for_selector("#cloneVoiceId", state="attached", timeout=5000)
    page.wait_for_selector("#cloneFileId", state="attached", timeout=5000)
    page.wait_for_selector("#cloneBtn", state="attached", timeout=5000)
    page.wait_for_selector("#cloneResult", state="attached", timeout=5000)

    # Set provider to mock (bypasses highRisk confirm) and fill valid clone form
    page.evaluate(""" () => {
        document.getElementById('cloneProvider').value = 'mock';
        document.getElementById('cloneProvider').dispatchEvent(new Event('change'));
    } """)

    # Fill required fields; use valid voice_id pattern (min 8 chars, starts with letter)
    page.locator("#cloneVoiceId").fill("e2e_clone_voice_success_001")
    page.locator("#cloneFileId").fill("123456")
    page.locator("#cloneModel").fill("speech-2.8-hd")
    page.locator("#clonePreviewText").fill("这是一段克隆成功E2E试听文本")

    # Verify clone button is enabled before clicking
    clone_btn_disabled = page.locator("#cloneBtn").get_attribute("disabled")
    assert not clone_btn_disabled, "cloneBtn should be enabled with valid inputs and mock capability"

    # Click clone via JS click() to ensure the onclick handler fires
    page.evaluate("document.getElementById('cloneBtn').click()")
    page.wait_for_timeout(2000)

    # Verify API was called
    assert clone_called.get("yes"), f"clone/create should have been called: {clone_called}"

    # Verify success message and voice_id appear in cloneResult
    result_html = page.locator("#cloneResult").inner_html()
    assert "克隆成功" in result_html, (
        f"Expected '克隆成功' in cloneResult, got: {result_html}"
    )
    assert "e2e_clone_voice_success_001" in result_html, (
        f"Expected voice_id 'e2e_clone_voice_success_001' in cloneResult, got: {result_html}"
    )

    # Verify demo audio player is rendered
    audio_player = page.locator("#cloneResult audio.audio-player")
    assert audio_player.count() > 0, f"Expected audio player in cloneResult, got: {result_html}"
    source_tag = page.locator('#cloneResult source[src="/static/e2e-clone-demo.mp3"]')
    assert source_tag.count() > 0, f"Expected source tag with demo_audio_url, got: {result_html}"

    # Verify quick bind panel appears
    assert page.locator("#cloneProfileWrap").count() > 0, "Quick bind profile wrap should exist"
    assert page.locator("#cloneBindBtn").count() > 0, "Quick bind button should exist"
    assert page.locator("#cloneBindModel").count() > 0, "Quick bind model select should exist"

    # Verify quick preview panel appears
    assert page.locator("#cloneQuickText").count() > 0, "Quick preview text input should exist"
    assert page.locator("#cloneQuickBtn").count() > 0, "Quick preview button should exist"
    assert page.locator("#cloneQuickResult").count() > 0, "Quick preview result should exist"

    # Verify button text is restored
    btn_text = page.locator("#cloneBtn").text_content()
    assert "克隆" in btn_text, f"cloneBtn should be restored to '克隆', got: {btn_text}"

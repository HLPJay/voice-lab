"""
Focused checks for P25B custom suggestions timeout and error handling.
"""

H5_APP = "apps/xiangta-h5/app.js"
H5_API = "apps/xiangta-h5/js/api.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fn_body(js: str, signature: str, window: int = 3200) -> str:
    idx = js.find(signature)
    assert idx >= 0, f"{signature} not found"
    return js[idx:idx + window]


class TestCustomSuggestionsTimeoutHandling:
    def test_demo_fixture_branch_still_bypasses_api(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function generateSuggestions()", window=4200)
        fixture_idx = body.find("state.demoFixtureActive")
        return_idx = body.find("return;", fixture_idx)
        api_idx = body.find('apiFetch("/api/xiangta/suggestions"')
        assert fixture_idx >= 0
        assert return_idx >= 0
        assert api_idx >= 0
        assert return_idx < api_idx

    def test_custom_branch_still_calls_real_suggestions_api(self):
        js = _read(H5_APP)
        assert 'apiFetch("/api/xiangta/suggestions"' in js

    def test_custom_branch_uses_finite_timeout(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function generateSuggestions()", window=2200)
        assert "timeoutMs: 12000" in body
        assert "timeoutMessage:" in body

    def test_button_resets_when_request_returns_null(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function generateSuggestions()", window=2600)
        assert 'setBusy("btnGenSuggestions", false' in body
        assert "if (!response)" in body

    def test_raw_text_payload_is_unchanged(self):
        js = _read(H5_APP)
        body = _fn_body(js, 'apiFetch("/api/xiangta/suggestions"', window=320)
        assert "recipient: state.selectedRecipient" in body
        assert "scene: state.selectedScene" in body
        assert "rawText: rawText" in body

    def test_api_fetch_supports_timeout_and_abort(self):
        js = _read(H5_API)
        assert "async function apiFetch(path, options, requestOptions)" in js
        assert "AbortController" in js
        assert "controller.abort()" in js
        assert 'apiFetch.lastErrorKind = "timeout"' in js

    def test_tts_payload_remains_unchanged(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function generateTtsTask()", window=3000)
        assert "text: text," in body
        assert "voicePreset: state.selectedVoice," in body
        assert "tone: state.selectedTone," in body
        assert "recipient: state.selectedRecipient," in body
        assert "scene: state.selectedScene," in body

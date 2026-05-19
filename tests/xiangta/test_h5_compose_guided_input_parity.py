"""
P25N structural tests: Compose guided-input prototype parity.

Verifies that:
- screenCompose retains step-screen structure
- All required Compose IDs still exist
- rawTextArea has maxlength
- fillExampleLink still present
- guidancePrompts container still present
- btnGenSuggestions calls generateSuggestions()
- renderGuidancePrompts exists in app.js
- Prompt click appends to rawTextArea and calls updateComposeState
- Cursor positioned at end after prompt click (setSelectionRange used)
- generateSuggestions payload unchanged (recipient, scene, rawText)
- Demo fixture bypass remains intact
- TTS payload unchanged
- Save payload unchanged
"""

import re

APP_JS = "apps/xiangta-h5/app.js"
INDEX_HTML = "apps/xiangta-h5/index.html"
COMPOSE_CSS = "apps/xiangta-h5/css/screens-compose.css"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─────────────────────────────────────────────
# HTML structure
# ─────────────────────────────────────────────

class TestComposeHTMLStructure:
    def test_screen_compose_exists(self):
        html = _read(INDEX_HTML)
        assert 'id="screenCompose"' in html

    def test_step_screen_wrapper(self):
        html = _read(INDEX_HTML)
        compose_idx = html.find('id="screenCompose"')
        snippet = html[compose_idx:compose_idx + 3000]
        assert 'class="step-screen"' in snippet

    def test_step_screen_header_present(self):
        html = _read(INDEX_HTML)
        compose_idx = html.find('id="screenCompose"')
        snippet = html[compose_idx:compose_idx + 3000]
        assert "step-screen-header" in snippet

    def test_step_screen_content_present(self):
        html = _read(INDEX_HTML)
        compose_idx = html.find('id="screenCompose"')
        snippet = html[compose_idx:compose_idx + 3000]
        assert "step-screen-content" in snippet

    def test_step_screen_cta_present(self):
        html = _read(INDEX_HTML)
        compose_idx = html.find('id="screenCompose"')
        snippet = html[compose_idx:compose_idx + 3000]
        assert "step-screen-cta" in snippet


class TestComposeRequiredIDs:
    def test_compose_title_id(self):
        html = _read(INDEX_HTML)
        assert 'id="composeTitle"' in html

    def test_compose_step_dots_id(self):
        html = _read(INDEX_HTML)
        assert 'id="composeStepDots"' in html

    def test_raw_text_wrap_id(self):
        html = _read(INDEX_HTML)
        assert 'id="rawTextWrap"' in html

    def test_raw_text_area_id(self):
        html = _read(INDEX_HTML)
        assert 'id="rawTextArea"' in html

    def test_raw_text_count_id(self):
        html = _read(INDEX_HTML)
        assert 'id="rawTextCount"' in html

    def test_fill_example_link_id(self):
        html = _read(INDEX_HTML)
        assert 'id="fillExampleLink"' in html

    def test_risk_hint_id(self):
        html = _read(INDEX_HTML)
        assert 'id="riskHint"' in html

    def test_guidance_prompts_id(self):
        html = _read(INDEX_HTML)
        assert 'id="guidancePrompts"' in html

    def test_btn_gen_suggestions_id(self):
        html = _read(INDEX_HTML)
        assert 'id="btnGenSuggestions"' in html

    def test_compose_cta_hint_id(self):
        html = _read(INDEX_HTML)
        assert 'id="composeCTAHint"' in html


class TestComposeInputField:
    def test_raw_text_area_has_maxlength(self):
        html = _read(INDEX_HTML)
        idx = html.find('id="rawTextArea"')
        tag = html[max(0, idx - 100):idx + 200]
        assert "maxlength" in tag, "rawTextArea must have maxlength attribute"

    def test_raw_text_area_maxlength_value(self):
        html = _read(INDEX_HTML)
        idx = html.find('id="rawTextArea"')
        tag = html[max(0, idx - 100):idx + 200]
        assert 'maxlength="500"' in tag, "rawTextArea maxlength must be 500"

    def test_btn_gen_suggestions_calls_generate(self):
        html = _read(INDEX_HTML)
        idx = html.find('id="btnGenSuggestions"')
        tag = html[max(0, idx - 20):idx + 200]
        assert "generateSuggestions()" in tag, \
            "btnGenSuggestions must call generateSuggestions() via onclick"


# ─────────────────────────────────────────────
# app.js guidance-prompt interaction
# ─────────────────────────────────────────────

class TestGuidancePromptInteraction:
    def test_render_guidance_prompts_exists(self):
        js = _read(APP_JS)
        assert "function renderGuidancePrompts(" in js

    def test_prompt_click_writes_to_textarea(self):
        js = _read(APP_JS)
        idx = js.find("function renderGuidancePrompts(")
        body = js[idx:idx + 1200]
        assert "textarea.value" in body, \
            "renderGuidancePrompts must write to textarea.value on prompt click"

    def test_prompt_click_calls_update_compose_state(self):
        js = _read(APP_JS)
        idx = js.find("function renderGuidancePrompts(")
        body = js[idx:idx + 1200]
        assert "updateComposeState()" in body, \
            "renderGuidancePrompts must call updateComposeState() after prompt click"

    def test_prompt_click_focuses_textarea(self):
        js = _read(APP_JS)
        idx = js.find("function renderGuidancePrompts(")
        body = js[idx:idx + 1200]
        assert "textarea.focus()" in body, \
            "renderGuidancePrompts must focus textarea after prompt click"

    def test_prompt_click_sets_selection_range(self):
        """Cursor must be positioned at end after append (prototype uses setSelectionRange)."""
        js = _read(APP_JS)
        idx = js.find("function renderGuidancePrompts(")
        body = js[idx:idx + 1600]  # wider window — setTimeout block is ~1300 chars in
        assert "setSelectionRange" in body, \
            "renderGuidancePrompts must call setSelectionRange to position cursor at end"

    def test_prompt_append_preserves_trailing_newline(self):
        """New value should end with newline so cursor lands on blank line."""
        js = _read(APP_JS)
        idx = js.find("function renderGuidancePrompts(")
        body = js[idx:idx + 1200]
        # The new value string should include a trailing \n before slicing
        assert r"\n`" in body or "\\n`" in body or "\\n'\n" in body or "\\n\"\n" in body or (
            "newVal" in body and "\\n" in body
        ), "prompt append must produce a value ending with \\n"

    def test_update_compose_state_function_exists(self):
        js = _read(APP_JS)
        assert "function updateComposeState(" in js


# ─────────────────────────────────────────────
# API payload invariants
# ─────────────────────────────────────────────

class TestSuggestionsPayload:
    def test_generate_suggestions_exists(self):
        js = _read(APP_JS)
        assert "async function generateSuggestions(" in js

    def test_suggestions_payload_recipient(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "recipient" in snippet

    def test_suggestions_payload_scene(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "scene" in snippet

    def test_suggestions_payload_raw_text(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "rawText" in snippet

    def test_no_profile_id_in_suggestions_payload(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "profileId" not in snippet


class TestDemoFixtureBypass:
    def test_fixture_bypass_still_present(self):
        js = _read(APP_JS)
        idx = js.find("async function generateSuggestions(")
        body = js[idx:idx + 2400]
        assert "demoFixtureActive" in body
        assert "DEMO_FIXTURES" in body

    def test_fixture_bypass_returns_before_api(self):
        js = _read(APP_JS)
        idx = js.find("async function generateSuggestions(")
        body = js[idx:idx + 2400]
        fixture_return = body.find("return;", body.find("DEMO_FIXTURES"))
        api_call = body.find('apiFetch("/api/xiangta/suggestions"')
        assert fixture_return >= 0
        assert api_call >= 0
        assert fixture_return < api_call, \
            "fixture bypass must return before the real apiFetch call"


class TestTTSPayload:
    # TTS payload is built in a `payload` object *before* the apiFetch call.
    # Look at the 500 chars preceding the apiFetch line.
    def _tts_region(self, js):
        idx = js.find('apiFetch("/api/xiangta/tts/tasks"')
        assert idx >= 0, "TTS apiFetch must exist"
        return js[max(0, idx - 500):idx + 200]

    def test_tts_payload_text(self):
        js = _read(APP_JS)
        assert "voicePreset" in js  # quick sanity
        region = self._tts_region(js)
        assert "text:" in region or '"text"' in region, \
            "TTS payload must include 'text' field"

    def test_tts_payload_voice_preset(self):
        js = _read(APP_JS)
        region = self._tts_region(js)
        assert "voicePreset" in region

    def test_tts_payload_tone(self):
        js = _read(APP_JS)
        region = self._tts_region(js)
        assert "tone" in region

    def test_tts_payload_recipient(self):
        js = _read(APP_JS)
        region = self._tts_region(js)
        assert "recipient" in region

    def test_tts_payload_scene(self):
        js = _read(APP_JS)
        region = self._tts_region(js)
        assert "scene" in region


class TestSavePayload:
    def test_save_payload_raw_text(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        assert idx >= 0, "letters save apiFetch must exist"
        snippet = js[idx:idx + 400]
        assert "rawText" in snippet

    def test_save_payload_final_text(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 400]
        assert "finalText" in snippet

    def test_save_payload_audio_url(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]  # audioUrl is ~10 lines after apiFetch
        assert "audioUrl" in snippet

    def test_save_payload_no_profile_id(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 400]
        assert "profileId" not in snippet


# ─────────────────────────────────────────────
# CSS parity checks
# ─────────────────────────────────────────────

class TestComposeCSSParity:
    def test_compose_subtitle_font_size(self):
        css = _read(COMPOSE_CSS)
        assert "step-subtitle" in css, \
            "screens-compose.css should define compose-specific step-subtitle size"
        assert "12px" in css or "font-size: 12" in css, \
            "compose subtitle font-size should be 12px (per prototype)"

    def test_prompt_card_tap_feedback(self):
        css = _read(COMPOSE_CSS)
        assert "prompt-card:active" in css, \
            "prompt-card:active state must be defined for mobile tap feedback"

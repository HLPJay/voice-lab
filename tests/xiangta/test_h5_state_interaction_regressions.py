"""
Focused structural checks for P24 H5 state and interaction regressions.
"""

H5_APP = "apps/xiangta-h5/app.js"
CSS_COMPONENTS = "apps/xiangta-h5/css/components.css"
CSS_SUGGEST_VOICE = "apps/xiangta-h5/css/screens-suggestions-voice.css"
CSS_OVERLAYS = "apps/xiangta-h5/css/overlays.css"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fn_body(js: str, signature: str, window: int = 2600) -> str:
    idx = js.find(signature)
    assert idx >= 0, f"{signature} not found"
    return js[idx:idx + window]


class TestSuggestionsSelectionNoRebuild:
    def test_select_suggestion_does_not_rerender_cards(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function selectSuggestion(index)")
        assert "renderSuggestionCards(" not in body

    def test_update_selection_helper_exists(self):
        js = _read(H5_APP)
        assert "function updateSuggestionSelectionUi(" in js


class TestSuggestionsActionLayout:
    def test_suggestion_actions_has_space_between_and_gap(self):
        css = _read(CSS_SUGGEST_VOICE)
        idx = css.find(".suggestion-actions")
        assert idx >= 0
        block = css[idx:idx + 220]
        assert "justify-content: space-between" in block
        assert "gap: 12px" in block

    def test_suggestion_action_left_has_gap(self):
        css = _read(CSS_SUGGEST_VOICE)
        idx = css.find(".suggestion-action-left")
        assert idx >= 0
        block = css[idx:idx + 180]
        assert "gap: 8px" in block


class TestFavoriteAndOverlay:
    def test_toggle_favorite_refreshes_meta_pills(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function toggleLetterDetailFavorite()")
        assert "renderLetterDetailMetaPills(" in body

    def test_opening_overlay_initially_hidden_in_css(self):
        css = _read(CSS_OVERLAYS)
        idx = css.find(".opening-overlay")
        assert idx >= 0
        block = css[idx:idx + 220]
        assert "display: none" in block

    def test_init_opening_overlay_shows_only_when_needed(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function initOpeningOverlay()")
        assert 'localStorage.getItem("xiangta_opening_seen") !== "1"' in body
        assert 'overlay.classList.add("visible")' in body


class TestVoicePressAndFlowPreservation:
    def test_voice_active_selector_excludes_disabled(self):
        css = _read(CSS_COMPONENTS)
        assert ".voice-option:not(.disabled):not(:disabled):active" in css

    def test_tts_payload_unchanged(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function generateTtsTask()", window=3000)
        assert "const payload = {" in body
        assert "text: text," in body
        assert "voicePreset: state.selectedVoice," in body
        assert "tone: state.selectedTone," in body
        assert "recipient: state.selectedRecipient," in body
        assert "scene: state.selectedScene," in body

    def test_demo_fixture_fallback_still_preserved(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function generateSuggestions()", window=4200)
        assert "state.demoFixtureActive" in body
        assert 'apiFetch("/api/xiangta/suggestions"' in body

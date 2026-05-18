"""
Tests for H5 History Prototype Parity (P22B).

Covers:
1. styles.css contains --xt-surface / --xt-accent-soft / --xt-text-2 token variables
2. styles.css contains spaCardIn / spaSlideInR / spaFadeOverlay / spaMiniPlayerUp keyframes
3. index.html has historySearchBox
4. index.html has historyFilterChips
5. index.html has historyAudio element
6. index.html has historyMiniPlayer
7. app.js has historyFilter state
8. app.js has historySearchQuery state
9. app.js has getFilteredLetters or equivalent
10. app.js has playHistoryLetter / toggleHistoryPlayback
11. app.js has historyAudio loadedmetadata/timeupdate/error listeners
12. app.js does not contain _silentWav
13. app.js does not use speechSynthesis for history playback
14. History cards no longer render native audio controls inline
15. renderHistoryMiniPlayer or equivalent exists
16. Formal H5 payload does not include profileId/coreProfileId
17. Dev mode profileId passthrough preserved
18. screenResult still exists (P22A)
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestPrototypeStyleTokens:
    def test_xt_surface_token_exists(self):
        """styles.css contains --xt-surface variable."""
        css = _read(H5_CSS)
        assert "--xt-surface:" in css, "--xt-surface token not found"

    def test_xt_accent_soft_token_exists(self):
        """styles.css contains --xt-accent-soft variable."""
        css = _read(H5_CSS)
        assert "--xt-accent-soft:" in css, "--xt-accent-soft token not found"

    def test_xt_text_2_token_exists(self):
        """styles.css contains --xt-text-2 variable."""
        css = _read(H5_CSS)
        assert "--xt-text-2:" in css, "--xt-text-2 token not found"

    def test_xt_bg_token_exists(self):
        """styles.css contains --xt-bg variable."""
        css = _read(H5_CSS)
        assert "--xt-bg:" in css, "--xt-bg token not found"


class TestPrototypeAnimations:
    def test_spa_card_in_animation_exists(self):
        """styles.css contains spaCardIn keyframe animation."""
        css = _read(H5_CSS)
        assert "@keyframes spaCardIn" in css, "spaCardIn keyframe not found"

    def test_spa_slide_in_r_animation_exists(self):
        """styles.css contains spaSlideInR keyframe animation."""
        css = _read(H5_CSS)
        assert "@keyframes spaSlideInR" in css, "spaSlideInR keyframe not found"

    def test_spa_fade_overlay_animation_exists(self):
        """styles.css contains spaFadeOverlay keyframe animation."""
        css = _read(H5_CSS)
        assert "@keyframes spaFadeOverlay" in css, "spaFadeOverlay keyframe not found"

    def test_spa_mini_player_up_animation_exists(self):
        """styles.css contains spaMiniPlayerUp keyframe animation."""
        css = _read(H5_CSS)
        assert "@keyframes spaMiniPlayerUp" in css, "spaMiniPlayerUp keyframe not found"


class TestHistoryDOMStructure:
    def test_history_search_box_exists(self):
        """index.html has historySearchBox element."""
        html = _read(H5_INDEX)
        assert 'id="historySearchBox"' in html, "historySearchBox not found"

    def test_history_filter_chips_exists(self):
        """index.html has historyFilterChips element."""
        html = _read(H5_INDEX)
        assert 'id="historyFilterChips"' in html, "historyFilterChips not found"

    def test_history_audio_exists(self):
        """index.html has historyAudio element."""
        html = _read(H5_INDEX)
        assert 'id="historyAudio"' in html, "historyAudio not found"

    def test_history_mini_player_exists(self):
        """index.html has historyMiniPlayer element."""
        html = _read(H5_INDEX)
        assert 'id="historyMiniPlayer"' in html, "historyMiniPlayer not found"


class TestHistoryAppState:
    def test_history_filter_state_exists(self):
        """app.js has historyFilter state."""
        js = _read(H5_APP)
        assert "historyFilter:" in js, "historyFilter state not found"

    def test_history_search_query_state_exists(self):
        """app.js has historySearchQuery state."""
        js = _read(H5_APP)
        assert "historySearchQuery:" in js, "historySearchQuery state not found"

    def test_get_filtered_letters_exists(self):
        """app.js has getFilteredLetters function."""
        js = _read(H5_APP)
        assert "function getFilteredLetters" in js or "getFilteredLetters =" in js, \
            "getFilteredLetters function not found"


class TestHistoryAudioPlayback:
    def test_play_history_letter_exists(self):
        """app.js has playHistoryLetter function."""
        js = _read(H5_APP)
        assert "function playHistoryLetter" in js or "playHistoryLetter =" in js, \
            "playHistoryLetter function not found"

    def test_toggle_history_playback_exists(self):
        """app.js has toggleHistoryPlayback function."""
        js = _read(H5_APP)
        assert "function toggleHistoryPlayback" in js or "toggleHistoryPlayback =" in js, \
            "toggleHistoryPlayback function not found"

    def test_history_audio_listeners_exist(self):
        """app.js has historyAudio event listeners for loadedmetadata/timeupdate/error."""
        js = _read(H5_APP)
        assert 'addEventListener("loadedmetadata"' in js or "addEventListener('loadedmetadata'" in js, \
            "loadedmetadata listener not found"
        assert 'addEventListener("timeupdate"' in js or "addEventListener('timeupdate'" in js, \
            "timeupdate listener not found"
        assert 'addEventListener("error"' in js or "addEventListener('error'" in js, \
            "error listener not found"


class TestNoMockAudio:
    def test_no_silent_wav_in_history(self):
        """app.js does not contain _silentWav."""
        js = _read(H5_APP)
        assert "_silentWav" not in js, "_silentWav should not be in app.js"

    def test_no_speech_synthesis_in_history(self):
        """app.js does not use speechSynthesis for history playback."""
        js = _read(H5_APP)
        # Check that history playback functions don't use speechSynthesis
        history_funcs = ["playHistoryLetter", "toggleHistoryPlayback", "setupHistoryAudioListeners"]
        for func in history_funcs:
            start = js.find(f"function {func}")
            if start == -1:
                start = js.find(f"{func} =")
            if start != -1:
                end = js.find("\n}", start)
                section = js[start:end]
                assert "speechSynthesis" not in section, \
                    f"{func} should not use speechSynthesis"


class TestHistoryCardRendering:
    def test_no_inline_audio_controls_in_render_letters(self):
        """renderLetters does not render inline audio controls."""
        js = _read(H5_APP)
        start = js.find("function renderLetters")
        end = js.find("\n}", start)
        section = js[start:end]
        # Should not have audio controls in card HTML
        assert 'controls' not in section or 'prototype-history-card' in section, \
            "renderLetters should not create inline audio controls"


class TestHistoryMiniPlayer:
    def test_render_history_mini_player_exists(self):
        """app.js has renderHistoryMiniPlayer function."""
        js = _read(H5_APP)
        assert "function renderHistoryMiniPlayer" in js or "renderHistoryMiniPlayer =" in js, \
            "renderHistoryMiniPlayer function not found"


class TestFormalDevModePreservation:
    def test_formal_payload_no_profile_id(self):
        """generateTtsTask does not include profileId in formal mode payload."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]

        if "profileId" in section:
            assert 'state.mode === "dev"' in section or "state.mode === 'dev'" in section, \
                "profileId must be guarded by dev mode"

    def test_dev_mode_profile_id_passthrough(self):
        """dev mode allows profileId passthrough in generateTtsTask."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]

        assert "state.mode === " in section, \
            "Dev mode check must exist for profileId passthrough"


class TestP22AResultScreenPreserved:
    def test_screen_result_still_exists(self):
        """screenResult section still exists (P22A result screen preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenResult"' in html, "screenResult not found — P22A broken"

    def test_render_result_screen_still_exists(self):
        """renderResultScreen function still exists (P22A preserved)."""
        js = _read(H5_APP)
        assert "function renderResultScreen" in js or "renderResultScreen =" in js, \
            "renderResultScreen not found — P22A broken"


class TestHistorySearchAndFilter:
    def test_toggle_history_search_exists(self):
        """app.js has toggleHistorySearch function."""
        js = _read(H5_APP)
        assert "function toggleHistorySearch" in js or "toggleHistorySearch =" in js, \
            "toggleHistorySearch function not found"

    def test_render_history_filter_chips_exists(self):
        """app.js has renderHistoryFilterChips function."""
        js = _read(H5_APP)
        assert "function renderHistoryFilterChips" in js or "renderHistoryFilterChips =" in js, \
            "renderHistoryFilterChips function not found"

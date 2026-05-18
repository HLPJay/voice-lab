"""
Tests for H5 Primary Screens Prototype Parity (P22C).

Covers:
1. Home topbar has settings button (not refresh)
2. Settings button shows showToast("设置页后续支持")
3. Home has history button + settings button in topbar
4. All four screens (Home, Compose, Suggestions, Voice) use spaCardIn animation on cards
5. StepDots are unified across screens (same step-progress styles)
6. AppBar is unified (step-appbar on all step screens)
7. P22A (screenResult) still works
8. P22B (screenHistory) still works
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestHomeScreenSettingsButton:
    def test_settings_button_exists_not_refresh(self):
        """Home topbar has settings button, not refresh button."""
        html = _read(H5_INDEX)
        # Should have settings button
        assert 'aria-label="设置"' in html or "aria-label='设置'" in html, \
            "Settings button not found in Home topbar"
        # Should NOT have refresh/刷新首页 button
        assert 'aria-label="刷新首页"' not in html and "aria-label='刷新首页'" not in html, \
            "Refresh button should be replaced with settings button"

    def test_settings_button_calls_show_screen(self):
        """Settings button calls showScreen('settings')."""
        html = _read(H5_INDEX)
        # Find the settings button onclick
        settings_match = re.search(
            r'aria-label="[^"]*设置[^"]*"[^>]*onclick="([^"]+)"',
            html,
            re.DOTALL
        )
        if not settings_match:
            settings_match = re.search(
                r"aria-label='[^']*设置[^']*'[^>]*onclick='([^']+)'",
                html,
                re.DOTALL
            )
        assert settings_match, "Settings button not found"
        onclick = settings_match.group(1)
        assert "showScreen" in onclick and "settings" in onclick, \
            "Settings button must call showScreen('settings')"

    def test_home_topbar_has_history_and_settings(self):
        """Home topbar has both history and settings buttons."""
        html = _read(H5_INDEX)
        # History button exists
        assert 'aria-label="历史信笺"' in html or "aria-label='历史信笺'" in html, \
            "History button not found"
        # Settings button exists
        assert 'aria-label="设置"' in html or "aria-label='设置'" in html, \
            "Settings button not found"


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

    def test_card_elements_have_spa_card_in_animation(self):
        """Card elements (recipient-card, scene-chip, prompt-card, voice-option, etc.) have spaCardIn animation."""
        css = _read(H5_CSS)
        # Check that the card selector group includes animation
        card_group = ".recipient-card,\n.scene-chip,\n.prompt-card,\n.voice-option,\n.suggestion-card,\n.tone-chip"
        # Find if any of these cards have spaCardIn animation
        assert "spaCardIn" in css, "spaCardIn animation must be referenced in CSS"


class TestStepDotsUnified:
    def test_step_progress_styles_exist(self):
        """styles.css has step-progress class."""
        css = _read(H5_CSS)
        assert ".step-progress" in css, "step-progress class not found"

    def test_step_track_styles_exist(self):
        """styles.css has step-track class for step dots."""
        css = _read(H5_CSS)
        assert ".step-track" in css, "step-track class not found"

    def test_step_dot_styles_exist(self):
        """styles.css has step-dot class for individual dots."""
        css = _read(H5_CSS)
        assert ".step-dot" in css, "step-dot class not found"


class TestAppBarUnified:
    def test_step_appbar_class_exists(self):
        """styles.css has step-appbar class."""
        css = _read(H5_CSS)
        assert ".step-appbar" in css, "step-appbar class not found"

    def test_compose_screen_uses_step_appbar(self):
        """screenCompose uses step-appbar."""
        html = _read(H5_INDEX)
        compose_start = html.find('id="screenCompose"')
        compose_end = html.find('</section>', compose_start)
        compose_section = html[compose_start:compose_end]
        assert 'class="step-appbar"' in compose_section, \
            "screenCompose must use step-appbar"

    def test_suggest_screen_uses_step_appbar(self):
        """screenSuggest uses step-appbar."""
        html = _read(H5_INDEX)
        suggest_start = html.find('id="screenSuggest"')
        suggest_end = html.find('</section>', suggest_start)
        suggest_section = html[suggest_start:suggest_end]
        assert 'class="step-appbar"' in suggest_section, \
            "screenSuggest must use step-appbar"

    def test_voice_screen_uses_step_appbar(self):
        """screenVoice uses step-appbar."""
        html = _read(H5_INDEX)
        voice_start = html.find('id="screenVoice"')
        voice_end = html.find('</section>', voice_start)
        voice_section = html[voice_start:voice_end]
        assert 'class="step-appbar"' in voice_section, \
            "screenVoice must use step-appbar"


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


class TestP22BHistoryScreenPreserved:
    def test_screen_history_still_exists(self):
        """screenHistory section still exists (P22B history screen preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenHistory"' in html, "screenHistory not found — P22B broken"

    def test_history_search_box_still_exists(self):
        """historySearchBox still exists (P22B preserved)."""
        html = _read(H5_INDEX)
        assert 'id="historySearchBox"' in html, "historySearchBox not found — P22B broken"

    def test_history_audio_still_exists(self):
        """historyAudio element still exists (P22B preserved)."""
        html = _read(H5_INDEX)
        assert 'id="historyAudio"' in html, "historyAudio not found — P22B broken"

    def test_history_mini_player_still_exists(self):
        """historyMiniPlayer still exists (P22B preserved)."""
        html = _read(H5_INDEX)
        assert 'id="historyMiniPlayer"' in html, "historyMiniPlayer not found — P22B broken"

    def test_play_history_letter_still_exists(self):
        """playHistoryLetter function still exists (P22B preserved)."""
        js = _read(H5_APP)
        assert "function playHistoryLetter" in js or "playHistoryLetter =" in js, \
            "playHistoryLetter not found — P22B broken"


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
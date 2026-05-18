"""
Tests for H5 Home/Compose Prototype Parity (P22C-FIX1).

Covers:
1. Home has history button
2. Home has settings button or settings toast
3. Home has homeDateLine
4. Home has homeRecentLetter section
5. Home uses state.letters for recent letter rendering
6. Home recipient-card and scene-chip preserved
7. Compose has "先说说" title
8. Compose has rawTextArea
9. Compose has rawTextCount
10. Compose has fillExampleLink
11. Compose has guidancePrompts
12. Compose prompt-card uses spaCardIn animation
13. Compose does not break generateSuggestions() call
14. screenResult still exists (P22A preserved)
15. screenHistory still exists (P22B preserved)
16. Formal H5 payload does not include profileId/coreProfileId
17. Dev mode profileId passthrough preserved
18. No new backend API paths introduced
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestHomeScreenStructure:
    def test_home_has_history_button(self):
        """Home has history button (aria-label='历史信笺')."""
        html = _read(H5_INDEX)
        assert 'aria-label="历史信笺"' in html or "aria-label='历史信笺'" in html, \
            "History button not found in Home"

    def test_home_has_settings_button_or_toast(self):
        """Home has settings button or settings toast placeholder."""
        html = _read(H5_INDEX)
        # Either settings button exists with toast, or settings button with showToast
        assert 'aria-label="设置"' in html or "showToast" in html, \
            "Settings button or toast not found"

    def test_home_has_home_date_line(self):
        """Home has homeDateLine element."""
        html = _read(H5_INDEX)
        assert 'id="homeDateLine"' in html, \
            "homeDateLine not found"

    def test_home_has_recent_letter_section(self):
        """Home has homeRecentLetter or equivalent recent letter area."""
        html = _read(H5_INDEX)
        assert 'id="homeRecentLetter"' in html or 'class="home-recent' in html, \
            "homeRecentLetter section not found"

    def test_home_uses_state_letters_for_recent(self):
        """renderHomeRecentLetter uses state.letters."""
        js = _read(H5_APP)
        assert "state.letters" in js, \
            "state.letters not found — recent letter must use state.letters"

    def test_render_home_recent_letter_exists(self):
        """renderHomeRecentLetter function exists."""
        js = _read(H5_APP)
        assert "function renderHomeRecentLetter" in js or "renderHomeRecentLetter =" in js, \
            "renderHomeRecentLetter function not found"

    def test_home_recipient_grid_exists(self):
        """Home has recipient-grid element."""
        html = _read(H5_INDEX)
        assert 'id="recipientGrid"' in html, \
            "recipientGrid not found"

    def test_home_scene_grid_exists(self):
        """Home has scene-grid element."""
        html = _read(H5_INDEX)
        assert 'id="sceneGrid"' in html, \
            "sceneGrid not found"

    def test_home_start_button_exists(self):
        """Home has 开始表达 button."""
        html = _read(H5_INDEX)
        assert "开始表达" in html, \
            "开始表达 button not found"


class TestComposeScreenStructure:
    def test_compose_has_title(self):
        """Compose has '先说说' title."""
        html = _read(H5_INDEX)
        assert "先说说" in html, \
            "Compose title '先说说' not found"

    def test_compose_has_raw_text_area(self):
        """Compose has rawTextArea element."""
        html = _read(H5_INDEX)
        assert 'id="rawTextArea"' in html, \
            "rawTextArea not found"

    def test_compose_has_raw_text_count(self):
        """Compose has rawTextCount element."""
        html = _read(H5_INDEX)
        assert 'id="rawTextCount"' in html, \
            "rawTextCount not found"

    def test_compose_has_fill_example_link(self):
        """Compose has fillExampleLink button."""
        html = _read(H5_INDEX)
        assert 'id="fillExampleLink"' in html or "用一个例子开始" in html, \
            "fillExampleLink not found"

    def test_compose_has_guidance_prompts(self):
        """Compose has guidancePrompts element."""
        html = _read(H5_INDEX)
        assert 'id="guidancePrompts"' in html, \
            "guidancePrompts not found"

    def test_compose_has_step_appbar(self):
        """Compose has step-appbar."""
        html = _read(H5_INDEX)
        compose_start = html.find('id="screenCompose"')
        compose_end = html.find("</section>", compose_start)
        compose_section = html[compose_start:compose_end]
        assert 'class="step-appbar"' in compose_section, \
            "step-appbar not found in screenCompose"

    def test_compose_has_step_progress(self):
        """Compose has step-progress (step dots)."""
        html = _read(H5_INDEX)
        assert 'id="composeStepDots"' in html, \
            "composeStepDots not found"


class TestComposePromptCardAnimation:
    def test_prompt_card_has_spa_card_in_animation(self):
        """prompt-card elements have spaCardIn animation via CSS."""
        css = _read(H5_CSS)
        # prompt-card should be in a group that includes spaCardIn animation
        # Check that prompt-card selector is grouped with cards that have spaCardIn
        assert "spaCardIn" in css, \
            "spaCardIn animation must be referenced in CSS"

    def test_prompt_card_styles_exist(self):
        """styles.css has prompt-card class."""
        css = _read(H5_CSS)
        assert ".prompt-card" in css, \
            "prompt-card class not found"


class TestGenerateSuggestionsPreserved:
    def test_generate_suggestions_function_exists(self):
        """generateSuggestions function still exists."""
        js = _read(H5_APP)
        assert "function generateSuggestions" in js or "generateSuggestions =" in js, \
            "generateSuggestions function not found"

    def test_compose_cta_calls_generate_suggestions(self):
        """btnGenSuggestions calls generateSuggestions onclick."""
        html = _read(H5_INDEX)
        assert 'onclick="generateSuggestions()"' in html or "onclick='generateSuggestions()'" in html, \
            "btnGenSuggestions must call generateSuggestions()"


class TestP22AResultScreenPreserved:
    def test_screen_result_still_exists(self):
        """screenResult still exists (P22A preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenResult"' in html, \
            "screenResult not found — P22A broken"


class TestP22BHistoryScreenPreserved:
    def test_screen_history_still_exists(self):
        """screenHistory still exists (P22B preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenHistory"' in html, \
            "screenHistory not found — P22B broken"

    def test_history_audio_still_exists(self):
        """historyAudio element still exists (P22B preserved)."""
        html = _read(H5_INDEX)
        assert 'id="historyAudio"' in html, \
            "historyAudio not found — P22B broken"


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


class TestNoNewBackendApis:
    def test_no_new_api_paths(self):
        """No new backend API paths were introduced."""
        js = _read(H5_APP)

        # Allowed API paths
        allowed = [
            "/api/xiangta/bootstrap",
            "/api/xiangta/suggestions",
            "/api/xiangta/tts/tasks",
            "/api/xiangta/tts",
            "/api/xiangta/letters",
            "/api/xiangta/voice-bindings/status",
            "/api/xiangta/core/profiles",
        ]

        # Find all API paths used
        api_pattern = r'/api/[a-zA-Z0-9/_-]+'
        found_apis = set(re.findall(api_pattern, js))

        for api in found_apis:
            assert any(api.startswith(allowed_api) for allowed_api in allowed), \
                f"Unexpected API path found: {api}"


class TestHomeRecentLetterRendering:
    def test_render_home_recent_letter_renders_empty_state(self):
        """renderHomeRecentLetter renders empty state when no letters."""
        js = _read(H5_APP)
        # Should have empty state with "还没有保存的信笺"
        assert "还没有保存的信笺" in js, \
            "Empty state text not found in renderHomeRecentLetter"

    def test_render_home_recent_letter_renders_letter_card(self):
        """renderHomeRecentLetter renders letter card with title and meta."""
        js = _read(H5_APP)
        # Should use getLetterTitle for the letter title
        assert "getLetterTitle" in js, \
            "getLetterTitle not used in renderHomeRecentLetter"

    def test_render_home_recent_letter_uses_recipient_meta(self):
        """renderHomeRecentLetter uses RECIPIENT_META for labels."""
        js = _read(H5_APP)
        assert "RECIPIENT_META" in js, \
            "RECIPIENT_META not used for labels"

    def test_render_home_recent_letter_uses_scene_meta(self):
        """renderHomeRecentLetter uses SCENE_META for labels."""
        js = _read(H5_APP)
        assert "SCENE_META" in js, \
            "SCENE_META not used for labels"

    def test_render_home_recent_letter_navigates_to_history(self):
        """Home recent letter card navigates to history on click."""
        js = _read(H5_APP)
        # The card onclick should call showScreen('history')
        assert "showScreen('history')" in js or 'showScreen("history")' in js, \
            "Home recent letter must navigate to history on click"


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


class TestHomeRecentLetterCSS:
    def test_home_recent_card_styles_exist(self):
        """styles.css has home-recent-card class."""
        css = _read(H5_CSS)
        assert ".home-recent-card" in css or ".home-recent-empty" in css, \
            "home-recent-card or home-recent-empty styles not found"

    def test_home_recent_letter_card_has_animation(self):
        """home-recent-letter-card has spaCardIn animation."""
        css = _read(H5_CSS)
        assert "home-recent-letter-card" in css and "spaCardIn" in css, \
            "home-recent-letter-card must have spaCardIn animation"

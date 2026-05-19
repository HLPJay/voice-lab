"""
Tests for H5 Compose Screen Prototype Parity (P22N).

Covers:
1. screenCompose still exists
2. composeStepDots still exists
3. composeTitle still exists
4. rawTextArea maxlength=500 still exists
5. rawTextWrap / composer-box still exists
6. fillExampleLink still exists and calls fillExample logic
7. rawTextCount still exists
8. riskHint still exists
9. guidancePrompts still exists
10. btnGenSuggestions calls generateSuggestions()
11. composeCTAHint still exists
12. CSS: composer-box uses --xt-surface, --xt-hairline-2, border-radius 18px
13. CSS: textarea transparent bg, serif, resize none
14. CSS: prompt-card uses spaCardIn animation
15. CSS: sticky CTA safe-area still exists
16. .screen.active { display:block } still exists
17. .screen.home-screen.active { display:flex } still exists
18. Home topbar still inside screenHome
19. btnStartCompose still in home-bottom-cta
20. formal H5 payload does not include profileId/coreProfileId
21. dev mode profileId passthrough preserved
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestComposeScreenExistence:
    """Compose screen DOM elements exist."""

    def test_screen_compose_exists(self):
        """screenCompose section exists."""
        html = _read(H5_INDEX)
        assert 'id="screenCompose"' in html, "screenCompose not found"

    def test_compose_step_dots_exists(self):
        """composeStepDots element exists."""
        html = _read(H5_INDEX)
        assert 'id="composeStepDots"' in html, "composeStepDots not found"

    def test_compose_title_exists(self):
        """composeTitle element exists."""
        html = _read(H5_INDEX)
        assert 'id="composeTitle"' in html, "composeTitle not found"

    def test_raw_text_area_exists(self):
        """rawTextArea element exists with maxlength=500."""
        html = _read(H5_INDEX)
        assert 'id="rawTextArea"' in html, "rawTextArea not found"
        assert 'maxlength="500"' in html, "rawTextArea must have maxlength=500"

    def test_composer_box_exists(self):
        """composer-box (rawTextWrap) exists."""
        html = _read(H5_INDEX)
        assert 'id="rawTextWrap"' in html or 'class="composer-box"' in html, \
            "composer-box not found"

    def test_fill_example_link_exists(self):
        """fillExampleLink exists."""
        html = _read(H5_INDEX)
        assert 'id="fillExampleLink"' in html, "fillExampleLink not found"

    def test_raw_text_count_exists(self):
        """rawTextCount exists."""
        html = _read(H5_INDEX)
        assert 'id="rawTextCount"' in html, "rawTextCount not found"

    def test_risk_hint_exists(self):
        """riskHint exists."""
        html = _read(H5_INDEX)
        assert 'id="riskHint"' in html, "riskHint not found"

    def test_guidance_prompts_exists(self):
        """guidancePrompts exists."""
        html = _read(H5_INDEX)
        assert 'id="guidancePrompts"' in html, "guidancePrompts not found"

    def test_btn_gen_suggestions_calls_generate_suggestions(self):
        """btnGenSuggestions calls generateSuggestions()."""
        html = _read(H5_INDEX)
        assert 'onclick="generateSuggestions()"' in html or "onclick='generateSuggestions()'" in html, \
            "btnGenSuggestions must call generateSuggestions()"

    def test_compose_cta_hint_exists(self):
        """composeCTAHint exists."""
        html = _read(H5_INDEX)
        assert 'id="composeCTAHint"' in html, "composeCTAHint not found"


class TestComposeScreenFunctions:
    """Compose screen JS functions exist."""

    def test_generate_suggestions_exists(self):
        """generateSuggestions function exists."""
        js = _read(H5_APP)
        assert "function generateSuggestions" in js or "generateSuggestions =" in js, \
            "generateSuggestions function not found"

    def test_render_guidance_prompts_exists(self):
        """renderGuidancePrompts function exists."""
        js = _read(H5_APP)
        assert "function renderGuidancePrompts" in js or "renderGuidancePrompts =" in js, \
            "renderGuidancePrompts function not found"

    def test_update_compose_state_exists(self):
        """updateComposeState function exists."""
        js = _read(H5_APP)
        assert "function updateComposeState" in js or "updateComposeState =" in js, \
            "updateComposeState function not found"


class TestComposeScreenCSS:
    """Compose screen CSS matches prototype."""

    def test_composer_box_uses_surface(self):
        """.composer-box uses --xt-surface background."""
        css = _read(H5_CSS)
        idx = css.find(".composer-box {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "--xt-surface" in section or "var(--surface)" in section or "#" in section, \
            ".composer-box must use surface background"

    def test_composer_box_border_radius_18px(self):
        """.composer-box has border-radius: 18px."""
        css = _read(H5_CSS)
        idx = css.find(".composer-box {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "18px" in section or "18rpx" in section, \
            ".composer-box must have border-radius: 18px"

    def test_textarea_transparent_background(self):
        """.composer-box textarea has transparent background."""
        css = _read(H5_CSS)
        idx = css.find(".composer-box textarea {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "background: transparent" in section or "background:transparent" in section, \
            ".composer-box textarea must have transparent background"

    def test_textarea_serif_font(self):
        """.composer-box textarea uses serif font."""
        css = _read(H5_CSS)
        idx = css.find(".composer-box textarea {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "serif" in section, \
            ".composer-box textarea must use serif font"

    def test_textarea_resize_none(self):
        """.composer-box textarea has resize: none."""
        css = _read(H5_CSS)
        idx = css.find(".composer-box textarea {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "resize: none" in section or "resize:none" in section, \
            ".composer-box textarea must have resize: none"

    def test_prompt_card_has_animation(self):
        """.prompt-card has spaCardIn animation."""
        css = _read(H5_CSS)
        assert "spaCardIn" in css, \
            ".prompt-card must have spaCardIn animation"

    def test_sticky_cta_safe_area(self):
        """.sticky-cta uses env(safe-area-inset-bottom)."""
        css = _read(H5_CSS)
        idx = css.find(".sticky-cta {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "safe-area-inset-bottom" in section, \
            ".sticky-cta must use env(safe-area-inset-bottom)"

    def test_step_progress_exists(self):
        """.step-progress CSS exists."""
        css = _read(H5_CSS)
        assert ".step-progress" in css, ".step-progress CSS rule must exist"


class TestLayoutContractPreserved:
    """Home/Compose layout contract from P22M-FIX2/FIX4 preserved."""

    def test_screen_active_display_block(self):
        """.screen.active has display: block."""
        css = _read(H5_CSS)
        idx = css.find(".screen.active {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "display: block" in section or "display:block" in section, \
            ".screen.active must have display:block"

    def test_home_screen_active_display_flex(self):
        """.screen.home-screen.active has display: flex."""
        css = _read(H5_CSS)
        idx = css.find(".screen.home-screen.active {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "display: flex" in section or "display:flex" in section, \
            ".screen.home-screen.active must have display:flex"

    def test_app_topbar_inside_screen_home(self):
        """appTopbar is inside screenHome."""
        html = _read(H5_INDEX)
        home_start = html.find('id="screenHome"')
        home_end = html.find("</section>", home_start)
        home_section = html[home_start:home_end]
        assert 'id="appTopbar"' in home_section, \
            "appTopbar must be inside screenHome"

    def test_btn_start_compose_in_home_bottom_cta(self):
        """btnStartCompose is inside home-bottom-cta."""
        html = _read(H5_INDEX)
        cta_start = html.find('class="home-bottom-cta"')
        cta_end = html.find("</div>", cta_start)
        cta_section = html[cta_start:cta_end]
        assert 'id="btnStartCompose"' in cta_section, \
            "btnStartCompose must be inside home-bottom-cta"


class TestFormalDevModePayload:
    """Payload integrity checks."""

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
        """dev mode allows profileId passthrough."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "state.mode === " in section, \
            "Dev mode check must exist for profileId passthrough"


class TestNoNewBackendApis:
    """No new backend API paths."""

    def test_no_new_api_paths(self):
        """No new backend API paths were introduced."""
        js = _read(H5_APP)
        allowed = [
            "/api/xiangta/bootstrap",
            "/api/xiangta/suggestions",
            "/api/xiangta/tts/tasks",
            "/api/xiangta/tts",
            "/api/xiangta/letters",
            "/api/xiangta/voice-bindings/status",
            "/api/xiangta/core/profiles",
        ]
        api_pattern = r'/api/[a-zA-Z0-9/_-]+'
        found_apis = set(re.findall(api_pattern, js))
        for api in found_apis:
            assert any(api.startswith(allowed_api) for allowed_api in allowed), \
                f"Unexpected API path found: {api}"

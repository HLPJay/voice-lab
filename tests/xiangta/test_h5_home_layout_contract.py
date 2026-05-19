"""
Tests for H5 Home Layout Contract (P22M-FIX2).

Covers:
1. appTopbar is inside screenHome (not outside phone-shell)
2. showScreen no longer manually controls appTopbar.style.display
3. .home-screen does not have display:flex directly
4. .screen.home-screen.active has display:flex
5. screenHome non-active has display:none (via .screen rule)
6. Home has home-content container
7. Home has home-bottom-cta container
8. btnStartCompose is in home-bottom-cta
9. Home has no ghost "查看历史" button
10. Home has no statusBar div
11. .home-content has overflow-y: auto
12. .home-content has scrollbar styles
13. .home-bottom-cta uses position: absolute or fixed
14. .home-bottom-cta uses env(safe-area-inset-bottom)
15. .home-content padding-bottom reserves CTA height
16. selectRecipient / selectScene / goCompose still exist
17. screenResult / screenHistory / screenSettings still exist
18. Formal H5 payload does not include profileId/coreProfileId
19. Dev mode profileId passthrough preserved
20. No new backend API paths
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestHomeLayoutStructure:
    """Home layout DOM structure."""

    def test_screen_home_has_home_screen_class(self):
        """screenHome has home-screen class."""
        html = _read(H5_INDEX)
        home_start = html.find('id="screenHome"')
        home_end = html.find("</section>", home_start)
        section = html[home_start:home_end]
        assert "home-screen" in section, "screenHome must have home-screen class"

    def test_home_has_home_content_container(self):
        """Home has home-content (scrollable) container."""
        html = _read(H5_INDEX)
        assert 'class="home-content"' in html or "class='home-content'" in html, \
            "home-content container not found"

    def test_home_has_home_bottom_cta_container(self):
        """Home has home-bottom-cta (fixed) container."""
        html = _read(H5_INDEX)
        assert 'class="home-bottom-cta"' in html or "class='home-bottom-cta'" in html, \
            "home-bottom-cta container not found"

    def test_btn_start_compose_in_home_bottom_cta(self):
        """btnStartCompose is in home-bottom-cta, not in home-content."""
        html = _read(H5_INDEX)
        # Find home-bottom-cta section
        cta_start = html.find('class="home-bottom-cta"')
        cta_end = html.find("</div>", cta_start)
        cta_section = html[cta_start:cta_end]
        assert 'id="btnStartCompose"' in cta_section, \
            "btnStartCompose must be inside home-bottom-cta"

        # Verify it's NOT inside home-content
        content_start = html.find('class="home-content"')
        content_end = html.find("</div>", content_start)
        content_section = html[content_start:content_end]
        # btnStartCompose should NOT be in home-content div
        # The home-content ends BEFORE home-bottom-cta starts
        assert content_section.find('id="btnStartCompose"') == -1, \
            "btnStartCompose must NOT be inside home-content"

    def test_home_no_ghost_history_button(self):
        """Home has no ghost '查看历史' button."""
        html = _read(H5_INDEX)
        home_start = html.find('id="screenHome"')
        home_end = html.find("</section>", home_start)
        section = html[home_start:home_end]
        assert "查看历史" not in section, \
            "Ghost '查看历史' button must not exist in Home"

    def test_home_no_status_bar_div(self):
        """Home has no statusBar div."""
        html = _read(H5_INDEX)
        assert 'id="statusBar"' not in html and "id='statusBar'" not in html, \
            "statusBar div must not exist"

    def test_app_topbar_inside_screen_home(self):
        """appTopbar is inside screenHome, not a direct child of phone-shell."""
        html = _read(H5_INDEX)
        # Find screenHome boundaries
        home_start = html.find('id="screenHome"')
        home_end = html.find("</section>", home_start)
        home_section = html[home_start:home_end]
        # appTopbar must be inside screenHome
        assert 'id="appTopbar"' in home_section, \
            "appTopbar must be inside screenHome"

    def test_history_button_calls_show_screen_history(self):
        """History button in Home topbar calls showScreen('history')."""
        html = _read(H5_INDEX)
        # Find appTopbar section
        topbar_start = html.find('id="appTopbar"')
        topbar_end = html.find("</header>", topbar_start)
        topbar_section = html[topbar_start:topbar_end]
        assert "showScreen('history')" in topbar_section or 'showScreen("history")' in topbar_section, \
            "History button must call showScreen('history')"

    def test_settings_button_calls_show_screen_settings(self):
        """Settings button in Home topbar calls showScreen('settings')."""
        html = _read(H5_INDEX)
        topbar_start = html.find('id="appTopbar"')
        topbar_end = html.find("</header>", topbar_start)
        topbar_section = html[topbar_start:topbar_end]
        assert "showScreen('settings')" in topbar_section or 'showScreen("settings")' in topbar_section, \
            "Settings button must call showScreen('settings')"


class TestHomeScreenDisplayFix:
    """Home screen display rules — home-screen must not override .screen {display:none}."""

    def test_home_screen_does_not_have_display_flex_directly(self):
        """.home-screen must not have display:flex directly (would override .screen{display:none})."""
        css = _read(H5_CSS)
        # Find .home-screen block
        idx = css.find(".home-screen {")
        end = css.find("}", idx)
        section = css[idx:end]
        # Must NOT have display:flex (only .screen.home-screen.active should have it)
        lines = [l.strip() for l in section.splitlines() if l.strip()]
        for line in lines:
            assert not line.startswith("display:") or "display:" not in line, \
                ".home-screen must not set display:flex directly"

    def test_screen_home_screen_active_has_display_flex(self):
        """.screen.home-screen.active must have display:flex."""
        css = _read(H5_CSS)
        idx = css.find(".screen.home-screen.active {")
        assert idx != -1, ".screen.home-screen.active rule not found"
        end = css.find("}", idx)
        section = css[idx:end]
        assert "display: flex" in section or "display:flex" in section, \
            ".screen.home-screen.active must have display:flex"

    def test_screen_active_restores_non_home_display(self):
        """.screen.active must have display:block for non-Home screens."""
        css = _read(H5_CSS)
        idx = css.find(".screen.active {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "display: block" in section or "display:block" in section, \
            ".screen.active must have display:block"

    def test_home_active_rule_after_screen_active(self):
        """.screen.home-screen.active must appear after .screen.active in CSS."""
        css = _read(H5_CSS)
        screen_active_idx = css.find(".screen.active")
        home_active_idx = css.find(".screen.home-screen.active")
        assert screen_active_idx != -1, ".screen.active rule not found"
        assert home_active_idx != -1, ".screen.home-screen.active rule not found"
        assert screen_active_idx < home_active_idx, \
            ".screen.home-screen.active must appear after .screen.active"

    def test_show_screen_no_longer_controls_app_topbar_display(self):
        """showScreen must not manually set appTopbar.style.display."""
        js = _read(H5_APP)
        start = js.find("function showScreen")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "appTopbar" not in section or "style.display" not in section, \
            "showScreen must not manually control appTopbar.style.display"


class TestHomeLayoutCSS:
    """Home layout CSS rules."""

    def test_home_content_overflow_y_auto(self):
        """.home-content has overflow-y: auto."""
        css = _read(H5_CSS)
        idx = css.find(".home-content {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "overflow-y: auto" in section, \
            ".home-content must have overflow-y: auto"

    def test_home_content_has_scrollbar_style(self):
        """.home-content has scrollbar-gutter or ::-webkit-scrollbar styles."""
        css = _read(H5_CSS)
        assert "scrollbar-gutter" in css or "::-webkit-scrollbar" in css, \
            ".home-content must have scrollbar style"

    def test_home_bottom_cta_position_absolute_or_fixed(self):
        """.home-bottom-cta uses position: absolute or fixed."""
        css = _read(H5_CSS)
        idx = css.find(".home-bottom-cta {")
        end = css.find("}", idx)
        section = css[idx:end]
        has_absolute = "position: absolute" in section
        has_fixed = "position: fixed" in section
        assert has_absolute or has_fixed, \
            ".home-bottom-cta must use position: absolute or fixed"

    def test_home_bottom_cta_uses_safe_area_inset_bottom(self):
        """.home-bottom-cta uses env(safe-area-inset-bottom)."""
        css = _read(H5_CSS)
        idx = css.find(".home-bottom-cta {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "safe-area-inset-bottom" in section, \
            ".home-bottom-cta must use env(safe-area-inset-bottom)"

    def test_home_content_padding_bottom_reserves_cta_height(self):
        """.home-content padding-bottom reserves space for bottom CTA."""
        css = _read(H5_CSS)
        idx = css.find(".home-content {")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "--home-bottom-cta-height" in section or "118px" in section, \
            ".home-content must reserve CTA height in padding-bottom"


class TestHomeScreenFunctions:
    """Home screen JS functions still exist."""

    def test_select_recipient_exists(self):
        """selectRecipient function still exists."""
        js = _read(H5_APP)
        assert "function selectRecipient" in js or "selectRecipient =" in js, \
            "selectRecipient function not found"

    def test_select_scene_exists(self):
        """selectScene function still exists."""
        js = _read(H5_APP)
        assert "function selectScene" in js or "selectScene =" in js, \
            "selectScene function not found"

    def test_go_compose_exists(self):
        """goCompose function still exists."""
        js = _read(H5_APP)
        assert "function goCompose" in js or "goCompose =" in js, \
            "goCompose function not found"


class TestOtherScreensPreserved:
    """Other screens remain intact."""

    def test_screen_result_still_exists(self):
        """screenResult still exists."""
        html = _read(H5_INDEX)
        assert 'id="screenResult"' in html, "screenResult not found"

    def test_screen_history_still_exists(self):
        """screenHistory still exists."""
        html = _read(H5_INDEX)
        assert 'id="screenHistory"' in html, "screenHistory not found"

    def test_screen_settings_still_exists(self):
        """screenSettings still exists."""
        html = _read(H5_INDEX)
        assert 'id="screenSettings"' in html, "screenSettings not found"


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

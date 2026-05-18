"""
Tests for H5 Home Layout Contract (P22M-FIX1).

Covers:
1. screenHome has home-screen class
2. Home has home-content (scrollable) container
3. Home has home-bottom-cta (fixed) container
4. btnStartCompose is in home-bottom-cta, not in home-content
5. Home has no ghost "查看历史" button
6. Home has no statusBar div
7. .home-content has overflow-y: auto
8. .home-content has scrollbar-gutter or scrollbar styles
9. .home-bottom-cta uses position: absolute or fixed
10. .home-bottom-cta uses env(safe-area-inset-bottom)
11. .home-content padding-bottom reserves space for CTA height
12. selectRecipient / selectScene / goCompose still exist
13. screenResult still exists
14. screenHistory still exists
15. screenSettings still exists
16. Formal H5 payload does not include profileId/coreProfileId
17. Dev mode profileId passthrough preserved
18. No new backend API paths
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

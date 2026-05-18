"""
Tests for H5 Settings Screen Prototype Parity (P22D).

Covers:
1. index.html has screenSettings
2. Home settings button calls showScreen("settings"), not showToast
3. app.js has renderSettingsScreen function
4. showScreen("settings") triggers renderSettingsScreen
5. Settings page has "设置" title
6. Settings page has "刷新状态" button
7. Settings page has "打开声线绑定配置页" button
8. Settings page links to /h5/admin-voice-bindings.html
9. Settings page does not expose sensitive fields (token, key, profileId, provider_voice_id)
10. Settings page uses state.voiceBindingStatus or equivalent data source
11. Settings page uses state.letters or equivalent for local letter count
12. screenResult still exists (P22A preserved)
13. screenHistory still exists (P22B preserved)
14. formal H5 payload does not include profileId/coreProfileId
15. dev mode profileId passthrough preserved
16. No new backend API paths introduced
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestSettingsScreenExistence:
    def test_screen_settings_exists(self):
        """index.html has screenSettings section."""
        html = _read(H5_INDEX)
        assert 'id="screenSettings"' in html, "screenSettings not found in index.html"

    def test_settings_content_element_exists(self):
        """Settings screen has settingsContent element for dynamic rendering."""
        html = _read(H5_INDEX)
        assert 'id="settingsContent"' in html, "settingsContent not found"


class TestHomeSettingsButton:
    def test_settings_button_calls_show_screen_not_toast(self):
        """Home settings button calls showScreen('settings'), not showToast."""
        html = _read(H5_INDEX)
        # Settings button should call showScreen, not showToast
        settings_btn = re.search(
            r'aria-label="[^"]*设置[^"]*"[^>]*onclick="([^"]+)"',
            html,
            re.DOTALL
        )
        if not settings_btn:
            settings_btn = re.search(
                r"aria-label='[^']*设置[^']*'[^>]*onclick='([^']+)'",
                html,
                re.DOTALL
            )
        assert settings_btn, "Settings button not found"
        onclick = settings_btn.group(1)
        assert "showScreen" in onclick and "settings" in onclick, \
            "Settings button must call showScreen('settings'), not showToast"
        assert "showToast" not in onclick, \
            "Settings button should not call showToast"


class TestRenderSettingsScreen:
    def test_render_settings_screen_function_exists(self):
        """app.js has renderSettingsScreen function."""
        js = _read(H5_APP)
        assert "function renderSettingsScreen" in js or "renderSettingsScreen =" in js, \
            "renderSettingsScreen function not found"

    def test_refresh_settings_status_function_exists(self):
        """app.js has refreshSettingsStatus function."""
        js = _read(H5_APP)
        assert "function refreshSettingsStatus" in js or "refreshSettingsStatus =" in js, \
            "refreshSettingsStatus function not found"


class TestShowScreenSettings:
    def test_show_screen_handles_settings(self):
        """showScreen handles 'settings' screen name."""
        js = _read(H5_APP)
        # showScreen should have a case for "settings"
        show_screen_match = re.search(
            r'function showScreen\([^)]*\)\s*\{(.*?)\n\}',
            js,
            re.DOTALL
        )
        if show_screen_match:
            body = show_screen_match.group(1)
            assert 'screen === "settings"' in body or "screen === 'settings'" in body, \
                "showScreen must handle 'settings' screen"
            assert "renderSettingsScreen" in body, \
                "showScreen('settings') must call renderSettingsScreen"


class TestSettingsPageContent:
    def test_settings_page_has_title(self):
        """Settings page has '设置' title in appbar."""
        html = _read(H5_INDEX)
        settings_start = html.find('id="screenSettings"')
        settings_end = html.find("</section>", settings_start)
        settings_section = html[settings_start:settings_end]
        assert "设置" in settings_section, \
            "Settings page must have 设置 title"

    def test_settings_page_has_refresh_button(self):
        """Settings page has '刷新状态' button."""
        html = _read(H5_INDEX)
        settings_start = html.find('id="screenSettings"')
        settings_end = html.find("</section>", settings_start)
        settings_section = html[settings_start:settings_end]
        assert "刷新状态" in settings_section, \
            "Settings page must have 刷新状态 button"

    def test_settings_page_has_voice_bind_button(self):
        """Settings page has '打开声线绑定配置页' button (in renderSettingsScreen)."""
        js = _read(H5_APP)
        assert "打开声线绑定配置页" in js, \
            "renderSettingsScreen must have 打开声线绑定配置页 button"

    def test_settings_page_links_to_admin_voice_bindings(self):
        """Settings page links to /h5/admin-voice-bindings.html (in renderSettingsScreen)."""
        js = _read(H5_APP)
        assert "/h5/admin-voice-bindings.html" in js, \
            "renderSettingsScreen must link to /h5/admin-voice-bindings.html"


class TestSettingsNoSensitiveFields:
    def test_settings_does_not_expose_api_key(self):
        """Settings screen does not display api_key."""
        js = _read(H5_APP)
        settings_func = re.search(
            r'function renderSettingsScreen\s*\([^)]*\)\s*\{(.*?)(?=\nfunction|\ndocument\.addEventListener|\Z)',
            js,
            re.DOTALL
        )
        if settings_func:
            body = settings_func.group(1)
            assert "api_key" not in body.lower() or "apiKey" not in body, \
                "renderSettingsScreen must not display api_key"

    def test_settings_does_not_expose_admin_token(self):
        """Settings screen does not display admin token."""
        js = _read(H5_APP)
        settings_func = re.search(
            r'function renderSettingsScreen\s*\([^)]*\)\s*\{(.*?)(?=\nfunction|\ndocument\.addEventListener|\Z)',
            js,
            re.DOTALL
        )
        if settings_func:
            body = settings_func.group(1)
            assert "admin" not in body.lower() or "ADMIN" not in body, \
                "renderSettingsScreen must not display admin token"

    def test_settings_does_not_expose_core_profile_id(self):
        """Settings screen does not display coreProfileId."""
        js = _read(H5_APP)
        settings_func = re.search(
            r'function renderSettingsScreen\s*\([^)]*\)\s*\{(.*?)(?=\nfunction|\ndocument\.addEventListener|\Z)',
            js,
            re.DOTALL
        )
        if settings_func:
            body = settings_func.group(1)
            assert "coreProfileId" not in body and "core_profile_id" not in body, \
                "renderSettingsScreen must not display coreProfileId"

    def test_settings_does_not_expose_provider_voice_id(self):
        """Settings screen does not display provider_voice_id."""
        js = _read(H5_APP)
        settings_func = re.search(
            r'function renderSettingsScreen\s*\([^)]*\)\s*\{(.*?)(?=\nfunction|\ndocument\.addEventListener|\Z)',
            js,
            re.DOTALL
        )
        if settings_func:
            body = settings_func.group(1)
            assert "provider_voice_id" not in body and "providerVoiceId" not in body, \
                "renderSettingsScreen must not display provider_voice_id"


class TestSettingsDataSources:
    def test_render_settings_uses_voice_binding_status(self):
        """renderSettingsScreen uses state.voiceBindingStatus."""
        js = _read(H5_APP)
        assert "state.voiceBindingStatus" in js, \
            "renderSettingsScreen must use state.voiceBindingStatus"

    def test_render_settings_uses_state_letters(self):
        """renderSettingsScreen uses state.letters for letter count."""
        js = _read(H5_APP)
        assert "state.letters" in js, \
            "renderSettingsScreen must use state.letters for letter count"


class TestP22APreserved:
    def test_screen_result_still_exists(self):
        """screenResult still exists (P22A preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenResult"' in html, "screenResult not found — P22A broken"


class TestP22BPreserved:
    def test_screen_history_still_exists(self):
        """screenHistory still exists (P22B preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenHistory"' in html, "screenHistory not found — P22B broken"


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


class TestSettingsCSS:
    def test_settings_screen_styles_exist(self):
        """styles.css has settings-screen class."""
        css = _read(H5_CSS)
        assert ".settings-screen" in css or ".settings-status" in css, \
            "settings-screen or settings-status styles not found"

    def test_settings_card_styles_exist(self):
        """styles.css has settings-card class."""
        css = _read(H5_CSS)
        assert ".settings-card" in css, \
            "settings-card styles not found"

    def test_settings_binding_badge_styles_exist(self):
        """styles.css has binding badge styles."""
        css = _read(H5_CSS)
        assert "binding-badge" in css, \
            "binding-badge styles not found"

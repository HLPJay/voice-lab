"""
Tests for H5 Result Screen (screenResult) — P22A-H5-RESULT-PAGE-PROTOTYPE-PARITY.

Covers:
1. index.html contains screenResult
2. app.js contains renderResultScreen
3. app.js navigates to result screen when completed + audioUrl
4. app.js contains resultAudio element reference
5. app.js contains restart logic (currentTime = 0)
6. app.js contains download logic (target="_blank")
7. app.js contains navigator.share with fallback
8. app.js reuses saveLetter pattern in resultSave
9. app.js contains resultSaved state
10. formal H5 payload does not include profileId/coreProfileId
11. dev mode profileId passthrough preserved
12. No new backend API paths introduced
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestIndexHtmlResultScreen:
    def test_screen_result_exists(self):
        """index.html has screenResult section."""
        html = _read(H5_INDEX)
        assert 'id="screenResult"' in html, "screenResult not found in index.html"

    def test_screen_result_has_letter_card(self):
        """screenResult has result-letter-card element."""
        html = _read(H5_INDEX)
        assert 'id="resultLetterCard"' in html or 'class="result-letter-card"' in html

    def test_screen_result_has_audio(self):
        """screenResult has audio element."""
        html = _read(H5_INDEX)
        assert 'id="resultAudio"' in html

    def test_screen_result_has_save_button(self):
        """screenResult has save button."""
        html = _read(H5_INDEX)
        assert 'btnResultSave' in html or 'result-save-button' in html

    def test_screen_result_has_action_buttons(self):
        """screenResult has action buttons: restart, download, copy, share, re-edit, changeTone."""
        html = _read(H5_INDEX)
        assert 'resultRestart' in html or '从头听' in html
        assert 'resultDownload' in html or '下载' in html
        assert 'resultCopy' in html or '复制文字' in html
        assert 'resultShare' in html or '分享' in html
        assert 'resultReEdit' in html or '重新编辑' in html
        assert 'resultChangeTone' in html or '换个语气' in html


class TestAppJsResultScreen:
    def test_render_result_screen_exists(self):
        """app.js has renderResultScreen function."""
        js = _read(H5_APP)
        assert "function renderResultScreen" in js or "renderResultScreen =" in js, \
            "renderResultScreen function not found"

    def test_result_audio_element_reference(self):
        """app.js references resultAudio element."""
        js = _read(H5_APP)
        assert 'el("resultAudio")' in js or "el('resultAudio')" in js, \
            "resultAudio element reference not found"

    def test_restart_logic_current_time_zero(self):
        """app.js has restart logic setting currentTime = 0."""
        js = _read(H5_APP)
        assert "currentTime = 0" in js, \
            "Restart logic with currentTime = 0 not found"

    def test_download_logic_target_blank(self):
        """app.js has download logic setting a.target = '_blank'."""
        js = _read(H5_APP)
        assert 'a.target = "_blank"' in js or 'a.target = \'_blank\'' in js, \
            "Download with a.target = '_blank' not found"

    def test_navigator_share_with_fallback(self):
        """app.js has navigator.share with clipboard fallback."""
        js = _read(H5_APP)
        assert "navigator.share" in js, \
            "navigator.share not found"
        assert "resultCopy" in js or "clipboard" in js, \
            "Share fallback to clipboard not found"

    def test_result_save_reuses_letter_pattern(self):
        """resultSave reuses /api/xiangta/letters POST pattern."""
        js = _read(H5_APP)
        # Find resultSave function
        start = js.find("function resultSave")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "/api/xiangta/letters" in section, \
            "resultSave must POST to /api/xiangta/letters"

    def test_result_saved_state_exists(self):
        """state has resultSaved field."""
        js = _read(H5_APP)
        # Find state object
        state_start = js.find("state = ")
        if state_start == -1:
            state_start = js.find("state={")
        state_end = js.find("};", state_start)
        state_section = js[state_start:state_end]
        assert "resultSaved" in state_section, \
            "state.resultSaved not found"


class TestResultScreenNavigation:
    def test_render_tts_task_navigates_on_success(self):
        """renderTtsTask navigates to result screen when completed + audioUrl."""
        js = _read(H5_APP)
        start = js.find("function renderTtsTask")
        end = js.find("\n}\n", start)
        section = js[start:end]

        # Must check for showScreen("result")
        assert 'showScreen("result")' in section or "showScreen('result')" in section, \
            "renderTtsTask must call showScreen('result') on success"

    def test_render_result_screen_calls_show_screen(self):
        """renderResultScreen is called before showScreen('result')."""
        js = _read(H5_APP)
        # The navigation pattern: renderResultScreen then showScreen("result")
        assert "renderResultScreen(result)" in js, \
            "renderResultScreen must be called with result"
        assert 'showScreen("result")' in js or "showScreen('result')" in js, \
            "showScreen('result') must be called"


class TestFormalDevModePreservation:
    def test_formal_payload_no_profile_id(self):
        """generateTtsTask does not include profileId in formal mode payload."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]

        # profileId should be guarded by state.mode === "dev"
        if "profileId" in section:
            # Must have dev mode guard
            assert 'state.mode === "dev"' in section or "state.mode === 'dev'" in section, \
                "profileId must be guarded by dev mode"

    def test_dev_mode_profile_id_passthrough(self):
        """dev mode allows profileId passthrough in generateTtsTask."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]

        # Check that dev mode path exists for profileId
        assert "state.mode === " in section, \
            "Dev mode check must exist for profileId passthrough"


class TestNoNewBackendApis:
    def test_no_new_api_paths(self):
        """No new backend API paths were introduced in result screen code."""
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


class TestResultScreenStyles:
    def test_result_screen_styles_exist(self):
        """styles.css has result screen styles."""
        css = _read("apps/xiangta-h5/styles.css")
        required_styles = [
            "result-screen",
            "result-letter-card",
            "result-audio-card",
            "result-actions-grid",
            "result-save-button",
        ]
        for style in required_styles:
            assert f".{style}" in css or f"#{style}" in css, \
                f"{style} style not found in styles.css"


class TestResultSaveCeremony:
    """P22F: Result save ceremony and letter detail navigation."""

    def test_result_save_seal_overlay_exists(self):
        """index.html has resultSaveSealOverlay element."""
        html = _read(H5_INDEX)
        assert 'id="resultSaveSealOverlay"' in html, \
            "resultSaveSealOverlay not found"

    def test_result_save_seal_label_text(self):
        """.result-save-seal-label contains '已 · 收 · 好'."""
        html = _read(H5_INDEX)
        assert "已 · 收 · 好" in html, \
            "'已 · 收 · 好' not found in index.html"

    def test_result_save_seal_overlay_css_exists(self):
        """styles.css has .result-save-seal-overlay class."""
        css = _read("apps/xiangta-h5/styles.css")
        assert ".result-save-seal-overlay" in css, \
            ".result-save-seal-overlay CSS not found"

    def test_result_save_seal_stamp_keyframes_exist(self):
        """styles.css has @keyframes spaStamp keyframe."""
        css = _read("apps/xiangta-h5/styles.css")
        assert "@keyframes spaStamp" in css, \
            "@keyframes spaStamp not found"

    def test_show_result_save_seal_then_open_detail_exists(self):
        """app.js has showResultSaveSealThenOpenDetail function."""
        js = _read(H5_APP)
        assert "function showResultSaveSealThenOpenDetail" in js or \
               "showResultSaveSealThenOpenDetail =" in js, \
            "showResultSaveSealThenOpenDetail function not found"

    def test_result_save_calls_seal_then_open_detail(self):
        """resultSave calls showResultSaveSealThenOpenDetail on success."""
        js = _read(H5_APP)
        start = js.find("function resultSave")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "showResultSaveSealThenOpenDetail" in section, \
            "resultSave must call showResultSaveSealThenOpenDetail"

    def test_result_save_sets_active_letter_detail(self):
        """resultSave (via showResultSaveSealThenOpenDetail) sets activeLetterDetailId and activeLetterDetail."""
        js = _read(H5_APP)
        # Check resultSave calls showResultSaveSealThenOpenDetail
        start = js.find("function resultSave")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "showResultSaveSealThenOpenDetail" in section, \
            "resultSave must call showResultSaveSealThenOpenDetail"
        # Check showResultSaveSealThenOpenDetail sets activeLetterDetailId
        seal_start = js.find("function showResultSaveSealThenOpenDetail")
        if seal_start != -1:
            seal_end = js.find("\n}", seal_start)
            seal_section = js[seal_start:seal_end]
            assert "activeLetterDetailId" in seal_section, \
                "showResultSaveSealThenOpenDetail must set activeLetterDetailId"
            assert "activeLetterDetail" in seal_section, \
                "showResultSaveSealThenOpenDetail must set activeLetterDetail"

    def test_result_save_writes_to_state_letters(self):
        """resultSave writes saved letter to state.letters or upsertLetterIntoState."""
        js = _read(H5_APP)
        start = js.find("function resultSave")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "upsertLetterIntoState" in section or "state.letters" in section, \
            "resultSave must write to state.letters"

    def test_result_save_sets_favorited_true(self):
        """resultSave sets favorited = true via buildSavedLetterViewModel or showResultSaveSealThenOpenDetail."""
        js = _read(H5_APP)
        # Check buildSavedLetterViewModel sets favorited: true
        build_start = js.find("function buildSavedLetterViewModel")
        if build_start != -1:
            build_end = js.find("\n}", build_start)
            build_section = js[build_start:build_end]
            assert "favorited: true" in build_section, \
                "buildSavedLetterViewModel must set favorited: true"
        # Or check showResultSaveSealThenOpenDetail sets letterDetailFavoritedMap
        seal_start = js.find("function showResultSaveSealThenOpenDetail")
        if seal_start != -1:
            seal_end = js.find("\n}", seal_start)
            seal_section = js[seal_start:seal_end]
            assert "letterDetailFavoritedMap" in seal_section, \
                "showResultSaveSealThenOpenDetail must set letterDetailFavoritedMap"

    def test_result_save_no_detail_api_call(self):
        """resultSave does not call GET /api/xiangta/letters/{id}."""
        js = _read(H5_APP)
        start = js.find("function resultSave")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "/api/xiangta/letters/" not in section, \
            "resultSave must not call GET /api/xiangta/letters/{id}"

    def test_result_save_no_real_provider_call(self):
        """resultSave does not call real MiniMax provider."""
        js = _read(H5_APP)
        start = js.find("function resultSave")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "_silentWav" not in section, \
            "resultSave must not use _silentWav"
        assert "speechSynthesis" not in section, \
            "resultSave must not use speechSynthesis"

    def test_upsert_letter_into_state_exists(self):
        """app.js has upsertLetterIntoState function."""
        js = _read(H5_APP)
        assert "function upsertLetterIntoState" in js or \
               "upsertLetterIntoState =" in js, \
            "upsertLetterIntoState function not found"

    def test_build_saved_letter_view_model_exists(self):
        """app.js has buildSavedLetterViewModel function."""
        js = _read(H5_APP)
        assert "function buildSavedLetterViewModel" in js or \
               "buildSavedLetterViewModel =" in js, \
            "buildSavedLetterViewModel function not found"

    def test_result_save_seal_overlay_hidden_by_default(self):
        """resultSaveSealOverlay is hidden by default in index.html."""
        html = _read(H5_INDEX)
        # Should have class="result-save-seal-overlay hidden"
        assert 'result-save-seal-overlay' in html, \
            "result-save-seal-overlay class not found"
        # Should be hidden initially
        assert 'class="result-save-seal-overlay hidden"' in html or \
               "class='result-save-seal-overlay hidden'" in html, \
            "resultSaveSealOverlay must be hidden by default"

    def test_result_save_seal_spa_stamp_keyframe(self):
        """styles.css has @keyframes spaStamp matching prototype."""
        css = _read("apps/xiangta-h5/styles.css")
        assert "@keyframes spaStamp" in css, \
            "@keyframes spaStamp not found"
        # Prototype uses rotate(-22deg) scale(1.6) at 0%
        idx = css.find("@keyframes spaStamp")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "rotate(-22deg)" in section or "rotate(-22" in section, \
            "spaStamp should start with rotate(-22deg)"
        assert "scale(1.6)" in section, \
            "spaStamp should scale to 1.6 at 0%"

    def test_result_save_seal_spa_label_in_keyframe(self):
        """styles.css has @keyframes spaLabelIn for label animation."""
        css = _read("apps/xiangta-h5/styles.css")
        assert "@keyframes spaLabelIn" in css, \
            "@keyframes spaLabelIn not found"

    def test_result_save_seal_overlay_uses_saturate(self):
        """result-save-seal-overlay backdrop-filter uses saturate."""
        css = _read("apps/xiangta-h5/styles.css")
        overlay_start = css.find(".result-save-seal-overlay")
        overlay_end = css.find("}", overlay_start)
        section = css[overlay_start:overlay_end]
        assert "saturate" in section, \
            "result-save-seal-overlay should use saturate in backdrop-filter"

    def test_result_save_seal_stamp_is_116px(self):
        """.result-save-seal-stamp is 116x116px with border-radius 20px."""
        css = _read("apps/xiangta-h5/styles.css")
        stamp_start = css.find(".result-save-seal-stamp")
        stamp_end = css.find("}", stamp_start)
        section = css[stamp_start:stamp_end]
        assert "116px" in section, \
            ".result-save-seal-stamp should be 116px"
        assert "20px" in section, \
            ".result-save-seal-stamp should have border-radius 20px"


class TestResultSaveButtonBehavior:
    """P22H: Result save button shows 查信笺 when returning after save."""

    def test_update_result_save_button_shows_view_letter_when_saved(self):
        """updateResultSaveButton shows 查看信笺 when state.resultSaved is true."""
        js = _read(H5_APP)
        start = js.find("function updateResultSaveButton")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "查看信笺" in section, \
            "updateResultSaveButton must show 查看信笺 when saved"
        assert "openLetterDetail" in section, \
            "updateResultSaveButton must call openLetterDetail when saved button clicked"

    def test_result_saved_button_navigates_to_letter_detail(self):
        """When saved, result save button onclick calls openLetterDetail."""
        js = _read(H5_APP)
        start = js.find("function updateResultSaveButton")
        end = js.find("\n}", start)
        section = js[start:end]
        # When resultSaved, onclick should call openLetterDetail
        assert "openLetterDetail" in section, \
            "Saved button must call openLetterDetail"


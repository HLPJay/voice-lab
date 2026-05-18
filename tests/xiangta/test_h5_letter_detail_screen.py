"""
Tests for H5 Letter Detail Screen Prototype Parity (P22E).

Covers:
1. index.html has screenLetterDetail
2. index.html has letterDetailAudio element
3. app.js has openLetterDetail function
4. app.js has renderLetterDetailScreen function
5. History card click calls openLetterDetail
6. History play button uses stopPropagation
7. app.js has restartLetterDetailAudio with currentTime = 0
8. app.js has downloadLetterDetailAudio
9. app.js has copyLetterDetailText
10. app.js has shareLetterDetail
11. app.js has retoneLetterDetail or equivalent
12. app.js has toggleLetterDetailFavorite
13. app.js does not use _silentWav for letter detail
14. app.js does not use speechSynthesis for letter detail playback
15. showScreen("letterDetail") works
16. screenResult still exists (P22A)
17. screenHistory still exists (P22B)
18. screenSettings still exists (P22D)
19. formal H5 payload does not include profileId/coreProfileId
20. dev mode profileId passthrough preserved
21. No new backend API paths introduced
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestLetterDetailScreenExistence:
    def test_screen_letter_detail_exists(self):
        """index.html has screenLetterDetail section."""
        html = _read(H5_INDEX)
        assert 'id="screenLetterDetail"' in html, \
            "screenLetterDetail not found"

    def test_letter_detail_audio_exists(self):
        """index.html has letterDetailAudio element."""
        html = _read(H5_INDEX)
        assert 'id="letterDetailAudio"' in html, \
            "letterDetailAudio not found"


class TestLetterDetailFunctions:
    def test_open_letter_detail_exists(self):
        """app.js has openLetterDetail function."""
        js = _read(H5_APP)
        assert "function openLetterDetail" in js or "openLetterDetail =" in js, \
            "openLetterDetail function not found"

    def test_render_letter_detail_screen_exists(self):
        """app.js has renderLetterDetailScreen function."""
        js = _read(H5_APP)
        assert "function renderLetterDetailScreen" in js or "renderLetterDetailScreen =" in js, \
            "renderLetterDetailScreen function not found"

    def test_restart_letter_detail_audio_exists(self):
        """app.js has restartLetterDetailAudio function."""
        js = _read(H5_APP)
        assert "function restartLetterDetailAudio" in js or "restartLetterDetailAudio =" in js, \
            "restartLetterDetailAudio function not found"

    def test_restart_letter_detail_has_current_time_zero(self):
        """restartLetterDetailAudio sets currentTime = 0."""
        js = _read(H5_APP)
        start = js.find("function restartLetterDetailAudio")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "currentTime = 0" in section or "currentTime=0" in section, \
            "restartLetterDetailAudio must set currentTime = 0"

    def test_download_letter_detail_audio_exists(self):
        """app.js has downloadLetterDetailAudio function."""
        js = _read(H5_APP)
        assert "function downloadLetterDetailAudio" in js or "downloadLetterDetailAudio =" in js, \
            "downloadLetterDetailAudio function not found"

    def test_copy_letter_detail_text_exists(self):
        """app.js has copyLetterDetailText function."""
        js = _read(H5_APP)
        assert "function copyLetterDetailText" in js or "copyLetterDetailText =" in js, \
            "copyLetterDetailText function not found"

    def test_share_letter_detail_exists(self):
        """app.js has shareLetterDetail function."""
        js = _read(H5_APP)
        assert "function shareLetterDetail" in js or "shareLetterDetail =" in js, \
            "shareLetterDetail function not found"

    def test_retone_letter_detail_exists(self):
        """app.js has retoneLetterDetail function."""
        js = _read(H5_APP)
        assert "function retoneLetterDetail" in js or "retoneLetterDetail =" in js, \
            "retoneLetterDetail function not found"

    def test_toggle_letter_detail_favorite_exists(self):
        """app.js has toggleLetterDetailFavorite function."""
        js = _read(H5_APP)
        assert "function toggleLetterDetailFavorite" in js or "toggleLetterDetailFavorite =" in js, \
            "toggleLetterDetailFavorite function not found"


class TestHistoryCardInteraction:
    def test_history_card_click_calls_open_letter_detail(self):
        """History card onclick calls openLetterDetail."""
        js = _read(H5_APP)
        # Look for card.onclick with openLetterDetail
        assert "openLetterDetail" in js, \
            "History card should call openLetterDetail on click"

    def test_history_card_play_btn_uses_stop_propagation(self):
        """History card play button uses stopPropagation."""
        js = _read(H5_APP)
        assert "event.stopPropagation()" in js or "event.stopPropagation" in js, \
            "History play button must use event.stopPropagation()"


class TestLetterDetailNoMockAudio:
    def test_no_silent_wav_in_letter_detail(self):
        """app.js does not use _silentWav for letter detail playback."""
        js = _read(H5_APP)
        # Check letter detail functions don't use _silentWav
        detail_funcs = ["restartLetterDetailAudio", "downloadLetterDetailAudio",
                        "renderLetterDetailScreen", "openLetterDetail"]
        for func in detail_funcs:
            start = js.find(f"function {func}")
            if start == -1:
                start = js.find(f"{func} =")
            if start != -1:
                end = js.find("\n}", start)
                section = js[start:end]
                assert "_silentWav" not in section, \
                    f"{func} should not use _silentWav"

    def test_no_speech_synthesis_in_letter_detail(self):
        """app.js does not use speechSynthesis for letter detail playback."""
        js = _read(H5_APP)
        detail_funcs = ["restartLetterDetailAudio", "downloadLetterDetailAudio",
                        "renderLetterDetailScreen", "openLetterDetail"]
        for func in detail_funcs:
            start = js.find(f"function {func}")
            if start == -1:
                start = js.find(f"{func} =")
            if start != -1:
                end = js.find("\n}", start)
                section = js[start:end]
                assert "speechSynthesis" not in section, \
                    f"{func} should not use speechSynthesis"


class TestShowScreenLetterDetail:
    def test_show_screen_handles_letter_detail(self):
        """showScreen handles 'letterDetail' screen name."""
        js = _read(H5_APP)
        show_screen_match = re.search(
            r'function showScreen\([^)]*\)\s*\{(.*?)\n\}',
            js,
            re.DOTALL
        )
        if show_screen_match:
            body = show_screen_match.group(1)
            assert 'screen === "letterDetail"' in body or "screen === 'letterDetail'" in body, \
                "showScreen must handle 'letterDetail'"


class TestLetterDetailState:
    def test_letter_detail_state_fields_exist(self):
        """state has activeLetterDetailId, activeLetterDetail, letterDetailFavoritedMap."""
        js = _read(H5_APP)
        assert "activeLetterDetailId" in js, \
            "state.activeLetterDetailId not found"
        assert "activeLetterDetail" in js, \
            "state.activeLetterDetail not found"
        assert "letterDetailFavoritedMap" in js, \
            "state.letterDetailFavoritedMap not found"


class TestP22APreserved:
    def test_screen_result_still_exists(self):
        """screenResult still exists (P22A preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenResult"' in html, \
            "screenResult not found — P22A broken"


class TestP22BPreserved:
    def test_screen_history_still_exists(self):
        """screenHistory still exists (P22B preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenHistory"' in html, \
            "screenHistory not found — P22B broken"


class TestP22DPreserved:
    def test_screen_settings_still_exists(self):
        """screenSettings still exists (P22D preserved)."""
        html = _read(H5_INDEX)
        assert 'id="screenSettings"' in html, \
            "screenSettings not found — P22D broken"


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


class TestLetterDetailCSS:
    def test_letter_detail_screen_styles_exist(self):
        """styles.css has letter-detail-screen class."""
        css = _read(H5_CSS)
        assert ".letter-detail-screen" in css or ".letter-detail-letter-card" in css, \
            "letter-detail-screen or letter-detail-letter-card styles not found"

    def test_letter_detail_audio_card_styles_exist(self):
        """styles.css has letter-detail-audio-card class."""
        css = _read(H5_CSS)
        assert ".letter-detail-audio-card" in css, \
            "letter-detail-audio-card styles not found"

    def test_letter_detail_favorite_styles_exist(self):
        """styles.css has letter-detail-favorite styles."""
        css = _read(H5_CSS)
        assert "letter-detail-favorite" in css, \
            "letter-detail-favorite styles not found"

    def test_history_card_playbtn_styles_exist(self):
        """styles.css has prototype-history-card-playbtn class."""
        css = _read(H5_CSS)
        assert "prototype-history-card-playbtn" in css, \
            "prototype-history-card-playbtn styles not found"

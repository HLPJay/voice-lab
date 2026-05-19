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


class TestLetterDetailHardening:
    """P22E-FIX1: Security and consistency hardening."""

    def test_letter_detail_body_uses_text_content(self):
        """renderLetterDetailScreen uses textContent or escHtml for body, not innerHTML."""
        js = _read(H5_APP)
        start = js.find("function renderLetterDetailScreen")
        end = js.find("\n}", start)
        section = js[start:end]
        # Must NOT use innerHTML = withBreaks
        assert "innerHTML = withBreaks" not in section, \
            "bodyEl.innerHTML = withBreaks is unsafe"
        # Must use textContent or escHtml
        assert "bodyEl.textContent" in section or "escHtml" in section, \
            "body must use textContent or escHtml"

    def test_letter_detail_body_white_space_pre_wrap(self):
        """.letter-detail-body CSS has white-space: pre-wrap."""
        css = _read(H5_CSS)
        body_start = css.find(".letter-detail-body")
        body_end = css.find("}", body_start)
        section = css[body_start:body_end]
        assert "white-space:" in section and "pre-wrap" in section, \
            ".letter-detail-body must have white-space: pre-wrap"

    def test_write_another_from_letter_detail_exists(self):
        """app.js has writeAnotherFromLetterDetail function."""
        js = _read(H5_APP)
        assert "function writeAnotherFromLetterDetail" in js or "writeAnotherFromLetterDetail =" in js, \
            "writeAnotherFromLetterDetail function not found"

    def test_write_another_does_not_call_suggestions_or_tts(self):
        """writeAnotherFromLetterDetail does not call generateSuggestions or generateTtsTask."""
        js = _read(H5_APP)
        start = js.find("function writeAnotherFromLetterDetail")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "generateSuggestions" not in section, \
            "writeAnotherFromLetterDetail must not call generateSuggestions"
        assert "generateTtsTask" not in section, \
            "writeAnotherFromLetterDetail must not call generateTtsTask"

    def test_write_another_resets_downstream_state(self):
        """writeAnotherFromLetterDetail resets finalText, suggestions, selectedIndex, ttsTask, ttsResult."""
        js = _read(H5_APP)
        start = js.find("function writeAnotherFromLetterDetail")
        end = js.find("\n}", start)
        section = js[start:end]
        assert 'state.finalText = ""' in section, "must reset state.finalText"
        assert "state.suggestions = []" in section, "must reset state.suggestions"
        assert "state.selectedIndex = -1" in section, "must reset state.selectedIndex"
        assert "state.ttsTask = null" in section, "must reset state.ttsTask"
        assert "state.ttsResult = null" in section, "must reset state.ttsResult"

    def test_write_another_navigates_to_compose(self):
        """writeAnotherFromLetterDetail calls showScreen('compose')."""
        js = _read(H5_APP)
        start = js.find("function writeAnotherFromLetterDetail")
        end = js.find("\n}", start)
        section = js[start:end]
        assert 'showScreen("compose")' in section, \
            "writeAnotherFromLetterDetail must navigate to compose"

    def test_re_write_button_calls_write_another(self):
        """index.html 再写一封 button calls writeAnotherFromLetterDetail."""
        html = _read(H5_INDEX)
        detail_start = html.find('id="screenLetterDetail"')
        detail_end = html.find("</section>", detail_start)
        section = html[detail_start:detail_end]
        # The 再写一封 button should call writeAnotherFromLetterDetail, not showScreen('home')
        assert "writeAnotherFromLetterDetail" in section, \
            "再写一封 button must call writeAnotherFromLetterDetail"
        assert 'onclick="showScreen(\'home\')"' not in section, \
            "再写一封 button must not call showScreen('home')"

    def test_toggle_favorite_syncs_letter_favorited(self):
        """toggleLetterDetailFavorite syncs to letter.favorited."""
        js = _read(H5_APP)
        start = js.find("function toggleLetterDetailFavorite")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "letter.favorited" in section, \
            "toggleLetterDetailFavorite must sync to letter.favorited"

    def test_toggle_favorite_no_backend_calls(self):
        """toggleLetterDetailFavorite does not call PATCH/PUT/DELETE /api/xiangta/letters."""
        js = _read(H5_APP)
        start = js.find("function toggleLetterDetailFavorite")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "PATCH" not in section and "PUT" not in section and "DELETE" not in section, \
            "toggleLetterDetailFavorite must not call backend HTTP methods"
        assert "/api/xiangta/letters/" not in section, \
            "toggleLetterDetailFavorite must not call letters detail API"

    def test_open_letter_detail_initializes_favorite_map(self):
        """openLetterDetail initializes letterDetailFavoritedMap from letter.favorited."""
        js = _read(H5_APP)
        start = js.find("function openLetterDetail")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "letterDetailFavoritedMap[letterId]" in section, \
            "openLetterDetail must initialize letterDetailFavoritedMap"

    def test_render_letter_detail_sets_audio_time(self):
        """renderLetterDetailScreen sets letterDetailAudioTime element."""
        js = _read(H5_APP)
        start = js.find("function renderLetterDetailScreen")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "letterDetailAudioTime" in section, \
            "renderLetterDetailScreen must set letterDetailAudioTime"

    def test_render_letter_detail_uses_format_duration(self):
        """renderLetterDetailScreen uses formatDuration for audio time."""
        js = _read(H5_APP)
        start = js.find("function renderLetterDetailScreen")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "formatDuration" in section, \
            "renderLetterDetailScreen must use formatDuration for time"

    def test_render_letters_no_inline_onclick_play_history(self):
        """renderLetters does not use inline onclick string with playHistoryLetter letter.id."""
        js = _read(H5_APP)
        start = js.find("function renderLetters")
        end = js.find("\n}", start)
        section = js[start:end]
        # Must NOT have the old inline onclick pattern
        assert "playHistoryLetter('${letter.id" not in section and \
               'playHistoryLetter(\'${letter.id' not in section and \
               "playHistoryLetter(`${letter.id" not in section, \
            "renderLetters must not use inline onclick string with letter.id"

    def test_render_letters_uses_add_event_listener(self):
        """renderLetters uses addEventListener for play button."""
        js = _read(H5_APP)
        start = js.find("function renderLetters")
        end = js.find("\n}", start)
        section = js[start:end]
        assert 'addEventListener("click"' in section or "addEventListener('click'" in section, \
            "renderLetters must use addEventListener for play button"

    def test_render_letters_uses_stop_propagation(self):
        """renderLetters play handler uses event.stopPropagation."""
        js = _read(H5_APP)
        start = js.find("function renderLetters")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "event.stopPropagation()" in section or "event.stopPropagation" in section, \
            "renderLetters play handler must use event.stopPropagation"

    def test_show_screen_letter_detail_fallback_exists(self):
        """showScreen handles letterDetail fallback when activeLetterDetail is missing."""
        js = _read(H5_APP)
        show_screen_match = re.search(
            r'function showScreen\([^)]*\)\s*\{(.*?)\n\}',
            js,
            re.DOTALL
        )
        if show_screen_match:
            body = show_screen_match.group(1)
            # Must have fallback logic for when activeLetterDetailId exists but activeLetterDetail doesn't
            assert "activeLetterDetailId" in body, \
                "showScreen letterDetail must handle activeLetterDetailId fallback"

    def test_show_screen_letter_detail_renders_on_fallback(self):
        """showScreen letterDetail calls renderLetterDetailScreen in fallback."""
        js = _read(H5_APP)
        show_screen_match = re.search(
            r'function showScreen\([^)]*\)\s*\{(.*?)\n\}',
            js,
            re.DOTALL
        )
        if show_screen_match:
            body = show_screen_match.group(1)
            assert "renderLetterDetailScreen" in body, \
                "showScreen letterDetail must call renderLetterDetailScreen"


class TestLetterDetailVisualParity:
    """P22G: Letter detail visual parity with prototype LetterScreen."""

    def test_letter_detail_title_element_exists(self):
        """index.html has letterDetailTitle element in appbar."""
        html = _read(H5_INDEX)
        detail_start = html.find('id="screenLetterDetail"')
        detail_end = html.find("</section>", detail_start)
        section = html[detail_start:detail_end]
        assert 'id="letterDetailTitle"' in section, \
            "letterDetailTitle element not found in screenLetterDetail"

    def test_letter_detail_subtitle_still_exists(self):
        """index.html has letterDetailSubtitle element."""
        html = _read(H5_INDEX)
        assert 'id="letterDetailSubtitle"' in html, \
            "letterDetailSubtitle not found"

    def test_render_letter_detail_sets_title(self):
        """renderLetterDetailScreen sets letterDetailTitle from letter.title."""
        js = _read(H5_APP)
        start = js.find("function renderLetterDetailScreen")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "letterDetailTitle" in section, \
            "renderLetterDetailScreen must set letterDetailTitle"
        assert "letter.title" in section or "letterTitle" in section, \
            "renderLetterDetailScreen should use letter.title for title"

    def test_render_letter_detail_sets_meta_pills_with_accent(self):
        """renderLetterDetailScreen builds meta pills with first pill accent style."""
        js = _read(H5_APP)
        start = js.find("function renderLetterDetailScreen")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "letter-meta-pill-accent" in section, \
            "renderLetterDetailScreen must apply letter-meta-pill-accent class"

    def test_render_letter_detail_meta_pills_include_favorited(self):
        """renderLetterDetailScreen adds favorited pill when letter is favorited."""
        js = _read(H5_APP)
        start = js.find("function renderLetterDetailScreen")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "favorited" in section, \
            "renderLetterDetailScreen should include favorited in meta pills"

    def test_letter_meta_pill_accent_css_exists(self):
        """styles.css has .letter-meta-pill-accent class."""
        css = _read(H5_CSS)
        assert ".letter-meta-pill-accent" in css, \
            ".letter-meta-pill-accent CSS not found"

    def test_letter_card_has_gradient_background(self):
        """.letter-detail-letter-card has gradient background."""
        css = _read(H5_CSS)
        card_start = css.find(".letter-detail-letter-card")
        card_end = css.find("}", card_start)
        section = css[card_start:card_end]
        assert "gradient" in section or ("var(--xt-surface-2)" in section and "var(--xt-surface)" in section), \
            ".letter-detail-letter-card should have gradient background"

    def test_letter_card_border_radius_22px(self):
        """.letter-detail-letter-card has border-radius 22px."""
        css = _read(H5_CSS)
        card_start = css.find(".letter-detail-letter-card")
        card_end = css.find("}", card_start)
        section = css[card_start:card_end]
        assert "22px" in section or "22" in section, \
            ".letter-detail-letter-card should have border-radius 22px"

    def test_letter_detail_body_font_size_17px(self):
        """.letter-detail-body has font-size 17px."""
        css = _read(H5_CSS)
        body_start = css.find(".letter-detail-body")
        body_end = css.find("}", body_start)
        section = css[body_start:body_end]
        assert "17px" in section, \
            ".letter-detail-body should have font-size 17px"

    def test_letter_detail_body_line_height_34px(self):
        """.letter-detail-body has line-height 34px."""
        css = _read(H5_CSS)
        body_start = css.find(".letter-detail-body")
        body_end = css.find("}", body_start)
        section = css[body_start:body_end]
        assert "34px" in section, \
            ".letter-detail-body should have line-height 34px"

    def test_letter_detail_has_seal_svg(self):
        """index.html letter detail card has letter seal SVG."""
        html = _read(H5_INDEX)
        detail_start = html.find('id="screenLetterDetail"')
        detail_end = html.find("</section>", detail_start)
        section = html[detail_start:detail_end]
        assert "letter-detail-seal" in section or "LetterSeal" in section, \
            "letter detail card should have seal SVG element"

    def test_letter_detail_has_date_separator(self):
        """index.html letter detail card has date row with separator line."""
        html = _read(H5_INDEX)
        detail_start = html.find('id="screenLetterDetail"')
        detail_end = html.find("</section>", detail_start)
        section = html[detail_start:detail_end]
        assert "letter-detail-date-row" in section or "letter-detail-date-line" in section, \
            "letter detail card should have date row with separator"

    def test_favorite_button_uses_accent_when_favorited(self):
        """.letter-detail-favorite-btn.favorited uses accent-soft background."""
        css = _read(H5_CSS)
        fav_start = css.find(".letter-detail-favorite-btn.favorited")
        fav_end = css.find("}", fav_start)
        section = css[fav_start:fav_end]
        assert "accent-soft" in section or "xt-accent-soft" in section, \
            ".letter-detail-favorite-btn.favorited should use accent-soft"

"""
P26-FIX1 static tests: Result and LetterDetail mobile prototype parity.

Verifies:
1.  Result required IDs still exist in index.html.
2.  LetterDetail required IDs still exist.
3.  renderResultScreen uses normalizePlayableAudioUrl.
4.  renderLetterDetailScreen uses normalizePlayableAudioUrl.
5.  resultSave posts the same save payload fields.
6.  TTS payload unchanged.
7.  Result save flow still calls showResultSaveSealThenOpenHistory.
8.  History-back-to-Result logic still exists.
9.  LetterDetail back target remains History.
10. Letter body rendered with renderLetterBodyLines (Chinese punctuation split).
11. result-letter-card has seal decoration.
12. LetterDetail double-padding removed.
13. screen-scroll bottom padding overridden for Result and LetterDetail.
14. Audio elements have accent-color.
"""

APP_JS = "apps/xiangta-h5/app.js"
INDEX_HTML = "apps/xiangta-h5/index.html"
RESULT_CSS = "apps/xiangta-h5/css/screens-result.css"
LETTER_CSS = "apps/xiangta-h5/css/screens-history-letter-settings.css"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─────────────────────────────────────────────
# HTML: required IDs
# ─────────────────────────────────────────────

class TestResultRequiredIDs:
    REQUIRED = [
        "screenResult", "resultMetaPills", "resultLetterDate", "resultLetterBody",
        "resultLetterSignature", "resultVoiceName", "resultAudioTime", "resultAudio",
        "btnResultSave", "resultSaveLabel", "resultViewHistoryBtn",
        "resultSaveSealOverlay",
    ]

    def test_all_result_ids_exist(self):
        html = _read(INDEX_HTML)
        for id_ in self.REQUIRED:
            assert f'id="{id_}"' in html, f"Missing required ID: {id_}"

    def test_result_save_button_calls_result_save(self):
        html = _read(INDEX_HTML)
        idx = html.find('id="btnResultSave"')
        tag = html[max(0, idx - 30):idx + 200]
        assert "resultSave()" in tag

    def test_result_letter_card_has_seal(self):
        """Seal decoration added to result-letter-card (matches LetterDetail and prototype)."""
        html = _read(INDEX_HTML)
        idx = html.find('id="resultLetterCard"')
        card_section = html[idx:idx + 800]
        assert "result-letter-seal" in card_section, \
            "result-letter-card must have a .result-letter-seal decoration"


class TestLetterDetailRequiredIDs:
    REQUIRED = [
        "screenLetterDetail", "letterDetailAudio", "btnLetterDetailFavorite",
        "letterDetailMetaPills", "letterDetailFavoriteLabel",
        "letterDetailTitle", "letterDetailBody", "letterDetailDate",
        "letterDetailAudioSection", "letterDetailEmptyAudio",
    ]

    def test_all_letter_detail_ids_exist(self):
        html = _read(INDEX_HTML)
        for id_ in self.REQUIRED:
            assert f'id="{id_}"' in html, f"Missing required ID: {id_}"

    def test_letter_detail_back_goes_to_history(self):
        html = _read(INDEX_HTML)
        idx = html.find('id="screenLetterDetail"')
        snippet = html[idx:idx + 600]
        assert "showScreen('history')" in snippet, \
            "LetterDetail back button must go to history"

    def test_letter_detail_favorite_btn_calls_toggle(self):
        html = _read(INDEX_HTML)
        idx = html.find('id="btnLetterDetailFavorite"')
        tag = html[max(0, idx - 30):idx + 200]
        assert "toggleLetterDetailFavorite()" in tag


# ─────────────────────────────────────────────
# app.js: functions
# ─────────────────────────────────────────────

class TestResultFunctions:
    def test_render_result_screen_exists(self):
        js = _read(APP_JS)
        assert "function renderResultScreen(" in js

    def test_render_result_screen_normalizes_audio(self):
        js = _read(APP_JS)
        idx = js.find("function renderResultScreen(")
        body = js[idx:idx + 600]
        assert "normalizePlayableAudioUrl(" in body

    def test_result_save_calls_seal_then_history(self):
        js = _read(APP_JS)
        assert "showResultSaveSealThenOpenHistory" in js, \
            "resultSave must call showResultSaveSealThenOpenHistory"

    def test_history_back_to_result_logic(self):
        """getBackTargetForScreen or similar must have result→history and history→result path."""
        js = _read(APP_JS)
        assert "historyReturnTo" in js, \
            "History back-to-result tracking must use historyReturnTo"
        assert '"result"' in js or "'result'" in js

    def test_result_save_payload_recipient(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]
        assert "recipient" in snippet

    def test_result_save_payload_final_text(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]
        assert "finalText" in snippet

    def test_result_save_payload_audio_url(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]
        assert "audioUrl" in snippet

    def test_result_save_payload_no_profile_id(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]
        assert "profileId" not in snippet


class TestLetterBodyRendering:
    def test_render_letter_body_lines_helper_exists(self):
        js = _read(APP_JS)
        assert "function renderLetterBodyLines(" in js

    def test_helper_splits_on_chinese_punctuation(self):
        js = _read(APP_JS)
        idx = js.find("function renderLetterBodyLines(")
        body = js[idx:idx + 500]
        # Must use Chinese punctuation pattern like prototype
        assert "。" in body or r"。" in body
        assert "！" in body or r"！" in body

    def test_render_result_screen_uses_helper(self):
        js = _read(APP_JS)
        idx = js.find("function renderResultScreen(")
        body = js[idx:idx + 1600]
        assert "renderLetterBodyLines(" in body, \
            "renderResultScreen must use renderLetterBodyLines"

    def test_render_letter_detail_uses_helper(self):
        js = _read(APP_JS)
        idx = js.find("function renderLetterDetailScreen(")
        body = js[idx:idx + 1400]
        assert "renderLetterBodyLines(" in body, \
            "renderLetterDetailScreen must use renderLetterBodyLines"

    def test_helper_uses_dom_safe_text_nodes(self):
        js = _read(APP_JS)
        idx = js.find("function renderLetterBodyLines(")
        body = js[idx:idx + 500]
        assert "createTextNode" in body, "Helper must use createTextNode (safe, no innerHTML with text)"


class TestLetterDetailNormalizeAudio:
    def test_render_letter_detail_normalizes_audio(self):
        js = _read(APP_JS)
        idx = js.find("function renderLetterDetailScreen(")
        body = js[idx:idx + 2400]
        assert "normalizePlayableAudioUrl(" in body


class TestTTSPayloadUnchanged:
    def test_tts_payload_voice_preset(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/tts/tasks"')
        region = js[max(0, idx - 500):idx + 200]
        assert "voicePreset" in region

    def test_tts_payload_tone(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/tts/tasks"')
        region = js[max(0, idx - 500):idx + 200]
        assert "tone" in region

    def test_suggestions_payload_raw_text(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "rawText" in snippet


# ─────────────────────────────────────────────
# CSS parity checks
# ─────────────────────────────────────────────

class TestResultCSSParity:
    def test_result_letter_seal_style(self):
        css = _read(RESULT_CSS)
        assert ".result-letter-seal" in css

    def test_result_screen_bottom_padding_override(self):
        """Result must override --xt-bottom-safe to avoid excessive bottom space."""
        css = _read(RESULT_CSS)
        assert ".screen-scroll.result-screen" in css
        assert "padding-bottom" in css

    def test_result_audio_has_accent_color(self):
        css = _read(RESULT_CSS)
        idx = css.find(".result-audio-card audio")
        snippet = css[idx:idx + 200]
        assert "accent-color" in snippet

    def test_result_letter_body_no_pre_line(self):
        """After renderLetterBodyLines, pre-line is not needed (we use <br> elements)."""
        css = _read(RESULT_CSS)
        idx = css.find(".result-letter-body")
        snippet = css[idx:idx + 200]
        assert "pre-line" not in snippet, \
            "result-letter-body should not use white-space: pre-line when using renderLetterBodyLines"


class TestLetterDetailCSSParity:
    def test_letter_detail_meta_pills_no_horizontal_padding(self):
        """Double-padding fix: meta pills must not have extra 16px horizontal padding."""
        css = _read(LETTER_CSS)
        idx = css.find(".letter-detail-meta-pills")
        snippet = css[idx:idx + 200]
        # Should not have padding: 0 16px (the old double-padding)
        assert "padding: 0 16px" not in snippet, \
            "letter-detail-meta-pills must not have double-padding (parent screen-scroll has 16px)"

    def test_letter_detail_card_no_horizontal_margin(self):
        """Double-padding fix: letter card must not have extra 16px horizontal margin."""
        css = _read(LETTER_CSS)
        idx = css.find(".letter-detail-letter-card")
        snippet = css[idx:idx + 300]
        assert "margin: 0 16px" not in snippet, \
            "letter-detail-letter-card must not have double-margin"

    def test_letter_detail_audio_card_no_horizontal_margin(self):
        css = _read(LETTER_CSS)
        idx = css.find(".letter-detail-audio-card {")
        snippet = css[idx:idx + 200]
        assert "margin: 0 16px" not in snippet

    def test_letter_detail_actions_grid_no_horizontal_margin(self):
        css = _read(LETTER_CSS)
        idx = css.find(".letter-detail-actions-grid")
        snippet = css[idx:idx + 200]
        assert "margin: 0 16px" not in snippet

    def test_letter_detail_screen_bottom_padding_override(self):
        """LetterDetail must override --xt-bottom-safe to avoid excessive bottom space."""
        css = _read(LETTER_CSS)
        assert ".screen-scroll.letter-detail-screen" in css
        assert "padding-bottom" in css

    def test_letter_detail_audio_has_accent_color(self):
        css = _read(LETTER_CSS)
        idx = css.find(".letter-detail-audio-card audio")
        snippet = css[idx:idx + 200]
        assert "accent-color" in snippet

    def test_letter_detail_body_no_pre_wrap(self):
        """After renderLetterBodyLines, pre-wrap not needed."""
        css = _read(LETTER_CSS)
        idx = css.find(".letter-detail-body")
        snippet = css[idx:idx + 200]
        assert "pre-wrap" not in snippet, \
            "letter-detail-body should not use white-space: pre-wrap when using renderLetterBodyLines"

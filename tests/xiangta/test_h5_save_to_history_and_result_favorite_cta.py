"""P25H: H5 save to history and result favorite CTA — targeted test."""
import re
import os

APP_JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "app.js"
)
INDEX_HTML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "index.html"
)


def read_app_js():
    with open(APP_JS_PATH, encoding="utf-8") as f:
        return f.read()


def read_index_html():
    with open(INDEX_HTML_PATH, encoding="utf-8") as f:
        return f.read()


def get_result_save_body(content):
    match = re.search(
        r'async function resultSave\(\).*?(?=\n(?:async function|function \w|\Z))',
        content,
        re.DOTALL,
    )
    assert match, "resultSave not found"
    return match.group(0)


def get_function_body(content, func_name):
    match = re.search(
        r'function ' + func_name + r'\(.*?\n\}',
        content,
        re.DOTALL,
    )
    assert match, func_name + " not found"
    return match.group(0)


class TestSaveToHistory:
    """Verify Result save opens History, not LetterDetail."""

    def test_save_animation_no_longer_opens_letterDetail(self):
        content = read_app_js()
        func_body = get_function_body(content, "showResultSaveSealThenOpenHistory")
        assert "letterDetail" not in func_body, (
            "showResultSaveSealThenOpenHistory must not reference letterDetail"
        )

    def test_save_animation_sets_historyReturnTo_result(self):
        content = read_app_js()
        func_body = get_function_body(content, "showResultSaveSealThenOpenHistory")
        assert 'historyReturnTo = "result"' in func_body, (
            "showResultSaveSealThenOpenHistory must set historyReturnTo = \"result\""
        )

    def test_save_animation_opens_history_screen(self):
        content = read_app_js()
        func_body = get_function_body(content, "showResultSaveSealThenOpenHistory")
        assert 'showScreen("history")' in func_body, (
            "showResultSaveSealThenOpenHistory must call showScreen(\"history\")"
        )

    def test_resultSave_calls_showResultSaveSealThenOpenHistory(self):
        content = read_app_js()
        body = get_result_save_body(content)
        assert "showResultSaveSealThenOpenHistory(savedLetter)" in body, (
            "resultSave must call showResultSaveSealThenOpenHistory(savedLetter)"
        )


class TestHistoryBackNavigation:
    """Verify History back returns to correct screen."""

    def test_history_screen_back_uses_handleHistoryBack(self):
        html = read_index_html()
        # screenHistory back button must use handleHistoryBack, not showScreen('home')
        # Find the History screen section
        hist_match = re.search(
            r'<section id="screenHistory".*?</section>',
            html,
            re.DOTALL,
        )
        assert hist_match, "screenHistory not found"
        hist_section = hist_match.group(0)
        # The back button with "返回首页" or "返回" in History header
        back_btn_match = re.search(
            r'<button[^>]+aria-label="[^"]*返回[^"]*"[^>]*onclick="([^"]+)"',
            hist_section,
        )
        assert back_btn_match, "History back button not found"
        onclick = back_btn_match.group(1)
        assert onclick == "handleHistoryBack()", (
            f"History back button must use handleHistoryBack(), got: {onclick}"
        )

    def test_letterDetail_back_does_NOT_use_handleHistoryBack(self):
        html = read_index_html()
        # screenLetterDetail back button must NOT use handleHistoryBack
        letter_match = re.search(
            r'<section id="screenLetterDetail".*?</section>',
            html,
            re.DOTALL,
        )
        assert letter_match, "screenLetterDetail not found"
        letter_section = letter_match.group(0)
        back_btn_match = re.search(
            r'<button[^>]+aria-label="[^"]*返回[^"]*"[^>]*onclick="([^"]+)"',
            letter_section,
        )
        assert back_btn_match, "LetterDetail back button not found"
        onclick = back_btn_match.group(1)
        assert "handleHistoryBack" not in onclick, (
            f"LetterDetail back button must NOT use handleHistoryBack(), got: {onclick}"
        )

    def test_handleHistoryBack_returns_to_result_when_historyReturnTo_is_result(self):
        content = read_app_js()
        body = get_function_body(content, "handleHistoryBack")
        assert 'historyReturnTo === "result"' in body, (
            "handleHistoryBack must check historyReturnTo === \"result\""
        )
        assert 'showScreen("result")' in body, (
            "handleHistoryBack must showScreen(\"result\") when returning to result"
        )

    def test_handleHistoryBack_defaults_to_home(self):
        content = read_app_js()
        body = get_function_body(content, "handleHistoryBack")
        assert 'showScreen("home")' in body, (
            "handleHistoryBack must showScreen(\"home\") as default"
        )


class TestResultFavoriteCTA:
    """Verify Result post-save CTA shows 收藏 / 已收藏."""

    def test_result_saved_state_shows_collect_cta(self):
        content = read_app_js()
        body = get_function_body(content, "updateResultSaveButton")
        assert "加入收藏" in body, (
            "updateResultSaveButton must show 加入收藏 when saved but not favorited"
        )
        assert "已收藏" in body, (
            "updateResultSaveButton must show 已收藏 when saved and favorited"
        )

    def test_result_save_stores_resultFavorited_state(self):
        content = read_app_js()
        body = get_result_save_body(content)
        assert "state.resultSavedLetterId" in body, (
            "resultSave must set state.resultSavedLetterId"
        )
        assert "state.resultFavorited" in body, (
            "resultSave must set state.resultFavorited"
        )


class TestSavedLetterDeclarationOrder:
    """Verify savedLetter is declared before use."""

    def test_savedLetter_declared_before_used_in_resultSave(self):
        content = read_app_js()
        body = get_result_save_body(content)
        # Find position of const savedLetter
        const_match = re.search(
            r'const\s+savedLetter\s*=\s*buildSavedLetterViewModel',
            body,
        )
        assert const_match, "const savedLetter declaration not found"
        const_pos = const_match.start()

        # Find position of first state.resultSavedLetterId usage
        usage_match = re.search(
            r'state\.resultSavedLetterId\s*=',
            body,
        )
        assert usage_match, "state.resultSavedLetterId usage not found"
        usage_pos = usage_match.start()

        assert const_pos < usage_pos, (
            f"const savedLetter (pos {const_pos}) must appear before "
            f"state.resultSavedLetterId (pos {usage_pos})"
        )


class TestPreservedBehavior:
    """Verify P25E/P25G fixes are preserved."""

    def test_resultSave_still_uses_setResultSaveBusy(self):
        content = read_app_js()
        body = get_result_save_body(content)
        assert "setResultSaveBusy(true" in body, (
            "resultSave must still use setResultSaveBusy for busy state"
        )

    def test_resultSave_timeoutMs_still_12000(self):
        content = read_app_js()
        body = get_result_save_body(content)
        timeout_match = re.search(r'timeoutMs\s*:\s*(\d+)', body)
        assert timeout_match
        assert timeout_match.group(1) == "12000", (
            "timeoutMs must remain 12000"
        )

    def test_save_payload_unchanged(self):
        content = read_app_js()
        body = get_result_save_body(content)
        required_keys = [
            "recipient", "scene", "style", "rawText", "finalText",
            "voicePreset", "tone", "audioUrl", "durationSecs", "title"
        ]
        for key in required_keys:
            assert key in body, f"Payload missing key: {key}"

    def test_tts_payload_unchanged(self):
        content = read_app_js()
        func_match = re.search(
            r'async function generateTts\(\).*?(?=\n(?:async function|function \w|\Z))',
            content,
            re.DOTALL,
        )
        assert func_match
        body = func_match.group(0)
        tts_keys = ["text", "voicePreset", "tone", "recipient", "scene"]
        for key in tts_keys:
            assert key in body, f"TTS payload missing key: {key}"

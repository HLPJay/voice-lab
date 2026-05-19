"""P25H: H5 save to history and result favorite CTA — minimal targeted test."""
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


class TestSaveToHistory:
    """Verify Result save opens History, not LetterDetail."""

    def test_save_animation_no_longer_opens_letterDetail(self):
        content = read_app_js()
        func_match = re.search(
            r'function showResultSaveSealThenOpenHistory\(',
            content,
        )
        assert func_match, "showResultSaveSealThenOpenHistory not found"
        # Find the full function
        full_match = re.search(
            r'function showResultSaveSealThenOpenHistory\(.*?\n\}',
            content,
            re.DOTALL,
        )
        assert full_match
        func_body = full_match.group(0)
        assert "letterDetail" not in func_body, (
            "showResultSaveSealThenOpenHistory must not reference letterDetail"
        )

    def test_save_animation_sets_historyReturnTo_result(self):
        content = read_app_js()
        full_match = re.search(
            r'function showResultSaveSealThenOpenHistory\(.*?\n\}',
            content,
            re.DOTALL,
        )
        assert full_match
        func_body = full_match.group(0)
        assert 'historyReturnTo = "result"' in func_body, (
            "showResultSaveSealThenOpenHistory must set historyReturnTo = \"result\""
        )

    def test_save_animation_opens_history_screen(self):
        content = read_app_js()
        full_match = re.search(
            r'function showResultSaveSealThenOpenHistory\(.*?\n\}',
            content,
            re.DOTALL,
        )
        assert full_match
        func_body = full_match.group(0)
        assert 'showScreen("history")' in func_body, (
            "showResultSaveSealThenOpenHistory must call showScreen(\"history\")"
        )

    def test_resultSave_calls_showResultSaveSealThenOpenHistory(self):
        content = read_app_js()
        body = get_result_save_body(content)
        assert "showResultSaveSealThenOpenHistory" in body, (
            "resultSave must call showResultSaveSealThenOpenHistory"
        )


class TestHistoryBackNavigation:
    """Verify History back returns to correct screen."""

    def test_history_back_uses_handleHistoryBack(self):
        html = read_index_html()
        # History back button must use handleHistoryBack, not showScreen('home')
        assert "handleHistoryBack" in html, (
            "History back button must use handleHistoryBack"
        )
        # Should not have old direct showScreen('history') for back navigation
        # (there may still be showScreen('history') for other purposes)

    def test_handleHistoryBack_returns_to_result_when_historyReturnTo_is_result(self):
        content = read_app_js()
        match = re.search(
            r'function handleHistoryBack\(\).*?\n\}',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        assert 'historyReturnTo === "result"' in body, (
            "handleHistoryBack must check historyReturnTo === \"result\""
        )
        assert "showScreen(\"result\")" in body, (
            "handleHistoryBack must showScreen(\"result\") when returning to result"
        )

    def test_handleHistoryBack_defaults_to_home(self):
        content = read_app_js()
        match = re.search(
            r'function handleHistoryBack\(\).*?\n\}',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        assert 'showScreen("home")' in body, (
            "handleHistoryBack must showScreen(\"home\") as default"
        )


class TestResultFavoriteCTA:
    """Verify Result post-save CTA shows 收藏 / 已收藏."""

    def test_result_saved_state_shows_collect_cta(self):
        content = read_app_js()
        match = re.search(
            r'function updateResultSaveButton\(\).*?\n\}',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
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

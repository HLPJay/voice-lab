"""P25H: H5 History favorite and playback — frontend targeted test."""
import re
import os

APP_JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "app.js"
)
STATE_JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "js", "state.js"
)


def read_app_js():
    with open(APP_JS_PATH, encoding="utf-8") as f:
        return f.read()


def read_state_js():
    with open(STATE_JS_PATH, encoding="utf-8") as f:
        return f.read()


def get_function_body(content, func_name):
    match = re.search(
        r'function ' + func_name + r'\(.*?\n\}',
        content,
        re.DOTALL,
    )
    assert match, f"{func_name} not found"
    return match.group(0)


class TestMiniPlayerFix:
    """Verify setupHistoryMiniPlayer ReferenceError is fixed."""

    def test_renderLetters_no_longer_calls_setupHistoryMiniPlayer(self):
        content = read_app_js()
        match = re.search(
            r'function renderLetters\(\).*?\n\}',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        assert "setupHistoryMiniPlayer" not in body, (
            "renderLetters must not call setupHistoryMiniPlayer"
        )

    def test_renderLetters_does_not_auto_play_first_audio(self):
        content = read_app_js()
        match = re.search(
            r'function renderLetters\(\).*?\n\}',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        # Must not find any .play() call in renderLetters
        assert "audio.play()" not in body, (
            "renderLetters must not auto-play audio"
        )

    def test_renderLetters_shows_active_mini_player_only(self):
        content = read_app_js()
        match = re.search(
            r'function renderLetters\(\).*?\n\}',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        # Must use activeHistoryLetterId to determine which letter to show
        assert "activeHistoryLetterId" in body, (
            "renderLetters must check activeHistoryLetterId for mini player"
        )

    def test_historyAudioListenersBound_in_state(self):
        content = read_state_js()
        assert "historyAudioListenersBound" in content, (
            "state.js must have historyAudioListenersBound field"
        )


class TestAudioListenersFix:
    """Verify audio listeners are bound once without cloning."""

    def test_setupHistoryAudioListeners_does_not_clone_node(self):
        content = read_app_js()
        body = get_function_body(content, "setupHistoryAudioListeners")
        assert "cloneNode" not in body, (
            "setupHistoryAudioListeners must not clone audio node"
        )
        assert "replaceChild" not in body, (
            "setupHistoryAudioListeners must not replace audio node"
        )

    def test_setupHistoryAudioListeners_binds_once_guard(self):
        content = read_app_js()
        body = get_function_body(content, "setupHistoryAudioListeners")
        assert "historyAudioListenersBound" in body, (
            "setupHistoryAudioListeners must check historyAudioListenersBound"
        )
        assert "state.historyAudioListenersBound = true" in body, (
            "setupHistoryAudioListeners must set historyAudioListenersBound = true after binding"
        )

    def test_playHistoryLetter_calls_renderHistoryMiniPlayer(self):
        content = read_app_js()
        body = get_function_body(content, "playHistoryLetter")
        assert "renderHistoryMiniPlayer" in body, (
            "playHistoryLetter must call renderHistoryMiniPlayer"
        )


class TestFavoriteAPICalls:
    """Verify favorite toggles call the backend API."""

    def test_toggleResultFavorite_calls_patch_api(self):
        content = read_app_js()
        body = get_function_body(content, "toggleResultFavorite")
        assert "/letters/" in body, (
            "toggleResultFavorite must call /letters/ endpoint"
        )
        assert 'method:' in body, (
            "toggleResultFavorite must use method: 'PATCH'"
        )
        assert "favorite" in body.lower(), (
            "toggleResultFavorite must send favorited in body"
        )

    def test_toggleLetterDetailFavorite_calls_patch_api(self):
        content = read_app_js()
        body = get_function_body(content, "toggleLetterDetailFavorite")
        assert "/letters/" in body, (
            "toggleLetterDetailFavorite must call /letters/ endpoint"
        )
        assert "favorite" in body.lower(), (
            "toggleLetterDetailFavorite must send favorited in body"
        )


class TestP25HPreverved:
    """Verify P25H-FIX1 routing behavior is preserved."""

    def test_showResultSaveSealThenOpenHistory_still_exists(self):
        content = read_app_js()
        assert "showResultSaveSealThenOpenHistory" in content, (
            "showResultSaveSealThenOpenHistory must still exist"
        )

    def test_resultSave_timeoutMs_still_12000(self):
        content = read_app_js()
        match = re.search(
            r'async function resultSave\(\).*?(?=\n(?:async function|function \w|\Z))',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        timeout_match = re.search(r'timeoutMs\s*:\s*(\d+)', body)
        assert timeout_match
        assert timeout_match.group(1) == "12000", (
            "timeoutMs must remain 12000"
        )

    def test_save_payload_unchanged(self):
        content = read_app_js()
        match = re.search(
            r'async function resultSave\(\).*?(?=\n(?:async function|function \w|\Z))',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        for key in ["recipient", "scene", "style", "rawText", "finalText",
                     "voicePreset", "tone", "audioUrl", "durationSecs", "title"]:
            assert key in body, f"Payload missing key: {key}"

    def test_tts_payload_unchanged(self):
        content = read_app_js()
        match = re.search(
            r'async function generateTts\(\).*?(?=\n(?:async function|function \w|\Z))',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        for key in ["text", "voicePreset", "tone", "recipient", "scene"]:
            assert key in body, f"TTS payload missing key: {key}"

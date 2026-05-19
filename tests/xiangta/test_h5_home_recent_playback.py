"""P25M: Home recent card playback interaction checks."""
import os
import re


APP_JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "app.js"
)


def read_app_js():
    with open(APP_JS_PATH, encoding="utf-8") as f:
        return f.read()


def get_function_body(content, name):
    match = re.search(
        r"(?:async\s+)?function\s+" + re.escape(name) + r"\(.*?(?=\n(?:async\s+function|function\s+\w|\Z))",
        content,
        re.DOTALL,
    )
    assert match, f"{name} not found"
    return match.group(0)


def test_render_home_recent_has_clickable_play_control():
    body = get_function_body(read_app_js(), "renderHomeRecentLetter")
    assert 'class="home-recent-icon' in body
    assert 'type="button"' in body
    assert "state.homeRecentAudioPlaying" in body
    assert "state.homeRecentLetterId" in body
    assert "pause-recent-letter" in body
    assert "play-recent-letter" in body
    assert "<rect x=\"3\" y=\"2\" width=\"3\" height=\"10\"" in body


def test_play_control_click_stops_propagation_and_calls_player():
    body = get_function_body(read_app_js(), "renderHomeRecentLetter")
    assert "event.stopPropagation();" in body
    assert "playHomeRecentLetter(recent);" in body


def test_card_body_still_opens_history():
    body = get_function_body(read_app_js(), "renderHomeRecentLetter")
    assert 'onclick="openHistoryFromHome()"' in body


def test_play_home_recent_uses_audio_url_and_no_audio_toast():
    body = get_function_body(read_app_js(), "playHomeRecentLetter")
    assert "if (!letter || !letter.audioUrl)" in body
    assert "showToast(" in body
    assert "audio.src = letter.audioUrl;" in body


def test_leaving_home_pauses_recent_audio():
    cleanup = get_function_body(read_app_js(), "cleanupBeforeScreenChange")
    assert 'fromScreen === "home" && toScreen !== "home"' in cleanup
    assert "pauseHomeRecentAudio();" in cleanup

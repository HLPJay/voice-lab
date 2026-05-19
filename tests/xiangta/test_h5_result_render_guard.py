"""
Tiny structural checks for P25F result render guard.
"""

H5_APP = "apps/xiangta-h5/app.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fn_body(js: str, signature: str, window: int = 2800) -> str:
    idx = js.find(signature)
    assert idx >= 0, f"{signature} not found"
    return js[idx:idx + window]


def test_show_screen_result_no_unsafe_render_without_arg():
    js = _read(H5_APP)
    body = _fn_body(js, "function showScreen(screen)", window=2000)
    assert "if (screen === \"result\")" in body
    assert "renderResultScreen();" not in body
    assert "renderResultScreen(state.ttsResult);" in body


def test_render_tts_success_still_renders_and_enters_result():
    js = _read(H5_APP)
    body = _fn_body(js, "function renderTtsTask(result)", window=2200)
    assert "renderResultScreen(result);" in body
    assert "showScreen(\"result\");" in body


def test_tts_payload_unchanged_and_result_save_timeout_kept():
    js = _read(H5_APP)
    tts_body = _fn_body(js, "async function generateTtsTask()", window=2600)
    assert "text: text," in tts_body
    assert "voicePreset: state.selectedVoice," in tts_body
    assert "tone: state.selectedTone," in tts_body
    assert "recipient: state.selectedRecipient," in tts_body
    assert "scene: state.selectedScene," in tts_body
    save_body = _fn_body(js, "async function resultSave()", window=3600)
    assert "timeoutMs: 12000" in save_body

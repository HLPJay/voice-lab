"""
Hotfix tests for Voice transient UI state reset on retone flows.
"""

H5_APP = "apps/xiangta-h5/app.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fn_body(js: str, signature: str, window: int = 2200) -> str:
    idx = js.find(signature)
    assert idx >= 0, f"{signature} not found"
    return js[idx:idx + window]


class TestVoiceTransientReset:
    def test_reset_helper_exists(self):
        js = _read(H5_APP)
        assert "function resetVoiceTransientUi()" in js

    def test_reset_helper_resets_busy_label(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function resetVoiceTransientUi()")
        assert 'setBusy("btnGenTtsTask", false, "生成语音")' in body

    def test_reset_helper_hides_tts_result(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function resetVoiceTransientUi()")
        assert 'const ttsResult = el("ttsResult")' in body
        assert 'ttsResult.classList.add("hidden")' in body

    def test_reset_helper_hides_save_letter_section(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function resetVoiceTransientUi()")
        assert 'const saveSection = el("saveLetterSection")' in body
        assert 'saveSection.classList.add("hidden")' in body

    def test_go_voice_calls_reset_helper(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function goVoice()")
        assert "resetVoiceTransientUi();" in body

    def test_result_change_tone_calls_reset_helper(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function resultChangeTone()")
        assert "resetVoiceTransientUi();" in body

    def test_result_change_tone_still_navigates_voice(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function resultChangeTone()")
        assert 'showScreen("voice");' in body

    def test_result_change_tone_does_not_clear_final_text(self):
        js = _read(H5_APP)
        body = _fn_body(js, "function resultChangeTone()", window=300)
        assert "state.finalText" not in body

    def test_generate_tts_task_payload_unchanged(self):
        js = _read(H5_APP)
        body = _fn_body(js, "async function generateTtsTask()", window=2600)
        assert "const payload = {" in body
        assert "text: text," in body
        assert "voicePreset: state.selectedVoice," in body
        assert "tone: state.selectedTone," in body
        assert "recipient: state.selectedRecipient," in body
        assert "scene: state.selectedScene," in body

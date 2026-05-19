"""
Focused structural checks for P25E return-path/transient-state fixes.
"""

H5_APP = "apps/xiangta-h5/app.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _fn_body(js: str, signature: str, window: int = 3600) -> str:
    idx = js.find(signature)
    assert idx >= 0, f"{signature} not found"
    return js[idx:idx + window]


def test_result_save_has_timeout_and_restores_button_on_null():
    js = _read(H5_APP)
    body = _fn_body(js, "async function resultSave()", window=4200)
    assert 'apiFetch("/api/xiangta/letters"' in body
    assert "timeoutMs: 12000" in body
    assert "timeoutMessage:" in body
    assert 'setBusy("btnResultSave", false' in body


def test_result_back_and_change_tone_use_fresh_voice_return():
    js = _read(H5_APP)
    assert "function returnToVoiceFresh()" in js
    back = _fn_body(js, "function resultGoBack()", window=260)
    tone = _fn_body(js, "function resultChangeTone()", window=360)
    assert "returnToVoiceFresh();" in back
    assert "returnToVoiceFresh();" in tone


def test_saved_letter_is_not_auto_favorited():
    js = _read(H5_APP)
    build_body = _fn_body(js, "function buildSavedLetterViewModel(responseData)", window=2200)
    assert "favorited: !!src.favorited" in build_body
    seal_body = _fn_body(js, "function showResultSaveSealThenOpenDetail(letter)", window=2600)
    assert "letterDetailFavoritedMap[letter.id || letter.letterId] = !!letter.favorited;" in seal_body
    assert "letterDetailFavoritedMap[letter.id || letter.letterId] = true;" not in seal_body


def test_show_screen_cleanup_pauses_audio():
    js = _read(H5_APP)
    body = _fn_body(js, "function cleanupBeforeScreenChange(fromScreen, toScreen)", window=2400)
    assert 'fromScreen === "result"' in body and "resultAudio" in body and ".pause()" in body
    assert 'fromScreen === "history"' in body and "historyAudio" in body and "hideHistoryMiniPlayer()" in body
    assert 'fromScreen === "letterDetail"' in body and "letterDetailAudio" in body and ".pause()" in body


def test_poll_uses_token_guard_and_tts_payload_unchanged():
    js = _read(H5_APP)
    poll = _fn_body(js, "async function pollTtsTask(task, token)", window=2600)
    assert "if (token !== state.ttsPollToken) return;" in poll
    tts = _fn_body(js, "async function generateTtsTask()", window=3200)
    assert "const token = ++state.ttsPollToken;" in tts
    assert "text: text," in tts
    assert "voicePreset: state.selectedVoice," in tts
    assert "tone: state.selectedTone," in tts
    assert "recipient: state.selectedRecipient," in tts
    assert "scene: state.selectedScene," in tts

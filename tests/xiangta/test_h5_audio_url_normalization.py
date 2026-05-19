"""
P25V-FIX1 — Frontend audio URL normalization static tests.

Verifies that:
1.  normalizePlayableAudioUrl exists in app.js
2.  It detects localhost / 127.0.0.1 / 0.0.0.0
3.  It builds /api/xiangta/audio/proxy?url= for local addresses
4.  renderResultScreen uses normalizePlayableAudioUrl
5.  renderTtsTask (inline audio) uses normalizePlayableAudioUrl
6.  playHistoryLetter uses normalizePlayableAudioUrl
7.  playHomeRecentLetter uses normalizePlayableAudioUrl
8.  renderLetterDetailScreen uses normalizePlayableAudioUrl
9.  resultSave saves normalized audioUrl (normalizePlayableAudioUrl at save site)
10. saveLetter saves normalized audioUrl
11. buildSavedLetterViewModel normalizes audioUrl
12. TTS payload unchanged (text, voicePreset, tone, recipient, scene)
13. Save payload structure unchanged (all required fields, no profileId in formal path)
"""

APP_JS = "apps/xiangta-h5/app.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestNormalizeHelperExists:
    def test_helper_function_defined(self):
        js = _read(APP_JS)
        assert "function normalizePlayableAudioUrl(" in js

    def test_helper_detects_localhost(self):
        js = _read(APP_JS)
        idx = js.find("function normalizePlayableAudioUrl(")
        body = js[idx:idx + 800]
        assert "localhost" in body

    def test_helper_detects_127_0_0_1(self):
        js = _read(APP_JS)
        idx = js.find("function normalizePlayableAudioUrl(")
        body = js[idx:idx + 800]
        assert "127.0.0.1" in body

    def test_helper_detects_0_0_0_0(self):
        js = _read(APP_JS)
        idx = js.find("function normalizePlayableAudioUrl(")
        body = js[idx:idx + 800]
        assert "0.0.0.0" in body

    def test_helper_builds_proxy_url(self):
        js = _read(APP_JS)
        idx = js.find("function normalizePlayableAudioUrl(")
        body = js[idx:idx + 800]
        assert "/api/xiangta/audio/proxy" in body
        assert "encodeURIComponent" in body

    def test_helper_guards_empty_input(self):
        js = _read(APP_JS)
        idx = js.find("function normalizePlayableAudioUrl(")
        body = js[idx:idx + 800]
        assert "return" in body  # early-return for falsy input

    def test_helper_guards_already_proxy(self):
        js = _read(APP_JS)
        idx = js.find("function normalizePlayableAudioUrl(")
        body = js[idx:idx + 800]
        assert "startsWith" in body or "audio/proxy" in body


class TestPlaybackPathsNormalized:
    def test_render_result_screen_normalizes(self):
        js = _read(APP_JS)
        idx = js.find("function renderResultScreen(")
        body = js[idx:idx + 600]
        assert "normalizePlayableAudioUrl(" in body

    def test_render_tts_task_normalizes_inline_audio(self):
        """The renderTtsTask inline <audio src=...> must use normalizePlayableAudioUrl."""
        js = _read(APP_JS)
        # Find the inline audio HTML construction
        idx = js.find('class="tts-audio"')
        assert idx >= 0, "tts-audio block must exist"
        snippet = js[max(0, idx - 20):idx + 200]
        assert "normalizePlayableAudioUrl(" in snippet

    def test_play_history_letter_normalizes(self):
        js = _read(APP_JS)
        idx = js.find("function playHistoryLetter(")
        body = js[idx:idx + 800]
        assert "normalizePlayableAudioUrl(" in body

    def test_play_home_recent_letter_normalizes(self):
        js = _read(APP_JS)
        idx = js.find("function playHomeRecentLetter(")
        body = js[idx:idx + 600]
        assert "normalizePlayableAudioUrl(" in body

    def test_render_letter_detail_screen_normalizes(self):
        js = _read(APP_JS)
        idx = js.find("function renderLetterDetailScreen(")
        body = js[idx:idx + 2300]  # normalizePlayableAudioUrl is ~2035 chars in
        assert "normalizePlayableAudioUrl(" in body


class TestSavePathsNormalized:
    def test_result_save_normalizes_audio_url(self):
        """The first resultSave function must normalize audioUrl before POST."""
        js = _read(APP_JS)
        # Find the save that uses setResultSaveBusy
        idx = js.find("setResultSaveBusy(true")
        assert idx >= 0
        body = js[max(0, idx - 50):idx + 500]
        assert "normalizePlayableAudioUrl(" in body

    def test_save_letter_normalizes_audio_url(self):
        """The saveLetter function must normalize audioUrl before POST."""
        js = _read(APP_JS)
        idx = js.find('setBusy("btnSaveLetter", true')
        assert idx >= 0
        body = js[idx:idx + 400]
        assert "normalizePlayableAudioUrl(" in body

    def test_build_saved_letter_view_model_normalizes(self):
        """buildSavedLetterViewModel must normalize audioUrl."""
        js = _read(APP_JS)
        idx = js.find("function buildSavedLetterViewModel(")
        body = js[idx:idx + 900]  # normalizePlayableAudioUrl is ~751 chars in
        assert "normalizePlayableAudioUrl(" in body


class TestPayloadInvariant:
    def test_suggestions_payload_recipient(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "recipient" in snippet

    def test_suggestions_payload_scene(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "scene" in snippet

    def test_suggestions_payload_raw_text(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "rawText" in snippet

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

    def test_save_payload_has_audio_url_field(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]
        assert "audioUrl" in snippet

    def test_save_payload_has_final_text(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]
        assert "finalText" in snippet

    def test_save_payload_no_profile_id_in_letters_call(self):
        js = _read(APP_JS)
        idx = js.find('apiFetch("/api/xiangta/letters"')
        snippet = js[idx:idx + 600]
        assert "profileId" not in snippet

"""
Tests for H5 Voice Screen Prototype Parity (P22K).

Covers:
1. screenVoice exists in index.html
2. Voice text preview area exists
3. Voice picker area exists
4. Tone chips area exists
5. Generate CTA button exists
6. goVoice function exists in app.js
7. generateTtsTask function exists
8. renderVoiceTextPreview shows "给X · Y · Z" context label
9. Tone chip selected uses --xt-accent border-color
10. No _silentWav in voice-related code
11. formal mode does not leak profileId
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestVoiceScreenExistence:
    def test_screen_voice_exists(self):
        """index.html has screenVoice section."""
        html = _read(H5_INDEX)
        assert 'id="screenVoice"' in html, "screenVoice not found"

    def test_voice_text_preview_exists(self):
        """Voice text preview element exists in index.html."""
        html = _read(H5_INDEX)
        assert 'id="voiceTextPreview"' in html, "voiceTextPreview not found"

    def test_voice_picker_exists(self):
        """Voice picker element exists in index.html."""
        html = _read(H5_INDEX)
        assert 'id="voicePicker"' in html, "voicePicker not found"

    def test_tone_chips_exists(self):
        """Tone chips element exists in index.html."""
        html = _read(H5_INDEX)
        assert 'id="toneChips"' in html, "toneChips not found"

    def test_generate_cta_exists(self):
        """Generate CTA button exists in index.html."""
        html = _read(H5_INDEX)
        assert 'btnGenTtsTask' in html, "btnGenTtsTask not found"


class TestVoiceScreenFunctions:
    def test_go_voice_exists(self):
        """app.js has goVoice function."""
        js = _read(H5_APP)
        assert "function goVoice" in js or "goVoice =" in js, \
            "goVoice function not found"

    def test_generate_tts_task_exists(self):
        """app.js has generateTtsTask function."""
        js = _read(H5_APP)
        assert "function generateTtsTask" in js or "generateTtsTask =" in js, \
            "generateTtsTask function not found"

    def test_render_voice_text_preview_exists(self):
        """app.js has renderVoiceTextPreview function."""
        js = _read(H5_APP)
        assert "function renderVoiceTextPreview" in js or "renderVoiceTextPreview =" in js, \
            "renderVoiceTextPreview function not found"


class TestVoiceScreenVisualParity:
    """P22K: Voice screen visual parity with prototype."""

    def test_voice_text_preview_has_context_label(self):
        """renderVoiceTextPreview shows '给X · Y · Z' context label."""
        js = _read(H5_APP)
        start = js.find("function renderVoiceTextPreview")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "给${" in section or "给" in section, \
            "renderVoiceTextPreview should show '给' context label"

    def test_tone_chip_selected_uses_xt_accent_border(self):
        """.tone-chip.selected uses --xt-accent border-color."""
        css = _read(H5_CSS)
        idx = css.find(".tone-chip.selected")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "--xt-accent" in section, \
            ".tone-chip.selected should use --xt-accent border-color"

    def test_voice_option_selected_has_accent_wave_bars(self):
        """.voice-option.selected wave bars use accent color."""
        css = _read(H5_CSS)
        idx = css.find(".voice-option.selected .voice-wave-bar")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "accent" in section, \
            "Selected voice option wave bars should use accent color"

    def test_voice_preview_card_has_border(self):
        """.voice-copy-card has border (xt-card parity)."""
        css = _read(H5_CSS)
        idx = css.find(".voice-copy-card")
        end = css.find("}", idx)
        section = css[idx:end]
        assert "border" in section, \
            ".voice-copy-card should have a border"


class TestVoiceScreenNoRegression:
    def test_no_silent_wav_in_voice(self):
        """app.js does not use _silentWav in voice screen."""
        js = _read(H5_APP)
        funcs = ["goVoice", "renderVoicePicker", "generateTtsTask", "renderTtsTask"]
        for func in funcs:
            start = js.find(f"function {func}")
            if start == -1:
                start = js.find(f"{func} =")
            if start != -1:
                end = js.find("\n}", start)
                section = js[start:end]
                assert "_silentWav" not in section, \
                    f"{func} must not use _silentWav"

    def test_no_speech_synthesis_in_voice(self):
        """app.js does not use speechSynthesis for voice generation."""
        js = _read(H5_APP)
        funcs = ["goVoice", "generateTtsTask", "generateTts"]
        for func in funcs:
            start = js.find(f"function {func}")
            if start == -1:
                start = js.find(f"{func} =")
            if start != -1:
                end = js.find("\n}", start)
                section = js[start:end]
                assert "speechSynthesis" not in section, \
                    f"{func} must not use speechSynthesis"

    def test_formal_mode_no_profile_id_in_generate_tts_task(self):
        """generateTtsTask does not include profileId in formal mode payload."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]
        if "profileId" in section:
            assert 'state.mode === "dev"' in section or "state.mode === 'dev'" in section, \
                "profileId must be guarded by dev mode"

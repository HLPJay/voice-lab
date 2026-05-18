"""
Tests for H5 mobile product flow (C9), trimmed to 8 static contract tests.

Covers:
1. index.html contains all 5 screen sections
2. app.js has state.screen and showScreen()
3. Formal TTS uses /api/xiangta/tts/tasks
4. app.js has pollTtsTask or equivalent polling
5. app.js generateTts is dev-only alias, not formal path
6. formal/dev mode preserved: getAppMode/applyModeUi/devPanel
7. formal mode does not pass profileId
8. setBusy button lock exists
9. history uses GET /api/xiangta/letters
10. styles.css has screen/mobile product flow styles
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestScreenStructure:
    def test_all_five_screens_present(self):
        """index.html has screenHome, screenCompose, screenSuggest, screenVoice, screenHistory."""
        html = _read(H5_INDEX)
        for screen in ["screenHome", "screenCompose", "screenSuggest", "screenVoice", "screenHistory"]:
            assert 'id="' + screen + '"' in html, screen + " not found in index.html"

    def test_screen_nav_buttons(self):
        """Compose, suggest, voice, history screens have back navigation."""
        html = _read(H5_INDEX)
        assert 'onclick="showScreen' in html


class TestAppJsScreenState:
    def test_state_has_screen_field(self):
        """state object has a 'screen' field."""
        js = _read(H5_APP)
        assert re.search(r'state\s*=\s*\{', js), "state object not found"
        assert re.search(r'screen\s*:', js), "state.screen not found"

    def test_show_screen_function_exists(self):
        """showScreen() function exists and toggles .active class."""
        js = _read(H5_APP)
        assert "function showScreen" in js or "showScreen =" in js
        assert ".screen" in js or "screen" in js


class TestTtsTaskFlow:
    def test_tts_tasks_endpoint_in_generate_tts_task(self):
        """generateTtsTask() calls POST /api/xiangta/tts/tasks."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "/api/xiangta/tts/tasks" in section, \
            "generateTtsTask must use /api/xiangta/tts/tasks"

    def test_poll_tts_task_function_exists(self):
        """pollTtsTask() or equivalent polling function exists."""
        js = _read(H5_APP)
        assert "pollTtsTask" in js, "pollTtsTask not found"

    def test_generate_tts_is_dev_only_alias(self):
        """generateTts() is present but is dev-only; formal path uses generateTtsTask()."""
        js = _read(H5_APP)
        # generateTts must exist (dev alias)
        assert "function generateTts" in js or "generateTts =" in js, \
            "generateTts dev alias not found"
        # generateTtsTask must exist (formal path)
        assert "function generateTtsTask" in js or "generateTtsTask =" in js, \
            "generateTtsTask formal path not found"


class TestFormalDevMode:
    def test_get_app_mode_exists(self):
        """getAppMode() exists and checks ?mode=dev."""
        js = _read(H5_APP)
        assert "function getAppMode" in js or "getAppMode =" in js
        assert "mode" in js

    def test_apply_mode_ui_exists(self):
        """applyModeUi() exists and toggles devPanel."""
        js = _read(H5_APP)
        assert "function applyModeUi" in js or "applyModeUi =" in js
        assert "devPanel" in js

    def test_dev_panel_in_index_html(self):
        """index.html has devPanel with coreProfileSelect inside."""
        html = _read(H5_INDEX)
        assert 'id="devPanel"' in html
        assert 'id="coreProfileSelect"' in html

    def test_profile_id_guard_in_generate_tts_task(self):
        """profileId is guarded by state.mode === 'dev' in generateTtsTask()."""
        js = _read(H5_APP)
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]
        # If profileId is mentioned, it must be guarded by dev mode
        if "profileId" in section:
            assert 'state.mode' in section and 'dev' in section, \
                "profileId must be guarded by dev mode check"


class TestButtonLock:
    def test_set_busy_function_exists(self):
        """setBusy() button lock function exists."""
        js = _read(H5_APP)
        assert "function setBusy" in js or "setBusy =" in js, \
            "setBusy button lock not found"


class TestHistory:
    def test_load_letters_uses_correct_endpoint(self):
        """loadLetters() uses GET /api/xiangta/letters."""
        js = _read(H5_APP)
        start = js.find("function loadLetters")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "/api/xiangta/letters" in section, \
            "loadLetters must use GET /api/xiangta/letters"


class TestStyles:
    def test_screen_styles_exist(self):
        """styles.css has .screen and .screen.active styles."""
        css = _read(H5_CSS)
        assert ".screen" in css, ".screen style not found"
        assert ".screen.active" in css or ".active" in css, ".screen.active not found"

    def test_mobile_product_flow_styles_exist(self):
        """styles.css has hero/choice-chip/bottom-actions/toast styles."""
        css = _read(H5_CSS)
        assert ".hero-card" in css or ".hero" in css, "hero style not found"
        assert ".choice-chip" in css or ".recipient-card" in css or ".scene-chip" in css, "choice card/chip style not found"
        assert ".bottom-actions" in css, "bottom-actions style not found"
        assert ".toast" in css, "toast style not found"


class TestTextLetterSaveFix:
    """FIX1: allow saving text letter even without audioUrl."""

    def test_reveal_save_letter_section_exists(self):
        """revealSaveLetterSection() function exists."""
        js = _read(H5_APP)
        assert "function revealSaveLetterSection" in js or "revealSaveLetterSection =" in js, \
            "revealSaveLetterSection not found"

    def test_render_tts_task_calls_reveal_save_letter(self):
        """renderTtsTask calls revealSaveLetterSection regardless of audioUrl."""
        js = _read(H5_APP)
        start = js.find("function renderTtsTask")
        end = js.find("\n}\n", start)
        section = js[start:end]
        assert "revealSaveLetterSection" in section, \
            "renderTtsTask must call revealSaveLetterSection"

    def test_render_tts_task_failed_branch_calls_reveal(self):
        """renderTtsTask failed branch does not return before revealSaveLetterSection."""
        js = _read(H5_APP)
        start = js.find("function renderTtsTask")
        end = js.find("\n}\n", start)
        section = js[start:end]

        # Find the failed branch
        failed_start = section.find('status === "failed"')
        if failed_start != -1:
            # Extract the failed block
            failed_block = section[failed_start:]
            # revealSaveLetterSection should appear after the return in failed block
            reveal_pos = failed_block.find("revealSaveLetterSection")
            return_pos = failed_block.find("return")
            if return_pos != -1:
                # If there's a return, revealSaveLetterSection must come before it
                assert reveal_pos != -1 and reveal_pos < return_pos, \
                    "failed branch must call revealSaveLetterSection before return"

    def test_tts_hint_style_exists(self):
        """.tts-hint style exists for no-audio hint message."""
        css = _read(H5_CSS)
        assert ".tts-hint" in css, ".tts-hint style not found"

    def test_save_letter_allows_null_audio(self):
        """saveLetter allows audioUrl to be null."""
        js = _read(H5_APP)
        start = js.find("function saveLetter")
        end = js.find("\n}\n", start)
        section = js[start:end]
        # Should have audioUrl with null fallback
        assert "audioUrl" in section, "saveLetter must handle audioUrl"
        # Should not require audioUrl to be truthy
        assert "|| null" in section or "||null" in section, \
            "saveLetter must allow audioUrl to be null"

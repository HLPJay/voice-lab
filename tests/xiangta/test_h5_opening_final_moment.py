"""
Tests for H5 opening overlay and final saved moment (P22Q).

Covers:
1. Opening overlay DOM exists in HTML
2. Opening text "有些话不好说" present
3. Opening text "但值得说" present
4. localStorage key "xiangta_opening_seen" used in JS
5. dismissOpeningOverlay function exists
6. initOpeningOverlay function exists
7. Result saved moment function showResultSavedMoment exists
8. showResultSavedMoment called after successful save
9. resultViewHistoryBtn still exists
10. resultViewHistoryBtn still calls showScreen("history")
11. resultSave duplicate guard preserved
12. Audio element still exists on result screen
13. No new backend API path added
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestOpeningOverlayDOM:
    """Opening overlay HTML structure."""

    def test_opening_overlay_exists(self):
        html = _read(H5_INDEX)
        assert 'id="openingOverlay"' in html

    def test_opening_overlay_has_headline_part1(self):
        html = _read(H5_INDEX)
        assert "有些话不好说" in html

    def test_opening_overlay_has_headline_part2(self):
        html = _read(H5_INDEX)
        assert "但值得说" in html

    def test_opening_overlay_has_body_text(self):
        html = _read(H5_INDEX)
        assert "整理成更合适的文字和语音" in html

    def test_opening_cta_button_text(self):
        html = _read(H5_INDEX)
        assert "开始表达" in html

    def test_opening_note_text(self):
        html = _read(H5_INDEX)
        assert "本机保存" in html

    def test_opening_dismiss_onclick(self):
        html = _read(H5_INDEX)
        assert "dismissOpeningOverlay" in html


class TestOpeningOverlayJS:
    """Opening overlay JS logic."""

    def test_init_opening_overlay_exists(self):
        js = _read(H5_APP)
        assert "function initOpeningOverlay" in js

    def test_dismiss_opening_overlay_exists(self):
        js = _read(H5_APP)
        assert "function dismissOpeningOverlay" in js

    def test_localstorage_key_used(self):
        js = _read(H5_APP)
        assert "xiangta_opening_seen" in js

    def test_localstorage_set_on_dismiss(self):
        js = _read(H5_APP)
        assert 'localStorage.setItem("xiangta_opening_seen"' in js or \
               "localStorage.setItem('xiangta_opening_seen'" in js

    def test_localstorage_get_on_init(self):
        js = _read(H5_APP)
        assert 'localStorage.getItem("xiangta_opening_seen")' in js or \
               "localStorage.getItem('xiangta_opening_seen')" in js

    def test_init_called_on_domcontentloaded(self):
        js = _read(H5_APP)
        dcl_idx = js.find("DOMContentLoaded")
        assert dcl_idx >= 0
        dcl_block = js[dcl_idx:dcl_idx + 400]
        assert "initOpeningOverlay" in dcl_block

    def test_fail_open_on_localstorage_error(self):
        """If localStorage throws, overlay must be hidden (fail open)."""
        js = _read(H5_APP)
        idx = js.find("function initOpeningOverlay")
        assert idx >= 0
        # Extract enough chars to cover the full function body (has nested braces)
        snippet = js[idx:idx + 500]
        assert "catch" in snippet, \
            "initOpeningOverlay must catch localStorage errors and fail open"


class TestOpeningOverlayCSS:
    """Opening overlay CSS."""

    def test_opening_overlay_css_exists(self):
        css = _read(H5_CSS)
        assert ".opening-overlay" in css

    def test_opening_overlay_z_index_high(self):
        css = _read(H5_CSS)
        m = re.search(r'\.opening-overlay\s*\{[^}]+\}', css)
        assert m
        assert "z-index" in m.group()

    def test_opening_headline_css_exists(self):
        css = _read(H5_CSS)
        assert ".opening-headline" in css

    def test_opening_cta_css_exists(self):
        css = _read(H5_CSS)
        assert ".opening-cta" in css


class TestResultSavedMoment:
    """Final saved moment after successful save."""

    def test_show_result_saved_moment_function_exists(self):
        js = _read(H5_APP)
        assert "function showResultSavedMoment" in js

    def test_show_result_saved_moment_called_after_save(self):
        js = _read(H5_APP)
        save_fn_idx = js.find("async function resultSave")
        assert save_fn_idx >= 0
        # Function body is ~1300 chars; use generous window
        save_fn_body = js[save_fn_idx:save_fn_idx + 1500]
        assert "showResultSavedMoment" in save_fn_body, \
            "resultSave must call showResultSavedMoment after success"

    def test_saved_moment_uses_seal_overlay(self):
        js = _read(H5_APP)
        m = re.search(r'function showResultSavedMoment\(\)\s*\{[^}]+\}', js, re.DOTALL)
        assert m
        assert "resultSaveSealOverlay" in m.group()

    def test_saved_moment_does_not_navigate(self):
        js = _read(H5_APP)
        m = re.search(r'function showResultSavedMoment\(\)\s*\{[^}]+\}', js, re.DOTALL)
        assert m
        fn_body = m.group()
        assert "showScreen" not in fn_body, \
            "showResultSavedMoment must not auto-navigate away from result"

    def test_result_save_seal_overlay_exists_in_html(self):
        html = _read(H5_INDEX)
        assert 'id="resultSaveSealOverlay"' in html

    def test_seal_label_已收好(self):
        html = _read(H5_INDEX)
        assert "已 · 收 · 好" in html


class TestResultSaveBehaviorPreserved:
    """P22P behavior must be fully preserved."""

    def test_result_view_history_btn_still_exists(self):
        html = _read(H5_INDEX)
        assert 'id="resultViewHistoryBtn"' in html

    def test_result_view_history_btn_calls_history(self):
        html = _read(H5_INDEX)
        idx = html.find('id="resultViewHistoryBtn"')
        snippet = html[idx:idx + 200]
        assert "showScreen('history')" in snippet or 'showScreen("history")' in snippet

    def test_duplicate_save_guard_preserved(self):
        js = _read(H5_APP)
        assert "if (state.resultSaved) return" in js

    def test_已保存_label_preserved(self):
        js = _read(H5_APP)
        assert '"已保存"' in js

    def test_toast_已保存到信笺夹_preserved(self):
        js = _read(H5_APP)
        assert "已保存到信笺夹" in js


class TestResultActionsPreserved:
    """Audio and result actions must be unchanged."""

    def test_result_audio_element_exists(self):
        html = _read(H5_INDEX)
        assert 'id="resultAudio"' in html

    def test_result_action_从头听_exists(self):
        html = _read(H5_INDEX)
        assert "从头听" in html

    def test_result_action_下载_exists(self):
        html = _read(H5_INDEX)
        assert "下载" in html

    def test_result_action_复制_exists(self):
        html = _read(H5_INDEX)
        assert "复制" in html

    def test_result_action_重新编辑_exists(self):
        html = _read(H5_INDEX)
        assert "重新编辑" in html

    def test_result_action_换个语气_exists(self):
        html = _read(H5_INDEX)
        assert "换个语气" in html

    def test_no_new_backend_api(self):
        js = _read(H5_APP)
        assert "/api/xiangta/opening" not in js
        assert "/api/xiangta/overlay" not in js


class TestClickFeedbackCSS:
    """Lightweight click/pressed feedback CSS."""

    def test_recipient_card_has_transition(self):
        css = _read(H5_CSS)
        m = re.search(r'\.recipient-card[\s,][^{]*\{[^}]+transition[^}]+\}', css, re.DOTALL)
        assert m or "transition: transform" in css, \
            "recipient-card should have transform transition"

    def test_cta_button_active_scale(self):
        css = _read(H5_CSS)
        assert ".cta-button:not(:disabled):active" in css

    def test_suggestion_card_active_scale(self):
        css = _read(H5_CSS)
        assert ".suggestion-card:active" in css

    def test_voice_option_active_scale(self):
        css = _read(H5_CSS)
        assert ".voice-option:active" in css

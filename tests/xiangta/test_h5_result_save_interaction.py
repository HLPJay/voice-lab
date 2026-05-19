"""
Tests for H5 Result page save interaction (P22P).

Covers:
1. Initial button state ("保存到信笺夹")
2. Saving in-progress text ("正在保存...")
3. After-save button text ("已保存") and disabled state
4. "查看信笺夹" button exists and is initially hidden
5. After save, "查看信笺夹" is revealed (removes "hidden")
6. "查看信笺夹" navigates to history screen
7. Toast "已保存到信笺夹" shown on success
8. Duplicate-save guard (state.resultSaved)
9. Result save section exists in HTML
10. Letters API endpoint preserved
11. updateResultSaveButton function exists
12. resultSave function exists
13. result-view-history-btn CSS rule exists
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestResultSaveInitialState:
    """Initial save button state in HTML."""

    def test_result_save_section_exists(self):
        html = _read(H5_INDEX)
        assert 'class="result-save-section"' in html

    def test_btn_result_save_exists(self):
        html = _read(H5_INDEX)
        assert 'id="btnResultSave"' in html

    def test_result_save_label_initial_text(self):
        html = _read(H5_INDEX)
        assert "保存到信笺夹" in html

    def test_view_history_btn_exists(self):
        html = _read(H5_INDEX)
        assert 'id="resultViewHistoryBtn"' in html

    def test_view_history_btn_initially_hidden(self):
        html = _read(H5_INDEX)
        assert 'id="resultViewHistoryBtn"' in html
        idx = html.find('id="resultViewHistoryBtn"')
        snippet = html[idx:idx + 120]
        assert "hidden" in snippet, \
            "resultViewHistoryBtn should have hidden class initially"

    def test_view_history_btn_calls_show_history(self):
        html = _read(H5_INDEX)
        idx = html.find('id="resultViewHistoryBtn"')
        snippet = html[idx:idx + 200]
        assert "showScreen('history')" in snippet or 'showScreen("history")' in snippet, \
            "resultViewHistoryBtn onclick should call showScreen('history')"


class TestResultSavingInProgress:
    """Saving in-progress state."""

    def test_正在保存_text_in_js(self):
        js = _read(H5_APP)
        assert "正在保存" in js, \
            "resultSave should show '正在保存...' while API call is in flight"

    def test_set_busy_called_on_save(self):
        js = _read(H5_APP)
        assert 'setBusy("btnResultSave", true' in js, \
            "resultSave should disable button while saving"


class TestResultAfterSaveSuccess:
    """State after successful save."""

    def test_saved_label_is_已保存(self):
        js = _read(H5_APP)
        assert '"已保存"' in js, \
            "updateResultSaveButton should set label to '已保存' when saved"

    def test_button_disabled_when_saved(self):
        js = _read(H5_APP)
        assert "btn.disabled = true" in js, \
            "Save button should be disabled after successful save"

    def test_view_history_btn_hidden_removed_when_saved(self):
        js = _read(H5_APP)
        assert 'viewHistoryBtn.classList.remove("hidden")' in js, \
            "resultViewHistoryBtn hidden class should be removed after save"

    def test_toast_已保存到信笺夹(self):
        js = _read(H5_APP)
        assert "已保存到信笺夹" in js, \
            "resultSave should show toast '已保存到信笺夹' on success"


class TestResultSaveDuplicateGuard:
    """Duplicate save prevention."""

    def test_result_saved_guard_exists(self):
        js = _read(H5_APP)
        assert "if (state.resultSaved) return" in js, \
            "resultSave must guard against duplicate saves"

    def test_state_result_saved_initialized_false(self):
        js = _read(H5_APP)
        assert "resultSaved: false" in js, \
            "state.resultSaved should initialize to false"


class TestResultSaveFunctionPreservation:
    """Core functions must be preserved."""

    def test_result_save_function_exists(self):
        js = _read(H5_APP)
        assert "async function resultSave" in js

    def test_update_result_save_button_exists(self):
        js = _read(H5_APP)
        assert "function updateResultSaveButton" in js

    def test_letters_api_endpoint_preserved(self):
        js = _read(H5_APP)
        assert "/api/xiangta/letters" in js


class TestResultViewHistoryButtonStyle:
    """CSS for result-view-history-btn."""

    def test_result_view_history_btn_css_exists(self):
        css = _read(H5_CSS)
        assert ".result-view-history-btn" in css, \
            "CSS rule for .result-view-history-btn must exist"

    def test_result_save_button_saved_disabled_cursor(self):
        css = _read(H5_CSS)
        m = re.search(r'\.result-save-button\.saved\s*\{[^}]+\}', css)
        assert m, ".result-save-button.saved rule not found"
        assert "cursor: not-allowed" in m.group(), \
            ".result-save-button.saved should show not-allowed cursor"

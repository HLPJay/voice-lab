"""P25G: H5 Result save button DOM restore — minimal targeted test."""
import re
import os

APP_JS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "apps", "xiangta-h5", "app.js"
)


def read_app_js():
    with open(APP_JS_PATH, encoding="utf-8") as f:
        return f.read()


def get_result_save_body(content):
    match = re.search(
        r'async function resultSave\(\).*?(?=\n(?:async function|function \w|\Z))',
        content,
        re.DOTALL,
    )
    assert match, "resultSave not found"
    return match.group(0)


class TestResultSaveButtonDomRestore:
    """Verify setResultSaveBusy replaces setBusy for btnResultSave, preserving DOM."""

    def test_resultSave_no_longer_calls_setBusy_on_btnResultSave(self):
        content = read_app_js()
        body = get_result_save_body(content)
        set_busy_calls = re.findall(
            r"setBusy\s*\(\s*['\"]btnResultSave['\"]", body
        )
        assert len(set_busy_calls) == 0, (
            f"resultSave still calls setBusy on btnResultSave: {set_busy_calls}"
        )

    def test_resultSave_uses_setResultSaveBusy_true(self):
        content = read_app_js()
        body = get_result_save_body(content)
        assert "setResultSaveBusy(true" in body, (
            "resultSave should call setResultSaveBusy(true, '正在收好...')"
        )

    def test_resultSave_uses_setResultSaveBusy_false_on_null_response(self):
        content = read_app_js()
        body = get_result_save_body(content)
        # Uses double quotes in app.js
        assert 'setResultSaveBusy(false, "保存到信笺夹")' in body, (
            "On null response resultSave should call setResultSaveBusy(false, \"保存到信笺夹\")"
        )

    def test_setResultSaveBusy_updates_label_not_button_textContent(self):
        content = read_app_js()
        match = re.search(
            r'function setResultSaveBusy\(.*?\n\}',
            content,
            re.DOTALL,
        )
        assert match, "setResultSaveBusy not found"
        body = match.group(0)
        assert "label.textContent" in body, (
            "setResultSaveBusy should update label.textContent"
        )
        assert "btn.textContent" not in body and "button.textContent" not in body, (
            "setResultSaveBusy must not assign button.textContent"
        )

    def test_ensureResultSaveButtonDom_can_recover_polluted_dom(self):
        content = read_app_js()
        assert "ensureResultSaveButtonDom" in content, (
            "ensureResultSaveButtonDom helper must exist"
        )
        match = re.search(
            r'function ensureResultSaveButtonDom\(\).*?\n\}',
            content,
            re.DOTALL,
        )
        assert match
        body = match.group(0)
        assert "resultSaveLabel" in body, (
            "ensureResultSaveButtonDom must recreate resultSaveLabel"
        )
        assert "btn.innerHTML" in body, (
            "ensureResultSaveButtonDom must rebuild innerHTML when label is missing"
        )

    def test_resultSave_timeoutMs_still_12000(self):
        content = read_app_js()
        body = get_result_save_body(content)
        timeout_match = re.search(r'timeoutMs\s*:\s*(\d+)', body)
        assert timeout_match, "timeoutMs not found in resultSave"
        assert timeout_match.group(1) == "12000", (
            f"timeoutMs should be 12000, got {timeout_match.group(1)}"
        )

    def test_save_payload_structure_unchanged(self):
        content = read_app_js()
        body = get_result_save_body(content)
        required_keys = [
            "recipient", "scene", "style", "rawText", "finalText",
            "voicePreset", "tone", "audioUrl", "durationSecs", "title"
        ]
        for key in required_keys:
            assert key in body, f"Payload missing key: {key}"
        post_body_match = re.search(
            r'apiFetch\(\s*"[^"]*letters[^"]*",\s*\{[^}]*body\s*:\s*JSON\.stringify\(\s*\{',
            body,
            re.DOTALL,
        )
        if post_body_match:
            post_body = post_body_match.group(0)
            assert "profileId" not in post_body, (
                "profileId should not appear in the save POST body"
            )

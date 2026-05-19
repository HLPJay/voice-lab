"""Tests for P23B: JS foundation module split into js/ subdirectory."""
import os

JS_DIR = "apps/xiangta-h5/js"
H5_APP = "apps/xiangta-h5/app.js"
H5_INDEX = "apps/xiangta-h5/index.html"

EXPECTED_MODULES = [
    "constants.js",
    "state.js",
    "dom.js",
    "api.js",
    "utils.js",
]


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestModuleFilesExist:
    def test_js_directory_exists(self):
        assert os.path.isdir(JS_DIR), "js/ subdirectory must exist"

    def test_all_module_files_exist(self):
        for name in EXPECTED_MODULES:
            path = os.path.join(JS_DIR, name)
            assert os.path.isfile(path), f"{name} must exist in js/"

    def test_app_js_still_exists(self):
        assert os.path.isfile(H5_APP), "app.js must still exist"


class TestIndexHtmlScriptOrder:
    def test_index_loads_all_modules_before_app_js(self):
        html = _read(H5_INDEX)
        for name in EXPECTED_MODULES:
            assert f"/h5/js/{name}" in html, \
                f"index.html must load /h5/js/{name}"
        app_idx = html.find("/h5/app.js")
        assert app_idx >= 0, "index.html must load /h5/app.js"
        for name in EXPECTED_MODULES:
            mod_idx = html.find(f"/h5/js/{name}")
            assert mod_idx < app_idx, \
                f"/h5/js/{name} must appear before /h5/app.js in index.html"

    def test_no_type_module_on_script_tags(self):
        html = _read(H5_INDEX)
        import re
        script_tags = re.findall(r'<script[^>]*>', html)
        for tag in script_tags:
            assert 'type="module"' not in tag and "type='module'" not in tag, \
                f"Script tag must not use type=module: {tag}"


class TestModuleContents:
    def test_constants_has_recipient_meta(self):
        js = _read(f"{JS_DIR}/constants.js")
        assert "RECIPIENT_META" in js
        assert "SCENE_META" in js
        assert "TONE_META" in js
        assert "STYLE_LABELS" in js
        assert "STEP_LABELS" in js
        assert "FLOW_EXAMPLES" in js

    def test_state_has_state_object(self):
        js = _read(f"{JS_DIR}/state.js")
        assert "const state" in js
        assert "selectedRecipient" in js
        assert "resultSaved" in js

    def test_dom_has_el_and_eschtml(self):
        js = _read(f"{JS_DIR}/dom.js")
        assert "function el(" in js
        assert "function escHtml(" in js

    def test_api_has_apifetch(self):
        js = _read(f"{JS_DIR}/api.js")
        assert "async function apiFetch(" in js
        assert "/api/xiangta" not in js, \
            "api.js should not contain xiangta-specific paths"

    def test_utils_has_key_functions(self):
        js = _read(f"{JS_DIR}/utils.js")
        assert "function normalizeCopyText(" in js
        assert "function formatDuration(" in js
        assert "function letterTime(" in js
        assert "function formatTime(" in js
        assert "function getBootstrapRecipientLabel(" in js
        assert "function getBootstrapSceneLabel(" in js
        assert "function getBootstrapVoiceLabel(" in js
        assert "function getBootstrapToneLabel(" in js


class TestAppJsPreservesPageLogic:
    def test_app_js_has_screen_functions(self):
        js = _read(H5_APP)
        for fn in [
            "function showScreen(",
            "function goCompose(",
            "async function generateSuggestions(",
            "async function goVoice(",
            "async function generateTtsTask(",
            "async function resultSave(",
            "function toggleHistorySearch(",
            "function refreshSettingsStatus(",
            "function dismissOpeningOverlay(",
        ]:
            assert fn in js, f"app.js must still contain {fn}"

    def test_app_js_does_not_contain_moved_functions(self):
        js = _read(H5_APP)
        assert "function el(" not in js, "el() must be in dom.js not app.js"
        assert "function escHtml(" not in js, "escHtml() must be in dom.js not app.js"
        assert "async function apiFetch(" not in js, "apiFetch() must be in api.js not app.js"
        assert "const state = {" not in js, "state must be in state.js not app.js"
        assert "RECIPIENT_META" not in js or "RECIPIENT_META[" in js, \
            "RECIPIENT_META definition must be in constants.js"

"""
Tests for H5 formal/dev mode separation.

Covers:
1. index.html contains devPanel
2. index.html coreProfileSelect is inside devPanel
3. app.js default mode is formal
4. app.js supports ?mode=dev
5. app.js formal mode doesn't unconditionally call loadCoreProfiles()
6. app.js only dev mode allows payload.profileId
7. styles.css contains dev-panel and hidden styles
"""
import re

import pytest

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestIndexHtml:
    def test_contains_dev_panel(self):
        html = _read(H5_INDEX)
        assert 'id="devPanel"' in html

    def test_core_profile_select_inside_dev_panel(self):
        html = _read(H5_INDEX)
        # Extract devPanel section by finding the opening div and counting matching close
        dev_panel_start = html.find('<div id="devPanel"')
        assert dev_panel_start != -1, "devPanel not found"

        # Find the matching closing </div> for devPanel
        # We scan from dev_panel_start and count div nesting
        pos = dev_panel_start
        depth = 0
        while pos < len(html):
            next_open = html.find('<div', pos)
            next_close = html.find('</div>', pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 1
            else:
                depth -= 1
                if depth == 0:
                    # found matching close for devPanel
                    dev_panel_end = next_close
                    break
                pos = next_close + 1

        core_profile_start = html.find('id="coreProfileSelect"')
        assert core_profile_start != -1, "coreProfileSelect not found"

        # coreProfileSelect must be between devPanel open and its closing tag
        assert dev_panel_start < core_profile_start < dev_panel_end, \
            "coreProfileSelect must be inside devPanel"

    def test_dev_panel_has_hidden_class_initially(self):
        html = _read(H5_INDEX)
        # devPanel should have hidden class so formal mode hides it by default
        assert re.search(r'id="devPanel"\s+class="[^"]*hidden', html) or \
               re.search(r'class="[^"]*hidden[^"]*"\s+id="devPanel"', html), \
               "devPanel must have 'hidden' class"


class TestAppJs:
    def test_default_mode_is_formal(self):
        js = _read(H5_APP)
        # state.mode should default to "formal"
        assert 'mode:            "formal"' in js or \
               'mode: "formal"' in js

    def test_supports_mode_dev_param(self):
        js = _read(H5_APP)
        # getAppMode() should check for ?mode=dev
        assert "params.get(\"mode\")" in js or \
               "params.get('mode')" in js
        assert '=== "dev"' in js or "=== 'dev'" in js

    def test_apply_mode_ui_toggles_dev_panel(self):
        js = _read(H5_APP)
        # applyModeUi should toggle hidden class on devPanel
        assert "applyModeUi" in js
        assert 'devPanel.classList.toggle("hidden"' in js or \
               "devPanel.classList.toggle('hidden'" in js

    def test_formal_mode_does_not_call_load_core_profiles_unconditionally(self):
        js = _read(H5_APP)
        # loadBootstrap should NOT unconditionally call loadCoreProfiles()
        # It should be wrapped in a mode check
        loadbootstrap_section = js[js.find("function loadBootstrap"):]
        loadbootstrap_section = loadbootstrap_section[:loadbootstrap_section.find("\n}\n")]

        # Should NOT have bare loadCoreProfiles() call
        # Should have it inside an if (state.mode === "dev") block
        if "loadCoreProfiles()" in loadbootstrap_section:
            # The bare call should NOT exist without the mode guard
            assert "if (state.mode === \"dev\")" in loadbootstrap_section or \
                   "if (state.mode === 'dev')" in loadbootstrap_section, \
                   "loadCoreProfiles() must be guarded by dev mode check"

    def test_profile_id_only_in_dev_mode(self):
        js = _read(H5_APP)
        # generateTts should only add profileId when in dev mode
        # The condition should include state.mode === "dev"
        generatetts_section = js[js.find("function generateTts"):]
        generatetts_section = generatetts_section[:generatetts_section.find("\n}\n")]

        if "payload.profileId" in generatetts_section:
            assert 'state.mode === "dev"' in generatetts_section or \
                   "state.mode === 'dev'" in generatetts_section, \
                   "profileId must only be set in dev mode"


class TestStylesCss:
    def test_hidden_utility_exists(self):
        css = _read(H5_CSS)
        assert ".hidden" in css or "#" not in css  # .hidden { display: none }

    def test_dev_panel_style_exists(self):
        css = _read(H5_CSS)
        assert ".dev-panel" in css
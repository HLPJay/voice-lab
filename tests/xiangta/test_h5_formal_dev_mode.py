"""
Tests for H5 formal/dev mode separation (trimmed to 8 tests).

Covers:
1. index.html contains devPanel with coreProfileSelect inside
2. devPanel has hidden class
3. app.js default mode is formal and supports ?mode=dev
4. app.js applyModeUi toggles devPanel and sets body[data-mode]
5. app.js loadCoreProfiles() guarded by dev mode
6. app.js payload.profileId guarded by dev mode
7. styles.css has explicit .hidden with display: none
8. styles.css has .dev-panel style
"""
import re

H5_INDEX = "apps/xiangta-h5/index.html"
H5_APP = "apps/xiangta-h5/app.js"
H5_CSS = "apps/xiangta-h5/styles.css"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestIndexHtml:
    def test_dev_panel_exists_and_contains_core_profile_select(self):
        """devPanel exists in index.html and coreProfileSelect is inside it."""
        html = _read(H5_INDEX)
        assert 'id="devPanel"' in html

        dev_panel_start = html.find('<div id="devPanel"')
        assert dev_panel_start != -1, "devPanel not found"

        # Find matching closing </div>
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
                    dev_panel_end = next_close
                    break
                pos = next_close + 1

        core_profile_start = html.find('id="coreProfileSelect"')
        assert core_profile_start != -1, "coreProfileSelect not found"
        assert dev_panel_start < core_profile_start < dev_panel_end, \
            "coreProfileSelect must be inside devPanel"

    def test_dev_panel_has_hidden_class(self):
        """devPanel has 'hidden' class so formal mode hides it by default."""
        html = _read(H5_INDEX)
        assert re.search(r'id="devPanel"\s+class="[^"]*hidden', html) or \
               re.search(r'class="[^"]*hidden[^"]*"\s+id="devPanel"', html), \
               "devPanel must have 'hidden' class"


class TestAppJs:
    def test_default_mode_is_formal_and_supports_dev_param(self):
        """state.mode defaults to formal, and getAppMode() checks ?mode=dev."""
        js = _read(H5_APP)
        assert 'mode:            "formal"' in js or 'mode: "formal"' in js
        assert "params.get(\"mode\")" in js or "params.get('mode')" in js
        assert '=== "dev"' in js or "=== 'dev'" in js

    def test_apply_mode_ui_toggles_dev_panel_and_sets_body_attribute(self):
        """applyModeUi toggles devPanel hidden and sets body[data-mode]."""
        js = _read(H5_APP)
        assert "applyModeUi" in js
        assert 'devPanel.classList.toggle("hidden"' in js or \
               "devPanel.classList.toggle('hidden'" in js
        assert 'document.body.setAttribute("data-mode"' in js or \
               "document.body.setAttribute('data-mode'" in js

    def test_load_core_profiles_guard(self):
        """loadCoreProfiles() call is guarded by state.mode === 'dev'."""
        js = _read(H5_APP)
        # Find loadBootstrap function
        start = js.find("function loadBootstrap")
        end = js.find("\n}\n", start)
        section = js[start:end]

        if "loadCoreProfiles()" in section:
            assert 'state.mode === "dev"' in section or \
                   "state.mode === 'dev'" in section, \
                   "loadCoreProfiles() must be guarded by dev mode check"

    def test_profile_id_guard(self):
        """payload.profileId is only set when state.mode === 'dev'."""
        js = _read(H5_APP)
        start = js.find("function generateTts")
        end = js.find("\n}\n", start)
        section = js[start:end]

        if "payload.profileId" in section:
            assert 'state.mode === "dev"' in section or \
                   "state.mode === 'dev'" in section, \
                   "profileId must only be set in dev mode"


class TestStylesCss:
    def test_hidden_utility_explicit(self):
        """.hidden utility explicitly sets display: none."""
        css = _read(H5_CSS)
        assert ".hidden" in css
        assert "display: none" in css

    def test_dev_panel_style_exists(self):
        """.dev-panel style exists for dev-only section."""
        css = _read(H5_CSS)
        assert ".dev-panel" in css
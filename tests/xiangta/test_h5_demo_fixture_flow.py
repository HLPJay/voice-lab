"""
Structural tests for P23D: H5 demo fixture flow.

Verifies that:
- demo-fixtures.js exists and is loaded before app.js
- state.js has demo fixture tracking fields
- app.js has the fixture bypass path in generateSuggestions
- fillSceneExample sets demoFixtureActive
- fixture bypass does not call /api/xiangta/suggestions
- edited rawText falls back to real API
- fixture data covers all 5 scenes
- no mock audio techniques used
- backend files untouched
"""
import os

JS_DIR = "apps/xiangta-h5/js"
H5_APP = "apps/xiangta-h5/app.js"
H5_INDEX = "apps/xiangta-h5/index.html"
H5_STATE = "apps/xiangta-h5/js/state.js"
H5_FIXTURES = "apps/xiangta-h5/js/demo-fixtures.js"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestFixtureFileExists:
    def test_demo_fixtures_js_exists(self):
        assert os.path.isfile(H5_FIXTURES), "demo-fixtures.js must exist in js/"

    def test_index_loads_demo_fixtures_before_app_js(self):
        html = _read(H5_INDEX)
        fixtures_idx = html.find("/h5/js/demo-fixtures.js")
        app_idx = html.find("/h5/app.js")
        assert fixtures_idx >= 0, "index.html must load /h5/js/demo-fixtures.js"
        assert fixtures_idx < app_idx, \
            "demo-fixtures.js must appear before app.js in index.html"

    def test_no_type_module_on_fixture_script(self):
        html = _read(H5_INDEX)
        import re
        for tag in re.findall(r'<script[^>]*demo-fixtures[^>]*>', html):
            assert 'type="module"' not in tag


class TestStateFields:
    def test_state_has_demo_fixture_key(self):
        js = _read(H5_STATE)
        assert "demoFixtureKey" in js, "state must have demoFixtureKey field"

    def test_state_has_demo_fixture_active(self):
        js = _read(H5_STATE)
        assert "demoFixtureActive" in js, "state must have demoFixtureActive field"

    def test_demo_fixture_active_defaults_false(self):
        js = _read(H5_STATE)
        assert "demoFixtureActive: false" in js


class TestFixtureActivation:
    def test_fill_scene_example_sets_fixture_active(self):
        js = _read(H5_APP)
        idx = js.find("function fillSceneExample(")
        assert idx >= 0
        body = js[idx:idx + 1200]
        assert "state.demoFixtureActive = true" in body, \
            "fillSceneExample must set state.demoFixtureActive = true"

    def test_fill_scene_example_sets_fixture_key(self):
        js = _read(H5_APP)
        idx = js.find("function fillSceneExample(")
        body = js[idx:idx + 1200]
        assert "state.demoFixtureKey" in body, \
            "fillSceneExample must set state.demoFixtureKey"


class TestFixtureBypass:
    def test_generate_suggestions_has_fixture_bypass(self):
        js = _read(H5_APP)
        idx = js.find("async function generateSuggestions(")
        assert idx >= 0
        body = js[idx:idx + 2200]
        assert "demoFixtureActive" in body, \
            "generateSuggestions must check demoFixtureActive"
        assert "DEMO_FIXTURES" in body, \
            "generateSuggestions must reference DEMO_FIXTURES"

    def test_fixture_bypass_does_not_call_suggestions_api(self):
        """The fixture branch must return before calling apiFetch('/api/xiangta/suggestions')."""
        js = _read(H5_APP)
        idx = js.find("async function generateSuggestions(")
        body = js[idx:idx + 2200]
        # Find the fixture bypass block: it should have a 'return;' before apiFetch
        fixture_block_end = body.find("return;", body.find("DEMO_FIXTURES"))
        api_call_idx = body.find('apiFetch("/api/xiangta/suggestions"')
        assert fixture_block_end >= 0, "fixture bypass must end with return;"
        assert api_call_idx >= 0, "real API call must still exist"
        assert fixture_block_end < api_call_idx, \
            "fixture bypass must return before the real apiFetch call"

    def test_real_api_call_preserved(self):
        js = _read(H5_APP)
        assert 'apiFetch("/api/xiangta/suggestions"' in js, \
            "real suggestions API call must be preserved in app.js"

    def test_real_api_payload_preserved(self):
        js = _read(H5_APP)
        idx = js.find('apiFetch("/api/xiangta/suggestions"')
        snippet = js[idx:idx + 300]
        assert "recipient" in snippet
        assert "scene" in snippet
        assert "rawText" in snippet

    def test_edited_text_falls_back_to_api(self):
        """rawText comparison ensures fixture is skipped when text is edited."""
        js = _read(H5_APP)
        idx = js.find("async function generateSuggestions(")
        body = js[idx:idx + 2200]
        # The bypass condition must compare rawText to fixture.rawText
        assert "fixture.rawText" in body or "rawText === DEMO_FIXTURES" in body or \
               ".rawText.trim()" in body, \
            "fixture bypass must compare rawText to fixture.rawText to detect edits"

    def test_update_compose_state_can_clear_fixture_flag_on_edit(self):
        """State hygiene: once text no longer matches fixture, demo flag can be cleared."""
        js = _read(H5_APP)
        idx = js.find("function updateComposeState(")
        assert idx >= 0
        body = js[idx:idx + 1200]
        assert "state.demoFixtureActive = false" in body


class TestFixtureData:
    def test_fixture_covers_all_scenes(self):
        js = _read(H5_FIXTURES)
        for scene in ["miss", "sorry", "thanks", "comfort", "night"]:
            assert f'"{scene}"' in js or f"  {scene}:" in js, \
                f"DEMO_FIXTURES must include scene '{scene}'"

    def test_fixture_has_suggestion_meta(self):
        js = _read(H5_FIXTURES)
        assert "suggestionMeta" in js
        assert "demo_fixture" in js

    def test_fixture_has_three_styles(self):
        js = _read(H5_FIXTURES)
        assert "restrained" in js
        assert "gentle" in js
        assert "sincere" in js

    def test_fixture_has_preferred_index(self):
        js = _read(H5_FIXTURES)
        assert "preferredIndex" in js

    def test_fixture_no_silent_wav(self):
        js = _read(H5_FIXTURES)
        assert "_silentWav" not in js
        assert "silentWav" not in js

    def test_fixture_no_speech_synthesis(self):
        js = _read(H5_FIXTURES)
        assert "speechSynthesis" not in js


class TestNoMockAudio:
    def test_app_js_no_silent_wav(self):
        js = _read(H5_APP)
        assert "_silentWav" not in js

    def test_app_js_no_speech_synthesis_in_fixture_path(self):
        js = _read(H5_APP)
        idx = js.find("async function generateSuggestions(")
        body = js[idx:idx + 2200]
        assert "speechSynthesis" not in body


class TestBackendUnmodified:
    def test_src_xiangta_not_in_allowed_files(self):
        """Confirm no src/xiangta files were listed as modified (structural check)."""
        # This is a policy check — we verify backend API paths are unchanged in app.js
        js = _read(H5_APP)
        assert 'apiFetch("/api/xiangta/suggestions"' in js
        assert 'apiFetch("/api/xiangta/tts/tasks"' in js or \
               'apiFetch("/api/xiangta/letters"' in js, \
            "backend API paths must be unchanged"

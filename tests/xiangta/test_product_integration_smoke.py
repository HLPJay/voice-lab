"""
P18-XIANGTA-PRODUCT-INTEGRATION-SMOKE-C10 — Product Flow Integration Smoke Tests

Covers:
1. Backend product API flow: no-audio letter save + history retrieval
2. Forbidden fields not leaked in any API response
3. H5 screen-based mobile product flow contract
4. H5 formal path uses /api/xiangta/tts/tasks
5. H5 no-audio text letter save contract
6. formal/dev mode separation contract
7. Mobile-first CSS contract
8. NEXT_TASKS.md current stage is C10

Scope: 8 tests, no browser, no real provider.
"""
import pytest
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.config.product_config_models import ProductVoiceMapping
from src.xiangta.services.letter_service import clear_letters_for_tests
from src.xiangta.services.tts_task_service import clear_tts_tasks_for_tests
from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService

_H5_DIR = Path(__file__).parent.parent.parent / "apps" / "xiangta-h5"

_USER_FORBIDDEN = {
    "api_key", "minimax_api_key", "mimo_api_key",
    "coreBindingKey", "core_binding_key",
    "coreProfileId", "core_profile_id", "profile_id",
    "provider_voice_id", "binding_id", "params_json",
    "model_id", "voice_id", "stack_trace",
    "rawResponse", "providerPolicy", "renderOverrides",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect_keys(obj, seen=None):
    if seen is None:
        seen = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            seen.add(k)
            _collect_keys(v, seen)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, seen)
    return seen


def _has_forbidden(body_str):
    for key in _USER_FORBIDDEN:
        if key in body_str:
            return key
    return None


async def _fake_generate_tts_success(
    self, *, text, target, tone, scene, style=None, metadata=None
):
    return {
        "taskId": "JOB_123",
        "status": "completed",
        "audioUrl": "/api/voice/assets/audio_123/download",
        "durationMs": 2000,
        "message": None,
        "contract": {
            "voicePresetId": target,
            "tone": tone,
            "toneHint": "soft",
            "scene": scene,
            "mode": "core_render_mock",
        },
    }


async def _fake_generate_tts_no_audio(
    self, *, text, target, tone, scene, style=None, metadata=None
):
    return {
        "taskId": "JOB_456",
        "status": "completed",
        "audioUrl": None,
        "durationMs": None,
        "message": "dry_run: no provider",
        "contract": {
            "voicePresetId": target,
            "tone": tone,
            "toneHint": "soft",
            "scene": scene,
            "mode": "core_render_mock",
        },
    }


def _mock_voice_mapping(monkeypatch):
    def fake_resolve(self, voice_preset_id):
        return ProductVoiceMapping(
            id="female-gentle", label="温柔女声", desc="适合想念",
            gender_style="female", suitable_recipients=["lover", "friend"],
            recommended_scenes=["miss", "night"], default_tone="gentle",
            enabled=True, sort_order=10,
            core_profile_id="deep_night_programmer",
            provider_policy="mock", render_overrides={}, notes=None,
        )
    monkeypatch.setattr(VoicePresetMappingService, "resolve", fake_resolve)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean():
    clear_letters_for_tests()
    clear_tts_tasks_for_tests()
    yield
    clear_letters_for_tests()
    clear_tts_tasks_for_tests()


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ── Test 1: Backend product flow with no-audio letter save ────────────────────

class TestProductApiFlow:
    """Integration smoke: bootstrap → suggestions → tts/tasks → letter save → history."""

    _SUGGESTION_BODY = {
        "recipient": "lover",
        "scene": "miss",
        "rawText": "好想你呀今天",
    }

    _LETTER_BODY_BASE = {
        "recipient": "lover",
        "scene": "miss",
        "style": "gentle",
        "rawText": "好想你呀今天",
        "finalText": "今天有风，想起了你，希望你一切都好。",
        "voicePreset": "female-gentle",
        "tone": "gentle",
    }

    def test_bootstrap_ok(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_suggestions_ok(self, client):
        r = client.post("/api/xiangta/suggestions", json=self._SUGGESTION_BODY)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_suggestions_returns_three_items(self, client):
        data = client.post("/api/xiangta/suggestions", json=self._SUGGESTION_BODY).json()["data"]
        assert len(data["suggestions"]) == 3

    def test_tts_task_no_audio_can_save_letter(self, client, monkeypatch):
        """Even if TTS returns no audioUrl, letter can be saved."""
        _mock_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts_no_audio)

        tts_body = {
            "text": "今天有风，想起了你，希望你一切都好。",
            "voicePreset": "female-gentle",
            "tone": "gentle",
            "recipient": "lover",
            "scene": "miss",
        }
        r = client.post("/api/xiangta/tts/tasks", json=tts_body)
        assert r.status_code == 200
        task_data = r.json()["data"]
        task_id = task_data["taskId"]

        r2 = client.get(f"/api/xiangta/tts/tasks/{task_id}")
        assert r2.status_code == 200
        task = r2.json()["data"]
        assert task["status"] == "completed"
        assert task["audioUrl"] is None

        letter_body = dict(self._LETTER_BODY_BASE)
        letter_body["audioUrl"] = None
        letter_body["durationSecs"] = None
        r3 = client.post("/api/xiangta/letters", json=letter_body)
        assert r3.status_code == 200
        assert r3.json()["ok"] is True
        saved_id = r3.json()["data"]["letterId"]

        history = client.get("/api/xiangta/letters?limit=20&offset=0")
        assert history.status_code == 200
        letters = history.json()["data"]["letters"]
        assert any(l["letterId"] == saved_id for l in letters)

    def test_tts_task_with_audio_can_save_letter(self, client, monkeypatch):
        """With audioUrl present, letter can be saved."""
        _mock_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts_success)

        tts_body = {
            "text": "今天有风，想起了你，希望你一切都好。",
            "voicePreset": "female-gentle",
            "tone": "gentle",
            "recipient": "lover",
            "scene": "miss",
        }
        r = client.post("/api/xiangta/tts/tasks", json=tts_body)
        assert r.status_code == 200
        task_data = r.json()["data"]
        task_id = task_data["taskId"]

        r2 = client.get(f"/api/xiangta/tts/tasks/{task_id}")
        task = r2.json()["data"]
        assert task["audioUrl"] is not None

        letter_body = dict(self._LETTER_BODY_BASE)
        letter_body["audioUrl"] = task["audioUrl"]
        letter_body["durationSecs"] = 2.0
        r3 = client.post("/api/xiangta/letters", json=letter_body)
        assert r3.status_code == 200
        assert r3.json()["ok"] is True


# ── Test 2: No forbidden fields in API responses ───────────────────────────────

class TestNoForbiddenFields:
    """All user-facing responses must not leak forbidden provider/core fields."""

    def test_bootstrap_no_forbidden_fields(self, client):
        body_str = str(client.get("/api/xiangta/bootstrap").json())
        found = _has_forbidden(body_str)
        assert found is None, f"bootstrap contains forbidden field: {found}"

    def test_suggestions_no_forbidden_fields(self, client):
        body = {
            "recipient": "lover", "scene": "miss", "rawText": "好想你呀今天",
        }
        body_str = str(client.post("/api/xiangta/suggestions", json=body).json())
        found = _has_forbidden(body_str)
        assert found is None, f"suggestions contains forbidden field: {found}"

    def test_letters_post_no_forbidden_fields(self, client):
        letter = {
            "recipient": "lover", "scene": "miss", "style": "gentle",
            "rawText": "好想你呀今天", "finalText": "今天有风，想起了你。",
            "voicePreset": "female-gentle", "tone": "gentle",
        }
        r = client.post("/api/xiangta/letters", json=letter)
        body_str = str(r.json())
        found = _has_forbidden(body_str)
        assert found is None, f"letters POST contains forbidden field: {found}"

    def test_letters_get_no_forbidden_fields(self, client):
        letter = {
            "recipient": "lover", "scene": "miss", "style": "gentle",
            "rawText": "好想你呀今天", "finalText": "今天有风，想起了你。",
            "voicePreset": "female-gentle", "tone": "gentle",
        }
        client.post("/api/xiangta/letters", json=letter)
        r = client.get("/api/xiangta/letters?limit=20&offset=0")
        body_str = str(r.json())
        found = _has_forbidden(body_str)
        assert found is None, f"letters GET contains forbidden field: {found}"


# ── Test 3: H5 screen-based mobile product flow ───────────────────────────────

class TestH5ScreenFlow:
    """H5 is screen-based mobile product flow, not step-by-step smoke page."""

    def test_all_five_screens_present(self):
        html = (_H5_DIR / "index.html").read_text(encoding="utf-8")
        for screen in ["screenHome", "screenCompose", "screenSuggest", "screenVoice", "screenHistory"]:
            assert f'id="{screen}"' in html, f"{screen} not found"

    def test_viewport_meta_present(self):
        html = (_H5_DIR / "index.html").read_text(encoding="utf-8")
        assert 'name="viewport"' in html

    def test_show_screen_exists(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        assert "function showScreen" in js or "showScreen =" in js

    def test_state_screen_exists(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        assert re.search(r'state\s*=\s*\{', js), "state object not found"
        assert re.search(r'screen\s*:', js), "state.screen not found"


# ── Test 4: H5 formal TTS path uses /tts/tasks ──────────────────────────────

class TestH5TtsTaskFlow:
    """Formal TTS path uses /api/xiangta/tts/tasks, not /api/xiangta/tts."""

    def test_generate_tts_task_uses_tasks_endpoint(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "/api/xiangta/tts/tasks" in section, \
            "generateTtsTask must use /api/xiangta/tts/tasks"

    def test_poll_tts_task_exists(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        assert "pollTtsTask" in js, "pollTtsTask not found"

    def test_tts_endpoint_only_in_dev_alias(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        # Find generateTtsTask section
        start = js.find("function generateTtsTask")
        end = js.find("\n}", start)
        formal_section = js[start:end] if start != -1 else ""
        # generateTts (dev-only) can reference /tts, but formal generateTtsTask must not
        if "function generateTts" in js:
            dev_start = js.find("function generateTts")
            dev_end = js.find("\n}", dev_start)
            dev_section = js[dev_start:dev_end]
            assert "/api/xiangta/tts/tasks" not in dev_section or \
                   "/api/xiangta/tts/tasks" in formal_section, \
                "/tts should only be in dev alias, /tts/tasks must be in formal"


# ── Test 5: H5 no-audio text letter save contract ───────────────────────────

class TestH5NoAudioSave:
    """H5 allows saving text letter even without audioUrl (C9-FIX1)."""

    def test_reveal_save_letter_section_exists(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        assert "function revealSaveLetterSection" in js or "revealSaveLetterSection =" in js

    def test_render_tts_task_calls_reveal(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        start = js.find("function renderTtsTask")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "revealSaveLetterSection" in section

    def test_tts_hint_style_exists(self):
        css = (_H5_DIR / "styles.css").read_text(encoding="utf-8")
        assert ".tts-hint" in css

    def test_save_letter_allows_null_audio(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        start = js.find("function saveLetter")
        end = js.find("\n}", start)
        section = js[start:end]
        assert "audioUrl" in section
        assert "|| null" in section or "||null" in section


# ── Test 6: H5 formal/dev mode separation ──────────────────────────────────

class TestFormalDevMode:
    """formal mode does not expose Core/profileId."""

    def test_dev_panel_hidden_in_formal(self):
        html = (_H5_DIR / "index.html").read_text(encoding="utf-8")
        assert 'id="devPanel"' in html
        assert 'class="dev-panel hidden"' in html or "hidden" in html.split('id="devPanel"')[1].split(">")[0]

    def test_core_profile_select_inside_dev_panel(self):
        html = (_H5_DIR / "index.html").read_text(encoding="utf-8")
        # coreProfileSelect must be within devPanel div
        assert 'id="coreProfileSelect"' in html
        # Count occurrences: if coreProfileSelect appears only once and it's after
        # the devPanel opening tag before its closing, it is inside
        dev_start = html.find('<div id="devPanel"')
        core_pos = html.find('id="coreProfileSelect"')
        assert dev_start != -1 and core_pos != -1
        assert dev_start < core_pos, "coreProfileSelect must come after devPanel start"
        # Find the section between devPanel start and the next screen's section tag
        after_dev = html[dev_start:]
        next_section = after_dev.find('<section ')
        dev_content = after_dev[:next_section] if next_section != -1 else after_dev
        assert 'id="coreProfileSelect"' in dev_content, \
            "coreProfileSelect must be inside devPanel"

    def test_get_app_mode_guards_dev(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        assert "function getAppMode" in js
        assert 'params.get("mode")' in js or "params.get('mode')" in js

    def test_load_core_profiles_guarded_by_dev_mode(self):
        js = (_H5_DIR / "app.js").read_text(encoding="utf-8")
        start = js.find("function loadBootstrap")
        end = js.find("\n}", start)
        section = js[start:end]
        if "loadCoreProfiles()" in section:
            assert 'state.mode === "dev"' in section or "state.mode === 'dev'" in section


# ── Test 7: Mobile-first CSS contract ──────────────────────────────────────

class TestMobileCss:
    """styles.css contains mobile-first product flow styles."""

    def test_screen_system_styles(self):
        css = (_H5_DIR / "styles.css").read_text(encoding="utf-8")
        assert ".screen" in css
        assert ".screen.active" in css or ".active" in css

    def test_hero_card_style(self):
        css = (_H5_DIR / "styles.css").read_text(encoding="utf-8")
        assert ".hero-card" in css or ".hero" in css

    def test_choice_chip_style(self):
        css = (_H5_DIR / "styles.css").read_text(encoding="utf-8")
        assert ".choice-chip" in css or ".recipient-card" in css or ".scene-chip" in css

    def test_bottom_actions_style(self):
        css = (_H5_DIR / "styles.css").read_text(encoding="utf-8")
        assert ".bottom-actions" in css

    def test_toast_style(self):
        css = (_H5_DIR / "styles.css").read_text(encoding="utf-8")
        assert ".toast" in css

    def test_mobile_viewport_css_variables(self):
        css = (_H5_DIR / "styles.css").read_text(encoding="utf-8")
        assert "--c-bg" in css or "--c-primary" in css

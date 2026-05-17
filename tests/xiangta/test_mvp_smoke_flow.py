"""
P17-XIANGTA-MVP-CLOSEOUT-B7 — MVP Smoke Flow Tests

轻量 smoke，验证默认路径稳定，不做复杂 mock 注入。

覆盖：
  - bootstrap 200
  - suggestions 200 + 3 条
  - tts 稳定响应（默认无 Core http_client → 400 no_provider）
  - letters POST→GET 闭环
  - admin/config 200
  - H5 静态文件存在
  - 用户端响应无禁止字段泄露
"""
import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.services.letter_service import clear_letters_for_tests

_H5_DIR = Path(__file__).parent.parent.parent / "apps" / "xiangta-h5"

_USER_FORBIDDEN = {
    "api_key", "minimax_api_key", "mimo_api_key", "MINIMAX_API_KEY",
    "provider_voice_id", "binding_id", "params_json",
    "model_id", "voice_id", "stack_trace",
    "core_profile_id", "profile_id",
}


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_letters():
    clear_letters_for_tests()
    yield
    clear_letters_for_tests()


# ── bootstrap ─────────────────────────────────────────────────────────────────

class TestBootstrapSmoke:

    def test_bootstrap_returns_200(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert r.status_code == 200

    def test_bootstrap_ok_true(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert r.json()["ok"] is True

    def test_bootstrap_has_required_keys(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        for key in ("recipients", "scenes", "voicePresets", "tonePresets", "limits", "providerStatus"):
            assert key in data, f"bootstrap.data missing key: {key}"

    def test_bootstrap_no_forbidden_fields(self, client):
        body = str(client.get("/api/xiangta/bootstrap").json())
        for key in _USER_FORBIDDEN:
            assert key not in body, f"bootstrap response contains forbidden field: {key}"

    def test_bootstrap_no_core_profile_id_in_user_data(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        for preset in data.get("voicePresets", []):
            assert "coreProfileId" not in preset


# ── suggestions ───────────────────────────────────────────────────────────────

class TestSuggestionsSmoke:

    _VALID_BODY = {
        "recipient": "lover",
        "scene": "miss",
        "rawText": "好想你呀今天",
    }

    def test_suggestions_returns_200(self, client):
        r = client.post("/api/xiangta/suggestions", json=self._VALID_BODY)
        assert r.status_code == 200

    def test_suggestions_ok_true(self, client):
        r = client.post("/api/xiangta/suggestions", json=self._VALID_BODY)
        assert r.json()["ok"] is True

    def test_suggestions_returns_three_items(self, client):
        data = client.post("/api/xiangta/suggestions", json=self._VALID_BODY).json()["data"]
        assert len(data["suggestions"]) == 3

    def test_suggestions_items_have_required_fields(self, client):
        items = client.post("/api/xiangta/suggestions", json=self._VALID_BODY).json()["data"]["suggestions"]
        for item in items:
            for field in ("style", "styleLabel", "fitsFor", "text", "charCount"):
                assert field in item, f"suggestion item missing field: {field}"

    def test_suggestions_no_forbidden_fields(self, client):
        body = str(client.post("/api/xiangta/suggestions", json=self._VALID_BODY).json())
        for key in _USER_FORBIDDEN:
            assert key not in body, f"suggestions response contains forbidden field: {key}"


# ── tts (default path) ────────────────────────────────────────────────────────

class TestTtsSmoke:

    _VALID_BODY = {
        "text": "好想你呀今天好想你",
        "voicePreset": "female-gentle",
        "tone": "gentle",
        "recipient": "lover",
        "scene": "miss",
    }

    def test_tts_returns_stable_http_response(self, client):
        r = client.post("/api/xiangta/tts", json=self._VALID_BODY)
        assert r.status_code in (200, 400), (
            f"tts returned unexpected status {r.status_code}: {r.text}"
        )

    def test_tts_no_uncaught_exception(self, client):
        r = client.post("/api/xiangta/tts", json=self._VALID_BODY)
        assert r.status_code != 500, f"tts raised 500: {r.text}"

    def test_tts_default_path_error_has_ok_false_and_kind(self, client):
        r = client.post("/api/xiangta/tts", json=self._VALID_BODY)
        if r.status_code == 400:
            body = r.json()
            assert body.get("ok") is False
            assert "errorKind" in body
            assert "message" in body
        elif r.status_code == 200:
            body = r.json()
            assert body.get("ok") is True
            assert "taskId" in body["data"]
            assert "status" in body["data"]


# ── letters ───────────────────────────────────────────────────────────────────

class TestLettersSmoke:

    _VALID_LETTER = {
        "recipient": "lover",
        "scene": "miss",
        "style": "gentle",
        "voicePreset": "female-gentle",
        "tone": "gentle",
        "rawText": "好想你呀今天",
        "finalText": "今天有风，想起了你，希望你一切都好。",
        "title": "小风",
    }

    def test_create_letter_returns_200(self, client):
        r = client.post("/api/xiangta/letters", json=self._VALID_LETTER)
        assert r.status_code == 200

    def test_create_letter_ok_true(self, client):
        r = client.post("/api/xiangta/letters", json=self._VALID_LETTER)
        assert r.json()["ok"] is True

    def test_create_letter_returns_id(self, client):
        data = client.post("/api/xiangta/letters", json=self._VALID_LETTER).json()["data"]
        assert "letterId" in data
        assert data["letterId"].startswith("L_")

    def test_list_letters_returns_200(self, client):
        client.post("/api/xiangta/letters", json=self._VALID_LETTER)
        r = client.get("/api/xiangta/letters")
        assert r.status_code == 200

    def test_list_letters_sees_created_record(self, client):
        letter_id = client.post("/api/xiangta/letters", json=self._VALID_LETTER).json()["data"]["letterId"]
        letters = client.get("/api/xiangta/letters").json()["data"]["letters"]
        ids = [item["letterId"] for item in letters]
        assert letter_id in ids

    def test_letters_no_forbidden_fields(self, client):
        body = str(client.post("/api/xiangta/letters", json=self._VALID_LETTER).json())
        for key in _USER_FORBIDDEN:
            assert key not in body, f"letters response contains forbidden field: {key}"


# ── admin config ──────────────────────────────────────────────────────────────

class TestAdminConfigSmoke:

    def test_admin_config_returns_200(self, client):
        r = client.get("/api/xiangta/admin/config")
        assert r.status_code == 200

    def test_admin_config_ok_true(self, client):
        r = client.get("/api/xiangta/admin/config")
        assert r.json()["ok"] is True

    def test_admin_config_has_voice_mappings(self, client):
        data = client.get("/api/xiangta/admin/config").json()["data"]
        assert "voiceMappings" in data
        assert len(data["voiceMappings"]) > 0

    def test_admin_config_has_tone_presets(self, client):
        data = client.get("/api/xiangta/admin/config").json()["data"]
        assert "tonePresets" in data
        assert len(data["tonePresets"]) > 0

    def test_admin_config_no_api_key_fields(self, client):
        body = str(client.get("/api/xiangta/admin/config").json())
        for key in ("api_key", "minimax_api_key", "MINIMAX_API_KEY", "stack_trace", "params_json"):
            assert key not in body, f"admin/config exposes forbidden field: {key}"

    def test_bootstrap_no_core_profile_id(self, client):
        r = client.get("/api/xiangta/bootstrap")
        data = r.json()["data"]
        for preset in data.get("voicePresets", []):
            assert "coreProfileId" not in preset, "voicePresets should not expose coreProfileId"


# ── H5 static ─────────────────────────────────────────────────────────────────

class TestH5StaticSmoke:

    def test_index_html_exists(self):
        assert (_H5_DIR / "index.html").exists()

    def test_app_js_exists(self):
        assert (_H5_DIR / "app.js").exists()

    def test_styles_css_exists(self):
        assert (_H5_DIR / "styles.css").exists()

    def test_serve_py_exists(self):
        assert (_H5_DIR / "serve.py").exists()

    def test_design_reference_exists(self):
        assert (_H5_DIR / "DESIGN_REFERENCE.md").exists()

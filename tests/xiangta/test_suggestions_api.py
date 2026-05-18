"""
P17-XIANGTA-COPYWRITING-B5-1 — POST /api/xiangta/suggestions API 集成测试
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router

FORBIDDEN_KEYS = {
    "provider", "model", "profile_id", "api_key",
    "coreProfileId", "core_profile_id", "provider_voice_id",
    "binding_id", "params_json", "voice_id", "model_id",
}

_REQUEST = {
    "recipient": "lover",
    "scene": "miss",
    "rawText": "我今天突然很想你",
}


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _collect_keys(obj, seen=None) -> set:
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


# ── 基本响应 ──────────────────────────────────────────────────────────────────

class TestSuggestionsBasic:

    def test_status_200(self, client):
        r = client.post("/api/xiangta/suggestions", json=_REQUEST)
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.post("/api/xiangta/suggestions", json=_REQUEST)
        assert r.json()["ok"] is True

    def test_has_data(self, client):
        r = client.post("/api/xiangta/suggestions", json=_REQUEST)
        assert "data" in r.json()

    def test_summary_non_empty(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        assert data["summary"]

    def test_intent_non_empty(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        assert data["intent"]

    def test_suggestions_length_3(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        assert len(data["suggestions"]) == 3

    def test_suggestions_styles_correct(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        styles = {s["style"] for s in data["suggestions"]}
        assert styles == {"restrained", "gentle", "sincere"}

    def test_each_suggestion_has_style(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        for s in data["suggestions"]:
            assert "style" in s

    def test_each_suggestion_has_style_label(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        for s in data["suggestions"]:
            assert "styleLabel" in s and s["styleLabel"]

    def test_each_suggestion_has_fits_for(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        for s in data["suggestions"]:
            assert "fitsFor" in s and s["fitsFor"]

    def test_each_suggestion_has_text(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        for s in data["suggestions"]:
            assert "text" in s and s["text"]

    def test_each_suggestion_has_char_count(self, client):
        data = client.post("/api/xiangta/suggestions", json=_REQUEST).json()["data"]
        for s in data["suggestions"]:
            assert "charCount" in s
            assert s["charCount"] == len(s["text"]), (
                f"charCount={s['charCount']} != len(text)={len(s['text'])}"
            )


# ── 输入验证 ──────────────────────────────────────────────────────────────────

class TestSuggestionsValidation:

    def test_raw_text_too_short_returns_422(self, client):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "lover", "scene": "miss", "rawText": "ab"
        })
        assert r.status_code == 422

    def test_missing_field_returns_422(self, client):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "lover", "scene": "miss"
        })
        assert r.status_code == 422

    def test_invalid_recipient_returns_422(self, client):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "alien", "scene": "miss", "rawText": "我今天很想你"
        })
        assert r.status_code == 422

    def test_invalid_scene_returns_422(self, client):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "lover", "scene": "birthday", "rawText": "我今天很想你"
        })
        assert r.status_code == 422


# ── 安全边界 ──────────────────────────────────────────────────────────────────

class TestSuggestionsSecurity:

    def test_no_forbidden_keys_in_response(self, client):
        body = client.post("/api/xiangta/suggestions", json=_REQUEST).json()
        keys = _collect_keys(body)
        bad = keys & FORBIDDEN_KEYS
        assert not bad, f"suggestions 响应包含禁止字段：{bad}"

    def test_llm_failed_returns_flat_error(self, monkeypatch):
        """LlmFailedError → 400 flat error contract (no detail)."""
        from src.xiangta.services.copywriting_service import CopywritingService
        from src.xiangta.services.error_translator import LlmFailedError

        async def raise_llm_failed(*args, **kwargs):
            raise LlmFailedError()

        monkeypatch.setattr(CopywritingService, "generate_suggestions", raise_llm_failed)
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        r = client.post("/api/xiangta/suggestions", json=_REQUEST)
        assert r.status_code == 400
        body = r.json()
        assert body["ok"] is False
        assert body["errorKind"] == "llm_failed"
        assert "detail" not in body


# ── 多场景 ────────────────────────────────────────────────────────────────────

class TestSuggestionsScenes:

    @pytest.mark.parametrize("scene", ["miss", "sorry", "thanks", "comfort", "night"])
    def test_all_scenes_return_200(self, client, scene):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "lover",
            "scene": scene,
            "rawText": "我想说一些话",
        })
        assert r.status_code == 200

    @pytest.mark.parametrize("recipient", ["lover", "family", "friend", "self"])
    def test_all_recipients_return_200(self, client, recipient):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": recipient,
            "scene": "miss",
            "rawText": "我今天很想你",
        })
        assert r.status_code == 200

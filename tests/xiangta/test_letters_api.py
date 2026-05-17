"""
P17-XIANGTA-LETTERS-B6-1 — Letters API 集成测试

POST /api/xiangta/letters
GET  /api/xiangta/letters
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.services.letter_service import clear_letters_for_tests

FORBIDDEN_KEYS = {
    "provider", "model", "profile_id", "api_key",
    "coreProfileId", "core_profile_id", "provider_voice_id",
    "binding_id", "params_json", "voice_id", "model_id",
}

_CREATE_BODY = {
    "recipient": "lover",
    "scene": "miss",
    "style": "gentle",
    "rawText": "我今天突然很想你",
    "finalText": "有些挂念你，我今天突然很想你，悄悄想了一会儿。",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "audioUrl": "/api/voice/assets/audio_123/download",
    "durationSecs": 2.4,
    "title": "想你了",
}


@pytest.fixture(autouse=True)
def clean_store():
    clear_letters_for_tests()
    yield
    clear_letters_for_tests()


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


# ── POST /letters ─────────────────────────────────────────────────────────────

class TestCreateLetter:

    def test_status_200(self, client):
        r = client.post("/api/xiangta/letters", json=_CREATE_BODY)
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.post("/api/xiangta/letters", json=_CREATE_BODY)
        assert r.json()["ok"] is True

    def test_returns_letter_id(self, client):
        r = client.post("/api/xiangta/letters", json=_CREATE_BODY)
        data = r.json()["data"]
        assert "letterId" in data
        assert data["letterId"].startswith("L_")

    def test_returns_created_at(self, client):
        r = client.post("/api/xiangta/letters", json=_CREATE_BODY)
        data = r.json()["data"]
        assert "createdAt" in data
        assert "T" in data["createdAt"]

    def test_missing_required_field_returns_422(self, client):
        body = {k: v for k, v in _CREATE_BODY.items() if k != "recipient"}
        r = client.post("/api/xiangta/letters", json=body)
        assert r.status_code == 422

    def test_empty_raw_text_returns_422(self, client):
        r = client.post("/api/xiangta/letters", json={**_CREATE_BODY, "rawText": ""})
        assert r.status_code == 422

    def test_empty_final_text_returns_422(self, client):
        r = client.post("/api/xiangta/letters", json={**_CREATE_BODY, "finalText": ""})
        assert r.status_code == 422

    def test_audio_url_optional(self, client):
        body = {**_CREATE_BODY, "audioUrl": None}
        r = client.post("/api/xiangta/letters", json=body)
        assert r.status_code == 200

    def test_no_forbidden_keys_in_response(self, client):
        r = client.post("/api/xiangta/letters", json=_CREATE_BODY)
        keys = _collect_keys(r.json())
        bad = keys & FORBIDDEN_KEYS
        assert not bad, f"POST /letters 响应包含禁止字段：{bad}"


# ── GET /letters ──────────────────────────────────────────────────────────────

class TestListLetters:

    def test_status_200(self, client):
        r = client.get("/api/xiangta/letters")
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.get("/api/xiangta/letters")
        assert r.json()["ok"] is True

    def test_empty_initially(self, client):
        r = client.get("/api/xiangta/letters")
        data = r.json()["data"]
        assert data["letters"] == []
        assert data["total"] == 0

    def test_post_then_get_shows_record(self, client):
        client.post("/api/xiangta/letters", json=_CREATE_BODY)
        r = client.get("/api/xiangta/letters")
        data = r.json()["data"]
        assert data["total"] == 1
        assert len(data["letters"]) == 1

    def test_letter_has_required_fields(self, client):
        client.post("/api/xiangta/letters", json=_CREATE_BODY)
        letter = client.get("/api/xiangta/letters").json()["data"]["letters"][0]
        assert "letterId" in letter
        assert "recipient" in letter
        assert "scene" in letter
        assert "style" in letter
        assert "rawText" in letter
        assert "finalText" in letter
        assert "voicePreset" in letter
        assert "tone" in letter
        assert "createdAt" in letter
        assert "favorited" in letter
        assert "openCount" in letter

    def test_newest_first(self, client):
        r1 = client.post("/api/xiangta/letters", json=_CREATE_BODY).json()["data"]
        r2 = client.post("/api/xiangta/letters", json={**_CREATE_BODY, "title": "第二条"}).json()["data"]
        letters = client.get("/api/xiangta/letters").json()["data"]["letters"]
        assert letters[0]["letterId"] == r2["letterId"]
        assert letters[1]["letterId"] == r1["letterId"]

    def test_limit_query_param(self, client):
        for _ in range(5):
            client.post("/api/xiangta/letters", json=_CREATE_BODY)
        r = client.get("/api/xiangta/letters?limit=2")
        data = r.json()["data"]
        assert len(data["letters"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2

    def test_offset_query_param(self, client):
        for i in range(4):
            client.post("/api/xiangta/letters", json={**_CREATE_BODY, "title": f"第{i}条"})
        r = client.get("/api/xiangta/letters?limit=2&offset=2")
        data = r.json()["data"]
        assert len(data["letters"]) == 2
        assert data["offset"] == 2

    def test_response_has_total_limit_offset(self, client):
        r = client.get("/api/xiangta/letters")
        data = r.json()["data"]
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_no_forbidden_keys_in_response(self, client):
        client.post("/api/xiangta/letters", json=_CREATE_BODY)
        r = client.get("/api/xiangta/letters")
        keys = _collect_keys(r.json())
        bad = keys & FORBIDDEN_KEYS
        assert not bad, f"GET /letters 响应包含禁止字段：{bad}"

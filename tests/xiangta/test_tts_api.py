"""
P17-XIANGTA-A2 — POST /api/xiangta/tts API 层测试

验证：
  - 正常 dry-run 返回 200 + ok: True + 产品层字段
  - 响应不包含 voice_id/model_id/sample_rate/bitrate/api_key
  - 错误 voicePreset（Pydantic 拦截）返回 422
  - 错误 tone（Pydantic 拦截）返回 422
  - text 超长（Pydantic 拦截）返回 422
  - text 格式合法但业务错误返回 400（使用 disabled 预设）
  - route 不依赖真实 Provider（dry-run 全程无网络 I/O）
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
}

VALID_PAYLOAD = {
    "text": "想念你",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "recipient": "lover",
    "scene": "miss",
}


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


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


# ── 正常 dry-run ─────────────────────────────────────────────────────────────

class TestTtsDryRunHappyPath:

    def test_status_200(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["ok"] is True

    def test_has_data(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert "data" in r.json()

    def test_has_task_id(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert "taskId" in r.json()["data"]

    def test_task_id_starts_with_dryrun(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["data"]["taskId"].startswith("dryrun_")

    def test_status_is_dry_run(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["data"]["status"] == "dry_run"

    def test_audio_url_is_null(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["data"]["audioUrl"] is None

    def test_char_count_correct(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["data"]["charCount"] == len(VALID_PAYLOAD["text"])

    def test_voice_preset_in_response(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["data"]["voicePreset"] == "female-gentle"

    def test_tone_in_response(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["data"]["tone"] == "gentle"

    def test_has_contract(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert "contract" in r.json()["data"]
        assert r.json()["data"]["contract"]["coreBindingKey"] == "xiangta_female_gentle"

    def test_no_forbidden_keys_in_response(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        all_keys = _collect_keys(r.json())
        bad = all_keys & FORBIDDEN_KEYS
        assert not bad, f"POST /tts 响应包含禁止字段：{bad}"


# ── 每次请求 taskId 唯一 ──────────────────────────────────────────────────────

class TestTaskIdUniqueness:

    def test_two_calls_return_different_task_ids(self, client):
        r1 = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        r2 = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r1.json()["data"]["taskId"] != r2.json()["data"]["taskId"]


# ── Pydantic 验证错误（422）────────────────────────────────────────────────────

class TestPydanticValidationErrors:

    def test_invalid_voice_preset_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "voicePreset": "nonexistent-voice"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_invalid_tone_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "tone": "nonexistent-tone"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_text_too_long_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "text": "字" * 501}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_empty_text_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "text": ""}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_invalid_recipient_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "recipient": "unknown-person"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_invalid_scene_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "scene": "unknown-scene"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_missing_required_field_returns_422(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "text"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422


# ── 业务错误响应格式 ──────────────────────────────────────────────────────────

class TestBusinessErrorFormat:

    def test_error_response_has_ok_false(self, client, monkeypatch):
        """模拟 preset_mapper 抛出 PresetMappingError，验证 400 错误格式。"""
        from src.xiangta.services import preset_mapper as pm_module
        from src.xiangta.services.preset_mapper import PresetMappingError

        original_resolve = pm_module.PresetMapper.resolve_binding

        def broken_resolve(self, *args, **kwargs):
            raise PresetMappingError("voicePreset 'male-mature' 已禁用")

        monkeypatch.setattr(pm_module.PresetMapper, "resolve_binding", broken_resolve)

        payload = {**VALID_PAYLOAD, "voicePreset": "male-mature"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 400
        body = r.json()
        assert body["ok"] is False
        assert "errorKind" in body
        assert "message" in body

    def test_error_response_no_forbidden_keys(self, client, monkeypatch):
        from src.xiangta.services import preset_mapper as pm_module
        from src.xiangta.services.preset_mapper import PresetMappingError

        def broken_resolve(self, *args, **kwargs):
            raise PresetMappingError("已禁用")

        monkeypatch.setattr(pm_module.PresetMapper, "resolve_binding", broken_resolve)

        payload = {**VALID_PAYLOAD, "voicePreset": "male-mature"}
        r = client.post("/api/xiangta/tts", json=payload)
        all_keys = _collect_keys(r.json())
        bad = all_keys & FORBIDDEN_KEYS
        assert not bad, f"错误响应包含禁止字段：{bad}"

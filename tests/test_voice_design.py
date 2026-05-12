from fastapi.testclient import TestClient


def test_design_voice(test_app):
    """POST /api/voice/design/create with mock returns voice_id."""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "成熟女性，温柔知性", "preview_text": "今天天气真好"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "voice_id" in data
    assert data["message"] == "设计成功"


def test_design_voice_custom_id(test_app):
    """自定义voice_id被正确返回。"""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "低沉男声", "preview_text": "测试文本", "voice_id": "my_custom_voice"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    assert resp.json()["voice_id"] == "my_custom_voice"


def test_design_empty_prompt(test_app):
    """空prompt返回422。"""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "", "preview_text": "测试"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_design_preview_text_too_long(test_app):
    """preview_text超500字返回422。"""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "测试", "preview_text": "a" * 501},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_voice_design_provider_signature_has_no_model():
    """design_voice() adapter method has no 'model' parameter (official API does not support it)."""
    import inspect
    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    sig = inspect.signature(MiniMaxSpeechAdapter.design_voice)
    assert "model" not in sig.parameters, \
        f"design_voice should not have 'model' parameter, but has: {list(sig.parameters.keys())}"
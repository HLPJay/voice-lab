from fastapi.testclient import TestClient


def test_upload_clone_audio(test_app):
    """POST /api/voice/clone/upload with mock file returns file_id."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/upload",
        files={"file": ("test.mp3", b"fake_audio_data")},
        data={"purpose": "voice_clone", "provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["file_id"] == 99999
    assert data["filename"] == "test.mp3"
    assert data["purpose"] == "voice_clone"


def test_upload_prompt_audio(test_app):
    """POST /api/voice/clone/upload with purpose=prompt_audio succeeds."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/upload",
        files={"file": ("prompt.wav", b"prompt_data")},
        data={"purpose": "prompt_audio", "provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["purpose"] == "prompt_audio"
    assert data["bytes"] == len(b"prompt_data")


def test_clone_voice(test_app):
    """POST /api/voice/clone/create returns voice_id."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={"voice_id": "test_clone_voice_01", "file_id": 99999},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "test_clone_voice_01"
    assert "message" in data


def test_clone_voice_with_prompt(test_app):
    """Clone with prompt_file_id and prompt_text succeeds."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={
            "voice_id": "test_clone_with_prompt",
            "file_id": 99999,
            "prompt_file_id": 88888,
            "prompt_text": "这是一段参考文本。",
            "preview_text": "试听文本。",
            "model": "speech-2.8-hd",
        },
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "test_clone_with_prompt"


def test_upload_invalid_purpose(test_app):
    """purpose不是voice_clone/prompt_audio时返回错误。"""
    resp = TestClient(test_app).post(
        "/api/voice/clone/upload",
        files={"file": ("test.mp3", b"data")},
        data={"purpose": "invalid_purpose", "provider": "mock"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert "Invalid purpose" in data["error"]["message"]


def test_clone_invalid_voice_id(test_app):
    """voice_id不符合正则时返回422。"""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={"voice_id": "123invalid", "file_id": 99999},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_clone_sensitive_bool_true_rejected(test_app, seed_mock_binding):
    """MiniMax API response with input_sensitive=True raises ProviderError."""
    from unittest.mock import patch
    from app.core.errors import ProviderError

    class SensitiveAdapter:
        async def clone_voice(self, request: dict) -> dict:
            # Simulate MiniMax response where content safety check fails
            raise ProviderError(
                "内容安全检测未通过",
                "input_sensitive=True, input_sensitive_type=1",
            )

    with patch("app.services.voice_clone_service.get_provider", return_value=SensitiveAdapter()):
        resp = TestClient(test_app).post(
            "/api/voice/clone/create",
            json={"voice_id": "test_sensitive_01", "file_id": 99999},
            params={"provider": "mock"},
        )
    assert resp.status_code == 400
    data = resp.json()
    assert "内容安全" in data["error"]["message"] or \
           "sensitive" in data["error"]["message"].lower()


def test_clone_prompt_pair_required(test_app):
    """Only prompt_file_id without prompt_text → 422 ValidationError."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={
            "voice_id": "test_prompt_pair_01",
            "file_id": 99999,
            "prompt_file_id": 88888,
            # intentionally omit prompt_text
        },
        params={"provider": "mock"},
    )
    assert resp.status_code == 422
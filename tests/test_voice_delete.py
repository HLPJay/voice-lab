from fastapi.testclient import TestClient


def test_delete_cloned_voice(test_app):
    """正常删除voice_cloning类型。"""
    resp = TestClient(test_app).post(
        "/api/voice/voices/delete",
        json={"provider_voice_id": "mock_clone_soft", "voice_type": "voice_cloning"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "mock_clone_soft"
    assert data["deleted"] is True


def test_delete_generated_voice(test_app):
    """正常删除voice_generation类型。"""
    resp = TestClient(test_app).post(
        "/api/voice/voices/delete",
        json={"provider_voice_id": "mock_generated_warm", "voice_type": "voice_generation"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "mock_generated_warm"


def test_delete_system_voice_rejected(test_app):
    """voice_type=system被422拒绝。"""
    resp = TestClient(test_app).post(
        "/api/voice/voices/delete",
        json={"provider_voice_id": "some_voice", "voice_type": "system"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_delete_empty_voice_id(test_app):
    """空voice_id被422拒绝。"""
    resp = TestClient(test_app).post(
        "/api/voice/voices/delete",
        json={"provider_voice_id": "", "voice_type": "voice_cloning"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422
import pytest


def test_render_with_mock_provider(temp_db, seed_profile):
    import os
    import tempfile
    from sqlmodel import Session, create_engine
    from fastapi.testclient import TestClient

    engine, db_path = temp_db
    # Override db
    from app.core import database
    original_engine = database.engine
    database.engine = engine

    from app.main import app

    # Override lifespan to avoid re-initializing
    client = TestClient(app)

    response = client.post(
        "/api/voice/render",
        json={
            "text": "我一直以为，是生活太难。后来才发现，真正让我害怕的是那个一直在逃避的自己。",
            "profile_id": "deep_night_programmer",
            "provider": "mock",
            "need_subtitle": True,
        },
    )
    database.engine = original_engine

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "success"
    assert data["provider"] == "mock"
    assert data["audio_asset"]["id"].startswith("audio_")
    assert data["audio_asset"]["url"]
    assert data["audio_asset"]["duration_ms"] is not None


def test_render_profile_not_found(temp_db):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/voice/render",
        json={
            "text": "测试文本",
            "profile_id": "nonexistent_profile",
            "provider": "mock",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFILE_NOT_FOUND"


def test_render_empty_text(temp_db):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/voice/render",
        json={
            "text": "",
            "profile_id": "deep_night_programmer",
        },
    )
    assert response.status_code == 422

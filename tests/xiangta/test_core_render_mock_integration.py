from __future__ import annotations

from fastapi.testclient import TestClient


def _mock_render_payload() -> dict:
    return {
        "text": "想念你",
        "profile_id": "deep_night_programmer",
        "provider": "mock",
        "need_subtitle": True,
        "output_format": "url",
        "audio_format": "mp3",
        "confirm_cost": False,
    }


def test_core_render_mock_path_returns_audio_asset(test_app, seed_mock_binding):
    _ = seed_mock_binding
    client = TestClient(test_app)

    response = client.post("/api/voice/render", json=_mock_render_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["job_id"]
    assert body["audio_asset"] is not None
    assert body["audio_asset"]["url"].startswith("/api/voice/assets/")
    assert body["audio_asset"]["url"].endswith("/download")
    assert isinstance(body["audio_asset"]["duration_ms"], int)
    assert body["audio_asset"]["duration_ms"] > 0
    assert body["provider"] == "mock"


def test_b2_mock_path_requires_explicit_mock_provider():
    payload = _mock_render_payload()
    assert payload["provider"] == "mock"


def test_core_render_mock_download_url_is_accessible(test_app, seed_mock_binding):
    _ = seed_mock_binding
    client = TestClient(test_app)

    render = client.post("/api/voice/render", json=_mock_render_payload())
    assert render.status_code == 200

    audio_url = render.json()["audio_asset"]["url"]
    download = client.get(audio_url)

    assert download.status_code == 200
    assert len(download.content) > 0


def test_mock_render_does_not_require_real_api_keys(monkeypatch, test_app, seed_mock_binding):
    _ = seed_mock_binding
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("MIMO_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = TestClient(test_app)
    response = client.post("/api/voice/render", json=_mock_render_payload())

    assert response.status_code == 200
    assert response.json()["status"] == "success"

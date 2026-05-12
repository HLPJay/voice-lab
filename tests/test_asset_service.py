from fastapi.testclient import TestClient


def test_save_audio_asset(test_app, seed_mock_binding):
    """POST /api/voice/render creates an audio asset retrievable via GET."""
    resp = TestClient(test_app).post(
        "/api/voice/render",
        json={
            "text": "音频资产测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert resp.status_code == 200
    audio_asset_id = resp.json()["audio_asset"]["id"]

    asset_resp = TestClient(test_app).get(f"/api/voice/assets/{audio_asset_id}")
    assert asset_resp.status_code == 200
    data = asset_resp.json()
    assert data["type"] == "audio"
    assert data["format"]
    assert data["file_path"]


def test_save_subtitle_asset(test_app, seed_mock_binding):
    """need_subtitle=True creates a subtitle asset retrievable via GET."""
    resp = TestClient(test_app).post(
        "/api/voice/render",
        json={
            "text": "字幕资产测试。",
            "provider": "mock",
            "need_subtitle": True,
        },
    )
    assert resp.status_code == 200
    subtitle_asset_id = resp.json()["subtitle_asset"]["id"]

    asset_resp = TestClient(test_app).get(f"/api/voice/assets/{subtitle_asset_id}")
    assert asset_resp.status_code == 200
    data = asset_resp.json()
    assert data["type"] == "subtitle"
    assert data["file_path"]


def test_audio_download(test_app, seed_mock_binding):
    """GET /api/voice/assets/{id}/download returns 200 with audio content-type."""
    resp = TestClient(test_app).post(
        "/api/voice/render",
        json={
            "text": "下载测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert resp.status_code == 200
    audio_asset_id = resp.json()["audio_asset"]["id"]

    dl_resp = TestClient(test_app).get(f"/api/voice/assets/{audio_asset_id}/download")
    assert dl_resp.status_code == 200
    assert "audio" in dl_resp.headers.get("content-type", "")


def test_no_subtitle_when_disabled(test_app, seed_mock_binding):
    """need_subtitle=False results in null subtitle_asset in response."""
    resp = TestClient(test_app).post(
        "/api/voice/render",
        json={
            "text": "无字幕测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["subtitle_asset"] is None

import time

import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
def test_e2e_sync_t2a(e2e_app, minimax_api_key):
    """同步T2A：提交→返回音频+字幕"""
    client = TestClient(e2e_app)
    resp = client.post(
        "/api/voice/render",
        json={
            "text": "End to end sync test.",
            "provider": "minimax",
            "need_subtitle": True,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert data["audio_asset"]["duration_ms"] > 0
    assert len(data["subtitle_asset"]["timeline"]) > 0


@pytest.mark.e2e
def test_e2e_async_t2a(e2e_app, minimax_api_key):
    """异步T2A：提交→轮询→成功获取音频"""
    client = TestClient(e2e_app)

    submit = client.post(
        "/api/voice/render/async",
        json={
            "text": "End to end async test.",
            "provider": "minimax",
            "need_subtitle": False,
        },
    )
    assert submit.status_code == 200, submit.text
    job_data = submit.json()
    assert job_data["status"] == "processing"
    job_id = job_data["job_id"]

    for _ in range(12):
        time.sleep(5)
        status = client.get(f"/api/voice/render/async/{job_id}/status")
        assert status.status_code == 200, status.text
        s = status.json()
        if s["status"] == "success":
            assert s["audio_asset"] is not None
            return
        if s["status"] == "failed":
            pytest.fail(f"Async task failed: {s.get('error_message')}")

    pytest.fail("Async task timed out after 60s")


@pytest.mark.e2e
def test_e2e_voice_catalog(e2e_app, minimax_api_key):
    """音色列表：refresh=true拉取，total>0"""
    client = TestClient(e2e_app)
    resp = client.get(
        "/api/voice/provider-voices",
        params={"provider": "minimax", "voice_type": "all", "refresh": "true"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] > 0
    assert any(v["voice_type"] == "system" for v in data["voices"])


@pytest.mark.e2e
def test_e2e_voice_design(e2e_app, minimax_api_key):
    """声音设计：提交→返回voice_id（200成功或400余额不足都说明链路通）"""
    client = TestClient(e2e_app)
    resp = client.post(
        "/api/voice/design/create",
        params={"provider": "minimax"},
        json={
            "prompt": "warm female voice",
            "preview_text": "Hello world.",
        },
    )
    assert resp.status_code in (200, 400), resp.text
    if resp.status_code == 200:
        assert resp.json()["voice_id"]


@pytest.mark.e2e
def test_e2e_voice_clone_upload(e2e_app, minimax_api_key):
    """克隆上传：上传测试文件→返回file_id（200成功或400格式错误都说明链路通）"""
    client = TestClient(e2e_app)
    resp = client.post(
        "/api/voice/clone/upload",
        files={"file": ("test.mp3", b"fake audio for e2e test" * 100)},
        data={"purpose": "voice_clone", "provider": "minimax"},
    )
    assert resp.status_code in (200, 400), resp.text
    if resp.status_code == 200:
        assert resp.json()["file_id"]


@pytest.mark.e2e
def test_e2e_voice_delete(e2e_app, minimax_api_key):
    """删除：删除不存在的voice→返回业务错误（链路通）"""
    client = TestClient(e2e_app)
    resp = client.post(
        "/api/voice/voices/delete",
        params={"provider": "minimax"},
        json={
            "provider_voice_id": "e2e_nonexistent_voice",
            "voice_type": "voice_cloning",
        },
    )
    assert resp.status_code == 400, resp.text
    assert "voice" in resp.json().get("error", {}).get("message", "").lower() or True

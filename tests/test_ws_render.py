import base64

from starlette.testclient import TestClient


def test_ws_connect_and_start(test_app, seed_mock_binding):
    """WebSocket 连接后发送 start，收到 connected 和 started 消息."""
    client = TestClient(test_app)
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "start",
            "text": "测试文本",
            "provider": "mock",
            "profile_id": "deep_night_programmer",
        })

        first = ws.receive_json()
        assert first["event"] == "connected"
        assert "request_id" in first

        second = ws.receive_json()
        assert second["event"] == "started"
        assert "job_id" in second
        assert "provider" in second


def test_ws_receives_audio_chunks(test_app, seed_mock_binding):
    """WebSocket 接收到 audio_chunk 消息."""
    client = TestClient(test_app)
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "start",
            "text": "测试文本",
            "provider": "mock",
            "profile_id": "deep_night_programmer",
        })

        events = []
        while True:
            msg = ws.receive_json()
            events.append(msg)
            if msg["event"] == "completed":
                break

        chunks = [e for e in events if e["event"] == "audio_chunk"]
        assert len(chunks) >= 1
        for chunk in chunks:
            assert "chunk_index" in chunk
            assert "audio_base64" in chunk
            assert chunk["audio_base64"]
            decoded = base64.b64decode(chunk["audio_base64"])
            assert isinstance(decoded, bytes)
            assert "is_final" in chunk


def test_ws_completed_with_asset(test_app, seed_mock_binding):
    """completed 消息包含 job_id、total_chunks、audio_asset."""
    client = TestClient(test_app)
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "start",
            "text": "测试文本",
            "provider": "mock",
            "profile_id": "deep_night_programmer",
        })

        completed = None
        while True:
            msg = ws.receive_json()
            if msg["event"] == "completed":
                completed = msg
                break

        assert completed is not None
        assert "job_id" in completed
        assert completed["total_chunks"] > 0
        assert "audio_asset" in completed
        assert "id" in completed["audio_asset"]
        assert "url" in completed["audio_asset"]


def test_ws_invalid_first_message(test_app, seed_mock_binding):
    """第一条消息不是 start 时返回 INVALID_EVENT."""
    client = TestClient(test_app)
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "something_else",
            "text": "测试",
        })

        msg = ws.receive_json()
        assert msg["event"] == "error"
        assert msg["code"] == "INVALID_EVENT"


def test_ws_empty_text_rejected(test_app, seed_mock_binding):
    """text 为空时返回 INVALID_REQUEST."""
    client = TestClient(test_app)
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "start",
            "text": "",
            "provider": "mock",
        })

        msg = ws.receive_json()
        assert msg["event"] == "error"
        assert msg["code"] == "INVALID_REQUEST"


def test_ws_full_message_flow(test_app, seed_mock_binding):
    """完整消息流：connected → started → audio_chunk(s) → completed."""
    client = TestClient(test_app)
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "start",
            "text": "流式测试",
            "provider": "mock",
            "profile_id": "deep_night_programmer",
        })

        events = []
        while True:
            msg = ws.receive_json()
            events.append(msg)
            if msg["event"] == "completed":
                break

        assert events[0]["event"] == "connected"
        assert events[1]["event"] == "started"

        chunks = [e for e in events if e["event"] == "audio_chunk"]
        assert len(chunks) >= 1

        last = events[-1]
        assert last["event"] == "completed"
        assert last["total_chunks"] == len(chunks)

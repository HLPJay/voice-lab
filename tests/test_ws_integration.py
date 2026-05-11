import base64
from pathlib import Path

from sqlmodel import select
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob


def collect_ws_events(client, text="测试文本", provider="mock", profile_id="deep_night_programmer"):
    """通过 WebSocket 完成一次流式生成，返回所有事件列表。"""
    events = []
    with client.websocket_connect("/api/voice/ws/render") as ws:
        ws.send_json({
            "event": "start",
            "text": text,
            "provider": provider,
            "profile_id": profile_id,
            "output_format": "mp3",
        })
        try:
            while True:
                msg = ws.receive_json()
                events.append(msg)
                if msg["event"] in ("completed", "error"):
                    break
        except WebSocketDisconnect:
            # Connection closed (e.g. after error + close, or profile not found)
            pass
    return events


def test_ws_stream_creates_job_with_correct_type(test_app, seed_mock_binding, ws_patched_session, session):
    """WebSocket 流式生成在数据库中创建 stream_render 类型的 VoiceJob."""
    client = TestClient(test_app)
    events = collect_ws_events(client, text="集成测试文本", provider="mock")

    completed = next((e for e in events if e["event"] == "completed"), None)
    assert completed is not None, f"No completed event. Events: {events}"

    # Use a fresh session from the same engine as `session` to read committed data
    from sqlmodel import Session
    engine = session.bind.engine
    with Session(engine) as verify_sess:
        job = verify_sess.exec(select(VoiceJob).where(VoiceJob.id == completed["job_id"])).first()
        assert job is not None
        assert job.job_type == "stream_render"
        assert job.status == "success"
        assert job.provider == "mock"
        assert "集成测试文本" in (job.input_text or "")
        assert job.render_plan_json is not None


def test_ws_stream_saves_audio_asset_on_disk(test_app, seed_mock_binding, ws_patched_session, session):
    """流式生成完成后音频文件实际写入磁盘."""
    client = TestClient(test_app)
    events = collect_ws_events(client, text="集成测试", provider="mock")

    completed = next((e for e in events if e["event"] == "completed"), None)
    assert completed is not None

    asset_id = completed.get("audio_asset", {}).get("id")
    assert asset_id is not None

    from sqlmodel import Session
    engine = session.bind.engine
    with Session(engine) as verify_sess:
        asset = verify_sess.exec(select(AudioAsset).where(AudioAsset.id == asset_id)).first()
        assert asset is not None
        file_path = asset.file_path
        assert file_path is not None
        assert Path(file_path).exists()
        assert Path(file_path).stat().st_size > 0


def test_ws_stream_audio_chunks_decodable(test_app, seed_mock_binding, ws_patched_session):
    """所有 audio_chunk 的 base64 数据可正确解码，拼接后音频有效."""
    client = TestClient(test_app)
    events = collect_ws_events(client, text="集成测试", provider="mock")

    chunks = [e for e in events if e["event"] == "audio_chunk"]
    assert len(chunks) >= 1

    total_bytes = 0
    indices = []
    for chunk in chunks:
        decoded = base64.b64decode(chunk["audio_base64"])
        assert isinstance(decoded, bytes)
        assert len(decoded) > 0
        total_bytes += len(decoded)
        indices.append(chunk["chunk_index"])

    assert total_bytes > 0
    assert indices == list(range(len(chunks))), "chunk_index must be sequential from 0"
    last_chunk = chunks[-1]
    assert last_chunk["is_final"] is True


def test_ws_stream_completed_totals_match_chunks(test_app, seed_mock_binding, ws_patched_session):
    """completed 消息中的统计与实际收到的 chunk 一致."""
    client = TestClient(test_app)
    events = collect_ws_events(client, text="集成测试", provider="mock")

    chunks = [e for e in events if e["event"] == "audio_chunk"]
    completed = next((e for e in events if e["event"] == "completed"), None)
    assert completed is not None

    assert completed["total_chunks"] == len(chunks)
    assert completed["total_duration_ms"] >= 0


def test_ws_stream_nonexistent_profile(test_app, seed_mock_binding, ws_patched_session):
    """不存在的 profile_id 返回 error 事件."""
    client = TestClient(test_app)
    events = collect_ws_events(
        client, text="测试", provider="mock", profile_id="nonexistent_xyz"
    )

    error = next((e for e in events if e["event"] == "error"), None)
    assert error is not None, f"No error event. Events: {events}"
    code_or_msg = (error.get("code", "") + error.get("message", "")).lower()
    assert "not_found" in code_or_msg or "not found" in code_or_msg, \
        f"Expected not found in code or message, got: {error}"


def test_ws_stream_text_exceeds_limit(test_app, seed_mock_binding, ws_patched_session):
    """超长文本（>10000）被拒绝."""
    client = TestClient(test_app)
    events = collect_ws_events(client, text="a" * 10001, provider="mock")

    error = next((e for e in events if e["event"] == "error"), None)
    assert error is not None, f"No error event. Events: {events}"
    assert error["code"] == "INVALID_REQUEST"


def test_ws_stream_message_order(test_app, seed_mock_binding, ws_patched_session):
    """消息顺序严格正确：connected → started → audio_chunk(s) → completed."""
    client = TestClient(test_app)
    events = collect_ws_events(client, text="集成测试", provider="mock")

    event_types = [e["event"] for e in events]

    connected_idx = event_types.index("connected")
    started_idx = event_types.index("started")
    completed_idx = event_types.index("completed")

    assert connected_idx < started_idx, "started must come after connected"
    assert started_idx < completed_idx, "completed must come after started"

    chunk_indices = [i for i, e in enumerate(event_types) if e == "audio_chunk"]
    if chunk_indices:
        first_chunk_idx = chunk_indices[0]
        last_chunk_idx = chunk_indices[-1]
        assert started_idx < first_chunk_idx, "first audio_chunk must come after started"
        assert last_chunk_idx < completed_idx, "completed must come after all audio_chunks"


def test_ws_stream_multiple_sequential_sessions(test_app, seed_mock_binding, ws_patched_session, session):
    """同一 TestClient 连续发起多次 WebSocket 流式生成，互不干扰."""
    client = TestClient(test_app)

    events1 = collect_ws_events(client, text="第一次会话", provider="mock")
    completed1 = next((e for e in events1 if e["event"] == "completed"), None)
    assert completed1 is not None
    job_id1 = completed1["job_id"]

    events2 = collect_ws_events(client, text="第二次会话", provider="mock")
    completed2 = next((e for e in events2 if e["event"] == "completed"), None)
    assert completed2 is not None
    job_id2 = completed2["job_id"]

    assert job_id1 != job_id2, "Two sessions must have different job_ids"

    from sqlmodel import Session
    engine = session.bind.engine
    with Session(engine) as verify_sess:
        jobs = verify_sess.exec(
            select(VoiceJob).where(VoiceJob.job_type == "stream_render")
        ).all()
        assert len(jobs) >= 2, f"Expected at least 2 stream_render jobs, got {len(jobs)}"

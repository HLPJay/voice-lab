import asyncio
import json
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from app.core.time import utc_now_iso
from app.domain.enums import BatchStatus
from app.domain.schemas import LongtextBatchRequest, ScriptBatchRequest, ScriptLine
from app.models.batch_job import BatchJob, BatchSegment
from app.services.batch_orchestration_service import BatchOrchestrationService


@pytest.fixture
def service():
    return BatchOrchestrationService()


def test_submit_longtext_creates_batch_and_segments(
    service, session: Session, seed_profile, seed_mock_binding
):
    """submit_longtext creates BatchJob and BatchSegments without executing."""
    request = LongtextBatchRequest(
        text="第一段。第二段。第三段。",
        profile_id="deep_night_programmer",
        provider="mock",
        segment_strategy="sentence",
        max_segment_chars=2000,
    )

    # Patch asyncio.create_task so the background execute() is not scheduled
    with patch("asyncio.create_task", side_effect=lambda coro: None):
        response = asyncio.get_event_loop().run_until_complete(
            service.submit_longtext(session, request)
        )

    assert response.batch_id.startswith("batch_")
    assert response.mode == "longtext"
    assert response.total_segments >= 1
    assert response.status == BatchStatus.pending

    batch_job = session.get(BatchJob, response.batch_id)
    assert batch_job is not None
    assert batch_job.mode == "longtext"
    assert batch_job.total_segments == response.total_segments

    segments = list(session.exec(
        select(BatchSegment).where(BatchSegment.batch_job_id == response.batch_id)
    ).all())
    assert len(segments) == response.total_segments


def test_submit_script_creates_batch_and_segments(
    service, session: Session, seed_profile, seed_mock_binding
):
    """submit_script creates BatchJob and BatchSegments without executing."""
    request = ScriptBatchRequest(
        script=[
            ScriptLine(role="旁白", text="旁白内容。", profile_id="deep_night_programmer"),
            ScriptLine(role="角色", text="对白内容！", profile_id="deep_night_programmer"),
        ],
        provider="mock",
    )

    with patch("asyncio.create_task", side_effect=lambda coro: None):
        response = asyncio.get_event_loop().run_until_complete(
            service.submit_script(session, request)
        )

    assert response.batch_id.startswith("batch_")
    assert response.mode == "script"
    assert response.total_segments == 2
    assert response.status == BatchStatus.pending

    segments = list(session.exec(
        select(BatchSegment).where(BatchSegment.batch_job_id == response.batch_id)
    ).all())
    assert len(segments) == 2
    assert segments[0].role == "旁白"
    assert segments[1].role == "角色"


def test_execute_batch_generates_all_segments(
    service, session: Session, seed_profile, seed_mock_binding
):
    """execute() renders all segments and updates their status."""
    now = utc_now_iso()
    batch_id = "batch_test_001"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status=BatchStatus.pending,
        provider="mock",
        output_format="mp3",
        total_segments=2,
        silence_between_ms=0,
        config_json=json.dumps({
            "text": "第一句。第二句。",
            "profile_id": "deep_night_programmer",
            "need_subtitle": False,
        }),
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    for i in range(2):
        seg = BatchSegment(
            id=f"seg_test_{i}",
            batch_job_id=batch_id,
            index=i,
            text=f"测试文本{i}。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
    session.commit()

    asyncio.get_event_loop().run_until_complete(
        service.execute(session, batch_id)
    )

    segments = list(session.exec(
        select(BatchSegment).where(BatchSegment.batch_job_id == batch_id)
        .order_by(BatchSegment.index)
    ).all())

    assert all(s.status == BatchStatus.success for s in segments)
    assert all(s.voice_job_id is not None for s in segments)
    assert all(s.audio_asset_id is not None for s in segments)
    assert all(s.duration_ms is not None for s in segments)

    session.refresh(batch_job)
    assert batch_job.status == BatchStatus.success
    assert batch_job.merged_audio_asset_id is not None


def test_execute_batch_merges_audio(
    service, session: Session, seed_profile, seed_mock_binding
):
    """After execution, merged audio asset is saved on BatchJob."""
    now = utc_now_iso()
    batch_id = "batch_test_002"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status=BatchStatus.pending,
        provider="mock",
        output_format="mp3",
        total_segments=2,
        silence_between_ms=300,
        config_json=json.dumps({
            "text": "短文一。短文二。",
            "profile_id": "deep_night_programmer",
            "need_subtitle": True,
        }),
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    for i in range(2):
        seg = BatchSegment(
            id=f"seg_merge_{i}",
            batch_job_id=batch_id,
            index=i,
            text=f"合并测试{i}。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
    session.commit()

    asyncio.get_event_loop().run_until_complete(
        service.execute(session, batch_id)
    )

    session.refresh(batch_job)
    assert batch_job.merged_audio_asset_id is not None
    assert batch_job.status in (BatchStatus.success, BatchStatus.partial)


def test_execute_batch_partial_failure(
    service, session: Session, seed_profile, seed_mock_binding
):
    """When one segment fails, others still succeed and merge runs."""
    now = utc_now_iso()
    batch_id = "batch_test_003"
    batch_job = BatchJob(
        id=batch_id,
        mode="script",
        status=BatchStatus.pending,
        provider="mock",
        output_format="mp3",
        total_segments=2,
        silence_between_ms=0,
        config_json=json.dumps({"need_subtitle": False}),
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    seg0 = BatchSegment(
        id="seg_partial_0",
        batch_job_id=batch_id,
        index=0,
        text="成功的内容。",
        profile_id="deep_night_programmer",
        params_json="{}",
        status=BatchStatus.pending,
        created_at=now,
        updated_at=now,
    )
    seg1 = BatchSegment(
        id="seg_partial_1",
        batch_job_id=batch_id,
        index=1,
        text="失败的内容。",
        profile_id="nonexistent_profile_xyz",
        params_json="{}",
        status=BatchStatus.pending,
        created_at=now,
        updated_at=now,
    )
    session.add_all([seg0, seg1])
    session.commit()

    asyncio.get_event_loop().run_until_complete(
        service.execute(session, batch_id)
    )

    session.refresh(batch_job)
    assert batch_job.status == BatchStatus.partial
    assert batch_job.completed_segments == 1
    assert batch_job.failed_segments == 1


def test_get_status_returns_progress(service, session: Session):
    """get_status returns correct progress for a running batch job."""
    now = utc_now_iso()
    batch_id = "batch_test_004"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status=BatchStatus.running,
        provider="mock",
        output_format="mp3",
        total_segments=3,
        completed_segments=1,
        failed_segments=1,
        silence_between_ms=0,
        config_json="{}",
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    for i in range(3):
        seg = BatchSegment(
            id=f"seg_status_{i}",
            batch_job_id=batch_id,
            index=i,
            text=f"文本{i}。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.success if i < 2 else BatchStatus.pending,
            voice_job_id=f"job_{i}" if i < 2 else None,
            audio_asset_id=f"audio_{i}" if i < 2 else None,
            duration_ms=1000 if i < 2 else None,
            error_message=None if i < 2 else None,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
    session.commit()

    response = asyncio.get_event_loop().run_until_complete(
        service.get_status(session, batch_id)
    )

    assert response.batch_id == batch_id
    assert response.total_segments == 3
    assert response.completed_segments == 1
    assert response.failed_segments == 1
    assert len(response.segments) == 3
    assert response.segments[0].status == BatchStatus.success
    assert response.segments[1].status == BatchStatus.success
    assert response.segments[2].status == BatchStatus.pending

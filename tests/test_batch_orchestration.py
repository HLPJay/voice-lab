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

    # Patch _execute_with_session so the background execute() is not scheduled
    with patch.object(service, '_execute_with_session', return_value=None):
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

    with patch.object(service, '_execute_with_session', return_value=None):
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


def test_batch_process_segment_uses_audio_format_not_output_format(
    service, session: Session, seed_profile, seed_mock_binding
):
    """Verify _process_segment passes audio_format (not output_format) as audio_params['format']."""
    from unittest.mock import AsyncMock
    from app.domain.render_plan import RenderPlan

    captured_plans: list[RenderPlan] = []

    async def mock_render_sync(plan: RenderPlan) -> dict:
        captured_plans.append(plan)
        # Return a minimal ProviderRenderResult-like dict
        from app.providers.base import ProviderRenderResult
        from app.utils.files import storage_path
        from app.utils.id_generator import new_id
        audio_id = new_id("audio_file")
        audio_path = storage_path("audio", f"{audio_id}.wav")
        from app.utils.audio import write_silent_wav
        write_silent_wav(audio_path, duration_ms=500, sample_rate=16000)
        return ProviderRenderResult(
            audio_path=str(audio_path),
            duration_ms=500,
            usage_characters=len(plan.text),
            trace_id="mock_trace",
            response_json={},
            timeline=[],
            metadata={},
        )

    # Patch get_provider on the service module
    import app.services.batch_orchestration_service as svc_module
    original_get = svc_module.get_provider

    class FakeAdapter:
        async def render_sync(self, plan):
            return await mock_render_sync(plan)

    def fake_get_provider(p):
        return FakeAdapter()

    svc_module.get_provider = fake_get_provider

    try:
        now = utc_now_iso()
        batch_id = "batch_test_audio_format"
        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status=BatchStatus.pending,
            provider="mock",
            output_format="hex",
            total_segments=1,
            silence_between_ms=0,
            config_json=json.dumps({
                "text": "测试文本。",
                "profile_id": "deep_night_programmer",
                "need_subtitle": False,
                "audio_format": "wav",
            }),
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        seg = BatchSegment(
            id="seg_audio_format",
            batch_job_id=batch_id,
            index=0,
            text="测试文本。",
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

        assert len(captured_plans) == 1
        plan = captured_plans[0]
        # audio_params['format'] must be the audio encoding (wav), not output_format (hex)
        assert plan.audio_params["format"] == "wav", \
            f"expected audio_params['format']='wav', got '{plan.audio_params['format']}'"
        # output_format must be hex/url
        assert plan.output_format in ("hex", "url"), \
            f"expected output_format in ('hex','url'), got '{plan.output_format}'"
    finally:
        svc_module.get_provider = original_get


def test_batch_legacy_output_format_mp3_sets_audio_format(
    service, session: Session, seed_profile, seed_mock_binding
):
    """Legacy batch job with output_format='mp3' (old schema) is treated as audio_format='mp3'.

    Compatibility: when batch_job.output_format is an audio format (mp3/wav/flac),
    it means the old schema stored the audio encoding there.
    The execute() should use it as audio_format and default output_format to hex.
    """
    now = utc_now_iso()
    batch_id = "batch_test_legacy"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status=BatchStatus.pending,
        provider="mock",
        output_format="mp3",  # old schema: this was the audio format
        total_segments=1,
        silence_between_ms=0,
        config_json=json.dumps({
            "text": "legacy text。",
            "profile_id": "deep_night_programmer",
            "need_subtitle": False,
            # no audio_format field → from legacy output_format="mp3"
        }),
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    seg = BatchSegment(
        id="seg_legacy",
        batch_job_id=batch_id,
        index=0,
        text="legacy text。",
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
    ).all())
    assert all(s.status == BatchStatus.success for s in segments)
    # Verify merged asset was created (old schema with mp3 audio_format works)
    session.refresh(batch_job)
    assert batch_job.merged_audio_asset_id is not None


def test_execute_batch_concurrent_respects_order(
    service, session: Session, seed_profile, seed_mock_binding
):
    """Concurrent execution preserves segment order in merged output."""
    now = utc_now_iso()
    batch_id = "batch_test_concurrent"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status=BatchStatus.pending,
        provider="mock",
        output_format="hex",
        total_segments=5,
        silence_between_ms=0,
        config_json=json.dumps({
            "text": "一二三四五",
            "profile_id": "deep_night_programmer",
            "need_subtitle": False,
        }),
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    for i in range(5):
        seg = BatchSegment(
            id=f"seg_conc_{i}",
            batch_job_id=batch_id,
            index=i,
            text=f"并发测试段落{i}。",
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

    session.expire_all()
    segments = list(session.exec(
        select(BatchSegment).where(BatchSegment.batch_job_id == batch_id)
        .order_by(BatchSegment.index)
    ).all())

    assert len(segments) == 5
    assert all(s.status == BatchStatus.success for s in segments)
    assert [s.index for s in segments] == [0, 1, 2, 3, 4]
    assert all(s.audio_asset_id is not None for s in segments)

    session.refresh(batch_job)
    assert batch_job.status == BatchStatus.success
    assert batch_job.completed_segments == 5
    assert batch_job.merged_audio_asset_id is not None


def test_batch_mode_literal_rejects_wrong_mode():
    """LongtextBatchRequest(mode='wrong') is rejected by Pydantic Literal validation."""
    from pydantic import ValidationError
    from app.domain.schemas import LongtextBatchRequest

    with pytest.raises(ValidationError):
        LongtextBatchRequest(
            mode="wrong",
            text="测试文本。",
            profile_id="deep_night_programmer",
        )


def test_batch_job_default_output_format_is_hex():
    """BatchJob() default output_format is 'hex'."""
    from app.models.batch_job import BatchJob

    job = BatchJob(
        id="test_default_format",
        mode="longtext",
        provider="mock",
        total_segments=0,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    assert job.output_format == "hex", \
        f"expected output_format='hex', got '{job.output_format}'"


class TestBatchResourceGuard:
    """Tests for Resource Guard integration in BatchOrchestrationService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_submit_longtext_rejected_when_guard_full(self, session, seed_profile, seed_mock_binding):
        """When batch_longtext limit=1 is held, submit_longtext raises ResourceLimitExceeded,
        does NOT create any BatchJob/BatchSegment records, and does NOT call _execute_with_session."""
        from app.services.resource_guard_service import get_resource_guard, ResourceLimitExceeded
        from app.domain.schemas import LongtextBatchRequest
        from app.models.batch_job import BatchJob, BatchSegment
        from unittest.mock import patch

        # Count existing records before the call.
        batch_job_count_before = len(list(session.exec(select(BatchJob)).all()))
        batch_segment_count_before = len(list(session.exec(select(BatchSegment)).all()))

        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="batch_longtext", job_id=None)

        try:
            service = BatchOrchestrationService()
            request = LongtextBatchRequest(
                text="测试文本。",
                profile_id="deep_night_programmer",
                provider="minimax",
                segment_strategy="sentence",
                max_segment_chars=2000,
                confirm_cost=True,
            )

            with patch.object(service, "_execute_with_session", return_value=None) as mock_execute:
                with pytest.raises(ResourceLimitExceeded):
                    await service.submit_longtext(session, request)
                mock_execute.assert_not_called()
        finally:
            await guard._release(lease)

        # Verify no new BatchJob or BatchSegment records were created.
        batch_job_count_after = len(list(session.exec(select(BatchJob)).all()))
        batch_segment_count_after = len(list(session.exec(select(BatchSegment)).all()))
        assert batch_job_count_after == batch_job_count_before
        assert batch_segment_count_after == batch_segment_count_before

    @pytest.mark.asyncio
    async def test_submit_script_rejected_when_guard_full(self, session, seed_profile, seed_mock_binding):
        """When batch_script limit=1 is held, submit_script raises ResourceLimitExceeded,
        does NOT create any BatchJob/BatchSegment records, and does NOT call _execute_with_session."""
        from app.services.resource_guard_service import get_resource_guard, ResourceLimitExceeded
        from app.domain.schemas import ScriptBatchRequest, ScriptLine
        from app.models.batch_job import BatchJob, BatchSegment
        from unittest.mock import patch

        batch_job_count_before = len(list(session.exec(select(BatchJob)).all()))
        batch_segment_count_before = len(list(session.exec(select(BatchSegment)).all()))

        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="batch_script", job_id=None)

        try:
            service = BatchOrchestrationService()
            request = ScriptBatchRequest(
                script=[
                    ScriptLine(role="旁白", text="内容。", profile_id="deep_night_programmer"),
                ],
                provider="minimax",
                confirm_cost=True,
            )

            with patch.object(service, "_execute_with_session", return_value=None) as mock_execute:
                with pytest.raises(ResourceLimitExceeded):
                    await service.submit_script(session, request)
                mock_execute.assert_not_called()
        finally:
            await guard._release(lease)

        batch_job_count_after = len(list(session.exec(select(BatchJob)).all()))
        batch_segment_count_after = len(list(session.exec(select(BatchSegment)).all()))
        assert batch_job_count_after == batch_job_count_before
        assert batch_segment_count_after == batch_segment_count_before

    @pytest.mark.asyncio
    async def test_execute_rejected_when_guard_full(self, session, seed_profile, seed_mock_binding):
        """When batch_execute limit=1 is held, execute marks batch as failed
        and no segment is successfully processed."""
        from app.services.resource_guard_service import get_resource_guard
        from app.models.batch_job import BatchJob, BatchSegment
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        batch_id = "batch_guard_test"
        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status=BatchStatus.pending,
            provider="minimax",
            output_format="mp3",
            total_segments=1,
            silence_between_ms=0,
            config_json=json.dumps({
                "text": "测试。",
                "profile_id": "deep_night_programmer",
                "need_subtitle": False,
            }),
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        seg = BatchSegment(
            id="seg_guard_test",
            batch_job_id=batch_id,
            index=0,
            text="测试。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
        session.commit()

        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="batch_execute", job_id=None)

        try:
            service = BatchOrchestrationService()
            await service.execute(session, batch_id)
        finally:
            await guard._release(lease)

        session.refresh(batch_job)
        # When guard rejects, batch status should be failed.
        assert batch_job.status == BatchStatus.failed
        # All segments should be counted as failed.
        assert batch_job.failed_segments == batch_job.total_segments
        # Error message should be set.
        assert batch_job.error_message is not None and batch_job.error_message != ""
        assert "batch_execute" in batch_job.error_message or "RESOURCE_LIMIT" in batch_job.error_message
        # Segment should NOT have voice_job_id or audio_asset_id set.
        session.refresh(seg)
        assert seg.voice_job_id is None, "Segment should not have voice_job_id when guard rejects"
        assert seg.audio_asset_id is None, "Segment should not have audio_asset_id when guard rejects"

    @pytest.mark.asyncio
    async def test_segment_render_error_marks_voice_job_and_segment_failed(self, session, seed_profile, seed_mock_binding):
        """When segment render fails, the segment and its VoiceJob are both marked as failed."""
        from app.models.batch_job import BatchJob, BatchSegment
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso
        from unittest.mock import patch

        now = utc_now_iso()
        batch_id = "batch_render_fail_test"
        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status=BatchStatus.pending,
            provider="mock",
            output_format="mp3",
            total_segments=1,
            silence_between_ms=0,
            config_json=json.dumps({
                "text": "测试。",
                "profile_id": "deep_night_programmer",
                "need_subtitle": False,
            }),
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        seg = BatchSegment(
            id="seg_render_fail",
            batch_job_id=batch_id,
            index=0,
            text="测试。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
        session.commit()

        class FailingAdapter:
            provider_name = "minimax"

            async def render_sync(self, plan):
                raise RuntimeError("Provider render error")

        service = BatchOrchestrationService()

        with patch("app.services.batch_orchestration_service.get_provider", return_value=FailingAdapter()):
            with patch("app.services.batch_orchestration_service.validate_binding_provider_voice"):
                await service.execute(session, batch_id)

        session.expire_all()

        # Reload segment and verify.
        seg = session.get(BatchSegment, "seg_render_fail")
        assert seg is not None
        assert seg.status == BatchStatus.failed, f"Expected segment status=failed, got {seg.status}"
        assert seg.error_message is not None and "Provider render error" in seg.error_message
        assert seg.voice_job_id is not None, "Segment should have voice_job_id after VoiceJob creation"

        # Verify the associated VoiceJob is also marked as failed.
        voice_job = session.get(VoiceJob, seg.voice_job_id)
        assert voice_job is not None
        assert voice_job.status == "failed", f"Expected VoiceJob status=failed, got {voice_job.status}"
        assert "Provider render error" in (voice_job.error_message or "")

    @pytest.mark.asyncio
    async def test_segment_save_assets_error_marks_voice_job_and_segment_failed(self, session, seed_profile, seed_mock_binding):
        """When save_assets fails, the segment and its VoiceJob are both marked as failed."""
        from app.models.batch_job import BatchJob, BatchSegment
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso
        from unittest.mock import patch, AsyncMock

        now = utc_now_iso()
        batch_id = "batch_save_fail_test"
        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status=BatchStatus.pending,
            provider="mock",
            output_format="mp3",
            total_segments=1,
            silence_between_ms=0,
            config_json=json.dumps({
                "text": "测试。",
                "profile_id": "deep_night_programmer",
                "need_subtitle": False,
            }),
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        seg = BatchSegment(
            id="seg_save_fail",
            batch_job_id=batch_id,
            index=0,
            text="测试。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
        session.commit()

        class SuccessRenderAdapter:
            provider_name = "minimax"

            async def render_sync(self, plan):
                from app.providers.base import ProviderRenderResult
                return ProviderRenderResult(
                    audio_path="/fake/audio.mp3",
                    duration_ms=100,
                    usage_characters=10,
                    trace_id="mock_trace",
                    response_json={},
                    timeline=[],
                    metadata={},
                )

        service = BatchOrchestrationService()

        with patch("app.services.batch_orchestration_service.get_provider", return_value=SuccessRenderAdapter()):
            with patch("app.services.batch_orchestration_service.validate_binding_provider_voice"):
                with patch.object(service.asset_service, "save_assets", side_effect=RuntimeError("save assets error")):
                    await service.execute(session, batch_id)

        session.expire_all()

        # Reload segment and verify.
        seg = session.get(BatchSegment, "seg_save_fail")
        assert seg is not None
        assert seg.status == BatchStatus.failed, f"Expected segment status=failed, got {seg.status}"
        assert seg.error_message is not None and "save assets error" in seg.error_message
        assert seg.voice_job_id is not None, "Segment should have voice_job_id after VoiceJob creation"

        # Verify the associated VoiceJob is also marked as failed.
        voice_job = session.get(VoiceJob, seg.voice_job_id)
        assert voice_job is not None
        assert voice_job.status == "failed", f"Expected VoiceJob status=failed, got {voice_job.status}"
        assert "save assets error" in (voice_job.error_message or "")

        # BatchJob should be failed (single segment failure = full failure).
        session.refresh(batch_job)
        assert batch_job.status == BatchStatus.failed

    @pytest.mark.asyncio
    async def test_minimax_batch_segments_execute_without_t2a_sync_guard(self, session, seed_profile, seed_mock_binding):
        """Minimax batch segments bypass t2a_sync guard even when t2a_sync slots are fully occupied.

        This test uses provider='minimax' with a fake adapter to verify that batch segments
        do NOT go through the t2a_sync Resource Guard path, even when minimax:t2a_sync
        slots are completely taken.
        """
        from app.models.batch_job import BatchJob, BatchSegment
        from app.core.time import utc_now_iso
        from app.services.resource_guard_service import get_resource_guard
        from unittest.mock import patch
        from app.providers.base import ProviderRenderResult

        now = utc_now_iso()
        batch_id = "batch_no_double_guard_test"

        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status=BatchStatus.pending,
            provider="minimax",
            output_format="mp3",
            total_segments=1,
            silence_between_ms=0,
            config_json=json.dumps({
                "text": "测试。",
                "profile_id": "deep_night_programmer",
                "need_subtitle": False,
            }),
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        seg = BatchSegment(
            id="seg_no_double_guard",
            batch_job_id=batch_id,
            index=0,
            text="测试。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
        session.commit()

        class FakeMinimaxAdapter:
            provider_name = "minimax"

            async def render_sync(self, plan):
                from app.utils.files import storage_path
                from app.utils.id_generator import new_id
                from app.utils.audio import write_silent_wav
                audio_id = new_id("audio")
                audio_path = storage_path("audio", f"{audio_id}.mp3")
                write_silent_wav(audio_path, duration_ms=500, sample_rate=16000)
                return ProviderRenderResult(
                    audio_path=str(audio_path),
                    duration_ms=500,
                    usage_characters=len(plan.text),
                    trace_id="mock_trace",
                    response_json={},
                    timeline=[],
                    metadata={},
                )

        # Hold ALL minimax:t2a_sync slots (limit=2). If batch segments incorrectly
        # enter t2a_sync guard, they will be rejected here.
        guard = get_resource_guard()
        lease1 = await guard._acquire(provider="minimax", operation="t2a_sync", job_id=None)
        lease2 = await guard._acquire(provider="minimax", operation="t2a_sync", job_id=None)

        try:
            service = BatchOrchestrationService()
            with patch("app.services.batch_orchestration_service.get_provider", return_value=FakeMinimaxAdapter()):
                with patch("app.services.batch_orchestration_service.validate_binding_provider_voice"):
                    await service.execute(session, batch_id)
        finally:
            await guard._release(lease1)
            await guard._release(lease2)

        session.refresh(batch_job)
        assert batch_job.status == BatchStatus.success, \
            f"Expected batch success, got {batch_job.status}. If failed due to RESOURCE_LIMIT_EXCEEDED on t2a_sync, segments may have wrongly entered t2a_sync guard."
        assert batch_job.completed_segments == 1

        session.refresh(seg)
        assert seg.status == BatchStatus.success, f"Expected segment success, got {seg.status}"
        assert seg.voice_job_id is not None, "Segment should have voice_job_id after successful render"
        assert seg.audio_asset_id is not None, "Segment should have audio_asset_id after successful render"
        assert batch_job.completed_segments == 1

    @pytest.mark.asyncio
    async def test_execute_success_path_regression(self, session, seed_profile, seed_mock_binding):
        """Normal batch execution still works correctly (regression test)."""
        from app.models.batch_job import BatchJob, BatchSegment
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        batch_id = "batch_success_regression"
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
                id=f"seg_regression_{i}",
                batch_job_id=batch_id,
                index=i,
                text=f"回归测试{i}。",
                profile_id="deep_night_programmer",
                params_json="{}",
                status=BatchStatus.pending,
                created_at=now,
                updated_at=now,
            )
            session.add(seg)
        session.commit()

        service = BatchOrchestrationService()
        await service.execute(session, batch_id)

        session.refresh(batch_job)
        assert batch_job.status == BatchStatus.success
        assert batch_job.completed_segments == 2
        assert batch_job.failed_segments == 0
        assert batch_job.merged_audio_asset_id is not None

    @pytest.mark.asyncio
    async def test_execute_merge_failure_marks_batch_failed(self, session, seed_profile, seed_mock_binding):
        """When segments succeed but merge fails, BatchJob.status is failed with error_message,
        completed_segments reflects success count, and segments remain success."""
        from app.models.batch_job import BatchJob, BatchSegment
        from app.core.time import utc_now_iso
        from unittest.mock import patch

        now = utc_now_iso()
        batch_id = "batch_merge_fail_test"
        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status=BatchStatus.pending,
            provider="mock",
            output_format="mp3",
            total_segments=1,
            silence_between_ms=0,
            config_json=json.dumps({
                "text": "测试。",
                "profile_id": "deep_night_programmer",
                "need_subtitle": False,
            }),
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        seg = BatchSegment(
            id="seg_merge_fail",
            batch_job_id=batch_id,
            index=0,
            text="测试。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
        session.commit()

        service = BatchOrchestrationService()

        with patch.object(service.audio_merger, "merge", side_effect=RuntimeError("merge failed")):
            await service.execute(session, batch_id)

        session.refresh(batch_job)

        # BatchJob should be failed due to merge error.
        assert batch_job.status == BatchStatus.failed, \
            f"Expected batch status=failed due to merge error, got {batch_job.status}"
        # Error message should mention merge failure.
        assert batch_job.error_message is not None
        assert "merge failed" in batch_job.error_message.lower()
        # completed_segments reflects successful segments.
        assert batch_job.completed_segments == 1
        # failed_segments is 0 since no segment failed, only merge.
        assert batch_job.failed_segments == 0
        # merged_audio_asset_id should NOT be set.
        assert batch_job.merged_audio_asset_id is None

        # Segment should still be success.
        session.refresh(seg)
        assert seg.status == BatchStatus.success, f"Expected segment status=success, got {seg.status}"
        assert seg.audio_asset_id is not None, "Segment should have audio_asset_id"
        assert seg.voice_job_id is not None, "Segment should have voice_job_id"

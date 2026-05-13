import pytest
from fastapi.testclient import TestClient


def test_submit_async_task(test_app, seed_profile, seed_mock_binding):
    """POST /api/voice/render/async returns job_id with processing status."""
    resp = TestClient(test_app).post(
        "/api/voice/render/async",
        json={
            "text": "异步长文本语音生成测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "processing"
    assert data["provider"] == "mock"
    assert data["model"]


def test_query_status_success(test_app, seed_profile, seed_mock_binding):
    """GET status after submit returns success with audio asset."""
    client = TestClient(test_app)
    submit = client.post(
        "/api/voice/render/async",
        json={
            "text": "异步状态查询测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert submit.status_code == 200
    job_id = submit.json()["job_id"]

    status = client.get(f"/api/voice/render/async/{job_id}/status")
    assert status.status_code == 200
    data = status.json()
    assert data["status"] == "success"
    assert data["audio_asset"] is not None
    assert data["audio_asset"]["id"].startswith("audio_")


def test_query_status_with_subtitle(test_app, seed_profile, seed_mock_binding):
    """Async render with need_subtitle=True produces subtitle asset on completion."""
    client = TestClient(test_app)
    submit = client.post(
        "/api/voice/render/async",
        json={
            "text": "异步字幕测试。",
            "provider": "mock",
            "need_subtitle": True,
        },
    )
    assert submit.status_code == 200
    job_id = submit.json()["job_id"]

    status = client.get(f"/api/voice/render/async/{job_id}/status")
    assert status.status_code == 200
    data = status.json()
    assert data["status"] == "success"
    assert data["subtitle_asset"] is not None
    assert data["subtitle_asset"]["id"].startswith("subtitle_")


def test_query_nonexistent_job(test_app, seed_profile):
    """Query a non-existent job_id returns 404."""
    resp = TestClient(test_app).get("/api/voice/render/async/job_nonexistent/status")
    assert resp.status_code == 404


def test_already_completed_job_returns_cached(test_app, seed_profile, seed_mock_binding):
    """Querying a completed job again returns same result without re-downloading."""
    client = TestClient(test_app)
    submit = client.post(
        "/api/voice/render/async",
        json={
            "text": "重复查询测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    job_id = submit.json()["job_id"]

    first = client.get(f"/api/voice/render/async/{job_id}/status")
    second = client.get(f"/api/voice/render/async/{job_id}/status")
    assert first.json()["status"] == "success"
    assert second.json()["status"] == "success"
    assert first.json()["audio_asset"]["id"] == second.json()["audio_asset"]["id"]


def test_submit_empty_text_rejected(test_app, seed_profile):
    """Empty text is rejected by request validation."""
    resp = TestClient(test_app).post(
        "/api/voice/render/async",
        json={
            "text": "",
            "provider": "mock",
        },
    )
    assert resp.status_code == 422


class TestAsyncRenderResourceGuard:
    """Tests for Resource Guard integration in AsyncRenderService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_submit_task_rejected_when_slot_full(self, session, seed_profile, seed_mock_binding):
        """When t2a_async_submit limit=2 is held, submit_task raises ResourceLimitExceeded 429."""
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.services.resource_guard_service import ResourceLimitExceeded, get_resource_guard
        from app.domain.schemas import AsyncRenderRequest

        adapter_called = False

        class CheckedSubmitAdapter:
            provider_name = "minimax"

            async def create_async_task(self, plan):
                nonlocal adapter_called
                adapter_called = True
                from app.providers.base import AsyncTaskResult
                return AsyncTaskResult(
                    task_id="mock_task",
                    provider_task_id="mock_task_id",
                    trace_id="mock_trace",
                    metadata={},
                )

        svc = AsyncRenderService()

        # Hold both t2a_async_submit slots (limit=2 for minimax)
        guard = get_resource_guard()
        lease1 = await guard._acquire(provider="minimax", operation="t2a_async_submit", job_id=None)
        lease2 = await guard._acquire(provider="minimax", operation="t2a_async_submit", job_id=None)

        with patch("app.services.async_render_service.get_provider", return_value=CheckedSubmitAdapter()):
            with patch("app.services.async_render_service.validate_binding_provider_voice"):
                req = AsyncRenderRequest(
                    text="异步提交测试",
                    profile_id="deep_night_programmer",
                    provider="minimax",
                    confirm_cost=True,
                )
                with pytest.raises(ResourceLimitExceeded) as exc_info:
                    await svc.submit_task(session, req)
                assert exc_info.value.status_code == 429
                assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert adapter_called is False, "create_async_task should not be called when guard rejects"

        # Cleanup
        await guard._release(lease1)
        await guard._release(lease2)

    @pytest.mark.asyncio
    async def test_query_status_rejected_preserves_job_status(self, session, seed_profile, seed_mock_binding):
        """When t2a_async_query_download is full, query_status raises 429 but job.status stays processing."""
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.services.resource_guard_service import ResourceLimitExceeded, get_resource_guard
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso

        # Create a processing job with provider_task_id
        now = utc_now_iso()
        job = VoiceJob(
            id="test_processing_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="测试文本",
            processed_text="测试文本",
            render_plan_json="{}",
            response_json='{"provider_task_id": "mock_provider_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        adapter_called = False

        class CheckedAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                nonlocal adapter_called
                adapter_called = True
                from app.providers.base import AsyncTaskStatus
                return AsyncTaskStatus(
                    task_id=provider_task_id,
                    status="processing",
                    file_url=None,
                    trace_id="mock_trace",
                    metadata={},
                )

        svc = AsyncRenderService()

        # Hold both t2a_async_query_download slots (limit=2, shared key with t2a_async_submit)
        guard = get_resource_guard()
        lease1 = await guard._acquire(provider="minimax", operation="t2a_async_query_download", job_id=None)
        lease2 = await guard._acquire(provider="minimax", operation="t2a_async_query_download", job_id=None)

        with patch("app.services.async_render_service.get_provider", return_value=CheckedAdapter()):
            with pytest.raises(ResourceLimitExceeded) as exc_info:
                await svc.query_status(session, "test_processing_job")
            assert exc_info.value.status_code == 429
            assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert adapter_called is False, "query_async_task should not be called when guard rejects"

        # Verify job status is still processing (not changed to failed)
        session.refresh(job)
        assert job.status == "processing", "Job status should remain processing when query guard rejects"

        # Cleanup
        await guard._release(lease1)
        await guard._release(lease2)

    @pytest.mark.asyncio
    async def test_query_status_success_no_file_url_marks_failed(self, session, seed_profile, seed_mock_binding):
        """When provider returns success but file_url is missing, job should be marked failed."""
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        job = VoiceJob(
            id="test_no_url_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="测试",
            processed_text="测试",
            render_plan_json="{}",
            response_json='{"provider_task_id": "mock_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        class NoFileUrlAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                from app.providers.base import AsyncTaskStatus
                return AsyncTaskStatus(
                    task_id=provider_task_id,
                    status="success",
                    file_url=None,  # missing!
                    trace_id="mock_trace",
                    metadata={},
                )

        svc = AsyncRenderService()

        with patch("app.services.async_render_service.get_provider", return_value=NoFileUrlAdapter()):
            result = await svc.query_status(session, "test_no_url_job")

        session.refresh(job)
        assert job.status == "failed", "Job should be marked failed when success but file_url missing"
        assert "file_url missing" in job.error_message

    @pytest.mark.asyncio
    async def test_query_status_provider_failed_marks_job_failed(self, session, seed_profile, seed_mock_binding):
        """When provider returns failed/expired, job should be marked failed."""
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        job = VoiceJob(
            id="test_failed_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="测试",
            processed_text="测试",
            render_plan_json="{}",
            response_json='{"provider_task_id": "mock_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        class FailedAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                from app.providers.base import AsyncTaskStatus
                return AsyncTaskStatus(
                    task_id=provider_task_id,
                    status="expired",
                    error_message="Task expired after 24h",
                    trace_id="mock_trace",
                    metadata={},
                )

        svc = AsyncRenderService()

        with patch("app.services.async_render_service.get_provider", return_value=FailedAdapter()):
            result = await svc.query_status(session, "test_failed_job")

        session.refresh(job)
        assert job.status == "failed", "Job should be marked failed when provider returns expired"
        assert "expired" in job.error_message

    @pytest.mark.asyncio
    async def test_query_status_already_success_skips_guard(self, session, seed_profile, seed_mock_binding):
        """Already-success job should return cached result without calling provider or using guard."""
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.services.resource_guard_service import get_resource_guard
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        job = VoiceJob(
            id="test_success_job",
            job_type="async_render",
            status="success",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="测试",
            processed_text="测试",
            render_plan_json="{}",
            response_json='{"provider_task_id": "mock_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        adapter_called = False

        class CheckedAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                nonlocal adapter_called
                adapter_called = True
                from app.providers.base import AsyncTaskStatus
                return AsyncTaskStatus(task_id=provider_task_id, status="success", file_url=None, trace_id="x", metadata={})

        svc = AsyncRenderService()

        # Hold t2a_async_query_download to verify it's not used
        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="t2a_async_query_download", job_id=None)

        with patch("app.services.async_render_service.get_provider", return_value=CheckedAdapter()):
            result = await svc.query_status(session, "test_success_job")

        assert adapter_called is False, "query_async_task should not be called for already-success job"
        assert result.status == "success"

        # Cleanup
        await guard._release(lease)

    @pytest.mark.asyncio
    async def test_query_status_missing_provider_task_id_marks_failed(self, session, seed_profile, seed_mock_binding):
        """When response_json has no provider_task_id, job should be marked failed."""
        from app.services.async_render_service import AsyncRenderService
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        job = VoiceJob(
            id="test_no_task_id_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="测试",
            processed_text="测试",
            render_plan_json="{}",
            response_json="{}",  # no provider_task_id
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        svc = AsyncRenderService()

        from app.core.errors import ProviderError
        with pytest.raises(ProviderError) as exc_info:
            await svc.query_status(session, "test_no_task_id_job")

        session.refresh(job)
        assert job.status == "failed", "Job should be marked failed when provider_task_id is missing"
        assert "provider task ID" in job.error_message

    @pytest.mark.asyncio
    async def test_query_status_complete_job_error_marks_failed(self, session, seed_profile, seed_mock_binding):
        """When _complete_job raises, job should be marked failed."""
        from unittest.mock import patch, AsyncMock
        from app.services.async_render_service import AsyncRenderService
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        job = VoiceJob(
            id="test_complete_error_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="测试",
            processed_text="测试",
            render_plan_json="{}",
            response_json='{"provider_task_id": "mock_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        class SuccessWithUrlAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                from app.providers.base import AsyncTaskStatus
                return AsyncTaskStatus(
                    task_id=provider_task_id,
                    status="success",
                    file_url="http://fake.url/audio.mp3",
                    trace_id="mock_trace",
                    metadata={},
                )

        async def failing_complete_job(sess, j, task_status):
            raise RuntimeError("Download failed: network error")

        svc = AsyncRenderService()

        with patch("app.services.async_render_service.get_provider", return_value=SuccessWithUrlAdapter()):
            with patch.object(svc, "_complete_job", side_effect=failing_complete_job):
                with pytest.raises(RuntimeError):
                    await svc.query_status(session, "test_complete_error_job")

        session.refresh(job)
        assert job.status == "failed", "Job should be marked failed when _complete_job raises"

    @pytest.mark.asyncio
    async def test_query_status_provider_query_error_keeps_processing(self, session, seed_profile, seed_mock_binding):
        """When adapter.query_async_task raises, job.status should stay processing (transient error)."""
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso

        now = utc_now_iso()
        job = VoiceJob(
            id="test_query_error_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="测试",
            processed_text="测试",
            render_plan_json="{}",
            response_json='{"provider_task_id": "mock_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        class QueryErrorAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                raise RuntimeError("Provider query transient error")

        svc = AsyncRenderService()

        with patch("app.services.async_render_service.get_provider", return_value=QueryErrorAdapter()):
            with pytest.raises(RuntimeError):
                await svc.query_status(session, "test_query_error_job")

        session.refresh(job)
        assert job.status == "processing", "Job should stay processing when provider query transiently fails"

    @pytest.mark.asyncio
    async def test_query_status_success_without_duration_estimates_subtitle_timeline_end(
        self, session, seed_profile, seed_mock_binding
    ):
        """When provider returns duration_ms=None and no timeline, estimate_duration_ms is used for timeline end."""
        import json
        from pathlib import Path
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso
        from app.utils.files import storage_path

        now = utc_now_iso()
        render_plan = {
            "subtitle": {"enabled": True, "type": "sentence"},
            "audio_params": {"format": "mp3"},
        }
        job = VoiceJob(
            id="test_no_duration_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="异步字幕测试",
            processed_text="异步字幕测试",
            render_plan_json=json.dumps(render_plan),
            response_json='{"provider_task_id": "mock_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        # Create a real temp audio file in storage directory
        audio_path = storage_path("audio", "test_async_duration_audio.mp3")
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(bytes([0xFF, 0xFB, 0x90, 0x00] + [0x00] * 100))

        class NoDurationAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                from app.providers.base import AsyncTaskStatus
                return AsyncTaskStatus(
                    task_id=provider_task_id,
                    status="success",
                    file_url=str(audio_path),
                    trace_id="mock_trace",
                    duration_ms=None,
                    metadata={},
                )

        svc = AsyncRenderService()

        with patch("app.services.async_render_service.get_provider", return_value=NoDurationAdapter()):
            result = await svc.query_status(session, "test_no_duration_job")

        session.refresh(job)
        assert job.status == "success", f"Job should be success, got {job.status}"

        audio_asset_resp = result.audio_asset
        assert audio_asset_resp is not None, "audio_asset should be present"
        assert audio_asset_resp.duration_ms is not None, "duration_ms should not be None"
        assert audio_asset_resp.duration_ms > 0, f"duration_ms should be > 0, got {audio_asset_resp.duration_ms}"

        subtitle_asset_resp = result.subtitle_asset
        assert subtitle_asset_resp is not None, "subtitle_asset should be present"
        timeline = subtitle_asset_resp.timeline
        assert len(timeline) > 0, "Timeline should not be empty"
        assert timeline[0]["start"] == 0.0, f"Timeline start should be 0.0, got {timeline[0]['start']}"
        assert timeline[0]["end"] > 0.0, f"Timeline end should be > 0.0 (estimated), got {timeline[0]['end']}"

    @pytest.mark.asyncio
    async def test_query_status_success_preserves_provider_timeline(
        self, session, seed_profile, seed_mock_binding
    ):
        """When provider returns a timeline in metadata, it should be preserved and not overwritten by estimate."""
        import json
        from pathlib import Path
        from unittest.mock import patch
        from app.services.async_render_service import AsyncRenderService
        from app.models.voice_job import VoiceJob
        from app.core.time import utc_now_iso
        from app.utils.files import storage_path

        now = utc_now_iso()
        render_plan = {
            "subtitle": {"enabled": True, "type": "sentence"},
            "audio_params": {"format": "mp3"},
        }
        job = VoiceJob(
            id="test_provider_timeline_job",
            job_type="async_render",
            status="processing",
            provider="minimax",
            model="speech-2.8-hd",
            profile_id="deep_night_programmer",
            binding_id="binding_mock_deep_night_programmer",
            input_text="provider timeline test",
            processed_text="provider timeline test",
            render_plan_json=json.dumps(render_plan),
            response_json='{"provider_task_id": "mock_task"}',
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        audio_path = storage_path("audio", "test_async_timeline_audio.mp3")
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(bytes([0xFF, 0xFB, 0x90, 0x00] + [0x00] * 100))

        provider_timeline = [
            {"text": "hello", "start": 0.0, "end": 1.23},
            {"text": "world", "start": 1.23, "end": 2.5},
        ]

        class ProviderTimelineAdapter:
            provider_name = "minimax"

            async def query_async_task(self, provider_task_id):
                from app.providers.base import AsyncTaskStatus
                return AsyncTaskStatus(
                    task_id=provider_task_id,
                    status="success",
                    file_url=str(audio_path),
                    trace_id="mock_trace",
                    duration_ms=None,
                    metadata={"timeline": provider_timeline},
                )

        svc = AsyncRenderService()

        with patch("app.services.async_render_service.get_provider", return_value=ProviderTimelineAdapter()):
            result = await svc.query_status(session, "test_provider_timeline_job")

        session.refresh(job)
        assert job.status == "success"

        subtitle_asset_resp = result.subtitle_asset
        assert subtitle_asset_resp is not None
        timeline = subtitle_asset_resp.timeline
        assert timeline == provider_timeline, f"Provider timeline should be preserved, got {timeline}"
        assert timeline[0]["end"] == 1.23, f"First entry end should be 1.23, got {timeline[0]['end']}"
        assert timeline[1]["end"] == 2.5, f"Second entry end should be 2.5, got {timeline[1]['end']}"


@pytest.mark.asyncio
async def test_async_query_provider_exception_resets_job_id_once_and_preserves_error(
    session, seed_profile, seed_mock_binding
):
    """provider query exception resets job_id context once and preserves original error."""
    from unittest.mock import AsyncMock, patch
    from app.core.context import get_job_id, set_job_id
    from app.models.voice_job import VoiceJob
    from app.services.async_render_service import AsyncRenderService

    # Create a processing job with provider_task_id
    job = VoiceJob(
        id="job_exception_test",
        job_type="async_render",
        status="processing",
        provider="mock",
        model="speech-2.8-hd",
        profile_id="deep_night_programmer",
        binding_id="binding_001",
        input_text="test",
        processed_text="test",
        render_plan_json="{}",
        response_json='{"provider_task_id": "mock_task_123"}',
        created_at="2026-05-13T10:00:00+00:00",
        updated_at="2026-05-13T10:00:00+00:00",
    )
    session.add(job)
    session.commit()

    old_job_id = get_job_id()

    class FailingQueryAdapter:
        provider_name = "mock"

        async def query_async_task(self, task_id):
            raise RuntimeError("provider query boom")

    svc = AsyncRenderService()

    with patch("app.services.async_render_service.get_provider", return_value=FailingQueryAdapter()):
        with pytest.raises(RuntimeError, match="provider query boom"):
            await svc.query_status(session, "job_exception_test")

    # Context should be restored
    assert get_job_id() == old_job_id


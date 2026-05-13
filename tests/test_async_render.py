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

"""Unit tests for app.services.resource_guard_service.

These tests only exercise the ResourceGuardService module in isolation.
No business services are integrated here.
No real MiniMax API calls are made.
No database access.
"""

import asyncio

import pytest

from app.services.resource_guard_service import (
    ResourceGuardService,
    ResourceLimitExceeded,
    ResourcePolicy,
    ResourceLease,
    get_resource_guard,
    reset_resource_guard_for_tests,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_guard():
    """Reset module-level singleton before and after each test to ensure isolation."""
    reset_resource_guard_for_tests()
    yield
    reset_resource_guard_for_tests()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def make_service(policies: dict[str, ResourcePolicy] | None = None) -> ResourceGuardService:
    """Create a fresh ResourceGuardService, optionally with custom policies."""
    return ResourceGuardService(policies=policies)


# ---------------------------------------------------------------------------
# test_mock_provider_unlimited
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mock_provider_unlimited():
    """mock provider should never be limited; no-op lease returned."""
    svc = make_service()

    # Acquire many times — all should succeed
    for _ in range(5):
        async with svc.guard(provider="mock", operation="voice_design", job_id="j1") as lease:
            assert lease.is_noop is True
        # snapshot should remain empty
        assert svc.snapshot() == {}

    # Different operations on mock should also work
    async with svc.guard(provider="mock", operation="t2a_stream", job_id="j2") as lease:
        assert lease.is_noop is True


# ---------------------------------------------------------------------------
# test_acquire_success_and_release
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_acquire_success_and_release():
    """Entering guard should increment slot; exiting should decrement."""
    svc = make_service()

    async with svc.guard(provider="minimax", operation="t2a_sync") as lease:
        assert lease.is_noop is False
        assert svc.current("minimax", "t2a_sync") == 1

    assert svc.current("minimax", "t2a_sync") == 0


# ---------------------------------------------------------------------------
# test_limit_exceeded
# ---------------------------------------------------------------------------


def _custom_t2a_sync_policy() -> dict[str, ResourcePolicy]:
    return {
        "minimax:t2a_sync": ResourcePolicy(
            provider="minimax", operation="t2a_sync", limit=1
        )
    }


@pytest.mark.asyncio
async def test_limit_exceeded():
    """Second concurrent guard should raise ResourceLimitExceeded."""
    svc = make_service(policies=_custom_t2a_sync_policy())

    async with svc.guard(provider="minimax", operation="t2a_sync", job_id="job1"):
        # Slot is now full
        with pytest.raises(ResourceLimitExceeded) as exc_info:
            async with svc.guard(provider="minimax", operation="t2a_sync", job_id="job2"):
                pass

        exc = exc_info.value
        assert exc.code == "RESOURCE_LIMIT_EXCEEDED"
        assert exc.status_code == 429
        assert "provider=minimax" in exc.detail
        assert "operation=t2a_sync" in exc.detail
        assert "limit=1" in exc.detail
        assert "current=1" in exc.detail
        assert "job_id=job2" in exc.detail

    # After exit, slot is free
    async with svc.guard(provider="minimax", operation="t2a_sync", job_id="job3"):
        assert svc.current("minimax", "t2a_sync") == 1


# ---------------------------------------------------------------------------
# test_release_on_exception
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_release_on_exception():
    """Exception inside guard should still release the slot."""
    svc = make_service()

    with pytest.raises(RuntimeError):
        async with svc.guard(provider="minimax", operation="voice_design"):
            assert svc.current("minimax", "voice_design") == 1
            raise RuntimeError("boom")

    # Slot must be released
    assert svc.current("minimax", "voice_design") == 0


# ---------------------------------------------------------------------------
# test_release_idempotent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_release_idempotent():
    """Calling _release twice must not cause negative current."""
    svc = make_service()

    async with svc.guard(provider="minimax", operation="voice_design", job_id="j1") as lease:
        assert svc.current("minimax", "voice_design") == 1

    # First explicit release (via guard exit already called it)
    await svc._release(lease)

    # Second explicit release — must be idempotent
    await svc._release(lease)

    assert svc.current("minimax", "voice_design") == 0
    # Keys with value 0 are retained in snapshot; only values matter
    assert all(v >= 0 for v in svc.snapshot().values())


# ---------------------------------------------------------------------------
# test_different_operations_independent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_different_operations_independent():
    """Different operations on the same provider should not share slots."""
    svc = make_service()

    # Hold t2a_sync
    async with svc.guard(provider="minimax", operation="t2a_sync", job_id="j1"):
        assert svc.current("minimax", "t2a_sync") == 1
        # voice_design should be independent
        async with svc.guard(provider="minimax", operation="voice_design", job_id="j2"):
            assert svc.current("minimax", "t2a_sync") == 1
            assert svc.current("minimax", "voice_design") == 1
        assert svc.current("minimax", "voice_design") == 0
        assert svc.current("minimax", "t2a_sync") == 1
    assert svc.current("minimax", "t2a_sync") == 0


# ---------------------------------------------------------------------------
# test_different_providers_independent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_different_providers_independent():
    """Different providers should have completely independent slot tracking."""
    svc = make_service()

    async with svc.guard(provider="minimax", operation="t2a_sync", job_id="j1"):
        assert svc.current("minimax", "t2a_sync") == 1
        # Another provider should be independent
        async with svc.guard(provider="other_provider", operation="t2a_sync", job_id="j2"):
            assert svc.current("minimax", "t2a_sync") == 1
            assert svc.current("other_provider", "t2a_sync") == 1


# ---------------------------------------------------------------------------
# test_shared_key_for_async_operations
# ---------------------------------------------------------------------------


def _async_shared_pool_policy() -> dict[str, ResourcePolicy]:
    return {
        "minimax:t2a_async_submit": ResourcePolicy(
            provider="minimax", operation="t2a_async_submit",
            limit=2, shared_key="minimax:t2a_async",
        ),
        "minimax:t2a_async_query_download": ResourcePolicy(
            provider="minimax", operation="t2a_async_query_download",
            limit=2, shared_key="minimax:t2a_async",
        ),
    }


@pytest.mark.asyncio
async def test_shared_key_for_async_operations():
    """t2a_async_submit and t2a_async_query_download should share the same pool."""
    svc = make_service(policies=_async_shared_pool_policy())

    # Take both slots with submit operations
    async with svc.guard(provider="minimax", operation="t2a_async_submit", job_id="s1"):
        assert svc.current("minimax", "t2a_async_submit") == 1
        async with svc.guard(provider="minimax", operation="t2a_async_submit", job_id="s2"):
            assert svc.current("minimax", "t2a_async_submit") == 2
            # Query should be blocked too (pool exhausted)
            with pytest.raises(ResourceLimitExceeded):
                async with svc.guard(provider="minimax", operation="t2a_async_query_download", job_id="q1"):
                    pass

    # Pool is free again
    async with svc.guard(provider="minimax", operation="t2a_async_query_download", job_id="q2"):
        assert svc.current("minimax", "t2a_async_query_download") == 1


# ---------------------------------------------------------------------------
# test_unknown_operation_default_limit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_operation_default_limit():
    """Unknown real-provider operations should default to limit=1."""
    svc = make_service()

    async with svc.guard(provider="minimax", operation="unknown_op", job_id="j1"):
        assert svc.current("minimax", "unknown_op") == 1
        with pytest.raises(ResourceLimitExceeded):
            async with svc.guard(provider="minimax", operation="unknown_op", job_id="j2"):
                pass

    assert svc.current("minimax", "unknown_op") == 0


# ---------------------------------------------------------------------------
# test_singleton_shared_state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_singleton_shared_state():
    """get_resource_guard() should return the same instance; reset should clear it."""
    # First call
    g1 = get_resource_guard()
    g2 = get_resource_guard()
    assert g1 is g2

    # Acquire a slot via first instance
    async with g1.guard(provider="minimax", operation="t2a_sync", job_id="j1"):
        assert g2.current("minimax", "t2a_sync") == 1

    # Reset
    reset_resource_guard_for_tests()

    # After reset, new instance
    g3 = get_resource_guard()
    assert g3 is not g1
    assert g3.snapshot() == {}
    assert g3.current("minimax", "t2a_sync") == 0


# ---------------------------------------------------------------------------
# test_concurrent_acquires_do_not_exceed_limit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_acquires_do_not_exceed_limit():
    """With limit=1, only one of N concurrent guards should succeed; others raise."""
    svc = make_service()

    accepted_count = 0
    rejected_count = 0

    async def try_acquire(job_id: str):
        nonlocal accepted_count, rejected_count
        try:
            async with svc.guard(provider="minimax", operation="t2a_stream", job_id=job_id):
                accepted_count += 1
        except ResourceLimitExceeded:
            rejected_count += 1

    # Run 5 coroutines concurrently; limit=1 so exactly 1 accepts, 4 reject
    await asyncio.gather(*[try_acquire(f"job_{i}") for i in range(5)])

    assert accepted_count == 1, f"expected 1 accepted, got {accepted_count}"
    assert rejected_count == 4, f"expected 4 rejected, got {rejected_count}"
    # All slots should be released
    assert svc.current("minimax", "t2a_stream") == 0


# ---------------------------------------------------------------------------
# test_voice_design_limit_1
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_voice_design_limit_1():
    """minimax voice_design default limit is 1."""
    svc = make_service()

    async with svc.guard(provider="minimax", operation="voice_design", job_id="j1"):
        assert svc.current("minimax", "voice_design") == 1
        with pytest.raises(ResourceLimitExceeded):
            async with svc.guard(provider="minimax", operation="voice_design", job_id="j2"):
                pass
    assert svc.current("minimax", "voice_design") == 0


# ---------------------------------------------------------------------------
# test_batch_longtext_limit_1
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_longtext_limit_1():
    """minimax batch_longtext default limit is 1."""
    svc = make_service()

    async with svc.guard(provider="minimax", operation="batch_longtext", job_id="j1"):
        assert svc.current("minimax", "batch_longtext") == 1
        with pytest.raises(ResourceLimitExceeded):
            async with svc.guard(provider="minimax", operation="batch_longtext", job_id="j2"):
                pass
    assert svc.current("minimax", "batch_longtext") == 0


# ---------------------------------------------------------------------------
# test_no_negative_current_after_multiple_release_attempts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_negative_current_after_multiple_release_attempts():
    """Repeated release on same lease must not drive current negative."""
    svc = make_service()

    lease = await svc._acquire(provider="minimax", operation="voice_design", job_id="j1")
    assert svc.current("minimax", "voice_design") == 1

    await svc._release(lease)
    await svc._release(lease)  # Idempotent second call
    await svc._release(lease)  # Third

    assert svc.current("minimax", "voice_design") == 0
    assert all(v >= 0 for v in svc.snapshot().values())


# ---------------------------------------------------------------------------
# test_guard_key_normalizes_to_lowercase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guard_key_normalizes_to_lowercase():
    """Provider and operation keys should be normalized to lowercase."""
    svc = make_service()

    async with svc.guard(provider="MiniMax", operation="T2A_Sync", job_id="j1"):
        assert svc.current("minimax", "t2a_sync") == 1
        assert svc.current("MINIMAX", "T2A_SYNC") == 1

    assert svc.current("MiniMax", "T2A_Sync") == 0

"""Resource Guard Service — in-process resource admission control layer.

Architecture position:
    Cost Guard → Resource Guard → Provider Adapter

第一版设计原则（来自 docs/P7_RESOURCE_GUARD_SPEC.md P7-A/P7-A1）：
- 内存级并发控制，单进程有效
- 不做 Redis / 分布式锁 / 任务排队 / 预算预占 / 持久化
- provider + operation 维度并发限制
- mock provider 不限制
- 超限时直接 raise ResourceLimitExceeded，不排队
- 使用 guard(...) async context manager，不暴露 _acquire 给业务代码
- 异常自动 release
- reset_resource_guard_for_tests() 用于测试隔离
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.errors import VoiceLabError
from app.core.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger("resource_guard")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ResourceLimitExceeded(VoiceLabError):
    """Raised when a resource slot is already at capacity."""

    status_code = 429  # Too Many Requests — 必须使用 status_code，与 VoiceLabError 体系一致
    code = "RESOURCE_LIMIT_EXCEEDED"

    def __init__(
        self,
        provider: str,
        operation: str,
        limit: int,
        current: int,
        *,
        job_id: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider
        self.operation = operation
        self.limit = limit
        self.current = current
        self.job_id = job_id
        self.model = model

        detail_parts = [
            f"provider={provider}",
            f"operation={operation}",
            f"limit={limit}",
            f"current={current}",
        ]
        if job_id:
            detail_parts.append(f"job_id={job_id}")
        if model:
            detail_parts.append(f"model={model}")

        detail = ", ".join(detail_parts)
        super().__init__(
            message="当前生成任务较多，请稍后再试",
            detail=detail,
        )


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResourcePolicy:
    """Definition of a resource slot limit for a provider + operation pair."""

    provider: str
    operation: str
    limit: int | None  # None means unlimited
    description: str = ""
    shared_key: str | None = None  # if set, this operation shares its pool with other operations


@dataclass
class ResourceLease:
    """A temporary claim on a resource slot, returned by guard(...)."""

    provider: str
    operation: str
    key: str
    limit: int | None
    job_id: str | None = None
    model: str | None = None
    acquired_at: float | None = None
    is_noop: bool = False
    _released: bool = False

    @property
    def released(self) -> bool:
        return self._released


# ---------------------------------------------------------------------------
# Default policies
# ---------------------------------------------------------------------------


def _build_default_policies() -> dict[str, ResourcePolicy]:
    """Build the default policy map for minimax operations.

    Keys are "{provider}:{operation}" in lowercase.
    """
    policies: list[ResourcePolicy] = [
        # T2A sync
        ResourcePolicy(provider="minimax", operation="t2a_sync", limit=2,
                       description="普通同步生成，并发限制2"),
        # Async — submit and query share the same concurrency pool
        ResourcePolicy(provider="minimax", operation="t2a_async_submit", limit=2,
                       shared_key="minimax:t2a_async",
                       description="异步提交，与 query 共享并发池"),
        ResourcePolicy(provider="minimax", operation="t2a_async_query_download", limit=2,
                       shared_key="minimax:t2a_async",
                       description="查询下载，与 submit 共享并发池"),
        # Stream
        ResourcePolicy(provider="minimax", operation="t2a_stream", limit=1,
                       description="WebSocket 流式，长连接资源宝贵"),
        # Preview
        ResourcePolicy(provider="minimax", operation="voice_preview", limit=2,
                       description="直接试听音色"),
        ResourcePolicy(provider="minimax", operation="binding_voice_preview", limit=2,
                       description="绑定试听"),
        # Variants
        ResourcePolicy(provider="minimax", operation="voice_variants", limit=1,
                       description="多版本试音，一次请求放大多个 T2A"),
        # Voice design / clone
        ResourcePolicy(provider="minimax", operation="voice_design", limit=1,
                       description="声音设计，高成本，串行"),
        ResourcePolicy(provider="minimax", operation="voice_clone_upload", limit=1,
                       description="克隆音频上传，串行"),
        ResourcePolicy(provider="minimax", operation="voice_clone_create", limit=1,
                       description="克隆任务创建，高成本，串行"),
        # Import
        ResourcePolicy(provider="minimax", operation="provider_voice_import_verify", limit=1,
                       description="音色导入验证"),
        # Batch
        ResourcePolicy(provider="minimax", operation="batch_longtext", limit=1,
                       description="批量长文本任务入口，防止重复提交"),
        ResourcePolicy(provider="minimax", operation="batch_script", limit=1,
                       description="剧本任务入口，防止重复提交"),
        # batch_segment_render — not included in default policies; evaluated in P7-E
    ]

    return {f"{p.provider}:{p.operation}": p for p in policies}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ResourceGuardService:
    """In-process resource admission control.

    第一版只做内存级并发控制，不做 Redis/排队/持久化。

    并发控制使用 asyncio.Lock + _active 原子计数：
    - _active 同时作为并发控制状态和 introspection 观测状态
    - 不使用 Semaphore，不等待，不排队
    """

    # Default limit for unknown real-provider operations (conservative: allow one)
    _UNKNOWN_OPERATION_DEFAULT_LIMIT = 1

    def __init__(
        self,
        policies: dict[str, ResourcePolicy] | None = None,
    ):
        self._policies: dict[str, ResourcePolicy] = policies or _build_default_policies()
        self._active: dict[str, int] = {}   # key -> current active count; single source of truth
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Internal: _acquire / _release
    # ------------------------------------------------------------------

    async def _acquire(
        self,
        *,
        provider: str,
        operation: str,
        model: str | None = None,
        job_id: str | None = None,
    ) -> ResourceLease:
        """Acquire a resource slot. Raises ResourceLimitExceeded if at capacity."""
        provider = provider.lower()
        operation = operation.lower()

        # mock provider always gets a no-op lease
        if provider == "mock":
            return ResourceLease(
                provider=provider,
                operation=operation,
                key=f"mock:{operation}",
                limit=None,
                model=model,
                job_id=job_id,
                acquired_at=time.time(),
                is_noop=True,
            )

        policy = self._policies.get(f"{provider}:{operation}")
        if policy is None:
            limit = self._UNKNOWN_OPERATION_DEFAULT_LIMIT
            key = f"{provider}:{operation}"
        else:
            key = policy.shared_key or f"{policy.provider}:{policy.operation}"
            limit = policy.limit

        # Unlimited: always succeeds
        if limit is None:
            return ResourceLease(
                provider=provider,
                operation=operation,
                key=key,
                limit=None,
                model=model,
                job_id=job_id,
                acquired_at=time.time(),
                is_noop=True,
            )

        # The lock serializes the entire check-and-increment as one atomic operation.
        # All concurrent callers queue here; only one enters at a time.
        async with self._lock:
            current = self._active.get(key, 0)
            if current >= limit:
                logger.warning(
                    "resource_rejected provider=%s operation=%s model=%s job_id=%s key=%s limit=%s current=%s reason=limit_exceeded",
                    provider, operation, model, job_id, key, limit, current,
                )
                raise ResourceLimitExceeded(
                    provider=provider,
                    operation=operation,
                    limit=limit,
                    current=current,
                    job_id=job_id,
                    model=model,
                )

            self._active[key] = current + 1
            logger.debug(
                "resource_acquired provider=%s operation=%s model=%s job_id=%s key=%s limit=%s current=%s",
                provider, operation, model, job_id, key, limit, self._active[key],
            )

        logger.info(
            "resource_acquire_attempt provider=%s operation=%s model=%s job_id=%s key=%s limit=%s",
            provider, operation, model, job_id, key, limit,
        )

        return ResourceLease(
            provider=provider,
            operation=operation,
            key=key,
            limit=limit,
            model=model,
            job_id=job_id,
            acquired_at=time.time(),
            is_noop=False,
        )

    async def _release(self, lease: ResourceLease) -> None:
        """Release a resource slot. Idempotent — safe to call multiple times."""
        if lease.is_noop:
            return

        if lease._released:
            return

        async with self._lock:
            if lease._released:
                return
            current = self._active.get(lease.key, 0)
            if current <= 1:
                self._active.pop(lease.key, None)
            else:
                self._active[lease.key] = current - 1
            # Mark as released while still holding the lock to ensure idempotency
            lease._released = True

            logger.debug(
                "resource_released provider=%s operation=%s model=%s job_id=%s key=%s limit=%s current=%s",
                lease.provider, lease.operation, lease.model, lease.job_id,
                lease.key, lease.limit, self._active.get(lease.key, 0),
            )

    # ------------------------------------------------------------------
    # Public: guard (...) async context manager
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def guard(
        self,
        *,
        provider: str,
        operation: str,
        model: str | None = None,
        job_id: str | None = None,
    ):
        """Business-facing async context manager for resource admission.

        Usage:
            async with resource_guard.guard(provider="minimax", operation="t2a_stream", job_id=job.id):
                async for msg in adapter.render_stream(plan):
                    ...
        """
        lease = await self._acquire(provider=provider, operation=operation, model=model, job_id=job_id)
        try:
            yield lease
        finally:
            await self._release(lease)

    # ------------------------------------------------------------------
    # Introspection (useful in tests)
    # ------------------------------------------------------------------

    def current(self, provider: str, operation: str) -> int:
        """Return current active count for a provider:operation key."""
        key = f"{provider.lower()}:{operation.lower()}"
        policy = self._policies.get(key)
        if policy and policy.shared_key:
            key = policy.shared_key
        return self._active.get(key, 0)

    def snapshot(self) -> dict[str, int]:
        """Return a copy of all active slot counts."""
        return dict(self._active)

    def reset(self) -> None:
        """Clear all active slot counts. Use only in tests."""
        self._active.clear()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_guard: ResourceGuardService | None = None


def get_resource_guard() -> ResourceGuardService:
    """Return the module-level ResourceGuardService singleton.

    All business services should use this rather than instantiating their own.
    """
    global _guard
    if _guard is None:
        _guard = ResourceGuardService()
    return _guard


def reset_resource_guard_for_tests() -> None:
    """Reset the module-level singleton. For test isolation only — do not call in production."""
    global _guard
    if _guard is not None:
        _guard.reset()
    _guard = None
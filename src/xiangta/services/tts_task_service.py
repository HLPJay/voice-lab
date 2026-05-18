"""
TTS Task Service — in-memory task state management.

C7 MVP: synchronous execution, process-local memory storage.
No Redis, no SQLite, no background worker, no Celery.
"""
from __future__ import annotations

import random
import string
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator


_TASKS: dict[str, dict] = {}


def clear_tts_tasks_for_tests() -> None:
    _TASKS.clear()


def _make_task_id() -> str:
    return "TTS_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class TtsTaskService:
    def __init__(self, tts_orchestrator: "TtsOrchestrator | None" = None) -> None:
        self._tts = tts_orchestrator

    async def create_task(
        self,
        *,
        text: str,
        voice_preset: str,
        tone: str,
        recipient: str,
        scene: str,
        profile_id: str | None = None,
    ) -> dict:
        """
        C7 MVP: synchronously generate TTS and store completed/failed task.

        Returns create response dict with taskId/status/pollUrl.
        """
        task_id = _make_task_id()
        now = _utc_now()

        _TASKS[task_id] = {
            "taskId": task_id,
            "status": "running",
            "audioUrl": None,
            "durationMs": None,
            "charCount": None,
            "voicePreset": voice_preset,
            "tone": tone,
            "message": None,
            "errorKind": None,
            "retryable": False,
            "createdAt": now,
            "updatedAt": now,
        }

        if self._tts is not None:
            try:
                result = await self._tts.generate(
                    text=text,
                    voice_preset=voice_preset,
                    tone=tone,
                    recipient=recipient,
                    scene=scene,
                    profile_id=profile_id,
                )
                _TASKS[task_id].update(
                    status="completed",
                    audioUrl=result.get("audioUrl"),
                    durationMs=result.get("durationMs"),
                    charCount=len(text),
                    message=result.get("message"),
                    updatedAt=_utc_now(),
                )
            except Exception as exc:
                from src.xiangta.services.error_translator import XiangTaError, translate

                xi = exc if isinstance(exc, XiangTaError) else translate(exc)
                _TASKS[task_id].update(
                    status="failed",
                    charCount=len(text),
                    errorKind=xi.kind,
                    message=xi.message,
                    retryable=xi.retryable,
                    updatedAt=_utc_now(),
                )
        else:
            _TASKS[task_id].update(
                status="failed",
                errorKind="no_provider",
                message="TTS orchestrator not configured.",
                retryable=True,
                updatedAt=_utc_now(),
            )

        return {
            "taskId": task_id,
            "status": _TASKS[task_id]["status"],
            "pollUrl": f"/api/xiangta/tts/tasks/{task_id}",
            "errorKind": _TASKS[task_id].get("errorKind"),
            "message": _TASKS[task_id].get("message"),
        }

    def get_task(self, task_id: str) -> dict | None:
        """Return task data dict, or None if not found."""
        return _TASKS.get(task_id) or None

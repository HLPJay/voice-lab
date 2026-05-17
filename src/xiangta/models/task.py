"""Task — TTS 异步任务状态追踪（预留，MVP 同步返回）。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional

TaskStatus = Literal["pending", "processing", "done", "failed"]


@dataclass
class TtsTask:
    task_id: str
    status: TaskStatus
    text: str
    voice_preset: str
    tone: str
    audio_url: Optional[str] = None
    duration_secs: Optional[float] = None
    error: Optional[str] = None
    # TODO(P17-A3): 如需异步队列，添加 celery task_id / created_at 等字段

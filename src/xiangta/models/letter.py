"""Letter — 已生成的信笺（MVP 存 localStorage，后续可迁移服务端）。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Letter:
    letter_id: str
    recipient: str
    scene: str
    style: str
    raw_text: str
    final_text: str
    voice_preset: str
    tone: str
    created_at: str          # ISO 8601
    audio_url: Optional[str] = None
    duration_secs: Optional[float] = None
    title: Optional[str] = None
    favorited: bool = False
    open_count: int = 0
    opened_at: Optional[str] = None

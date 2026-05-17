"""Draft — 用户在 Input/Suggestions 阶段的临时草稿（内存/缓存，不持久化）。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Draft:
    recipient: str
    scene: str
    raw_text: str
    style: Optional[str] = None
    final_text: Optional[str] = None
    voice_preset: Optional[str] = None
    tone: Optional[str] = None
    # TODO(P17-A2): 添加 suggestions 缓存字段

"""Suggestion — 一条 LLM 生成的文案建议。"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Suggestion:
    style: str          # restrained | gentle | sincere
    style_label: str    # 克制版 | 温柔版 | 真诚版
    fits_for: str       # 对应场景下的推荐说明
    text: str           # 生成的文案正文
    char_count: int

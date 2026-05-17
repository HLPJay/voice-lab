"""
XiangTa 产品配置模型。

只定义配置 DTO / 投影模型，不读文件，不调用 Core。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProductVoiceMapping:
    id: str
    label: str
    desc: str
    gender_style: str | None
    suitable_recipients: list[str] = field(default_factory=list)
    recommended_scenes: list[str] = field(default_factory=list)
    default_tone: str = ""
    enabled: bool = True
    sort_order: int = 0
    core_profile_id: str = ""
    provider_policy: str | None = None
    render_overrides: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("ProductVoiceMapping.id 不能为空")
        if not self.label.strip():
            raise ValueError("ProductVoiceMapping.label 不能为空")
        if not self.core_profile_id.strip():
            raise ValueError("ProductVoiceMapping.core_profile_id 不能为空")


@dataclass(frozen=True)
class PublicVoicePreset:
    id: str
    label: str
    desc: str
    gender_style: str | None
    suitable_recipients: list[str] = field(default_factory=list)
    recommended_scenes: list[str] = field(default_factory=list)
    default_tone: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("PublicVoicePreset.id 不能为空")
        if not self.label.strip():
            raise ValueError("PublicVoicePreset.label 不能为空")


@dataclass(frozen=True)
class TonePreset:
    id: str
    label: str
    desc: str
    style_hint: str
    copywriting_style: str | None = None
    render_overrides: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    sort_order: int = 0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("TonePreset.id 不能为空")
        if not self.label.strip():
            raise ValueError("TonePreset.label 不能为空")
        if not self.style_hint.strip():
            raise ValueError("TonePreset.style_hint 不能为空")


@dataclass(frozen=True)
class ProductLimits:
    max_raw_text_chars: int = 500
    max_tts_chars: int = 500
    max_suggestions: int = 3
    allow_real_provider: bool = False
    default_audio_format: str = "mp3"
    need_subtitle_default: bool = True


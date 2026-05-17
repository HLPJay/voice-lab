"""
XiangTa API 请求/响应 Pydantic 模型。

前端传入的字段全部是产品语义（recipient, scene, style, voicePreset, tone）。
不暴露 voice_id、model_id、sample_rate、provider、API key 等底层概念。
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

# ── 枚举值 ────────────────────────────────────────────────────────────────────

RecipientId   = Literal["lover", "family", "friend", "self"]
SceneId       = Literal["miss", "sorry", "thanks", "comfort", "night"]
StyleId       = Literal["restrained", "gentle", "sincere"]
VoicePresetId = Literal["female-gentle", "male-gentle", "female-bright", "male-mature"]
ToneId        = Literal["restrained", "gentle", "sincere", "whisper", "bedtime"]
ProviderKind  = Literal["not_integrated", "ok", "degraded", "quota", "error", "unknown"]


# ── 通用响应包装 ───────────────────────────────────────────────────────────────

class OkResponse(BaseModel):
    ok: bool = True


class ErrorResponse(BaseModel):
    ok: bool = False
    errorKind: str
    message: str
    retryable: bool = False


# ── Bootstrap 子模型 ───────────────────────────────────────────────────────────

class RecipientItem(BaseModel):
    id: str
    label: str
    hint: Optional[str] = None
    enabled: bool = True


class SceneItem(BaseModel):
    id: str
    label: str
    hint: Optional[str] = None
    enabled: bool = True


class StyleItem(BaseModel):
    id: str
    label: str
    desc: Optional[str] = None
    enabled: bool = True


class VoicePresetItem(BaseModel):
    id: str
    name: str
    desc: str
    suitable_recipients: list[str] = []
    recommended_scenes: list[str] = []
    default_tone: str
    core_binding_key: str
    enabled: bool = True


class TonePresetItem(BaseModel):
    id: str
    label: str
    desc: str
    style_hint: str
    enabled: bool = True


class LimitsData(BaseModel):
    maxRawTextChars: int = 500
    maxTtsChars: int = 500
    maxSuggestions: int = 3


class ProviderStatusData(BaseModel):
    kind: ProviderKind
    label: str
    detail: str
    quotaPct: float


class BootstrapData(BaseModel):
    recipients: list[RecipientItem]
    scenes: list[SceneItem]
    styles: list[StyleItem]
    voicePresets: list[VoicePresetItem]
    tonePresets: list[TonePresetItem]
    limits: LimitsData
    providerStatus: ProviderStatusData


class BootstrapResponse(OkResponse):
    data: BootstrapData


class ProviderStatusResponse(OkResponse):
    data: ProviderStatusData


# ── POST /suggestions ─────────────────────────────────────────────────────────

class SuggestionsRequest(BaseModel):
    recipient: RecipientId
    scene: SceneId
    rawText: str = Field(min_length=4, max_length=500)


class SuggestionItem(BaseModel):
    style: StyleId
    styleLabel: str
    fitsFor: str
    text: str
    charCount: int


class SuggestionsData(BaseModel):
    summary: str
    intent: str
    suggestions: list[SuggestionItem]


class SuggestionsResponse(OkResponse):
    data: SuggestionsData


# ── POST /tts ─────────────────────────────────────────────────────────────────

class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    voicePreset: VoicePresetId
    tone: ToneId
    recipient: RecipientId
    scene: SceneId


class TtsContract(BaseModel):
    """Product→Core bridge echo — safe product-layer identifiers only."""
    coreBindingKey: str
    voicePreset: str
    tone: str
    toneHint: str
    scene: str


class TtsData(BaseModel):
    taskId: str
    status: str                          # "dry_run" | "completed"
    audioUrl: Optional[str] = None
    durationMs: Optional[int] = None
    charCount: int
    voicePreset: str
    tone: str
    message: Optional[str] = None
    contract: Optional[TtsContract] = None


class TtsResponse(OkResponse):
    data: TtsData


# ── POST /letters ─────────────────────────────────────────────────────────────

class CreateLetterRequest(BaseModel):
    recipient: RecipientId
    scene: SceneId
    style: StyleId
    rawText: str
    finalText: str
    voicePreset: VoicePresetId
    tone: ToneId
    audioUrl: Optional[str] = None
    durationSecs: Optional[float] = None
    title: Optional[str] = None


class CreateLetterData(BaseModel):
    letterId: str
    createdAt: str  # ISO 8601


class CreateLetterResponse(OkResponse):
    data: CreateLetterData

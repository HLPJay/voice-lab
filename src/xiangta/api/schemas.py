"""
XiangTa API 请求/响应 Pydantic 模型。

前端传入的字段全部是产品语义（recipient, scene, style, voicePreset, tone）。
不暴露 voice_id、model_id、sample_rate、provider、API key 等底层概念。
"""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

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
    model_config = ConfigDict(populate_by_name=True)

    id: str
    label: str
    desc: str
    gender_style: Optional[str] = Field(default=None, alias="genderStyle")
    suitable_recipients: list[str] = Field(default_factory=list, alias="suitableRecipients")
    recommended_scenes: list[str] = Field(default_factory=list, alias="recommendedScenes")
    default_tone: str = Field(alias="defaultTone")
    enabled: bool = True


class TonePresetItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    label: str
    desc: str
    style_hint: str = Field(alias="styleHint")
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
    voicePresetId: str
    tone: str
    toneHint: str
    scene: str
    mode: str = "dry_run"


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


# ── Admin Config (read-only) ──────────────────────────────────────────────────

class AdminVoiceMappingItem(BaseModel):
    id: str
    label: str
    desc: str
    genderStyle: Optional[str] = None
    suitableRecipients: list[str] = Field(default_factory=list)
    recommendedScenes: list[str] = Field(default_factory=list)
    defaultTone: str
    enabled: bool
    sortOrder: int
    coreProfileId: str
    providerPolicy: Optional[str] = None
    renderOverrides: dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class AdminTonePresetItem(BaseModel):
    id: str
    label: str
    desc: str
    styleHint: str
    copywritingStyle: Optional[str] = None
    renderOverrides: dict[str, Any] = Field(default_factory=dict)
    enabled: bool
    sortOrder: int


class AdminConfigData(BaseModel):
    voiceMappings: list[AdminVoiceMappingItem]
    tonePresets: list[AdminTonePresetItem]
    recipients: list[dict]
    scenes: list[dict]
    limits: LimitsData


class AdminConfigResponse(OkResponse):
    data: AdminConfigData


class AdminVoiceMappingsResponse(OkResponse):
    data: list[AdminVoiceMappingItem]


class AdminTonePresetsResponse(OkResponse):
    data: list[AdminTonePresetItem]


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

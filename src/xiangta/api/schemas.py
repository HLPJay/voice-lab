"""
XiangTa API 请求/响应 Pydantic 模型。

前端传入的字段全部是产品语义（recipient, scene, style, voicePreset, tone）。
不暴露 voice_id、model_id、sample_rate、provider、API key 等底层概念。
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

# ── 枚举值 ────────────────────────────────────────────────────────────────────

RecipientId = Literal["lover", "family", "friend", "self"]
SceneId     = Literal["miss", "sorry", "thanks", "comfort", "night"]
StyleId     = Literal["restrained", "gentle", "sincere"]
VoicePresetId = Literal["female-gentle", "male-gentle", "female-bright", "male-mature"]
ToneId      = Literal["restrained", "gentle", "sincere", "whisper", "bedtime"]


# ── 通用响应包装 ───────────────────────────────────────────────────────────────

class OkResponse(BaseModel):
    ok: bool = True


class ErrorResponse(BaseModel):
    ok: bool = False
    errorKind: str
    message: str
    retryable: bool = False


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


class TtsData(BaseModel):
    taskId: str
    audioUrl: str
    durationSecs: float
    charCount: int
    voicePreset: VoicePresetId
    tone: ToneId


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


# ── GET /provider/status ──────────────────────────────────────────────────────

ProviderKind = Literal["ok", "degraded", "quota", "error"]


class ProviderStatusData(BaseModel):
    kind: ProviderKind
    label: str
    detail: str
    quotaPct: float


class ProviderStatusResponse(OkResponse):
    data: ProviderStatusData

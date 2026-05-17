"""
Voice Lab Gateway — XiangTa 访问 Core 的唯一入口。

【强制约束】
- 本文件是产品层与 Core 之间的隔离边界。
- 产品服务层（copywriting_service, tts_orchestrator 等）只能 import 本模块，
  不得直接 import 任何 src.voice_lab.* 模块。
- 本模块公共方法参数只接受产品层稳定字段和内部 CoreRenderTarget，
  不接受 voice_id、model_id、sample_rate 等 Provider-specific 参数。
- Provider-specific 参数的解析在 Core 内部或 gateway 的私有实现中完成，
  对外完全不可见。
- P17-INIT 阶段：只定义接口边界，不 import provider adapter，不调用真实 MiniMax。

Core Contract Gap 登记：
  如发现 Core 缺口，在 docs/agent/NEXT_TASKS.md 的 Core Contract Gap 区段登记。
"""
from __future__ import annotations

from dataclasses import dataclass
import uuid
from typing import Any


# TODO(P17-A3): import Core 服务（只允许 import Core 公开服务接口）
# from src.voice_lab.services.tts_service import TTSService
# from src.voice_lab.services.provider_service import ProviderService


@dataclass(frozen=True)
class CoreRenderTarget:
    profile_id: str
    provider: str | None = None
    need_subtitle: bool = True
    output_format: str = "url"
    audio_format: str = "mp3"
    speed: float | None = None
    vol: float | None = None
    pitch: int | None = None
    emotion: str | None = None


class VoiceLabGateway:
    """
    代理对 Voice Lab Core 的所有调用。

    公共方法只接受产品层稳定字段或内部 CoreRenderTarget。
    Provider-specific 参数（voice_id、model_id、sample_rate）在本模块或 Core 内部解析，
    不暴露给上层 Product Server。
    """

    async def generate_tts(
        self,
        *,
        text: str,
        target: CoreRenderTarget,
        tone: str,
        scene: str,
        style: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate TTS through archived Voice Lab Core.

        Public XiangTa boundary uses product-level binding keys only.
        Provider-specific params (voice_id, model_id, sample_rate, bitrate)
        are resolved inside gateway/Core, never by callers.

        Args:
            text:             要朗读的文案
            target:           供 Core render 使用的内部目标对象
            tone:             语气预设 ID（如 "gentle"）
            scene:            场景 ID（如 "miss"），用于 Core 内部语境
            style:            风格 ID（如 "restrained"），可选
            metadata:         扩展元数据，用于日志 / 统计

        Returns:
            {"audio_url": str, "duration_secs": float, "task_id": str}
        """
        # TODO(P17-A3): 调用 Core TTSService
        # Core 内部负责将 target 解析为实际 provider render 请求
        raise NotImplementedError

    async def generate_tts_dry_run(
        self,
        *,
        text: str,
        target: CoreRenderTarget,
        tone: str,
        tone_hint: str,
        scene: str,
        voice_preset_id: str,
        style: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Dry-run contract — validates product→Core bridge without calling any Provider.

        No real network call. No API key read. No Provider import.

        Returns:
            {
              "taskId": "dryrun_<hex>",
              "status": "dry_run",
              "audioUrl": None,
              "durationMs": None,
              "message": "dry-run only, no provider call",
              "contract": {
                "voicePresetId": str,
                "tone": str,
                "toneHint": str,
                "scene": str,
                "mode": "dry_run",
              },
            }
        """
        _ = (text, target, style, metadata)
        return {
            "taskId": f"dryrun_{uuid.uuid4().hex[:8]}",
            "status": "dry_run",
            "audioUrl": None,
            "durationMs": None,
            "message": "dry-run only, no provider call",
            "contract": {
                "voicePresetId": voice_preset_id,
                "tone": tone,
                "toneHint": tone_hint,
                "scene": scene,
                "mode": "dry_run",
            },
        }

    async def get_provider_status(self) -> dict[str, Any]:
        """Query Voice Lab Core provider status.

        Returns product-level status only:
            {"kind": str, "label": str, "detail": str, "quota_pct": float}

        Does not expose provider-internal fields.
        """
        # TODO(P17-A1): 调用 Core ProviderService
        raise NotImplementedError

    async def generate_llm_text(
        self,
        *,
        prompt: str,
        max_tokens: int = 512,
    ) -> str:
        """Call Core LLM service for copywriting suggestions.

        Returns generated text string.

        Core Contract Gap 候选：如 Core 无 LLM 公开接口，登记 GAP-001。
        """
        # TODO(P17-A4): 调用 Core LLM 服务
        raise NotImplementedError


# 模块级单例
_gateway: VoiceLabGateway | None = None


def get_gateway() -> VoiceLabGateway:
    global _gateway
    if _gateway is None:
        _gateway = VoiceLabGateway()
    return _gateway

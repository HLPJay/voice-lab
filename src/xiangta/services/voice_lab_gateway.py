"""
Voice Lab Gateway — XiangTa 访问 Core 的唯一入口。

【强制约束】
- 本文件是产品层与 Core 之间的隔离边界。
- 产品服务层（copywriting_service, tts_orchestrator 等）只能 import 本模块，
  不得直接 import 任何 src.voice_lab.* 模块。
- 本模块不含产品业务逻辑，只做调用代理和参数透传。
- P17-INIT 阶段：只定义接口边界，不 import provider adapter，不调用真实 MiniMax。

Core Contract Gap 登记：
  如发现 Core 缺口，在 docs/agent/NEXT_TASKS.md 的 Core Contract Gap 区段登记，
  不在本文件内绕过边界直接实现。
"""
from __future__ import annotations

from typing import Any


# TODO(P17-A1): import Core 服务（仅允许 import 公开服务接口，不得 import adapter 层）
# from src.voice_lab.services.tts_service import TTSService
# from src.voice_lab.services.provider_service import ProviderService


class VoiceLabGateway:
    """
    代理对 Voice Lab Core 的所有调用。
    实例由 DI 注入或作为模块级单例使用。
    """

    async def generate_tts(
        self,
        *,
        text: str,
        voice_id: str,
        model_id: str,
        speed: float,
        sample_rate: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        调用 Core TTS 服务生成语音。

        参数由 preset_mapper 解析后传入，产品层不直接构造这些参数。

        Returns:
            {"audio_url": str, "duration_secs": float, "task_id": str}
        """
        # TODO(P17-A3): 调用 Core TTSService
        raise NotImplementedError

    async def get_provider_status(self) -> dict[str, Any]:
        """
        查询底层 Provider 当前状态。

        Returns:
            {"kind": str, "label": str, "detail": str, "quota_pct": float}
        """
        # TODO(P17-A1): 调用 Core ProviderService
        raise NotImplementedError

    async def generate_llm_text(
        self,
        *,
        prompt: str,
        max_tokens: int = 512,
        **kwargs: Any,
    ) -> str:
        """
        调用 Core LLM 服务生成文本（用于文案建议）。

        Returns:
            生成的文本字符串
        """
        # TODO(P17-A2): 调用 Core LLM 服务（待确认 Core 是否已暴露 LLM 接口）
        # Core Contract Gap 候选：如 Core 无 LLM 公开接口，登记 GAP-001
        raise NotImplementedError


# 模块级单例，供 DI 不可用时直接 import
_gateway: VoiceLabGateway | None = None


def get_gateway() -> VoiceLabGateway:
    global _gateway
    if _gateway is None:
        _gateway = VoiceLabGateway()
    return _gateway

"""
Bootstrap Service — 专职组装 GET /api/xiangta/bootstrap 的响应数据。

职责：
  - 从 config.loader 读取 recipients / scenes / voicePresets / tonePresets
  - 从 config.bootstrap_config 取 styles / limits（静态）
  - 从 ProviderStatusService 取当前 providerStatus

不承担产品主流程编排，不持有 TTS / LLM / Letter 子服务。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.xiangta.config import loader as _loader
from src.xiangta.config.bootstrap_config import LIMITS, STYLES

if TYPE_CHECKING:
    from src.xiangta.services.provider_status_service import ProviderStatusService


class BootstrapService:

    def __init__(self, provider_status: "ProviderStatusService") -> None:
        self._provider_status = provider_status

    async def get_bootstrap(self) -> dict[str, Any]:
        """
        返回前端启动所需的完整配置快照。
        只读操作：读配置文件 + 查询 provider 状态。
        不调用 voice_lab Core，不调用任何外部 API。
        """
        provider_status = await self._provider_status.get_status()

        return {
            "recipients":     _loader.load_recipients(),
            "scenes":         _loader.load_scenes(),
            "styles":         STYLES,
            "voicePresets":   _loader.load_voice_presets(),
            "tonePresets":    _loader.load_tone_presets(),
            "limits":         LIMITS,
            "providerStatus": provider_status,
        }


def create_bootstrap_service() -> "BootstrapService":
    """默认工厂：A1 阶段不需要真实 gateway。"""
    from src.xiangta.services.provider_status_service import ProviderStatusService
    return BootstrapService(provider_status=ProviderStatusService(gateway=None))

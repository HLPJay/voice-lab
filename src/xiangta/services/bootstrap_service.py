"""
Bootstrap Service — 专职组装 GET /api/xiangta/bootstrap 的响应数据。

职责：
  - 从 ProductConfigRepository 读取 recipients / scenes / voicePresets / tonePresets / limits
  - 从 config.bootstrap_config 取 styles（静态）
  - 从 ProviderStatusService 取当前 providerStatus

不承担产品主流程编排，不持有 TTS / LLM / Letter 子服务。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.xiangta.config.bootstrap_config import STYLES

if TYPE_CHECKING:
    from src.xiangta.config.product_config_repository import ProductConfigRepository
    from src.xiangta.services.provider_status_service import ProviderStatusService


class BootstrapService:

    def __init__(
        self,
        provider_status: "ProviderStatusService",
        config_repository: "ProductConfigRepository",
    ) -> None:
        self._provider_status = provider_status
        self._config_repository = config_repository

    async def get_bootstrap(self) -> dict[str, Any]:
        """
        返回前端启动所需的完整配置快照。
        只读操作：读产品配置 + 查询 provider 状态。
        不调用 voice_lab Core，不调用任何外部 API。
        """
        provider_status = await self._provider_status.get_status()
        voice_presets = [
            {
                "id": item.id,
                "label": item.label,
                "desc": item.desc,
                "genderStyle": item.gender_style,
                "suitableRecipients": list(item.suitable_recipients),
                "recommendedScenes": list(item.recommended_scenes),
                "defaultTone": item.default_tone,
                "enabled": item.enabled,
            }
            for item in self._config_repository.list_public_voice_presets()
        ]
        tone_presets = [
            {
                "id": item.id,
                "label": item.label,
                "desc": item.desc,
                "styleHint": item.style_hint,
                "enabled": item.enabled,
            }
            for item in self._config_repository.list_tone_presets()
            if item.enabled
        ]
        limits = self._config_repository.get_limits()

        return {
            "recipients":     self._config_repository.list_recipients(),
            "scenes":         self._config_repository.list_scenes(),
            "styles":         STYLES,
            "voicePresets":   voice_presets,
            "tonePresets":    tone_presets,
            "limits":         {
                "maxRawTextChars": limits.max_raw_text_chars,
                "maxTtsChars": limits.max_tts_chars,
                "maxSuggestions": limits.max_suggestions,
            },
            "providerStatus": provider_status,
        }


def create_bootstrap_service() -> "BootstrapService":
    """默认工厂：A1 阶段不需要真实 gateway。"""
    from src.xiangta.config.product_config_repository import ProductConfigRepository
    from src.xiangta.services.provider_status_service import ProviderStatusService
    return BootstrapService(
        provider_status=ProviderStatusService(gateway=None),
        config_repository=ProductConfigRepository(),
    )

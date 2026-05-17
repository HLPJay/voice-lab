"""
Product Service — 产品主流程编排。

职责：作为对外门面，将请求路由到各子服务。
不持有配置读取逻辑、静态常量、或 Bootstrap 组装细节。

子服务分工：
  bootstrap_service   — 配置快照组装（GET /bootstrap）
  provider_status     — Provider 状态查询
  copywriting         — LLM 文案生成（A4）
  tts                 — TTS 任务调度（A3）
  letters             — 信笺 CRUD（A4+）
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.bootstrap_service import BootstrapService
    from src.xiangta.services.copywriting_service import CopywritingService
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator
    from src.xiangta.services.letter_service import LetterService
    from src.xiangta.services.provider_status_service import ProviderStatusService


class ProductService:

    def __init__(
        self,
        bootstrap: "BootstrapService",
        provider_status: "ProviderStatusService",
        copywriting: "CopywritingService | None" = None,
        tts: "TtsOrchestrator | None" = None,
        letters: "LetterService | None" = None,
    ) -> None:
        self._bootstrap       = bootstrap
        self._provider_status = provider_status
        self._copywriting     = copywriting
        self._tts             = tts
        self._letters         = letters

    async def get_bootstrap(self) -> dict:
        return await self._bootstrap.get_bootstrap()

    async def get_provider_status(self) -> dict:
        return await self._provider_status.get_status()

    async def get_suggestions(self, recipient: str, scene: str, raw_text: str) -> dict:
        """参见 copywriting_service.generate_suggestions。"""
        # TODO(P17-A4)
        raise NotImplementedError

    async def generate_tts(
        self, *, text: str, voice_preset: str, tone: str, recipient: str, scene: str
    ) -> dict:
        """委托给 TtsOrchestrator；ProductService 只做门面。"""
        return await self._tts.generate(
            text=text,
            voice_preset=voice_preset,
            tone=tone,
            recipient=recipient,
            scene=scene,
        )


def create_product_service() -> "ProductService":
    """默认工厂：A2 阶段装配 dry-run TtsOrchestrator（不接真实 Provider）。"""
    from src.xiangta.config.product_config_repository import ProductConfigRepository
    from src.xiangta.services.provider_status_service import ProviderStatusService
    from src.xiangta.services.bootstrap_service import BootstrapService
    from src.xiangta.services.preset_mapper import PresetMapper
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

    provider_status = ProviderStatusService(gateway=None)
    config_repository = ProductConfigRepository()
    bootstrap       = BootstrapService(
        provider_status=provider_status,
        config_repository=config_repository,
    )
    gateway         = VoiceLabGateway()
    mapper          = PresetMapper()
    tts             = TtsOrchestrator(gateway=gateway, mapper=mapper)
    return ProductService(bootstrap=bootstrap, provider_status=provider_status, tts=tts)

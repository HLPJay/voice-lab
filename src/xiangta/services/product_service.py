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
    from src.xiangta.config.product_config_repository import ProductConfigRepository
    from src.xiangta.services.admin_config_service import AdminConfigService


class ProductService:

    def __init__(
        self,
        bootstrap: "BootstrapService",
        provider_status: "ProviderStatusService",
        copywriting: "CopywritingService | None" = None,
        tts: "TtsOrchestrator | None" = None,
        letters: "LetterService | None" = None,
        config_repository: "ProductConfigRepository | None" = None,
        admin_config_service: "AdminConfigService | None" = None,
    ) -> None:
        self._bootstrap             = bootstrap
        self._provider_status       = provider_status
        self._copywriting           = copywriting
        self._tts                   = tts
        self._letters               = letters
        self._config_repository     = config_repository
        self._admin_config_service  = admin_config_service

    async def get_bootstrap(self) -> dict:
        return await self._bootstrap.get_bootstrap()

    async def get_provider_status(self) -> dict:
        return await self._provider_status.get_status()

    def get_admin_voice_mappings(self) -> list[dict]:
        """Return full voice mapping data including admin fields (coreProfileId, etc.)."""
        if self._config_repository is None:
            return []
        return [
            {
                "id": m.id,
                "label": m.label,
                "desc": m.desc,
                "genderStyle": m.gender_style,
                "suitableRecipients": list(m.suitable_recipients),
                "recommendedScenes": list(m.recommended_scenes),
                "defaultTone": m.default_tone,
                "enabled": m.enabled,
                "sortOrder": m.sort_order,
                "coreProfileId": m.core_profile_id,
                "providerPolicy": m.provider_policy,
                "renderOverrides": dict(m.render_overrides),
                "notes": m.notes,
            }
            for m in self._config_repository.list_voice_mappings()
        ]

    def get_admin_tone_presets(self) -> list[dict]:
        """Return full tone preset data including admin fields (renderOverrides, etc.)."""
        if self._config_repository is None:
            return []
        return [
            {
                "id": t.id,
                "label": t.label,
                "desc": t.desc,
                "styleHint": t.style_hint,
                "copywritingStyle": t.copywriting_style,
                "renderOverrides": dict(t.render_overrides),
                "enabled": t.enabled,
                "sortOrder": t.sort_order,
            }
            for t in self._config_repository.list_tone_presets()
        ]

    def get_admin_config(self) -> dict:
        """Return full admin config snapshot."""
        if self._config_repository is None:
            limits = {"maxRawTextChars": 500, "maxTtsChars": 500, "maxSuggestions": 3}
            return {
                "voiceMappings": [],
                "tonePresets": [],
                "recipients": [],
                "scenes": [],
                "limits": limits,
            }
        lim = self._config_repository.get_limits()
        return {
            "voiceMappings": self.get_admin_voice_mappings(),
            "tonePresets": self.get_admin_tone_presets(),
            "recipients": self._config_repository.list_recipients(),
            "scenes": self._config_repository.list_scenes(),
            "limits": {
                "maxRawTextChars": lim.max_raw_text_chars,
                "maxTtsChars": lim.max_tts_chars,
                "maxSuggestions": lim.max_suggestions,
            },
        }

    def update_admin_voice_mapping(self, id: str, data: dict) -> dict:
        if self._admin_config_service is None:
            raise RuntimeError("admin_config_service not wired")
        return self._admin_config_service.update_voice_mapping(id, data)

    def toggle_admin_voice_mapping_enabled(self, id: str, enabled: bool) -> dict:
        if self._admin_config_service is None:
            raise RuntimeError("admin_config_service not wired")
        return self._admin_config_service.toggle_voice_mapping_enabled(id, enabled)

    def update_admin_tone_preset(self, id: str, data: dict) -> dict:
        if self._admin_config_service is None:
            raise RuntimeError("admin_config_service not wired")
        return self._admin_config_service.update_tone_preset(id, data)

    def toggle_admin_tone_preset_enabled(self, id: str, enabled: bool) -> dict:
        if self._admin_config_service is None:
            raise RuntimeError("admin_config_service not wired")
        return self._admin_config_service.toggle_tone_preset_enabled(id, enabled)

    async def get_suggestions(self, recipient: str, scene: str, raw_text: str) -> dict:
        """委托给 CopywritingService；ProductService 只做门面。"""
        if self._copywriting is None:
            raise RuntimeError("copywriting service not wired")
        return await self._copywriting.generate_suggestions(
            recipient=recipient,
            scene=scene,
            raw_text=raw_text,
        )

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
    """默认工厂：装配安全的 Core render mock-path 编排，不真实访问网络。"""
    from src.xiangta.config.product_config_repository import ProductConfigRepository
    from src.xiangta.services.provider_status_service import ProviderStatusService
    from src.xiangta.services.bootstrap_service import BootstrapService
    from src.xiangta.services.tone_preset_service import TonePresetService
    from src.xiangta.services.tts_orchestrator import TtsOrchestrator
    from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

    from src.xiangta.config.product_config_writer import ProductConfigWriter
    from src.xiangta.services.admin_config_service import AdminConfigService
    from src.xiangta.services.copywriting_service import CopywritingService

    config_repository = ProductConfigRepository()
    gateway         = VoiceLabGateway()
    provider_status = ProviderStatusService(gateway=gateway)
    bootstrap       = BootstrapService(
        provider_status=provider_status,
        config_repository=config_repository,
    )
    voice_mapping_service = VoicePresetMappingService(config_repository=config_repository)
    tone_preset_service = TonePresetService(config_repository=config_repository)
    limits = config_repository.get_limits()
    tts             = TtsOrchestrator(
        gateway=gateway,
        voice_mapping_service=voice_mapping_service,
        tone_preset_service=tone_preset_service,
        max_tts_chars=limits.max_tts_chars,
        use_dry_run=False,
    )
    writer = ProductConfigWriter()
    admin_config_svc = AdminConfigService(writer=writer)
    copywriting = CopywritingService(gateway=gateway)
    return ProductService(
        bootstrap=bootstrap,
        provider_status=provider_status,
        tts=tts,
        config_repository=config_repository,
        admin_config_service=admin_config_svc,
        copywriting=copywriting,
    )

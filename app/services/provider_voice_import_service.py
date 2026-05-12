import json

from sqlmodel import Session

from app.core.errors import ProviderError, ValidationError
from app.core.logging import get_logger
from app.domain.enums import ProviderVoiceStatus
from app.domain.schemas import (
    AudioAssetResponse,
    ProviderVoiceImportRequest,
    ProviderVoiceImportResponse,
    ProviderVoicePreviewRequest,
)
from app.repositories.provider_voice_repo import upsert_provider_voice
from app.services.cost_guard_service import CostGuardService
from app.services.provider_voice_preview_service import ProviderVoicePreviewService


class ProviderVoiceImportService:
    def __init__(self):
        self.logger = get_logger("provider_voice_import")
        self.cost_guard = CostGuardService()
        self.preview_service = ProviderVoicePreviewService()

    async def import_voice(
        self,
        session: Session,
        request: ProviderVoiceImportRequest,
    ) -> ProviderVoiceImportResponse:
        if request.voice_type not in ("voice_cloning", "voice_generation"):
            raise ValidationError(
                "Invalid voice_type",
                "voice_type must be 'voice_cloning' or 'voice_generation'",
            )

        verified_audio_asset: AudioAssetResponse | None = None
        verified = False

        if request.verify:
            self.logger.info(
                "import_verify provider=%s voice_id=%s model=%s",
                request.provider, request.provider_voice_id, request.model,
            )
            try:
                self.cost_guard.require_confirmed(
                    request.provider, "provider_voice_import_verify", request.confirm_cost
                )
                preview_req = ProviderVoicePreviewRequest(
                    provider=request.provider,
                    provider_voice_id=request.provider_voice_id,
                    model=request.model,
                    text=request.preview_text,
                    audio_format="mp3",
                    output_format="hex",
                    need_subtitle=False,
                    confirm_cost=request.confirm_cost,
                )
                preview_result = await self.preview_service.preview(
                    session, request.provider, preview_req
                )
                verified_audio_asset = preview_result.audio_asset
                verified = True
                self.logger.info(
                    "import_verify_success provider=%s voice_id=%s",
                    request.provider, request.provider_voice_id,
                )
            except ValidationError:
                raise  # ValidationError must propagate with its own status_code (422)
            except Exception as exc:
                self.logger.warning(
                    "import_verify_failed provider=%s voice_id=%s error=%s",
                    request.provider, request.provider_voice_id, str(exc),
                )
                raise ProviderError(
                    "导入失败：试听验证不通过",
                    f"voice_id={request.provider_voice_id}，错误：{str(exc)}",
                )
        else:
            self.logger.info(
                "import_skip_verify provider=%s voice_id=%s",
                request.provider, request.provider_voice_id,
            )

        name = request.name or request.provider_voice_id
        description = request.description or f"手动导入的{'克隆' if request.voice_type == 'voice_cloning' else '设计'}音色"

        metadata = {
            "source": "manual_import",
            "verified": verified,
            "model": request.model,
            "preview_text": request.preview_text if request.verify else None,
        }

        pv = upsert_provider_voice(
            session,
            provider=request.provider,
            provider_voice_id=request.provider_voice_id,
            voice_type=request.voice_type,
            name=name,
            description=description,
            status=ProviderVoiceStatus.available,
            metadata=metadata,
        )

        self.logger.info(
            "import_success provider=%s voice_id=%s voice_type=%s verified=%s",
            request.provider, request.provider_voice_id, request.voice_type, verified,
        )

        return ProviderVoiceImportResponse(
            provider=request.provider,
            provider_voice_id=request.provider_voice_id,
            voice_type=request.voice_type,
            name=pv.name,
            status=pv.status,
            verified=verified,
            audio_asset=verified_audio_asset,
            message="导入成功",
        )

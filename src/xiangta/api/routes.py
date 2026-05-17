"""
XiangTa API 路由定义。

NOTE: 本模块不注册到主应用（app/main.py）。
      通过 include_router 在独立 XiangTa 入口或测试中挂载。

实现状态（P17-XIANGTA-A2）：
  GET  /bootstrap       ✅ 可用（读取配置，固定 not_integrated）
  GET  /provider/status ✅ 可用（固定 not_integrated）
  POST /tts             ✅ dry-run 合约（不调用真实 Provider）
  POST /suggestions     ⏳ 未实现（A4）
  POST /letters         ⏳ 未实现（A4+）
  GET  /letters         ⏳ 未实现（A4+）
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.xiangta.api.schemas import (
    AdminConfigResponse,
    AdminTonePresetItemResponse,
    AdminTonePresetUpdateRequest,
    AdminTonePresetsResponse,
    AdminToggleEnabledRequest,
    AdminVoiceMappingItemResponse,
    AdminVoiceMappingUpdateRequest,
    AdminVoiceMappingsResponse,
    BootstrapResponse,
    ProviderStatusResponse,
    SuggestionsRequest,
    SuggestionsResponse,
    TtsRequest,
    TtsResponse,
)
from src.xiangta.config.product_config_writer import (
    ConfigNotFoundError,
    InvalidConfigInputError,
    InvalidCoreProfileError,
    InvalidRenderOverrideError,
)
from src.xiangta.services.error_translator import XiangTaError
from src.xiangta.services.product_service import create_product_service

router = APIRouter(prefix="/api/xiangta", tags=["xiangta"])


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap():
    """返回前端启动所需的配置快照。

    A1 阶段：从本地 configs/*.json 读取，providerStatus 固定为 not_integrated。
    不调用 voice_lab Core，不调用外部 API。
    """
    svc = create_product_service()
    data = await svc.get_bootstrap()
    return BootstrapResponse(data=data)


@router.get("/provider/status", response_model=ProviderStatusResponse)
async def provider_status():
    """实时查询 Provider 状态。

    A1 阶段：固定返回 not_integrated。
    A3 阶段后：转为真实查询 voice_lab_gateway。
    """
    svc = create_product_service()
    data = await svc.get_provider_status()
    return ProviderStatusResponse(data=data)


@router.get("/admin/config", response_model=AdminConfigResponse)
async def admin_config():
    """Admin-only: return full config snapshot including Core mapping fields."""
    svc = create_product_service()
    data = svc.get_admin_config()
    return AdminConfigResponse(data=data)


@router.get("/admin/voice-mappings", response_model=AdminVoiceMappingsResponse)
async def admin_voice_mappings():
    """Admin-only: return all voice mappings with Core fields."""
    svc = create_product_service()
    return AdminVoiceMappingsResponse(data=svc.get_admin_voice_mappings())


@router.get("/admin/tone-presets", response_model=AdminTonePresetsResponse)
async def admin_tone_presets():
    """Admin-only: return all tone presets with render overrides."""
    svc = create_product_service()
    return AdminTonePresetsResponse(data=svc.get_admin_tone_presets())


def _write_error_response(exc: Exception) -> JSONResponse:
    if isinstance(exc, ConfigNotFoundError):
        return JSONResponse(status_code=404, content={"ok": False, "errorKind": "not_found", "message": str(exc)})
    if isinstance(exc, (InvalidConfigInputError, InvalidRenderOverrideError, InvalidCoreProfileError)):
        return JSONResponse(status_code=422, content={"ok": False, "errorKind": "validation_error", "message": str(exc)})
    return JSONResponse(status_code=500, content={"ok": False, "errorKind": "write_failed", "message": str(exc)})


@router.put("/admin/voice-mappings/{id}", response_model=AdminVoiceMappingItemResponse)
async def admin_update_voice_mapping(id: str, body: AdminVoiceMappingUpdateRequest):
    """Admin-only: update a voice mapping by id."""
    svc = create_product_service()
    try:
        data = svc.update_admin_voice_mapping(id, body.model_dump(exclude_unset=True))
        return AdminVoiceMappingItemResponse(data=data)
    except (ConfigNotFoundError, InvalidConfigInputError, InvalidRenderOverrideError, InvalidCoreProfileError) as exc:
        return _write_error_response(exc)


@router.patch("/admin/voice-mappings/{id}/enabled", response_model=AdminVoiceMappingItemResponse)
async def admin_toggle_voice_mapping_enabled(id: str, body: AdminToggleEnabledRequest):
    """Admin-only: toggle enabled state of a voice mapping."""
    svc = create_product_service()
    try:
        data = svc.toggle_admin_voice_mapping_enabled(id, body.enabled)
        return AdminVoiceMappingItemResponse(data=data)
    except ConfigNotFoundError as exc:
        return _write_error_response(exc)


@router.put("/admin/tone-presets/{id}", response_model=AdminTonePresetItemResponse)
async def admin_update_tone_preset(id: str, body: AdminTonePresetUpdateRequest):
    """Admin-only: update a tone preset by id."""
    svc = create_product_service()
    try:
        data = svc.update_admin_tone_preset(id, body.model_dump(exclude_unset=True))
        return AdminTonePresetItemResponse(data=data)
    except (ConfigNotFoundError, InvalidConfigInputError, InvalidRenderOverrideError) as exc:
        return _write_error_response(exc)


@router.patch("/admin/tone-presets/{id}/enabled", response_model=AdminTonePresetItemResponse)
async def admin_toggle_tone_preset_enabled(id: str, body: AdminToggleEnabledRequest):
    """Admin-only: toggle enabled state of a tone preset."""
    svc = create_product_service()
    try:
        data = svc.toggle_admin_tone_preset_enabled(id, body.enabled)
        return AdminTonePresetItemResponse(data=data)
    except ConfigNotFoundError as exc:
        return _write_error_response(exc)


@router.post("/suggestions", response_model=SuggestionsResponse)
async def suggestions(body: SuggestionsRequest):
    """生成 3 条模板文案建议（B5-1：不调用真实 LLM）。"""
    svc = create_product_service()
    try:
        data = await svc.get_suggestions(
            recipient=body.recipient,
            scene=body.scene,
            raw_text=body.rawText,
        )
        return SuggestionsResponse(data=data)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "errorKind": "invalid_input", "message": str(exc), "retryable": False},
        )


@router.post("/tts")
async def tts(body: TtsRequest):
    """TTS dry-run 合约（A2）。

    不调用真实 Provider，不生成真实音频，不读取真实 API key。
    返回 taskId / status / contract，供前端验证链路。
    """
    svc = create_product_service()
    try:
        data = await svc.generate_tts(
            text=body.text,
            voice_preset=body.voicePreset,
            tone=body.tone,
            recipient=body.recipient,
            scene=body.scene,
        )
        return TtsResponse(data=data)
    except XiangTaError as exc:
        return JSONResponse(status_code=400, content=exc.to_dict())


@router.post("/letters")
async def create_letter():
    """保存信笺（A4+ 实现，当前返回 501）。"""
    raise HTTPException(status_code=501, detail="not_integrated")


@router.get("/letters")
async def list_letters():
    """获取信笺列表（A4+ 实现，当前返回 501）。"""
    raise HTTPException(status_code=501, detail="not_integrated")

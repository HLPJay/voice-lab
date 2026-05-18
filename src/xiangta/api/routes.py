"""
XiangTa API 路由定义。

NOTE: 本模块不注册到主应用（app/main.py）。
      通过 include_router 在独立 XiangTa 入口或测试中挂载。

实现状态：
  GET  /bootstrap             ✅ 可用
  GET  /provider/status       ✅ 可用（固定 not_integrated）
  GET  /voice-presets         ✅ 可用，公开产品声线（无 coreProfileId）
  GET  /core/profiles         ✅ B9 可用，读取 Core profiles
  POST /tts                   ✅ B9 可用，支持 profileId → Core render
  POST /suggestions           ✅ 可用，当前为模板文案，不调用真实 LLM
  POST /letters               ✅ 可用，当前为进程内内存存储
  GET  /letters               ✅ 可用，当前为进程内内存存储
  /admin/*                    ✅ 本地/Admin 配置接口，生产前需鉴权或 dev-only gate
"""
from fastapi import APIRouter, Depends, Header, HTTPException
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
    CoreProfilesResponse,
    CreateLetterRequest,
    CreateLetterResponse,
    ListLettersResponse,
    ProviderStatusResponse,
    SuggestionsRequest,
    SuggestionsResponse,
    TtsRequest,
    TtsResponse,
    VoicePresetsResponse,
)
from src.xiangta.config.product_config_writer import (
    ConfigNotFoundError,
    InvalidConfigInputError,
    InvalidCoreProfileError,
    InvalidRenderOverrideError,
)
from src.xiangta.config.runtime_config import load_runtime_config
from src.xiangta.services.error_translator import XiangTaError
from src.xiangta.services.product_service import create_product_service

router = APIRouter(prefix="/api/xiangta", tags=["xiangta"])


def _admin_forbidden() -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "ok": False,
            "errorKind": "admin_forbidden",
            "message": "Admin API is not enabled or token is invalid.",
            "retryable": False,
        },
    )


async def require_admin(x_xiangta_admin_token: str | None = Header(default=None)) -> None:
    config = load_runtime_config()
    if not config.admin_enabled:
        raise _admin_forbidden()
    if not config.admin_token:
        raise _admin_forbidden()
    if x_xiangta_admin_token != config.admin_token:
        raise _admin_forbidden()


@router.get("/core/profiles", response_model=CoreProfilesResponse)
async def core_profiles():
    """
    B9: 返回 Core 已有人设列表，供 H5 选择 profileId 后发起 TTS。
    - 配置了 Core：返回真实 profiles，source="core"。
    - 未配置 Core：返回空列表，source="not_integrated"，不 500。
    - 响应不包含 forbidden fields（api_key, provider_voice_id, binding_id 等）。
    """
    svc = create_product_service()
    data = await svc.list_core_profiles()
    return CoreProfilesResponse(data=data)


@router.get("/voice-presets", response_model=VoicePresetsResponse)
async def voice_presets():
    """
    Public voice presets API for formal H5.
    Returns only product-layer fields (no coreProfileId, providerPolicy, renderOverrides, etc.).
    Only enabled presets are returned.
    """
    svc = create_product_service()
    data = svc.list_public_voice_presets()
    return VoicePresetsResponse(data=data)


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


@router.get("/admin/config", response_model=AdminConfigResponse, dependencies=[Depends(require_admin)])
async def admin_config():
    """Admin-only: return full config snapshot including Core mapping fields."""
    svc = create_product_service()
    data = svc.get_admin_config()
    return AdminConfigResponse(data=data)


@router.get("/admin/voice-mappings", response_model=AdminVoiceMappingsResponse, dependencies=[Depends(require_admin)])
async def admin_voice_mappings():
    """Admin-only: return all voice mappings with Core fields."""
    svc = create_product_service()
    return AdminVoiceMappingsResponse(data=svc.get_admin_voice_mappings())


@router.get("/admin/tone-presets", response_model=AdminTonePresetsResponse, dependencies=[Depends(require_admin)])
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


@router.put("/admin/voice-mappings/{id}", response_model=AdminVoiceMappingItemResponse, dependencies=[Depends(require_admin)])
async def admin_update_voice_mapping(id: str, body: AdminVoiceMappingUpdateRequest):
    """Admin-only: update a voice mapping by id."""
    svc = create_product_service()
    try:
        data = svc.update_admin_voice_mapping(id, body.model_dump(exclude_unset=True))
        return AdminVoiceMappingItemResponse(data=data)
    except (ConfigNotFoundError, InvalidConfigInputError, InvalidRenderOverrideError, InvalidCoreProfileError) as exc:
        return _write_error_response(exc)


@router.patch("/admin/voice-mappings/{id}/enabled", response_model=AdminVoiceMappingItemResponse, dependencies=[Depends(require_admin)])
async def admin_toggle_voice_mapping_enabled(id: str, body: AdminToggleEnabledRequest):
    """Admin-only: toggle enabled state of a voice mapping."""
    svc = create_product_service()
    try:
        data = svc.toggle_admin_voice_mapping_enabled(id, body.enabled)
        return AdminVoiceMappingItemResponse(data=data)
    except ConfigNotFoundError as exc:
        return _write_error_response(exc)


@router.put("/admin/tone-presets/{id}", response_model=AdminTonePresetItemResponse, dependencies=[Depends(require_admin)])
async def admin_update_tone_preset(id: str, body: AdminTonePresetUpdateRequest):
    """Admin-only: update a tone preset by id."""
    svc = create_product_service()
    try:
        data = svc.update_admin_tone_preset(id, body.model_dump(exclude_unset=True))
        return AdminTonePresetItemResponse(data=data)
    except (ConfigNotFoundError, InvalidConfigInputError, InvalidRenderOverrideError) as exc:
        return _write_error_response(exc)


@router.patch("/admin/tone-presets/{id}/enabled", response_model=AdminTonePresetItemResponse, dependencies=[Depends(require_admin)])
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
            profile_id=body.profileId,  # B9: optional direct profileId path
        )
        return TtsResponse(data=data)
    except XiangTaError as exc:
        return JSONResponse(status_code=400, content=exc.to_dict())


@router.post("/letters", response_model=CreateLetterResponse)
async def create_letter(body: CreateLetterRequest):
    """保存信笺（B6-1：进程内内存存储）。"""
    svc = create_product_service()
    data = await svc.create_letter(body.model_dump())
    return CreateLetterResponse(data=data)


@router.get("/letters", response_model=ListLettersResponse)
async def list_letters(limit: int = 50, offset: int = 0):
    """获取信笺列表（B6-1：进程内内存存储）。"""
    svc = create_product_service()
    data = await svc.list_letters(limit=limit, offset=offset)
    return ListLettersResponse(data=data)

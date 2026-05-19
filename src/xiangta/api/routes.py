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
  POST /tts/tasks             ✅ C7 可用，同步执行 TTS，内存存储 task
  GET  /tts/tasks/{taskId}   ✅ C7 可用，轮询 task 状态
  POST /suggestions           ✅ 可用，当前为模板文案，不调用真实 LLM
  POST /letters               ✅ 可用，当前为进程内内存存储
  GET  /letters               ✅ 可用，当前为进程内内存存储
  PATCH /letters/{id}/favorite ✅ 可用
  /admin/*                    ✅ 本地/Admin 配置接口，生产前需鉴权或 dev-only gate
"""
import urllib.parse

import httpx
from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from src.xiangta.api.error_contract import error_response
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
    TtsTaskCreateResponse,
    TtsTaskStatusResponse,
    UpdateLetterFavoriteRequest,
    UpdateLetterFavoriteResponse,
    VoiceBindingsStatusResponse,
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


def admin_guard_response(x_xiangta_admin_token: str | None) -> JSONResponse | None:
    """Return flat forbidden JSONResponse if token is invalid, else None."""
    config = load_runtime_config()
    if not config.admin_enabled:
        return error_response(
            status_code=403,
            error_kind="admin_forbidden",
            message="Admin API is not enabled or token is invalid.",
            retryable=False,
        )
    if not config.admin_token:
        return error_response(
            status_code=403,
            error_kind="admin_forbidden",
            message="Admin API is not enabled or token is invalid.",
            retryable=False,
        )
    if x_xiangta_admin_token != config.admin_token:
        return error_response(
            status_code=403,
            error_kind="admin_forbidden",
            message="Admin API is not enabled or token is invalid.",
            retryable=False,
        )
    return None


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


@router.get("/voice-bindings/status", response_model=VoiceBindingsStatusResponse)
async def voice_bindings_status():
    """
    Public: return voice preset binding status for formal H5 Step 3.

    Does NOT expose coreProfileId.
    - bound=true when coreProfileId is set and not a placeholder.
    - coreAvailable=True/False only when Core is connected and reachable.
    - When Core is not connected, coreAvailable=null and reason reflects connection state.
    """
    svc = create_product_service()
    data = await svc.get_voice_binding_status()
    return VoiceBindingsStatusResponse(data=data)


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
async def admin_config(x_xiangta_admin_token: str | None = Header(default=None)):
    """Admin-only: return full config snapshot including Core mapping fields."""
    guard = admin_guard_response(x_xiangta_admin_token)
    if guard is not None:
        return guard
    svc = create_product_service()
    data = svc.get_admin_config()
    return AdminConfigResponse(data=data)


@router.get("/admin/voice-mappings", response_model=AdminVoiceMappingsResponse)
async def admin_voice_mappings(x_xiangta_admin_token: str | None = Header(default=None)):
    """Admin-only: return all voice mappings with Core fields."""
    guard = admin_guard_response(x_xiangta_admin_token)
    if guard is not None:
        return guard
    svc = create_product_service()
    return AdminVoiceMappingsResponse(data=svc.get_admin_voice_mappings())


@router.get("/admin/tone-presets", response_model=AdminTonePresetsResponse)
async def admin_tone_presets(x_xiangta_admin_token: str | None = Header(default=None)):
    """Admin-only: return all tone presets with render overrides."""
    guard = admin_guard_response(x_xiangta_admin_token)
    if guard is not None:
        return guard
    svc = create_product_service()
    return AdminTonePresetsResponse(data=svc.get_admin_tone_presets())


def _write_error_response(exc: Exception) -> JSONResponse:
    if isinstance(exc, ConfigNotFoundError):
        return error_response(status_code=404, error_kind="not_found", message=str(exc))
    if isinstance(exc, (InvalidConfigInputError, InvalidRenderOverrideError, InvalidCoreProfileError)):
        return error_response(status_code=422, error_kind="validation_error", message=str(exc))
    return error_response(status_code=500, error_kind="write_failed", message=str(exc))


@router.put("/admin/voice-mappings/{id}", response_model=AdminVoiceMappingItemResponse)
async def admin_update_voice_mapping(id: str, body: AdminVoiceMappingUpdateRequest, x_xiangta_admin_token: str | None = Header(default=None)):
    """Admin-only: update a voice mapping by id."""
    guard = admin_guard_response(x_xiangta_admin_token)
    if guard is not None:
        return guard
    svc = create_product_service()
    try:
        data = svc.update_admin_voice_mapping(id, body.model_dump(exclude_unset=True))
        return AdminVoiceMappingItemResponse(data=data)
    except (ConfigNotFoundError, InvalidConfigInputError, InvalidRenderOverrideError, InvalidCoreProfileError) as exc:
        return _write_error_response(exc)


@router.patch("/admin/voice-mappings/{id}/enabled", response_model=AdminVoiceMappingItemResponse)
async def admin_toggle_voice_mapping_enabled(id: str, body: AdminToggleEnabledRequest, x_xiangta_admin_token: str | None = Header(default=None)):
    """Admin-only: toggle enabled state of a voice mapping."""
    guard = admin_guard_response(x_xiangta_admin_token)
    if guard is not None:
        return guard
    svc = create_product_service()
    try:
        data = svc.toggle_admin_voice_mapping_enabled(id, body.enabled)
        return AdminVoiceMappingItemResponse(data=data)
    except ConfigNotFoundError as exc:
        return _write_error_response(exc)


@router.put("/admin/tone-presets/{id}", response_model=AdminTonePresetItemResponse)
async def admin_update_tone_preset(id: str, body: AdminTonePresetUpdateRequest, x_xiangta_admin_token: str | None = Header(default=None)):
    """Admin-only: update a tone preset by id."""
    guard = admin_guard_response(x_xiangta_admin_token)
    if guard is not None:
        return guard
    svc = create_product_service()
    try:
        data = svc.update_admin_tone_preset(id, body.model_dump(exclude_unset=True))
        return AdminTonePresetItemResponse(data=data)
    except (ConfigNotFoundError, InvalidConfigInputError, InvalidRenderOverrideError) as exc:
        return _write_error_response(exc)


@router.patch("/admin/tone-presets/{id}/enabled", response_model=AdminTonePresetItemResponse)
async def admin_toggle_tone_preset_enabled(id: str, body: AdminToggleEnabledRequest, x_xiangta_admin_token: str | None = Header(default=None)):
    """Admin-only: toggle enabled state of a tone preset."""
    guard = admin_guard_response(x_xiangta_admin_token)
    if guard is not None:
        return guard
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
        return error_response(
            status_code=400,
            error_kind="invalid_input",
            message=str(exc),
            retryable=False,
        )
    except XiangTaError as exc:
        return error_response(
            status_code=400,
            error_kind=exc.kind,
            message=exc.message,
            retryable=exc.retryable,
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
        return error_response(
            status_code=400,
            error_kind=exc.kind,
            message=exc.message,
            retryable=exc.retryable,
        )


@router.post("/tts/tasks", response_model=TtsTaskCreateResponse)
async def create_tts_task(body: TtsRequest):
    """
    C7: Submit a TTS task and immediately execute it synchronously.

    Returns taskId/status/pollUrl.
    Business errors are stored as failed tasks (not HTTP 400).
    """
    svc = create_product_service()
    data = await svc.create_tts_task(
        text=body.text,
        voice_preset=body.voicePreset,
        tone=body.tone,
        recipient=body.recipient,
        scene=body.scene,
        profile_id=body.profileId,
    )
    return TtsTaskCreateResponse(data=data)


@router.get("/tts/tasks/{task_id}", response_model=TtsTaskStatusResponse)
async def get_tts_task(task_id: str):
    """
    C7: Poll task status by taskId.

    Returns task data or 404 flat error if not found.
    """
    svc = create_product_service()
    task = svc.get_tts_task(task_id)
    if task is None:
        return error_response(
            status_code=404,
            error_kind="not_found",
            message="TTS task not found.",
            retryable=False,
        )
    return TtsTaskStatusResponse(data=task)


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


@router.patch("/letters/{letter_id}/favorite", response_model=UpdateLetterFavoriteResponse)
async def update_letter_favorite(letter_id: str, body: UpdateLetterFavoriteRequest):
    """更新信笺收藏状态。"""
    svc = create_product_service()
    updated = await svc.update_letter_favorite(letter_id, body.favorited)
    if updated is None:
        return error_response(
            status_code=404,
            error_kind="not_found",
            message="Letter not found.",
            retryable=False,
        )
    return UpdateLetterFavoriteResponse(data=updated)


# ---------------------------------------------------------------------------
# Same-origin audio proxy (P25V-FIX1)
#
# Mobile browsers cannot reach 127.0.0.1 / localhost audio URLs returned by
# Core.  This endpoint fetches the audio server-side and streams it back
# through the same origin as the H5 page.
#
# Security: only URLs whose host:port match core_base_url are allowed.
# ---------------------------------------------------------------------------

def _parse_core_netloc(core_base_url: str) -> str:
    """Return 'host:port' or 'host' from the configured core_base_url."""
    parsed = urllib.parse.urlparse(core_base_url)
    return parsed.netloc  # e.g. '127.0.0.1:8000'


@router.get("/audio/proxy")
async def audio_proxy(
    request: Request,
    url: str = Query(default=""),
):
    """
    Proxy a Core audio asset URL through the same origin so that mobile
    browsers can play it without hitting a localhost address.

    Only URLs whose host:port match the configured core_base_url are
    allowed — this is NOT an open proxy.
    """
    # 1. Require url parameter
    if not url:
        return error_response(
            status_code=400,
            error_kind="bad_request",
            message="Missing required query parameter: url",
            retryable=False,
        )

    # 2. Require http/https scheme
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        parsed = None

    if not parsed or parsed.scheme not in ("http", "https"):
        return error_response(
            status_code=400,
            error_kind="bad_request",
            message="url must be an http or https URL",
            retryable=False,
        )

    # 3. Validate against core_base_url allowlist — prevent open proxy
    config = load_runtime_config()
    core_base_url = config.core_base_url
    if not core_base_url:
        return error_response(
            status_code=503,
            error_kind="not_configured",
            message="Core base URL is not configured; audio proxy unavailable",
            retryable=False,
        )

    allowed_netloc = _parse_core_netloc(core_base_url)
    if parsed.netloc != allowed_netloc:
        return error_response(
            status_code=403,
            error_kind="forbidden",
            message="Target URL host is not on the allowlist",
            retryable=False,
        )

    # 4. Forward the request to Core
    headers: dict[str, str] = {}
    if "range" in request.headers:
        headers["Range"] = request.headers["range"]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        return error_response(
            status_code=502,
            error_kind="upstream_error",
            message=f"Failed to fetch audio from Core: {type(exc).__name__}",
            retryable=True,
        )

    # 5. Build response headers to forward
    forward_headers: dict[str, str] = {}
    content_type = upstream.headers.get("content-type", "audio/mpeg")
    forward_headers["Content-Type"] = content_type
    if "content-length" in upstream.headers:
        forward_headers["Content-Length"] = upstream.headers["content-length"]
    if "content-range" in upstream.headers:
        forward_headers["Content-Range"] = upstream.headers["content-range"]
    if "accept-ranges" in upstream.headers:
        forward_headers["Accept-Ranges"] = upstream.headers["accept-ranges"]

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=forward_headers,
    )

"""
XiangTa API 路由定义。

NOTE: 本模块不注册到主应用（app/main.py）。
      单独通过 include_router 在 XiangTa 独立入口挂载。
      P17-INIT 阶段：只定义路由签名，不实现业务逻辑。
"""
from fastapi import APIRouter

# TODO(P17-A1): 实现 bootstrap、suggestions、tts、letters、provider/status 路由
# 参见 docs/product/XIANGTA_API_CONTRACT.md 中的协议草案

router = APIRouter(prefix="/api/xiangta", tags=["xiangta"])


@router.get("/bootstrap")
async def bootstrap():
    """返回前端启动所需的配置快照：对象、场景、声线预设、语气预设、Provider 状态。"""
    # TODO(P17-A1): 从 configs/*.json 读取配置，从 provider_status_service 获取状态
    raise NotImplementedError


@router.post("/suggestions")
async def suggestions():
    """接收用户原始输入，调用 LLM 生成 3 条风格建议。"""
    # TODO(P17-A2): copywriting_service.generate_suggestions(recipient, scene, raw_text)
    raise NotImplementedError


@router.post("/tts")
async def tts():
    """对选定文案生成 TTS 音频，返回音频 URL 和时长。"""
    # TODO(P17-A3): tts_orchestrator.generate(text, voice_preset, tone, ...)
    raise NotImplementedError


@router.post("/letters")
async def create_letter():
    """保存信笺（MVP 阶段返回占位 ID，数据由前端 localStorage 持久化）。"""
    # TODO(P17-A4): letter_service.create(...)
    raise NotImplementedError


@router.get("/letters")
async def list_letters():
    """获取信笺列表（MVP 阶段前端用 localStorage，本路由预留）。"""
    # TODO(P17-A4): letter_service.list(...)
    raise NotImplementedError


@router.get("/provider/status")
async def provider_status():
    """实时查询底层 Provider 状态。"""
    # TODO(P17-A1): provider_status_service.get_status()
    raise NotImplementedError

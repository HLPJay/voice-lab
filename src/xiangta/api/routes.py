"""
XiangTa API 路由定义。

NOTE: 本模块不注册到主应用（app/main.py）。
      通过 include_router 在独立 XiangTa 入口或测试中挂载。

实现状态（P17-XIANGTA-A1）：
  GET  /bootstrap       ✅ 可用（读取配置，固定 not_integrated）
  GET  /provider/status ✅ 可用（固定 not_integrated）
  POST /suggestions     ⏳ 未实现（A4）
  POST /tts             ⏳ 未实现（A3）
  POST /letters         ⏳ 未实现（A4+）
  GET  /letters         ⏳ 未实现（A4+）
"""
from fastapi import APIRouter, HTTPException

from src.xiangta.api.schemas import (
    BootstrapResponse,
    ProviderStatusResponse,
)
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


@router.post("/suggestions")
async def suggestions():
    """生成文案建议（A4 实现，当前返回 501）。"""
    raise HTTPException(status_code=501, detail="not_integrated")


@router.post("/tts")
async def tts():
    """生成 TTS 语音（A3 实现，当前返回 501）。"""
    raise HTTPException(status_code=501, detail="not_integrated")


@router.post("/letters")
async def create_letter():
    """保存信笺（A4+ 实现，当前返回 501）。"""
    raise HTTPException(status_code=501, detail="not_integrated")


@router.get("/letters")
async def list_letters():
    """获取信笺列表（A4+ 实现，当前返回 501）。"""
    raise HTTPException(status_code=501, detail="not_integrated")

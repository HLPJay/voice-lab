"""XiangTa 本地 MVP runtime。

提供：
  /api/xiangta/*  — 产品 API（src.xiangta.api.routes）
  /h5/*           — H5 静态页面（apps/xiangta-h5/）
  /               — 重定向到 /h5/index.html

runtime 本身不直接调用真实 Provider，不读取真实 Provider API key。
当配置 XIANGTA_CORE_BASE_URL 环境变量时，src/xiangta 通过 HTTP 调用 Voice Lab Core 上层 API。
Core 作为独立服务运行（port 8000），XiangTa runtime 作为产品入口（port 5174）。
/tts 链路：H5 → XiangTa runtime → Core HTTP API → audioUrl → H5 audio player。
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.xiangta.api.routes import router as xiangta_router

app = FastAPI(
    title="XiangTa Runtime",
    version="0.1.0",
    description="XiangTa 本地 MVP runtime — H5 + /api/xiangta/*",
)

app.include_router(xiangta_router)

_h5_dir = Path(__file__).resolve().parents[1] / "xiangta-h5"

if _h5_dir.exists():
    app.mount(
        "/h5",
        StaticFiles(directory=str(_h5_dir), html=True),
        name="xiangta-h5",
    )


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/h5/index.html")

"""XiangTa 本地 MVP runtime。

提供：
  /api/xiangta/*  — 产品 API（src.xiangta.api.routes）
  /h5/*           — H5 静态页面（apps/xiangta-h5/）
  /               — 重定向到 /h5/index.html

不接真实 Provider / LLM / Core http client。
/tts 默认返回稳定 400 no_provider，是当前 MVP 预期行为。
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

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.database import create_db_and_tables, seed_defaults
from app.core.errors import VoiceLabError, voice_lab_error_handler
from app.utils.files import ensure_storage_dirs


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    seed_defaults()
    ensure_storage_dirs()
    yield


app = FastAPI(
    title="Voice Lab",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_exception_handler(VoiceLabError, voice_lab_error_handler)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Voice Lab"}

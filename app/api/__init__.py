from fastapi import APIRouter

from app.api import health, voice_assets, voice_jobs, voice_profiles, voice_render, voice_variants

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(voice_profiles.router, prefix="/api/voice", tags=["voice_profiles"])
api_router.include_router(voice_render.router, prefix="/api/voice", tags=["voice_render"])
api_router.include_router(voice_variants.router, prefix="/api/voice", tags=["voice_variants"])
api_router.include_router(voice_jobs.router, prefix="/api/voice", tags=["voice_jobs"])
api_router.include_router(voice_assets.router, prefix="/api/voice", tags=["voice_assets"])

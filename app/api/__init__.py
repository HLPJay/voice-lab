from fastapi import APIRouter

from app.api import async_render, health, provider_voices, voice_assets, voice_bindings, voice_clone, voice_jobs, voice_profiles, voice_render, voice_variants

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(voice_profiles.router, prefix="/api/voice", tags=["voice_profiles"])
api_router.include_router(voice_bindings.router, prefix="/api/voice", tags=["voice_bindings"])
api_router.include_router(voice_render.router, prefix="/api/voice", tags=["voice_render"])
api_router.include_router(voice_variants.router, prefix="/api/voice", tags=["voice_variants"])
api_router.include_router(voice_jobs.router, prefix="/api/voice", tags=["voice_jobs"])
api_router.include_router(voice_assets.router, prefix="/api/voice", tags=["voice_assets"])
api_router.include_router(async_render.router, prefix="/api/voice", tags=["async_render"])
api_router.include_router(voice_clone.router, prefix="/api/voice", tags=["voice_clone"])
api_router.include_router(provider_voices.router, prefix="/api/voice", tags=["provider_voices"])

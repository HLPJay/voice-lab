from fastapi import APIRouter

from app.api import admin, async_render, health, provider_voices, voice_assets, voice_bindings, voice_clone, voice_delete, voice_design, voice_jobs, voice_profiles, voice_render, voice_variants, ws_render

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
api_router.include_router(voice_design.router, prefix="/api/voice", tags=["voice_design"])
api_router.include_router(voice_delete.router, prefix="/api/voice", tags=["voice_delete"])
api_router.include_router(provider_voices.router, prefix="/api/voice", tags=["provider_voices"])
api_router.include_router(admin.router, prefix="/api/admin", tags=["admin"])
api_router.include_router(ws_render.router, prefix="/api/voice", tags=["ws_render"])

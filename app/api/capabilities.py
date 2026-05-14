from fastapi import APIRouter, HTTPException, Query

from app.core.errors import UnsupportedProvider
from app.providers.capability_registry import get_capability, list_capabilities

router = APIRouter(tags=["voice-capabilities"])


@router.get("/capabilities")
def get_capabilities(provider: str | None = Query(default=None)):
    if provider:
        try:
            cap = get_capability(provider)
            return cap.model_dump()
        except UnsupportedProvider:
            raise HTTPException(status_code=404, detail=f"Provider not found: {provider}")
    providers = [cap.model_dump() for cap in list_capabilities()]
    return {"providers": providers, "count": len(providers)}

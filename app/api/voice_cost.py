"""Cost estimation API for Voice Lab."""

from fastapi import APIRouter

from app.domain.schemas import CostEstimateRequest, CostEstimateResponse
from app.services.cost_guard_service import CostGuardService

router = APIRouter()
cost_guard = CostGuardService()


@router.post("/cost/estimate", response_model=CostEstimateResponse)
async def estimate_cost(request: CostEstimateRequest) -> CostEstimateResponse:
    """Estimate cost for a T2A operation.

    Returns billing character count and estimated cost in CNY based on
    provider pricing. Does not enforce confirm_cost — use this endpoint
    to show cost preview to users before they confirm a high-risk operation.
    """
    est = cost_guard.estimate_t2a_cost(request.provider, request.model, request.text)
    return CostEstimateResponse(
        provider=est["provider"],
        model=est["model"],
        operation=request.operation,
        billing_characters=est["billing_characters"],
        estimated_cost_cny=est["estimated_cost_cny"],
        unit_price_cny_per_10k_chars=est["unit_price_cny_per_10k_chars"],
        unknown_price=est["unknown_price"],
        warnings=est["warnings"],
    )

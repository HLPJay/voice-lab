"""Cost estimation and guard service for Voice Lab."""

from app.core.logging import get_logger

logger = get_logger("cost_guard")

# MiniMax pricing (CNY per 10,000 characters)
MINIMAX_PRICE_PER_10K = {
    "speech-2.8-turbo": 2.0,
    "speech-02.5-turbo": 2.0,
}

MINIMAX_HD_PRICE_PER_10K = 3.5

# Characters that count as 1 billing character (ASCII subset)
_SINGLE_CHAR_SET = frozenset(
    " \t\n\r0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    ".,;:!?-()[]{}'\"~@#$%^&*+=<>/\\|_`"
)


def estimate_billing_characters(text: str) -> int:
    """Estimate billing characters for a given text.

    Rules:
    - CJK (Chinese/Japanese/Korean) characters: 2 billing chars each
    - ASCII letters, digits, spaces, punctuation: 1 billing char each
    - Other Unicode characters: 2 billing chars each
    """
    total = 0
    for ch in text:
        if ch in _SINGLE_CHAR_SET:
            total += 1
        elif ord(ch) < 0x4E00:  # Not in CJK Unified Ideographs block
            total += 1
        else:
            total += 2
    return total


def _get_minimax_unit_price(model: str) -> tuple[float, bool]:
    """Return (price_per_10k_chars, is_unknown)."""
    if model in MINIMAX_PRICE_PER_10K:
        return MINIMAX_PRICE_PER_10K[model], False
    if "hd" in model.lower() or "high" in model.lower():
        return MINIMAX_HD_PRICE_PER_10K, False
    if "turbo" in model.lower():
        return 2.0, False
    return 0.0, True


def estimate_t2a_cost(provider: str, model: str, text: str) -> dict:
    """Estimate T2A cost for a given provider/model/text combination."""
    billing_chars = estimate_billing_characters(text)
    warnings: list[str] = []

    result = {
        "provider": provider,
        "model": model,
        "billing_characters": billing_chars,
        "estimated_cost_cny": None,
        "unit_price_cny_per_10k_chars": None,
        "unknown_price": True,
        "warnings": warnings,
    }

    if provider != "minimax":
        warnings.append("当前 provider 暂未配置价格估算")
        return result

    unit_price, is_unknown = _get_minimax_unit_price(model)
    result["unit_price_cny_per_10k_chars"] = unit_price

    if is_unknown:
        warnings.append(f"模型 {model} 暂未配置价格估算")
        result["estimated_cost_cny"] = None
    else:
        result["estimated_cost_cny"] = round(billing_chars / 10000 * unit_price, 6)

    result["unknown_price"] = is_unknown

    return result


class CostGuardService:
    """Service for cost estimation and high-risk operation guarding."""

    def estimate_billing_characters(self, text: str) -> int:
        return estimate_billing_characters(text)

    def estimate_t2a_cost(self, provider: str, model: str, text: str) -> dict:
        return estimate_t2a_cost(provider, model, text)

    def log_render_cost(self, provider: str, model: str, text: str) -> None:
        """Log cost estimate for a render operation without enforcing confirm."""
        if provider == "mock":
            return
        est = estimate_t2a_cost(provider, model, text)
        logger.info(
            "render_cost_estimate provider=%s model=%s billing_chars=%d estimated_cny=%.6f",
            provider, model, est["billing_characters"], est["estimated_cost_cny"] or 0,
        )

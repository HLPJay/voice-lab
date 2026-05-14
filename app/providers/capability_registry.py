from app.core.errors import UnsupportedProvider
from app.domain.capabilities import ProviderCapability
from app.providers.mock_capabilities import MOCK_CAPABILITY
from app.providers.minimax_capabilities import build_minimax_capability


def _build_registry() -> dict[str, ProviderCapability]:
    return {
        "mock": MOCK_CAPABILITY,
        "minimax": build_minimax_capability(),
    }


def list_capabilities() -> list[ProviderCapability]:
    return list(_build_registry().values())


def get_capability(provider: str) -> ProviderCapability:
    registry = _build_registry()
    cap = registry.get(provider)
    if not cap:
        raise UnsupportedProvider(f"Unsupported provider: {provider}", provider)
    return cap


def provider_exists(provider: str) -> bool:
    return provider in _build_registry()

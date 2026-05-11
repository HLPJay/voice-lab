from app.core.errors import UnsupportedProvider
from app.providers.base import SpeechProvider
from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
from app.providers.mock_speech_adapter import MockSpeechAdapter


PROVIDER_REGISTRY: dict[str, type[SpeechProvider]] = {
    "mock": MockSpeechAdapter,
    "minimax": MiniMaxSpeechAdapter,
}


def get_provider(name: str) -> SpeechProvider:
    """Look up a provider by name and return a new instance."""
    cls = PROVIDER_REGISTRY.get(name)
    if not cls:
        raise UnsupportedProvider(f"Unsupported provider: {name}", name)
    return cls()

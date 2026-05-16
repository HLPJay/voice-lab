"""Providers package.

Registers adapter types at import time so that ADAPTER_TYPE_REGISTRY
is populated before any code tries to route providers via config.
"""

from app.providers.adapter_type_registry import register_adapter_type
from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
from app.providers.mock_speech_adapter import MockSpeechAdapter

# Register known adapter types
register_adapter_type("mock", MockSpeechAdapter)
register_adapter_type("minimax", MiniMaxSpeechAdapter)

"""Providers package.

Primary registration path:
  config/adapters/*.yaml -> AdapterConfig.plugin.import_path
    -> load_adapter_plugins_from_config() -> register_adapter_type()

Legacy fallback (do not add new adapters here):
  register_adapter_type("mock", MockSpeechAdapter)
  register_adapter_type("minimax", MiniMaxSpeechAdapter)

For new adapters, add plugin.import_path to config/adapters/{adapter_type}.yaml
instead of modifying this file.
"""

from app.providers.adapter_type_registry import register_adapter_type
from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
from app.providers.mock_speech_adapter import MockSpeechAdapter

# Legacy fallback registration — new adapters should use config-driven path
register_adapter_type("mock", MockSpeechAdapter)
register_adapter_type("minimax", MiniMaxSpeechAdapter)

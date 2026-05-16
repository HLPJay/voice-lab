"""Providers package.

Primary registration path:
  config/adapters/*.yaml -> AdapterConfig.plugin.import_path
    -> load_adapter_plugins_from_config() -> register_adapter_type()

Legacy fallback (do not add new adapters here):
  get_provider() falls back to PROVIDER_REGISTRY for backward compatibility
  only when provider name is not found in config.

For new adapters, add plugin.import_path to config/adapters/{adapter_type}.yaml
instead of modifying this file.
"""

# No eager registration here.
# All adapters are registered via config/adapters/*.yaml plugin.import_path
# by calling load_adapter_plugins_from_config() at runtime.
#
# The legacy PROVIDER_REGISTRY in registry.py is kept as a backward-
# compatibility fallback for hardcoded provider names not in config, but
# mock/minimax are now config-driven only.

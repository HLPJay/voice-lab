"""Providers package.

Registration path:
  config/adapters/*.yaml -> AdapterConfig.plugin.import_path
    -> load_adapter_plugins_from_config() -> register_adapter_type()

For new adapters, add plugin.import_path to config/adapters/{adapter_type}.yaml.
No code changes needed elsewhere.
"""

# P16-ADAPTER-PLUGIN-DISCOVERY-B1-CHECK-FIX1：修复 Adapter 插件发现主路径与错误处理

## 1. 复核背景

P16-ADAPTER-PLUGIN-DISCOVERY-B1 实现后进行复核，发现两个架构问题需要修复。

**前置阶段**：
- `P16-ADAPTER-PLUGIN-DISCOVERY-B1`：Adapter 插件发现与配置化注册 ✅

## 2. 发现的问题

### 问题 1：配置发现没有真正成为主路径

**现状**：
- `adapter_type_registry.py` 在模块 import 时 eager 调用 `_ensure_core_adapters_registered()`（行 206）
- `registry.py` 的 `get_provider()` 在 config-driven route 之前调用 `_ensure_core_adapters_registered()`
- `providers/__init__.py` 在模块 import 时向 `PROVIDER_REGISTRY` 注册 mock/minimax

**影响**：
- mock/minimax 在配置发现前就被硬编码注册
- 无法证明插件发现配置化是主路径
- 后续新 adapter 扩展仍可能绕过配置发现

**处理方案**：
1. 移除 `adapter_type_registry.py` 模块 import 时的 eager `_ensure_core_adapters_registered()` 调用
2. 移除 `registry.py` 的 `get_provider()` 中对 `_ensure_core_adapters_registered()` 的提前调用
3. 移除 `providers/__init__.py` 中的 eager 注册（mock/minimax 现在完全由 config 驱动）
4. `_ensure_core_adapters_registered()` 保留为 legacy fallback，只在 `get_adapter_type_adapter()` 最后一步使用

**修改后的 Resolution chain**：
```
get_adapter_type_adapter(adapter_type)
  1. ADAPTER_TYPE_REGISTRY 已有 → 直接返回
  2. load_adapter_plugins_from_config() → 从 config/adapters/*.yaml 动态 import
  3. 成功则返回
  4. _ensure_core_adapters_registered() (legacy fallback)
  5. 成功则返回
  6. 抛 UnsupportedProvider
```

### 问题 2：plugin.import_path 加载错误被静默吞掉

**现状**：
```python
# adapter_type_registry.py
try:
    register_adapter_type_from_import_path(...)
except (ValueError, ImportError, AttributeError, TypeError):
    pass  # 静默吞掉！
```

**影响**：
- 未来 `xiaomi_mimo_chat_tts.yaml` 写错 `plugin.import_path` 时，会变成难排查的 `UnsupportedProvider`
- 配置声明了 plugin 但加载失败时，用户完全不知道原因

**处理方案**：
1. 新增 `AdapterPluginLoadError` 异常类，包含 `adapter_type`、`import_path`、`cause`
2. `load_adapter_plugins_from_config(strict=True)` 默认 strict=True，遇到错误默认抛 `AdapterPluginLoadError`
3. `strict=False` 允许静默跳过（仅用于向后兼容测试）
4. 错误信息包含 adapter_type 和 import_path，便于排查

```python
class AdapterPluginLoadError(Exception):
    def __init__(self, adapter_type: str, import_path: str, cause: Exception):
        self.adapter_type = adapter_type
        self.import_path = import_path
        self.cause = cause
        super().__init__(
            f"Failed to load adapter plugin for '{adapter_type}' "
            f"from import_path '{import_path}': {type(cause).__name__}: {cause}"
        )
```

## 3. 实际修改文件

| 文件 | 改动 |
|---|---|
| `app/providers/adapter_type_registry.py` | 移除 eager `_ensure_core_adapters_registered()` 调用；新增 `AdapterPluginLoadError`；`load_adapter_plugins_from_config(strict=True)`；`clear_adapter_type_registry_for_tests()` 增加清理 `PROVIDER_REGISTRY` |
| `app/providers/registry.py` | 移除 `get_provider()` 中对 `_ensure_core_adapters_registered()` 的调用；移除相关 import |
| `app/providers/__init__.py` | 移除 eager `register_adapter_type()` 调用，改为注释说明 |
| `tests/test_provider_config_dynamic.py` | `TestAdapterTypeRegistry` 增加 `setup_method` 调用 `load_adapter_plugins_from_config()` |
| `tests/test_adapter_plugin_discovery.py` | 新增 `TestNoEagerRegistration`、`TestPluginLoadErrorNotSwallowed`、`TestProviderRoutingRegression` 测试类 |

## 4. 测试结果

| 测试套件 | 结果 |
|---|---|
| test_adapter_plugin_discovery.py | 44 passed ✅ |
| test_adapter_config_loader.py | 51 passed ✅ |
| test_provider_config_dynamic.py | 47 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |
| **总计** | **225 passed** |

## 5. 剩余风险

无阻塞风险。

**非阻塞观察项**：
- `providers/__init__.py` 完全移除了 eager 注册，mock/minimax 完全依赖 config 驱动。如果 config 加载失败且没有 legacy fallback，系统将无法启动（符合预期——强制配置正确性）

## 6. 下一阶段建议

### 推荐：P16-XIAOMI-MIMO-TTS-B1

**目标**：基于 Adapter Plugin Discovery 机制，实现小米 MiMo Chat TTS 最小可行路径。

**注意**：小米 MiMo adapter 现在可以通过创建 `config/adapters/xiaomi_mimo_chat_tts.yaml` 并配置 `plugin.import_path` 来注册，无需修改任何 Python 源码。

**Xiaomi adapter 注册方式**：
```yaml
# config/adapters/xiaomi_mimo_chat_tts.yaml
adapter_type: "xiaomi_mimo_chat_tts"
plugin:
  import_path: "app.providers.xiaomi_mimo_chat_tts_adapter.XiaomiMiMoChatTTSAdapter"
tts:
  supported: true
  models: ["mimo-v2.5-tts"]
  ...
```

## 7. 明确未做

- 未实现 Xiaomi MiMo adapter
- 未提交 Xiaomi adapter WIP 文件
- 未新增 `config/adapters/xiaomi_mimo_chat_tts.yaml`
- 未修改 `config/providers.yaml` 新增 xiaomi_mimo
- 未接 OpenAI
- 未调用真实外部 API
- 未改 RenderPlan / VoiceBinding / ProviderVoice / VoiceProfile schema

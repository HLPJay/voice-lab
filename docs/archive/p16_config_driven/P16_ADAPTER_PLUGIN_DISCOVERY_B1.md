# P16-ADAPTER-PLUGIN-DISCOVERY-B1：Adapter 插件发现与配置化注册

## 1. 阶段背景

### 1.1 已完成的基础设施

- `ProviderConfig`：provider 实例配置（enabled、real_cost、api_key_env、adapter_type）
- `AdapterConfig`：adapter 默认能力（models、audio_formats、supports_xxx、metadata）
- `config/adapters/*.yaml`：AdapterConfig YAML 声明

### 1.2 发现的问题

**问题**：每新增一个 adapter 都要修改 `app/providers/__init__.py` 或 `app/providers/adapter_type_registry.py` 做硬编码注册：

```python
# app/providers/__init__.py
register_adapter_type("xiaomi_mimo_chat_tts", XiaomiMiMoChatTTSAdapter)  # 每新增一个都要改
```

**影响**：
- 与"插件化 + 配置化 Provider"目标不一致
- 后续 Xiaomi MiMo / OpenAI 等 adapter 接入会不断污染注册表源码
- Xiaomi MiMo B1 已经开始，发现这个架构问题

**处理**：AdapterConfig 增加 `plugin.import_path`，adapter_type_registry 从配置动态 import 并注册。

## 2. 实现内容

### 2.1 新增 AdapterPluginConfig

文件：`app/domain/adapter_config.py`

```python
class AdapterPluginConfig(BaseModel):
    """Plugin configuration for dynamically loading an adapter class."""

    import_path: str = Field(
        ...,
        description="Python import path to the adapter class",
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_import_path(self) -> AdapterPluginConfig:
        """Validate import_path is non-empty and starts with app.providers."""
        if not self.import_path or not self.import_path.strip():
            raise ValueError("plugin.import_path must not be empty")
        if not self.import_path.startswith("app.providers."):
            raise ValueError("plugin.import_path must start with 'app.providers.'")
        # Must be in format module.path.ClassName where ClassName starts with uppercase
        parts = self.import_path.rsplit(".", 1)
        if len(parts) != 2 or not parts[1]:
            raise ValueError(
                "plugin.import_path must be in the format 'module.path.ClassName'"
            )
        class_name = parts[1]
        if not class_name[0].isupper():
            raise ValueError(
                "plugin.import_path class name must start with an uppercase letter "
                f"(e.g. 'MockSpeechAdapter'), got: {class_name}"
            )
        return self
```

**校验规则**：
- `import_path` 必须非空
- `import_path` 必须以 `app.providers.` 开头
- `import_path` 必须包含模块路径和类名
- 类名必须以大写字母开头（符合 Python 类名约定）

### 2.2 AdapterConfig 新增 plugin 字段

```python
class AdapterConfig(BaseModel):
    adapter_type: str
    plugin: AdapterPluginConfig | None = Field(default=None)
    # ... existing fields
```

**兼容策略**：
- `plugin` 可以暂时为 `None`，以便旧配置 fallback
- `mock.yaml` 和 `minimax.yaml` 已显式补充 `plugin.import_path`

### 2.3 mock.yaml plugin.import_path

```yaml
adapter_type: "mock"

plugin:
  import_path: "app.providers.mock_speech_adapter.MockSpeechAdapter"

default_model: "mock-tts"
# ... existing fields
```

### 2.4 minimax.yaml plugin.import_path

```yaml
adapter_type: "minimax"

plugin:
  import_path: "app.providers.minimax_speech_adapter.MiniMaxSpeechAdapter"

default_base_url: "https://api.minimaxi.com"
# ... existing fields
```

### 2.5 adapter_type_registry 动态注册逻辑

文件：`app/providers/adapter_type_registry.py`

**核心机制**：

1. `register_adapter_type_from_import_path(adapter_type, import_path)`：
   - 验证 `import_path` 以 `app.providers.` 开头
   - 使用 `importlib.import_module` 动态导入模块
   - 验证类存在且是 `SpeechProvider` 子类
   - 注册到 `ADAPTER_TYPE_REGISTRY`

2. `load_adapter_plugins_from_config()`：
   - 调用 `list_adapter_configs()` 获取所有 adapter 配置
   - 对每个有 `plugin.import_path` 的配置，调用 `register_adapter_type_from_import_path()`
   - 跳过加载失败的配置（可能尚未完成迁移）

3. `get_adapter_type_adapter(adapter_type)` 修改行为：
   - 快速路径：已注册直接返回
   - 配置路径：尝试 `load_adapter_plugins_from_config()` 后返回
   - Fallback：` _ensure_core_adapters_registered()` 兜底
   - 仍没有则抛 `UnsupportedProvider`

4. `clear_adapter_type_registry_for_tests()`：
   - 清空 `ADAPTER_TYPE_REGISTRY`
   - 重置 `_plugins_loaded` 标志
   - 用于测试场景

### 2.6 Fallback 策略

**不要一次性删除现有 hardcoded fallback**。保留作为兼容兜底。

- `__init__.py` 中的 `register_adapter_type("mock", ...)` 和 `register_adapter_type("minimax", ...)` 降级为 legacy fallback
- 新增 adapter **不应再修改** `__init__.py` 做硬编码注册
- `get_adapter_type_adapter` 会先尝试从配置加载，加载不到才走 fallback

```
主路径：config/adapters/*.yaml -> plugin.import_path -> 动态 import -> 注册
Fallback：_ensure_core_adapters_registered() -> 硬编码 mock/minimax 注册
```

## 3. 验证结果

### 3.1 测试结果

| 测试套件 | 结果 |
|---|---|
| test_adapter_plugin_discovery.py | 37 passed ✅ |
| test_adapter_config_loader.py | 51 passed ✅ |
| test_provider_config_dynamic.py | 40 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |
| **总计** | **211 passed** |

### 3.2 功能验证

| 检查项 | 结果 |
|---|---|
| `mock.yaml` 可解析 `plugin.import_path` | ✅ |
| `minimax.yaml` 可解析 `plugin.import_path` | ✅ |
| `plugin.import_path` 为空时报错 | ✅ |
| `plugin.import_path` 非 `app.providers.` 前缀时报错 | ✅ |
| `plugin.import_path` 类名非大写开头时报错 | ✅ |
| `plugin` 多余字段时报错 | ✅ |
| 从 mock.yaml 动态注册 mock | ✅ |
| 从 minimax.yaml 动态注册 minimax | ✅ |
| `get_adapter_type_adapter("mock")` 返回 MockSpeechAdapter | ✅ |
| `get_adapter_type_adapter("minimax")` 返回 MiniMaxSpeechAdapter | ✅ |
| `get_provider("mock")` 返回 MockSpeechAdapter 实例 | ✅ |
| `get_provider("minimax")` 返回 MiniMaxSpeechAdapter 实例 | ✅ |
| `get_provider("mock_configured")` 返回 MockSpeechAdapter 实例 | ✅ |
| `get_provider("disabled_provider")` 抛 UnsupportedProvider | ✅ |
| `/api/voice/capabilities` 包含 mock | ✅ |
| `/api/voice/capabilities` 包含 minimax | ✅ |
| `/api/voice/capabilities` 包含 mock_configured | ✅ |
| `/api/voice/capabilities` 不包含 disabled_provider | ✅ |
| metadata `adapter_type` / `real_cost` / `configured_via_yaml` 不回归 | ✅ |
| import_path 指向不存在模块，抛清晰 ImportError | ✅ |
| import_path 指向不存在 class，抛清晰 AttributeError | ✅ |
| import_path 指向非 SpeechProvider class，抛清晰 TypeError | ✅ |
| import_path 指向非 app.providers. 前缀，抛清晰 ValueError | ✅ |
| 动态 import 不调用外部 API | ✅ |

## 4. 风险与处理

| 风险 | 级别 | 处理 |
|---|---|---|
| 动态 import 有安全风险 | 🟡 中 | 限制 `import_path` 必须以 `app.providers.` 开头 |
| `import_path` 错误需要清晰报错 | ✅ | ValueError / ImportError / AttributeError / TypeError 分层处理 |
| class 必须是 SpeechProvider 子类 | ✅ | 验证 `issubclass(cls, SpeechProvider)` |
| 不调用外部 API | ✅ | 纯 Python import，无网络调用 |
| 不提交密钥 | ✅ | 无敏感信息变更 |

## 5. 下一阶段建议

### 推荐：P16-XIAOMI-MIMO-TTS-B1

**目标**：基于 Adapter Plugin Discovery 机制，继续小米 MiMo Chat TTS 最小实现。

**届时新增 Xiaomi MiMo adapter 不再修改** `__init__.py` **或** `adapter_type_registry.py`，只需：

1. 创建 `app/providers/xiaomi_mimo_chat_tts_adapter.py`
2. 创建 `config/adapters/xiaomi_mimo_chat_tts.yaml`（含 `plugin.import_path`）
3. 在 `config/providers.yaml` 新增 disabled 的 xiaomi_mimo provider
4. 创建 mock transport 单元测试

### 备选

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-XIAOMI-MIMO-TTS-B1-CHECK | verify Xiaomi MiMo Chat TTS implementation | B1 完成 |
| P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 | analyze MiMo voicedesign semantic mapping | B1-CHECK 后评估 |
| P16-XIAOMI-MIMO-TTS-VOICE-CLONE-A0 | analyze MiMo voiceclone semantic mapping | B1-CHECK 后评估 |
| P16-OPENAI-COMPATIBLE-TTS-A0 | design OpenAI-compatible TTS adapter | 可后置 |
| P16-DYNAMIC-PROVIDER-CONFIG-B2 | provider capability override enhancements | 可后置 |

## 6. 明确未做

- 未实现 Xiaomi MiMo adapter
- 未实现 OpenAI adapter
- 未调用真实 MiniMax / 小米 / OpenAI / 任何外部 API
- 未改 RenderPlan / VoiceBinding / ProviderVoice / VoiceProfile schema
- 未改 resolve_binding
- 未删除现有 mock/minimax adapter
- 未删除现有 Python capability builder
- 未做 UI 改造

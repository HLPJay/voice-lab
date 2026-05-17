# P16-ADAPTER-PLUGIN-CONFIG-B1：实现 AdapterConfig 与 Adapter 插件配置加载

## 1. 阶段背景

P16-ADAPTER-PLUGIN-CONFIG-A0 设计已完成，本阶段实现 AdapterConfig schema、adapter_config_loader、config/adapters/*.yaml 配置加载，以及 capability_registry 的 ProviderConfig + AdapterConfig 合成。

前置阶段：
- `P16-ADAPTER-PLUGIN-CONFIG-A0`：Adapter 插件化与配置分层设计 ✅
- `P16-DYNAMIC-PROVIDER-CONFIG-B1-CLOSE`：Provider 配置化接入阶段收口 ✅

## 2. 已完成内容

### 2.1 新增文件

| 文件 | 用途 |
|---|---|
| `app/domain/adapter_config.py` | AdapterConfig Pydantic schema（EndpointConfig, TTSCapabilityConfig, BatchCapabilityConfig, ScriptCapabilityConfig, VoiceCloneCapabilityConfig, VoiceDesignCapabilityConfig, ProviderVoicesCapabilityConfig） |
| `app/config/adapter_config_loader.py` | YAML 配置加载器（list_adapter_configs, get_adapter_config, clear_adapter_config_cache） |
| `config/adapters/mock.yaml` | Mock adapter 默认配置 |
| `config/adapters/minimax.yaml` | MiniMax adapter 默认配置 |
| `tests/test_adapter_config_loader.py` | 30 项测试覆盖 |

### 2.2 修改文件

| 文件 | 改动 |
|---|---|
| `app/providers/capability_registry.py` | 支持 ProviderConfig + AdapterConfig 合成，构建最终 ProviderCapability |

### 2.3 AdapterConfig Schema

```python
class AdapterConfig(BaseModel):
    adapter_type: str  # 唯一标识，对应 providers.yaml 中的 adapter_type
    default_base_url: str | None
    default_timeout_seconds: int = 120
    endpoints: EndpointConfig
    default_model: str | None
    tts: TTSCapabilityConfig | None
    batch: BatchCapabilityConfig | None
    script: ScriptCapabilityConfig | None
    voice_clone: VoiceCloneCapabilityConfig | None
    voice_design: VoiceDesignCapabilityConfig | None
    provider_voices: ProviderVoicesCapabilityConfig | None
    metadata: dict[str, Any]
```

### 2.4 配置合并优先级

```
ProviderConfig（最高优先级）
  → AdapterConfig（来自 config/adapters/*.yaml）
    → Python builder fallback（最低优先级）
```

## 3. 合并逻辑说明

### 3.1 TTS Capability 合并

1. ProviderConfig.tts.enabled 控制是否启用
2. 如果启用，models/audio_formats/max_text_chars 等优先从 AdapterConfig 获取
3. ProviderConfig.default_model 覆盖 AdapterConfig.default_model
4. speed/vol/pitch 等复杂参数仍从 Python builder 获取

### 3.2 Batch/Script Capability 合并

1. ProviderConfig.batch/script.enabled 控制是否启用
2. max_text_chars/max_segments 从 AdapterConfig 获取
3. segment_strategies 等从 Python builder 获取

### 3.3 Metadata 合并

1. 从 Python builder 的 metadata 开始
2. 添加/覆盖 AdapterConfig.metadata 的值
3. 添加 `adapter_type`, `real_cost`, `configured_via_yaml` 等字段

## 4. 验证结果

### 4.1 测试结果

| 测试套件 | 结果 |
|---|---|
| test_adapter_config_loader.py | 30 passed ✅ |
| test_provider_config_dynamic.py | 40 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |

### 4.2 功能验证

| 检查项 | 结果 |
|---|---|
| `get_adapter_config("mock")` 返回 mock 配置 | ✅ |
| `get_adapter_config("minimax")` 返回 minimax 配置 | ✅ |
| `get_adapter_config("nonexistent")` 返回 None | ✅ |
| `list_adapter_configs()` 包含 mock 和 minimax | ✅ |
| `get_capability("mock")` 使用 AdapterConfig 构建 TTS | ✅ |
| `get_capability("minimax")` TTS models 来自 AdapterConfig | ✅ |
| `mock_configured` 通过 mock adapter_type 获取 capability | ✅ |
| `disabled_provider` 不出现在 capability list 中 | ✅ |

## 5. 发现的问题及处理

### 5.1 发现：VoiceClone/VoiceDesign/ProviderVoices Capability 暂不合并

**现状**：这些 capability 的合并逻辑较为复杂，涉及 VoiceIdConstraint 等嵌套 schema。当前阶段这些 capability 仍直接从 Python builder 获取。

**处理**：保持从 builder 获取，暂不在 AdapterConfig 中定义这些字段的合并逻辑。

**后续**：在 B2 阶段或 OpenAI-compatible TTS 接入时，基于真实需求再实现合并。

### 5.2 发现：TTS/Batch/Script 合并逻辑较复杂

**现状**：Capability 合并涉及多个字段和优先级判断，代码较长。

**处理**：已在代码中添加详细注释说明合并规则。

**后续**：如后续发现合并逻辑有问题，可以简化——当前设计是保守的，优先保证不改变已有行为。

## 6. 剩余风险

无阻塞风险。

**非阻塞观察项**：
- VoiceClone/VoiceDesign/ProviderVoices 暂不合并，依赖 Python builder
- speed/vol/pitch 等 NumericRange 参数仍从 builder 获取，未实现 AdapterConfig 配置
- AdapterConfig 的 extra="forbid"，如果 schema 需要扩展字段需要同步修改

## 7. 未进入范围

| 内容 | 原因 |
|---|---|
| VoiceClone/VoiceDesign/ProviderVoices 合并 | 复杂 schema，需要多 Provider 验证 |
| speed/vol/pitch range 配置化 | 不同 provider 差异大，需多 Provider 接入后分析 |
| OpenAI adapter | 另一阶段 A0 设计 |
| 运行时配置热更新 | 当前阶段不需要 |
| Provider 管理 UI | 当前阶段不需要 |

## 8. 收口结论

AdapterConfig 与 Adapter 插件配置加载 B1 阶段完成 ✅

- `AdapterConfig` schema 实现（EndpointConfig, TTSCapabilityConfig, BatchCapabilityConfig 等）
- `adapter_config_loader` 实现（list_adapter_configs, get_adapter_config, clear_adapter_config_cache）
- `config/adapters/mock.yaml` 和 `config/adapters/minimax.yaml` 创建
- `capability_registry` 支持 ProviderConfig + AdapterConfig 合成
- 全部测试通过（30 + 40 + 43 + 40 = 153 passed）
- 向后兼容现有 Python builder 逻辑

**下一阶段**：`P16-DYNAMIC-PROVIDER-CONFIG-B2` 或 `P16-OPENAI-COMPATIBLE-TTS-A0`（待评估）

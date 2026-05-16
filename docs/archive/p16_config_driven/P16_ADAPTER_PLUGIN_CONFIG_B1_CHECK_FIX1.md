# P16-ADAPTER-PLUGIN-CONFIG-B1-CHECK-FIX1：修复 AdapterConfig 与 capability 合成边界

## 1. 阶段背景

P16-ADAPTER-PLUGIN-CONFIG-B1 实现后，复核发现 3 个边界问题需要修复。

**前置阶段**：
- `P16-ADAPTER-PLUGIN-CONFIG-B1`：实现 AdapterConfig 与 Adapter 插件配置加载 ✅

## 2. 发现的问题

### 问题 1：AdapterConfig.metadata 缺少敏感字段校验

**影响**：
adapter metadata 可能误放 api key/token/secret 等敏感信息。如果用户配置 `metadata: {api_key: "xxx"}`，系统不会拒绝，导致敏感信息泄露风险。

**发现位置**：
`app/domain/adapter_config.py` 中 `metadata: dict[str, Any] = Field(default_factory=dict)` 没有 validator。

**处理方案**：
参照 `app/domain/provider_config.py` 和 `app/domain/capabilities.py` 的敏感字段校验逻辑，为 `AdapterConfig` 新增 `@model_validator`：

```python
SENSITIVE_METADATA_KEYS = frozenset({
    "api_key", "apikey", "secret", "token", "password",
    "minimax_api_key", "openai_api_key",
})

@model_validator(mode="after")
def validate_no_secret_metadata(self) -> AdapterConfig:
    for key, value in self.metadata.items():
        lower_key = str(key).lower()
        if lower_key in SENSITIVE_METADATA_KEYS:
            raise ValueError(f"AdapterConfig.metadata must not contain sensitive key: {key}")
        if isinstance(value, str) and "sk-" in value:
            raise ValueError(f"AdapterConfig.metadata value must not contain secret patterns: {key}")
    return self
```

**新增测试**：
- `test_metadata_rejects_api_key` - api_key 被拒绝
- `test_metadata_rejects_token` - token 被拒绝
- `test_metadata_rejects_secret` - secret 被拒绝
- `test_metadata_rejects_password` - password 被拒绝
- `test_metadata_rejects_sk_pattern` - sk- pattern 被拒绝
- `test_metadata_accepts_safe_values` - 安全值通过
- `test_metadata_case_insensitive_key_check` - 大小写不敏感检查

---

### 问题 2：AdapterConfig capability config 缺少 supported 字段

**影响**：
`TTSCapabilityConfig`、`BatchCapabilityConfig`、`ScriptCapabilityConfig`、`VoiceCloneCapabilityConfig`、`VoiceDesignCapabilityConfig`、`ProviderVoicesCapabilityConfig` 没有 `supported` 字段。AdapterConfig 无法明确表达"某个 adapter 默认不支持某能力"。

**发现位置**：
`app/domain/adapter_config.py` 中各 CapabilityConfig 类。

**处理方案**：
为各 CapabilityConfig 增加 `supported: bool` 字段：

| CapabilityConfig | 默认值 |
|---|---|
| `TTSCapabilityConfig.supported` | `True` |
| `BatchCapabilityConfig.supported` | `True` |
| `ScriptCapabilityConfig.supported` | `True` |
| `VoiceCloneCapabilityConfig.supported` | `False` |
| `VoiceDesignCapabilityConfig.supported` | `False` |
| `ProviderVoicesCapabilityConfig.supported` | `True` |

同步更新 `config/adapters/mock.yaml` 和 `config/adapters/minimax.yaml`，在所有 capability 配置块中显式添加 `supported` 字段，避免默认值歧义。

**新增测试**：
- `test_mock_adapter_tts_supported_true`
- `test_minimax_adapter_tts_supported_true`
- `test_mock_adapter_batch_supported_true`
- `test_mock_adapter_script_supported_true`
- `test_mock_adapter_voice_clone_supported_true`
- `test_mock_adapter_voice_design_supported_true`
- `test_mock_adapter_provider_voices_supported_true`

---

### 问题 3：capability_registry 需要尊重 ProviderConfig enabled=false 的 provider-level override

**影响**：
当 `ProviderConfig.tts.enabled=false` 时，如果 `AdapterConfig.tts` 存在 capability 配置，当前代码可能通过 adapter_config 分支把 TTS 重新构造成 `supported=true`。这导致 provider 实例级禁用能力不可靠。

**发现位置**：
`app/providers/capability_registry.py` 中 `_build_capability_from_config()` 函数的 TTS/Batch/Script 合成逻辑。

**处理方案**：
重构 capability 合成逻辑，明确 ProviderConfig.enabled=false 优先：

```python
# Build TTS capability with merge rules
# Priority: ProviderConfig.enabled (highest) > AdapterConfig > builder fallback

# Check if provider explicitly disables TTS
provider_tts_disabled = config.tts and not config.tts.enabled

if provider_tts_disabled:
    # Provider-level TTS disabled - must respect, do not re-enable via AdapterConfig
    tts_cap = TTSCapability(supported=False)
elif config.tts and config.tts.enabled:
    # Provider-level TTS enabled - merge with builder/AdapterConfig
    ...
elif adapter_config and adapter_config.tts and adapter_config.tts.supported:
    # Adapter has TTS config and says supported - use AdapterConfig
    ...
else:
    # Use builder's TTS
    tts_cap = tts_builder
```

对 TTS、Batch、Script、VoiceClone、VoiceDesign、ProviderVoices 都应用相同逻辑。

**新增测试**：
- `test_provider_tts_disabled_stays_disabled`
- `test_provider_batch_disabled_stays_disabled`
- `test_provider_script_disabled_stays_disabled`
- `test_provider_voice_clone_disabled_stays_disabled`
- `test_provider_voice_design_disabled_stays_disabled`
- `test_provider_provider_voices_disabled_stays_disabled`

## 3. 实际修改文件

| 文件 | 改动 |
|---|---|
| `app/domain/adapter_config.py` | 新增 sensitive metadata validator；新增各 CapabilityConfig 的 supported 字段 |
| `app/providers/capability_registry.py` | 重构 TTS/Batch/Script/VoiceClone/VoiceDesign/ProviderVoices 合成逻辑，ProviderConfig enabled=false 优先 |
| `config/adapters/mock.yaml` | 补充所有 capability 的 supported 字段 |
| `config/adapters/minimax.yaml` | 补充所有 capability 的 supported 字段 |
| `tests/test_adapter_config_loader.py` | 新增 3 个测试类：TestAdapterConfigMetadataSecurity、TestAdapterConfigSupportedField、TestProviderConfigEnabledOverride |

## 4. 测试结果

| 测试套件 | 结果 |
|---|---|
| test_adapter_config_loader.py | 51 passed ✅ |
| test_provider_config_dynamic.py | 40 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |
| **总计** | **174 passed** |

## 5. 剩余风险

无阻塞风险。

**非阻塞观察项**：
- VoiceClone/VoiceDesign/ProviderVoices 的合并逻辑仍较简单，主要依赖 builder
- AdapterConfig 的 supported 字段默认值可能需要在真实多 Provider 接入后调整

## 6. 下一阶段建议

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-ADAPTER-PLUGIN-CONFIG-B1-CLOSE | close adapter plugin config B1 | 本阶段完成 |
| P16-OPENAI-COMPATIBLE-TTS-A0 | design OpenAI-compatible TTS adapter | B1-CLOSE 后评估 |
| P16-DYNAMIC-PROVIDER-CONFIG-B2 | provider capability override enhancements | B1-CLOSE 后评估 |

**明确未做**：
- 未接入 OpenAI
- 未接入小米 MiMo
- 未调用真实外部 API
- 未改 RenderPlan / VoiceBinding / ProviderVoice / VoiceProfile schema
- 未改 resolve_binding
- 未删 Python capability builder

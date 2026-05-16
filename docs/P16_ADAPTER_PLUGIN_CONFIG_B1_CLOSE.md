# P16-ADAPTER-PLUGIN-CONFIG-B1-CLOSE：AdapterConfig 与插件配置加载阶段收口

## 1. 阶段背景

### 1.1 B1 实现内容

P16-ADAPTER-PLUGIN-CONFIG-B1 已实现：

- `AdapterConfig` schema（`app/domain/adapter_config.py`）
- `adapter_config_loader`（`app/config/adapter_config_loader.py`）
- `config/adapters/mock.yaml` 和 `config/adapters/minimax.yaml`
- `capability_registry` 支持 ProviderConfig + AdapterConfig 初步合成

### 1.2 B1-CHECK-FIX1 修复内容

P16-ADAPTER-PLUGIN-CONFIG-B1-CHECK-FIX1 修复了 3 个边界问题：

- AdapterConfig.metadata 敏感字段校验缺失 → 已修复
- AdapterConfig capability config 缺少 supported 字段 → 已修复
- ProviderConfig enabled=false 可能被 AdapterConfig 重新打开 → 已修复

## 2. 已完成内容

### 2.1 新增文件

| 文件 | 用途 |
|---|---|
| `app/domain/adapter_config.py` | AdapterConfig Pydantic schema（含 EndpointConfig、TTSCapabilityConfig、BatchCapabilityConfig、ScriptCapabilityConfig、VoiceCloneCapabilityConfig、VoiceDesignCapabilityConfig、ProviderVoicesCapabilityConfig） |
| `app/config/adapter_config_loader.py` | YAML 配置加载器（list_adapter_configs、get_adapter_config、clear_adapter_config_cache） |
| `config/adapters/mock.yaml` | Mock adapter 默认配置（含 supported 字段） |
| `config/adapters/minimax.yaml` | MiniMax adapter 默认配置（含 supported 字段） |
| `tests/test_adapter_config_loader.py` | 51 项测试覆盖 |
| `docs/P16_ADAPTER_PLUGIN_CONFIG_B1.md` | B1 实现文档 |
| `docs/P16_ADAPTER_PLUGIN_CONFIG_B1_CHECK_FIX1.md` | B1-CHECK-FIX1 修复文档 |

### 2.2 修改文件

| 文件 | 改动 |
|---|---|
| `app/providers/capability_registry.py` | 支持 ProviderConfig + AdapterConfig 合成，ProviderConfig enabled=false 最高优先级 |

### 2.3 AdapterConfig Schema 特性

- `adapter_type`：唯一标识，对应 providers.yaml 中的 adapter_type
- `default_base_url` / `default_timeout_seconds` / `endpoints`：API 默认配置
- `default_model`：默认模型
- `tts` / `batch` / `script` / `voice_clone` / `voice_design` / `provider_voices`：各能力配置（含 supported 字段）
- `metadata`：非敏感配置元信息（含敏感字段校验 validator）

### 2.4 配置合并优先级

```
ProviderConfig.enabled=false（最高优先级）
  → ProviderConfig.enabled=true + AdapterConfig.supported
    → Python builder fallback（最低优先级）
```

## 3. 问题与处理方案

### 问题 1：AdapterConfig.metadata 缺少敏感字段校验

**影响**：adapter metadata 可能误放 api key/token/secret。

**处理**：
- 新增 `SENSITIVE_METADATA_KEYS` frozenset
- 新增 `@model_validator` 校验 key 和 value
- 拒绝 api_key/apikey/secret/token/password/minimax_api_key/openai_api_key
- 拒绝 value 包含 "sk-"

**状态**：已修复 ✅

---

### 问题 2：AdapterConfig capability config 缺少 supported 字段

**影响**：AdapterConfig 无法明确表达"某个 adapter 默认不支持某能力"。

**处理**：
- 为 TTSCapabilityConfig/BatchCapabilityConfig/ScriptCapabilityConfig 新增 `supported: bool = True`
- 为 VoiceCloneCapabilityConfig/VoiceDesignCapabilityConfig 新增 `supported: bool = False`
- 为 ProviderVoicesCapabilityConfig 新增 `supported: bool = True`
- 同步更新 mock.yaml 和 minimax.yaml，显式添加 supported 字段

**状态**：已修复 ✅

---

### 问题 3：ProviderConfig enabled=false 可能被 AdapterConfig 重新打开

**影响**：当 ProviderConfig.tts.enabled=false 时，如果 AdapterConfig.tts 有配置，能力可能被重新构造成 supported=true。

**处理**：
- 重构 capability 合成逻辑，明确 ProviderConfig enabled=false 最高优先级
- 对 TTS、Batch、Script、VoiceClone、VoiceDesign、ProviderVoices 都应用相同逻辑
- Provider-level disabled 不会被 AdapterConfig override

**状态**：已修复 ✅

## 4. 验证结果

### 4.1 测试结果

| 测试套件 | 结果 |
|---|---|
| test_adapter_config_loader.py | 51 passed ✅ |
| test_provider_config_dynamic.py | 40 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |
| **总计** | **174 passed** |

### 4.2 功能验证

| 检查项 | 结果 |
|---|---|
| `get_adapter_config("mock")` 返回 mock 配置 | ✅ |
| `get_adapter_config("minimax")` 返回 minimax 配置 | ✅ |
| `list_adapter_configs()` 包含 mock 和 minimax | ✅ |
| `get_capability("mock")` 使用 AdapterConfig 构建 TTS | ✅ |
| `get_capability("minimax")` TTS models 来自 AdapterConfig | ✅ |
| `mock_configured` 通过 mock adapter_type 获取 capability | ✅ |
| `disabled_provider` 不出现在 capability list 中 | ✅ |
| metadata 敏感字段被拒绝 | ✅ |
| ProviderConfig tts.enabled=false 时 capability.tts.supported=false | ✅ |

## 5. 剩余风险 / 非阻塞观察项

| 观察项 | 说明 | 后续处理 |
|---|---|---|
| VoiceClone/VoiceDesign/ProviderVoices 合成逻辑较简单 | 当前主要依赖 Python builder，未实现 AdapterConfig 合并 | B2 阶段或小米 MiMo/OpenAI 接入时处理 |
| AdapterConfig.supported 默认值需继续校准 | 当前默认值基于 minimax/mock 设计，多 Provider 接入后可能需调整 | 小米 MiMo 接入时验证 |
| ProviderConfig.enabled 默认 true，与 AdapterConfig.supported=false 组合语义待验证 | 需要在真实多 Provider 场景下验证优先级 | 小米 MiMo 接入时验证 |
| adapter constructor 未接收 ProviderRuntimeConfig | 当前 adapter 仍使用 get_settings()，无法在同一 adapter class 上实例化不同配置 | B2 阶段评估 |
| 未实现运行时热更新 | config 变更需重启服务 | 当前阶段不需要 |
| 未做 Provider 管理 UI | 当前阶段不需要 | 后期待定 |

## 6. 未进入范围

| 内容 | 原因 |
|---|---|
| OpenAI adapter | B1-CLOSE 后进入 P16-OPENAI-COMPATIBLE-TTS-A0 |
| 小米 MiMo adapter | B1-CLOSE 后进入 P16-XIAOMI-MIMO-TTS-A0 |
| VoiceClone/VoiceDesign/ProviderVoices AdapterConfig 合并 | 需要多 Provider 真实数据验证 |
| speed/vol/pitch range 配置化 | 不同 provider 差异大，需多 Provider 接入后分析 |
| adapter constructor 接收 ProviderRuntimeConfig | B2 阶段评估 |
| 运行时配置热更新 | 当前阶段不需要 |
| Provider 管理 UI | 当前阶段不需要 |

## 7. 明确未做

- 未接 OpenAI
- 未接小米 MiMo
- 未新增 xiaomi_mimo_tts adapter
- 未新增 openai adapter
- 未调用真实 MiniMax / OpenAI / 小米 / 任何外部 API
- 未改 RenderPlan
- 未改 VoiceBinding / ProviderVoice / VoiceProfile schema
- 未改 resolve_binding
- 未删 Python capability builder

## 8. 下一阶段建议

### 推荐：P16-XIAOMI-MIMO-TTS-A0

**目标**：
只读分析小米 MiMo speech-synthesis-v2.5 API 文档，判断：
- 是否需要新增 xiaomi_mimo_tts adapter plugin
- 如何映射到当前 AdapterConfig / ProviderConfig / Capability 架构
- 与 minimax adapter 的差异点

**验证内容**：
- 小米 MiMo API 协议是否兼容现有 adapter
- 是否需要新的 adapter type
- 是否需要新增 config/adapters/xiaomi_mimo_tts.yaml
- 是否需要新增 config/providers.yaml entry

### 备选

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-OPENAI-COMPATIBLE-TTS-A0 | 设计 OpenAI-compatible TTS adapter | B1-CLOSE 后评估 |
| P16-DYNAMIC-PROVIDER-CONFIG-B2 | provider capability override enhancements | B1-CLOSE 后评估 |

## 9. 收口结论

AdapterConfig 与 Adapter 插件配置加载 B1 阶段完成收口 ✅

- AdapterConfig schema 实现（含 metadata 安全校验和 supported 字段）
- adapter_config_loader 实现（list/get/clear cache）
- config/adapters/mock.yaml 和 minimax.yaml 创建
- capability_registry 支持 ProviderConfig + AdapterConfig 合成（enabled=false 最高优先级）
- 全部 174 项测试通过
- 向后兼容现有 Python builder 逻辑
- 无阻塞风险

**下一阶段**：P16-XIAOMI-MIMO-TTS-A0（推荐）

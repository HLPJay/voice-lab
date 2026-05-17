# P16-ADAPTER-PLUGIN-CONFIG-A0：Adapter 插件化与配置分层设计

## 1. 背景与问题

### 1.1 当前已完成的能力

通过 B1 阶段，Provider 配置化接入已完成：

| 组件 | 现状 |
|---|---|
| `ProviderConfig` / `config/providers.yaml` | ✅ 已实现 |
| `provider_config_loader` | ✅ 已实现 |
| `adapter_type_registry` | ✅ 已实现 |
| `get_provider()` 配置化路由 | ✅ 已实现 |
| `capability_registry` 从 provider config 构建 | ✅ 已实现 |
| `CostGuardService` 使用 `real_cost` | ✅ 已实现 |

**当前路由链**：
```
provider name → ProviderConfig → adapter_type → ADAPTER_TYPE_REGISTRY → SpeechProvider class
```

### 1.2 当前尚未完成的能力

| 能力 | 现状 |
|---|---|
| `AdapterConfig` 拆分 | ❌ 未实现 |
| `config/adapters/*.yaml` | ❌ 未实现 |
| Adapter 插件默认能力配置化 | ❌ 未实现 |
| `ProviderConfig + AdapterConfig` 合并生成 `ProviderCapability` | ❌ 未实现 |
| Adapter 构造函数接收 `ProviderRuntimeConfig` | ❌ 未实现 |
| 新真实 Provider 接入 | ❌ 未实现 |

### 1.3 当前 `providers.yaml` 的问题

当前 `config/providers.yaml` 同时承担两类职责：

1. **Provider 实例配置**：`name`, `display_name`, `enabled`, `real_cost`, `api_key_env`
2. **Adapter 默认能力配置**：`default_model`, `endpoints`, `tts.models`, `batch.max_text_chars` 等

随着 Provider 实例增多，每个实例都重复复制相同的 adapter 默认能力值。例如 `mock` 和 `mock_configured` 的 adapter 能力完全相同，但每个 provider config 都独立定义一遍。

**影响**：当 adapter 端点路径变化时，所有 provider 实例都需要更新。

### 1.4 当前 capability_registry 的问题

当前 `capability_registry` 仍主要依赖 Python builder 函数（`_CAPABILITY_BUILDERS`），`ProviderConfig` 中的 capability 字段（如 `tts.enabled`）实际上没有生效——所有 capability 细节来自 builder 返回的 hardcoded 对象。

**影响**：无法通过 YAML 配置调整具体 capability 数值（如 max_text_chars、supported audio formats），只能 toggle enabled/disabled。

### 1.5 当前 adapter 的问题

当前 `MiniMaxSpeechAdapter` 和 `MockSpeechAdapter`：

1. 使用 `get_settings()` 获取配置，而不是通过 constructor 接收 `ProviderRuntimeConfig`
2. `provider_name` 是 class attribute，不是从 config 传入
3. `endpoints` 路径是 hardcoded 在代码中，而不是从 config 传入

**影响**：同一个 adapter class 的多个实例无法持有不同配置（无法用不同 base_url 实例化同一个 adapter）。

## 2. 核心架构判断

### 2.1 Adapter 是固定代码插件

> **判断**：Adapter 不是从零动态生成的接口代码。Adapter 是固定代码插件。

- 每个 adapter 是固定的 Python class，实现 `SpeechProvider` 接口
- adapter class 的代码不会从配置文件动态生成
- 新增协议需要新增 adapter Python class
- adapter class 一旦写好，一般不需要因为新增 provider 而修改

### 2.2 配置文件只负责声明

配置文件负责：
- 启用哪个 adapter plugin
- 如何初始化 adapter（API key env、base_url override）
- adapter 默认暴露哪些能力（可被 provider config override）
- provider 实例覆盖哪些配置

### 2.3 配置驱动的本质

**配置驱动的本质是减少每次新增 provider 时需要改的代码量**，而不是把 adapter 代码变成配置文件。

## 3. 配置分层方案

### 3.1 两层配置设计

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: ProviderConfig / config/providers.yaml              │
│  职责：provider 实例级配置                                      │
│  - name / display_name / enabled                             │
│  - adapter_type (指向哪个 adapter plugin)                      │
│  - real_cost / api_key_env / base_url override              │
│  - provider-level override (覆盖 adapter 默认值)              │
│  - provider-level metadata                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ adapter_type
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: AdapterConfig / config/adapters/*.yaml             │
│  职责：adapter plugin 默认能力                                 │
│  - adapter_type (adapter identity)                          │
│  - default_base_url / endpoints                              │
│  - default models / default_model                            │
│  - audio_formats / max_text_chars                           │
│  - supports_subtitle / supports_streaming / supports_emotion  │
│  - voice_clone / voice_design / batch / script 默认能力       │
│  - adapter-level metadata                                    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 建议目录结构

```
config/
  providers.yaml              # Provider 实例配置
  adapters/
    mock.yaml                # Mock adapter 默认配置
    minimax.yaml            # MiniMax adapter 默认配置
    openai_compatible_tts.yaml  # (未来)

app/
  domain/
    provider_config.py       # ProviderConfig schema (已存在)
    adapter_config.py        # AdapterConfig schema (新增)
  config/
    provider_config_loader.py    # (已存在)
    adapter_config_loader.py     # (新增)
  providers/
    adapter_type_registry.py     # (已存在)
    registry.py                  # (已存在)
    base.py                      # SpeechProvider (已存在)
    mock_speech_adapter.py        # (已存在)
    minimax_speech_adapter.py     # (已存在)
    openai_compatible_tts_adapter.py  # (未来新增)
```

### 3.3 AdapterConfig Schema 草案

```python
# app/domain/adapter_config.py

from typing import Any
from pydantic import BaseModel, Field


class EndpointConfig(BaseModel):
    t2a: str | None = None
    t2a_async: str | None = None
    query_async: str | None = None
    file_upload: str | None = None
    voice_clone: str | None = None
    voice_design: str | None = None
    delete_voice: str | None = None
    list_voices: str | None = None


class TTSCapabilityConfig(BaseModel):
    models: list[str] = Field(default_factory=list)
    default_model: str | None = None
    max_text_chars: int = 10000
    audio_formats: list[str] = Field(default_factory=list)
    supports_subtitle: bool = False
    supports_streaming: bool = False
    supports_emotion: bool = False


class BatchCapabilityConfig(BaseModel):
    max_text_chars: int = 50000
    max_segments: int | None = None


class AdapterConfig(BaseModel):
    """Configuration schema for an adapter plugin's default capabilities."""

    adapter_type: str = Field(..., description="Unique adapter type identifier")

    # API defaults
    default_base_url: str | None = None
    endpoints: EndpointConfig = Field(default_factory=EndpointConfig)

    # Model defaults
    default_model: str | None = None
    default_timeout_seconds: int = 120

    # Capability defaults
    tts: TTSCapabilityConfig | None = None
    batch: BatchCapabilityConfig | None = None
    # ... (voice_clone, voice_design, etc.)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}
```

## 4. 运行时合并逻辑

### 4.1 目标链路

```
provider name
  → ProviderConfig
  → adapter_type
  → AdapterConfig (config/adapters/{adapter_type}.yaml)
  → Adapter Plugin class (via adapter_type_registry)
  → ProviderRuntimeConfig (merged: AdapterConfig defaults + ProviderConfig overrides)
  → SpeechProvider adapter instance (with runtime config)
```

### 4.2 ProviderRuntimeConfig 草案

```python
class ProviderRuntimeConfig(BaseModel):
    """Final resolved config for a provider instance.

    Merge rules:
    1. Start with AdapterConfig defaults
    2. Override with ProviderConfig values (where set)
    3. Environment variable resolution happens lazily at access time
    """

    provider_name: str
    adapter_type: str
    base_url: str
    api_key: str | None  # resolved from api_key_env
    endpoints: EndpointConfig
    default_model: str
    tts_capability: TTSCapabilityConfig
    # ...
```

### 4.3 配置优先级

```
ProviderConfig override  >  AdapterConfig default  >  Adapter code fallback
```

- `ProviderConfig` 中的值会 override `AdapterConfig` 的默认值
- `AdapterConfig` 中的值是 adapter plugin 的合理默认值
- Adapter Python 代码中的 fallback 是最后的保障

**举例**：
- `config/adapters/minimax.yaml` 定义 `default_model: "speech-2.8-hd"`
- `config/providers.yaml` 中某 provider 可覆盖为 `default_model: "speech-02.5-turbo"`
- 如果都没配置，adapter 代码 fallback 到 hardcoded 默认值

## 5. Adapter 插件注册表设计

### 5.1 长期语义

`adapter_type_registry` 的长期语义：

```
adapter_type (string key)
  → adapter class (固定 Python 代码)
  → default AdapterConfig (config/adapters/{type}.yaml)
```

### 5.2 已有 adapter 注册

```python
# app/providers/__init__.py
register_adapter_type("mock", MockSpeechAdapter)
register_adapter_type("minimax", MiniMaxSpeechAdapter)
```

### 5.3 新增同协议 Provider 不需要改 registry

接入新的 MiniMax-based provider（如另一个 account）：

```yaml
# config/providers.yaml
- name: "minimax-account-2"
  adapter_type: "minimax"      # 复用同一个 adapter plugin
  real_cost: true
  api_key_env: "MINIMAX_ACCOUNT2_API_KEY"
```

不需要改 `adapter_type_registry.py`，不需要改 adapter class。

### 5.4 新增新协议 Provider 才需要改 registry

接入 OpenAI-compatible TTS provider：

```python
# app/providers/__init__.py
register_adapter_type("openai_compatible_tts", OpenAICompatibleTTSAdapter)
```

这是唯一需要改 Python 代码的情况。

## 6. Capability 合成设计

### 6.1 当前状态

当前 `_build_capability_from_config()` 从 `ProviderConfig` 读取元信息（`real_cost`, `adapter_type`），但 capability 细节仍来自 Python builder。

### 6.2 目标状态

`ProviderConfig + AdapterConfig → ProviderCapability`

支持通过 YAML 配置表达的字段：

| 字段 | 来源 | 说明 |
|---|---|---|
| `tts.supported` | ProviderConfig.tts.enabled | Provider-level toggle |
| `tts.models` | AdapterConfig | adapter 默认值 |
| `tts.default_model` | ProviderConfig 或 AdapterConfig | 按优先级合并 |
| `tts.audio_formats` | AdapterConfig | adapter 默认值 |
| `tts.supports_subtitle` | AdapterConfig | adapter 默认值 |
| `tts.supports_streaming` | AdapterConfig | adapter 默认值 |
| `tts.supports_emotion` | AdapterConfig | adapter 默认值 |
| `batch.enabled` | ProviderConfig.batch.enabled | Provider-level toggle |
| `batch.max_text_chars` | AdapterConfig | adapter 默认值 |
| `script.enabled` | ProviderConfig.script.enabled | Provider-level toggle |
| `voice_clone.enabled` | ProviderConfig.voice_clone.enabled | Provider-level toggle |
| `voice_design.enabled` | ProviderConfig.voice_design.enabled | Provider-level toggle |
| `provider_voices.enabled` | ProviderConfig.provider_voices.enabled | Provider-level toggle |
| `metadata.real_cost` | ProviderConfig.real_cost | ✅ 已配置化 |
| `metadata.adapter_type` | ProviderConfig.adapter_type | ✅ 已配置化 |
| `metadata.configured_via_yaml` | — | ✅ 已配置化 |

### 6.3 不急于抽象的字段

以下字段涉及模型通用能力抽象，当前不试图一次性定义完整：

- `speed` / `vol` / `pitch` range（不同 provider 差异大）
- `emotion` 参数格式（不同 provider 表达方式不同）
- `voice_clone` 细节参数
- `voice_design` 细节参数

**原因**：这些字段的通用抽象需要在多个真实 Provider 接入后，才能准确判断哪些是"通用"、哪些是"provider 特定"的。提前抽象容易出错。

### 6.4 MiniMax-first 痕迹

当前 `SpeechProvider` 接口和 `RenderPlan` 有 MiniMax-first 设计痕迹：

- `emotion` 参数（MiniMax 特有，其他 provider 可能不支持）
- `audio_format` 枚举值可能不通用
- `output_format: "hex"` 是 MiniMax 特有

**处理**：不在本阶段重组。重组需要基于 OpenAI / 其他 Provider 接入后的真实差异分析。

## 7. 接入新模型 / 新 Provider 的规则

### 情况 A：已有 adapter plugin，新增模型

**条件**：已有 adapter class，新模型只是 API 上的新 model name。

**操作**：修改 `config/adapters/{adapter_type}.yaml` 中的 `models` 列表。

**示例**：MiniMax 新增了 `speech-3.0-hd` 模型。
```yaml
# config/adapters/minimax.yaml
tts:
  models:
    - "speech-2.8-hd"
    - "speech-02.5-turbo"
    - "speech-3.0-hd"    # 新增
```

### 情况 B：已有 adapter plugin，新增 Provider 实例

**条件**：同一种 adapter type 的新 account/endpoint。

**操作**：修改 `config/providers.yaml`，新增 provider entry。

**示例**：用户有第二个 MiniMax 账号。
```yaml
# config/providers.yaml
- name: "minimax-account-2"
  adapter_type: "minimax"
  api_key_env: "MINIMAX_ACCOUNT2_API_KEY"
```

### 情况 C：新 Provider 兼容已有协议

**条件**：新 Provider 使用与已有 adapter 相同的 API 协议。

**操作**：
1. 在 `config/providers.yaml` 新增 provider entry，指向已有 `adapter_type`
2. 如果 endpoint URL 不同，override `base_url` 或 `endpoints`
3. 如果默认 model 不同，override `default_model`

**示例**：接入另一个 OpenAI-compatible TTS provider。
```yaml
# config/providers.yaml
- name: "my-openai-tts"
  adapter_type: "openai_compatible_tts"
  api_key_env: "MY_OPENAI_API_KEY"
  base_url: "https://api.example.com/v1"
```

### 情况 D：新 Provider 是新协议

**条件**：新 Provider 的 API 协议与所有现有 adapter 都不兼容。

**操作**：
1. 编写新的 adapter class（固定 Python 代码），实现 `SpeechProvider` 接口
2. 在 `app/providers/__init__.py` 注册 `adapter_type`
3. 新增 `config/adapters/{new_type}.yaml`
4. 新增 `config/providers.yaml` entry
5. 新增 tests

**示例**：接入 Azure TTS。

## 8. 问题与处理方案落地

### 问题 1：`providers.yaml` 同时承担 instance 和 adapter 默认职责

**现状**：`mock` 和 `mock_configured` 各自完整定义了相同的 adapter 能力，存在重复。

**影响**：adapter 能力变更需要更新所有 provider entries，维护成本高。

**处理方案**：拆分为两层配置（ProviderConfig + AdapterConfig）。

**为什么不现在处理**：需要同时实现 `AdapterConfig` schema、`adapter_config_loader`、capability 合成逻辑、adapter constructor 改造。工作量大，可以作为 B2 阶段。

**后续阶段**：B2 阶段实施。

### 问题 2：capability_registry 仍主要依赖 Python builder

**现状**：`_CAPABILITY_BUILDERS` 是 Python dict，capability 细节 hardcoded 在 builder 函数中。

**影响**：无法通过 YAML 调整 capability 数值（如 `max_text_chars`），只能 toggle enabled/disabled。

**处理方案**：在 B2 阶段支持 `AdapterConfig` 中的 capability 字段，合并到 `ProviderCapability`。

**为什么不现在处理**：当前 `ProviderConfig` 中的 capability toggle 已足够 toggle 能力开关，数值 hardcoded 在 builder 中暂不影响接入新 Provider。

**后续阶段**：B2 阶段实施。

### 问题 3：adapter 尚未接收 ProviderRuntimeConfig

**现状**：`MiniMaxSpeechAdapter` 使用 `get_settings()` 和 class attribute `provider_name`，无法在同一 adapter class 上实例化不同配置。

**影响**：同一个 adapter class 无法服务两个不同 base_url 的 provider 实例。

**处理方案**：在 B2 阶段改造 adapter constructor 接收 `ProviderRuntimeConfig`，不再用 `get_settings()`。

**为什么不现在处理**：当前 `get_provider("minimax-account-2")` 会返回第二个 `MiniMaxSpeechAdapter` 实例，但两个实例共享 `get_settings()` 的值（因为 adapter 没有接收 instance-level config）。这在当前阶段不构成问题，因为新增 provider 都是通过不同 env var 实现配置隔离的。

**后续阶段**：B2 阶段实施。

### 问题 4：通用协议存在 MiniMax-first 痕迹

**现状**：`SpeechProvider` 接口、`RenderPlan`、`audio_format` 枚举值存在 MiniMax-first 设计。

**影响**：接入非 MiniMax provider 时可能需要适配层。

**处理方案**：在 OpenAI / 其他 Provider 接入时，基于真实差异分析后再决定是否需要抽象适配层或保持 provider-specific。

**为什么不现在处理**：重组需要多个真实 Provider 接入后的差异分析，现在做会过早优化。

**后续阶段**：OpenAI-compatible TTS adapter 接入时分析。

### 问题 5：模型通用能力需要真实多 Provider 接入后才能准确抽象

**现状**：当前所有 capability schema（Pydantic models）都是基于 MiniMax 设计的。

**影响**：提前抽象可能不准确，导致后续需要大幅修改。

**处理方案**：在 B2 阶段先支持 adapter config 中的基础字段（models、audio_formats、supported flags），真正复杂的参数（speed/pitch/emotion range）留到多 Provider 接入后。

**为什么不现在处理**：需要真实 Provider 接入后的差异数据支撑抽象设计。

**后续阶段**：OpenAI-compatible TTS 接入后分析。

## 9. 当前不做什么

以下内容不在本 A0 设计范围内：

| 内容 | 原因 |
|---|---|
| OpenAI adapter 实现 | 需要真实 API 对比分析 |
| AdapterConfig 代码实现 | 本 A0 只做设计 |
| RenderPlan 重构 | 需要多 Provider 差异分析 |
| VoiceBinding / ProviderVoice schema 修改 | 不在范围内 |
| resolve_binding 修改 | 不在范围内 |
| Provider 管理 UI | 当前阶段不需要 |
| 运行时配置热更新 | 当前阶段不需要 |
| 通用协议重组（MiniMax-first 痕迹） | 需要多 Provider 接入后分析 |

## 10. 下一阶段建议

### 推荐优先：B2 — AdapterConfig 与插件配置加载

**目标**：
1. 实现 `AdapterConfig` schema (`app/domain/adapter_config.py`)
2. 实现 `adapter_config_loader` (`app/config/adapter_config_loader.py`)
3. 创建 `config/adapters/mock.yaml` 和 `config/adapters/minimax.yaml`
4. 改造 `capability_registry` 支持 `ProviderConfig + AdapterConfig` 合成
5. 改造 `MiniMaxSpeechAdapter` constructor 接收 `ProviderRuntimeConfig`（可选）

**验证场景**：
- `mock_configured` provider 通过 `mock` adapter + `mock` adapter config 获取 capability
- `minimax` provider 通过 `minimax` adapter + `minimax` adapter config 获取 capability

### 后续阶段：OpenAI-compatible TTS A0

**目标**：设计第一个真实非 MiniMax Provider adapter，验证 Adapter 插件化接入机制。

**验证内容**：
- 新 adapter plugin 不需要改主业务链路
- capability 可通过 adapter config 配置
- 新 provider 接入只需要改配置文件

## 11. B1/B2 阶段对比

| | B1 | B2 |
|---|---|---|
| 核心 | Provider 配置化 | AdapterConfig 拆分 |
| ProviderConfig | ✅ 已实现 | 增强 override |
| AdapterConfig | ❌ | ✅ 新增 |
| adapter_config_loader | ❌ | ✅ 新增 |
| config/adapters/*.yaml | ❌ | ✅ 新增 |
| capability_registry 合成 | ❌ | ✅ 支持 |
| adapter 接收 RuntimeConfig | ❌ | 可选 |
| 新真实 Provider 接入 | ❌ | ❌ |

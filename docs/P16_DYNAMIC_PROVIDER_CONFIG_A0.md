# P16-DYNAMIC-PROVIDER-CONFIG-A0：Provider 配置化接入架构设计

## 1. 背景与目标

### 1.1 当前状态

当前 Provider 接入是硬编码的：

```python
# app/providers/registry.py
PROVIDER_REGISTRY: dict[str, type[SpeechProvider]] = {
    "mock": MockSpeechAdapter,
    "minimax": MiniMaxSpeechAdapter,
}

def get_provider(name: str) -> SpeechProvider:
    cls = PROVIDER_REGISTRY.get(name)
    if not cls:
        raise UnsupportedProvider(f"Unsupported provider: {name}", name)
    return cls()
```

```python
# app/providers/capability_registry.py
def _build_registry() -> dict[str, ProviderCapability]:
    return {
        "mock": MOCK_CAPABILITY,
        "minimax": build_minimax_capability(),
    }
```

```python
# app/services/cost_guard_service.py
COST_PROVIDER_SET = frozenset({"minimax"})
```

新增一个 Provider 需要：
1. 在 `PROVIDER_REGISTRY` 增加条目
2. 在 `_build_registry()` 增加 capability 构建逻辑
3. 在 `COST_PROVIDER_SET` 增加条目（如适用）
4. 在 `app/core/config.py` 增加 env 配置

每次添加 Provider 都要改代码，新增外部 Provider（OpenAI/Azure/火山引擎/阿里云等）成本高。

### 1.2 目标

将 Provider 接入从硬编码改造为配置驱动：

```
Provider name -> ProviderConfig (YAML) -> adapter_type -> Adapter Class
```

新增 Provider 时只需在 YAML 配置文件中增加条目，不需要改 Python 代码（只需要新的 Adapter 类如果 adapter_type 不支持）。

### 1.3 本阶段范围

**本阶段是设计文档阶段（A0），不实现代码。**

目标：
1. 完成配置化架构设计文档
2. 给出 `config/providers.yaml` 格式设计
3. 给出 `provider_config_loader` 接口设计
4. 给出 Adapter Type Registry 设计
5. 给出 Capability Registry 集成设计
6. 给出 Cost Guard 改造方案
7. 给出前端影响分析
8. 给出 B1 实现阶段建议
9. 用 `mock_configured` 作为验证场景（不调用真实 API）

## 2. 核心设计原则

1. **配置驱动**：Provider 元信息（名称、显示名、是否启用、是否真实计费、API 配置）从 YAML 文件读取
2. **适配器协议化**：每个 Provider 通过 `adapter_type` 协议接入，Adapter 类与 Provider 名称解耦
3. **Capability 即代码**：每个 Provider 的 capability 细节（TTS 参数、batch 限制、clone 支持等）仍然通过 Python 代码构建（因为涉及复杂验证逻辑），但外部元信息从配置读取
4. **不破坏现有链路**：`VoiceRenderService` 主业务链路不变，`get_provider()` 接口不变
5. **向后兼容**：`mock` 和 `minimax` 的现有行为保持不变，只改内部实现

## 3. ProviderConfig Schema

### 3.1 YAML 配置格式

文件位置：`config/providers.yaml`

```yaml
providers:
  - name: "mock"
    display_name: "Mock"
    enabled: true
    adapter_type: "mock"
    real_cost: false
    api_key_env: null
    base_url_env: null
    base_url: null
    endpoints: {}
    default_model: "mock-tts"
    tts:
      enabled: true
      default_model: "mock-tts"
    batch:
      enabled: true
    script:
      enabled: true
    voice_clone:
      enabled: true
    voice_design:
      enabled: true
    provider_voices:
      enabled: true
    metadata:
      mode: "mock"

  - name: "minimax"
    display_name: "MiniMax"
    enabled: true
    adapter_type: "minimax"
    real_cost: true
    api_key_env: "MINIMAX_API_KEY"
    base_url_env: null
    base_url: "https://api.minimaxi.com"
    endpoints:
      t2a: "/v1/t2a_v2"
      t2a_async: "/v1/t2a_async_v2"
      query_async: "/v1/query/t2a_async_query_v2"
      file_upload: "/v1/files/upload"
      voice_clone: "/v1/voice_clone"
      voice_design: "/v1/voice_design"
      delete_voice: "/v1/delete_voice"
    default_model: "speech-2.8-hd"
    tts:
      enabled: true
      default_model: "speech-2.8-hd"
    batch:
      enabled: true
    script:
      enabled: true
    voice_clone:
      enabled: true
    voice_design:
      enabled: true
    provider_voices:
      enabled: true
    metadata:
      ws_model: "speech-2.8-hd"
      clone_audio_max_size_mb: 20

  - name: "mock_configured"
    display_name: "Mock Configured"
    enabled: true
    adapter_type: "mock"
    real_cost: false
    api_key_env: null
    base_url_env: null
    base_url: null
    endpoints: {}
    default_model: "mock-tts"
    tts:
      enabled: true
      default_model: "mock-tts"
    batch:
      enabled: true
    script:
      enabled: true
    voice_clone:
      enabled: true
    voice_design:
      enabled: true
    provider_voices:
      enabled: true
    metadata:
      mode: "mock_configured"
      configured_via_yaml: true
```

### 3.2 ProviderConfig Pydantic Schema

```python
# app/domain/provider_config.py

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


class CapabilityToggle(BaseModel):
    enabled: bool = True


class TTSConfig(CapabilityToggle):
    default_model: str | None = None


class BatchConfig(CapabilityToggle):
    pass


class ScriptConfig(CapabilityToggle):
    pass


class VoiceCloneConfig(CapabilityToggle):
    pass


class VoiceDesignConfig(CapabilityToggle):
    pass


class ProviderVoicesConfig(CapabilityToggle):
    pass


class ProviderConfig(BaseModel):
    """Configuration schema for a single provider."""

    # Core identity
    name: str = Field(..., description="Unique provider identifier (used in API and registry)")
    display_name: str = Field(..., description="Human-readable display name")

    # Lifecycle
    enabled: bool = Field(True, description="Whether this provider is active")

    # Adapter routing
    adapter_type: str = Field(
        ...,
        description="Adapter type key, maps to ADAPTER_TYPE_REGISTRY. "
                   "e.g. 'mock', 'minimax', 'openai', 'azure', 'volcengine', 'aliyun'"
    )

    # Cost
    real_cost: bool = Field(
        False,
        description="Whether this provider incurs real costs (affects CostGuardService)"
    )

    # API configuration
    api_key_env: str | None = Field(
        None,
        description="Environment variable name containing the API key. "
                    "Never serialized to API responses."
    )
    base_url_env: str | None = Field(
        None,
        description="Environment variable name containing the base URL override."
    )
    base_url: str | None = Field(
        None,
        description="Default base URL for this provider (used if base_url_env not set)"
    )
    endpoints: EndpointConfig = Field(
        default_factory=EndpointConfig,
        description="API endpoint paths for this provider"
    )

    # Default model
    default_model: str | None = Field(
        None,
        description="Default model for this provider"
    )

    # Capability toggles (capability details are still built in Python)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    batch: BatchConfig = Field(default_factory=BatchConfig)
    script: ScriptConfig = Field(default_factory=ScriptConfig)
    voice_clone: VoiceCloneConfig = Field(default_factory=VoiceCloneConfig)
    voice_design: VoiceDesignConfig = Field(default_factory=VoiceDesignConfig)
    provider_voices: ProviderVoicesConfig = Field(default_factory=ProviderVoicesConfig)

    # Arbitrary metadata (no secrets allowed)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def api_key(self) -> str | None:
        """Resolve API key from environment variable."""
        if not self.api_key_env:
            return None
        import os
        return os.environ.get(self.api_key_env)

    @property
    def resolved_base_url(self) -> str | None:
        """Resolve base URL from env var or config."""
        if self.base_url_env:
            import os
            return os.environ.get(self.base_url_env)
        return self.base_url

    model_config = {"extra": "forbid"}
```

## 4. provider_config_loader 设计

### 4.1 文件位置

`app/config/provider_config_loader.py`

### 4.2 接口设计

```python
"""Provider configuration loader from config/providers.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from app.domain.provider_config import ProviderConfig


_PROVIDER_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "providers.yaml"

# In-memory cache
_cached_configs: dict[str, ProviderConfig] | None = None


def _load_raw_configs() -> list[dict]:
    """Load raw configs from YAML file. Does not parse into ProviderConfig."""
    path = os.environ.get("VOICE_LAB_PROVIDER_CONFIG_PATH", str(_PROVIDER_CONFIG_PATH))
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "providers" not in data:
        return []
    return data["providers"]


def list_provider_configs() -> list[ProviderConfig]:
    """List all provider configs (cached)."""
    global _cached_configs
    if _cached_configs is None:
        from app.domain.provider_config import ProviderConfig
        raw = _load_raw_configs()
        _cached_configs = {c["name"]: ProviderConfig(**c) for c in raw}
    return list(_cached_configs.values())


def get_provider_config(name: str) -> ProviderConfig | None:
    """Get a single provider config by name (cached)."""
    configs = list_provider_configs()
    for cfg in configs:
        if cfg.name == name:
            return cfg
    return None


def list_enabled_provider_configs() -> list[ProviderConfig]:
    """List all enabled provider configs."""
    return [c for c in list_provider_configs() if c.enabled]


def clear_provider_config_cache() -> None:
    """Clear the in-memory config cache. Call after config file changes in tests."""
    global _cached_configs
    _cached_configs = None
```

### 4.3 缓存策略

- `_cached_configs` 是模块级缓存，生命周期跟随进程
- `clear_provider_config_cache()` 用于测试中清除缓存
- 配置路径可通过环境变量 `VOICE_LAB_PROVIDER_CONFIG_PATH` 覆盖

## 5. Adapter Type Registry

### 5.1 设计思路

当前问题是 `PROVIDER_REGISTRY` 直接映射 `provider name -> Adapter class`。这导致：
- `provider name` 和 `Adapter class` 强耦合
- 想用 `minimax` 适配器但换一个 name 就得改代码

改造后：

```
provider name -> ProviderConfig -> adapter_type -> ADAPTER_TYPE_REGISTRY[adapter_type] -> Adapter class
```

`PROVIDER_REGISTRY` 改为由配置驱动，不再硬编码 `mock`/`minimax`。

### 5.2 ADAPTER_TYPE_REGISTRY

```python
# app/providers/adapter_type_registry.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base import SpeechProvider

# Maps adapter_type string to a factory function
ADAPTER_TYPE_REGISTRY: dict[str, callable] = {}


def register_adapter_type(adapter_type: str, factory: callable) -> None:
    """Decorator or manual registration for adapter types."""
    ADAPTER_TYPE_REGISTRY[adapter_type] = factory


def get_adapter_type_adapter(adapter_type: str) -> type[SpeechProvider]:
    """Look up an adapter class by adapter_type string."""
    from app.core.errors import UnsupportedProvider
    factory = ADAPTER_TYPE_REGISTRY.get(adapter_type)
    if not factory:
        raise UnsupportedProvider(
            f"Unsupported adapter type: {adapter_type}",
            adapter_type,
        )
    return factory
```

### 5.3 Adapter 类注册

```python
# app/providers/__init__.py

from app.providers.mock_speech_adapter import MockSpeechAdapter
from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
from app.providers.adapter_type_registry import register_adapter_type

# Register adapter types (code change needed only when adding NEW protocol types)
register_adapter_type("mock", MockSpeechAdapter)
register_adapter_type("minimax", MiniMaxSpeechAdapter)
```

### 5.4 新增 Provider 不需要改 registry.py

添加新的 Provider（如 `mock_configured`）时：
1. 在 `config/providers.yaml` 增加条目，`adapter_type: "mock"`
2. `get_provider("mock_configured")` 查找 ProviderConfig，得到 `adapter_type: "mock"`
3. `get_adapter_type_adapter("mock")` 返回 `MockSpeechAdapter`
4. `registry.py` 中的 `get_provider()` 逻辑需要改造（见 5.5）

### 5.5 改造后的 get_provider()

```python
# app/providers/registry.py

from app.core.errors import UnsupportedProvider
from app.providers.base import SpeechProvider
from app.config.provider_config_loader import get_provider_config
from app.providers.adapter_type_registry import get_adapter_type_adapter


def get_provider(name: str) -> SpeechProvider:
    """Look up a provider by name and return a new instance.

    Resolution chain:
      name -> ProviderConfig -> adapter_type -> ADAPTER_TYPE_REGISTRY -> Adapter class
    """
    config = get_provider_config(name)
    if not config:
        raise UnsupportedProvider(f"Unsupported provider: {name}", name)
    if not config.enabled:
        raise UnsupportedProvider(f"Provider {name} is not enabled", name)

    adapter_cls = get_adapter_type_adapter(config.adapter_type)
    return adapter_cls()
```

**关键约束**：`get_provider()` 本身不硬编码任何 provider 名称。已有的 `mock`/`minimax` 通过 YAML 配置找到对应的 `adapter_type`，再路由到适配器类。

### 5.6 Backward Compatibility

`PROVIDER_REGISTRY` 可以保留用于静态检查和 type hint：

```python
# 保留，但不再用于 get_provider 运行时路由
PROVIDER_REGISTRY: dict[str, type[SpeechProvider]] = {
    "mock": MockSpeechAdapter,
    "minimax": MiniMaxSpeechAdapter,
}
```

如果配置文件中找不到某个 name，回退到 `PROVIDER_REGISTRY`（向后兼容旧逻辑）：

```python
def get_provider(name: str) -> SpeechProvider:
    config = get_provider_config(name)
    if config:
        adapter_cls = get_adapter_type_adapter(config.adapter_type)
        return adapter_cls()
    # Fallback for hardcoded providers (backward compatibility)
    cls = PROVIDER_REGISTRY.get(name)
    if not cls:
        raise UnsupportedProvider(f"Unsupported provider: {name}", name)
    return cls()
```

## 6. Capability Registry 集成

### 6.1 改造思路

当前 `_build_registry()` 硬编码构建 capability。改造后：

```
ProviderConfig -> capability builder function -> ProviderCapability
```

每个 `adapter_type` 注册一个 capability builder：

```python
# app/providers/capability_registry.py

from app.core.errors import UnsupportedProvider
from app.domain.capabilities import ProviderCapability
from app.config.provider_config_loader import list_enabled_provider_configs
from app.providers.mock_capabilities import build_mock_capability
from app.providers.minimax_capabilities import build_minimax_capability

# Maps adapter_type to capability builder functions
_CAPABILITY_BUILDERS: dict[str, callable] = {
    "mock": build_mock_capability,
    "minimax": build_minimax_capability,
}


def _build_capability_from_config(config: ProviderConfig) -> ProviderCapability:
    """Build ProviderCapability from a ProviderConfig + adapter_type builder."""
    builder = _CAPABILITY_BUILDERS.get(config.adapter_type)
    if not builder:
        raise UnsupportedProvider(
            f"No capability builder for adapter type: {config.adapter_type}",
            config.name,
        )
    base_capability = builder()

    # Override/enrich with config-driven fields
    return ProviderCapability(
        provider=config.name,
        display_name=config.display_name,
        enabled=config.enabled,
        default_model=config.default_model or base_capability.default_model,
        tts=base_capability.tts,
        batch=base_capability.batch,
        script=base_capability.script,
        voice_clone=base_capability.voice_clone,
        voice_design=base_capability.voice_design,
        provider_voices=base_capability.provider_voices,
        metadata={
            **base_capability.metadata,
            "adapter_type": config.adapter_type,
            "real_cost": config.real_cost,
            "configured_via_yaml": True,
        },
    )


def _build_registry() -> dict[str, ProviderCapability]:
    """Build the full capability registry from YAML config."""
    registry = {}
    for config in list_enabled_provider_configs():
        cap = _build_capability_from_config(config)
        registry[config.name] = cap
    return registry
```

### 6.2 Metadata 安全约束

```python
# app/domain/capabilities.py 中的 SENSITIVE_METADATA_KEYS 保持不变
SENSITIVE_METADATA_KEYS = {
    "api_key", "apikey", "secret", "token", "password",
    "minimax_api_key", "openai_api_key",
}
```

`ProviderConfig.metadata` 不允许包含 `api_key_env` 对应的真实值。API 响应中只暴露：

```python
metadata={
    "adapter_type": config.adapter_type,
    "real_cost": config.real_cost,
    "configured_via_yaml": True,
    # 允许的非敏感 metadata
}
```

`api_key_env` 本身不出现在 capability metadata 中。

### 6.3 /api/voice/capabilities 保持不变

```python
# app/api/voice_capabilities.py
@router.get("/capabilities", response_model=list[ProviderCapability])
def get_capabilities():
    return list_capabilities()
```

响应格式不变，因为 `ProviderCapability` schema 没变。

## 7. Cost Guard 改造

### 7.1 改造方案

不再使用 `COST_PROVIDER_SET = frozenset({"minimax"})`。

```python
# app/services/cost_guard_service.py

from app.config.provider_config_loader import get_provider_config


class CostGuardService:
    def require_confirmed(self, provider: str, operation: str, confirm_cost: bool) -> None:
        """Enforce cost confirmation for high-risk operations on real-cost providers.

        Rules:
        - mock provider: never requires confirm_cost (always allowed)
        - ProviderConfig.real_cost == True and operation in HIGH_RISK_OPERATIONS
          and confirm_cost != True: raise ValidationError
        """
        if provider == "mock":
            return

        config = get_provider_config(provider)
        if config and config.real_cost and operation in HIGH_RISK_OPERATIONS and not confirm_cost:
            raise ValidationError(
                "需要确认成本后才能执行该操作",
                f"{operation} requires confirm_cost=true for {provider} provider",
            )
```

### 7.2 Cost Guard 规则保持不变

- `HIGH_RISK_OPERATIONS` 集合不变
- `estimate_t2a_cost` 仍按 `provider == "minimax"` 特殊处理（这是 pricing 问题，不是 cost guard 问题）
- `COST_PROVIDER_SET` 可以移除（如果确定没有其他代码依赖它）

### 7.3 Pricing Metadata

后续可在 `ProviderConfig.metadata` 中增加 pricing 信息：

```yaml
metadata:
  pricing:
    tts_per_10k_chars: 2.0
    currency: "CNY"
    model_overrides:
      "speech-2.8-hd": 3.5
```

这属于 B1 后续扩展，不在本 A0 设计范围内。

## 8. 前端影响

### 8.1 /api/voice/capabilities 继续工作

前端 `provider_capabilities.js` 继续依赖 `/api/voice/capabilities`，该接口返回的 `ProviderCapability[]` 格式不变。

### 8.2 provider 下拉不受影响

前端 provider 下拉的选项来源于 `/api/voice/capabilities` 返回的 `provider` 字段。配置化后仍然返回相同的 provider 列表（只是数据来源从硬编码变成了 YAML）。

### 8.3 high-risk 确认不再写死

当前前端有类似代码：

```javascript
// app/static/index.html (P16-CANCEL-FIX1)
if (provider === 'minimax' && !confirmHighRiskOperation(operation)) {
  return;
}
```

改造后应该通过 capability metadata 标记：

```javascript
// 从 /api/voice/capabilities 获取 real_cost 信息
const caps = await fetch('/api/voice/capabilities').then(r => r.json());
const cap = caps.find(c => c.provider === provider);
const isRealCost = cap?.metadata?.real_cost === true;

if (isRealCost && !confirmHighRiskOperation(operation)) {
  return;
}
```

`provider === 'minimax'` 的硬编码改为通过 capability metadata 判断。这属于 B1 前端改造范围。

## 9. mock_configured 验证策略

### 9.1 目标

验证配置化接入的最小路径：
1. `config/providers.yaml` 中增加 `mock_configured` 条目
2. `get_provider("mock_configured")` 能返回可用的 `MockSpeechAdapter`
3. `/api/voice/capabilities` 响应中包含 `mock_configured`
4. 不调用任何真实外部 API

### 9.2 mock_configured 配置

```yaml
  - name: "mock_configured"
    display_name: "Mock Configured"
    enabled: true
    adapter_type: "mock"
    real_cost: false
    api_key_env: null
    base_url_env: null
    base_url: null
    endpoints: {}
    default_model: "mock-tts"
    tts:
      enabled: true
      default_model: "mock-tts"
    batch:
      enabled: true
    script:
      enabled: true
    voice_clone:
      enabled: true
    voice_design:
      enabled: true
    provider_voices:
      enabled: true
    metadata:
      mode: "mock_configured"
      configured_via_yaml: true
```

### 9.3 验证步骤（B1 实现阶段）

1. 添加 `mock_configured` 到 YAML
2. `get_provider("mock_configured")` 返回 `MockSpeechAdapter` 实例
3. `/api/voice/capabilities` 包含 `mock_configured`
4. Cost Guard 对 `mock_configured.real_cost = false` 不触发确认
5. `get_provider("mock")` 仍然正常工作（向后兼容）
6. `get_provider("minimax")` 仍然返回 `MiniMaxSpeechAdapter`

## 10. B1 实现阶段建议

### 10.1 阶段目标

完成 Provider 配置化的最小可用实现（MVI），以 `mock_configured` 作为端到端验证场景。

### 10.2 实现步骤

**Step 1: 新增文件**
- `app/domain/provider_config.py` — `ProviderConfig` Pydantic schema
- `app/config/__init__.py` — config package
- `app/config/provider_config_loader.py` — YAML loader
- `app/providers/adapter_type_registry.py` — adapter type registry
- `config/providers.yaml` — 初始配置文件（包含 mock 和 minimax）

**Step 2: 改造 registry.py**
- 将 `PROVIDER_REGISTRY` 改为 `get_provider()` 由配置驱动
- 保留 fallback 向后兼容

**Step 3: 改造 capability_registry.py**
- `_build_registry()` 从 YAML 配置读取
- capability builder 仍然按 `adapter_type` 分发

**Step 4: 改造 CostGuardService**
- 用 `ProviderConfig.real_cost` 替代 `COST_PROVIDER_SET`
- `COST_PROVIDER_SET` 移除或标记废弃

**Step 5: 添加 mock_configured 验证**
- 在 YAML 中添加 `mock_configured` 条目
- 端到端测试 `get_provider("mock_configured")` 返回可用 adapter
- `/api/voice/capabilities` 包含 `mock_configured`

**Step 6: 回归测试**
- 现有 `get_provider("mock")` 和 `get_provider("minimax")` 仍然工作
- `CostGuardService.require_confirmed("minimax", ...)` 行为不变
- `/api/voice/capabilities` 响应格式不变
- 全部既有测试通过

### 10.3 B1 测试要求

```
新增测试：
- test_provider_config_schema: ProviderConfig validation
- test_provider_config_loader: YAML loading and caching
- test_adapter_type_registry: adapter type routing
- test_get_provider_from_config: get_provider uses config
- test_mock_configured_provider: mock_configured works
- test_cost_guard_uses_real_cost: CostGuard uses config.real_cost
```

### 10.4 不在 B1 实现的内容

- OpenAI / Azure / 火山 / 阿里云 接入
- 管理 UI（增删改 provider 配置）
- 运行时配置热更新（不实现）
- pricing metadata
- 前端 high-risk 确认改造

## 11. 关键架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     config/providers.yaml                    │
│  (mock, minimax, mock_configured, openai, azure, ...)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               provider_config_loader.py                      │
│  list_provider_configs() / get_provider_config(name)        │
│  list_enabled_provider_configs() / clear_provider_config_cache()│
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
┌──────────────────┐    ┌──────────────────────────┐
│ ProviderConfig    │    │  ADAPTER_TYPE_REGISTRY    │
│ .name             │    │  "mock" → MockSpeechAdapter│
│ .adapter_type     │───▶│  "minimax" → MiniMaxAdapt │
│ .real_cost        │    │  "openai" → OpenAIAdapt  │
│ .api_key_env      │    └──────────────────────────┘
│ .base_url         │
│ ...               │
└──────────────────┘
          │                         ▲
          ▼                         │
┌──────────────────┐                │
│ get_provider(name)│───────────────┘
└────────┬─────────┘
         │ returns SpeechProvider instance
         ▼
┌─────────────────────────────────────┐
│      VoiceRenderService.render()     │
│  (unchanged main business logic)     │
└─────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │     CostGuardService.require_confirmed()│
         │  Uses ProviderConfig.real_cost        │
         │  instead of COST_PROVIDER_SET         │
         └──────────────────────────────────────┘
```

## 12. 未纳入本设计范围

以下内容在后续阶段处理，不在本 A0 设计范围内：

1. **OpenAI / Azure / 火山引擎 / 阿里云实际接入** — 需要单独调研各 Provider API 差异
2. **管理 UI** — 增加/删除/编辑 provider 配置
3. **运行时配置热更新** — 进程启动后修改 YAML 不生效
4. **Pricing metadata** — per-model pricing 信息
5. **前端 high-risk 确认改造** — `provider === "minimax"` 硬编码改为 capability metadata 判断
6. **Provider 生命周期管理** — 启用/禁用 provider 而不重启服务
7. **Provider 权重/优先级** — 多 provider 负载均衡
8. **Provider 健康检查** — 失败时自动切换

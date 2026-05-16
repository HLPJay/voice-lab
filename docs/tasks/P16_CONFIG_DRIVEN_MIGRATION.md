# P16-CONFIG-DRIVEN-MIGRATION：全面配置驱动迁移 + 插件化注册 + 环境变量精简

## 背景

当前系统存在三套配置体系并存的过渡态：

1. **旧体系**：`app/core/config.py` Settings + `.env`（MiniMax adapter 实际消费）
2. **新体系 Layer 1**：`config/providers.yaml`（provider 实例配置）
3. **新体系 Layer 2**：`config/adapters/*.yaml`（adapter 默认能力）

同时，adapter 注册仍有多处硬编码：
- `registry.py` 中的 `PROVIDER_REGISTRY` 静态 dict
- `capability_registry.py` 中的 `_CAPABILITY_BUILDERS` 静态 dict
- `adapter_type_registry.py` 中的 `_ensure_core_adapters_registered()` hardcoded fallback
- `minimax_capabilities.py` 中整个 builder 函数依赖 Settings

**目标**：新增 adapter 只需要做两件事：
1. 写一个 Python class（实现 SpeechProvider 接口）
2. 写一个 `config/adapters/{type}.yaml`（声明 plugin.import_path + 能力配置）

不改任何其他文件，系统自动发现、注册、构建 capability。

XiaomiMiMo adapter 已完整走新链路，但 MiniMax adapter 仍通过 `get_settings()` 读取 13+ 处配置。
需要统一为新架构，让所有 adapter 共享同一配置消费路径。

## 目标状态

### 配置分工

| 层 | 位置 | 职责 |
|---|---|---|
| 密钥/环境 | `.env` / 环境变量 | API key 等敏感信息 |
| Provider 实例 | `config/providers.yaml` | 谁启用、用哪个 adapter、api_key_env、base_url override |
| Adapter 默认 | `config/adapters/*.yaml` | endpoints、models、capability、plugin.import_path |
| 应用基础设施 | `.env` / Settings | DATABASE_URL、STORAGE_DIR、LOG_LEVEL 等与 provider 无关的配置 |

### 迁移后 `.env.example`

```env
# === 应用基础设施 ===
APP_NAME=Voice Lab
APP_ENV=dev
DATABASE_URL=sqlite:///./voice_lab.db

# Storage
STORAGE_DIR=./storage
DEFAULT_AUDIO_FORMAT=mp3
DEFAULT_SAMPLE_RATE=32000
DEFAULT_BITRATE=128000
DEFAULT_CHANNEL=1

# Batch
BATCH_MAX_CONCURRENCY=1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIR=./logs
LOG_RETENTION_DAYS=30

# Retry
PROVIDER_RETRY_MAX_ATTEMPTS=3
PROVIDER_RETRY_BACKOFF_BASE=1.0

# === Provider API Keys（密钥走环境变量，配置走 YAML）===
MINIMAX_API_KEY=replace_me
# MIMO_API_KEY=replace_me

# === 可选：自定义配置路径 ===
# VOICE_LAB_PROVIDER_CONFIG_PATH=./config/providers.yaml
# VOICE_LAB_ADAPTER_CONFIG_DIR=./config/adapters
# VOICE_LAB_ENV_FILE=./.env.local
```

### 废弃的 env vars（从 Settings 和 .env.example 中移除）

```
VOICE_PROVIDER
MINIMAX_BASE_URL
MINIMAX_T2A_PATH
MINIMAX_ASYNC_T2A_PATH
MINIMAX_ASYNC_QUERY_PATH
MINIMAX_FILE_UPLOAD_PATH
MINIMAX_VOICE_CLONE_PATH
MINIMAX_VOICE_DESIGN_PATH
MINIMAX_DELETE_VOICE_PATH
MINIMAX_DEFAULT_MODEL
MINIMAX_TIMEOUT_SECONDS
MINIMAX_WS_URL
MINIMAX_WS_MODEL
MINIMAX_WS_TIMEOUT_SECONDS
CLONE_AUDIO_MAX_SIZE_MB
MOCK_FALLBACK_PROVIDER
```

---

## 核心设计：纯插件化注册

### 接入新 Adapter 的完整流程（目标态）

```
1. 编写 app/providers/my_new_adapter.py  (实现 SpeechProvider)
2. 编写 config/adapters/my_new.yaml       (声明 plugin.import_path + 能力)
3. 在 config/providers.yaml 添加 provider 实例条目
4. 完成。无需改任何注册代码。
```

### 需要消灭的硬编码注册点

| 文件 | 硬编码 | 处理 |
|------|--------|------|
| `app/providers/registry.py` | `PROVIDER_REGISTRY` dict + `_register_static_providers()` | **删除**，全走 config |
| `app/providers/capability_registry.py` | `_CAPABILITY_BUILDERS = {"mock": ..., "minimax": ...}` | **删除**，capability 全从 AdapterConfig 构建 |
| `app/providers/adapter_type_registry.py` | `_ensure_core_adapters_registered()` hardcoded mock/minimax | **删除**，全走 plugin discovery |
| `app/providers/minimax_capabilities.py` | `build_minimax_capability()` 整个函数 | **删除**，能力数据已在 `adapters/minimax.yaml` |
| `app/providers/mock_capabilities.py` | `MOCK_CAPABILITY` 硬编码对象 | **删除**，能力数据已在 `adapters/mock.yaml` |
| `app/providers/__init__.py` | 注释中的 legacy 说明 | 清理 |

### 消灭后的注册链路

```
系统启动 / 首次调用
  → adapter_type_registry.load_adapter_plugins_from_config()
  → 扫描 config/adapters/*.yaml
  → 每个 yaml 的 plugin.import_path → importlib 动态加载 class
  → register_adapter_type(adapter_type, class)
  → 完成

get_provider(name):
  → providers.yaml 查 name → adapter_type
  → ADAPTER_TYPE_REGISTRY[adapter_type] → class
  → class(provider_config, adapter_config) → instance

capability_registry:
  → providers.yaml 所有 enabled provider
  → 每个 provider 的 adapter_type → 加载对应 adapters/*.yaml
  → 纯配置合成 ProviderCapability（不需要 Python builder）
```

### Capability 纯配置构建

迁移后 `capability_registry.py` 不再需要 `_CAPABILITY_BUILDERS`。

所有 capability 数据来源：

| 字段 | 来源 |
|------|------|
| `tts.models` / `audio_formats` / `supports_*` | `adapters/*.yaml` → tts 段 |
| `tts.speed` / `vol` / `pitch` (NumericRange) | `adapters/*.yaml` → tts 段新增 |
| `batch.*` | `adapters/*.yaml` → batch 段 |
| `voice_clone.*` | `adapters/*.yaml` → voice_clone 段 |
| `voice_design.*` | `adapters/*.yaml` → voice_design 段 |
| `provider_voices.*` | `adapters/*.yaml` → provider_voices 段 |
| `enabled` toggle | `providers.yaml` → 各 capability enabled 字段 |
| `metadata` | 合并 adapters/*.yaml metadata + providers.yaml metadata |

#### AdapterConfig schema 需扩展的字段

当前 `adapters/minimax.yaml` 缺少的 capability 细节（目前只在 `minimax_capabilities.py` 中 hardcoded）：

```yaml
# config/adapters/minimax.yaml 需新增
tts:
  # 已有字段...
  speed:
    min: 0.5
    max: 2.0
  vol:
    min: 0.1
    max: 10.0
  pitch:
    min: -12
    max: 12

batch:
  # 已有字段...
  segment_strategies:
    - "auto"
    - "paragraph"
    - "sentence"
    - "line"
  max_segment_chars:
    min: 100
    max: 5000
  silence_between_ms:
    min: 0
    max: 3000
  supports_merge_audio: true
  supports_merge_subtitle: true

voice_clone:
  # 已有字段...
  voice_id:
    min_length: 8
    max_length: 256
    pattern: "^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
    hint: "至少 8 位，必须以字母开头，只能包含字母、数字、下划线和短横线"

voice_design:
  # 已有字段...
  voice_id:
    min_length: 8
    max_length: 256
    pattern: "^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
    hint: "至少 8 位，必须以字母开头，只能包含字母、数字、下划线和短横线"

# WebSocket 配置
websocket:
  url: "wss://api.minimaxi.com/ws/v1/t2a_v2"
  model: "speech-2.8-hd"
  timeout_seconds: 120

metadata:
  ws_model: "speech-2.8-hd"
  clone_audio_max_size_mb: 20
```

#### AdapterConfig Pydantic schema 需扩展

`app/domain/adapter_config.py` 需新增以下类型：

```python
class NumericRangeConfig(BaseModel):
    min: float
    max: float

class VoiceIdConfig(BaseModel):
    min_length: int = 8
    max_length: int = 256
    pattern: str | None = None
    hint: str | None = None

class WebSocketConfig(BaseModel):
    url: str | None = None
    model: str | None = None
    timeout_seconds: int = 120
```

并在已有 schema 中新增字段：

```python
class TTSCapabilityConfig(BaseModel):
    # 已有字段...
    speed: NumericRangeConfig | None = None
    vol: NumericRangeConfig | None = None
    pitch: NumericRangeConfig | None = None

class BatchCapabilityConfig(BaseModel):
    # 已有字段...
    segment_strategies: list[str] = Field(default_factory=list)
    max_segment_chars: NumericRangeConfig | None = None
    silence_between_ms: NumericRangeConfig | None = None
    supports_merge_audio: bool = False
    supports_merge_subtitle: bool = False

class VoiceCloneCapabilityConfig(BaseModel):
    # 已有字段...
    voice_id: VoiceIdConfig | None = None

class VoiceDesignCapabilityConfig(BaseModel):
    # 已有字段...
    voice_id: VoiceIdConfig | None = None

class AdapterConfig(BaseModel):
    # 已有字段...
    websocket: WebSocketConfig | None = None
```

---

## 步骤 1：统一 Adapter 构造函数签名

### 目标

所有 adapter 接收 `ProviderConfig` + `AdapterConfig`，不再使用 `get_settings()`。

### SpeechProvider base class 修改

文件：`app/providers/base.py`

```python
class SpeechProvider(ABC):
    provider_name: str

    def __init__(
        self,
        provider_config: "ProviderConfig | None" = None,
        adapter_config: "AdapterConfig | None" = None,
    ) -> None:
        if provider_config:
            self.provider_name = provider_config.name
        self._provider_config = provider_config
        self._adapter_config = adapter_config
```

### 约束

- `provider_name` 从 `provider_config.name` 取（instance attribute 优先于 class attribute）
- `_provider_config` 和 `_adapter_config` 为 protected，供子类使用
- 保留 `provider_config=None` 兼容测试中的无参构造

---

## 步骤 2：`get_provider()` 注入配置

### 目标

`registry.py` 的 `get_provider()` 传入 `ProviderConfig` + `AdapterConfig` 给 adapter。

文件：`app/providers/registry.py`

```python
def get_provider(name: str) -> SpeechProvider:
    config = get_provider_config(name)
    if config:
        if not config.enabled:
            raise UnsupportedProvider(f"Provider {name} is not enabled", name)
        adapter_cls = get_adapter_type_adapter(config.adapter_type)
        adapter_config = get_adapter_config(config.adapter_type)
        return adapter_cls(provider_config=config, adapter_config=adapter_config)

    # Fallback (backward compatibility)
    cls = PROVIDER_REGISTRY.get(name)
    if cls:
        return cls()
    raise UnsupportedProvider(f"Unsupported provider: {name}", name)
```

---

## 步骤 3：迁移 MiniMaxSpeechAdapter

### 目标

将 `minimax_speech_adapter.py` 中所有 `get_settings()` 调用替换为从 `self._provider_config` / `self._adapter_config` 读取。

### 配置读取映射

| 旧（Settings） | 新（来源） |
|---|---|
| `settings.minimax_api_key` | `self._provider_config.resolved_api_key` |
| `settings.minimax_base_url` | `self._provider_config.resolved_base_url` 或 `self._adapter_config.default_base_url` |
| `settings.minimax_t2a_path` | `self._adapter_config.endpoints.t2a` |
| `settings.minimax_async_t2a_path` | `self._adapter_config.endpoints.t2a_async` |
| `settings.minimax_async_query_path` | `self._adapter_config.endpoints.query_async` |
| `settings.minimax_file_upload_path` | `self._adapter_config.endpoints.file_upload` |
| `settings.minimax_voice_clone_path` | `self._adapter_config.endpoints.voice_clone` |
| `settings.minimax_voice_design_path` | `self._adapter_config.endpoints.voice_design` |
| `settings.minimax_delete_voice_path` | `self._adapter_config.endpoints.delete_voice` |
| `settings.minimax_default_model` | `self._adapter_config.default_model` |
| `settings.minimax_timeout_seconds` | `self._adapter_config.default_timeout_seconds` |
| `settings.minimax_ws_url` | `self._adapter_config.metadata.get("ws_url")` 或 adapters/minimax.yaml 新增字段 |
| `settings.minimax_ws_model` | `self._adapter_config.metadata.get("ws_model")` |
| `settings.minimax_ws_timeout_seconds` | `self._adapter_config.default_timeout_seconds` |
| `settings.clone_audio_max_size_mb` | `self._adapter_config.voice_clone.max_file_size_mb` |

### 辅助方法建议

在 adapter 中新增 helper：

```python
@property
def _base_url(self) -> str:
    if self._provider_config and self._provider_config.resolved_base_url:
        return self._provider_config.resolved_base_url.rstrip("/")
    if self._adapter_config and self._adapter_config.default_base_url:
        return self._adapter_config.default_base_url.rstrip("/")
    return "https://api.minimaxi.com"  # hardcoded fallback

@property
def _api_key(self) -> str:
    if self._provider_config:
        key = self._provider_config.resolved_api_key
        if key:
            return key
    raise ProviderNotConfigured("MINIMAX_API_KEY not set")

def _endpoint(self, name: str) -> str:
    if self._adapter_config and self._adapter_config.endpoints:
        val = getattr(self._adapter_config.endpoints, name, None)
        if val:
            return val
    # fallback to provider config endpoints
    if self._provider_config and self._provider_config.endpoints:
        val = getattr(self._provider_config.endpoints, name, None)
        if val:
            return val
    raise ProviderError(f"Endpoint '{name}' not configured")
```

### adapters/minimax.yaml 需新增字段

```yaml
# WebSocket 配置（当前在 Settings 中）
metadata:
  ws_url: "wss://api.minimaxi.com/ws/v1/t2a_v2"
  ws_model: "speech-2.8-hd"
  ws_timeout_seconds: 120
  clone_audio_max_size_mb: 20
```

或者更好的方式是在 AdapterConfig schema 新增 `websocket` 配置块（如果 WS 是 minimax 特有的，放 metadata 即可）。

---

## 步骤 4：迁移 MockSpeechAdapter

### 目标

Mock adapter 构造函数接收 `provider_config` + `adapter_config`，保持功能不变。

文件：`app/providers/mock_speech_adapter.py`

Mock adapter 较简单，大部分不依赖外部配置。主要改动：
- 构造函数调用 `super().__init__(provider_config, adapter_config)`
- `provider_name` 从 config 取（如果传了 config）

---

## 步骤 5：精简 Settings 类

### 目标

`app/core/config.py` 只保留与 provider 无关的应用基础设施配置。

### 保留字段

```python
class Settings(BaseSettings):
    app_name: str = "Voice Lab"
    app_env: str = "dev"
    database_url: str = "sqlite:///./voice_lab.db"

    storage_dir: str = "./storage"
    default_audio_format: str = "mp3"
    default_sample_rate: int = 32000
    default_bitrate: int = 128000
    default_channel: int = 1

    batch_max_concurrency: int = 5

    log_level: str = "INFO"
    log_format: str = "json"
    log_dir: str = "./logs"
    log_retention_days: int = 30

    provider_retry_max_attempts: int = 3
    provider_retry_backoff_base: float = 1.0
```

### 移除字段

所有 `minimax_*`、`voice_provider`、`mock_fallback_provider`、`async_poll_interval_seconds`、`async_max_wait_seconds`、`clone_audio_max_size_mb`。

### 受影响的非 adapter 调用点

需要检查 `get_settings()` 的非 adapter 调用：

| 文件 | 用途 | 处理 |
|---|---|---|
| `app/core/database.py:57` | `model=get_settings().minimax_default_model` 用于 seed_defaults | 改为从 providers.yaml 读 |
| `app/services/async_render_service.py` | `async_poll_interval_seconds`、`async_max_wait_seconds` | 移到 adapters/minimax.yaml metadata 或保留在 Settings（async 轮询是基础设施行为） |
| `app/services/batch_orchestration_service.py` | `batch_max_concurrency` | 保留在 Settings |
| `app/services/capability_validator.py` | `voice_provider` 默认 provider | 废弃，改为从前端传入或从 providers.yaml 取第一个 enabled |
| `app/api/voice_clone.py` | `clone_audio_max_size_mb` | 改为从 adapter_config 读 |

---

## 步骤 6：废弃 `VOICE_PROVIDER` 语义

### 目标

不再通过 env var 决定默认 provider。

### 处理

- `capability_validator.py` 中的 `get_settings().voice_provider` 改为从 `providers.yaml` 中取第一个 `enabled=true` 且 `real_cost=false` 的 provider（安全默认），或者要求前端每次请求必须传 `provider` 参数
- 如果前端已经在请求中传 `provider`，直接移除这个默认逻辑

---

## 步骤 7：更新 `.env.example`

按照上面「目标状态」中的模板重写。

---

## 步骤 8：更新文档

### 需要更新的文档

| 文档 | 操作 |
|---|---|
| `docs/P16_DYNAMIC_PROVIDER_CONFIG_A0.md` | 末尾标注"已完成迁移" |
| `docs/P16_ADAPTER_PLUGIN_CONFIG_A0.md` | 末尾标注"已完成迁移" |
| `docs/PROJECT_HEALTH_CHECK.md` | 新增 P16-CONFIG-DRIVEN-MIGRATION 阶段记录 |
| `docs/ARCHITECTURE.md` | 更新配置架构段落 |
| `CLAUDE.md` | 移除"禁止事项"中关于 Provider Adapter 的限制（如果迁移完成） |

### 需要归档的文档

以下文档记录的是已完成的中间设计过程，迁移完成后归档：

| 文档 | 归档理由 |
|---|---|
| `docs/P16_DYNAMIC_PROVIDER_CONFIG_B1.md` | B1 已实现 |
| `docs/P16_DYNAMIC_PROVIDER_CONFIG_B1_CHECK.md` | 复核已完成 |
| `docs/P16_DYNAMIC_PROVIDER_CONFIG_B1_CLOSE.md` | 收口已完成 |
| `docs/P16_ADAPTER_PLUGIN_CONFIG_B1.md` | B1 已实现 |
| `docs/P16_ADAPTER_PLUGIN_CONFIG_B1_CHECK_FIX1.md` | 修复已完成 |
| `docs/P16_ADAPTER_PLUGIN_CONFIG_B1_CLOSE.md` | 收口已完成 |
| `docs/P16_ADAPTER_PLUGIN_DISCOVERY_B1.md` | 已实现 |
| `docs/P16_ADAPTER_PLUGIN_DISCOVERY_B1_CHECK_FIX1.md` | 已修复 |

归档方式：移到 `docs/archive/p16_config_driven/` 目录。

---

## 验证标准

### 功能验证

1. `python -m pytest tests/ -q` 全部通过
2. MiniMax adapter 通过 config 读取 base_url/endpoints/model（不再用 Settings）
3. XiaomiMiMo adapter 行为不变
4. Mock adapter 行为不变
5. `/api/voice/capabilities` 返回正确
6. `.env` 中只保留密钥 + 基础设施
7. 移除任何 `minimax_*` env var 后，MiniMax adapter 仍然正常工作（配置来自 YAML）
8. 保留 `MINIMAX_API_KEY` env var 后，adapter 能正常鉴权

### 回归验证

1. 前端 E2E 全量通过
2. `get_provider("mock")` / `get_provider("minimax")` / `get_provider("mock_configured")` 正常
3. CostGuard 对 minimax 仍触发确认
4. 批量任务 concurrency 仍受 `BATCH_MAX_CONCURRENCY` 控制

---

## 子任务拆分

| 子任务 | 内容 | 风险 |
|--------|------|------|
| M1 | AdapterConfig schema 扩展（NumericRange/VoiceId/WebSocket/batch 细节字段） | 低 |
| M2 | `adapters/minimax.yaml` + `adapters/mock.yaml` 补全所有 capability 细节 | 低 |
| M3 | SpeechProvider base 构造函数 + `get_provider()` 注入 config + Mock adapter 适配 | 低 |
| M4 | MiniMax adapter 迁移（13 处 get_settings 替换为 config） | 中 |
| M5 | capability_registry 纯配置化（删除 `_CAPABILITY_BUILDERS` + `minimax_capabilities.py` + `mock_capabilities.py`） | 中 |
| M6 | 删除硬编码注册（`PROVIDER_REGISTRY` + `_register_static_providers` + `_ensure_core_adapters_registered`） | 中 |
| M7 | Settings 精简 + 非 adapter 调用点修复 | 中 |
| M8 | `.env.example` 重写 + `VOICE_PROVIDER` 废弃 | 低 |
| M9 | 文档归档 + ARCHITECTURE / CLAUDE.md 更新 | 低 |

### 执行顺序

```
M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9
```

每步一个 commit。每步完成后跑 `python -m pytest tests/ -q` 确认全量通过。

### 各子任务详细说明

#### M1：AdapterConfig schema 扩展

文件：`app/domain/adapter_config.py`

新增 Pydantic models：
- `NumericRangeConfig(min, max)`
- `VoiceIdConfig(min_length, max_length, pattern, hint)`
- `WebSocketConfig(url, model, timeout_seconds)`

扩展已有 models：
- `TTSCapabilityConfig` 新增 `speed` / `vol` / `pitch` (NumericRangeConfig | None)
- `BatchCapabilityConfig` 新增 `segment_strategies` / `max_segment_chars` / `silence_between_ms` / `supports_merge_audio` / `supports_merge_subtitle`
- `ScriptCapabilityConfig` 新增同 batch 的字段
- `VoiceCloneCapabilityConfig` 新增 `voice_id` (VoiceIdConfig | None)
- `VoiceDesignCapabilityConfig` 新增 `voice_id` (VoiceIdConfig | None)
- `AdapterConfig` 新增 `websocket` (WebSocketConfig | None)

验证：已有 adapter config loader 测试通过 + 新增 schema 校验测试。

#### M2：补全 adapters/*.yaml

文件：`config/adapters/minimax.yaml` / `config/adapters/mock.yaml`

将 `minimax_capabilities.py` 和 `mock_capabilities.py` 中的所有 hardcoded 值
搬到 YAML。包括：speed/vol/pitch range、batch segment_strategies、
voice_id constraint、websocket 配置等。

验证：YAML 能被 AdapterConfig schema 正确加载。

#### M3：统一构造函数 + get_provider 注入

文件：
- `app/providers/base.py` — 基类新增 `__init__(provider_config, adapter_config)`
- `app/providers/registry.py` — `get_provider()` 传入两个 config
- `app/providers/mock_speech_adapter.py` — 构造函数适配

验证：`get_provider("mock")` / `get_provider("mock_configured")` 正常。

#### M4：MiniMax adapter 迁移

文件：`app/providers/minimax_speech_adapter.py`

13+ 处 `get_settings()` 替换为从 `self._provider_config` / `self._adapter_config` 读取。
详见上方「步骤 3：迁移 MiniMaxSpeechAdapter」的映射表。

验证：MiniMax adapter 不再 import `get_settings`。全量测试通过。

#### M5：capability_registry 纯配置化

文件：
- `app/providers/capability_registry.py` — 重写 `_build_capability_from_config()`，纯从 AdapterConfig 构建 ProviderCapability
- 删除 `app/providers/minimax_capabilities.py`
- 删除 `app/providers/mock_capabilities.py`（或保留为空模块避免 import 失败）

关键：`_build_capability_from_config()` 中的 NumericRange / VoiceIdConstraint 等对象
需要从 AdapterConfig 的 `NumericRangeConfig` / `VoiceIdConfig` 转换为
`capabilities.py` 中的 `NumericRange` / `VoiceIdConstraint`。

验证：`/api/voice/capabilities` 返回与迁移前完全一致的 JSON 结构。

#### M6：删除硬编码注册

文件：
- `app/providers/registry.py` — 删除 `PROVIDER_REGISTRY` dict / `_register_static_providers()`
- `app/providers/adapter_type_registry.py` — 删除 `_ensure_core_adapters_registered()`
- `app/providers/__init__.py` — 清理 legacy 注释

`get_provider()` 简化为：

```python
def get_provider(name: str) -> SpeechProvider:
    config = get_provider_config(name)
    if not config:
        raise UnsupportedProvider(f"Unknown provider: {name}", name)
    if not config.enabled:
        raise UnsupportedProvider(f"Provider {name} is not enabled", name)
    adapter_cls = get_adapter_type_adapter(config.adapter_type)
    adapter_config = get_adapter_config(config.adapter_type)
    return adapter_cls(provider_config=config, adapter_config=adapter_config)
```

无 fallback。全走配置。

验证：所有现有测试通过。`get_provider("不存在")` 抛 UnsupportedProvider。

#### M7：Settings 精简

文件：`app/core/config.py`

移除所有 `minimax_*` 字段、`voice_provider`、`mock_fallback_provider`、
`async_poll_interval_seconds`、`async_max_wait_seconds`、`clone_audio_max_size_mb`。

修复非 adapter 调用点：
- `database.py` seed_defaults — 从 providers.yaml 读 default_model
- `capability_validator.py` — 废弃 voice_provider
- `voice_clone.py` — 从 adapter_config 读 max_file_size
- `async_render_service.py` — poll_interval / max_wait 移到 adapter metadata 或保留 Settings

验证：Settings 类中无 `minimax` 关键字。全量测试通过。

#### M8：.env.example 重写

文件：`.env.example`

精简为：应用基础设施 + Provider API Keys。
详见上方目标状态模板。

验证：删除所有 `MINIMAX_*` env var（保留 `MINIMAX_API_KEY`），应用正常启动。

#### M9：文档归档

操作：
1. 创建 `docs/archive/p16_config_driven/`
2. 移入已完成的中间过程文档
3. 更新 `docs/PROJECT_HEALTH_CHECK.md`
4. 更新 `docs/ARCHITECTURE.md` 配置架构段落
5. 更新 `CLAUDE.md` 移除过时的禁止事项

---

## 明确不做

- 不改 `RenderPlan` schema
- 不改 `VoiceBinding` / `ProviderVoice` schema
- 不改 `resolve_binding` 逻辑
- 不接新 provider
- 不做配置热更新
- 不做管理 UI
- 不改前端（除非 `VOICE_PROVIDER` 废弃影响了前端逻辑）

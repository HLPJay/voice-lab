# P16-XIAOMI-MIMO-TTS-B1-CHECK-FIX1：验证并修复 Xiaomi MiMo Chat TTS 配置化边界

## 1. 阶段目标

复核 P16-XIAOMI-MIMO-TTS-B1 中发现的配置化边界问题，确保 Xiaomi MiMo adapter 真正基于 ProviderConfig + AdapterConfig 运行，而不是依赖硬编码常量。

## 2. 发现的问题

### 问题 1：api_key 读取硬编码

**原实现**：
```python
def _get_api_key(self) -> str:
    api_key = os.environ.get("MIMO_API_KEY")  # 硬编码环境变量名
    if not api_key or api_key == "replace_me":
        raise ProviderNotConfigured(...)
    return api_key
```

**修复后**：
```python
def _get_api_key(self) -> str:
    provider_config = self._get_provider_config()
    api_key = provider_config.resolved_api_key  # 通过 ProviderConfig.api_key_env 解析
    if not api_key or api_key == "replace_me":
        env_name = provider_config.api_key_env or "MIMO_API_KEY"
        raise ProviderNotConfigured(...)
    return api_key
```

**配置层级**：
1. `ProviderConfig.api_key_env` → 环境变量名
2. `resolve_env_value(api_key_env)` → 实际 key（支持 os.environ + .env 文件）

### 问题 2：base_url 硬编码

**原实现**：
```python
DEFAULT_BASE_URL = "https://api.xiaomimimo.com"

def _get_base_url(self) -> str:
    return os.environ.get("XIAOMI_MIMO_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
```

**修复后**：
```python
def _get_base_url(self) -> str:
    provider_config = self._get_provider_config()
    adapter_config = self._get_adapter_config()

    # 1. ProviderConfig.resolved_base_url (优先)
    if provider_config is not None:
        base_url = provider_config.resolved_base_url
        if base_url:
            return base_url.rstrip("/")

    # 2. AdapterConfig.default_base_url
    if adapter_config is not None and adapter_config.default_base_url:
        return adapter_config.default_base_url.rstrip("/")

    # 3. 硬编码 fallback
    return _FALLBACK_BASE_URL.rstrip("/")
```

**配置层级**：
1. `ProviderConfig.resolved_base_url`（来自 `base_url_env` 或 `base_url`）
2. `AdapterConfig.default_base_url`
3. 硬编码 fallback

### 问题 3：endpoint / model / timeout 硬编码

**原实现**：
```python
response = await self._request("POST", "/v1/chat/completions", json=payload)  # 硬编码 endpoint
model = plan.model or DEFAULT_MODEL  # 硬编码 model
request_timeout = timeout or DEFAULT_TIMEOUT_SECONDS  # 硬编码 timeout
```

**修复后**：
```python
# _get_endpoint() 配置层级
def _get_endpoint(self) -> str:
    # 1. ProviderConfig.endpoints.tts
    # 2. AdapterConfig.endpoints.tts
    # 3. 硬编码 fallback

# _get_model(plan) 配置层级
def _get_model(self, plan: RenderPlan) -> str:
    # 1. plan.model
    # 2. ProviderConfig.default_model
    # 3. AdapterConfig.default_model
    # 4. 硬编码 fallback

# _get_timeout() 配置层级
def _get_timeout(self) -> int:
    # 1. AdapterConfig.default_timeout_seconds
    # 2. 硬编码 fallback
```

### 问题 4：静态音色列表硬编码

**原实现**：
```python
async def list_voices(self, voice_type: str = "all") -> list[ProviderVoiceRead]:
    preset_voices = [
        {"id": "mimo_default", "name": "MiMo-默认", ...},
        {"id": "冰糖", "name": "冰糖", ...},
        # ... 9 个硬编码音色
    ]
```

**修复后**：
```python
async def list_voices(self, voice_type: str = "all") -> list[ProviderVoiceRead]:
    adapter_config = self._get_adapter_config()

    # 配置层级：优先使用 AdapterConfig.provider_voices.static_voices
    if adapter_config is not None and adapter_config.provider_voices is not None:
        static_voices = adapter_config.provider_voices.static_voices
        if static_voices:
            preset_voices = [
                {"voice_id": v.voice_id, "name": v.name, ...}
                for v in static_voices
            ]
        else:
            preset_voices = default_preset_voices
    else:
        preset_voices = default_preset_voices
```

## 3. 新增文件

| 文件 | 用途 |
|---|---|
| `app/config/env_resolver.py` | 环境变量解析器，支持 os.environ + .env 文件 fallback |

## 4. 修改文件

| 文件 | 改动 |
|---|---|
| `app/domain/provider_config.py` | `EndpointConfig` 增加 `tts` 字段；`resolved_api_key`/`resolved_base_url` 使用 `resolve_env_value` |
| `app/domain/adapter_config.py` | `EndpointConfig` 增加 `tts` 字段；新增 `StaticVoiceConfig`；`ProviderVoicesCapabilityConfig` 增加 `static_voices` |
| `app/providers/xiaomi_mimo_chat_tts_adapter.py` | 完全配置化：api_key/base_url/endpoint/model/timeout/list_voices 全部通过 config 层级解析 |
| `config/adapters/xiaomi_mimo_chat_tts.yaml` | 增加 `static_voices` 列表；`endpoints.tts` |
| `config/providers.yaml` | xiaomi_mimo 增加 `base_url_env: "XIAOMI_MIMO_BASE_URL"` 和 `endpoints.tts` |
| `tests/test_xiaomi_mimo_chat_tts_adapter.py` | 新增 14 个配置化行为测试 |

## 5. 配置变更

### 5.1 ProviderConfig（providers.yaml）

```yaml
- name: "xiaomi_mimo"
  api_key_env: "MIMO_API_KEY"
  base_url_env: "XIAOMI_MIMO_BASE_URL"  # 新增
  endpoints:
    tts: "/v1/chat/completions"          # 新增
  default_model: "mimo-v2.5-tts"
```

### 5.2 AdapterConfig（xiaomi_mimo_chat_tts.yaml）

```yaml
endpoints:
  tts: "/v1/chat/completions"

provider_voices:
  static_voices:
    - voice_id: "mimo_default"
      name: "MiMo-默认"
      language: "zh"
      gender: "neutral"
      description: "默认音色"
    - voice_id: "冰糖"
      name: "冰糖"
      language: "zh"
      gender: "female"
      description: "中文女性音色"
    # ... 共 9 个预置音色
```

## 6. 架构决策

### 6.1 为什么需要 env_resolver.py？

ProviderConfig 已经有 `api_key_env` 和 `base_url_env` 字段，但 `resolved_api_key` 和 `resolved_base_url` 直接使用 `os.environ.get()`。这有两个问题：

1. **不兼容 .env 文件**：某些部署使用 .env 文件而不是直接在环境中设置变量
2. **不一致性**：如果将来 .env 支持成为标准，每个 resolver 都需修改

`resolve_env_value(env_name)` 的实现：
```python
def resolve_env_value(env_name: str) -> str | None:
    # 1. 优先检查 os.environ
    value = os.environ.get(env_name)
    if value is not None:
        return value
    # 2. fallback 到 .env 文件
    env_file = _load_env_file()
    return env_file.get(env_name)
```

### 6.2 为什么需要 `tts` 字段在 EndpointConfig？

MiniMax adapter 的 endpoint 字段是 `t2a`（text-to-audio），但 Xiaomi MiMo 使用 `/v1/chat/completions`。原设计中 `EndpointConfig` 没有 `tts` 字段，只有 `t2a`。

新增 `tts: str | None = None` 到两个 `EndpointConfig` 类：
- `app/domain/provider_config.py`
- `app/domain/adapter_config.py`

### 6.3 为什么 static_voices 在 ProviderVoicesCapabilityConfig？

设计目标是：
- `AdapterConfig.provider_voices.static_voices` 定义预置音色列表
- `XiaomiMiMoChatTTSAdapter.list_voices()` 优先从配置读取，无配置则用硬编码 fallback
- 未来可以通过配置文件更新音色列表，无需修改代码

## 7. 测试结果

| 测试套件 | 结果 |
|---|---|
| test_xiaomi_mimo_chat_tts_adapter.py | 46 passed ✅ |
| test_adapter_plugin_discovery.py | 44 passed ✅ |
| test_adapter_config_loader.py | 51 passed ✅ |
| test_provider_config_dynamic.py | 47 passed ✅ |
| test_capabilities.py | 43 passed ✅ |
| test_cost_guard.py | 40 passed ✅ |
| **Adapter 相关总计** | **264 passed** |

### 新增测试覆盖

- `TestConfigDrivenBehavior`（12 tests）：验证 base_url/endpoint/model/timeout/api_key/list_voices 配置层级
- `TestEnvResolverDotEnvFallback`（2 tests）：验证 env_resolver 行为

## 8. 剩余风险

**无阻塞风险**。

**非阻塞观察项**：
- `.env` 文件解析在 Windows 上可能有 GBK 编码问题（现有 .env 文件含中文），测试时使用 UTF-8 编码可避免
- 真实 API 调用未测试（需要真实 MIMO_API_KEY）
- voice design / voice clone 语义映射待 P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 分析

## 9. 下一阶段建议

### 推荐：P16-XIAOMI-MIMO-TTS-B1-CHECK

**目标**：集成测试（需要真实或 mock MIMO_API_KEY）

**验证内容**：
- `get_provider("xiaomi_mimo")` 在 enabled=true 时返回 `XiaomiMiMoChatTTSAdapter` 实例
- 端到端 render_sync 测试

### 备选

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 | 分析 MiMo voicedesign 语义映射 | B1-CHECK 后 |
| P16-XIAOMI-MIMO-TTS-VOICE-CLONE-A0 | 分析 MiMo voiceclone 语义映射 | B1-CHECK 后 |
| P16-OPENAI-COMPATIBLE-TTS-A0 | 设计通用 OpenAI-compatible TTS adapter | 可后置 |

## 10. 明确未做

- **未实现真实的 voice design / voice clone** — 仅结构支持
- **未修改其他 adapter** — 仅修复 Xiaomi MiMo 的配置化边界
- **未修改 ProviderConfig schema** — 仅添加 `tts` 到 EndpointConfig
- **未改 RenderPlan / VoiceBinding / ProviderVoice / VoiceProfile schema**
- **未做 UI 改造**

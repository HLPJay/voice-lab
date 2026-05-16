# P16-DYNAMIC-PROVIDER-CONFIG-B1：Provider 配置化接入实现

## 1. 阶段目标

实现 Provider 配置化接入最小闭环，使新增 provider instance 可以通过 `config/providers.yaml` 接入。

验证：`mock_configured` provider 使用 `adapter_type=mock`，不接 OpenAI，不调用真实外部 API。

## 2. 实现内容

### 2.1 新增文件

| 文件 | 用途 |
|---|---|
| `config/providers.yaml` | Provider 配置文件，包含 mock、minimax、mock_configured |
| `app/domain/provider_config.py` | ProviderConfig Pydantic schema |
| `app/config/__init__.py` | config 包初始化 |
| `app/config/provider_config_loader.py` | YAML 配置加载器 |
| `app/providers/adapter_type_registry.py` | adapter_type -> Adapter class 注册表 |
| `app/providers/__init__.py` | 核心 adapter type 注册 |
| `tests/test_provider_config_dynamic.py` | 配置化 provider 测试（35 项） |

### 2.2 修改文件

| 文件 | 改动 |
|---|---|
| `app/providers/registry.py` | `get_provider()` 改为配置驱动路由 |
| `app/providers/capability_registry.py` | `_build_registry()` 从 YAML 配置读取 |
| `app/services/cost_guard_service.py` | 用 `ProviderConfig.real_cost` 替代 `COST_PROVIDER_SET` |

### 2.3 配置化路由链

```
get_provider("mock_configured")
  → get_provider_config("mock_configured")
    → ProviderConfig { name: "mock_configured", adapter_type: "mock" }
  → get_adapter_type_adapter("mock")
    → MockSpeechAdapter
```

### 2.4 Capability Registry 改造

`_build_registry()` 从 `list_enabled_provider_configs()` 读取配置，为每个 `adapter_type` 调用对应的 capability builder，返回的 `ProviderCapability.metadata` 包含：

```python
{
    "adapter_type": "mock",           # 来自 config
    "real_cost": False,               # 来自 config
    "configured_via_yaml": True,      # 新增标记
    # ... 原有 base capability metadata
}
```

`api_key`、`token`、`secret`、`password` 等敏感键值不会出现在 API 响应中。

### 2.5 Cost Guard 改造

`CostGuardService.require_confirmed()` 改为：

```python
config = get_provider_config(provider)
if config:
    if config.real_cost and operation in HIGH_RISK_OPERATIONS and not confirm_cost:
        raise ValidationError(...)
```

向后兼容：若 provider 不在配置中，回退到 `COST_PROVIDER_SET = {"minimax"}` 判断。

## 3. mock_configured 验证

### 3.1 配置

```yaml
name: "mock_configured"
adapter_type: "mock"
real_cost: false
```

### 3.2 验证结果

| 检查项 | 结果 |
|---|---|
| `get_provider("mock_configured")` 返回 `MockSpeechAdapter` | ✅ |
| `/api/voice/capabilities` 包含 `mock_configured` | ✅ |
| `mock_configured.metadata.adapter_type == "mock"` | ✅ |
| `mock_configured.metadata.real_cost == false` | ✅ |
| `mock_configured.metadata.configured_via_yaml == true` | ✅ |
| Cost Guard 对 `mock_configured` 不要求 confirm | ✅ |
| `get_provider("mock")` 仍返回 `MockSpeechAdapter` | ✅ |
| `get_provider("minimax")` 仍返回 `MiniMaxSpeechAdapter` | ✅ |

## 4. 测试结果

- 新增测试: 35 passed ✅
- Cost Guard 回归: 40 passed ✅
- Provider mock boundary 回归: 39 passed ✅
- Provider binding UI 回归: 50 passed ✅
- Capabilities API 回归: 43 passed ✅
- 全量静态测试: 1426 passed, 1 pre-existing failure (`test_safePushWorkspaceSample_writes_context_id_to_sample`)

## 5. 自检发现的问题

### 5.1 已知非阻塞问题

无

### 5.2 已知 pre-existing failure

`test_safePushWorkspaceSample_writes_context_id_to_sample`：safePushWorkspaceSample 缺少 `context_id` 字段，与本阶段无关。

## 6. 未纳入范围

- OpenAI / Azure / 火山 / 阿里云 实际接入
- 管理 UI（增删改 provider 配置）
- 运行时配置热更新
- Pricing metadata
- 前端 high-risk 确认改造（`provider === "minimax"` 硬编码）
- `COST_PROVIDER_SET` 完全移除（保留向后兼容 fallback）

## 7. B1 实现步骤回顾

1. ✅ 新增 `config/providers.yaml`
2. ✅ 新增 `app/domain/provider_config.py`
3. ✅ 新增 `app/config/provider_config_loader.py`
4. ✅ 新增 `app/providers/adapter_type_registry.py`
5. ✅ 修改 `app/providers/registry.py`（配置驱动路由）
6. ✅ 修改 `app/providers/capability_registry.py`（从 YAML 构建）
7. ✅ 修改 `app/services/cost_guard_service.py`（使用 real_cost）
8. ✅ 新增 `tests/test_provider_config_dynamic.py`
9. ✅ 端到端验证 `mock_configured`
10. ✅ 回归测试通过

## 8. 收口结论

Provider 配置化接入 B1 实现完成 ✅

- `mock_configured` 通过 YAML 配置接入
- 新增 provider 不需要改 Python 代码（只需要新的 adapter type 如果不支持）
- 现有 `mock`/`minimax` 链路完全向后兼容
- Cost Guard 从硬编码改为配置驱动

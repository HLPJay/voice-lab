# P16-DYNAMIC-PROVIDER-CONFIG-B1-CHECK：Provider 配置化接入实现复核

## 1. 复核结论

**通过，发现并修复 1 个边界问题** ✅

## 2. 复核范围

验证远端 commit `a444587` 的实现是否满足 B1 要求。

## 3. B1 要求核对

| 要求 | 状态 |
|---|---|
| `config/providers.yaml` 包含 mock/minimax/mock_configured | ✅ |
| `get_provider("mock_configured")` 返回 `MockSpeechAdapter` | ✅ |
| `/api/voice/capabilities` 包含 `mock_configured` | ✅ |
| `CostGuardService` 使用 `ProviderConfig.real_cost` | ✅ |
| mock/minimax 旧链路保持可用 | ✅ |
| 不调用真实外部 API | ✅ |

## 4. 发现并修复的问题

### 4.1 修复：disabled provider 未检查 enabled 状态

**问题**：`get_provider(name)` 在配置中找到 provider 时，未检查 `ProviderConfig.enabled` 是否为 `false`。当 `enabled=false` 时，仍返回 adapter 实例。

**修复**：`get_provider()` 增加 `enabled` 检查：

```python
config = get_provider_config(name)
if config:
    if not config.enabled:
        raise UnsupportedProvider(f"Provider {name} is not enabled", name)
    adapter_cls = get_adapter_type_adapter(config.adapter_type)
    return adapter_cls()
```

**影响**：仅修复边界，不影响已有逻辑。

### 4.2 发现：Cache 隔离

`provider_config_loader` 和 `capability_registry` 各自有独立缓存。测试时需要同时调用 `clear_provider_config_cache()` 和 `clear_capability_registry_cache()`。在测试中已显式体现，文档化提醒。

## 5. 补充测试

| 测试 | 描述 |
|---|---|
| `test_disabled_provider_excluded_from_enabled` | `list_enabled_provider_configs()` 不包含 `disabled_provider` |
| `test_disabled_provider_still_in_list_all` | `list_provider_configs()` 包含 `disabled_provider` |
| `test_get_provider_disabled_raises` | `get_provider("disabled_provider")` 抛 `UnsupportedProvider` |
| `test_disabled_provider_not_in_capabilities` | `list_capabilities()` 不包含 `disabled_provider` |
| `test_both_caches_need_clear` | 两个 cache 独立，需分别清理 |

## 6. 测试结果

- 新增/更新测试: 40 passed ✅
- Cost Guard 回归: 40 passed ✅
- Provider mock boundary 回归: 39 passed ✅
- Provider binding UI 回归: 50 passed ✅
- Capabilities API 回归: 43 passed ✅

## 7. 阻塞问题

无

## 8. 非阻塞观察项

无

## 9. 下一阶段

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-DYNAMIC-PROVIDER-CONFIG-B1-CLOSE | close provider config B1 implementation | B1-CHECK 完成 |
| P16-DYNAMIC-PROVIDER-CONFIG-B2 | additional provider config enhancements | B1-CLOSE 后评估 |
| P16-OPENAI-COMPATIBLE-TTS-A0 | design OpenAI-compatible TTS adapter | B1-CLOSE 后评估 |

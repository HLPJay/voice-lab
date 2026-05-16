# P16-DYNAMIC-PROVIDER-CONFIG-B1-CLOSE：Provider 配置化接入阶段收口

## 1. 阶段背景

Provider 配置化接入 B1 实现 + B1-CHECK 复核均已完成，现进行收口。

前置阶段：
- `P16-DYNAMIC-PROVIDER-CONFIG-A0`：Provider 配置化接入架构设计 ✅
- `P16-DYNAMIC-PROVIDER-CONFIG-B1`：Provider 配置化接入实现 ✅
- `P16-DYNAMIC-PROVIDER-CONFIG-B1-CHECK`：Provider 配置化接入实现复核 ✅

## 2. 已完成内容

### 2.1 新增文件

| 文件 | 用途 |
|---|---|
| `config/providers.yaml` | Provider 配置文件（mock, minimax, mock_configured, disabled_provider） |
| `app/domain/provider_config.py` | ProviderConfig Pydantic schema |
| `app/config/__init__.py` | config 包初始化 |
| `app/config/provider_config_loader.py` | YAML 配置加载器 |
| `app/providers/adapter_type_registry.py` | adapter_type -> Adapter class 注册表 |
| `app/providers/__init__.py` | 核心 adapter type 注册 |
| `tests/test_provider_config_dynamic.py` | 配置化 provider 测试（40 项） |

### 2.2 改造文件

| 文件 | 改动 |
|---|---|
| `app/providers/registry.py` | `get_provider()` 改为配置驱动路由，增加 enabled 检查 |
| `app/providers/capability_registry.py` | `_build_registry()` 从 YAML 配置读取 |
| `app/services/cost_guard_service.py` | 用 `ProviderConfig.real_cost` 替代 `COST_PROVIDER_SET` |

## 3. 发现的问题及处理

### 3.1 B1-CHECK 发现：disabled provider 未检查 enabled 状态

**问题**：`get_provider(name)` 在配置中找到 provider 时，未检查 `ProviderConfig.enabled` 是否为 `false`。

**处理**：增加 enabled 检查，抛出 `UnsupportedProvider`。

**状态**：已修复并测试覆盖。

### 3.2 发现：Cache 隔离

`provider_config_loader` 和 `capability_registry` 各自有独立缓存，测试时需要同时清理两个 cache。

**处理**：在测试中显式体现，文档化提醒。

**状态**：已文档化，非阻塞。

## 4. disabled_provider 决策

**决策**：保留 `disabled_provider` 在 `config/providers.yaml` 中。

**理由**：
- 作为 YAML 配置驱动的 disabled 边界验证用例，证明 `enabled=false` 时的行为符合预期
- 正式配置中有 disabled 条目符合实际部署场景（provider 需要临时禁用但保留配置的场景）
- 迁移到测试临时 YAML 会增加测试复杂度

## 5. 验证结果

| 检查项 | 结果 |
|---|---|
| `get_provider("mock_configured")` 返回 `MockSpeechAdapter` | ✅ |
| `/api/voice/capabilities` 包含 `mock_configured` | ✅ |
| `mock_configured.metadata.adapter_type == "mock"` | ✅ |
| `mock_configured.metadata.real_cost == false` | ✅ |
| Cost Guard 对 `mock_configured` 不要求 confirm | ✅ |
| `get_provider("disabled_provider")` 抛出 `UnsupportedProvider` | ✅ |
| `get_provider("mock")` 仍返回 `MockSpeechAdapter` | ✅ |
| `get_provider("minimax")` 仍返回 `MiniMaxSpeechAdapter` | ✅ |
| `list_capabilities()` 不包含 `disabled_provider` | ✅ |

## 6. 测试结果

- 新增/更新测试: 40 passed ✅
- Cost Guard 回归: 40 passed ✅
- Provider mock boundary 回归: 39 passed ✅
- Provider binding UI 回归: 50 passed ✅
- Capabilities API 回归: 43 passed ✅
- 全量静态测试: 1426 passed, 1 pre-existing failure

## 7. 剩余风险

无阻塞风险。

**非阻塞观察项**：
- Cache 隔离需要同时调用两个 clear 函数，测试中已显式处理
- `COST_PROVIDER_SET` 保留作为 fallback，向后兼容非 YAML 配置的 provider
- `disabled_provider` 保留在正式配置中，是有意的设计决策

## 8. 未进入范围

- OpenAI / Azure / 火山 / 阿里云 实际接入
- 管理 UI（增删改 provider 配置）
- 运行时配置热更新
- Pricing metadata
- 前端 high-risk 确认改造（`provider === "minimax"` 硬编码）
- `COST_PROVIDER_SET` 完全移除

## 9. 收口结论

Provider 配置化接入 B1 阶段完成 ✅

- `mock_configured` 通过 YAML 配置接入，不改 Python 代码
- `get_provider()` 由配置驱动，`enabled=false` 正确抛出异常
- `CostGuardService` 从硬编码改为配置驱动
- 向后兼容 `mock`/`minimax` 旧链路
- 全部测试通过

**下一阶段**：`NEXT-PRIORITY-REVIEW：下一阶段优先级确认`

# P16 D4 Issues Archive - 2026-05-17

## 1. 日期

2026-05-17

## 2. 当前分支

`p16/real-usage-issues`

---

## 3. 已处理问题清单

### D4-E0：Testing provider 隔离（Provider visibility filter）

- **commit**: `d0116e2`
- **问题**: testing_only 的 mock_configured provider 在正常 UI 中显示
- **处理**: `providers.yaml` 增加 `ui_visible/dev_only/testing_only` metadata；`capability_registry.py` 修复 metadata 传播；`provider_capabilities.js` 新增 `isDevMode()`/`isUiVisibleProvider()`/`getUiProviderCapabilities()` 过滤方法
- **状态**: 已完成

### D4-F0：Header provider/model 错配

- **commit**: `a3f762a`
- **问题**: 顶部状态栏可能显示 `xiaomi_mimo / speech-2.8-hd`（错误的 provider/model 组合）
- **根因**: `chipModel` 无条件使用 `data.current.default_model`（总是 MiniMax 的 speech-2.8-hd），不考虑当前页面选中的 provider
- **处理**: `runtime_status.js` 改为 provider-aware chipModel（`getDefaultTtsModel(currentProvider)`），providerSelect 切换后即时触发 `loadRuntimeStatus()`，监听 `provider-capabilities-applied` 事件；`runtime_status.py` 新增 `_get_auth_hint()` 动态 auth hint、`default_ws_model` 字段
- **状态**: 已完成

### D4-F1：用量 / 统计 / 官方账单口径误导

- **commit**: `740bc5e`
- **问题**: 首页 chipToday/chipMonth 和管理面板统计标签容易被误解为官方真实扣费额度
- **根因**: 首页 chip 文字无"本地"标识；管理面板 `总字符数` 等措辞暗示官方账单
- **处理**: 首页 chip 改为 `今日本地 N 字` / `本月本地 N 字` + 说明 title；管理面板 `总字符数` → `本地字符数`，调用次数加"本地"前缀，新增免责声明；cost guard warning 补充"不代表官方扣费"；URL provider filter 功能实装（banner + loadLogs/loadErrors 参数）
- **状态**: 已完成

### D4-F1A：Admin provider filter 首次加载顺序

- **commit**: `013c011`
- **问题**: `loadAll()` 早于 `applyFocusFromURL()` 执行，`?provider=xiaomi_mimo` 首次加载时 loadLogs/loadErrors 未带 provider 参数
- **根因**: 初始化顺序 `requestAnimationFrame(() => { loadAll(); applyFocusFromURL(); })` 中 `currentProviderFilter` 在 loadAll 时仍为 null
- **处理**: 调整为 `applyFocusFromURL()` 同步执行，`loadAll()` 延迟到 `requestAnimationFrame` 回调中
- **状态**: 已完成

### D4-F2：Full suite baseline triage 文档

- **commit**: `bcc9785`
- **问题**: full suite 57 个失败来源不清，不能直接合并 main
- **处理**: 创建 `docs/P16_FULL_SUITE_BASELINE_TRIAGE_D4_F2.md`，通过 git worktree 验证所有失败均为 pre-existing，明确分类和合并条件
- **状态**: 已完成

### D4-F3：Xiaomi MiMo ProviderCallLog 缺失 + StatsService AudioAsset-only 漏显示

- **commit**: 本任务（见下方）
- **问题 1**: Xiaomi MiMo Web 生成成功但管理面板 Provider 统计不显示 xiaomi_mimo
- **根因 1**: `XiaomiMiMoChatTTSAdapter._request()` 只写 logger，不写 `ProviderCallLog`；`duration_ms` 硬编码为 0
- **问题 2**: `StatsService.by_provider` 仅遍历 `ProviderCallLog`，无 call log 的 provider（只有 AudioAsset）不出现在统计
- **处理**: adapter 新增 `_save_call_log()`/`update_call_log()`，`_request()` 使用 `time.monotonic()` 记录真实耗时并写 ProviderCallLog，`render_sync()` 成功后回填 `usage_characters` 和 `provider_trace_id`；stats_service 补充 AudioAsset-only provider 合并逻辑
- **状态**: 已完成

### D4-F4：Voice preview 测试适配 provider 必填字段

- **commit**: 本任务（见下方）
- **问题**: `tests/test_voice_preview.py` 中 3 个独立测试未适配 `ProviderVoicePreviewRequest.provider` 已变为必填字段的当前 schema
- **处理**: API 请求体补充 `provider: "mock"`；两个 `ProviderVoicePreviewRequest(...)` 对象构造补充 `provider="minimax"`，保持原有断言不变
- **状态**: 已完成

---

## 4. 当前仍未处理问题

| 问题 | 计划任务 | 优先级 |
|------|----------|--------|
| `test_xiaomi_mimo_chat_tts_adapter.py` 4 个失败：旧断言 disabled/unsupported，与 V1 口径不符 | D4-F5 | 阻塞合并 |
| jsdom npm 包未安装，33 个静态 JS 测试失败（context_store / cancel_confirmation / workspace_restore） | D4-F6 / 环境 | 可延后 |
| Playwright E2E 4 个失败：UI 结构变化导致 locator 过期 | D4-F7 / E2E 专项 | 可延后 |
| full suite 测试顺序污染（11 个 voice clone/design/import 仅在全量套件中失败） | D4-F8 / 低优先级 | 可延后 |
| 官方账单同步（Provider 控制台余额、真实扣费） | V2 规划 | V2 |
| model-level stats（按模型细分用量） | V2 规划 | V2 |
| 日志保留周期 / 清理脚本 | V2 运维 | V2 |
| xiaomi_mimo 双前缀鉴权路由（sk- vs tp-） | V2 | V2 |

---

## 5. 当前 V1 边界

- **MiniMax 主链路**：单段同步 TTS、异步批处理、WebSocket 流式；V1 主能力，完整覆盖
- **Xiaomi MiMo**：V1 只承诺单段同步 TTS 样板（`render_sync`）；voice clone/design 实验性，暂不作为 V1 承诺
- **管理面板统计**：来自本地 `ProviderCallLog` + `AudioAsset` 数据，非 Provider 官方账单
- **ProviderCallLog**：轻量审计日志，只保存 provider/path/method/status/duration/error/usage/trace；不保存完整 request payload、response JSON、base64 audio、API key
- **不承诺**：官方余额同步、官方费用精算、SaaS 计费、model-level billing

---

## 6. 下一步建议

按优先顺序：

1. **D4-F5**：对齐 `test_xiaomi_mimo_chat_tts_adapter.py` 4 个旧测试口径（改为当前 V1 enabled 断言）— 阻塞合并
2. **D4-F6**：`npm install jsdom` 解锁 33 个 Node.js 静态 JS 测试 — 可延后
3. **D4-CLOSEOUT**：P16 V1 收口文档 + 合并 main
4. **V2 规划**：官方账单接入、model-level stats、日志清理策略

# Voice Lab 项目健康检查

## 1. 当前项目定位

Voice Lab 当前定位为：AI 声音资产管理与语音生成工作台。

当前系统已经从单纯 API Demo 逐步演进为具备以下能力的声音生产工作台：

- 声音人设管理
- Provider 音色资产管理
- 人设与音色绑定
- T2A 同步生成
- 异步生成
- WebSocket 流式生成
- 声音设计
- 声音克隆
- 音色导入
- 音色删除
- 批量长文本生成
- 多角色剧本生成
- 成本确认保护
- Provider 调用统计雏形

## 2. 当前已完成能力

### 2.1 声音资产与绑定

已完成：

- VoiceProfile 声音人设
- ProviderVoice Provider 音色资产
- VoiceBinding 人设与音色绑定
- ProviderVoice 本地缓存
- 远端 voice_id 导入本地
- 绑定创建时校验 provider_voice 是否存在且 available

### 2.2 Provider 能力

当前已经具备 Provider Adapter 基础。

当前已注册 Provider：

- mock
- minimax

当前尚未接入：

- mimo
- local_gpt_sovits
- local_cosyvoice
- aliyun
- volcengine
- elevenlabs

### 2.3 MiniMax 能力

当前 MiniMax Provider 已支持：

- T2A 同步生成
- 异步任务创建与查询
- WebSocket 流式生成
- 音色列表查询
- 声音克隆
- 声音设计
- 音色删除
- 文件上传
- Provider 调用日志

### 2.4 批量生成能力

已支持：

- 长文本分段生成
- 剧本多角色生成
- segment 级别状态记录
- success / partial / failed 状态
- 失败段重试
- 成功段复用
- 音频合并
- 字幕合并

## 3. 当前核心保护机制

### 3.1 删除音色生命周期闭环

当前已完成：

- 远端删除音色成功后，本地 provider_voices 标记为 deprecated
- 远端删除音色成功后，相关 voice_bindings 标记为 deprecated
- 删除失败时不更新本地状态
- 本地 provider_voice 不存在时不影响远端删除成功结果

### 3.2 生成前 ProviderVoice 状态校验

当前已完成：

- 同步生成前校验 provider_voice 是否存在
- 同步生成前校验 provider_voice.status 是否 available
- 异步生成前校验 provider_voice
- 流式生成前校验 provider_voice
- 批量 segment 生成前校验 provider_voice

该机制用于防止：

- 已删除音色继续被使用
- 脏数据绕过绑定状态
- 本地缺失 provider_voice 仍进入真实 provider 调用
- 无效 voice_id 请求打到云端模型

### 3.3 Cost Guard 第一版

当前已完成：

- 计费字符估算
- MiniMax T2A 费用估算
- /api/voice/cost/estimate 成本估算接口
- 高风险操作增加 confirm_cost
- MiniMax 声音设计未确认时拒绝
- MiniMax 声音克隆未确认时拒绝
- MiniMax 直连试听未确认时拒绝
- MiniMax 批量生成未确认时拒绝
- mock provider 不强制 confirm_cost
- 普通 T2A 暂不强制确认，但会记录成本估算日志

### 3.4 Provider 调用统计

当前已有：

- provider_call_logs
- usage_characters 字段
- provider_trace_id 字段
- StatsService 聚合统计

可统计：

- 总任务数
- 成功率
- 失败率
- 总字符数
- 按 provider 统计
- 按 API 统计
- 按天统计
- 平均耗时
- P95 耗时

## 4. 当前测试状态

### 4.1 全量测试

```bash
python -m pytest tests/ -x -q
```

测试结果：

```text
322 passed, 6 skipped in 171.42s (0:02:51)
```

- 总测试数量：328（322 passed + 6 skipped）
- 通过数量：322
- 跳过数量：6（均为 E2E 测试，需要真实 API Key）
- 失败数量：0

### 4.2 WebSocket 专项测试

```bash
python -m pytest tests/test_ws_render.py -q
```

测试结果：

```text
6 passed in 2.91s
```

### 4.3 历史遗留问题记录

**问题：WebSocket 端点无法通过测试 fixture 注入数据库会话**

- 发现时间：2026-05-12
- 根本原因：`ws_render.py` 使用 `session = next(get_session())` 绕过 FastAPI 的 `dependency_overrides` 机制，导致测试中 `ws_patched_session` fixture 无法替换为测试引擎会话
- 修复方案：将 `session = next(get_session())` 改为 FastAPI 依赖注入 `session: Session = Depends(get_session)`，让 FastAPI 的 `dependency_overrides` 在测试中生效
- 修改文件：`app/api/ws_render.py`
- 状态：**已修复并验证通过**

## 5. 当前试用准备度评估

当前项目可以：

- 本地演示
- 单人测试
- 验证 MiniMax 语音链路
- 验证声音资产生命周期
- 验证成本确认保护
- 验证批量生成流程

当前项目暂不适合直接开放多人试用。

主要原因：

- 前端仍是测试面板，不是产品工作台
- 缺少全局 Resource Guard
- 缺少 Provider / model / operation 级别并发控制
- 缺少预算预占与实际结算
- SQLite 对多人并发试用存在风险
- 默认 batch_max_concurrency 对试用阶段偏高
- Provider 差异抽象还不完整
- 手机端体验尚未产品化

## 6. 当前结论

Voice Lab 当前已经从 API Demo 进入声音工作台雏形阶段。

当前最应该做的是：

1. 固化项目状态
2. 整理产品主流程
3. 建立全局资源保护
4. 再接入低成本 Provider
5. 再做手机端 H5/PWA

不建议现在继续无序增加底层能力。

---

## 7. P6 前端测试面板基础验证

### 验证背景

- 当前分支：dev
- 当前阶段：P6 固化收尾
- 验证方式：人工前端页面基础测试
- 验证结论：暂未发现明显阻塞问题

### 验证范围

已基本测试以下页面或能力：

- T2A 生成（同步）
- T2A 生成（异步）
- T2A 生成（WebSocket 流式）
- 音色管理
- 声音克隆
- 声音设计
- 绑定管理
- 批量生成（长文本）
- 批量生成（剧本多角色）
- 管理面板入口

### 验证结果

- 页面可正常打开
- 基本交互可用
- 同步生成链路可用
- 异步生成链路可用（短文本异步模式明显慢于同步模式，属于异步链路正常特性）
- 流式生成链路可用
- 批量生成链路可用
- 暂未发现明显阻塞问题

### 观察项

- 当前前端仍是测试面板，不是最终产品主流程
- 异步生成依赖前端轮询推进状态，短文本建议优先使用同步生成或流式生成
- 批量长文本自动分段策略主要按双换行或超长文本拆分，单换行短文本可能仍被视为一段
- 后续进入 Resource Guard 前，应保留当前 P6 baseline

---

## 8. .env.example 与 Settings 配置同步

### 问题现象

- `app/core/config.py` 中已有 WebSocket、批量、日志、重试等配置项
- `.env.example` 未完整覆盖这些配置
- 这可能导致换机器、交接、部署或让代码执行器运行时出现配置遗漏

### 原因分析

- 项目功能从 P3 推进到 P6 后，新增了 WebSocket、批量任务、日志、重试等能力
- 但 `.env.example` 没有及时跟进 Settings 配置项变化
- 配置文档和代码存在漂移

### 修改方案

- 对照 `app/core/config.py` 中 Settings 类同步 `.env.example`
- 补充 WebSocket、Batch、Logging、Retry、Async Poll 等配置
- 将 `BATCH_MAX_CONCURRENCY` 示例值设为 1，作为试用阶段保守默认值
- 清理当前未使用的配置项（`ENABLE_MOCK_PROVIDER`、`CLONE_AUDIO_MIN_DURATION_SEC`、`CLONE_AUDIO_MAX_DURATION_SEC`、`PROMPT_AUDIO_MAX_DURATION_SEC`），移至注释区标注"未启用/保留说明"
- 保留 `MOCK_FALLBACK_PROVIDER`，该字段被 `voice_profile_repo.py` 实际使用

### 修改文件

- `.env.example`
- `docs/PROJECT_HEALTH_CHECK.md`

### 同步的配置项（按 Settings 字段对照）

| Settings 字段 | .env.example 配置 | 状态 |
|---|---|---|
| `async_poll_interval_seconds` | `ASYNC_POLL_INTERVAL_SECONDS=5` | 新增 |
| `async_max_wait_seconds` | `ASYNC_MAX_WAIT_SECONDS=600` | 新增 |
| `minimax_ws_url` | `MINIMAX_WS_URL=wss://api.minimaxi.com/ws/v1/t2a_v2` | 新增 |
| `minimax_ws_model` | `MINIMAX_WS_MODEL=speech-2.8-hd` | 新增 |
| `minimax_ws_timeout_seconds` | `MINIMAX_WS_TIMEOUT_SECONDS=120` | 新增 |
| `batch_max_concurrency` | `BATCH_MAX_CONCURRENCY=1` | 新增（从5改为1） |
| `log_level` | `LOG_LEVEL=INFO` | 新增 |
| `log_format` | `LOG_FORMAT=json` | 新增 |
| `log_dir` | `LOG_DIR=./logs` | 新增 |
| `log_retention_days` | `LOG_RETENTION_DAYS=30` | 新增 |
| `provider_retry_max_attempts` | `PROVIDER_RETRY_MAX_ATTEMPTS=3` | 新增 |
| `provider_retry_backoff_base` | `PROVIDER_RETRY_BACKOFF_BASE=1.0` | 新增 |
| `mock_fallback_provider` | `MOCK_FALLBACK_PROVIDER=minimax` | 新增 |
| `clone_audio_max_size_mb` | `CLONE_AUDIO_MAX_SIZE_MB=20` | 已有 |
| `minimax_file_upload_path` | `MINIMAX_FILE_UPLOAD_PATH=/v1/files/upload` | 已有 |
| `minimax_voice_clone_path` | `MINIMAX_VOICE_CLONE_PATH=/v1/voice_clone` | 已有 |
| `minimax_voice_design_path` | `MINIMAX_VOICE_DESIGN_PATH=/v1/voice_design` | 已有 |
| `minimax_delete_voice_path` | `MINIMAX_DELETE_VOICE_PATH=/v1/delete_voice` | 已有 |

### 清理的配置项

| 配置 | 原因 |
|---|---|
| `ENABLE_MOCK_PROVIDER=false` | 字段不存在于 Settings，代码无引用 |
| `CLONE_AUDIO_MIN_DURATION_SEC=10` | 字段不存在于 Settings，代码无引用 |
| `CLONE_AUDIO_MAX_DURATION_SEC=300` | 字段不存在于 Settings，代码无引用 |
| `PROMPT_AUDIO_MAX_DURATION_SEC=8` | 字段不存在于 Settings，代码无引用 |

### 后续注意

- 后续每次新增 Settings 配置项，都需要同步 `.env.example`
- 后续接入 Resource Guard 时，也需要同步相关环境变量示例
- 不应让 `.env.example` 长期落后于 `config.py`

---

## 9. 本次测试执行记录

### 全量测试

测试命令：

```bash
python -m pytest tests/ -x -q
```

测试输出：

```text
322 passed, 6 skipped in 171.42s (0:02:51)
```

测试结果摘要：

- 总测试数量：328（322 passed + 6 skipped）
- 通过数量：322
- 跳过数量：6（均为 E2E 测试，需要真实 API Key）
- 失败数量：0
- 第一个失败测试：无

---

## P7-A Resource Guard 第一版方案设计

### 背景

- P6 baseline 已于 2026-05-13 完成（tag: p6-dev-baseline-20260513）
- 项目当前具备多条真实 MiniMax 调用路径：同步T2A、异步T2A、WebSocket流式、声音设计、声音克隆、音色试听、多版本试音、批量生成
- 当前已有 Cost Guard（confirm_cost 检查），但缺少 Resource Guard（资源准入控制）
- 下一阶段需要先完成方案设计，确保实现受控，而不是直接写代码

### 本次工作

- 新增 `docs/P7_RESOURCE_GUARD_SPEC.md`
- 覆盖内容：定位与边界、operation类型定义、默认策略、错误模型、Service接入点、与其他模块关系、日志设计、测试计划、风险、分阶段实施计划
- 本次不改任何业务代码，不新增 Python service，不修改测试

### 修改文件

- `docs/P7_RESOURCE_GUARD_SPEC.md`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`（追加本节）

### 验证命令

```bash
git diff --stat
git diff --check
```

### 验证结果

- git diff --stat: docs/P7_RESOURCE_GUARD_SPEC.md（新增）、docs/PROJECT_HEALTH_CHECK.md（追加）
- git diff --check: 无 whitespace error
- 本次为文档任务，未执行全量测试

### 后续实施计划

| 阶段 | 目标 |
|---|---|
| P7-A | 方案设计（本次） |
| P7-B | 实现 ResourceGuardService 基础模块 + 单元测试 |
| P7-C | 接入核心同步路径（t2a_sync、voice_design、voice_clone、preview） |
| P7-D | 接入流式和异步路径（stream、async、variants） |
| P7-E | 接入批量路径（batch_longtext/script，评估 segment_render） |
| P7-F | 前端 RESOURCE_LIMIT_EXCEEDED 友好提示 |

---

## P7-A1 Resource Guard 方案审查修订

### 背景

- P7-A 方案设计已于上一 commit 完成（f249198）
- 人工审查发现部分设计边界需要修订，避免 P7-B 实现走偏
- 本次只修订文档，不修改任何业务代码

### 修订内容

1. **错误模型字段修正**：将 `http_status = 429` 改为 `status_code = 429`，与 `VoiceLabError` 体系一致，`voice_lab_error_handler` 读取 `exc.status_code`
2. **明确业务层使用 guard(...)**：对业务 Service 暴露 `guard(...)` 作为 async context manager，`_acquire` 作为内部方法，确保业务代码无法绕过 release
3. **增加测试隔离 reset 机制**：必须提供 `reset_resource_guard_for_tests()` 函数和 pytest autouse fixture 设计，避免单例状态导致测试间污染
4. **修正异步任务跨请求持有 lease**：明确第一版不跨 HTTP 请求持有 lease，submit 和 query/download 使用共享并发池（limit=2），不是同一长期租约
5. **修正批量任务 lease 生命周期边界**：区分 Layer 1（submit 入口瞬时保护）和 Layer 2（后台 execute 生命周期保护，P7-E 再设计）
6. **增加 CostGuard/ResourceGuard operation 映射表**：明确两个 Guard 的 operation 命名差异，Service 接入时需分别查表
7. **修正 VoiceRenderService 方法名**：将 `VoiceRenderService.render` 修正为 `VoiceRenderService.render_voice`
8. **补充 VoicePreviewService 与 ProviderVoicePreviewService 的 job_id 语义差异**：前者使用 preview_job 临时 ID（不对应真实 VoiceJob），后者使用真实 VoiceJob.id

### 修改文件

- `docs/P7_RESOURCE_GUARD_SPEC.md`（多处修订）
- `docs/PROJECT_HEALTH_CHECK.md`（追加本节）

### 验证命令

```bash
git diff --stat
git diff --check
```

### 验证结果

- git diff --stat: 通过（仅 docs/P7_RESOURCE_GUARD_SPEC.md、docs/PROJECT_HEALTH_CHECK.md）
- git diff --check: 通过，无 whitespace error
- 全量测试：未运行，原因：文档修订

### 后续实施计划

| 阶段 | 目标 |
|---|---|
| P7-B | 实现 ResourceGuardService 基础模块 + 单元测试（含测试 reset 机制） |
| P7-C | 接入核心同步与高风险路径（render_voice、design、clone、preview 等） |
| P7-D | 接入流式与异步路径（明确只做瞬时调用并发，不跨请求持有 lease） |
| P7-E | 接入批量路径（先 Layer 1 submit 入口，再评估 Layer 2 execute 生命周期） |

---

## P7-B ResourceGuardService 基础模块实现

### 背景

- P7-A 方案设计（f249198）和 P7-A1 修订（f6617a6）已完成
- 本次实现 ResourceGuardService 基础模块及单元测试，不接入业务服务
- 技术决策：采用 asyncio.Semaphore 实现并发控制（而非纯 Lock + Counter）

### 实现内容

新增文件：
- `app/services/resource_guard_service.py`：ResourceGuardService、ResourceLimitExceeded、ResourcePolicy、ResourceLease、get_resource_guard()、reset_resource_guard_for_tests()
- `tests/test_resource_guard.py`：15 个单元测试

### 技术决策记录

1. **Semaphore vs Lock+Counter**：第一版采用 `asyncio.Semaphore` 而非 Lock+Counter。Semaphore 本身是原子操作，适合"尝试获取-成功或拒绝"模式。

2. **wait_for timeout=0.001**：使用 `asyncio.wait_for(sem.acquire(), timeout=0.001)` 实现非阻塞语义。timeout=0 会导致 Python asyncio 内部任务取消异常传播问题，timeout=0.001（1ms）足以让可用permit立即成功，拒绝对timeout敏感的场景。

3. **_active 单独加锁**：`_active` dict 用于 introspection（current()、snapshot()），与 Semaphore 并发控制解耦。更新时使用独立 Lock 保护。

4. **_acquire/_release 保留为测试方法**：业务代码使用 `guard()` async context manager，`_acquire/_release` 仅供测试直接调用。

### 修改文件

- `app/services/resource_guard_service.py`（新增）
- `tests/test_resource_guard.py`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`（追加本节）

### 验证结果

```bash
python -m pytest tests/test_resource_guard.py -q
# 15 passed

python -m pytest tests/ -x -q
# 337 passed, 6 skipped (0:01:26)
```

### 后续实施计划

| 阶段 | 目标 |
|---|---|
| P7-C | 接入核心同步与高风险路径（render_voice、design、clone、preview 等） |
| P7-D | 接入流式与异步路径 |
| P7-E | 接入批量路径 |
| P7-F | 前端 RESOURCE_LIMIT_EXCEEDED 友好提示 |

---

## P7-B1 ResourceGuardService 并发控制实现修复

### 背景

- P7-B 已完成 ResourceGuardService 基础模块（commit eb31d25）
- 代码审查发现当前实现使用 `asyncio.Semaphore + wait_for(timeout=0.001)` 模拟非阻塞准入
- 该实现虽然测试通过，但和 P7-A1 的"立即拒绝、不排队、不等待"设计存在偏差
- `_active` 仅用于观测，不是真实控制来源，存在控制状态和观测状态不一致的风险

### 修复内容

1. **移除 asyncio.Semaphore**：删除 `_semaphores` dict 和 `_get_semaphore()` 方法，不再使用 Semaphore

2. **移除 wait_for(timeout=0.001)**：不再使用 `asyncio.wait_for(sem.acquire(), timeout=0.001)` 模拟非阻塞

3. **使用 asyncio.Lock + _active 原子计数**：`_active` 同时作为并发控制状态和 introspection 观测状态的单一来源。check 和 increment 在同一个 lock critical section 内完成，无等待、无排队

4. **_acquire/_release 保留为测试方法**：业务代码使用 `guard()` async context manager，`_acquire/_release` 仅供测试直接调用

5. **guard(...) finally 统一调用 _release(lease)**：guard 的 finally 只调用 `_release(lease)`，不再有自己的释放逻辑

6. **_release 幂等**：重复释放不会导致 `_active` 变负。降到 0 时 pop key 保持 snapshot 简洁

7. **重写并发测试**：使用 `asyncio.Event` 保证 holder 先持有 slot，contenders 再尝试获取，消除事件循环时序依赖

### 修改文件

- `app/services/resource_guard_service.py`
- `tests/test_resource_guard.py`
- `docs/PROJECT_HEALTH_CHECK.md`

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- `tests/test_resource_guard.py`：15 passed
- 全量测试：337 passed, 6 skipped (0:01:16)

### 后续计划

| 阶段 | 目标 |
|---|---|
| P7-C | 接入核心同步与高风险路径 |
| P7-C1 | 修复 voice_variants 双重 guard 边界问题 |
| P7-C1-fix | 修复真实 provider 双重限流 |
| P7-D | 接入异步与流式路径 |
| P7-E | 接入批量路径 |

---

## P7-C Resource Guard 核心同步与高风险路径接入

### 背景

- P7-B / P7-B1 已完成 ResourceGuardService 基础模块和实现修复（commit a66d04d）
- 本次进入 P7-C
- 本阶段只接入核心同步与高风险真实 Provider 调用路径
- 不接入异步、流式、批量

### 本次接入范围

- VoiceRenderService.render_voice → t2a_sync
- VoiceDesignService → voice_design
- VoiceCloneService.upload_audio → voice_clone_upload
- VoiceCloneService.clone_voice → voice_clone_create
- ProviderVoicePreviewService.preview → voice_preview
- VoicePreviewService.preview → binding_voice_preview
- VoiceVariantService → voice_variants

### 本次不接入范围

- AsyncRenderService
- StreamRenderService
- BatchOrchestrationService
- 前端
- Provider Adapter
- 数据库模型

### 修改文件

- app/services/voice_render_service.py
- app/services/voice_design_service.py
- app/services/voice_clone_service.py
- app/services/provider_voice_preview_service.py
- app/services/voice_preview_service.py
- app/services/voice_variant_service.py
- tests/test_voice_design.py（新增 Resource Guard 测试）
- tests/test_voice_clone.py（新增 Resource Guard 测试）
- tests/test_voice_preview.py（新增 Resource Guard 测试）
- tests/test_voice_variant_service.py（新增 Resource Guard 测试）
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_voice_design.py tests/test_voice_clone.py tests/test_voice_preview.py tests/test_voice_variant_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- 相关 Service 测试：55 passed
- 全量测试：343 passed, 6 skipped (0:01:28)

### 后续计划

| 阶段 | 目标 |
|---|---|
| P7-C1 | 修复 voice_variants 双重 guard 边界问题 |
| P7-D | 接入 AsyncRenderService 和 StreamRenderService |
| P7-E | 接入 BatchOrchestrationService |
| P7-F | 前端 RESOURCE_LIMIT_EXCEEDED 友好提示 |

---

## P7-C1 voice_variants 双重 guard 边界修复

### 背景

- P7-C 已完成 ResourceGuardService 基础模块和7个核心同步路径接入
- voice_variants 使用外层 voice_variants guard，但内部 render_voice 调用会再次获取 t2a_sync，形成双重限流
- VoiceVariantGroup 创建在 Resource Guard 之外，reject 时可能留下空 group 记录

### 问题

1. VoiceVariantService 外层 guard 使用 voice_variants，但 render_voice 内部又获取 t2a_sync（双重限流）
2. VoiceVariantGroup 在 guard 之前创建，reject 时 group 已存在但无 variants（空壳记录）

### 修改内容

1. **voice_render_service.py**：新增 `resource_guard_already_acquired: bool = False` 参数，当为 True 时跳过 t2a_sync guard
2. **voice_variant_service.py**：
   - 将 VoiceVariantGroup 创建移入 guard 内部（先 admission 再建 group，避免空记录）
   - render_voice 调用时传入 `resource_guard_already_acquired=True`（voice_variants guard 已保护，跳过 t2a_sync guard）
3. **tests/test_voice_variant_service.py**：新增3个 Resource Guard 测试用例

### 新增测试

- `test_variants_rejected_when_slot_full`：验证 voice_variants slot 满时拒绝，create_group 未被调用
- `test_variants_not_affected_by_t2a_sync_limit`：验证 t2a_sync 全满时 variants 不受影响（resource_guard_already_acquired=True 生效）
- `test_variants_success_path_works`：验证正常 variants 流程正确

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_voice_variant_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- VoiceVariant Service 测试：8 passed
- 全量测试：346 passed, 6 skipped

### 补充修复（P7-C1-provider）

在 P7-C1 基础上额外修复 provider 透传问题：

- `request.provider=None` 时，外层 guard 按 "mock" 处理，但内部 `render_voice` 收到 `None` 后会解析为真实 provider，导致外层/内层 provider 不一致
- 修复：`VoiceRenderRequest(provider=provider)` 使用已解析 provider，而非 `request.provider`
- `resource_guard_already_acquired=(provider == "mock")`：此设计仍有误，真实 provider 下仍然双重限流，需要进一步修复（见 P7-C1-fix）
- 新增测试：`test_variants_provider_none_passes_mock_to_render_voice`

---

## P7-C1-fix VoiceVariantService 真实 Provider 双重限流修复

### 背景

- P7-C1 初步修复后，VoiceVariantGroup 已移入 voice_variants guard 内部，provider 也已改为透传解析后的 provider
- 但 cae269f 中 `resource_guard_already_acquired=(provider == "mock")` 导致真实 provider 下仍然会进入内部 t2a_sync guard
- 这会让 voice_variants 和 t2a_sync 双重限流问题在 minimax 等真实 provider 下继续存在

### 修复内容

- `resource_guard_already_acquired=True` 始终传给 render_voice，不再区分 mock/real
- 修正错误注释：voice_variants guard 保护整个多版本请求，mock 和真实 provider 都适用
- 保留 `VoiceRenderRequest(provider=provider)` 正确透传
- 保留 VoiceVariantGroup 在 voice_variants guard 通过后创建
- 新增测试：`test_variants_real_provider_skips_t2a_sync_guard`（provider=minimax 时也传 True）
- 新增测试：`test_variants_not_affected_by_t2a_sync_limit`（t2a_sync 满载不影响 variants）

### 修改文件

- app/services/voice_variant_service.py
- tests/test_voice_variant_service.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_voice_variant_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- VoiceVariantService 测试：9 passed
- 全量测试：347 passed, 6 skipped

---

## P7-D Resource Guard 异步与流式路径接入

### 背景

- P7-C / P7-C1-fix 已完成核心同步、高风险路径和 voice_variants 双重 guard 边界修复
- 本次进入 P7-D
- 本阶段只接入 AsyncRenderService 和 StreamRenderService
- 不接入 BatchOrchestrationService

### 本次接入范围

- AsyncRenderService.submit_task → t2a_async_submit
- AsyncRenderService.query_status / _complete_job → t2a_async_query_download
- StreamRenderService.render_stream → t2a_stream

### 关键设计确认

- 异步任务不跨 HTTP 请求长期持有 lease
- submit_task 只保护 create_async_task 瞬时调用
- query_status 只保护 query_async_task 和成功后的 download/save 瞬时阶段
- query_status 被 Resource Guard 拒绝时，不把 job 标记 failed（因为只是查询资源忙，不是任务本身失败）
- stream guard 覆盖整个 async generator 生命周期
- stream 拿到 guard 后才 yield started
- stream 断开或 generator close 后自动释放 guard（async context manager）
- 本次不接入批量任务

### 本次不接入范围

- BatchOrchestrationService
- 前端
- Provider Adapter
- 数据库模型

### 修改文件

- app/services/async_render_service.py
- app/services/stream_render_service.py
- tests/test_async_render.py
- tests/test_stream_render_service.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：358 passed, 6 skipped

---

## P7-E Resource Guard 批量生成路径接入

### 背景

- P7-D1 已完成异步与流式路径的 Resource Guard 接入和状态机边界修复
- BatchOrchestrationService 尚需接入 Resource Guard
- submit_longtext 和 submit_script 需要在提交前做 admission control
- execute 需要在整个执行生命周期做 admission control
- segment 渲染失败时需要标记关联 VoiceJob 为 failed

### 修复内容

- submit_longtext: guard(batch_longtext) 包裹 BatchJob + BatchSegments 创建和 _execute_with_session 调用
- submit_script: guard(batch_script) 包裹 BatchJob + BatchSegments 创建和 _execute_with_session 调用
- execute: guard(batch_execute) 包裹整个执行生命周期；ResourceLimitExceeded 异常时标记 batch_job.status=failed 并返回
- _process_segment: try/except 包裹 render_sync 和 save_assets，异常时标记关联 VoiceJob.status=failed 后重新抛出
- 本次批量任务内的 segment 并发受 batch_max_concurrency 控制，不使用 t2a_sync guard（t2a_sync 是同步单次调用，无 guard）

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：16 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：363 passed, 6 skipped

---

## P7-E1 批量生成状态机边界修正

### 背景

- P7-E 首次提交后审查发现 segment 失败路径中 BatchSegment.voice_job_id 未稳定绑定
- 异常时 VoiceJob 可能处于 running 状态未被标记 failed
- save_assets 失败时状态同步缺失
- submit 被 Resource Guard 拒绝时未充分验证不产生脏数据
- submit_script 在 guard 内部做 profile 校验，边界不够清晰

### 修复内容

- VoiceJob 创建并标记 running 后，立即同步 BatchSegment.voice_job_id 和 status=running，确保失败路径可追踪
- 新增 _mark_segment_voice_job_failed helper 方法，统一处理 render_sync 和 save_assets 失败的收口
- _process_segment_isolated 增强兜底：segment 异常时若 VoiceJob 仍为 pending/running/processing则同步标记 failed
- submit_script 预校验所有 profile_id 后再进入 Resource Guard，符合"资源准入与业务校验分离"原则
- save_assets 失败时 BatchSegment + VoiceJob 同步 failed

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 测试增强

- submit_longtext rejected：验证 BatchJob/BatchSegment 数量不变，不启动 execute
- submit_script rejected：验证同上
- execute rejected：验证 failed_segments == total_segments，segment 无 voice_job_id/audio_asset_id
- segment render error：验证 segment.voice_job_id 非空，VoiceJob 与 segment 同步 failed
- save_assets error：新增测试，验证 segment + VoiceJob 同步 failed
- no t2a_sync double guard：验证 batch segments 不进入 t2a_sync guard（持有 minimax t2a_sync slots 不影响 mock batch 执行）

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：18 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：365 passed, 6 skipped

---

## P7-E2 Batch 状态机兜底与 no-double-guard 测试增强

### 背景

- P7-E1 首次提交后复核发现两个小问题
- _process_segment_isolated 兜底中，若 segment.status 已是 failed 但 voice_job 刚被改为 failed，则不会 commit
- test_batch_segments_execute_without_t2a_sync_guard 使用 provider="mock"，不能强证明 minimax batch segment 不走 t2a_sync guard

### 修复内容

- _process_segment_isolated 兜底改为 dirty flag 方式：changed = True 只要有任何一个对象被修改就 commit
- no t2a_sync double guard 测试改为 provider="minimax" + FakeMinimaxAdapter，更强验证 minimax batch segment 不进入 t2a_sync guard

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：18 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：365 passed, 6 skipped

---

## P7-E3 Batch 状态机最终收口

### 背景

- P7-E2 后继续基于完整现态代码审查 BatchOrchestrationService
- 发现 execute Resource Guard 拒绝时 BatchJob.error_message 缺失
- submit rejected 测试未断言 _execute_with_session 未调用
- merge 失败时可能导致 BatchJob 被误标 success

### 修复内容

- execute Resource Guard 拒绝时补充 BatchJob.error_message（使用 exc.message + exc.detail）
- submit_longtext / submit_script rejected 测试补充 _execute_with_session.assert_not_called()
- merge 失败时 BatchJob 不再误标 success（merge_error 优先判断）
- merge 失败只影响 BatchJob 最终状态，不回滚成功 segment

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：19 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：366 passed, 6 skipped

---

## P7-F 前端 RESOURCE_LIMIT_EXCEEDED 友好提示

### 背景

- P7 Resource Guard 后端准入控制已覆盖主要真实 provider 调用路径
- 后端在资源超限时返回 RESOURCE_LIMIT_EXCEEDED / HTTP 429
- 前端测试面板此前将该错误展示为普通失败或 alert 原始 JSON
- 本阶段只做前端错误解析与友好展示，不修改后端 Resource Guard

### 修改内容

- 在 app/static/index.html 新增统一 API 错误解析 helper：parseApiError、formatApiError、renderApiError、extractDetailValue、operationLabel
- 新增 RESOURCE_LIMIT_EXCEEDED 友好提示 CSS 样式（.resource-limit-msg）
- 普通 JSON fetch 接口统一解析 VoiceLabError payload
- T2A 同步 / 异步 / 流式 / 多版本试音 / 声音设计 / 声音克隆 / 批量提交等入口展示资源繁忙提示
- Resource Guard 拒绝时不展示成功结果、不启动无效 polling、不污染任务状态

### 修改文件

- app/static/index.html
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- 全量测试：366 passed, 6 skipped

---

## P7-F1 前端 Resource Limit 提示准确性收口

### 背景

- P7-F 已完成 RESOURCE_LIMIT_EXCEEDED 友好提示主体能力
- 复核发现 WebSocket error payload 可能没有 detail 字段，导致前端无法解析 operation
- 异步 query/download 被资源限制拒绝时，不应提示"没有创建新的任务"

### 修复内容

- WebSocket RESOURCE_LIMIT_EXCEEDED 使用 message 作为 detail fallback
- formatApiError 支持从 detail 或 message 中解析 operation
- renderApiError 根据 operation 展示不同额外说明
- t2a_async_query_download 提示"任务可能仍在处理中"
- submit 类操作继续提示"没有创建新的任务"
- batch_execute 提示"批量任务可能尚未开始执行"

### 修改文件

- app/static/index.html
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/ -x -q
```

### 验证结果

- 全量测试：366 passed, 6 skipped

## P7-D1 异步与流式状态机边界修复

### 背景

- P7-D 已接入 AsyncRenderService 与 StreamRenderService 的 Resource Guard
- 审查发现 query_status 异常处理范围过宽，可能让下载/保存失败的 job 长期 processing
- 审查发现 provider_task_id 缺失时 job 没有标记 failed
- 审查发现 stream generator 提前关闭时 Resource Guard 会释放，但 job 可能仍 running

### 修复内容

- query_status 中 ResourceLimitExceeded 仍保持 job processing
- provider_task_id 缺失时标记 job failed
- _complete_job 下载/保存失败时标记 job failed
- provider query 本身临时异常保持 processing 并重新抛出（本次不做改变）
- stream generator started 后、completed 前提前关闭时标记 job failed（finally 块处理）
- stream 正常完成不被 finally 覆盖
- stream Resource Guard 拒绝不 yield started，并保持 RESOURCE_LIMIT_EXCEEDED 语义
- 本次不接入 BatchOrchestrationService

### 修改文件

- app/services/async_render_service.py
- app/services/stream_render_service.py
- tests/test_async_render.py
- tests/test_stream_render_service.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：358 passed, 6 skipped

---

## P7-G Resource Guard 阶段总验收

### 背景

- P7-A 至 P7-F1 已完成 Resource Guard 后端准入、任务状态机、前端友好提示
- 本阶段进行完整现态复核与验收文档收口

### 工作内容

- 新增 docs/P7_RESOURCE_GUARD_ACCEPTANCE.md
- 汇总所有 Resource Guard operation 与业务入口（13 个唯一 operation，14 条业务入口覆盖记录）
- 汇总后端状态机验收点（同步、异步、流式、preview、clone、design、batch）
- 汇总前端 RESOURCE_LIMIT_EXCEEDED 提示验收点
- 执行后端回归测试
- 明确 P7 阶段结论：主线完成，可进入下一阶段

### 修改文件

- docs/P7_RESOURCE_GUARD_ACCEPTANCE.md（新增）
- docs/PROJECT_HEALTH_CHECK.md（追加本节）

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- BatchOrchestrationService 测试：19 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：**366 passed, 6 skipped**

### 阶段结论

**P7 Resource Guard 主线完成，可以进入下一阶段。**

所有后端 service 均正确接入 Resource Guard，状态机在拒绝路径保持一致，前端 RESOURCE_LIMIT_EXCEEDED 友好提示已覆盖所有入口。366 个自动化测试全部通过，无阻塞问题。

---

## P7-H 当前项目能力测试与验收

### 背景

- P7 Resource Guard 已完成（e05714a）
- 进入产品化前，需要对当前项目已有音频能力做系统测试
- 本阶段不新增业务能力，重点是验证现有能力是否可用

### 工作内容

- 新增 docs/P7_H_CAPABILITY_ACCEPTANCE.md
- 执行自动化测试（366 passed, 6 skipped）
- 代码审查确认各能力实现状态
- 汇总能力可用性与产品化建议
- 区分 mock 自动化验证和 minimax 代码审查确认

### 修改文件

- docs/P7_H_CAPABILITY_ACCEPTANCE.md（新增）
- docs/PROJECT_HEALTH_CHECK.md（追加本节）

### 测试结果

**自动化测试**：

```
tests/test_resource_guard.py         → 15 passed
tests/test_batch_orchestration.py    → 19 passed
tests/test_async_render.py          → 14 passed
tests/test_stream_render_service.py  → 9 passed
tests/ -x -q                         → 366 passed, 6 skipped
```

**手工测试**：未执行（需要启动 uvicorn 服务并使用真实 MiniMax token）

### 能力验收结论

| 能力 | 状态 |
|---|---|
| 同步 T2A（所有格式和参数） | 工程链路可用，真实 MiniMax 待 smoke test |
| 异步 T2A（submit/poll/download） | 工程链路可用，真实 MiniMax 待 smoke test |
| HTTP / WebSocket 流式 T2A | 工程链路可用，真实 MiniMax 待 smoke test |
| provider voice preview | 工程链路可用，真实 MiniMax 待 smoke test |
| binding voice preview | 工程链路可用，真实 MiniMax 待 smoke test |
| 声音克隆（上传/创建/绑定） | 暂缓产品化（高成本，需单独评估） |
| 声音设计 | 暂缓产品化（高成本，需单独评估） |
| 多版本试音 | 工程链路可用，真实 MiniMax 待 smoke test |
| 批量长文本生成 | 工程链路可用，真实 MiniMax 待 smoke test |
| 批量剧本生成 | 工程链路可用，真实 MiniMax 待 smoke test |
| 资产下载 / 历史记录 | 工程链路可用，真实 MiniMax 待 smoke test |
| Resource Guard 拒绝路径 | 工程链路可用，真实 MiniMax 待 smoke test |
| 前端测试面板交互 | 待手工验证 |

### 阶段结论

**P7-H 能力验收完成。第一批核心能力工程链路已通过自动化测试和代码审查，真实 MiniMax 能力仍需小文本 smoke test；声音克隆和声音设计为高成本能力，暂缓真实验证，后续单独立项。手工验证尚未执行，建议补充实际浏览器测试后进入 P8 前端 UX 修复阶段。**

---

## P7-I 低成本真实 MiniMax Smoke Test 与前端手工验证

### 背景

- P7-H 已确认工程链路可用
- 本阶段执行低成本真实 MiniMax smoke test（CLI 环境直接 API 调用）
- 声音克隆和声音设计继续暂缓真实验证
- 前端交互和 WebSocket 因无浏览器环境无法测试

### 工作内容

- 新增 docs/P7_I_MINIMAX_SMOKE_TEST.md
- 执行后端自动化测试（366 passed, 6 skipped）
- 启动 uvicorn 服务，直接 curl API 调用验证真实 MiniMax
- 测试同步 T2A、异步 T2A、批量长文本、批量剧本、provider preview
- 发现异步 subtitle timeline end 为 0.0 异常（P2-2）
- 发现 HTTP 流式端点不存在（P2-1）

### 修改文件

- docs/P7_I_MINIMAX_SMOKE_TEST.md（新增）
- docs/PROJECT_HEALTH_CHECK.md（追加本节）

### 测试结果

**自动化测试**：366 passed, 6 skipped

**真实 MiniMax API 测试**：

| 能力 | 结果 |
|---|---|
| 同步 T2A（url/hex） | ✅ 成功，~2s |
| 异步 T2A | ✅ 成功，约 4.5min（MiniMax 服务特性） |
| 批量长文本 | ✅ 成功，merged_audio + merged_subtitle |
| 批量剧本（2角色） | ✅ 成功，多角色正常 |
| provider voice preview | ✅ 成功 |
| 任务历史 | ✅ 成功 |
| WebSocket 流式 | ⚠️ 未测试（CLI 无浏览器） |
| 前端交互 | ⚠️ 未测试（CLI 无浏览器） |
| HTTP 流式端点 | ⚠️ 不存在（流式走 WebSocket） |
| 声音克隆/设计 | **暂缓** |

### 发现问题

- **P1**：异步 T2A 耗时约 4.5 分钟（MiniMax 服务特性，非代码问题）
- **P2-1**：HTTP 流式端点不存在，流式仅走 WebSocket
- **P2-2**：异步任务 subtitle timeline end 为 0.0 → **P7-I1 已修复**

### 阶段结论

**P7-I 真实 MiniMax smoke test 完成。同步 T2A、异步 T2A、批量生成、provider preview 均真实可用。P2-2 已修复；P2-1 HTTP 流式端点不存在仍作为产品/API 口径评估项保留。进入 P8 前仍需补充浏览器前端验证。**

---

## P7-I1 异步 T2A Subtitle Timeline 修复（P2-2）

### 背景

- P7-I 发现异步 T2A 任务完成后 subtitle timeline 的 end 时间为 0.0
- 根因：MiniMax 异步任务返回 `duration_ms=None`，且 metadata 中无 timeline 时，代码未做兜底

### 修复内容

- **文件**：app/services/async_render_service.py
- **修改**：`_complete_job` 方法中 `resolved_duration_ms` 增加 `estimate_duration_ms` 兜底
  ```python
  resolved_duration_ms = (
      task_status.duration_ms
      or task_status.metadata.get("duration_ms")
      or task_status.metadata.get("audio_length")
      or estimate_duration_ms(job.processed_text or job.input_text or "")
  )
  ```
- 同时确保 `duration_ms` 参数传给 `ProviderRenderResult`（之前传的是 `task_status.duration_ms`）

### 测试验证

- 后端自动化测试：366 passed, 6 skipped
- docs/P7_I_MINIMAX_SMOKE_TEST.md 更新：P2-2 标记为已修复

### 阶段结论

**P2-2 已修复；P2-1 HTTP 流式端点不存在仍作为产品/API 口径评估项保留。真实 MiniMax 主链路可用；进入 P8 前仍需补充浏览器前端验证，HTTP 流式端点是否补充另行评估。**

---

## P7-I2 Smoke Test 测试体系治理与进程防护

### 背景

- P7-I 真实 MiniMax smoke test 需要启动 uvicorn
- 手动启动服务后可能残留进程，占用端口
- 本阶段新增标准 smoke runner，治理端口和进程生命周期

### 修改内容

- 新增 `scripts/run_minimax_smoke.py` - 标准 smoke test runner
- 新增 `scripts/stop_smoke_server.py` - 停止残留 smoke server
- smoke test 使用独立端口 8010（可通过 `SMOKE_PORT` 覆盖）
- 启动 uvicorn 不使用 `--reload`
- 使用 `.tmp/uvicorn-smoke.pid` 管理进程
- 默认 dry-run / skip-minimax 不消耗 token
- 真实 MiniMax 调用必须显式 `--real-minimax`
- 测试结束自动清理 uvicorn（try/finally）
- 未知端口占用 fail fast，不盲目 kill
- `.gitignore` 忽略 `.tmp/`

### 阶段边界

- **本阶段不修复 P2-2 异步字幕 timeline**（P7-I1 已修复）
- **本阶段不补 HTTP stream 端点**
- **本阶段不测试声音克隆 / 声音设计**
- **本阶段不修改 app/services/*、app/providers/* 等业务逻辑**

### 阶段结论

**P7-I2 smoke runner 已就绪，可安全执行 dry-run 和真实 smoke test，无需手动管理进程。**

---

## P7-I2a Smoke Runner 可靠性收口

### 修复内容

- runner 自己启动的 uvicorn 优先通过 `proc.terminate()` / `proc.kill()` 清理，pidfile 仅用于残留清理
- 修正 stop 脚本 process alive 判断（tasklist CSV 输出解析，中英双语兼容）
- argparse 模式改为互斥组（`--dry-run | --skip-minimax | --real-minimax`）
- 结果状态统一为 `passed / failed / skipped`
- 删除 `--include-async` / `--include-batch` 参数（预留，暂不执行）
- Ctrl+C / ready 失败时正确清理
- 结果文件记录真实 `started_at / ended_at`

### 验证结果

- `--dry-run`：PASS ready_check，Cleanup: terminated
- `--skip-minimax`：PASS ready_check + jobs_history
- `stop_smoke_server.py`：no pidfile 时 clean
- `--dry-run --skip-minimax`：argparse 报错 "not allowed with argument"
- pytest：368 passed, 6 skipped

### 阶段边界

- 不修改业务代码
- 不真实消耗 MiniMax token（除非显式 `--real-minimax`）

---

## P7-I3 前端异步轮询退避与慢任务体验优化

### 背景

- P7-I 浏览器简测发现功能主链路正常
- 异步 T2A 回复较慢，符合 MiniMax 异步服务特性
- 原有前端固定 3 秒轮询导致日志刷屏和 provider query 压力

### 修改内容

- `app/static/index.html` 增加异步轮询状态对象 `asyncPollingState`
- 增加轮询退避策略 `getAsyncPollingDelay()`：0-30s 每 3s，30s-2min 每 10s，2min+ 每 20s
- 提交后显示"可能需要 1-5 分钟"慢任务提示
- 增加手动刷新（`manualRefreshAsyncJob`）和停止自动刷新（`stopAsyncPolling`）按钮
- Resource Guard 查询拒绝时停止自动轮询
- 添加空 favicon `data:,`，避免 `/favicon.ico` 404 日志噪音

### 验证结果

- 代码层面已接入异步轮询退避，手动刷新、停止自动刷新和最大自动轮询保护；浏览器手工验证结果需按实际测试补充。
- pytest：368 passed, 6 skipped
- 不消耗 MiniMax token（前端体验优化，无后端改动）

### 阶段边界

- 不修改 `app/services/*`、`app/providers/*` 等业务代码
- 不修改 Resource Guard 策略
- 不实现新的后端能力

---

## P7-I3a 异步轮询退避收口

### 背景

- P7-I3 已完成异步轮询退避和慢任务提示
- 复核发现手动刷新可能导致重复 timer
- 自动轮询缺少最大时长限制

### 修改内容

- 增加 `clearAsyncPollingTimer()` 分层 helper
- 手动刷新前清理旧 timer
- 设置新 timer 前清理旧 timer
- 增加 jobId 防护，避免旧 timer 污染当前 job
- 增加最大自动轮询时长（15 分钟），超过后暂停自动刷新
- 停止自动刷新后更新 UI 提示

### 验证结果

- 代码层面已完成所有 timer 防护逻辑
- pytest：368 passed, 6 skipped
- 前端浏览器手工验证结果需补充

### 阶段结论

异步轮询已实现防重复 timer 和最大自动轮询时长保护，逻辑完整。
- 不修改 Resource Guard 策略
- 不实现新的后端能力

---

## P7-I5 Admin Stats characters=0 修复 + Provider Error Attribution

### 背景

- Admin stats API 返回 `total_characters: 0`，即使有成功的 T2A 任务
- 需要工具分析 provider 错误归因

### 根因分析

**问题 1：`job_id` 上下文未设置**
- `job_id_var` 从未被设置，`get_job_id()` 返回空字符串
- `_save_call_log` 存储 `job_id=NULL`，`update_call_log` 查询 `job_id=""` 找不到记录
- 导致 `usage_characters` 从未被正确更新

**问题 2：异步任务从未调用 `update_call_log`**
- `create_async_task` 不调用 `update_call_log`

**问题 3：`StatsService` 仅从 `ProviderCallLog` 读取**
- 不使用 `AudioAsset.usage_characters` 作为后备

### 修改内容

**context.py**
- 新增 `set_job_id(job_id: str)` 函数

**voice_render_service.py**
- `render_voice()` 在调用 `render_sync()` 前设置 `set_job_id(job.id)`

**async_render_service.py**
- `submit_task()` 在调用 `create_async_task()` 前设置 `set_job_id(job.id)`
- `query_status()` 在调用 `query_async_task()` 前设置 `set_job_id(job.id)`

**stats_service.py**
- `get_summary()` 对 `total_characters`、`by_provider`、`by_day` 使用 `MAX(call_chars, asset_chars)` 
- 这确保即使 `ProviderCallLog.usage_characters` 未更新，也能从 `AudioAsset` 获取准确值

**scripts/analyze_provider_errors.py**（新增）
- 按错误类型、错误消息前缀、API路径、provider 分组分析错误
- 支持 `--days`、`--provider`、`--error-type`、`--top`、`--json` 参数

### 验证结果

- pytest：368 passed, 6 skipped
- `python scripts/analyze_provider_errors.py --days 7 --top 5` 正常运行

### 阶段结论

- `job_id` 上下文修复确保同步 T2A 的 `update_call_log` 正常工作
- `AudioAsset` 后备确保异步任务字符统计准确
- Provider error analysis 脚本可用于识别错误模式

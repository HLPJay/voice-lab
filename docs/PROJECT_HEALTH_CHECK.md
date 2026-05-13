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
| P7-D | 接入流式与异步路径 |
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
- VoiceVariant Service 测试：7 passed
- 全量测试：345 passed, 6 skipped

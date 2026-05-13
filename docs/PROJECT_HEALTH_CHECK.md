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

# P7-A Resource Guard 第一版方案设计

## 1. 背景

Voice Lab 当前已完成 P6 固化，全量测试 322 passed，6 skipped，已建立 baseline tag `p6-dev-baseline-20260513`。

项目当前已经具备以下真实 Provider 调用能力：

- 同步 T2A 生成（VoiceRenderService）
- 异步 T2A 提交与轮询（AsyncRenderService）
- WebSocket 流式 T2A（StreamRenderService）
- 声音设计（VoiceDesignService）
- 声音克隆（VoiceCloneService）
- 音色试听（ProviderVoicePreviewService / VoicePreviewService）
- 多版本试音（VoiceVariantService）
- 批量长文本生成（BatchOrchestrationService）
- 多角色剧本生成（BatchOrchestrationService）

这些能力都会触发真实 MiniMax API 调用。当前已有 Cost Guard，但它只解决"用户是否确认成本"的问题，不解决"当前资源是否允许执行"的问题。

当前缺失的保护层：

- 无 provider / model / operation 维度的并发控制
- 无高风险操作串行保护
- 无批量任务的全局资源限制
- 无重复点击防护
- 无 WebSocket 长连接占用期间的资源隔离

Resource Guard 是进入小范围真实试用前的必要保护层，其目标是在 Cost Guard 之后、Provider Adapter 之前，统一管控真实调用的资源准入。

---

## 2. Resource Guard 的定位

### 2.1 职责边界

Resource Guard 不是以下任何一种：

| 模块 | 职责 |
|---|---|
| Cost Guard | 判断用户是否已确认成本（confirm_cost） |
| Resource Guard | 判断当前是否允许执行（资源是否允许） |
| Budget Guard | 判断预算是否足够（未来） |
| Request Cache | 判断是否可以复用已有结果（未来） |
| Provider Adapter | 实际执行 Provider HTTP 调用 |
| 后台任务队列 | 任务持久化和异步调度（未来） |

### 2.2 架构位置

```
API Request
     ↓
Service Layer
     ↓
Cost Guard (confirm_cost 检查)
     ↓
Resource Guard (资源准入控制)
     ↓
RenderPlan / Operation Payload
     ↓
Provider Adapter
     ↓
MiniMax / Future Providers
```

- **Cost Guard**：先执行，用户未 confirm_cost 时直接拒绝，不进入 Resource Guard
- **Resource Guard**：Cost Guard 通过后，判断当前资源是否允许执行
- **Provider Adapter**：Resource Guard 通过后，执行真实 Provider 调用

### 2.3 第一版设计原则

- 内存级并发控制，单进程有效
- 不做 Redis 分布式锁
- 不做任务排队
- 不做预算预占
- 不做持久化
- 可选 model 维度（第一版只记录，不单独限制）
- mock provider 不限制

---

## 3. 第一版设计边界

### 3.1 第一版要做

- provider + operation 维度的并发限制
- 内存级 slot 管理（asyncio.Semaphore 或 dict + lock）
- async context manager 模式的 acquire/release
- 异常时自动 release（保证不泄漏）
- mock provider 直接放行（no-op lease）
- 真实 provider 受限
- 超限时直接抛出 `ResourceLimitExceeded` 异常
- 结构化日志记录 acquire / release / reject 事件
- 单例或模块级共享状态（避免每次 new 导致限流失效）

### 3.2 第一版不做

- Redis / 分布式锁
- 后台队列
- 任务排队（超限直接拒绝，不排队）
- 预算预占和结算
- 多用户额度管理
- API Key 池
- 管理后台
- 持久化资源占用表
- 自动重试排队
- Resource Guard 前端配置页面
- Request Cache
- Budget Guard

---

## 4. Operation 类型定义

### 4.1 第一版识别的 operation

| operation | 场景 | Provider 调用 | 风险等级 | 默认策略 | 说明 |
|---|---|---|---|---|---|
| `t2a_sync` | 同步 T2A 生成 | 是 | 中 | limit=2 | 普通同步生成 |
| `t2a_async_submit` | 异步任务提交 | 是 | 中 | limit=2 | 异步提交阶段 |
| `t2a_async_query_download` | 异步任务查询和文件下载 | 是 | 中 | limit=2 | 与 submit 共享 limit |
| `t2a_stream` | WebSocket 流式生成 | 是 | 中 | limit=1 | 长连接占用资源，保守限制 |
| `voice_preview` | Provider 直连试听 | 是 | 低 | limit=2 | 直接试听已有音色 |
| `binding_voice_preview` | 绑定试听 | 是 | 低 | limit=2 | 绑定关系试听 |
| `voice_variants` | 多版本试音 | 是 | 中 | limit=1 | 一次请求放大多个 T2A |
| `voice_design` | 声音设计 | 是 | 高 | limit=1 | 串行保护高成本操作 |
| `voice_clone_upload` | 克隆音频上传 | 是 | 中 | limit=1 | 上传阶段串行保护 |
| `voice_clone_create` | 克隆任务创建 | 是 | 高 | limit=1 | 高成本操作，串行 |
| `provider_voice_import_verify` | 音色导入验证 | 是 | 低 | limit=1 | 导入过程含试听 |
| `batch_longtext` | 批量长文本任务入口 | 是 | 中 | limit=1 | 保护批量总入口 |
| `batch_script` | 批量剧本任务入口 | 是 | 中 | limit=1 | 剧本批量总入口 |
| `batch_segment_render` | 批量段落内部渲染 | 是 | 中 | 受 batch_max_concurrency 共同约束 | 第一版不单独接入，待 P7-E 评估 |

### 4.2 接入优先级分类

**第一优先级（必须接入，高风险或易放大）：**

- `t2a_stream` — WebSocket 长连接，limit=1
- `voice_design` — 高成本，limit=1
- `voice_clone_create` — 高成本，limit=1
- `voice_clone_upload` — 串行保护，limit=1
- `voice_variants` — 一次请求放大多个 T2A，limit=1
- `batch_longtext` — 批量总入口，limit=1
- `batch_script` — 批量总入口，limit=1

**第二优先级（建议接入）：**

- `t2a_sync` — 普通生成，limit=2
- `t2a_async_submit` — 异步提交，limit=2
- `t2a_async_query_download` — 查询下载，limit=2
- `voice_preview` — 试听，limit=2
- `binding_voice_preview` — 试听，limit=2
- `provider_voice_import_verify` — 导入验证，limit=1

**第三优先级（暂不接入，需要和 batch_max_concurrency 联合设计）：**

- `batch_segment_render` — 段落内部渲染，避免双重 semaphore 死锁，待 P7-E 评估

---

## 5. 默认资源策略

### 5.1 mock provider 策略

| provider | operation | limit | 说明 |
|---|---|---|---|
| mock | all | unlimited | 测试 provider，不限制 |

### 5.2 MiniMax 策略

| provider | operation | limit | 说明 |
|---|---|---|---|
| minimax | t2a_sync | 2 | 普通同步生成，并发限制2 |
| minimax | t2a_async_submit | 2 | 异步提交，与 query 共享状态 |
| minimax | t2a_async_query_download | 2 | 查询下载，与 submit 共享状态 |
| minimax | t2a_stream | 1 | WebSocket 长连接，占用资源时间长 |
| minimax | voice_preview | 2 | 直接试听音色 |
| minimax | binding_voice_preview | 2 | 绑定试听 |
| minimax | voice_variants | 1 | 多版本试音放大调用次数 |
| minimax | voice_design | 1 | 高成本，声音设计串行 |
| minimax | voice_clone_upload | 1 | 音频上传串行 |
| minimax | voice_clone_create | 1 | 高成本，克隆创建串行 |
| minimax | provider_voice_import_verify | 1 | 导入含试听 |
| minimax | batch_longtext | 1 | 批量长文本任务入口串行 |
| minimax | batch_script | 1 | 剧本任务入口串行 |
| minimax | batch_segment_render | 待评估 | 需避免与 batch_max_concurrency 冲突 |

### 5.3 设计原则说明

**宁可保守，不追求吞吐。** P6 baseline 后，试用阶段重点是防失控，不是最大并发。

**batch_longtext / batch_script 保护任务入口。** 批量任务总入口限流，确保同时只能有一个批量任务在运行，防止多批量同时提交导致成本放大。

**batch_segment_render 与 batch_max_concurrency 的关系需要谨慎设计：**

- `batch_max_concurrency` 控制批量内部同时渲染的段落数（semaphore in BatchOrchestrationService）
- `batch_segment_render` 是 Resource Guard 层面的真实 Provider 调用限流
- 如果两个都限制得太死，可能导致批量任务几乎无法并行
- 建议 P7-E 阶段再评估如何接入，避免第一版引入复杂联合限流逻辑

**async submit 和 query_download 使用共享状态。** 异步任务提交后，查询和下载是同一任务的延续阶段，应该共享 slot，避免一个任务占着 submit slot 还在同时查询。

---

## 6. ResourceGuardService 设计草案

### 6.1 模块位置

```
app/services/resource_guard_service.py
```

### 6.2 核心对象

```python
# 资源策略定义
class ResourcePolicy:
    provider: str
    operation: str
    limit: int  # 并发上限
    description: str

# 租约对象（context manager 返回）
class ResourceLease:
    provider: str
    operation: str
    job_id: str | None
    acquired_at: float
    is_noop: bool  # mock provider 或 unlimited 时为 True

    async def release(self): ...

# 异常
class ResourceLimitExceeded(VoiceLabError):
    code = "RESOURCE_LIMIT_EXCEEDED"
    provider: str
    operation: str
    limit: int
    current: int
    job_id: str | None

# 服务主体
class ResourceGuardService:
    def __init__(self):
        # 模块级共享状态，不能每个 Service new 一个实例
        self._slots: dict[str, int]  # key = f"{provider}:{operation}"
        self._locks: dict[str, asyncio.Lock]
        self._policies: dict[str, ResourcePolicy]

    async def acquire(
        self,
        provider: str,
        operation: str,
        model: str | None = None,
        job_id: str | None = None,
    ) -> ResourceLease:
        """申请资源租约，成功则返回 lease，失败则抛出 ResourceLimitExceeded"""

    async def release(self, lease: ResourceLease): ...

# 模块级单例（关键：确保所有 Service 共享同一状态）
_guard: ResourceGuardService | None = None

def get_resource_guard() -> ResourceGuardService:
    global _guard
    if _guard is None:
        _guard = ResourceGuardService()
    return _guard
```

### 6.3 acquire 语义

```python
# 正确用法（async with 保证 release）
async with resource_guard.acquire(provider="minimax", operation="t2a_stream", job_id=job.id):
    async for msg in adapter.render_stream(plan):
        await websocket.send_json(msg)

# 错误用法（不允许手动 acquire 后忘记 release）
lease = await resource_guard.acquire(provider="minimax", operation="t2a_stream")
# ... 业务逻辑 ...
await resource_guard.release(lease)  # 容易忘记，容易异常路径遗漏
```

### 6.4 mock provider 处理

```python
async def acquire(self, provider, operation, ...):
    if provider == "mock":
        return ResourceLease(provider=provider, operation=operation, is_noop=True)
    # 否则走真实限流逻辑
```

### 6.5 状态共享关键设计

**问题：** 如果每个 Service 都 `ResourceGuardService()` 新建实例，而内部 `_slots` 状态不是共享的，则限流完全失效——每个实例的 slot 计数都是独立的零。

**解决方案：**

```python
# 方案A：模块级单例（推荐）
_guard: ResourceGuardService | None = None

def get_resource_guard() -> ResourceGuardService:
    global _guard
    if _guard is None:
        _guard = ResourceGuardService()
    return _guard

# 方案B：FastAPI dependency（需要 request.app.state）
# 方案A 更简单，不需要修改 FastAPI 依赖注入体系
```

### 6.6 slot key 设计

```
f"{provider}:{operation}"
# 例如: "minimax:t2a_stream", "minimax:voice_design"
```

对于 async submit/query_download 共享：

```
f"{provider}:t2a_async"  # 两种 operation 共用同一 slot
```

---

## 7. 错误模型设计

### 7.1 错误类定义

```python
class ResourceLimitExceeded(VoiceLabError):
    code = "RESOURCE_LIMIT_EXCEEDED"
    http_status = 429  # Too Many Requests

    def __init__(
        self,
        provider: str,
        operation: str,
        limit: int,
        current: int,
        job_id: str | None = None,
    ):
        self.provider = provider
        self.operation = operation
        self.limit = limit
        self.current = current
        self.job_id = job_id
        detail = f"provider={provider}, operation={operation}, limit={limit}, current={current}"
        if job_id:
            detail += f", job_id={job_id}"
        super().__init__(
            message="当前生成任务较多，请稍后再试",
            detail=detail,
        )
```

### 7.2 HTTP 响应格式

```json
{
  "error": {
    "code": "RESOURCE_LIMIT_EXCEEDED",
    "message": "当前生成任务较多，请稍后再试",
    "detail": "provider=minimax, operation=t2a_stream, limit=1, current=1"
  }
}
```

### 7.3 错误处理原则

- 走现有 VoiceLabError 体系，不新建异常类型
- 不暴露 Provider API Key 等敏感信息
- `detail` 字段供前端调试和日志分析，不直接展示给用户
- 前端根据 `code == "RESOURCE_LIMIT_EXCEEDED"` 显示友好重试提示
- 第一版不排队，超限直接失败

---

## 8. Service 接入点设计

### 8.1 接入模式

每个 Service 的 Provider 调用路径，包裹 `async with resource_guard.acquire(...)`。

### 8.2 接入点详细列表

**1. VoiceRenderService.render**
- operation: `t2a_sync`
- 包裹 `adapter.render_sync(plan)`
- 位置：在 Cost Guard 检查之后，adapter 调用之前

**2. AsyncRenderService.submit_task**
- operation: `t2a_async_submit`
- 包裹 `adapter.create_async_task(plan)`

**3. AsyncRenderService.query_status / _complete_job**
- operation: `t2a_async_query_download`
- 包裹查询和文件下载阶段
- 注意：submit 和 query 可共享 slot key `t2a_async`

**4. StreamRenderService.render_stream**
- operation: `t2a_stream`
- 包裹整个 `async for msg in adapter.render_stream(plan)` 循环
- 关键：WebSocket 断开时必须触发 release，即使客户端异常退出

**5. VoiceVariantService.render_variants**
- operation: `voice_variants`
- 包裹整个多版本试音循环，在循环开始前 acquire，在所有变体完成后 release
- 注意：一个 variants 请求会放大为多个 T2A 调用，必须整体受保护

**6. VoiceDesignService.design_voice**
- operation: `voice_design`
- 包裹 `adapter.design_voice(...)`

**7. VoiceCloneService.upload_audio**
- operation: `voice_clone_upload`
- 包裹 `adapter.upload_voice_file(...)`

**8. VoiceCloneService.clone_voice**
- operation: `voice_clone_create`
- 包裹 `adapter.clone_voice(...)`

**9. ProviderVoicePreviewService.preview**
- operation: `voice_preview`
- 包裹 `adapter.render_sync(plan)`

**10. VoicePreviewService.preview**
- operation: `binding_voice_preview`
- 包裹 `adapter.render_sync(plan)`

**11. ProviderVoiceImportService.import_voice**
- operation: `provider_voice_import_verify`
- 包裹 verify 阶段 `adapter.render_sync(plan)`

**12. BatchOrchestrationService.submit_longtext**
- operation: `batch_longtext`
- 在批量任务整体开始前 acquire，整个批量任务完成后 release
- 注意：批量任务周期长，lease 生命周期需要覆盖所有 segment

**13. BatchOrchestrationService.submit_script**
- operation: `batch_script`
- 同 submit_longtext

**14. BatchOrchestrationService._process_segment**
- operation: `batch_segment_render`
- 第一版暂不接入（见 5.3 说明）
- 后续 P7-E 评估是否以及如何接入

### 8.3 接入顺序建议

**第一阶段接入（高风险和易放大，必须做）：**

1. `t2a_stream` — StreamRenderService
2. `voice_design` — VoiceDesignService
3. `voice_clone_create` — VoiceCloneService
4. `voice_clone_upload` — VoiceCloneService
5. `voice_variants` — VoiceVariantService
6. `batch_longtext` — BatchOrchestrationService
7. `batch_script` — BatchOrchestrationService

**第二阶段接入（普通并发限制）：**

8. `t2a_sync` — VoiceRenderService
9. `voice_preview` — ProviderVoicePreviewService
10. `binding_voice_preview` — VoicePreviewService
11. `provider_voice_import_verify` — ProviderVoiceImportService

**第三阶段接入（异步链路）：**

12. `t2a_async_submit` — AsyncRenderService
13. `t2a_async_query_download` — AsyncRenderService

---

## 9. 与已有模块的关系

### 9.1 CostGuardService

- Cost Guard 先执行
- 用户未 `confirm_cost` 时，直接 raise ValidationError (422)，不进入 Resource Guard
- 用户确认成本后，再进入 Resource Guard 判断资源是否允许
- 两个 Guard 是串联关系，不是互斥关系

### 9.2 Provider Adapter

- Provider Adapter 不感知业务 operation 概念
- Resource Guard 不应修改 MiniMaxSpeechAdapter 的请求拼装逻辑
- Resource Guard 在 adapter 调用之前拦截，不在后端响应之后

### 9.3 ProviderCallLog

- Resource Guard 第一版不写 ProviderCallLog
- ProviderCallLog 仍然只记录实际 Provider 调用
- 被 Resource Guard 拒绝的请求不会产生 Provider 调用日志
- 应在业务日志中记录被拒绝的事件（`resource_rejected`）

### 9.4 VoiceJob

- 如果 job 在 Resource Guard 通过前创建，超限后需要更新 `job.status = "failed"`
- 如果 job 在 Resource Guard 通过后创建，异常时必须同时更新 job
- 推荐：尽量在真实 Provider 调用前、创建高成本任务前拦截
- Stream/WebSocket 场景：job 已创建，Resource Guard 失败时需要更新 job

### 9.5 batch_max_concurrency

| 维度 | batch_max_concurrency | Resource Guard |
|---|---|---|
| 位置 | BatchOrchestrationService 内部 | Service 和 Adapter 之间 |
| 控制 | 批量内部段落并发数 | 真实 Provider 全局调用数 |
| 范围 | 单个批量任务 | 全局所有任务共享 |
| 持久化 | 无 | 无（内存） |

两者不能互相替代：
- `batch_max_concurrency=1` 时，一个批量任务内部最多 1 个 segment 并行
- `Resource Guard t2a_stream=1` 时，全局最多 1 个 WebSocket 流式生成

**双重限流死锁风险：** 如果 batch_segment_render 同时受两者限制，且各自为 1，可能导致批量任务几乎无法推进。第一版不接入 batch_segment_render。

---

## 10. 日志设计

### 10.1 事件类型

| 事件 | 触发时机 | 建议级别 |
|---|---|---|
| `resource_acquire_attempt` | 开始申请租约 | INFO |
| `resource_acquired` | 租约成功获取 | DEBUG |
| `resource_rejected` | 租约被拒绝（超限） | WARN |
| `resource_released` | 租约正常释放 | DEBUG |
| `resource_release_failed` | 租约释放异常 | ERROR |

### 10.2 日志字段

```python
logger.info(
    "resource_acquired",
    provider=provider,
    operation=operation,
    model=model,
    job_id=job_id,
    limit=limit,
    current=current_after_acquire,
    duration_ms=time.time() - acquired_at,
)

logger.warn(
    "resource_rejected",
    provider=provider,
    operation=operation,
    model=model,
    job_id=job_id,
    limit=limit,
    current=current,
    reason="limit exceeded",
)
```

### 10.3 日志存储

- 第一版写结构化日志到现有日志体系（不新增数据库表）
- 日志字段包含 provider、operation、job_id、limit、current、duration_ms
- 可通过 `provider_trace_id` 或 `job_id` 关联具体请求

---

## 11. 测试计划

### 11.1 新增测试文件

```
tests/test_resource_guard.py
```

### 11.2 单元测试场景

**基础功能测试：**

1. `test_mock_provider_unlimited` — mock provider 所有 operation 都不限流，返回 noop lease
2. `test_acquire_success` — minimax t2a_sync limit=2 时，第一次 acquire 成功
3. `test_acquire_rejected` — minimax t2a_sync limit=1 时，第二个并发 acquire 被拒绝，抛出 ResourceLimitExceeded
4. `test_release_called_on_exit` — async with 正常退出时 release 被调用
5. `test_release_called_on_exception` — async with 内抛异常时 release 仍被调用
6. `test_different_operations_independent` — 不同 operation 互不影响
7. `test_different_providers_independent` — 不同 provider 互不影响
8. `test_same_operation_blocked` — 同一 operation 达到 limit 后后续请求阻塞

**错误模型测试：**

9. `test_resource_limit_exceeded_error_code` — 错误 code 为 RESOURCE_LIMIT_EXCEEDED
10. `test_resource_limit_exceeded_http_status` — HTTP status 为 429
11. `test_resource_limit_exceeded_detail_fields` — detail 包含 provider、operation、limit、current

**并发安全测试：**

12. `test_concurrent_acquires_respected` — asyncio.gather 并发 acquire，验证 slot 不超限
13. `test_rapid_acquire_release_cycle` — 快速反复获取释放，状态保持一致

**特殊 operation 测试：**

14. `test_voice_design_limit_1` — voice_design limit=1 串行保护
15. `test_batch_longtext_limit_1` — batch_longtext limit=1 保护任务入口
16. `test_voice_variants_limit_1` — voice_variants limit=1 防止调用放大

**边界测试：**

17. `test_unknown_operation_default_limit` — 未定义的 operation 应有默认行为
18. `test_model_field_recorded` — model 字段被记录到日志（第一版不限制，仅记录）

### 11.3 集成测试建议（后续 P7-C/D/E 接入后）

- VoiceRenderService 接入后测试超限拒绝
- StreamRenderService 接入后测试连接占用期间第二个 stream 被拒绝
- VoiceDesignService 接入后测试 confirm_cost 通过但资源超限仍拒绝
- BatchOrchestrationService 接入后测试 batch 入口限流

---

## 12. 风险与注意事项

### 12.1 单进程限制

第一版是内存级并发控制，不支持多进程部署：

- uvicorn 多 worker 时，每个 worker 有独立 Resource Guard 状态
- 多 worker 部署下限流不生效
- 后续如需多进程，需要 Redis 分布式锁（P8 考虑）

### 12.2 服务重启

- 服务重启后所有资源状态清空
- 长时间 running 的任务（如 batch）重启后需要确保状态一致
- 建议：服务重启前拒绝新任务，待已有任务完成（或超时）

### 12.3 WebSocket release 保证

- WebSocket 断开时必须确保 release 被调用
- 使用 `try/finally` 或 `async with` 保证
- 前端断网、标签页关闭、服务端重启都需要能正确 release

### 12.4 异步任务阶段分离

- async submit 和 query/download 是不同阶段
- 不能简单将两者等同为同一 operation slot
- query/download 阶段如果单独限流，需要考虑：一个任务提交后，在查询期间 slot 是否释放？

**建议：** async submit 和 query 使用共享 slot key，确保整个任务周期内占用资源。

### 12.5 批量任务 lease 生命周期

- batch_longtext / batch_script 的 lease 需要覆盖整个批量任务周期
- 如果批量任务后台执行，Service 持有 lease 直到所有 segment 完成
- 如果中间出错，需要确保 lease 仍被释放

### 12.6 实例复用问题

- 如果每个 Service 都 `ResourceGuardService()` 新建实例，限流完全失效
- 必须使用模块级单例或 FastAPI app.state 共享状态
- 测试时需要 patch `get_resource_guard()` 返回测试实例

### 12.7 避免引入复杂队列

- 第一版不做排队，超限直接拒绝
- 不要为了"体验更好"偷偷加入排队逻辑
- 排队逻辑应该在 P8/P9 阶段单独设计

---

## 13. 分阶段实施计划

### P7-A：方案设计（本次）

- 完成本文档
- 不改代码

### P7-B：实现 ResourceGuardService 基础模块

- 新增 `app/services/resource_guard_service.py`
- 实现 `ResourceGuardService`、`ResourcePolicy`、`ResourceLease`、`ResourceLimitExceeded`
- 实现 `get_resource_guard()` 模块级单例
- 接入所有 operation 的默认策略
- 新增 `tests/test_resource_guard.py`
- 验证所有单元测试通过
- 不接入任何业务 Service

### P7-C：接入核心同步路径

- 接入 `VoiceRenderService`（t2a_sync）
- 接入 `VoiceDesignService`（voice_design）
- 接入 `VoiceCloneService`（voice_clone_upload、voice_clone_create）
- 接入 `ProviderVoicePreviewService`（voice_preview）
- 接入 `VoicePreviewService`（binding_voice_preview）
- 接入 `ProviderVoiceImportService`（provider_voice_import_verify）
- 重点测试：confirm_cost 通过但 resource 超限时正确拒绝

### P7-D：接入流式和异步路径

- 接入 `StreamRenderService`（t2a_stream）
- 接入 `AsyncRenderService`（t2a_async_submit、t2a_async_query_download）
- 接入 `VoiceVariantService`（voice_variants）
- 重点测试：WebSocket 断开后 release、async 任务各阶段 slot 状态

### P7-E：接入批量路径

- 接入 `BatchOrchestrationService.submit_longtext`（batch_longtext）
- 接入 `BatchOrchestrationService.submit_script`（batch_script）
- 评估 `batch_segment_render` 是否接入及如何避免双重限流
- 避免与 `batch_max_concurrency` 冲突

### P7-F：前端错误提示

- 前端对 `RESOURCE_LIMIT_EXCEEDED` 展示友好重试提示
- 不做复杂排队 UI

### P8 及以后（超出第一版范围）

- Redis 分布式锁（多进程支持）
- Budget Guard
- Request Cache
- 多用户额度
- 后台任务队列

---

## 14. 验收标准

本文档验收标准：

1. **定位清晰**：明确 Resource Guard 不是 Cost Guard、Budget Guard、Request Cache、Provider Adapter
2. **边界明确**：第一版只做内存级单进程并发控制，不做 Redis/排队/持久化
3. **Operation 完整**：覆盖所有 14 个 operation，有优先级分类
4. **策略明确**：给出 mock / minimax 的默认策略表，batch 设置 limit=1
5. **接入点清晰**：列出全部 14 个接入点，有优先级排序
6. **机制明确**：async context manager，异常自动 release，单例共享状态
7. **错误模型**：RESOURCE_LIMIT_EXCEEDED，429，结构化 detail
8. **测试计划**：18 个单元测试场景，覆盖正常/异常/并发/边界
9. **不做范围明确**：Redis、排队、Budget、多用户等明确排除
10. **实施阶段清晰**：P7-A~F 各阶段目标明确

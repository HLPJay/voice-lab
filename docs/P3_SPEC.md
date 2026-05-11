# P3 规范：日志管理、可观测性与报告分析

## 目标

将 Voice Lab 从"能跑通"提升到"可运维"：结构化日志、全链路追踪、Provider 调用审计、用量统计与报告分析。

## 设计原则

1. **P0 原则不变**：不引入 Redis / Kafka / ELK 等外部依赖，所有数据落 SQLite + 本地文件
2. **渐进增强**：现有 Service/Provider 代码改动最小化，通过中间件和装饰器注入能力
3. **结构化优先**：所有日志输出 JSON 格式，支持机器解析和后续接入外部系统
4. **零敏感数据**：日志中不得出现 API Key、完整音频数据、用户原文（仅保留 text_length）

---

## 模块拆解

### P3-A：结构化日志 + 请求上下文

**当前问题**：
- `app/core/logging.py` 只有 `basicConfig`，纯文本格式
- 无 request_id，无法关联同一请求的多条日志
- Provider API 调用完全静默（9 个外部 HTTP 调用无任何日志）
- 错误发生时无自动日志，仅依赖 Service 手动 `self.logger.error()`

**目标交付**：

#### A1：日志基础设施重构（`app/core/logging.py`）

重写 `setup_logging()` 和 `get_logger()`：

```python
# 输出格式：每行一个 JSON 对象
{
  "timestamp": "2026-05-11T14:30:00.123Z",
  "level": "INFO",
  "logger": "voice_render",
  "message": "render_success",
  "request_id": "req_abc123",
  "job_id": "job_xxx",
  "provider": "minimax",
  "model": "speech-2.8-hd",
  "duration_ms": 2340,
  "trace_id": "minimax_trace_xxx",
  "extra": {}
}
```

实现要求：
- 使用 `python-json-logger` 或手写 `logging.Formatter` 输出 JSON
- 支持 `LOG_LEVEL` 环境变量控制级别（默认 INFO）
- 支持 `LOG_FORMAT` 环境变量切换 `json` / `text`（开发时用 text 方便阅读）
- `get_logger(name)` 返回的 logger 支持 `extra` 关键字参数自动合并到 JSON
- 日志同时输出到 stdout 和按天轮转的文件（`logs/voice_lab_YYYY-MM-DD.log`）
- 日志文件保留天数可配置（默认 30 天）

新增配置项（`app/core/config.py`）：
```python
log_level: str = "INFO"
log_format: str = "json"           # "json" | "text"
log_dir: str = "./logs"
log_retention_days: int = 30
```

验收：
- `uvicorn` 启动后日志输出为 JSON（LOG_FORMAT=json）
- `logs/` 目录下按天生成日志文件
- 所有现有 `self.logger.info/error` 调用不报错（向后兼容）

#### A2：请求上下文中间件（`app/core/middleware.py`，新建）

FastAPI 中间件，为每个请求注入 `request_id`：

```python
# 中间件职责：
# 1. 生成 request_id（格式：req_ + 12位随机字符）
# 2. 存入 contextvars（全链路可读）
# 3. 注入 response header：X-Request-ID
# 4. 记录请求开始日志（method, path, client_ip）
# 5. 记录请求结束日志（status_code, duration_ms）
```

上下文传播机制（`app/core/context.py`，新建）：
```python
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def get_request_id() -> str:
    return request_id_var.get()
```

`get_logger()` 增强：返回的 logger 自动从 contextvars 读取 `request_id` 注入每条日志。

验收：
- 每个 API 请求的所有日志带相同 `request_id`
- Response header 包含 `X-Request-ID`
- 请求开始/结束各一条日志，包含 `method`、`path`、`status_code`、`duration_ms`

#### A3：Provider 调用日志（修改 `app/providers/minimax_speech_adapter.py`）

为所有 Provider HTTP 调用添加结构化日志，**不改变现有业务逻辑**：

每次 `httpx` 调用前后各记录一条日志：

```python
# 调用前（DEBUG 级别）
{"message": "provider_request", "provider": "minimax", "method": "POST", "path": "/v1/t2a_v2", "request_id": "req_xxx"}

# 调用后（INFO 级别）
{"message": "provider_response", "provider": "minimax", "method": "POST", "path": "/v1/t2a_v2", 
 "status_code": 200, "duration_ms": 1234, "trace_id": "xxx", "request_id": "req_xxx"}

# 调用失败（ERROR 级别）
{"message": "provider_error", "provider": "minimax", "method": "POST", "path": "/v1/t2a_v2",
 "error_type": "httpx.TimeoutException", "error_message": "...", "duration_ms": 30000, "request_id": "req_xxx"}
```

实现方式：在 `MiniMaxSpeechAdapter` 中增加一个私有方法 `_request(method, path, **kwargs)` 统一包装 httpx 调用，自动记录日志和计时。所有现有方法改为调用 `_request()` 而非直接用 `httpx.AsyncClient`。

验收：
- 每次 Provider API 调用产生 request + response 两条日志
- 超时/网络错误产生 error 日志
- 日志中不包含 API Key 或请求 body（body 可能含用户文本）

#### A4：错误处理增强（修改 `app/core/errors.py`）

在 `voice_lab_error_handler` 中自动记录错误日志：

```python
async def voice_lab_error_handler(request: Request, exc: VoiceLabError) -> JSONResponse:
    logger = get_logger("error_handler")
    logger.warning(
        "voice_lab_error",
        extra={
            "error_code": exc.code,
            "error_message": exc.message,
            "status_code": exc.status_code,
            "path": request.url.path,
        }
    )
    # ... 现有返回逻辑不变
```

同时为 unhandled exception 添加全局 500 handler：

```python
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_error", extra={"error_type": type(exc).__name__, "error_message": str(exc)})
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}})
```

验收：
- 所有 4xx 错误自动产生 WARNING 日志
- 未捕获异常产生 ERROR 日志 + 返回 500 统一格式
- 不泄露内部堆栈到客户端

---

### P3-B：Provider 调用审计表

**当前问题**：
- Provider API 调用记录分散在 VoiceJob.response_json 中
- 无法独立查询"某段时间内调了多少次 MiniMax API"
- Clone/Design/Delete 调用不经过 VoiceJob，完全无记录

**目标交付**：

#### B1：审计表模型（`app/models/provider_call_log.py`，新建）

```sql
CREATE TABLE provider_call_logs (
    id TEXT PRIMARY KEY,                -- calllog_xxx
    request_id TEXT,                    -- 关联 API 请求
    job_id TEXT,                        -- 关联 VoiceJob（可为空，clone/design/delete 无 job）
    provider TEXT NOT NULL,             -- "minimax"
    api_path TEXT NOT NULL,             -- "/v1/t2a_v2"
    method TEXT NOT NULL,               -- "POST"
    status_code INTEGER,               -- HTTP 状态码
    duration_ms INTEGER,               -- 调用耗时
    provider_trace_id TEXT,            -- Provider 返回的 trace_id
    usage_characters INTEGER,          -- 字符消耗量（T2A 场景）
    error_type TEXT,                    -- 异常类型（成功时为空）
    error_message TEXT,                -- 异常信息（成功时为空）
    created_at TEXT NOT NULL            -- ISO 时间戳
);

CREATE INDEX idx_call_logs_provider ON provider_call_logs(provider, created_at);
CREATE INDEX idx_call_logs_request ON provider_call_logs(request_id);
CREATE INDEX idx_call_logs_job ON provider_call_logs(job_id);
```

#### B2：审计记录写入

在 A3 的 `_request()` 方法中，调用完成后写入审计表。写入操作：
- 使用独立 Session（不影响业务事务）
- 写入失败只记日志，不影响业务流程

```python
# _request() 伪代码
async def _request(self, method, path, *, session=None, job_id=None, **kwargs):
    start = time.monotonic()
    try:
        resp = await client.request(method, url, **kwargs)
        self._log_call(session, method, path, resp.status_code, duration_ms, ...)
        return resp
    except Exception as exc:
        self._log_call(session, method, path, None, duration_ms, error=exc)
        raise
```

#### B3：审计查询 API（`app/api/admin.py`，新建）

```
GET /api/admin/call-logs?provider=minimax&start=2026-05-11&end=2026-05-12&limit=100
```

响应：
```json
{
  "logs": [
    {
      "id": "calllog_xxx",
      "request_id": "req_xxx",
      "job_id": "job_xxx",
      "provider": "minimax",
      "api_path": "/v1/t2a_v2",
      "status_code": 200,
      "duration_ms": 1234,
      "usage_characters": 50,
      "created_at": "2026-05-11T14:30:00Z"
    }
  ],
  "total": 42,
  "has_more": false
}
```

验收：
- 每次 Provider 调用自动写入 provider_call_logs 表
- `GET /api/admin/call-logs` 返回调用记录
- 支持按 provider / 时间范围 / job_id 过滤

---

### P3-C：用量统计与报告

**当前问题**：
- 无法回答"今天用了多少字符""本周生成了多少音频""哪个接口调用最多"
- 无法回答"平均耗时多少""错误率是多少"

**目标交付**：

#### C1：统计聚合 API（`app/api/admin.py` 扩展）

```
GET /api/admin/stats/summary?start=2026-05-01&end=2026-05-11
```

响应：
```json
{
  "period": {"start": "2026-05-01", "end": "2026-05-11"},
  "overview": {
    "total_jobs": 156,
    "success_jobs": 148,
    "failed_jobs": 8,
    "success_rate": 0.949,
    "total_characters": 23456,
    "total_audio_duration_ms": 1234567
  },
  "by_provider": {
    "minimax": {
      "api_calls": 210,
      "avg_duration_ms": 1850,
      "p95_duration_ms": 4200,
      "error_rate": 0.038,
      "characters_used": 23456
    }
  },
  "by_api": {
    "/v1/t2a_v2": {"calls": 120, "avg_ms": 2100, "errors": 3},
    "/v1/t2a_async_v2": {"calls": 30, "avg_ms": 800, "errors": 1},
    "/v1/voice_clone": {"calls": 5, "avg_ms": 3200, "errors": 0},
    "/v1/voice_design": {"calls": 8, "avg_ms": 2800, "errors": 2},
    "/v1/get_voice": {"calls": 15, "avg_ms": 600, "errors": 0}
  },
  "by_day": [
    {"date": "2026-05-01", "jobs": 12, "characters": 2345, "errors": 1},
    {"date": "2026-05-02", "jobs": 18, "characters": 3100, "errors": 0}
  ]
}
```

数据来源：
- `overview` → 聚合 `voice_jobs` 表
- `by_provider` / `by_api` → 聚合 `provider_call_logs` 表
- `by_day` → GROUP BY date(created_at)

#### C2：每日趋势 API

```
GET /api/admin/stats/daily?start=2026-05-01&end=2026-05-11&metric=characters
```

支持的 metric：`jobs`、`characters`、`errors`、`avg_duration`

响应：
```json
{
  "metric": "characters",
  "data": [
    {"date": "2026-05-01", "value": 2345},
    {"date": "2026-05-02", "value": 3100}
  ]
}
```

#### C3：报告页面（`app/static/admin.html`，新建）

独立的管理页面，路由 `/static/admin.html`，展示：

| 区域 | 内容 |
|------|------|
| 顶部概览卡片 | 总任务数、成功率、总字符数、总音频时长 |
| Provider 调用统计 | 按 API 分组的调用次数、平均耗时、错误率 |
| 每日趋势图 | 折线图：任务数 / 字符数 / 错误数 按天变化 |
| 最近调用记录 | 表格：最近 50 条 Provider 调用日志 |
| 错误列表 | 表格：最近失败的 job 和 provider 调用 |

技术：纯 HTML + CSS + JS（与现有 index.html 一致，无构建工具），用 `<canvas>` 或简单 SVG 画趋势图。

验收：
- 访问 `/static/admin.html` 展示统计面板
- 数据从 `/api/admin/stats/*` 和 `/api/admin/call-logs` 获取
- 支持选择日期范围

---

### P3-D：错误重试机制

**当前问题**：
- Provider 调用失败直接抛异常，无重试
- 临时网络抖动导致整个任务失败

**目标交付**：

#### D1：可重试装饰器（`app/core/retry.py`，新建）

```python
# 使用方式
@retry(max_attempts=3, backoff_base=1.0, retryable_exceptions=(httpx.TimeoutException, httpx.NetworkError))
async def _request(self, method, path, **kwargs):
    ...
```

策略：
- 指数退避：1s → 2s → 4s（`backoff_base * 2^attempt`）
- 可重试异常白名单：`TimeoutException`、`NetworkError`、HTTP 502/503/504
- 不重试：4xx 客户端错误、`ProviderError`（业务错误）
- 每次重试记录 WARNING 日志
- 最终失败记录 ERROR 日志（含总尝试次数）

新增配置项：
```python
provider_retry_max_attempts: int = 3
provider_retry_backoff_base: float = 1.0
```

#### D2：集成到 Provider Adapter

在 A3 实现的 `_request()` 方法上应用重试装饰器。对调用方透明。

验收：
- Provider 超时后自动重试，最多 3 次
- 重试日志可见（每次 attempt 一条 WARNING）
- 4xx 错误不重试
- 配置项可调

---

### P3-E：健康检查增强

**当前问题**：`GET /health` 只返回固定 `{"status": "ok"}`，不检查任何依赖

**目标交付**：

```
GET /health           # 快速探活（保持现有）
GET /health/detail    # 详细健康检查
```

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "checks": {
    "database": {"status": "healthy", "latency_ms": 2},
    "storage": {"status": "healthy", "free_space_mb": 5120},
    "minimax_api": {"status": "healthy", "last_call_at": "2026-05-11T14:30:00Z", "last_status_code": 200}
  }
}
```

- `database`：执行 `SELECT 1` 验证连接
- `storage`：检查 storage 目录存在且可写，报告剩余空间
- `minimax_api`：从 `provider_call_logs` 读最近一次调用状态（不主动发请求）

验收：
- `/health/detail` 返回各组件状态
- 任一组件异常时 overall status 变为 `degraded`

---

## 分轮实施计划

| 轮次 | 编号 | 内容 | 改动范围 |
|------|------|------|----------|
| 1 | A1 | 结构化日志基础设施 | `core/logging.py`, `core/config.py`, `requirements.txt` |
| 2 | A2 | 请求上下文中间件 | `core/middleware.py`(新), `core/context.py`(新), `main.py` |
| 3 | A3 | Provider 调用日志 | `providers/minimax_speech_adapter.py` |
| 4 | A4 | 错误处理增强 | `core/errors.py`, `main.py` |
| 5 | B1-B2 | 审计表 + 写入 | `models/provider_call_log.py`(新), adapter 集成 |
| 6 | B3 | 审计查询 API | `api/admin.py`(新), `api/__init__.py` |
| 7 | C1-C2 | 统计聚合 API | `services/stats_service.py`(新), `api/admin.py` |
| 8 | C3 | 报告面板 | `static/admin.html`(新) |
| 9 | D1-D2 | 错误重试 | `core/retry.py`(新), adapter 集成 |
| 10 | E | 健康检查增强 | `api/health.py` |

每轮交付包含：代码 + 对应测试 + `pytest -q` 全量通过。

---

## 新增依赖

```
python-json-logger>=3.0.0    # JSON 日志格式化（A1 需要）
```

仅增加 1 个依赖，保持轻量。

---

## 文件变更汇总

| 文件 | 操作 | 所属轮次 |
|------|------|----------|
| `app/core/logging.py` | 重写 | A1 |
| `app/core/config.py` | 增加配置项 | A1, D1 |
| `app/core/context.py` | 新建 | A2 |
| `app/core/middleware.py` | 新建 | A2 |
| `app/core/errors.py` | 修改 | A4 |
| `app/core/retry.py` | 新建 | D1 |
| `app/main.py` | 注册中间件/handler | A2, A4 |
| `app/providers/minimax_speech_adapter.py` | 增加 _request() | A3, B2, D2 |
| `app/models/provider_call_log.py` | 新建 | B1 |
| `app/api/admin.py` | 新建 | B3, C1, C2 |
| `app/api/__init__.py` | 注册 admin router | B3 |
| `app/api/health.py` | 扩展 | E |
| `app/services/stats_service.py` | 新建 | C1, C2 |
| `app/static/admin.html` | 新建 | C3 |
| `requirements.txt` | 增加依赖 | A1 |
| `tests/test_logging.py` | 新建 | A1 |
| `tests/test_middleware.py` | 新建 | A2 |
| `tests/test_provider_call_log.py` | 新建 | B1-B2 |
| `tests/test_admin_api.py` | 新建 | B3, C1 |
| `tests/test_retry.py` | 新建 | D1 |
| `tests/test_health_detail.py` | 新建 | E |

---

## 安全约束

- 日志中禁止出现：`MINIMAX_API_KEY`、`Authorization` header、音频 base64、用户原文
- 用户原文只记录 `text_length`，不记录内容
- `provider_call_logs` 不存储请求/响应 body
- Admin API 在 P3 暂无鉴权（后续 P4 可加 API Key 或 Basic Auth）
- 日志文件权限 600（仅 owner 可读）

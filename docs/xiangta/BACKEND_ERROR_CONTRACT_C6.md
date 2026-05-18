# P17 XiangTa Backend Error Contract C6

## 1. 阶段定位

### 当前问题

XiangTa API 错误响应尚未完全统一：

- `error_translator.py` 有 `XiangTaError` + `to_dict()`，但 `translate()` 覆盖不全
- `routes.py` 部分接口返回 `JSONResponse` + 平铺结构，部分用 `exc.to_dict()`
- Admin 接口错误结构不完全统一
- `CoreHttpClient` 对 network error 返回 generic `{"error": "network_error"}`，上下文丢失（CA-04）
- TTS task failed 状态的 errorKind / message / retryable 未统一
- LLM fallback 与真正错误未区分（影响 C5）
- Admin API 无鉴权 gate（CA-01）

### C6 目标

```
C6 只设计统一错误契约，不实现。
后续 C6-* 实现阶段再修改 error_translator.py / routes.py / CoreHttpClient / H5。
C9/C10/C11 按依赖拆入各自实现。
```

### C6 不修复的问题

```
CA-01: Admin 无鉴权 — C6 只设计契约，实现延后
CA-04: CoreHttpClient 错误上下文丢失 — C6 设计目标结构，实现延后
CA-06: H5 防重复点击 — C8 H5 Design Alignment 处理
```

---

## 2. 当前错误处理现状

### 2.1 error_translator.py

```python
class XiangTaError(Exception):
    kind: str
    message: str
    retryable: bool
    def to_dict(self) -> dict:  # 返回 {"ok": False, "errorKind": ..., "message": ..., "retryable": ...}

# 子类
QuotaExhaustedError   → errorKind="quota", retryable=False
NoProviderError       → errorKind="no_provider", retryable=True
InvalidInputError     → errorKind="invalid_input", retryable=False
TextTooLongError      → errorKind="text_too_long", retryable=False
PresetNotFoundError   → errorKind="preset_not_found", retryable=False
TtsFailedError        → errorKind="tts_failed", retryable=True
LlmFailedError        → errorKind="llm_failed", retryable=True
```

`translate()` 只处理 `XiangTaError` 和 `PresetMappingError`，其他全部 → `unknown`。

### 2.2 routes.py 现状

| Route | 错误处理方式 |
|---|---|
| `GET /core/profiles` | `list_core_profiles()` 返回 `{"profiles": [], "source": ...}` 降级，不抛异常 |
| `GET /bootstrap` | 直接返回，异常未捕获 |
| `GET /provider/status` | 直接返回，异常未捕获 |
| `POST /suggestions` | `ValueError` → `{"ok": False, "errorKind": "invalid_input", ...}` HTTP 400 |
| `POST /tts` | `XiangTaError` → `exc.to_dict()` HTTP 400 |
| `POST /letters` | 未捕获异常 |
| Admin routes | `_write_error_response()` → `not_found`/`validation_error`/HTTP 500 |
| `GET /letters` | 未捕获异常 |

### 2.3 CoreHttpClient 现状

```python
async def get(self, path: str) -> dict:
    except Exception as exc:
        logger.warning("Core HTTP GET %s failed: %s", path, exc)
        return {"error": "network_error", "detail": "Failed to reach Core"}
```

问题：
- 不区分网络超时、连接拒绝、HTTP 4xx/5xx
- 返回 dict 而不是抛异常，业务层无法区分错误类型
- CA-04 已登记

### 2.4 VoiceLabGateway 异常体系

```python
CoreRenderUnavailableError   # 无 client 注入
CoreRenderResponseError     # response 不匹配合约
CoreStatusUnavailableError
CoreStatusResponseError
CoreProfilesUnavailableError
CoreProfilesResponseError
```

### 2.5 TtsOrchestrator 异常转换

```python
except CoreRenderUnavailableError as exc:
    raise NoProviderError() from exc  # errorKind="no_provider"
except CoreRenderResponseError as exc:
    raise TtsFailedError() from exc   # errorKind="tts_failed"
```

### 2.6 C5 Copywriting 现状

- 当前模板文案不抛异常，直接返回 `SuggestionsData`
- C5 设计的 LLM 路径：`copywriting_timeout` / `copywriting_provider_error` / `copywriting_invalid_output`
- `fallbackToTemplate=true` 时这些不返回前端；`fallbackToTemplate=false` 时返回

### 2.7 Admin 现状

- `/admin/*` 无任何鉴权（CA-01）
- `_write_error_response()` 只处理 `ConfigNotFoundError` / `InvalidConfigInputError` 等 writer 异常
- 无 `features.adminEnabled` gate

---

## 3. 统一错误响应结构

### 3.1 推荐结构（嵌套 error 对象）

```json
{
  "ok": false,
  "error": {
    "errorKind": "provider_quota",
    "message": "语音生成额度暂时不可用，请稍后再试。",
    "retryable": true,
    "requestId": "req_a1b2c3d4e5f6",
    "taskId": null,
    "details": null
  }
}
```

### 3.2 兼容当前平铺结构

```json
{
  "ok": false,
  "errorKind": "provider_quota",
  "message": "语音生成额度暂时不可用，请稍后再试。",
  "retryable": true
}
```

### 3.3 字段定义

| 字段 | 类型 | 说明 |
|---|---|---|
| `ok` | `false` | 固定 false |
| `error.errorKind` | `string` | 稳定枚举，前端可判断 |
| `error.message` | `string` | 用户可理解文案，1-100字符 |
| `error.retryable` | `bool` | 是否建议稍后重试 |
| `error.requestId` | `string\|null` | 请求追踪 ID |
| `error.taskId` | `string\|null` | 关联 TTS task ID |
| `error.details` | `any\|null` | 开发态 detail，正式环境 null |

### 3.4 禁止返回字段

```
❌ stack trace
❌ API key / token
❌ provider raw response
❌ Core internal path / config
❌ binding detail / voice_id / model_id
❌ full prompt 原文
❌ database error message
❌ file path
```

### 3.5 迁移策略

```
阶段 1：新接口使用嵌套 error 对象
阶段 2：旧接口兼容平铺结构，逐步迁移
阶段 3：H5 统一使用 normalizeError(response) helper
```

**新接口定义**：C10 TTS Task API、C11 LLM Copywriting API。

---

## 4. 成功但业务状态失败的区别

### 4.1 API 调用失败

```json
{
  "ok": false,
  "error": {
    "errorKind": "validation_error",
    "message": "输入内容过长。",
    "retryable": false
  }
}
```

### 4.2 Task 查询成功，但任务失败

```json
{
  "ok": true,
  "data": {
    "taskId": "T_a1b2c3d4",
    "status": "failed",
    "errorKind": "provider_quota",
    "message": "语音生成额度暂时不可用，请稍后再试。",
    "retryable": true
  }
}
```

**关键语义**：GET `/tts/tasks/{taskId}` 查询到 `failed` task 时 `ok=true`。只有 task 不存在、无权限、参数错误时 `ok=false`。

---

## 5. errorKind 枚举设计

### 5.1 通用错误

| errorKind | 说明 | HTTP | retryable |
|---|---|---|---|
| `validation_error` | 输入校验失败 | 400 | false |
| `unauthorized` | 未认证 | 401 | false |
| `forbidden` | 无权限 | 403 | false |
| `not_found` | 资源不存在 | 404 | false |
| `rate_limited` | 速率限制 | 429 | true |
| `queue_full` | 队列满 | 429 | true |
| `conflict` | 状态冲突 | 409 | false |
| `timeout` | 通用超时 | 408 | true |
| `unknown` | 未知错误 | 500 | true |

### 5.2 Core / Gateway 错误

| errorKind | 说明 | HTTP | retryable |
|---|---|---|---|
| `core_unavailable` | Core 不可达 | 503 | true |
| `core_timeout` | Core 超时 | 408 | true |
| `core_bad_response` | Core 响应不符合合约 | 502 | true |
| `core_contract_mismatch` | Core 返回结构不匹配 | 502 | false |
| `core_asset_unavailable` | Core 资产 URL 不可用 | 502 | true |

### 5.3 TTS 错误

| errorKind | 说明 | HTTP | retryable |
|---|---|---|---|
| `profile_not_found` | profile 不存在 | 404 | false |
| `voice_binding_missing` | voice binding 缺失 | 404 | false |
| `voice_preset_not_found` | voice preset 不存在 | 404 | false |
| `voice_preset_disabled` | voice preset 已禁用 | 400 | false |
| `tone_preset_not_found` | tone preset 不存在 | 404 | false |
| `tone_preset_disabled` | tone preset 已禁用 | 400 | false |
| `tts_failed` | TTS 生成失败 | 500 | true |
| `tts_timeout` | TTS 超时 | 408 | true |
| `provider_quota` | Provider 额度不足 | 429 | false |
| `provider_error` | Provider 错误 | 502 | true |
| `no_provider` | 无可用 Provider | 503 | true |
| `cost_confirmation_required` | 需要费用确认 | 422 | false |
| `text_too_long` | 文案超长 | 400 | false |

### 5.4 Copywriting / LLM 错误

| errorKind | 说明 | HTTP | retryable | fallback |
|---|---|---|---|---|
| `copywriting_timeout` | LLM 超时 | 200 | true | template |
| `copywriting_provider_error` | Provider 错误 | 200 | true | template |
| `copywriting_invalid_output` | LLM 输出无效 | 200 | true | template |
| `copywriting_blocked` | 内容安全检查失败 | 200 | false | no |
| `copywriting_unavailable` | 文案服务不可用 | 503 | true | no |
| `llm_failed` | LLM 失败（遗留） | 500 | true | template |

### 5.5 Storage 错误

| errorKind | 说明 | HTTP | retryable |
|---|---|---|---|
| `storage_unavailable` | 存储不可用 | 503 | true |
| `storage_write_failed` | 写入失败 | 500 | false |
| `storage_read_failed` | 读取失败 | 500 | false |
| `migration_required` | 需要迁移 | 500 | false |
| `migration_failed` | 迁移失败 | 500 | false |

### 5.6 Admin / Config 错误

| errorKind | 说明 | HTTP | retryable |
|---|---|---|---|
| `admin_disabled` | Admin 接口未启用 | 403 | false |
| `admin_auth_required` | Admin 鉴权缺失 | 401 | false |
| `admin_forbidden` | Admin token 错误 | 403 | false |
| `config_validation_error` | 配置校验失败 | 422 | false |
| `config_write_failed` | 配置写入失败 | 500 | false |
| `config_read_failed` | 配置读取失败 | 500 | false |

### 5.7 Task 错误

| errorKind | 说明 | HTTP | retryable |
|---|---|---|---|
| `task_not_found` | Task 不存在 | 404 | false |
| `task_not_cancellable` | Task 不可取消 | 409 | false |
| `task_expired` | Task 已过期 | 404 | false |
| `task_already_completed` | Task 已完成 | 409 | false |
| `task_state_conflict` | Task 状态冲突 | 409 | false |
| `idempotency_conflict` | 幂等性冲突 | 409 | false |

### 5.8 errorKind 设计原则

```
errorKind 是稳定 contract，H5 和日志依赖它。
message 可以随产品文案调整，不影响前端逻辑。
同一 errorKind 在不同 API 中含义一致。
```

---

## 6. HTTP 状态码映射

| HTTP Status | errorKind 场景 |
|---|---|
| 400 | `validation_error`, `text_too_long`, `voice_preset_disabled`, `tone_preset_disabled` |
| 401 | `unauthorized`, `admin_auth_required` |
| 403 | `forbidden`, `admin_disabled`, `admin_forbidden` |
| 404 | `not_found`, `task_not_found`, `profile_not_found`, `voice_preset_not_found`, `tone_preset_not_found`, `task_expired` |
| 408 | `timeout`, `core_timeout`, `tts_timeout`, `copywriting_timeout` |
| 409 | `conflict`, `task_state_conflict`, `task_not_cancellable`, `task_already_completed`, `idempotency_conflict` |
| 422 | `contract_mismatch`, `cost_confirmation_required`, `config_validation_error` |
| 429 | `rate_limited`, `queue_full`, `provider_quota` |
| 500 | `unknown`, `tts_failed`, `storage_write_failed`, `config_write_failed`, `storage_read_failed`, `migration_failed` |
| 502 | `core_bad_response`, `core_contract_mismatch`, `provider_error`, `core_asset_unavailable` |
| 503 | `core_unavailable`, `no_provider`, `storage_unavailable`, `copywriting_unavailable` |

**说明**：
- HTTP status 给客户端和代理层使用
- errorKind 给前端产品逻辑使用
- message 给用户展示

---

## 7. retryable 语义

### 7.1 retryable=true

```
core_unavailable
core_timeout
core_bad_response
core_asset_unavailable
tts_timeout
tts_failed
provider_error
copywriting_timeout
copywriting_provider_error
copywriting_invalid_output
storage_unavailable
rate_limited
queue_full
unknown
```

### 7.2 retryable=false

```
validation_error
unauthorized
forbidden
admin_forbidden
admin_disabled
admin_auth_required
not_found
profile_not_found
voice_preset_not_found
voice_preset_disabled
tone_preset_not_found
tone_preset_disabled
text_too_long
copywriting_blocked
task_not_found
task_not_cancellable
task_expired
task_already_completed
task_state_conflict
idempotency_conflict
provider_quota  ⚠️ 见 7.3
config_validation_error
```

### 7.3 provider_quota 讨论

```
语义区分：
- 短时限流（分钟级）→ retryable=true
- 额度耗尽（日级）→ retryable=false

C6 设计建议：
errorKind 层面先保留 provider_quota，
后续实现时在 error.details 中区分：
  {"errorKind": "provider_quota", "details": {"type": "rate_limited"}}
  {"errorKind": "provider_quota", "details": {"type": "exhausted"}}
```

---

## 8. 用户 message 与内部 detail 边界

### 8.1 响应结构

```json
{
  "ok": false,
  "error": {
    "errorKind": "core_unavailable",
    "message": "语音服务暂时连接不上，请稍后再试。",
    "retryable": true,
    "requestId": "req_a1b2c3d4",
    "taskId": null,
    "details": null
  }
}
```

### 8.2 message 设计原则

```
- 简洁，1-100字符
- 无技术术语（不说 "CoreHttpClient"、"HTTP 502"、"SQLite"）
- 无内部字段名（不说 "coreProfileId"、"binding_id"）
- 无 API key / token
- 无 stack trace
- 提供解决方向（"请稍后再试"、"请检查输入"）
```

### 8.3 details 字段

```
正式环境：details = null（不返回任何技术细节）
开发态（dev mode）：details = {"coreStatusCode": 503, "safeDetail": "Core unreachable"}
details 只在确认安全时返回，不包含 stack trace / API key / prompt
```

### 8.4 内部日志字段（不返回前端）

```
request_id
task_id
user_id (nullable)
route
method
status_code
error_kind
retryable
latency_ms
core_status_code (nullable)
provider (nullable)
profile_id (nullable)
voice_preset (nullable)
copywriting_provider (nullable)
fallback_used (nullable)
exception_class
exc_message (stripped, no secrets)
```

---

## 9. requestId / taskId 设计

### 9.1 requestId 生成

```
每个 API 请求生成 requestId。
如果前端传 X-Request-Id header，校验后沿用；否则后端生成。
响应错误时必须返回 requestId。
日志必须包含 requestId。
格式：req_<12 random lowercase chars>
示例：req_a1b2c3d4e5f6
```

### 9.2 taskId 格式

```
TTS task 使用 T_<10 random chars>。
示例：T_a1b2c3d4e5
与 requestId 分别独立。
```

### 9.3 实现位置

```
C6 只设计。
后续实现：FastAPI middleware 生成 requestId → 注入 request state → 写入 log context。
不修改现有同步接口签名（向后兼容）。
```

### 9.4 多层级追踪

```
requestId：每个 HTTP 请求
taskId：TTS task 生命周期
两者可以同时出现在同一错误响应中。
```

---

## 10. Core / Gateway 错误映射

### 10.1 CoreHttpClient（CA-04 目标）

**当前**：`get/post` 捕获所有异常返回 `{"error": "network_error"}`

**C6 设计目标**：

```python
class CoreHttpError(Exception):
    kind: str          # "core_unavailable" | "core_timeout" | "core_bad_response"
    status_code: int | None
    safe_detail: str | None   # 不含 API key / stack trace

# get/post 改为抛异常，不返回 dict
async def get(self, path: str) -> dict:
    try:
        ...
    except httpx.TimeoutException as exc:
        raise CoreHttpError(kind="core_timeout", status_code=None, safe_detail="Core timed out")
    except httpx.ConnectError as exc:
        raise CoreHttpError(kind="core_unavailable", status_code=None, safe_detail="Cannot connect to Core")
    except httpx.HTTPStatusError as exc:
        raise CoreHttpError(kind="core_bad_response", status_code=exc.response.status_code, safe_detail=f"Core returned {exc.response.status_code}")
    except Exception as exc:
        raise CoreHttpError(kind="core_unavailable", status_code=None, safe_detail="Unexpected Core error")
```

**推荐方向**：内部抛异常，Gateway 捕获并转换。不要让业务层解析 dict error。

### 10.2 VoiceLabGateway 异常转换

| CoreHttpClient 抛出 | VoiceLabGateway 转换为 |
|---|---|
| `CoreHttpError(kind="core_unavailable")` | `CoreRenderUnavailableError` |
| `CoreHttpError(kind="core_timeout")` | `CoreRenderUnavailableError` |
| `CoreHttpError(kind="core_bad_response", status_code=...)` | `CoreRenderResponseError` |
| profiles parse fail | `CoreProfilesResponseError` |
| render response missing `audio_asset.url` | `CoreRenderResponseError` |
| render response `status != "success"` | `CoreRenderResponseError` |
| relative audio URL | normal path, 不报错 |

### 10.3 TtsOrchestrator 异常转换

| Gateway 异常 | TtsOrchestrator 转换为 |
|---|---|
| `CoreRenderUnavailableError` | `NoProviderError` → `errorKind="no_provider"` |
| `CoreRenderResponseError` | `TtsFailedError` → `errorKind="tts_failed"` |
| `PresetMappingError` | `PresetNotFoundError` → `errorKind="preset_not_found"` |
| `TextTooLongError` | 透传 → `errorKind="text_too_long"` |

### 10.4 避免重复包装

```
后续 C6 实现需注意：不要在多个层级重复包装同一异常，导致 errorKind 丢失或重复翻译。
推荐路径：CoreHttpClient → 抛 CoreHttpError → VoiceLabGateway 捕获 → 抛 VoiceLabGateway 异常 → TtsOrchestrator 捕获 → 抛 XiangTaError → routes 捕获 → 返回 JSONResponse
```

---

## 11. TTS Task 错误映射（对齐 C4）

### 11.1 创建 Task 时（POST /tts/tasks）

| 错误条件 | 行为 |
|---|---|
| `validation_error` | 不创建 task，ok=false，HTTP 400 |
| `queue_full` | 不创建 task，ok=false，HTTP 429 |
| `rate_limited` | 不创建 task，ok=false，HTTP 429 |
| `voice_preset_not_found` | 不创建 task，ok=false，HTTP 404 |
| `no_provider` | 不创建 task，ok=false，HTTP 503 |

### 11.2 Task 执行时（worker）

| 错误条件 | Task status | errorKind | retryable |
|---|---|---|---|
| `core_unavailable` | `failed` | `core_unavailable` | true |
| `provider_quota` | `failed` | `provider_quota` | false |
| `provider_error` | `failed` | `provider_error` | true |
| `tts_timeout` | `failed` | `tts_timeout` | true |
| `unknown` | `failed` | `unknown` | true |

### 11.3 查询 Task 时（GET /tts/tasks/{taskId}）

| 情况 | 响应 |
|---|---|
| task 存在且 `status=failed` | `ok=true`, `data.status=failed`, `errorKind`, `message`, `retryable` |
| task 不存在 | `ok=false`, `errorKind=task_not_found`, HTTP 404 |
| task 属于其他 user | `ok=false`, `errorKind=forbidden`, HTTP 403 |
| task 已 `completed` | `ok=true`, `data.status=completed` |
| task 已 `cancelled` | `ok=true`, `data.status=cancelled` |
| task 已 `expired` | `ok=true`, `data.status=expired` |

---

## 12. Copywriting / LLM 错误映射（对齐 C5）

### 12.1 fallbackToTemplate=true（默认）

| LLM 错误 | HTTP | ok | 行为 |
|---|---|---|---|
| `copywriting_timeout` | 200 | true | fallback，source=template，fallbackUsed=true |
| `copywriting_provider_error` | 200 | true | fallback，source=template，fallbackUsed=true |
| `copywriting_invalid_output` | 200 | true | fallback，source=template，fallbackUsed=true |

### 12.2 fallbackToTemplate=false

| LLM 错误 | HTTP | ok | errorKind |
|---|---|---|---|
| `copywriting_timeout` | 200 | false | `copywriting_timeout` |
| `copywriting_provider_error` | 200 | false | `copywriting_provider_error` |
| `copywriting_invalid_output` | 200 | false | `copywriting_invalid_output` |

### 12.3 不 fallback 的情况

| 情况 | HTTP | ok | errorKind | 原因 |
|---|---|---|---|---|
| `validation_error` | 400 | false | `validation_error` | 输入非法，不 fallback |
| `copywriting_blocked` | 200 | false | `copywriting_blocked` | 内容不适合生成，是否 fallback 需要产品策略 |

### 12.4 copywriting_blocked 策略

```
copywriting_blocked 默认不 fallback。
返回 ok=false，给用户安全文案："这段内容暂时不适合生成文案，请换一种表达。"
可选：在 details 中记录 blocked 原因（不返回前端）。
```

---

## 13. Storage 错误映射（对齐 C3）

| 存储错误 | errorKind | HTTP | retryable |
|---|---|---|---|
| SQLite 文件不存在 / 无法打开 | `storage_unavailable` | 503 | true |
| 写入失败 | `storage_write_failed` | 500 | false |
| 读取失败 | `storage_read_failed` | 500 | false |
| 需要迁移 | `migration_required` | 500 | false |
| 迁移失败 | `migration_failed` | 500 | false |

### 13.1 Letter 保存失败

```
Letter 保存失败时：
- 音频已生成，仍可播放（audioUrl 已在 TtsData 中）
- 返回 letter 保存失败提示，不阻塞音频播放
- 建议：TTS 响应和 Letter 保存分开处理，不要级联失败
```

### 13.2 错误消息示例

```
storage_unavailable → "数据服务暂时不可用，请稍后再试。"
storage_write_failed → "保存失败，请重试。"
```

---

## 14. Admin / Config 错误与安全边界

### 14.1 两阶段策略

**阶段 1（MVP / local dev）**：

```python
# runtime_config.features.adminEnabled = false
# 或 XIANGTA_ADMIN_ENABLED=false
```

所有 `/admin/*` 返回：

```json
{
  "ok": false,
  "error": {
    "errorKind": "admin_disabled",
    "message": "管理接口未启用。",
    "retryable": false
  }
}
```

HTTP 403。

**阶段 2（local admin token）**：

```bash
XIANGTA_ADMIN_TOKEN=<secure-random-token>
Header: X-XiangTa-Admin-Token: <token>
```

未提供 header：

```json
{
  "ok": false,
  "error": {
    "errorKind": "admin_auth_required",
    "message": "请提供管理员凭证。",
    "retryable": false
  }
}
```

HTTP 401。

Token 错误：

```json
{
  "ok": false,
  "error": {
    "errorKind": "admin_forbidden",
    "message": "管理员凭证无效。",
    "retryable": false
  }
}
```

HTTP 403。

### 14.2 C6 不实现

```
C6 只设计 Admin 错误契约。
不实现 Admin 鉴权 middleware。
Admin 鉴权实现可在 C6-7 或独立安全任务中处理。
正式用户系统前，Admin API 不应暴露公网。
```

---

## 15. H5 错误展示策略

### 15.1 错误分类与展示方式

| errorKind | 展示位置 | 方式 | 示例文案 |
|---|---|---|---|
| `validation_error` | 表单下方 | 红色提示 | "输入内容过长，请缩短后再试。" |
| `core_unavailable` | 结果区 | 错误卡片+重试按钮 | "语音服务暂时连接不上，请稍后再试。" |
| `provider_error` | 结果区 | 错误卡片+重试按钮 | "语音生成失败了，可以重试一次。" |
| `tts_timeout` | 结果区 | 错误卡片+重试按钮 | "语音生成超时了，请稍后再试。" |
| `provider_quota` | 结果区 | 温和提示 | "当前语音额度暂时不可用，请稍后再试。" |
| `queue_full` | 结果区 | 温和提示 | "当前生成任务较多，请稍后再试。" |
| `rate_limited` | 结果区 | 温和提示 | "操作太频繁了，请稍后再试。" |
| `copywriting_blocked` | 文案区 | 温和提示 | "这段内容暂时不适合生成文案，请换一种表达。" |
| `copywriting_fallback` | 文案区 | 正常展示（dev 模式可显示 badge） | 不打扰用户 |
| `storage_write_failed` | 保存区 | Toast 提示 | "保存失败，但音频已生成。" |
| `admin_disabled` | — | H5 普通用户不应触发 | N/A |
| `admin_auth_required` | — | H5 普通用户不应触发 | N/A |
| `task_not_found` | 结果区 | 提示+返回 | "未找到对应任务。" |
| `no_provider` | 结果区 | 错误卡片+重试 | "声音服务暂时连接不上，请稍后再试。" |

### 15.2 重试策略

```
H5 收到 retryable=true 错误时：
- 显示"重试"按钮
- 禁用相关操作按钮
- 重试时带上 X-Request-Id 以便关联日志

H5 收到 retryable=false 错误时：
- 显示错误文案
- 不显示"重试"按钮
- 引导用户修正输入（validation_error）或联系支持（其他）
```

### 15.3 Copywriting fallback 展示

```
dev 模式：suggestions 卡片显示"模板生成"badge
正式模式：不显示 source 信息，用户无感知
用户选择 suggestion 后正常填入 TTS
```

---

## 16. Observability / Logging

### 16.1 日志字段

```json
{
  "request_id": "req_a1b2c3d4e5f6",
  "task_id": "T_a1b2c3d4",
  "user_id": null,
  "route": "/api/xiangta/tts",
  "method": "POST",
  "status_code": 200,
  "error_kind": null,
  "retryable": null,
  "latency_ms": 1234,
  "core_status_code": null,
  "provider": null,
  "profile_id": "deep_night_programmer",
  "voice_preset": "female-gentle",
  "tone_preset": "gentle",
  "copywriting_provider": null,
  "fallback_used": false,
  "request_size_bytes": 256,
  "response_size_bytes": 1024
}
```

### 16.2 敏感字段处理

```
✅ 记录：request_id, task_id, route, error_kind, latency_ms, voice_preset, tone_preset
❌ 不记录：raw_text 内容（只记录长度和 hash）
❌ 不记录：prompt 原文
❌ 不记录：API key / token
❌ 不记录：Core internal error body
```

### 16.3 日志级别

```
INFO: 成功请求
WARN: retryable 错误（core_unavailable, provider_error 等）
ERROR: 非预期异常、storage 错误
```

---

## 17. API Contract 迁移策略

### 17.1 现状

当前部分接口返回平铺结构：

```json
{"ok": false, "errorKind": "...", "message": "...", "retryable": true}
```

### 17.2 目标结构

```json
{"ok": false, "error": {"errorKind": "...", "message": "...", "retryable": true, "requestId": "...", "taskId": null, "details": null}}
```

### 17.3 迁移路径

```
阶段 1（不破坏现有接口）：
- 新增 XiangTaError.to_dict_v2() → 嵌套结构
- requestId 通过 middleware 生成

阶段 2（新接口使用新结构）：
- C10 TTS Task API 使用嵌套结构
- C11 LLM Copywriting API 使用嵌套结构

阶段 3（逐步迁移旧接口）：
- routes.py 逐个接口改为返回 to_dict_v2()

阶段 4（H5 统一）：
- H5 使用 normalizeError(response) helper
- 同时兼容平铺和嵌套结构
```

### 17.4 H5 normalizeError helper

```javascript
function normalizeError(response) {
  // 兼容平铺和嵌套结构
  if (response.error) {
    return {
      ok: false,
      errorKind: response.error.errorKind,
      message: response.error.message,
      retryable: response.error.retryable,
      requestId: response.error.requestId || null,
      taskId: response.error.taskId || null,
    };
  }
  // 兼容旧平铺结构
  return {
    ok: response.ok,
    errorKind: response.errorKind,
    message: response.message,
    retryable: response.retryable,
    requestId: null,
    taskId: null,
  };
}
```

---

## 18. 错误映射总表

| Source | 原始条件 | errorKind | HTTP | retryable | User message |
|---|---|---|---|---|---|
| Validation | `rawText` 为空 | `validation_error` | 400 | false | "输入内容不能为空。" |
| Validation | `rawText` 超长 | `validation_error` | 400 | false | "输入内容过长，请缩短后再试。" |
| Validation | 无效 `recipient` | `validation_error` | 400 | false | "选择的对象类型无效。" |
| Core | CoreHttpClient `ConnectError` | `core_unavailable` | 503 | true | "语音服务暂时连接不上，请稍后再试。" |
| Core | CoreHttpClient `TimeoutException` | `core_timeout` | 408 | true | "语音服务响应超时，请稍后再试。" |
| Core | Core 返回非 2xx | `core_bad_response` | 502 | true | "语音服务响应异常，请稍后再试。" |
| Core | render response `status != "success"` | `tts_failed` | 500 | true | "生成声音时遇到了问题，可以再试一次。" |
| Provider | Provider 返回 quota 错误 | `provider_quota` | 429 | false | "当前语音额度暂时不可用，请稍后再试。" |
| Provider | Provider 其他错误 | `provider_error` | 502 | true | "语音生成失败了，可以重试一次。" |
| TTS | 渲染超时 | `tts_timeout` | 408 | true | "语音生成超时了，请稍后再试。" |
| Copywriting | LLM 超时 | `copywriting_timeout` | 200 | true | fallback |
| Copywriting | LLM provider error | `copywriting_provider_error` | 200 | true | fallback |
| Copywriting | LLM invalid JSON | `copywriting_invalid_output` | 200 | true | fallback |
| Copywriting | 内容被拦截 | `copywriting_blocked` | 200 | false | "这段内容暂时不适合生成文案，请换一种表达。" |
| Copywriting | validation error | `validation_error` | 400 | false | "输入内容无效。" |
| Storage | SQLite 不可用 | `storage_unavailable` | 503 | true | "数据服务暂时不可用，请稍后再试。" |
| Storage | 写入失败 | `storage_write_failed` | 500 | false | "保存失败，请重试。" |
| Storage | 读取失败 | `storage_read_failed` | 500 | false | "读取数据失败，请重试。" |
| Admin | `features.adminEnabled=false` | `admin_disabled` | 403 | false | "管理接口未启用。" |
| Admin | 无 token header | `admin_auth_required` | 401 | false | "请提供管理员凭证。" |
| Admin | token 错误 | `admin_forbidden` | 403 | false | "管理员凭证无效。" |
| Admin | 配置校验失败 | `config_validation_error` | 422 | false | "配置格式无效。" |
| Admin | 配置写入失败 | `config_write_failed` | 500 | false | "保存配置失败。" |
| Task | task 不存在 | `task_not_found` | 404 | false | "未找到对应任务。" |
| Task | task 不可取消 | `task_not_cancellable` | 409 | false | "该任务当前无法取消。" |
| Task | task 已过期 | `task_expired` | 404 | false | "该任务已过期。" |
| Task | task 已完成 | `task_already_completed` | 409 | false | "该任务已完成。" |
| Queue | 队列满 | `queue_full` | 429 | true | "当前生成任务较多，请稍后再试。" |
| Rate | 速率限制 | `rate_limited` | 429 | true | "操作太频繁了，请稍后再试。" |
| Unknown | 其他未捕获异常 | `unknown` | 500 | true | "出了点小问题，可以再试一次。" |

---

## 19. 示例响应

### 19.1 validation_error

```json
{
  "ok": false,
  "error": {
    "errorKind": "validation_error",
    "message": "输入内容过长，请缩短后再试。",
    "retryable": false,
    "requestId": "req_f1e2d3c4b5a6",
    "taskId": null,
    "details": null
  }
}
```

### 19.2 core_unavailable

```json
{
  "ok": false,
  "error": {
    "errorKind": "core_unavailable",
    "message": "语音服务暂时连接不上，请稍后再试。",
    "retryable": true,
    "requestId": "req_a1b2c3d4e5f6",
    "taskId": null,
    "details": null
  }
}
```

### 19.3 provider_quota

```json
{
  "ok": false,
  "error": {
    "errorKind": "provider_quota",
    "message": "当前语音额度暂时不可用，请稍后再试。",
    "retryable": false,
    "requestId": "req_b2c3d4e5f6a1",
    "taskId": null,
    "details": null
  }
}
```

### 19.4 copywriting fallback success

```json
{
  "ok": true,
  "data": {
    "summary": "表达想念与牵挂",
    "intent": "miss",
    "suggestions": [...],
    "source": "template",
    "fallbackUsed": true
  }
}
```

### 19.5 task failed data response

```json
{
  "ok": true,
  "data": {
    "taskId": "T_a1b2c3d4e5",
    "status": "failed",
    "errorKind": "provider_quota",
    "message": "当前语音额度暂时不可用，请稍后再试。",
    "retryable": false
  }
}
```

### 19.6 admin_disabled

```json
{
  "ok": false,
  "error": {
    "errorKind": "admin_disabled",
    "message": "管理接口未启用。",
    "retryable": false,
    "requestId": "req_c3d4e5f6a1b2",
    "taskId": null,
    "details": null
  }
}
```

### 19.7 unknown

```json
{
  "ok": false,
  "error": {
    "errorKind": "unknown",
    "message": "出了点小问题，可以再试一次。",
    "retryable": true,
    "requestId": "req_d4e5f6a1b2c3",
    "taskId": null,
    "details": null
  }
}
```

---

## 20. 测试设计建议

C11 实现时需要覆盖的测试点：

### 通用

```
validation_error returns HTTP 400
unknown exception returns unknown without stack trace
error response never contains API key
error response never contains stack trace
error response never contains provider raw response
requestId appears in error response when generated
```

### Core / Gateway

```
Core unavailable → errorKind="core_unavailable"
Core timeout → errorKind="core_timeout"
Core bad response → errorKind="core_bad_response"
VoiceLabGateway parse fail → CoreProfilesResponseError
```

### TTS

```
CoreRenderUnavailableError → errorKind="no_provider"
CoreRenderResponseError → errorKind="tts_failed"
PresetNotFoundError → errorKind="preset_not_found"
TextTooLongError → errorKind="text_too_long"
```

### TTS Task（C10 实现时）

```
Task not found → ok=false, errorKind="task_not_found", HTTP 404
Task belongs to another user → ok=false, errorKind="forbidden", HTTP 403
Task status=failed → ok=true, data.status=failed
Task not cancellable → errorKind="task_not_cancellable"
```

### Copywriting / LLM（C11 实现时）

```
copywriting_timeout fallbackToTemplate=true → ok=true, source=template, fallbackUsed=true
copywriting_provider_error fallback → ok=true, source=template
copywriting_invalid_output fallback → ok=true
fallbackToTemplate=false + LLM error → ok=false, errorKind
validation_error → ok=false, no fallback
copywriting_blocked → ok=false, errorKind="copywriting_blocked"
charCount 由后端计算
```

### Admin

```
features.adminEnabled=false → admin_disabled, HTTP 403
Admin missing token → admin_auth_required, HTTP 401
Admin wrong token → admin_forbidden, HTTP 403
```

### Storage（C9 实现时）

```
Storage write failure → errorKind="storage_write_failed"
Storage unavailable → errorKind="storage_unavailable"
```

---

## 21. 实现阶段拆分

| 阶段 | 任务 | 类型 | 依赖 |
|---|---|---|---|
| C6 | Backend Error Contract Design | **Design（当前）** | — |
| C6-1 | Error Schema & errorKind Enum | Implementation | C6 ✅ |
| C6-2 | requestId middleware/helper | Implementation | C6-1 |
| C6-3 | CoreHttpClient structured error | Implementation | C6-1 |
| C6-4 | Gateway error mapping | Implementation | C6-3 |
| C6-5 | TTS task error integration | Implementation | C10 |
| C6-6 | Copywriting fallback/error integration | Implementation | C11 |
| C6-7 | Admin gate design implementation | Implementation | C6-1 |
| C6-8 | H5 normalizeError adapter | Implementation | C8 |
| C7 | Profile Mapping Design | Design | C6 ✅ |
| C8 | H5 Design Alignment | Design | C6 ✅, C7 ✅ |
| C9 | Storage Foundation | Implementation | C6-1 ✅ |
| C10 | TTS Task MVP | Implementation | C6-1 ✅, C9 |
| C11 | LLM Copywriting MVP | Implementation | C6-1 ✅, C9, C10 |

**说明**：
- C6-1 errorKind enum 是所有实现的基石
- C6-3 CoreHttpClient structured error 解 CA-04
- C6-7 Admin gate 解 CA-01
- C6 实现完成后不建议立刻实现所有 C6-*，建议先 C7/C8 再按依赖拆入

---

## 22. 交叉引用

- **C1 Backend Capability Plan**：定义了 error handling 需求
- **C2 Runtime Config**：features.adminEnabled 是 Admin gate 的配置基础
- **C3 Storage Design**：storage 错误映射基础
- **C4 TTS Task Orchestration**：task failed 状态与 errorKind 对齐
- **C5 Copywriting LLM Design**：LLM fallback 与 errorKind 对齐
- **C2A CA-01**：Admin 无鉴权，deferred to C6/C7
- **C2A CA-04**：CoreHttpClient 错误上下文，deferred to C6
- **C7 Profile Mapping Design**：依赖 C6 errorKind
- **C8 H5 Design Alignment**：依赖 C6 errorKind 和 H5 normalizeError
- **C10 TTS Task MVP**：依赖 C6-1 errorKind + C6-5
- **C11 LLM Copywriting MVP**：依赖 C6-1 + C6-6

---

## 23. 关键设计决策总结

| 决策 | 选择 | 原因 |
|---|---|---|
| 新接口使用嵌套 error 对象 | ✅ | 扩展性强，future-proof |
| 旧接口保留平铺结构 | ✅ | 向后兼容，不破坏现有 H5 |
| errorKind 是稳定 contract | ✅ | H5 和日志依赖，不随 message 文案变化 |
| stack trace / API key 不返回前端 | ✅ | 安全边界 |
| Task failed status 用 ok=true | ✅ | 查询成功，任务状态是业务数据 |
| LLM 技术失败 fallback to template | ✅ | 前端体验稳定，不报错 |
| validation_error / copywriting_blocked 不 fallback | ✅ | 输入非法不应 fallback |
| Admin gate 先用 env flag | ✅ | MVP 最简方案 |
| requestId 通过 middleware 生成 | ✅ | 非侵入，不改接口签名 |
| CoreHttpClient 改为抛异常 | ✅ | 业务层可区分错误类型，CA-04 修复 |

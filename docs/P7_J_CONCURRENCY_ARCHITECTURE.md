# P7-J0 并发架构问题归纳与轻量策略

---

## 1. 当前背景

P7-I 已完成真实 MiniMax 主链路验证与修复收口，当前后台核心能力基本稳定。

已完成能力包括：

- 同步 T2A 可用
- 异步 T2A 可用
- WebSocket 流式可用
- 批量长文本 / 批量剧本可用
- 字幕、资产下载、历史记录可用
- Resource Guard 已接入
- Admin 统计主问题已修复
- Smoke runner 已完成
- 当前无 P0/P1 阻塞

本阶段要把讨论过的并发问题正式归档，包括：

- 并发能力边界
- 前端误点 / 连点问题
- 刷新后重复提交问题
- 多浏览器 / 多窗口 / 多用户访问问题
- Resource Guard 能力边界
- 多 worker / 多进程风险
- SQLite 并发风险
- 本地 App / SaaS / BYOK 产品形态对并发架构的影响

---

## 2. 当前总体判断

当前系统已经具备基础并发保护能力，但不是完整的多用户高并发生产架构。

| 使用场景 | 当前状态 |
|---|---|
| 单用户顺序使用 | 基本稳定 |
| 小规模多浏览器 / 多用户轻量使用 | 有基础保护，可用 |
| 高并发多人使用 | 未系统验证 |
| 正式 SaaS 多用户生产环境 | 还需要用户体系、幂等、队列、数据库升级等能力 |

当前并发架构属于：

- 单进程
- 小规模
- operation 级
- 拒绝型限流模型

系统现有"保护阀"，还不是"队列调度系统"。

---

## 3. 当前并发运行模型

```
浏览器请求 → FastAPI/Uvicorn → async service → Resource Guard → MiniMax Provider → SQLite → 响应
```

- HTTP 请求由 FastAPI / Uvicorn 处理
- Provider HTTP 调用是 async I/O
- WebSocket 流式是 async I/O
- 数据库当前是同步 SQLModel Session
- 如果使用 SQLite，多并发写入可能存在 `database is locked` 风险

---

## 4. 多个请求同时运行时链路是否可靠

正常情况下，多个 HTTP 请求不会串线。

原因：

- 每个 HTTP 请求有自己的 coroutine
- 每个请求有自己的局部变量
- `await` 返回时恢复原 coroutine
- `job_id` 独立
- `provider_task_id` 独立
- `ContextVar` 按异步上下文隔离
- `ProviderCallLog` / `AudioAsset` / `VoiceJob` 通过 `job_id` 关联

### 4.1 同步 T2A 链路

```
HTTP 请求 → 创建 VoiceJob → 设置 job_id context → await render_sync → 保存 AudioAsset → 返回
```

### 4.2 异步 T2A 链路

Submit 阶段：

```
HTTP 请求 → 创建 VoiceJob → await create_async_task → 保存 provider_task_id → 返回 job_id
```

Query 阶段：

```
前端拿 job_id 查询 → 后台找 VoiceJob → await query_async_task → 保存结果 → 返回状态
```

### 4.3 WebSocket 流式链路

```
WebSocket 连接 → 创建 VoiceJob → 设置 job_id context → async for chunk in render_stream → 每个 chunk 通过同一 WebSocket 返回 → 保存完整音频
```

---

## 5. 当前 Resource Guard 并发控制

Resource Guard 的性质：

- 进程内内存级并发控制
- provider + operation 维度
- `asyncio.Lock` + active counter
- 超限直接拒绝
- 不排队
- 不持久化
- 不做 Redis / 分布式锁

Resource Guard 当前解决的问题：

- 防止同时过多请求打 MiniMax
- 防止高成本能力无限并发
- 防止流式连接过多
- 防止批量任务同时放大 provider 调用
- 超过限制时返回 `RESOURCE_LIMIT_EXCEEDED`

Resource Guard 当前不是：

- 用户级并发限制
- 队列型调度
- 多进程全局限流
- 分布式并发控制

---

## 6. 当前 operation 并发策略

| Operation | 当前性质 | 当前策略 |
|---|---|---|
| `t2a_sync` | 同步生成，直接占 provider 调用 | 保守限制 |
| `t2a_async_submit` | 创建 MiniMax 异步任务 | 可适当放开，但仍需限制 |
| `t2a_async_query_download` | 查询 / 下载异步任务，可能触发 provider query | 退避轮询 + guard |
| `t2a_stream` | WebSocket 长连接 | 严格限制 |
| `voice_preview` | 音色试听 | 中等限制 |
| `voice_variants` | 一次请求放大多个 T2A | 严格限制 |
| `batch_longtext` | 批量入口 | 严格限制 |
| `batch_script` | 批量剧本入口 | 严格限制 |
| `voice_design` | 高成本能力 | 暂缓 / 严格限制 |
| `voice_clone_*` | 高成本能力 | 暂缓 / 严格限制 |

当前限制可以逐步调大，但必须按 operation 分开调，不应全局一把放开。

---

## 7. 多进程 / 多 worker 风险

Resource Guard 是进程内内存计数。

如果启动多个 worker（如 `uvicorn --workers 4`），每个 worker 都有自己的 Resource Guard 实例：

| 配置 | 结果 |
|---|---|
| `t2a_sync limit = 2` | 单 worker 下最多 2 个 |
| `workers = 4` | 实际可能变成 2 × 4 = 8 个 |

建议：

- 小规模阶段建议单 worker 部署，更可控
- 如果需要多 worker / 多机器，需要 Redis / 分布式锁 / 全局计数器

---

## 8. 多浏览器 / 多用户接入时的判断

多个浏览器、多个窗口、多个人访问时，前端按钮锁不再有效，真正起作用的是后端 Resource Guard。

- 小规模多浏览器 / 多用户请求：有基础保护
- 超过 Resource Guard 限制：返回 `RESOURCE_LIMIT_EXCEEDED`
- 多用户请求不会直接打爆 provider
- 没有用户级公平调度和队列

**当前是全局 operation 级限流，不是用户级限流。**

---

## 9. 前端误点与系统并发的区别

### 9.1 前端误点 / 连点

场景：同一个页面、同一按钮、用户连续点击。

当前可用轻量策略：

- 按钮 loading 状态
- 按钮短暂禁用
- 请求返回后恢复
- 异步任务提交成功后展示任务卡片

解决的是单页面误点问题。

### 9.2 多入口并发

场景：多个浏览器、多个窗口、多人同时访问、脚本直接请求接口。

不能靠前端按钮锁，需要：

- Resource Guard
- 任务状态机
- 后端限流
- 数据库稳定性
- Provider 并发控制

---

## 10. 刷新后重新提交的问题

用户提交任务后刷新页面，再次点击生成，可能出现：

- 重复创建 VoiceJob
- 重复调用 MiniMax
- 重复消耗 token
- 历史记录出现重复任务

### 10.1 异步任务

如果已经拿到 `job_id`，任务可通过历史记录或 status 查询恢复。如果 submit 已到后端但前端刷新前没拿到 `job_id`，任务可能已创建但前端丢失追踪。

### 10.2 同步任务

如果请求期间刷新，后端可能已成功保存 asset 但前端没收到结果，再次提交可能重复消耗 token。

### 10.3 当前轻量建议

P8 可用 localStorage 保存最近任务信息（`job_id`、`batch_id`、创建时间、文本预览、当前状态），刷新后提示"检测到上次未完成任务，是否继续查看？"

当前不建议马上做完整幂等表。

---

## 11. 幂等机制是否现在必须做

完整方案包括：

- `client_request_id`
- `Idempotency-Key`
- `idempotency_records` 表
- `operation + client_request_id` 唯一约束
- running / success / failed 状态返回策略

**当前判断**：当前产品还未进入高并发 / 多用户生产阶段，不建议立刻做完整幂等系统。

**当前建议**：

- 先做前端轻量防误点
- 异步 / 批量任务 localStorage 恢复
- 继续依赖 Resource Guard
- 把完整幂等机制记录为后续阶段

---

## 12. 并发与产品形态的关系

### 12.1 本地 App + 用户自己的 MiniMax Token

- 每个用户本地运行，使用自己的 API Key
- 用户自己的本地数据库和资产
- 并发压力分散，不需要我们承担 token 成本
- 适合个人创作者和开发者
- 问题：用户需要懂 API Key，安装和配置体验要做好

### 12.2 Web SaaS + 平台 Key

- 用户直接使用平台能力，所有请求集中到服务器
- 所有 token 成本和并发压力由平台承担
- 需要：登录、额度、计费、幂等、用户级并发限制、队列、worker、PostgreSQL / Redis

### 12.3 BYOK Web 版

用户在网页中提供自己的 MiniMax API Key。

需要：

- 用户 / session 体系
- credential 加密存储
- 按 `credential_id` 做 Resource Guard
- 并发限制变成 `provider + credential_id + operation`

### 12.4 开放 API 平台

复杂度最高，需要：开发者 API Key、鉴权、QPS、额度、计费、幂等、队列、监控、错误码规范、滥用防护。

**当前不建议做。**

---

## 13. 当前阶段策略

**当前不做**：

- 复杂并发架构
- 完整队列 worker
- 完整用户体系
- 开放 API 平台
- BYOK 密钥管理
- 多租户计费

**当前采用**：

- 前端轻量防误点
- Resource Guard 全局 operation 限流
- 异步轮询退避
- 批量入口限制
- 流式连接限制
- 文档明确小规模使用边界

---

## 14. 如果大模型并发能力更强，是否可以调大限制

可以逐步调大，但不能一把放开。

原则：

- 按 operation 调整
- 一次只调一个入口
- 从 1 / 2 调到 3 / 5，小步调整
- 观察错误率、耗时、`database locked`、stuck job、WebSocket 断开、音频保存失败

可以优先调大：

- 异步 submit
- 异步 query / download
- voice preview

谨慎调大：

- 同步 T2A
- WebSocket stream
- batch execute
- voice variants

暂不调大：

- voice clone
- voice design

---

## 15. 当前能力边界总结

当前系统支持基础并发。

并发控制是：

- 单进程
- operation 级
- 拒绝型限流

**小规模多浏览器 / 多用户访问相对安全。**

**当前不承诺高并发多人 SaaS 能力。**

当出现以下情况时，应进入更强并发架构阶段：

- 多人经常撞到 Resource Guard
- 重复提交明显浪费 token
- SQLite 出现 `database is locked`
- 批量任务互相影响
- MiniMax 错误率升高
- 准备对外开放注册
- 准备做 Web SaaS 或开放 API

届时再考虑：

- session / user 体系
- 幂等记录表
- 任务队列
- 后台 worker
- Redis 全局限流
- PostgreSQL
- 用户额度和计费

---

## 16. P8 相关建议

P8 应聚焦产品化，不应马上扩张复杂后端并发架构。

**P8 建议做**：

- 前端产品化
- 音色选择 / 试听工作台
- 任务卡片
- 历史记录和下载体验
- 本地 App / Web App 路线设计
- localStorage 最近任务恢复
- 按钮级防误点
- cost estimate debounce
- profiles 缓存

**P8 不建议做**：

- 完整高并发架构
- 开放 API
- 复杂用户系统
- 大规模队列 worker
- BYOK 密钥管理
- 多租户计费
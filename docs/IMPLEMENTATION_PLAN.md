# Voice Lab 实现计划

## 开发原则

P0 只做模块化单体，不做微服务、用户系统、计费系统、复杂前端、队列 Worker 或 Redis。

开发顺序必须先保证 Mock Provider 跑通，再接 MiniMax 真实调用。

## P0 任务拆解

### 1. 项目启动骨架 ✅ 已完成

目标：

- 创建 `app/main.py`
- 注册 FastAPI 应用
- 注册错误处理器
- 启动时创建数据库表
- 启动时写入默认 seed profile 和 binding

验收：✅

```text
uvicorn app.main:app --reload
GET /health -> {"status": "ok"}
```

### 2. API 路由 ✅ 已完成

目标：

- `app/api/health.py`
- `app/api/voice_profiles.py`
- `app/api/voice_render.py`
- `app/api/voice_variants.py`
- `app/api/voice_jobs.py`
- `app/api/voice_assets.py`

验收：✅

- API 层只调用 service，不直接拼 Provider 请求。
- 所有响应遵守 README 中的结构。

### 3. 数据库与必要 Repository ✅ 已完成

目标：

- P0 所需数据库表已创建。
- P0 已实现 `voice_profile_repo.py`，job、asset、variant 当前由 service/API 直接使用 SQLModel session。
- 保持业务逻辑主要在 service 层。
- 所有 JSON 字段统一用 `json.dumps(..., ensure_ascii=False)` 存储。

验收：✅

- seed 数据只在数据库为空时写入。
- 不重复创建默认 profile。
- job、asset、variant repository 可在 P1 或服务复杂度上升时补齐。

### 4. 单条语音生成 ✅ 已完成

目标：

- `POST /api/voice/render`
- 使用 `VoiceRenderService`
- 支持 `provider=mock`
- 支持显式 `provider=minimax`
- 保存 `AudioAsset`
- 可选保存 `SubtitleAsset`
- 更新 `VoiceJob` 状态

验收：✅

- Mock 请求成功返回 `job_id` 和 `audio_asset.url`。
- profile 不存在返回 `PROFILE_NOT_FOUND`。
- text 为空返回统一 `VALIDATION_ERROR` 格式。
- MiniMax API Key 缺失且请求 MiniMax 返回 `PROVIDER_NOT_CONFIGURED`。

### 5. 多版本试音 ✅ 已完成

目标：

- `POST /api/voice/variants/render`
- 默认串行生成。
- 默认组合：
  - `speed=0.85, emotion=sad`
  - `speed=0.92, emotion=calm`
  - `speed=1.00, emotion=neutral`

验收：✅

- 返回 `group_id`。
- 每个 variant 都有对应 `job_id`、`audio_asset_id`、`audio_url`。

### 6. 资产下载 ✅ 已完成

目标：

- `GET /api/voice/assets/{asset_id}`
- `GET /api/voice/assets/{asset_id}/download`
- 支持 audio asset 和 subtitle asset。

验收：✅

- 文件不存在返回 `ASSET_NOT_FOUND`（已修复 500 -> 404）。
- 下载接口返回文件流。

### 7. pytest ✅ 已完成

最低测试：

- `GET /health` ✅
- 文本预处理能插入停顿 ✅
- `RenderPlan` 能正确生成 ✅
- `MockSpeechAdapter` 能返回假音频资产 ✅
- `POST /api/voice/render` 使用 mock provider 成功 ✅
- profile 不存在返回错误 ✅
- text 为空返回错误 ✅

测试要求：✅

- 不依赖真实 MiniMax API。
- 测试数据库使用临时 SQLite。
- 测试 storage 使用临时目录。

pytest -q 结果：`82 passed`（含 P1 集成审查轮新增测试）

## P1 计划：Voice Catalog（MiniMax Get Voice）✅ 已完成

> 完成 commit：`6dee90f`，pytest -q：`23 passed`，真实验收：`total=304`，`by_type={'system':303,'voice_cloning':1}`

### 功能边界

**做：**
- MiniMax Get Voice 只读同步：`POST /v1/get_voice`，`voice_type=all`
- 将音色列表同步落库为 `provider_voices` 表
- 提供 `GET /api/voice/provider-voices?provider=minimax&voice_type=all&refresh=false`
- 支持 `refresh=true` 强制从 MiniMax 重新拉取并 upsert

**不做：**
- Delete Voice / Update Voice
- Voice Clone / Voice Design
- 不做启动自动同步（P1 初版仅 refresh=true 时请求 Provider，refresh=false 只读缓存，缓存为空返回空列表）
- 前端试音台
- 多 Provider 真实接入

---

### 推荐 API

```
GET /api/voice/provider-voices?provider=minimax&voice_type=all&refresh=false
```

**不推荐** `GET /api/voice/providers/minimax/voices`。

原因：
- Voice Lab 上层不应绑定 MiniMax 路由
- 未来可扩展 `provider=openai/elevenlabs/azure`，API 层保持通用
- Provider Adapter 内部做厂商翻译，API 层无 Provider 特定逻辑

**请求参数：**
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `provider` | string | required | `minimax` |
| `voice_type` | string | `all` | `system` / `voice_cloning` / `voice_generation` / `all` |
| `refresh` | bool | `false` | `true`=强制从 Provider 拉取 |

**响应结构：**
```json
{
  "provider": "minimax",
  "voice_type": "all",
  "voices": [
    {
      "id": "pv_xxx",
      "provider": "minimax",
      "provider_voice_id": "English_expressive_narrator",
      "voice_type": "system",
      "name": "English Expressive Narrator",
      "description": "Expressive English narration voice",
      "language": "en",
      "gender": "female",
      "status": "available",
      "provider_created_time": "2024-01-15T10:00:00Z"
    }
  ],
  "synced_at": "2026-05-11T12:00:00Z",
  "total": 1
}
```

**错误响应：**
- `400` / `PROVIDER_NOT_CONFIGURED`：MiniMax API Key 缺失
- `502` / `PROVIDER_ERROR`：Provider 调用失败

---

### 内部标准对象

**ProviderVoice（domain 层）：**
```python
class ProviderVoice(BaseModel):
    id: str                          # 内部 ID，pv_xxx
    provider: str                    # "minimax"
    provider_voice_id: str           # MiniMax 原始 voice_id
    voice_type: str                  # "system" / "voice_cloning" / "voice_generation"
    name: str                        # voice_name
    description: str | None           # MiniMax description
    language: str | None             # 从 name/description 推断或 MiniMax 返回
    gender: str | None               # 从 name/description 推断或 MiniMax 返回
    status: str                      # "available"（Delete 时为 "deprecated"）
    provider_created_time: str | None # MiniMax created_time
    metadata_json: str = "{}"        # 原始额外字段
    synced_at: str                   # 最后同步时间
    created_at: str
    updated_at: str
```

---

### 数据库设计

**provider_voices 表：**
```sql
CREATE TABLE provider_voices (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    provider_voice_id TEXT NOT NULL,
    voice_type TEXT NOT NULL,
    name TEXT,
    description TEXT,
    language TEXT,
    gender TEXT,
    status TEXT DEFAULT "available",
    provider_created_time TEXT,
    metadata_json TEXT DEFAULT "{}",
    synced_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(provider, provider_voice_id)
);
```

**索引：** `(provider, voice_type)` 加速按类型筛选。

---

### Provider Adapter 设计

**`MiniMaxSpeechAdapter.list_voices(voice_type: str = "all")`**

MiniMax 端点：
```
POST {MINIMAX_BASE_URL}/v1/get_voice
Body: {"voice_type": voice_type}
```

转换规则（MiniMax 返回 → ProviderVoice）：

| MiniMax 路径 | ProviderVoice 字段 |
|---|---|
| `system_voice[].voice_id` | `provider_voice_id`，`voice_type="system"` |
| `voice_cloning[].voice_id` | `provider_voice_id`，`voice_type="voice_cloning"` |
| `voice_generation[].voice_id` | `provider_voice_id`，`voice_type="voice_generation"` |
| `voice_name` | `name` |
| `description` | `description` |
| `created_time` | `provider_created_time` |

注意：MiniMax 原始返回中 `language` / `gender` 字段可能不存在，需从 `voice_name` / `description` 推断或置空。

**Mock 实现：**
- 返回 2-3 条固定 mock 数据
- 支持 `voice_type` 过滤

---

### Service 层设计

**新增 `VoiceCatalogService`（`app/services/voice_catalog_service.py`）：**

```python
class VoiceCatalogService:
    async def list_provider_voices(
        session,
        provider: str,
        voice_type: str = "all",
        refresh: bool = False,
    ) -> ProviderVoiceListResponse:
        if refresh:
            # 1. 调 Provider Adapter.list_voices()
            # 2. upsert provider_voices 表（对返回的每条 voice 执行 insert or update）
            # 3. 将本地已有但本次未返回的同 provider voice 标记 status=deprecated
            # 4. 更新 synced_at
            # 5. 返回

        # refresh=false:
        # 1. 从 provider_voices 表查询（status=available）
        # 2. 若缓存为空，返回空列表，synced_at=null
        # 3. 返回
```

**缓存策略：**
- `refresh=false` 时优先读数据库缓存，返回 `status=available` 的记录
- 缓存为空（表无记录）时返回空列表，`synced_at=null`，不自动触发 refresh
- `refresh=true` 时强制从 Provider 拉取，对返回的每条 voice 执行 upsert，并将本地已有但本次未返回的同 provider voice 标记 `status=deprecated`（不物理删除，避免破坏 VoiceBinding 历史引用）
- 后续可增加 `auto_refresh` 配置开关

---

### 测试设计

**禁止请求真实 MiniMax，所有测试使用 Mock。**

| 测试 | 说明 |
|---|---|
| `test_provider_voice_model` | ProviderVoice schema 构造和验证 |
| `test_mock_list_voices` | MockSpeechAdapter.list_voices() 返回非空列表 |
| `test_voice_catalog_from_cache` | 不调 Provider，直接从库查缓存 |
| `test_voice_catalog_refresh` | refresh=true 触发 upsert |
| `test_provider_voices_api` | `GET /api/voice/provider-voices?provider=mock` 返回 200 |
| `test_provider_voices_minimax_not_configured` | 无 key 时返回 `PROVIDER_NOT_CONFIGURED` |
| `test_voice_type_filter` | `voice_type=system` 只返回 system 音色 |

MiniMax 适配器响应转换用 `unittest.mock.patch` 或 `httpx.MockTransport`：
```python
@pytest.mark.asyncio
async def test_minimax_voice_type_conversion():
    with patch.object(MiniMaxSpeechAdapter, 'list_voices', mock_voice_response):
        result = await service.list_provider_voices(session, "minimax", refresh=True)
        assert all(v.voice_type in ["system", "voice_cloning", "voice_generation"] for v in result.voices)
```

---

### 分轮实现计划

**第 1 轮：数据模型 + Schema**
- 新建 `app/models/provider_voice.py`（SQLModel 表）
- 新建 `app/domain/schemas.py` 新增 `ProviderVoice`、`ProviderVoiceListResponse` schema
- 新建 `app/repositories/provider_voice_repo.py`（upsert / list / get_by_provider）
- 验收：`pytest tests/test_provider_voice.py -v` 通过

**第 2 轮：Mock Adapter + Service**
- `MockSpeechAdapter.list_voices()` 实现（返回固定 mock 数据，支持 voice_type 过滤）
- 新建 `app/services/voice_catalog_service.py`
- 验收：`pytest tests/test_voice_catalog.py -v` 通过

**第 3 轮：API 端点**
- 新建 `app/api/provider_voices.py`
- 注册到 `app/api/__init__.py`
- 验收：`GET /api/voice/provider-voices?provider=mock` 返回 200，`?provider=minimax` 无 key 返回 400

**第 4 轮：MiniMax 适配器（人工验证）**
- `MiniMaxSpeechAdapter.list_voices()` 实现 `POST /v1/get_voice` 请求和响应转换
- 测试用 `@patch` 模拟，不请求外网
- 人工验证：设置真实 `MINIMAX_API_KEY` 后 `GET /api/voice/provider-voices?provider=minimax&refresh=true` 返回音色列表

---

### 风险

1. **MiniMax 字段不确定**：官方 `language` / `gender` 可能不在返回中，需容错处理
2. **voice_cloning / voice_generation 可能为空**：需处理空列表情况
3. **API Key 权限不足**：T2A Key 可能不支持 Voice Management API，需明确错误
4. **不写入测试或文档**：严禁真实 token 进入代码或文档

---

### 开放问题

1. MiniMax 返回中是否已有 `language` / `gender` 字段？需官方文档确认
2. `voice_type=all` 时三个分组的 voice_id 是否可能重复？需确认唯一性
3. 音色是否支持分页？单次请求可能返回数百条

---

## P1 其他计划（Voice Catalog 之后）

- 支持 MiniMax `output_format=url` 时自动下载并落地。
- 支持字幕 JSON / SRT 更完整解析。
- 增加简单旁白试音台前端。
- 增加 Provider 能力注册表。

## P1 VoiceBinding 管理 API ✅ 已完成

> 完成 commit：`e7aa95d`，pytest -q：`77 passed`

### 功能边界

**做：**
- VoiceBinding CRUD 管理：GET/POST/PATCH/DELETE
- binding 软删除（status=deprecated）
- duplicate 检查：profile_id + provider + model + provider_voice_id
- provider_voice 可用性验证（必须存在且 status=available）
- 跨 profile 绑定同一 provider_voice_id（不同 profile 不冲突）
- binding 列表排除 deprecated 状态

**不做：**
- render API 直接接受 provider_voice_id（必须通过 binding）
- binding 使用统计
- binding 操作审计日志
- 物理删除（只做软删除）
- 前端音色选择 UI

---

### 推荐 API

```
GET  /api/voice/profiles/{profile_id}/bindings
POST /api/voice/profiles/{profile_id}/bindings
PATCH /api/voice/bindings/{binding_id}
DELETE /api/voice/bindings/{binding_id}
```

---

### 请求/响应结构

**VoiceBindingCreate（POST body）：**
```json
{
  "provider": "minimax",
  "model": "speech-2.8-hd",
  "provider_voice_id": "Voice_Alpha",
  "params": {"speed": 0.88},
  "priority": 1
}
```

**VoiceBindingRead（响应）：**
```json
{
  "id": "binding_xxx",
  "profile_id": "profile_xxx",
  "provider": "minimax",
  "model": "speech-2.8-hd",
  "provider_voice_id": "Voice_Alpha",
  "provider_voice_name": "Voice Alpha",
  "params": {"speed": 0.88},
  "priority": 1,
  "status": "available",
  "created_at": "2026-05-11T12:00:00Z",
  "updated_at": "2026-05-11T12:00:00Z"
}
```

**错误响应：**
- `404` / `PROFILE_NOT_FOUND`：profile 不存在
- `404` / `BINDING_NOT_FOUND`：binding 不存在
- `422` / `VALIDATION_ERROR`：duplicate binding 或 provider_voice 不可用

---

### 数据库设计

**voice_bindings 表（当前 SQLModel 实际字段）：**
```sql
CREATE TABLE voice_bindings (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    provider_voice_id TEXT NOT NULL,
    params_json TEXT DEFAULT '{}',
    priority INTEGER DEFAULT 1,
    status TEXT DEFAULT 'available',
    created_at TEXT,
    updated_at TEXT
);
```

当前 P1 没有新增数据库唯一约束或迁移脚本；重复绑定由 `VoiceBindingService` 在创建/更新时做服务层校验，检查范围为 `profile_id + provider + model + provider_voice_id`。后续如果引入 Alembic 或生产级并发写入，再评估是否增加数据库唯一索引。

---

### 核心设计约束

1. **render API 不直接接受 provider_voice_id**：上层业务通过 binding 配置音色，不直接传递 voice_id
2. **provider_voice 必须可用**：创建/更新 binding 时验证 provider_voice 存在且 status=available
3. **duplicate 检查范围**：同一 profile 内 (provider + model + provider_voice_id) 不可重复
4. **跨 profile 不冲突**：同一 provider_voice_id 可绑定到不同 profile
5. **软删除策略**：DELETE 只设置 status=deprecated，不物理删除
6. **binding ID 全局唯一**：使用 new_id("binding")，不依赖 voice_id 派生

## P1 集成一致性审查 ✅ 已完成

> 完成 commit：`2412dfe`，pytest -q：`82 passed`

### 审查目标

确认 render 链路是否真正遵守 VoiceBinding 管理结果，并补齐缺失的防护和测试。

### 完成项

| 项目 | Commit | 说明 |
|---|---|---|
| priority tiebreaker | `932bd91` | ORDER BY priority, created_at 防止同 priority 时行为不确定 |
| binding 选择测试 | `4f0d622` | T1: 全 deprecated → 404, T2: 多 binding 按 priority, T3: deprecated 被跳过 |
| BindingStatus 枚举 | `f093f10` | 替代魔法字符串，统一 voice_profile_repo 和 voice_binding_repo 查询条件 |
| job binding_id | `5d6325f` | VoiceJob 记录实际选用的 binding，提高可观测性 |
| voice_params 白名单 | `2a3fbc7` | RenderPlan validator 过滤非法 key，防止数据注入到 Provider API |
| Provider 枚举 + 错误码 | `2412dfe` | 未知 provider 返回 400 UNSUPPORTED_PROVIDER，不再误用 BINDING_NOT_FOUND |

### 非阻断遗留

- ProviderVoice status 仍用魔法字符串（独立领域，后续可独立枚举化）
- mock fallback 逻辑（provider=mock 时 fallback 到 minimax binding）建议后续加配置开关

---

## P2 计划 ✅ 主体已完成

### P2-A: 异步长文本T2A ✅
- 枚举/Schema/Config扩展（`01eb244`）
- Provider基类 + Mock异步实现（`e5d49d8`）
- MiniMax异步Adapter（`cbb9ba5`）
- AsyncRenderService（`d12d1df`）
- API端点 + 测试（`508242f`）
- 前端异步UI（`924fa0f`）

### P2-C: Voice Clone ✅
- Schema/Config/Provider基类（`f78439f`）
- MiniMax/Mock Adapter（`b44859a`）
- Service + API + 测试（`9ab6291`）

### P2-D: Voice Design ✅
- Schema/Config/Adapter（`76b27ac`）
- Service + API + 测试（`9ed1e6a`）

### P2-B: Voice Delete ✅
- 全栈实现（`82dce61`）

### P2-F: 统一测试面板 ✅
- 4-Tab前端（`bb862d7`）

### P2-E: T2A WebSocket（已移至 P4 完成）
- 独立为 P4 实现，含完整 WebSocket 流式链路

### 未纳入P2的项目
- 多用户、额度统计、API Key管理、对象存储、队列Worker、评测反馈、视频模块

---

## P3 计划 ✅ 已完成

### P3-A: 结构化日志 + 请求上下文 ✅
- A1: 结构化日志基础设施（JSON/text 双格式 + TimedRotatingFileHandler）（`04e1f87`）
- A2: 请求上下文中间件（request_id contextvars + ASGI 原生中间件）（`736f0f6`）
- A3: Provider 调用日志（_request() 统一包装 9 个 HTTP 调用）（`0e7b5c1`）
- A4: 错误处理增强（自动日志 + unhandled 500 + ASGI 重写）（`4ff5d20`）

### P3-B: Provider 调用审计 ✅
- B1-B2: 审计表模型 + 自动写入（provider_call_logs 表）（`d554353`）
- B3: 审计查询 API（GET /api/admin/call-logs 过滤/分页）（`9b95d78`）

### P3-C: 用量统计与报告 ✅
- C1-C2: 统计聚合 API（summary + daily trend）（`7dec9ca`）
- C3: 管理面板 admin.html（Canvas 折线图 + 统计表格）（`872e12b`）

### P3-D: 错误重试 ✅
- D1-D2: 指数退避重试（1s→2s→4s，502/503/504 + 超时/网络错误）（`fd402e6`）

### P3-E: 健康检查增强 ✅
- 数据库/存储/Provider 三维检查（GET /health/detail）（`9bedc54`）

pytest：181 passed, 6 skipped (e2e)

---

## P4 计划 ✅ 已完成

### P4-A: Provider 基类 + WebSocket 适配器 ✅
- StreamAudioChunk 模型 + SpeechProvider.render_stream() 签名（`ebec791`）
- MiniMax WebSocket 适配器（WSS 连接 + task_start/continue/finish 协议）
- Mock 流式适配器（3 chunk 模拟）
- WebSocket 配置项（ws_url / ws_model / ws_timeout）
- websockets>=13.0 依赖

### P4-B: StreamRenderService ✅
- StreamRenderRequest schema + JobType.stream_render 枚举（`2b6b710`）
- 流式 Service：验证 → RenderPlan → VoiceJob → yield started/audio_chunk/completed
- 音频 chunk 拼接保存为 AudioAsset
- 错误 yield error 事件 + job 状态更新

### P4-C: WebSocket API 端点 ✅
- `/api/voice/ws/render` WebSocket 端点（`9e90e3e`）
- 消息协议：start → connected → started → audio_chunk × N → completed
- 输入校验（event 类型、text 非空、text 长度 ≤ 10000）
- 错误处理（VoiceLabError / 通用异常 / 客户端断连）

### P4-D: 前端流式播放器 ✅
- T2A Tab 新增"流式生成"radio 选项（`d7ef300`）
- WebSocket 连接 + 实时进度（片段计数 / 累计时长）
- base64 chunk 拼接为 Blob URL 一次性播放
- 服务端下载 + 本地缓存下载双链接

### P4-E: 集成测试 + Bug 修复 ✅
- 8 个端到端集成测试（`8a52ac8`）
- 修复 ws_render.py error_code 属性名不一致 bug
- ws_patched_session fixture 解决 WS 端点 session 隔离

pytest：206 passed, 6 skipped (e2e)

---

## P5 计划 ✅ 已完成

### Hotfix: 流式错误 detail 传播 ✅
- ws_render.py + stream_render_service.py: error 事件拼接 exc.detail（`64666cb`）
- minimax_speech_adapter.py: task_failed 时记录完整 status_msg 和 base_resp

### P5-A: T2A 参数调节 + 流式 UI 修正 ✅
- VoiceRenderRequest / StreamRenderRequest 新增 speed/vol/pitch/emotion（`d859397`）
- voice_render.py 提取 voice_overrides 传给 service
- 前端：音频格式下拉框、语音参数控件、流式模式隐藏字幕

### P5-B: 绑定管理 Tab ✅
- 第 5 个 Tab：查询/创建/删除 VoiceBinding（`9d80517`）
- 表格展示 + JSON 参数校验 + 创建后自动刷新列表

### P5-C: 音色列表增强 ✅
- 搜索过滤（name/voice_id/description）+ 一键绑定到人设（`4085a15`）
- 前端截断显示前 50 条 + renderVoiceTable 复用

### P5-D: 历史记录 + Job 列表 API ✅
- GET /api/voice/jobs 列表端点（过滤/分页）（`f6617a6`）
- T2A Tab 可折叠历史记录 + 加载更多
- 4 个测试

pytest：210 passed, 6 skipped (e2e)

## 禁止事项

- 不要把 MiniMax API Key 写死在代码里。
- 不要让上层业务直接传 MiniMax `voice_setting`。
- 不要跳过 `RenderPlan`。
- 不要删除 Mock Provider。
- 不要把音频二进制塞进数据库。
- 不要让测试依赖真实外部 API。
- 不要在日志中打印 Authorization。

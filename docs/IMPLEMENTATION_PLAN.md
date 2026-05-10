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

pytest -q 结果：`11 passed`

## P1 计划：Voice Catalog（MiniMax Get Voice）

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

## P2 计划

- Voice Design。
- 异步长文本 T2A。
- Voice Clone。
- 多用户。
- 额度统计。
- API Key 管理。
- 对象存储。
- 队列 Worker。
- 评测反馈系统。
- 视频模块集成。

## 禁止事项

- 不要把 MiniMax API Key 写死在代码里。
- 不要让上层业务直接传 MiniMax `voice_setting`。
- 不要跳过 `RenderPlan`。
- 不要删除 Mock Provider。
- 不要把音频二进制塞进数据库。
- 不要让测试依赖真实外部 API。
- 不要在日志中打印 Authorization。

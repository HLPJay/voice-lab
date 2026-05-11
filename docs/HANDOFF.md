# 当前收尾与接手说明

## 本轮已完成

本轮已经完成目标归档和架构文档，并创建了部分 P0 后端代码骨架。

已创建的主要文件：

```text
voice_lab/.env.example
voice_lab/requirements.txt
voice_lab/app/core/*
voice_lab/app/domain/*
voice_lab/app/models/*
voice_lab/app/providers/*
voice_lab/app/services/*
voice_lab/app/utils/*
voice_lab/docs/*
voice_lab/README.md
```

## 当前代码状态

P0 后端已达到可运行基线（commit `5b8d731`）。
P1 T2A HTTP 增强已完成（commit `0e5177a`）。
P1 VoiceBinding 管理 API 已完成（commit `e7aa95d`）。
P2 异步 T2A 已完成（commit `924fa0f`）。
P2 Voice Clone 已完成（commit `9ab6291`）。
P2 Voice Design 已完成（commit `9ed1e6a`）。
P2 Voice Delete 已完成（commit `82dce61`）。
P2 统一测试面板已完成（commit `bb862d7`）。

已验证：
- pytest 116/116 通过
- uvicorn 可正常启动
- Mock Provider 完整闭环
- 所有 P0+P1+P2 接口和错误边界验收通过
- 前端 4-Tab 面板（T2A生成 / 音色管理 / 声音克隆 / 声音设计）

## 已有代码可复用点

### 配置

`app/core/config.py` 已定义：

- APP 配置
- SQLite URL
- MiniMax API 配置
- storage 配置
- Mock Provider 开关

### 数据模型

`app/models/` 已包含：

- `VoiceProfile`
- `VoiceBinding`
- `VoiceJob`
- `AudioAsset`
- `SubtitleAsset`
- `VoiceVariantGroup`
- `VoiceVariant`

### Provider

`app/providers/base.py` 已定义 Provider 抽象接口和标准 `ProviderRenderResult`。

`MockSpeechAdapter` 已能生成静音 wav 文件。

`MiniMaxSpeechAdapter` 已实现同步 T2A 请求体转换、hex/url 音频保存的初版逻辑。

### 服务层

已有草稿：

- `TextPreprocessService`
- `AssetService`
- `VoiceProfileService`
- `VoiceRenderService`
- `VoiceVariantService`

这些服务需要在 API 接入后再做一轮启动验证和测试修正。

## 必须优先补齐的文件

以下文件在 P0 阶段已实现并验收通过：

```text
app/main.py                  ✅
app/api/__init__.py          ✅
app/api/health.py            ✅
app/api/voice_profiles.py    ✅
app/api/voice_render.py      ✅
app/api/voice_variants.py    ✅
app/api/voice_jobs.py        ✅
app/api/voice_assets.py      ✅
tests/                       ✅ (11 tests passing)
```

## 潜在注意点

1. `VoiceRenderService` 通过 `Depends(get_session)` 注入 session，已正确接入 API。
2. `TextPreprocessService` 对 9500 字符以上同步文本做拒绝，返回 VALIDATION_ERROR。
3. `MockSpeechAdapter` 返回 wav 文件，`RenderPlan.audio_params.format` 仍为 mp3；不影响 mock 闭环。
4. MiniMax 字幕返回结构已验证：`data.subtitle_file` 为 OSS URL，`_extract_timeline_from_subtitle_file` 已支持下载 + JSON 解析 sentences/items/timeline。
5. 错误处理器已注册到 FastAPI app。
6. pytest 和 uvicorn 启动验证均已通过。

## 交接标准（P0 已达到）

```text
uvicorn app.main:app --reload
GET /health -> {"status":"ok","app":"Voice Lab"}
POST /api/voice/render provider=mock -> success
storage/audio/YYYY-MM-DD/ 下生成文件
pytest -q -> 11 passed
```

## 非阻断问题（已知）

1. Windows 终端可能显示 UTF-8 字幕内容为乱码（GBK 终端编码），文件本身 UTF-8 正常

## P1 Voice Catalog 已完成

MiniMax Voice Management / Provider Voice Catalog 已完成实现（commit `6dee90f`）。

**已实现功能：**
- `GET /api/voice/provider-voices?provider=minimax&voice_type=all&refresh=true`
- `provider_voices` 表（含 upsert + deprecated 标记策略）
- `VoiceCatalogService`（缓存优先，refresh=true 强制拉取）
- `MiniMaxSpeechAdapter.list_voices()` 真实调用

**真实验收结果：**
- `refresh=true&provider=minimax` 返回 `total=304`
- `by_type={'system':303,'voice_cloning':1}`
- pytest -q: `23 passed`

**注意：** 自动测试不请求真实 MiniMax，真实验收需在 `.env` 配置 `MINIMAX_API_KEY`。

**风险（已知）：**
- language/gender 字段：MiniMax Get Voice 返回中暂无稳定字段，当前标准响应中保留为 null，不做自动推断

## P1 T2A HTTP 增强已完成

T2A 响应解析硬化已完成（commit `0e5177a fix: harden minimax t2a response parsing`）。

**已修复问题：**
- `output_format=url` 时 MiniMax 仍返回 `data.audio`（hex），`data.audio_url` 不存在；Voice Lab 优先 `audio_url` 下载，hex 为 fallback
- `data.audio` 奇长度 hex 字符串导致 `binascii.unhexlify` 崩溃 → 改为先校验再解码，非法时抛 ProviderError
- `data.subtitle_file` 是 URL 字符串，非内嵌 dict/list；需下载后解析 JSON

**真实验收结果（output_format=url）**：
- audio_asset 创建：✅（71412 bytes，file exists）
- subtitle_asset 创建：✅（timeline 1 条）
- subtitle json/srt 文件存在：✅
- `data.audio` 存在：`true`（hex）
- `data.subtitle_file` 存在：`true`（URL）
- `base_resp.status_code=0`：`success`
- 无 ProviderError：✅

**真实 timeline item 字段（已验证）**：
`text`, `pronounce_text`, `time_begin`, `time_end`, `text_begin`, `text_end`, `pronounce_text_begin`, `pronounce_text_end`, `is_final_segment`

**pytest -q**：`47 passed`

## P1 VoiceBinding 管理 API 已完成

VoiceBinding 管理 API 已完成（commit `e7aa95d` feat: expose voice binding management api）。

**已实现功能：**
- `GET /api/voice/profiles/{profile_id}/bindings` - 列出绑定
- `POST /api/voice/profiles/{profile_id}/bindings` - 创建绑定
- `PATCH /api/voice/bindings/{binding_id}` - 更新绑定
- `DELETE /api/voice/bindings/{binding_id}` - 软删除（status=deprecated）

**设计约束：**
- render API 仍不接受 provider_voice_id，必须通过 binding 管理
- provider_voice_id 必须存在且 status=available 才能绑定
- duplicate 判断：profile_id + provider + model + provider_voice_id
- 同 provider_voice_id 可绑定不同 profile（同 voice_id 不同 profile 不冲突）
- 同一 profile 内 provider_voice_id 不可重复
- binding ID 使用 new_id("binding") 全局唯一

**pytest -q**：`77 passed`（新增 VoiceBinding 测试 30 个）

**后续风险（已知）：**
- 还没有前端选择音色 UI
- 还没有绑定操作审计日志
- 还没有 binding 使用统计
- 还没有物理删除策略，P1 只做软删除

## P2 异步 T2A 已完成

**已实现功能：**
- `POST /api/voice/render/async` - 提交异步任务，立即返回 job_id
- `GET /api/voice/render/async/{job_id}/status` - 轮询状态，成功后返回 audio_asset
- `AsyncRenderService.submit_task` + `query_status` + `_complete_job`
- `MiniMaxSpeechAdapter.create_async_task` + `query_async_task`
- `MockSpeechAdapter.create_async_task` + `query_async_task`（返回 success + 静默 wav）
- 前端异步模式：选中"异步生成"Radio，生成后自动轮询，每3秒一次，最多120次

**pytest -q**：`+6 test_async_render.py` → `116 passed`

## P2 Voice Clone 已完成

**已实现功能：**
- `POST /api/voice/clone/upload` - multipart 文件上传（purpose=voice_clone/prompt_audio）
- `POST /api/voice/clone/create` - 执行克隆（file_id / voice_id / prompt_file_id / preview_text 等）
- `VoiceCloneUploadResponse` / `VoiceCloneRequest` / `VoiceCloneResponse` Schema
- `MiniMaxSpeechAdapter.upload_voice_file` + `clone_voice`
- `MockSpeechAdapter.upload_voice_file` + `clone_voice`（返回固定 file_id=99999）
- 内容安全检测：`input_sensitive.type != 0` 时抛 ProviderError

**pytest -q**：`+6 test_voice_clone.py`

## P2 Voice Design 已完成

**已实现功能：**
- `POST /api/voice/design/create` - 文字描述生成声音（prompt + preview_text）
- `VoiceDesignRequest` / `VoiceDesignResponse` Schema
- `MiniMaxSpeechAdapter.design_voice` - POST `/v1/voice_design`
- `MockSpeechAdapter.design_voice` - 返回 mock_designed_<id>
- `VoiceDesignService` - 若有 trial_audio_hex 则转存为音频文件

**pytest -q**：`+4 test_voice_design.py`

## P2 Voice Delete 已完成

**已实现功能：**
- `POST /api/voice/voices/delete` - 删除克隆/设计音色
- `VoiceDeleteRequest`（voice_id 必填，voice_type 正则 `^(voice_cloning|voice_generation)$`）
- `MiniMaxSpeechAdapter.delete_voice` - POST `/v1/delete_voice`
- `MockSpeechAdapter.delete_voice` - 返回 `{"voice_id": ..., "deleted": True}`
- `VoiceDeleteService` - voice_type 双重校验，禁止删除 system 音色

**pytest -q**：`+4 test_voice_delete.py`

## P2 统一测试面板已完成

**前端 4-Tab 布局（`app/static/index.html`）：**
- Tab1: T2A 生成 - 同步/异步/多版本生成（原有逻辑完整保留）
- Tab2: 音色管理 - 查询音色列表（`refresh=true`）+ 删除音色
- Tab3: 声音克隆 - 步骤1上传音频 + 步骤2执行克隆，file_id 自动联动
- Tab4: 声音设计 - prompt + preview_text 生成音色

**关键约束：**
- 音色查询首次必须 `refresh=true`（缓存为空时返回空列表）
- 克隆步骤1成功后 file_id 自动填入步骤2表单
- 所有 Tab 独立 provider 选择器

## P2-E: T2A WebSocket（未实现）

低优先，需额外架构设计（连接管理、流式响应），不在 P2 主体范围内。

## 前端测试面板使用说明

启动：`uvicorn app.main:app --reload`，访问 `http://127.0.0.1:8000/`

| Tab | 接口 | 说明 |
|-----|------|------|
| T2A 生成 | `POST /api/voice/render` | 同步生成 |
| T2A 生成 | `POST /api/voice/render/async` | 异步提交 + 轮询 |
| T2A 生成 | `POST /api/voice/variants/render` | 多版本生成 |
| 音色管理 | `GET /api/voice/provider-voices?refresh=true` | 查询音色 |
| 音色管理 | `POST /api/voice/voices/delete` | 删除音色 |
| 声音克隆 | `POST /api/voice/clone/upload` | 上传音频 |
| 声音克隆 | `POST /api/voice/clone/create` | 执行克隆 |
| 声音设计 | `POST /api/voice/design/create` | 文字生成声音 |

所有功能均支持 `provider=mock`（无需真实 API Key）。

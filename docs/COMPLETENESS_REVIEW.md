# Completeness Review

检查时间：2026-05-11
P0 可运行基线 commit：`5b8d731 fix: return not found for missing assets`
P1 Voice Catalog commit：`6dee90f`
P1 T2A HTTP 增强 commit：`0e5177a fix: harden minimax t2a response parsing`
P1 VoiceBinding 管理 API commit：`e7aa95d feat: expose voice binding management api`

本文档记录当前 Voice Lab P0 和 P1 的完整性检查结果。

## 当前总体判断

P0 后端已达到可运行基线，所有接口和错误边界验收通过。
P1 Voice Catalog（MiniMax Get Voice）已完成，真实 MiniMax 验收通过。
P1 T2A HTTP 增强（响应解析硬化）已完成，真实 MiniMax `output_format=url` + `subtitle_file` 验收通过。
P1 VoiceBinding 管理 API 已完成，pytest 77 passed。

## 自动测试

```bash
pytest -q
```
P0 结果：`11 passed`
P1 Voice Catalog 结果：`23 passed`（含 P0 原有 11 个）
P1 T2A HTTP 增强后结果：`47 passed`（含 P0 11 + Voice Catalog 12 + T2A 解析 22 + 新增 2）
P1 VoiceBinding 管理后结果：`77 passed`（含 P0 11 + Voice Catalog 12 + T2A 解析 22 + VoiceBinding 30 + 其他 2）

## 已执行 P0 验收检查

| 检查项 | 结果 |
|--------|------|
| `GET /health` | 200 ✅ |
| `GET /api/voice/profiles` | 200 ✅ |
| `POST /api/voice/profiles` | 200 ✅ |
| `POST /api/voice/render` (mock) | 200 ✅ |
| `POST /api/voice/variants/render` (mock) | 200 ✅ |
| `GET /api/voice/jobs/{job_id}` | 200 ✅ |
| `GET /api/voice/assets/{asset_id}` | 200 ✅ |
| `GET /api/voice/assets/{asset_id}/download` | 200 ✅ |
| profile 不存在 -> PROFILE_NOT_FOUND | 404 ✅ |
| text 为空 -> VALIDATION_ERROR | 422 ✅ |
| provider=minimax 无 key -> PROVIDER_NOT_CONFIGURED | 400 ✅ |
| job 不存在 -> JOB_NOT_FOUND | 404 ✅ |
| asset 不存在 -> ASSET_NOT_FOUND | 404 ✅ |
| text 超 9500 字符 -> VALIDATION_ERROR | 422 ✅ |

## P1 Voice Catalog 验收

| 检查项 | 结果 |
|--------|------|
| `GET /api/voice/provider-voices?provider=mock` | 200 ✅ |
| `GET /api/voice/provider-voices?provider=mock&voice_type=system` | 200 ✅ |
| `GET /api/voice/provider-voices?provider=minimax&refresh=true`（真实 MiniMax） | 200 ✅ |
| 返回 `total=304`，`by_type={'system':303,'voice_cloning':1}` | ✅ |
| MiniMax API Key 缺失时 `PROVIDER_NOT_CONFIGURED` | 400 ✅ |
| pytest -q | `23 passed` ✅ |
| 自动测试不请求真实 MiniMax | ✅ |

**真实验收条件**：需在 `.env` 中配置 `MINIMAX_API_KEY`，然后手动调用 `GET /api/voice/provider-voices?provider=minimax&refresh=true`。

## P1 T2A HTTP 增强验收（commit `0e5177a`）

| 检查项 | 结果 |
|--------|------|
| pytest -q | `47 passed` ✅ |
| 真实 MiniMax `output_format=url` 调用 | 200 ✅ |
| audio_asset 创建 | ✅ |
| audio 文件存在 + 有内容 | ✅（71412 bytes） |
| subtitle_asset 创建（非 null） | ✅ |
| subtitle json/srt 文件存在 | ✅ |
| timeline 非空 | ✅（1 条） |
| `data.audio` 存在（hex fallback） | ✅ |
| `data.subtitle_file` URL 下载解析 | ✅ |
| `base_resp.status_code=0` | ✅ |
| 无 ProviderError | ✅ |

**真实 T2A 响应结构**（已验证）：
- 顶层 keys：`data`, `extra_info`, `trace_id`, `base_resp`
- `data` keys：`audio`, `status`, `ced`, `subtitle_file`
- `data.subtitle_file` 类型：URL 字符串（OSS），非 dict/list
- `data.audio_url` / `data.url`：不存在
- timeline item 字段：`text`, `pronounce_text`, `time_begin`, `time_end`, `text_begin`, `text_end`, `pronounce_text_begin`, `pronounce_text_end`, `is_final_segment`

**关键发现**：
- `output_format=url` 时 MiniMax 仍返回 `data.audio`（hex），`data.audio_url` 不存在
- Voice Lab 优先 `audio_url` 下载，hex 作为 fallback 逻辑正确
- `data.subtitle_file` 是 URL 字符串，需下载后按 JSON 解析

## P1 VoiceBinding 管理 API 验收（commit `e7aa95d`）

| 检查项 | 结果 |
|--------|------|
| pytest -q | `77 passed` ✅ |
| `GET /api/voice/profiles/{profile_id}/bindings` | 200 ✅ |
| `POST /api/voice/profiles/{profile_id}/bindings` | 201 ✅ |
| `PATCH /api/voice/bindings/{binding_id}` | 200 ✅ |
| `DELETE /api/voice/bindings/{binding_id}`（软删除） | 200 ✅ |
| profile 不存在 -> PROFILE_NOT_FOUND | 404 ✅ |
| binding 不存在 -> BINDING_NOT_FOUND | 404 ✅ |
| duplicate binding -> VALIDATION_ERROR | 422 ✅ |
| provider_voice 不存在/不可用 -> VALIDATION_ERROR | 422 ✅ |
| 软删除后 status=deprecated | ✅ |
| 同 provider_voice_id 可绑定不同 profile | ✅ |
| 同 profile 内 provider_voice_id 不可重复 | ✅ |

**VoiceBinding 设计约束：**
- render API 仍不接受 provider_voice_id（绑定只能通过 VoiceBinding 管理）
- provider_voice_id 必须存在于 provider_voices 表且 status=available 才能绑定
- duplicate 判断：profile_id + provider + model + provider_voice_id
- 删除为软删除（status=deprecated），不删除 provider_voice
- binding ID 使用 new_id("binding") 全局唯一，不依赖 voice_id

## 架构约束检查

- VoiceProfile -> VoiceBinding -> RenderPlan -> Provider Adapter 链路：✅
- API 层未暴露 MiniMax voice_setting/audio_setting：✅
- MockSpeechAdapter 保留：✅
- 未引入 P1/P2 范围（Redis/Celery/Docker/用户系统/计费）：✅
- storage/ 被 .gitignore 忽略：✅
- 测试不依赖真实 MiniMax API：✅

## 剩余非阻断问题

1. **Windows 终端显示 UTF-8 字幕内容为乱码**（GBK 终端编码问题），文件本身 UTF-8 正常
2. **language/gender 字段**：MiniMax Get Voice 返回中暂无稳定字段，当前标准响应中保留为 null，不做自动推断
3. ~~**字幕真实结构**：MiniMax T2A 字幕返回结构仍待真实 T2A 请求验证~~ ✅ 已验证（见 P1 T2A HTTP 增强验收）

## 文件结构检查

### 已具备

- `app/main.py`
- `app/api/__init__.py`
- `app/api/health.py`
- `app/api/voice_profiles.py`
- `app/api/voice_render.py`
- `app/api/voice_variants.py`
- `app/api/voice_jobs.py`
- `app/api/voice_assets.py`
- `app/api/provider_voices.py`            # P1: Voice Catalog
- `app/core/config.py`
- `app/core/database.py`
- `app/core/errors.py`
- `app/core/time.py`
- `app/domain/enums.py`
- `app/domain/render_plan.py`
- `app/domain/schemas.py`
- `app/models/voice_profile.py`
- `app/models/voice_binding.py`
- `app/models/voice_job.py`
- `app/models/voice_asset.py`
- `app/models/voice_variant.py`
- `app/models/provider_voice.py`          # P1: Voice Catalog
- `app/providers/base.py`
- `app/providers/mock_speech_adapter.py`
- `app/providers/minimax_speech_adapter.py`
- `app/services/text_preprocess_service.py`
- `app/services/asset_service.py`
- `app/services/voice_profile_service.py`
- `app/services/voice_render_service.py`
- `app/services/voice_variant_service.py`
- `app/services/voice_catalog_service.py`   # P1: Voice Catalog
- `app/repositories/voice_profile_repo.py`
- `app/repositories/provider_voice_repo.py`  # P1: Voice Catalog
- `app/utils/id_generator.py`
- `app/utils/files.py`
- `app/utils/audio.py`
- `app/utils/srt.py`
- `tests/conftest.py`
- `tests/test_health.py`
- `tests/test_text_preprocess.py`
- `tests/test_render_plan.py`
- `tests/test_mock_adapter.py`
- `tests/test_api_render.py`
- `tests/test_minimax_speech_adapter.py`

### 建议后续补齐（非 P0）

- `app/core/logging.py` - 统一日志
- `app/repositories/voice_job_repo.py` - job 仓库
- `app/repositories/voice_asset_repo.py` - asset 仓库
- `app/repositories/voice_variant_repo.py` - variant 仓库
- `app/services/job_service.py` - job 服务层

## 安全检查

搜索项：Authorization / voice_setting / audio_setting / provider_voice_id / Redis / Celery / Voice Clone / Voice Design

结论：
- `Authorization` 仅在 MiniMax Adapter 请求头中出现，未发现日志输出
- `voice_setting` / `audio_setting` 仅在 Provider Adapter 内部，API 层未暴露
- Redis / Celery / Voice Clone / Voice Design 未在 P0 范围实现

## 结论

- P0 可运行基线：✅ 已达到（commit `5b8d731`）
- P1 Voice Catalog：✅ 已完成（commit `6dee90f`），真实 MiniMax 验收通过（total=304）
- P1 T2A HTTP 增强：✅ 已完成（commit `0e5177a`），真实 MiniMax `output_format=url` 验收通过
- P1 VoiceBinding 管理 API：✅ 已完成（commit `e7aa95d`）
- pytest -q：`77 passed`
- 是否建议 push：待确认

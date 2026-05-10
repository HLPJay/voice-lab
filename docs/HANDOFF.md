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

已验证：
- pytest 11/11 通过
- uvicorn 可正常启动
- Mock Provider 完整闭环
- 所有 P0 接口和错误边界验收通过

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
4. MiniMax 字幕返回结构需基于真实响应再适配（P1 范围）。
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

1. 空文本返回 FastAPI 原生 422 格式（`{"detail": [...]}`）而非统一 error 格式
2. Windows 终端可能显示 UTF-8 字幕内容为乱码（GBK 终端编码），文件本身 UTF-8 正常

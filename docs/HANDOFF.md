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

当前代码是“设计骨架 + 服务层草稿”，不是完整可运行版本。

原因：

- 用户已明确要求本轮收口为任务描述、架构设计和标准制定。
- 不继续补大量 API、测试和真实运行验证。
- 后续实现模块应从现有骨架继续，而不是推倒重来。

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

下一位实现者应优先补：

```text
app/main.py
app/api/__init__.py
app/api/health.py
app/api/voice_profiles.py
app/api/voice_render.py
app/api/voice_variants.py
app/api/voice_jobs.py
app/api/voice_assets.py
tests/
```

## 潜在注意点

1. `VoiceRenderService` 当前依赖 SQLModel session，API 层需要通过 `Depends(get_session)` 注入。
2. `TextPreprocessService` 已对 9500 字符以上同步文本做拒绝。
3. `MockSpeechAdapter` 返回 wav 文件，但 `RenderPlan.audio_params.format` 默认仍是 mp3；后续可选择统一 mock 文件格式或在返回资产中以实际后缀为准。
4. MiniMax 字幕返回结构需要基于真实响应再适配一次。
5. 错误处理器已经有草稿，但还未注册到 FastAPI app。
6. 当前未运行 pytest，也未做启动验证。

## 下一步建议

按以下顺序接手：

1. 补 `app/main.py` 和 `/health`。
2. 注册数据库初始化、seed、storage 目录创建。
3. 补 voice profiles API。
4. 补 render API，先只验 `provider=mock`。
5. 补 assets download API。
6. 补 variants API。
7. 补 tests，并修正服务层中暴露的问题。
8. 最后再用真实 MiniMax Key 做人工验证。

## 交接标准

后续实现完成后，至少应满足：

```text
uvicorn app.main:app --reload
GET /health -> {"status":"ok","app":"Voice Lab"}
POST /api/voice/render provider=mock -> success
storage/audio/YYYY-MM-DD/ 下生成文件
pytest 通过
```

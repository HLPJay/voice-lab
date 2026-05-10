# Control And Safety Checklist

本文档用于控制其他模型或开发模块实现 P0，目标是让实现过程可控、可测试、可回滚，并避免引入不必要风险。

## 交付控制原则

每次只允许实现一个小闭环：

1. 启动闭环。
2. Profiles API。
3. Mock render。
4. Jobs 和 assets。
5. Variants。
6. Tests。
7. MiniMax 人工验证。

禁止一次性实现 P1/P2。

## 范围控制

P0 允许：

- FastAPI 后端。
- SQLite。
- 本地 storage。
- Mock Provider。
- MiniMax 同步 T2A Adapter。
- 单条生成。
- 多版本生成。
- 任务记录。
- 资产下载。
- pytest 基础测试。

P0 禁止：

- 用户系统。
- 计费系统。
- Redis / Celery。
- Docker 复杂部署。
- 前端试音台。
- Voice Clone。
- Voice Design。
- Voice Management 完整流程。
- 异步长文本完整流程。
- WebSocket 流式语音。
- 多 Provider 真实接入。

## 安全策略

### API Key

要求：

- 只能从 `.env` 或环境变量读取。
- 不允许写死到代码。
- 不允许写入测试文件。
- 不允许打印到日志。
- 不允许进入异常 detail。

检查点：

- 搜索 `MINIMAX_API_KEY`。
- 搜索 `Authorization`。
- 搜索真实 token 前缀或明显密钥字符串。

### Provider 隔离

要求：

- API 层不得出现 MiniMax `voice_setting`。
- API 层不得出现 MiniMax `audio_setting`。
- API 层不得要求用户传 `provider_voice_id`。
- MiniMax 字段只允许在 `app/providers/minimax_speech_adapter.py` 内构造。

检查点：

- 搜索 `voice_setting`。
- 搜索 `audio_setting`。
- 搜索 `provider_voice_id`。
- 确认这些字段没有成为对外 API 必填字段。

### 文件安全

要求：

- 所有生成文件必须写入 `storage/` 内。
- 下载接口必须通过数据库 asset id 查询路径。
- 不允许用户直接传任意文件路径下载。
- 文件不存在时返回 `ASSET_NOT_FOUND`。

检查点：

- 下载接口是否接受 path 参数。
- 是否使用 `FileResponse` 返回数据库记录对应文件。
- 是否检查文件存在。
- 是否避免 `../` 路径穿越。

### 数据库安全

要求：

- 音频二进制不能存入数据库。
- 数据库只存路径、参数、状态、metadata。
- JSON 字段统一 `ensure_ascii=False`，便于中文可读。

检查点：

- `AudioAsset.file_path` 是否保存路径。
- 是否存在大字段保存音频 bytes。
- `VoiceJob.response_json` 是否可能保存敏感 header。

### 测试安全

要求：

- 测试默认使用 Mock Provider。
- 测试不请求外网。
- 测试不依赖真实 MiniMax Key。
- 测试使用临时数据库和临时 storage。

检查点：

- 测试是否 monkeypatch 配置。
- 测试是否创建临时目录。
- 测试是否调用 `provider=minimax`。
- 测试是否需要 `.env` 中的真实密钥。

## 可测试策略

每个阶段必须有明确验收。

### 启动验收

```text
uvicorn app.main:app --reload
GET /health
```

期望：

```json
{
  "status": "ok",
  "app": "Voice Lab"
}
```

### Mock Render 验收

请求：

```json
{
  "text": "我一直以为，是生活太难。后来才发现，真正让我害怕的是那个一直在逃避的自己。",
  "profile_id": "deep_night_programmer",
  "provider": "mock",
  "need_subtitle": true
}
```

期望：

- 返回 `status=success`。
- 返回 `job_id`。
- 返回 `audio_asset.id`。
- 返回 `audio_asset.url`。
- `storage/audio/YYYY-MM-DD/` 有文件。
- 数据库有 `voice_jobs` 和 `audio_assets` 记录。

### 错误验收

必须覆盖：

- 空 text。
- 不存在的 profile_id。
- 不存在的 asset_id。
- MiniMax API Key 缺失。
- Provider 调用失败。

## 完整性检查清单

交付前逐项确认：

- [ ] `app/main.py` 可启动。
- [ ] `app/api/__init__.py` 注册所有 P0 router。
- [ ] `/health` 返回正确。
- [ ] SQLite 表自动创建。
- [ ] 默认 profile 和 binding 自动 seed。
- [ ] `provider=mock` 单条生成成功。
- [ ] 多版本生成返回 `group_id` 和 variants。
- [ ] Job 查询可用。
- [ ] Asset 查询可用。
- [ ] Asset 下载可用。
- [ ] storage 下有生成文件。
- [ ] 失败时 VoiceJob 状态更新为 `failed`。
- [ ] MiniMax Key 缺失时返回 `PROVIDER_NOT_CONFIGURED`。
- [ ] 测试不依赖真实外部 API。
- [ ] README 与实际启动方式一致。
- [ ] 没有把 MiniMax 字段暴露给上层业务。
- [ ] 没有把音频二进制写进数据库。
- [ ] 没有日志输出密钥或 Authorization。

## 代码审查重点

审查其他模型的实现时，优先看这些问题：

1. 是否为了跑通接口，把业务逻辑塞进 API 路由。
2. 是否绕过 `RenderPlan` 直接调用 Provider。
3. 是否删除或弱化 Mock Provider。
4. 是否让测试依赖真实 MiniMax。
5. 是否新增了 P1/P2 功能导致范围失控。
6. 是否把 MiniMax 临时 URL 当成长期资产。
7. 是否下载任意用户传入路径。
8. 是否在异常中返回敏感配置。
9. 是否对现有架构做了不必要重构。

## 给其他模型的提交要求

每轮实现完成后，必须输出：

```text
1. 修改文件列表
2. 本轮完成内容
3. 验证命令
4. 验证结果
5. 未完成事项
6. 风险点
7. 是否建议进入下一轮
```

如果无法验证，必须明确说明原因，不能假装通过。


# P16-XIAOMI-MIMO-TTS-REAL-PROBE-A0：小米 MiMo 真实 API 最小探测方案设计

## 1. 阶段目标

设计小米 MiMo Chat TTS 真实 API 最小探测方案，为后续 P16-XIAOMI-MIMO-TTS-REAL-PROBE-B1 执行提供完整的技术方案和安全边界。

## 2. 为什么不直接启用 provider

当前 `xiaomi_mimo` provider 在 `config/providers.yaml` 中设置为 `enabled: false`。这是**预期行为**，原因如下：

1. **成本风险**：`real_cost: true`，启用后会触发 CostGuard，可能影响真实账户
2. **未验证**：真实 API 协议、响应格式、错误处理尚未确认真实行为
3. **UI 影响**：启用后 Xiaomi MiMo 会出现在前端 Provider 下拉框，用户可能误选
4. **隔离验证**：探测阶段应与正式业务隔离，不应通过正式业务路径

**探测目的**是在启用前确认真实 API 行为，验证 adapter 实现是否正确。

## 3. 真实探测前置条件

### 3.1 必须满足的条件

| 条件 | 说明 |
|---|---|
| 用户明确授权 | 用户必须显式同意执行真实 API 调用 |
| 有效的 MIMO_API_KEY | KEY 必须来自小米开发者平台 |
| KEY 获取方式 | 只能来自以下途径，不能写入 Git 或文档 |

### 3.2 KEY 获取优先级

1. `os.environ["MIMO_API_KEY"]`（最高优先级）
2. `VOICE_LAB_ENV_FILE` 指向的 env 文件中的 `MIMO_API_KEY`
3. 项目根目录 `.env` 中的 `MIMO_API_KEY`（仅本地开发）

### 3.3 安全禁令

- **禁止**：把 key 写入 Git
- **禁止**：把 key 写入日志
- **禁止**：在文档中粘贴 key
- **禁止**：默认执行真实请求
- **禁止**：CI 自动执行真实 probe

## 4. 探测范围

本阶段探测**只验证**最小同步 TTS：

| 项目 | 值 |
|---|---|
| model | `mimo-v2.5-tts` |
| endpoint | `POST https://api.xiaomimimo.com/v1/chat/completions` |
| auth | `api-key: $MIMO_API_KEY` |
| output format | `wav` |
| voice | `mimo_default`（主测）、`冰糖`（备测） |
| text | 简短中文测试文本，10-30 字符 |
| response path | `choices[0].message.audio.data` |
| audio decode | base64 → wav bytes |

## 5. 不探测范围

以下功能**不在本阶段探测范围内**：

- voice_design
- voice_clone
- streaming（`stream: true`）
- async task
- subtitle
- batch
- script
- UI 集成
- provider 正式启用

## 6. 探测脚本设计

### 6.1 脚本位置

```
scripts/probe_xiaomi_mimo_tts.py
```

### 6.2 核心设计原则

| 原则 | 说明 |
|---|---|
| 默认 dry-run | 不带 `--real-call` 时只打印，不请求 |
| 显式授权 | 必须 `--real-call` 才发真实请求 |
| 输出隔离 | 结果输出到 `tmp/probes/xiaomi_mimo/`，不进入业务路径 |
| Redaction | 敏感信息（key、header）必须脱敏 |
| 独立执行 | 不依赖 UI、业务代码、数据库 |

### 6.3 CLI 参数设计

```bash
# 默认 dry-run
python scripts/probe_xiaomi_mimo_tts.py --dry-run

# 完整 real-call
python scripts/probe_xiaomi_mimo_tts.py \
  --real-call \
  --text "你好，这是一次小米 MiMo 语音合成探测。" \
  --voice "mimo_default" \
  --format wav

# 使用自定义 env 文件
python scripts/probe_xiaomi_mimo_tts.py \
  --real-call \
  --env-file .env.local \
  --voice "冰糖"
```

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--dry-run` | true | 默认 dry-run 模式 |
| `--real-call` | false | 设为 true 才发真实请求 |
| `--env-file` | None | 设置 VOICE_LAB_ENV_FILE |
| `--text` | "你好，这是一次小米 MiMo 语音合成探测。" | 测试文本 |
| `--voice` | "mimo_default" | 音色 ID |
| `--model` | "mimo-v2.5-tts" | 模型名称 |
| `--format` | "wav" | 音频格式 |
| `--output-dir` | `tmp/probes/xiaomi_mimo/` | 输出目录 |

## 7. dry-run 行为

当使用 `--dry-run`（默认）时：

```
$ python scripts/probe_xiaomi_mimo_tts.py --dry-run

[DRY-RUN] Xiaomi MiMo TTS Real Probe
=====================================

Real API call: NO (use --real-call to enable)

Configuration:
  endpoint:    POST https://api.xiaomimimo.com/v1/chat/completions
  model:        mimo-v2.5-tts
  voice:        mimo_default
  format:       wav
  text:         你好，这是一次小米 MiMo 语音合成探测。
  text_chars:   20
  output_dir:   tmp/probes/xiaomi_mimo/

API Key: Checking...
  - os.environ.MIMO_API_KEY: NOT SET
  - VOICE_LAB_ENV_FILE: /path/to/.env.local
  - Project .env: SET ✓

Ready to probe. No network call made.
```

**不执行的操作**：
- 不创建输出目录
- 不保存文件
- 不发 HTTP 请求
- 不打印 key 值

## 8. real-call 行为

当使用 `--real-call` 时：

```
$ python scripts/probe_xiaomi_mimo_tts.py --real-call --text "你好"

[REAL-CALL] Xiaomi MiMo TTS Real Probe
=======================================

API Key: Found (hidden)
Making real API call to https://api.xiaomimimo.com/v1/chat/completions...

[SUCCESS] Audio saved to:
  tmp/probes/xiaomi_mimo/probe_20260516_143052/request.redacted.json
  tmp/probes/xiaomi_mimo/probe_20260516_143052/response.redacted.json
  tmp/probes/xiaomi_mimo/probe_20260516_143052/metadata.json
  tmp/probes/xiaomi_mimo/probe_20260516_143052/output.wav
```

**执行的检查**：
- 验证 MIMO_API_KEY 存在
- 发 POST 请求
- 解析响应
- 保存音频文件
- 保存 metadata

## 9. 探测用例列表

### Case 1：dry-run（默认）

**目的**：确认脚本默认不请求外部 API

**期望**：
- 输出 endpoint / model / voice / text / output_dir
- 明确显示 `Real API call: NO`
- 不创建音频文件
- 不调用网络

### Case 2：最小成功请求

**输入**：
```bash
python scripts/probe_xiaomi_mimo_tts.py \
  --real-call \
  --text "你好，这是一次小米 MiMo 语音合成探测。" \
  --voice "mimo_default"
```

**验证项**：
| 验证项 | 期望 |
|---|---|
| HTTP status | 2xx |
| response 有 choices | choices 非空 |
| audio.data 存在 | choices[0].message.audio.data 非空 |
| base64 可解码 | bytes 非空 |
| wav 文件非空 | output.wav 大于 0 bytes |
| wav 文件头 | RIFF 格式或至少 bytes 非空 |

**metadata 记录**：
```json
{
  "provider": "xiaomi_mimo",
  "adapter_type": "xiaomi_mimo_chat_tts",
  "model": "mimo-v2.5-tts",
  "voice": "mimo_default",
  "format": "wav",
  "text_chars": 20,
  "real_call": true,
  "success": true,
  "status_code": 200,
  "audio_path": "tmp/probes/xiaomi_mimo/xxx/output.wav",
  "audio_bytes": 12345,
  "trace_id": "...",
  "started_at": "...",
  "finished_at": "...",
  "duration_ms": 1234
}
```

### Case 3：中文预置音色

**输入**：`--voice "冰糖"`

**目的**：确认中文 voice name 可用

**验证项**：
- 请求 body `audio.voice == "冰糖"`
- 成功返回音频
- 输出文件保存

### Case 4：非法 API key

**输入**：使用错误 key

**目的**：确认鉴权失败错误结构

**验证项**：
| 验证项 | 期望 |
|---|---|
| HTTP status | 401 / 403 或 API 返回错误 |
| 错误信息脱敏 | error_message 不含真实 key |
| 不保存空音频 | output.wav 不创建 |
| metadata 标记失败 | `success: false` |

### Case 5：非法 voice

**输入**：`--voice "not_existing_voice"`

**目的**：确认 voice 错误结构

**验证项**：
- 捕获错误响应
- 记录 `status_code` / `error_type` / `error_message`（redacted）
- 不崩溃

### Case 6：非法 model

**输入**：`--model "not-existing-model"`

**目的**：确认 model 错误结构

**验证项**：
- 捕获错误响应
- 不保存音频
- `success: false`

### Case 7：长文本边界（可选）

**输入**：接近 5000 字符的文本

**目的**：初步观察接口长文本限制

**注意**：此 Case 可能消耗较多额度，默认不执行，除非用户明确授权。

## 10. 探测结果目录结构

```
tmp/probes/xiaomi_mimo/
  probe_YYYYMMDD_HHMMSS/
    request.redacted.json
    response.redacted.json
    metadata.json
    output.wav
```

## 11. metadata.json 格式

### 成功时

```json
{
  "provider": "xiaomi_mimo",
  "adapter_type": "xiaomi_mimo_chat_tts",
  "model": "mimo-v2.5-tts",
  "voice": "mimo_default",
  "format": "wav",
  "text": "你好，这是一次小米 MiMo 语音合成探测。",
  "text_chars": 20,
  "real_call": true,
  "success": true,
  "status_code": 200,
  "audio_path": "tmp/probes/xiaomi_mimo/probe_xxx/output.wav",
  "audio_bytes": 12345,
  "trace_id": "123e4567-e89b-12d3-a456-426614174000",
  "started_at": "2026-05-16T14:30:52Z",
  "finished_at": "2026-05-16T14:30:54Z",
  "duration_ms": 2340,
  "api_key_source": "os.environ"
}
```

### 失败时

```json
{
  "provider": "xiaomi_mimo",
  "adapter_type": "xiaomi_mimo_chat_tts",
  "model": "mimo-v2.5-tts",
  "voice": "mimo_default",
  "format": "wav",
  "text": "你好",
  "text_chars": 3,
  "real_call": true,
  "success": false,
  "status_code": 401,
  "error_type": "authentication_error",
  "error_message": "Invalid API key provided",
  "trace_id": null,
  "started_at": "2026-05-16T14:30:52Z",
  "finished_at": "2026-05-16T14:30:53Z",
  "duration_ms": 1234,
  "api_key_source": "os.environ"
}
```

## 12. request / response redaction 规则

### 12.1 request.redacted.json

```json
{
  "url": "https://api.xiaomimimo.com/v1/chat/completions",
  "method": "POST",
  "headers": {
    "api-key": "***REDACTED***",
    "Content-Type": "application/json"
  },
  "body": {
    "model": "mimo-v2.5-tts",
    "messages": [{"role": "assistant", "content": "你好"}],
    "audio": {"format": "wav", "voice": "mimo_default"}
  }
}
```

**关键规则**：
- `headers["api-key"]` → `"***REDACTED***"`
- `headers` 中其他 header 不变

### 12.2 response.redacted.json

```json
{
  "status_code": 200,
  "headers": {
    "content-type": "application/json"
  },
  "body": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "choices": [{
      "message": {
        "audio": {"data": "***REDACTED_BASE64***", "format": "wav"},
        "content": ""
      }
    }],
    "usage": {"completion_tokens": 50}
  }
}
```

**关键规则**：
- `body.choices[0].message.audio.data` → `"***REDACTED_BASE64***"`（不保存原始 base64）
- 其他字段正常保留

## 13. 安全边界

| 边界 | 说明 |
|---|---|
| dry-run 默认 | 不带 `--real-call` 绝不发请求 |
| --real-call 显式授权 | 必须显式传入才发真实请求 |
| MIMO_API_KEY 存在性检查 | key 不存在时提前退出 |
| 不打印 key | 只显示 key 来源（os.environ / VOICE_LAB_ENV_FILE / .env） |
| request.redacted.json | headers.api-key 写为 `***REDACTED***` |
| 不进入业务数据库 | 不写入 AudioAsset、SampleStore |
| 不进入生成历史 | 不写入 audition_records |
| 不修改 config | 不改 providers.yaml enabled 状态 |
| 不进入前端 | 不出现在 Provider 下拉框 |
| pytest 不自动运行 | 测试套件不包含 real-call probe |
| CI 不运行 real probe | CI 不会执行 `--real-call` |

## 14. 与当前 adapter 的关系

### 方案 A：复用 XiaomiMiMoChatTTSAdapter.render_sync()

| 优点 | 风险 |
|---|---|
| 验证真实业务 adapter 路径 | render_sync 保存到正式 storage_path("audio", ...) |
| 最接近未来正式调用 | 可能进入正式存储目录，不够隔离 |
| | 需要临时启用 provider |

### 方案 B：独立 HTTP probe 脚本（推荐）

| 优点 | 风险 |
|---|---|
| 完全隔离，不进入业务路径 | 不能完全验证 adapter render_sync 真实行为 |
| 不依赖 RenderPlan / storage_path | 只能验证 API 协议 |
| 输出到 tmp/probes | 后续需要额外 adapter-level 验证 |
| 不需要改 enabled 状态 | |

### 推荐：方案 B 作为第一轮探测

理由：
1. 先验证小米真实 API 协议和响应格式
2. 不经过业务链路，隔离性好
3. 输出到 `tmp/probes`，不会污染业务存储
4. 确认真实响应后，再做 P16-XIAOMI-MIMO-TTS-REAL-PROBE-B2（adapter-level 验证）

## 15. 推荐 B1 实现范围

P16-XIAOMI-MIMO-TTS-REAL-PROBE-B1 应实现：

```
scripts/probe_xiaomi_mimo_tts.py
```

**必须实现**：
- `--dry-run` 默认行为
- `--real-call` 显式授权
- `--env-file` 支持
- `--text` / `--voice` / `--model` / `--format` 参数
- `--output-dir` 参数
- `tmp/probes/xiaomi_mimo/` 输出结构
- `request.redacted.json` / `response.redacted.json` / `metadata.json` / `output.wav`
- Redaction 规则
- API key 检查（不打印 key）
- 安全退出（key 不存在时）

**不实现**（留到后续阶段）：
- Case 7 长文本边界（可选，用户明确授权时执行）
- 复用 adapter render_sync（留到 REAL-PROBE-B2）

## 16. 剩余风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| API 协议差异 | 真实响应可能与 B1 设计不符 | B1 probe 验证后会调整 adapter |
| 额度消耗 | 探测会消耗真实 API 额度 | 最小化探测用例，控制调用次数 |
| Key 泄露 | key 在命令行参数中可见 | 只通过 env 文件提供，不传参 |
| 并发探测 | 多人同时 probe 可能冲突 | 仅本地执行，无并发场景 |

## 17. 下一阶段建议

### P16-XIAOMI-MIMO-TTS-REAL-PROBE-B1

**目标**：实现并手动执行 probe 脚本

**执行方式**：
```bash
# 1. 用户显式授权
# 2. 确保 MIMO_API_KEY 存在（os.environ / .env.local）
# 3. 执行 probe
python scripts/probe_xiaomi_mimo_tts.py --real-call
# 4. 检查 tmp/probes/xiaomi_mimo/ 输出
```

**验证项**：
- Case 2 最小成功请求（必须）
- Case 3 中文音色（必须）
- Case 4 / 5 / 6 错误处理（必须）
- Case 1 dry-run（默认通过）

### P16-XIAOMI-MIMO-TTS-REAL-PROBE-B2

**目标**：验证 adapter render_sync 真实调用

**前置条件**：REAL-PROBE-B1 成功（真实 API 可用）

**内容**：
- 临时启用 xiaomi_mimo（enabled: true）
- 使用 adapter 真实调用
- 验证保存路径正确
- 恢复 enabled: false

## 18. 明确未做

- **未调用真实小米 API**
- **未启用正式 xiaomi_mimo provider**
- **未执行真实探测**
- **未提交真实 MIMO_API_KEY**
- **未实现 probe 脚本**（仅设计）
- **未改 UI**
- **未实现 voice_design / voice_clone / streaming**

## 19. 前置条件汇总

| 阶段 | 前置条件 |
|---|---|
| REAL-PROBE-B1 | 用户明确授权 + 有效 MIMO_API_KEY |
| REAL-PROBE-B2 | REAL-PROBE-B1 成功 |
| VOICE-DESIGN-A0 | REAL-PROBE-B1 成功 |
| VOICE-CLONE-A0 | REAL-PROBE-B1 成功 |

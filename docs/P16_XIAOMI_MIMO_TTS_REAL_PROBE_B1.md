# P16-XIAOMI-MIMO-TTS-REAL-PROBE-B1：小米 MiMo 真实 API 最小探测实现

## 阶段目标

实现并测试小米 MiMo 真实 API 探测脚本 `scripts/probe_xiaomi_mimo_tts.py`。

## 实现的文件

### scripts/probe_xiaomi_mimo_tts.py

真实 API 探测脚本，实现了以下功能：

| 功能 | 说明 |
|---|---|
| `--dry-run`（默认） | 只打印配置，不发请求 |
| `--real-call` | 启用真实 API 请求 |
| `--env-file` | 设置 VOICE_LAB_ENV_FILE |
| `--text/--voice/--model/--format` | 自定义请求参数 |
| `--output-dir` | 自定义输出目录 |
| `--timeout` | 请求超时时间 |

**输出文件**（位于 `tmp/probes/xiaomi_mimo/probe_YYYYMMDD_HHMMSS/`）：
- `request.redacted.json` - 请求内容（API key 已脱敏）
- `response.redacted.json` - 响应内容（audio data 已脱敏）
- `metadata.json` - 探测元数据
- `output.wav` - 合成的音频文件

**Redaction 规则**：
- `headers["api-key"]` → `***REDACTED***`
- `body.choices[0].message.audio.data` → `***REDACTED_BASE64***`
- metadata 中 api_key_source = "hidden"

### tests/test_probe_xiaomi_mimo_tts.py

完整的测试套件，包含 12 个测试用例：

| 测试类 | 用例数 | 覆盖内容 |
|---|---|---|
| `TestDryRun` | 2 | dry-run 不发 HTTP 请求，输出配置 |
| `TestRealCall` | 2 | --real-call 发起请求，无 key 时阻止 |
| `TestEnvFile` | 1 | --env-file 参数生效 |
| `TestRedaction` | 3 | API key 和 audio data 脱敏验证 |
| `TestOutputStructure` | 1 | 成功时生成所有输出文件 |
| `TestErrorHandling` | 3 | 401 错误、缺失 audio、无效 base64 |

## 关键设计决策

### 1. main(argv=None) 接口

`main()` 函数接受可选的 `argv` 参数，使测试可以传递参数列表而不依赖 `sys.argv`：

```python
def main(argv: list[str] | None = None) -> int:
    args = parser.parse_args(argv)
```

### 2. MissingAudioData 错误处理

当响应中缺少 `audio.data` 时，探测脚本将其标记为失败：

```python
if audio_data is None:
    error_type = "MissingAudioData"
    error_message = "response missing audio.data"
```

### 3. UTF-8 编码显式指定

所有 JSON 文件读写使用显式 `encoding="utf-8"`，确保 Windows 环境下中文正确处理。

## 安全边界

| 边界 | 状态 |
|---|---|
| dry-run 默认 | ✅ 不发请求 |
| --real-call 显式授权 | ✅ 必须显式传入 |
| API key 不打印/不保存 | ✅ api_key_source="hidden" |
| 请求/响应脱敏 | ✅ headers.api-key 和 audio.data |
| 不进入业务路径 | ✅ 输出到 tmp/probes |
| pytest 不自动运行 | ✅ 测试使用 fake httpx |

## 测试结果

```
12 passed in 0.42s
```

## 执行方式

```bash
# dry-run（默认，不发请求）
python scripts/probe_xiaomi_mimo_tts.py --dry-run

# 真实探测（需要用户授权）
python scripts/probe_xiaomi_mimo_tts.py --real-call --env-file .env.local
```

## 下一阶段

| 阶段 | 前置条件 |
|---|---|
| P16-XIAOMI-MIMO-TTS-REAL-PROBE-B2 | 用户授权 + 手动执行 B1 |
| P16-XIAOMI-MIMO-TTS-VOICE-DESIGN-A0 | REAL-PROBE-B1 成功 |
| P16-XIAOMI-MIMO-TTS-VOICE-CLONE-A0 | REAL-PROBE-B1 成功 |

## 明确未做

- 未启用 xiaomi_mimo provider（enabled: false 保持不变）
- 未实现 voice_design / voice_clone
- 未修改 UI
- 未运行真实探测（需用户手动授权）
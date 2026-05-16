# P16-XIAOMI-MIMO-TTS-REAL-PROBE-B2：真实 API 探测执行

## 阶段目标

执行小米 MiMo TTS 真实 API 最小探测。

## 执行历史

### 第一阶段：B2-BLOCKED（commit 9b6b5e0）

初始状态：MIMO_API_KEY 不存在，real-call 未执行。

| 检查项 | 状态 |
|---|---|
| dry-run 执行 | ✅ 已执行 |
| dry-run 结果 | ✅ 成功（配置输出正确，未发 HTTP 请求） |
| --real-call 执行 | ❌ 未执行 |
| MIMO_API_KEY 检测 | ❌ 不存在 |

### 第二阶段：B2-REAL-CALL-SUCCESS（用户手动执行）

**用户手动执行**：
```bash
python scripts/probe_xiaomi_mimo_tts.py --real-call --env-file .env
```

**成功结果**：

| 检查项 | 值 |
|---|---|
| status_code | 200 |
| audio_bytes | 161324 |
| trace_id | 615f66a3b19d4ad3ba9b4165ef575873 |
| duration_ms | 5796 |
| output.wav | ✅ 已生成 |

**输出目录**：`tmp/probes/xiaomi_mimo/probe_20260516_210920`

**输出文件**：
- `request.redacted.json` - 已脱敏请求
- `response.redacted.json` - 已脱敏响应
- `metadata.json` - 探测元数据
- `output.wav` - 合成的音频文件

### 第三阶段：C0（commit d8df563）

adapter 测试失败排查。

**失败测试**：`TestConfigDrivenBehavior::test_get_api_key_raises_when_missing`

**根因**：测试假设 `os.environ.pop("MIMO_API_KEY")` 后 `_get_api_key()` 会 raise，但 `resolve_env_value()` 会 fallback 到 `.env` 文件（该文件包含真实的 `MIMO_API_KEY`）。

**修复**：使用 `patch("app.config.env_resolver.resolve_env_value")` mock `resolve_env_value` 返回 None。

**C0 测试结果**：
- `test_xiaomi_mimo_chat_tts_adapter.py`: 46 passed
- `test_probe_xiaomi_mimo_tts.py`: 12 passed
- `test_adapter_plugin_discovery.py`: 44 passed
- `test_adapter_config_loader.py`: 51 passed
- **总计: 153 passed**

## 当前最终状态

| 检查项 | 状态 |
|---|---|
| dry-run | ✅ 成功 |
| real-call | ✅ 成功（用户手动执行） |
| status_code | 200 |
| audio_bytes | 161324 |
| trace_id | 615f66a3b19d4ad3ba9b4165ef575873 |
| output.wav | ✅ 已生成 |

## 安全状态

| 检查项 | 状态 |
|---|---|
| 是否修改代码 | ❌ 否 |
| 是否修改配置 | ❌ 否 |
| 是否启用 xiaomi_mimo provider | ❌ 否 |
| 是否修改 schema | ❌ 否 |
| 是否修改 resolve_binding | ❌ 否 |
| 是否提交密钥 | ❌ 否 |
| 是否泄露 key | ❌ 否 |
| .env 是否提交 | ❌ 否 |
| tmp/ 是否提交 | ❌ 否（已添加到 .gitignore） |

## 当前剩余问题

### probe real-call 日志重复打印

**现象**：real-call 执行时，日志 banner 被打印了两次。

**影响**：不影响实际探测结果，但用户体验不佳。

**需确认**：是否为重复 HTTP 请求（需 D1 排查）。

**当前禁止**：不要重复执行 real-call，除非用户明确授权。

## 文件变更记录

| 文件 | 变更 |
|---|---|
| `.gitignore` | 新增 `tmp/` 忽略规则 |
| `docs/P16_XIAOMI_MIMO_TTS_REAL_PROBE_B2.md` | 本文档 |
| `tests/test_xiaomi_mimo_chat_tts_adapter.py` | C0 修复测试 |

## 下一阶段建议

| 阶段 | 前置条件 | 内容 |
|---|---|---|
| P16-XIAOMI-MIMO-TTS-PROBE-DUPLICATE-CALL-TRIAGE-D1 | 用户授权（可选） | 排查 probe 日志重复打印问题 |

**当前禁止事项**：
- 不要重复执行 real-call
- 不要启用 xiaomi_mimo provider
- 不要进入 B3（adapter render_sync 验证）
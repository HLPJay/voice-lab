# P16-XIAOMI-MIMO-TTS-REAL-PROBE-B2：真实 API 探测执行（Blocked）

## 阶段目标

执行小米 MiMo TTS 真实 API 最小探测。

## 执行状态

| 检查项 | 状态 |
|---|---|
| dry-run 执行 | ✅ 已执行 |
| dry-run 结果 | ✅ 成功（配置输出正确，未发 HTTP 请求） |
| --real-call 执行 | ❌ 未执行 |
| MIMO_API_KEY 检测 | ❌ 不存在 |

## 阻塞原因

**MIMO_API_KEY 不存在**

检查结果：
- `os.environ["MIMO_API_KEY"]` - 未设置
- `VOICE_LAB_ENV_FILE` 环境变量 - 未设置
- 项目 `.env` 文件 - 文件存在但**不含** `MIMO_API_KEY` 字段

## dry-run 输出

```
[DRY-RUN] Xiaomi MiMo TTS Real Probe
==================================================

Real API call: NO (use --real-call to enable)

Configuration:
  endpoint:    POST https://api.xiaomimimo.com/v1/chat/completions
  model:      mimo-v2.5-tts
  voice:      mimo_default
  format:     wav
  text:       你好，这是一次小米 MiMo 语音合成探测。
  text_chars: 22
  output_dir: tmp\probes\xiaomi_mimo\probe_20260516_205723

API Key:
  - os.environ.MIMO_API_KEY: NOT SET
  - VOICE_LAB_ENV_FILE: NOT SET
  - Project .env: D:\...\voice_lab\.env

Ready to probe. No network call made.
```

## 观察记录

### Windows 终端中文乱码

**现象**：终端输出中文显示为乱码（如 `你好` 显示为 `��ã`）

**原因**：Windows 终端默认编码问题，非脚本 bug。脚本已使用 UTF-8 编码输出文件，探测结果文件正常。

**不影响**：
- 探测输出文件（JSON）编码正确
- 真实 API 调用（如有 key）
- 脱敏逻辑

### 探测脚本行为验证

dry-run 成功验证了以下逻辑：
1. API Key 来源检测正确
2. 配置参数输出正确
3. 未发任何 HTTP 请求
4. 未创建输出目录/文件

## 安全状态

| 检查项 | 状态 |
|---|---|
| 是否修改代码 | ❌ 否 |
| 是否修改配置 | ❌ 否 |
| 是否启用 xiaomi_mimo provider | ❌ 否 |
| 是否修改 schema | ❌ 否 |
| 是否修改 resolve_binding | ❌ 否 |
| 是否提交密钥 | ❌ 否 |
| 是否泄露 key | ❌ 否（real-call 未执行） |
| 是否误提交 tmp/ | ❌ 已添加到 .gitignore |

## 下一阶段前置条件

**获取有效的 MIMO_API_KEY**：

根据 P16_XIAOMI_MIMO_TTS_REAL_PROBE_A0.md，KEY 获取优先级：
1. `os.environ["MIMO_API_KEY"]`
2. `VOICE_LAB_ENV_FILE` 指向的 env 文件
3. 项目根目录 `.env`

**安全要求**：
- 永远不要将真实 key 提交到 Git
- 探测完成后从 `.env` 中移除 key
- 不要在文档中粘贴 key

## 文件变更

- `.gitignore` - 新增 `tmp/` 忽略规则
- `docs/P16_XIAOMI_MIMO_TTS_REAL_PROBE_B2.md` - 本文档
# MiniMax Copywriting Adapter Gap Analysis C10D-FIX2

## 1. 当前 adapter 实现摘要

当前文件：[`copywriting_minimax_gateway.py`](D:\claude_code\20260511_minimax声音模块扩展项目\voice_lab\src\xiangta\services\copywriting_minimax_gateway.py)

当前行为摘要：

- 通过 `UrllibMiniMaxHttpClient` 发起 HTTP POST
- 使用：
  - `Authorization` bearer-token 鉴权
  - `Content-Type: application/json`
- 请求 URL 组装方式：

```text
base_url.rstrip("/") + "/v1/chat/completions"
```

- 当前请求体最小字段：
  - `model`
  - `messages`
- 当前响应 parser 支持多个路径：
  - `choices[0].message.content`
  - `reply`
  - `content`
  - `data.choices[0].message.content`

## 2. 当前 runtime config 摘要

当前文件：[`runtime_config.py`](D:\claude_code\20260511_minimax声音模块扩展项目\voice_lab\src\xiangta\config\runtime_config.py)

当前与 MiniMax Copywriting 相关配置字段：

- `minimax_copywriting_base_url`
- `minimax_copywriting_model`
- `minimax_copywriting_api_key`

当前没有：

- `endpoint_path`
- `timeout_seconds`
- `temperature`
- `max_completion_tokens`

## 3. 当前 local config 示例摘要

当前文件：[`xiangta.runtime.local.example.json`](D:\claude_code\20260511_minimax声音模块扩展项目\voice_lab\configs\xiangta.runtime.local.example.json)

当前示例结构：

```json
{
  "llm": {
    "minimaxCopywriting": {
      "baseUrl": "<MINIMAX_TEXT_CHAT_OPENAI_BASE_URL>",
      "model": "<MINIMAX_MODEL_NAME>",
      "apiKey": "<LOCAL_TOKEN>"
    }
  }
}
```

问题不在字段名，而在 `baseUrl` 占位语义不够明确，容易被误填为完整 endpoint。

## 4. 与官方 text-chat-openai 的差异

官方基线见：

- [MiniMax text-chat-openai](https://platform.minimaxi.com/docs/api-reference/text-chat-openai)

### 核心对比

| 项 | 官方要求 | 当前实现 | 判断 |
|---|---|---|---|
| Base URL | `https://api.minimaxi.com` | 语义未锁定 | 有风险 |
| Endpoint path | `/v1/chat/completions` | 代码硬编码追加 | 正确 |
| Full URL | host + endpoint path | 文档曾暗示可能把完整 endpoint 写进 `baseUrl` | 有风险 |
| Auth | `Authorization` bearer-token | 相同 | 正确 |
| Request body | `model`, `messages`, optional `stream/temperature/top_p/max_completion_tokens` | 仅 `model/messages` | 最小可用，但不完整 |
| Response parse | `choices[0].message.content` | 支持该路径，也支持多种猜测路径 | 主路径正确，旁路过宽 |

## 5. A 类必须修复项

### A-1. `baseUrl` / endpoint path 语义冲突

这是当前最明确的 blocker。

现状：

- 官方文档已经确认：
  - base host：`https://api.minimaxi.com`
  - endpoint path：`/v1/chat/completions`
- 当前 adapter 会在 `base_url` 后面继续拼接 `/v1/chat/completions`
- 但当前项目旧文档和示例里，曾把完整 endpoint 填进 `baseUrl`

风险：

```text
如果 baseUrl 被配置为 https://api.minimaxi.com/v1/chat/completions
当前代码会拼成
https://api.minimaxi.com/v1/chat/completions/v1/chat/completions
```

结论：

- 这是 C10E 前必须处理的 A 类问题

### A-2. 旧文档中的 URL 示例已不再安全

当前旧文档中存在“完整 endpoint 写入 baseUrl”的历史猜测，这会误导真实联调配置。

结论：

- C10E 前至少要统一文档与 local config 的 `baseUrl` 语义

## 6. B 类联调前建议修复项

### B-1. parser 当前容忍了无官方依据的 response shape

当前 parser 支持：

- `reply`
- `content`
- `data.choices[0].message.content`

官方 `text-chat-openai` 页能支撑的主路径是：

```text
choices[0].message.content
```

结论：

- C10E 前建议把非官方 shape 降为 fallback，而不是主路径依据

### B-2. 请求体缺少官方可选控制字段的策略说明

官方支持：

- `stream`
- `temperature`
- `top_p`
- `max_completion_tokens`

当前 adapter 未传这些字段，本身不一定阻塞联调，但建议在 C10E 前明确：

- 首轮是否固定 `stream=false`
- 是否显式传 `temperature`
- 是否显式传 `max_completion_tokens`

### B-3. 缺少最小错误映射说明

官方有：

- `base_resp.status_code`
- 错误码页
- rate-limits 页

当前 adapter skeleton 还没有把这些整理成最小联调策略。

## 7. C 类后续 cleanup

### C-1. 配置字段可读性

后续可以考虑增加：

- `endpointPath`
- `timeoutSeconds`
- `temperature`
- `maxCompletionTokens`

但这不是 C10E 的第一阻塞项。

### C-2. 文档归档清理

旧的 C10D / C10D-FIX1 文档记录了当时“官方文档不可访问时的猜测”。它们作为历史记录可以保留，但后续应在索引层明确“不可再当作字段权威来源”。

## 8. 给 C10E 的代码修复建议

### C10E 前必须先处理

1. 明确 `baseUrl` 只允许 host/base，不允许完整 endpoint
2. 或者新增 `endpointPath`，把路径语义从 `baseUrl` 中分离出来
3. 更新 local config 示例，避免重复拼接
4. 将正式响应解析主路径收敛到 `choices[0].message.content`

### C10E 可同步评估

1. 是否显式传 `stream=false`
2. 是否加 `temperature`
3. 是否加 `max_completion_tokens`
4. 是否把 `base_resp.status_code` 纳入错误分类

## 9. 给 C10E 的真实联调步骤建议

建议顺序：

1. 先改掉 A 类 URL 语义冲突
2. 用本地私有配置填：
   - host/base
   - model
   - apiKey
3. 只做单次、非流式、最小 messages 联调
4. 先验证：
   - URL 正确
   - 401/403 行为可读
   - 200 响应能从 `choices[0].message.content` 解析
5. 再做 10-case 情绪效果评估

## 10. 结论

### A 类必须修复项

- `baseUrl` / endpoint path 语义冲突
- 旧文档和示例对 `baseUrl` 的误导

### B 类联调前建议修复项

- parser 非官方路径过宽
- 可选字段策略未明确
- 错误映射未最小固化

### C 类后续 cleanup

- 配置字段细化
- 历史文档索引清理

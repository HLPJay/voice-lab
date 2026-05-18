# MiniMax Official API Reference C10D-FIX2

> **C10D-FIX3 更新**：C10D-FIX3 已将 baseUrl 和 endpointPath 语义拆分：
> - `baseUrl` = `https://api.minimaxi.com`（host/base，不含 path）
> - `endpointPath` = `/v1/chat/completions`（单独配置）
> - 完整 URL = `https://api.minimaxi.com/v1/chat/completions`

## 1. 文档访问情况

- `text-chat-openai`: 已访问并作为本任务唯一权威来源
- `text-chat-anthropic`: 已访问，仅做对比参考
- `text-ai-sdk`: 已访问，仅做实现路线参考
- `rate-limits`: 已访问，用于补充 RPM / TPM 与联调风险
- `errorcode`: 已访问，用于补充错误码与 C10E 前错误处理建议

官方链接：

- [text-chat-openai](https://platform.minimaxi.com/docs/api-reference/text-chat-openai)
- [text-chat-anthropic](https://platform.minimaxi.com/docs/api-reference/text-chat-anthropic)
- [text-ai-sdk](https://platform.minimaxi.com/docs/api-reference/text-ai-sdk)
- [rate-limits](https://platform.minimaxi.com/docs/guides/rate-limits)
- [errorcode](https://platform.minimaxi.com/docs/api-reference/errorcode)

## 2. text-chat-openai 字段整理

### 核心结论

- API 类型：MiniMax 文本对话，OpenAI API 兼容形态
- Base URL：`https://api.minimaxi.com`
- Endpoint path：`/v1/chat/completions`
- 完整 URL 示例：`https://api.minimaxi.com/v1/chat/completions`
- HTTP method：`POST`
- Auth header：`Authorization` 使用 bearer-token 语义
- Content-Type：`application/json`

### 请求体

官方页面明确展示或列出的字段：

- `model`：必填
- `messages`：必填
- `stream`：可选，默认 `false`
- `max_completion_tokens`：可选
- `temperature`：可选，默认 `1`
- `top_p`：可选，默认 `0.95`

### messages 结构

官方示例采用 OpenAI 风格消息数组，至少明确支持：

- `role: "system"`
- `role: "user"`
- 响应中的 `role: "assistant"`

文档说明中还提到 richer role / message 设定能力，但当前 FastAPI adapter 在 C10E 前只需要按标准 OpenAI 兼容消息结构实现即可。

### 模型字段

官方页面当前列出的模型示例：

- `MiniMax-M2.7`
- `MiniMax-M2.7-highspeed`
- `MiniMax-M2.5`
- `MiniMax-M2.1`

结论：

- `model` 字段名已官方确认
- 旧文档中猜测的模型名不能再视为权威

### 响应结构

非流式响应页面明确给出：

- `choices`
- `choices[0].message.content`
- `choices[0].message.role`
- `model`
- `usage`
- `base_resp.status_code`
- `base_resp.status_msg`

本项目当前应以：

```text
choices[0].message.content
```

作为正式解析主路径。

### 流式支持

### `response_format` 状态

本次以官方 `text-chat-openai` 页面为准重新核验后，当前页面**未直接确认** `response_format` 字段。

结论：

- 本任务不能把 `response_format=json_object` 写成“已官方确认”
- 如果 C10E 需要结构化输出，应在真实联调前再次到官方页或最新 API 参考中二次确认

### 流式支持

官方字段中有：

- `stream: true/false`
- `object` 非流式为 `chat.completion`
- `object` 流式为 `chat.completion.chunk`

结论：

- 流式能力存在
- 但当前 XiangTa Copywriting adapter skeleton 不需要在 C10E 首轮联调中启用流式

### error / rate limit / timeout

- 官方错误码页提供了通用错误码，如：`1001`、`1002`、`1004`、`1039`、`2013`、`2049`、`2056`
- 官方 rate limit 页给出文本模型 RPM / TPM 维度
- 当前未在本任务中发现 text-chat-openai 页面给出专门的 retry 公式

结论：

- C10E 前应至少识别 401/403/429/5xx 与 `base_resp`
- retry 策略应保守，不应在本任务中凭猜测定死

## 3. text-chat-anthropic 与 text-chat-openai 差异摘要

| 项 | text-chat-openai | text-chat-anthropic |
|---|---|---|
| URL | `/v1/chat/completions` | `/anthropic/v1/messages` |
| 鉴权头 | `Authorization` bearer-token | `X-Api-Key: <api-key>` |
| 请求风格 | OpenAI chat completions | Anthropic messages |
| 响应内容主路径 | `choices[0].message.content` | `content[].text` |
| 当前是否适合作为 XiangTa adapter 主路径 | 是 | 否 |

结论：

- 当前 XiangTa FastAPI adapter 已经按 OpenAI 兼容思路实现
- 因此 `text-chat-openai` 是当前最合适的官方对照面

## 4. text-ai-sdk 为什么暂不作为当前 FastAPI adapter 主路径

`text-ai-sdk` 官方页面说明了 MiniMax 的 AI SDK provider 用法，但它不适合作为当前 XiangTa adapter 主路径，原因很简单：

1. XiangTa 当前是 Python / FastAPI 后端
2. 当前 adapter 需要显式控制 HTTP request / response
3. 当前项目不准备为 C10E 引入新的 SDK 依赖
4. C10E 的目标是先核验官方 HTTP contract，而不是切 SDK 栈

结论：

- `text-ai-sdk` 可作为生态参考
- 但当前实现仍应以 `text-chat-openai` HTTP contract 为准

## 5. 官方字段表

| 项 | 官方文档字段 | 项目当前实现 | 结论 | 需要改动 |
|---|---|---|---|---|
| Base URL | `https://api.minimaxi.com` | `base_url` 语义未锁定 | 当前必须明确为 host/base，不应混入完整 endpoint | 是 |
| Endpoint path | `/v1/chat/completions` | 代码中硬编码追加 `/v1/chat/completions` | 路径本身与官方一致 | 否 |
| Full URL | `https://api.minimaxi.com/v1/chat/completions` | 文档里曾把完整 endpoint 写进 `baseUrl` | 这会导致重复拼接风险 | 是 |
| Auth | `Authorization` bearer-token | 当前实现相同 | 鉴权头实现方向正确 | 否 |
| Content-Type | `application/json` | 当前实现相同 | 正确 | 否 |
| model | `model` | 当前实现相同 | 正确 | 否 |
| messages | `messages` | 当前实现相同 | 正确 | 否 |
| stream | 支持，默认 `false` | 当前未显式传 | C10E 首轮可继续非流式 | 否 |
| max token 字段 | `max_completion_tokens` | 当前未传 | 若需要控制长度，应对齐官方字段名 | 建议 |
| temperature | `temperature` | 当前未传 | 官方支持，可按需补 | 建议 |
| top_p | `top_p` | 当前未传 | 官方支持，可按需补 | 建议 |
| Response content path | `choices[0].message.content` | 当前支持此路径，同时容忍多种猜测路径 | 正式主路径已有官方依据；其他路径无官方依据 | 是 |
| response_format | 当前页未直接确认 | 当前未使用 | 不应在 C10E 前假设支持 `json_object` | 建议 |
| Error schema | 参考 `base_resp` 与错误码页 | 当前未专门对齐 | C10E 前建议补最小错误映射 | 建议 |

## 6. 本项目应该采用的最终字段建议

### 推荐语义

```text
baseUrl = https://api.minimaxi.com
endpointPath = /v1/chat/completions
```

如果暂时不增加 `endpointPath` 配置字段，那么也必须在文档和 local config 里把 `baseUrl` 明确限定为 host/base，而不是完整 endpoint。

### 推荐请求主形态

```json
{
  "model": "<official model name>",
  "messages": [...],
  "stream": false
}
```

按需要再补：

- `temperature`
- `top_p`
- `max_completion_tokens`

### 推荐响应解析主路径

```text
choices[0].message.content
```

## 7. 尚待人工确认项

以下项目本任务不应凭猜测写死：

1. C10E 首轮联调最终采用的具体模型名
2. 是否在 C10E 首轮就启用 `max_completion_tokens`
3. 是否启用 `temperature`
4. `response_format` 是否在该接口上正式可用
5. 是否要把 `base_resp.status_code` 纳入正式 adapter 错误分类

# MiniMax Copywriting Adapter — API Reference Decision Record

**任务**: P18-XIANGTA-MINIMAX-COPYWRITING-ADAPTER-C10D
**状态**: C10D 实现完成，C10E 联调前置

---

## 1. 为什么选择 MiniMax text-chat-openai 作为主参考

C10D adapter 选择了 OpenAI-compatible 的 `text-chat-openai` 风格作为主实现形态，原因：

1. **接口兼容性**：OpenAI-compatible 形态是业界最广泛的 LLM API 风格，HTTP client 复用度高（urllib / httpx / aiohttp 均支持）。
2. **MiniMax 官方文档**：提供 `text-chat-openai` endpoint，`Authorization: Bearer <key>`，请求体为 `{"model": "...", "messages": [...]}`，与 OpenAI 完全一致。
3. **C10C prompt contract 已按 OpenAI messages 格式设计**：无需额外转换。
4. **UrllibMiniMaxHttpClient 可用 stdlib 实现**：无额外依赖。

---

## 2. 为什么 text-ai-sdk 暂不作为 FastAPI adapter 主参考

`text-ai-sdk` 是 MiniMax 的官方 SDK：

- 优势：官方维护，字段映射更准确，自动重试/超时封装。
- 劣势：引入额外 pip 依赖（`minimax-live` 或类似包），在纯 stdlib 环境下不可用。
- 当前决策：MVP 阶段优先使用 `urllib.request` 的 OpenAI-compatible HTTP 实现；SDK 路径留作 C10E 联调后评估。

---

## 3. 为什么 text-chat-anthropic 作为备用参考

`text-chat-anthropic` 使用 Claude 风格的 `system` 字段和不同的 role 约定：

- 当前 C10C prompt contract 不使用 `system` role，所有 instruction 都注入 user message。
- Anthropic 风格响应格式与 OpenAI 一致（`choices[0].message.content`），因此响应解析路径可以共用。
- 如果未来需要更强的 instruction following，可以评估切换到 `text-chat-anthropic`。

---

## 4. C10D Adapter 使用的请求形态

```python
# HTTP
POST https://<base_url>/v1/chat/completions

# Headers
{
    "Content-Type": "application/json",
    "Authorization": "Bearer <api_key>",
}

# Body
{
    "model": "<model>",
    "messages": [
        {"role": "user", "content": "<prompt>"}
    ],
}

# Response (same shape as OpenAI)
{
    "choices": [
        {"message": {"content": "..."}}
    ]
}
```

---

## 5. 当前执行环境无法访问 MiniMax 官方文档

**环境限制**: `platform.minimaxi.com` 在当前执行网络环境下不可访问。

因此：
- C10D adapter 仍按 OpenAI-compatible 形态实现。
- **C10E 真实联调前必须由人工打开官网确认以下字段**：
  - 确认 base URL 和 endpoint path（是否确为 `/v1/chat/completions`）
  - 确认 auth header 格式（是否确为 `Bearer` token）
  - 确认 model 字段名称和有效模型名列表
  - 确认 request body 是否有额外必填字段（如 `response_format`）
  - 确认 streaming 是否支持（当前 C10D 不支持 streaming）
  - 确认 error response schema
  - 确认 rate limit / timeout 推荐值

**未确认前不得把真实 Provider 作为默认路径。**

---

## 6. 待 C10E 手工确认字段清单

| 字段 | 当前状态 | 需确认 |
|---|---|---|
| base URL | `https://api.minimax.chat/v1/text/chatcompletion_v2` (待确认) | 是 |
| endpoint path | `/v1/chat/completions` (假设) | 是 |
| auth | `Bearer <key>` (假设) | 是 |
| model 有效值 | `MiniMax-Text-01` (假设) | 是 |
| request body 必填字段 | 仅 `model` + `messages` (假设) | 是 |
| `response_format` | 未使用 | 待确认是否支持 |
| timeout 推荐值 | 20s | 待确认 |
| error schema | 假设 HTTP status + body | 是 |
| streaming | 不支持 | N/A |

# MiniMax Copywriting Adapter

## 概述

`MiniMaxCopywritingGateway` 是 MiniMax LLM 文案生成的实现类。

实现文件：`src/xiangta/services/copywriting_minimax_gateway.py`

## API 端点结论

- **Base URL**: `https://api.minimaxi.com`
- **Endpoint path**: `/v1/chat/completions`
- **Full URL**: `https://api.minimaxi.com/v1/chat/completions`
- **HTTP method**: `POST`
- **Auth**: `Authorization: Bearer <api_key>`
- **Response content path**: `choices[0].message.content`

## 配置语义

| 字段 | 含义 | 示例 |
|---|---|---|
| `baseUrl` | API host/base，**不包含 endpoint path** | `https://api.minimaxi.com` |
| `endpointPath` | API path，单独配置 | `/v1/chat/completions` |
| `model` | 模型名称 | `MiniMax-M2.7` |
| `apiKey` | MiniMax API key | `your_key_here` |

**重要**：`baseUrl` 不得包含 `/v1/chat/completions`。
如果误填，`build_minimax_chat_completion_url()` 会抛出 `MiniMaxConfigError`。

## 配置示例

### local config（gitignored，可含 apiKey）

`configs/xiangta.runtime.local.json`：

```json
{
  "features": {
    "llmCopywritingEnabled": true
  },
  "copywriting": {
    "mode": "llm",
    "provider": "minimax",
    "timeoutSecs": 20,
    "fallbackToTemplate": true,
    "minimax": {
      "baseUrl": "https://api.minimaxi.com",
      "endpointPath": "/v1/chat/completions",
      "model": "MiniMax-M2.7",
      "apiKey": "<DO_NOT_COMMIT_REAL_KEY>"
    }
  }
}
```

### 环境变量覆盖

```bash
export XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED=true
export XIANGTA_COPYWRITING_MODE=llm
export XIANGTA_COPYWRITING_PROVIDER=minimax
export XIANGTA_MINIMAX_COPYWRITING_BASE_URL=https://api.minimaxi.com
export XIANGTA_MINIMAX_COPYWRITING_ENDPOINT_PATH=/v1/chat/completions
export XIANGTA_MINIMAX_COPYWRITING_MODEL=MiniMax-M2.7
export XIANGTA_MINIMAX_COPYWRITING_API_KEY=your_key_here
```

## 配置优先级

```
default → runtime.json → runtime.local.json → XIANGTA_* env
```

## 启用条件

全部满足才启用真实 MiniMax：

```python
cfg.feature_llm_copywriting_enabled == True
cfg.copywriting_mode == "llm"
cfg.copywriting_provider == "minimax"
cfg.minimax_copywriting_api_key is not None
cfg.minimax_copywriting_base_url is not None
cfg.minimax_copywriting_model is not None
```

任一不满足则 fallback 到 `TemplateCopywritingGateway`。

## 请求体

当前最小实现：

```json
{
  "model": "<model>",
  "messages": [
    {"role": "user", "content": "<prompt>"}
  ]
}
```

## 响应解析

主路径：`choices[0].message.content`

兼容 fallback 路径（标记为非官方 fallback）：
- `reply`
- `content`
- `data.choices[0].message.content`

## 异常

| 异常 | 含义 |
|---|---|
| `MiniMaxHttpError` | 网络或 HTTP 错误 |
| `MiniMaxConfigError` | 配置错误（如 baseUrl 含 endpoint path） |
| `MiniMaxCopywritingResponseError` | 响应解析或验证失败 |

## 真实联调前检查清单

1. `configs/xiangta.runtime.local.json` 已创建并填入真实 key
2. `baseUrl` = `https://api.minimaxi.com`（不含 path）
3. `endpointPath` = `/v1/chat/completions`
4. `XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED=true`
5. `XIANGTA_COPYWRITING_MODE=llm`
6. `XIANGTA_COPYWRITING_PROVIDER=minimax`
7. `/api/xiangta/suggestions` 返回真实 LLM 结果
8. 未启用时默认走 template gateway

## 安全边界

- apiKey 只来自 local config 或 env，不从 committed runtime.json 读取
- `XiangTaRuntimeConfig.__repr__()` 不暴露 apiKey
- local config 已在 `.gitignore` 中
- 不打印 apiKey 到日志
- 不将 apiKey 返回给前端

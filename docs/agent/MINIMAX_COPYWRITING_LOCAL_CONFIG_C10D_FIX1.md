# MiniMax Copywriting — Local Config Guide

**任务**: P18-XIANGTA-MINIMAX-COPYWRITING-CONFIG-C10D-FIX1

---

## 配置模型

XiangTa 运行时配置优先级（从低到高）：

```
default → runtime.json → configs/xiangta.runtime.local.json → XIANGTA_* env
```

| 配置层 | 路径 | 是否可提交 Git | 允许内容 |
|---|---|---|---|
| default | 代码 | — | 安全默认值 |
| runtime.json | `src/xiangta/configs/runtime.json` | 是 | 能力开关、baseUrl、model、timeout、fallback |
| runtime local | `configs/xiangta.runtime.local.json` | **否** | baseUrl、model、**apiKey** |
| env | `XIANGTA_*` | 部署时覆盖 | 最高优先级，全部字段 |

---

## 哪些配置可以写入可提交 runtime.json

以下字段可以写在 `src/xiangta/configs/runtime.json`（可提交）：

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
      "baseUrl": "https://api.minimax.chat/v1/text/chatcompletion_v2",
      "model": "MiniMax-Text-01"
    }
  }
}
```

**注意**：`apiKey` 不应写入 runtime.json（即使写入也不会生效）。

---

## 哪些配置必须放 local config 或 secret

以下字段只能通过 env 或 local config 提供，不得写入可提交的 runtime.json：

- `copywriting.minimax.apiKey`

---

## 本地创建 configs/xiangta.runtime.local.json 步骤

### 1. 复制示例文件

```bash
cp configs/xiangta.runtime.local.example.json configs/xiangta.runtime.local.json
```

### 2. 编辑真实值

编辑 `configs/xiangta.runtime.local.json`，填入真实 key：

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
      "baseUrl": "https://api.minimax.chat/v1/text/chatcompletion_v2",
      "model": "MiniMax-Text-01",
      "apiKey": "your_real_key_here"
    }
  }
}
```

### 3. 确认文件被忽略

`.gitignore` 已包含：

```
configs/xiangta.runtime.local.json
*.runtime.local.json
*.local.secret.json
```

运行 `git status` 确认该文件显示为 untracked，不会被意外提交。

---

## 环境变量覆盖示例

### PowerShell

```powershell
$env:XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED="true"
$env:XIANGTA_COPYWRITING_MODE="llm"
$env:XIANGTA_COPYWRITING_PROVIDER="minimax"
$env:XIANGTA_MINIMAX_COPYWRITING_API_KEY="your_key_here"
$env:XIANGTA_MINIMAX_COPYWRITING_BASE_URL="https://api.minimax.chat/v1/text/chatcompletion_v2"
$env:XIANGTA_MINIMAX_COPYWRITING_MODEL="MiniMax-Text-01"
```

### Git Bash / Linux / macOS

```bash
export XIANGTA_FEATURE_LLM_COPYWRITING_ENABLED=true
export XIANGTA_COPYWRITING_MODE=llm
export XIANGTA_COPYWRITING_PROVIDER=minimax
export XIANGTA_MINIMAX_COPYWRITING_API_KEY=your_key_here
export XIANGTA_MINIMAX_COPYWRITING_BASE_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
export XIANGTA_MINIMAX_COPYWRITING_MODEL=MiniMax-Text-01
```

环境变量覆盖 local config 和 runtime.json，优先级最高。

---

## 如何确认默认仍是 template

启动应用（不配置任何 env 或 local config），默认配置：

```
feature_llm_copywriting_enabled = False
copywriting_mode = "template"
copywriting_provider = "none"
```

调用 `/api/xiangta/suggestions` 仍走 TemplateCopywritingGateway，无真实 LLM 调用。

---

## 如何确认 MiniMax behind flag 生效

配置 local config 后，还需同时满足以下全部条件才启用真实 MiniMax：

```python
# runtime_config 字段全部为真时启用
cfg.feature_llm_copywriting_enabled == True       # 能力开关
cfg.copywriting_mode == "llm"                     # LLM 模式
cfg.copywriting_provider == "minimax"            # 指定 provider
cfg.minimax_copywriting_api_key is not None      # 有 key
cfg.minimax_copywriting_base_url is not None     # 有 URL
cfg.minimax_copywriting_model is not None        # 有 model
```

任一条件不满足则 fallback 到 TemplateCopywritingGateway。

---

## 警告：不得提交真实 key

- **不得**将真实 `apiKey` 写入 `configs/xiangta.runtime.local.example.json`
- **不得**将真实 `apiKey` 写入 `docs/**`
- **不得**将真实 `apiKey` 写入 `.env.example`
- **不得**将真实 `apiKey` 写入 `runtime.json`（即使写入也不会生效）
- `configs/xiangta.runtime.local.json` 已在 `.gitignore` 中，但仍建议不要在公共机器上保留真实 key

---

## 调试：如何查看当前配置状态（不暴露 key）

```python
from src.xiangta.config.runtime_config import load_runtime_config
cfg = load_runtime_config()
print({
    "llm_enabled": cfg.feature_llm_copywriting_enabled,
    "mode": cfg.copywriting_mode,
    "provider": cfg.copywriting_provider,
    "minimax_url": cfg.minimax_copywriting_base_url,
    "minimax_model": cfg.minimax_copywriting_model,
    "api_key_configured": cfg.minimax_copywriting_api_key is not None,
    # 注意：永远不打印 api_key 的实际值
})
```

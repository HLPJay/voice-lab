# P18-XIANGTA-MINIMAX-COPYWRITING-CONFIG-C10D-FIX1 — Archive

**本地私有配置支持、apiKey 安全、文档补充**

## 概述

修复 C10D 后的配置与文档问题，建立可长期维护的 MiniMax Copywriting 配置方案。

## 新增文件

- `configs/xiangta.runtime.local.example.json` — 本地私有配置示例
- `docs/agent/MINIMAX_COPYWRITING_ADAPTER_DECISION_C10D.md` — MiniMax 官方文档决策说明
- `docs/agent/MINIMAX_COPYWRITING_LOCAL_CONFIG_C10D_FIX1.md` — 本地配置使用指南

## 修改文件

- `.gitignore` — 新增 local config ignore 规则
- `src/xiangta/config/runtime_config.py` — 新增 local config 支持
- `tests/xiangta/test_runtime_config.py` — 新增 9 个 local config 测试
- `docs/agent/NEXT_TASKS.md` — 修复 C10B 重复行，标记 C10D-FIX1 ✅

## 实现内容

### 1. 本地私有配置支持

新增 `configs/xiangta.runtime.local.json`（gitignored）支持：

```
优先级（低→高）: default → runtime.json → runtime.local.json → XIANGTA_* env
```

local config 支持完整的 MiniMax 配置，包括 `apiKey`。

### 2. API Key 安全规则

- `apiKey` **只能**来自 local config 或 env
- committed `runtime.json` 中的 `apiKey` 不会生效
- `XiangTaRuntimeConfig.__repr__()` 不暴露 apiKey 值（显示为 `<hidden>`）
- warning 日志不打印 key 值

### 3. 嵌套 minimax 配置

支持 `copywriting.minimax.*` 嵌套结构：

```json
{
  "copywriting": {
    "minimax": {
      "baseUrl": "...",
      "model": "...",
      "apiKey": "..."
    }
  }
}
```

嵌套路径优先于 flat `minimaxBaseUrl`/`minimaxModel` 字段。

### 4. .gitignore 规则

```
configs/xiangta.runtime.local.json
*.runtime.local.json
*.local.secret.json
```

### 5. MiniMax 官方文档决策

当前执行环境无法访问 `platform.minimaxi.com`，文档记录：
- C10D adapter 按 OpenAI-compatible 形态实现
- C10E 联调前必须人工确认 endpoint/auth/request/response 字段
- 未确认前不得把真实 Provider 作为默认路径

### 6. NEXT_TASKS 修复

- 删除重复的 C10B 状态行
- 添加 C10D-FIX1 ✅ 状态行
- 更新下一步约束（增加 C10E 联调前人工确认要求）

## 配置优先级确认

```
default → runtime.json → runtime.local.json → XIANGTA_* env
```

## API Key 安全确认

- 未提交真实 key
- local config 被 .gitignore 忽略
- example 只有 placeholder
- runtime.json 中 apiKey 不生效
- env 可覆盖 local config
- `__repr__` 隐藏 apiKey 值

## 测试结果

```
tests/xiangta/test_runtime_config.py::TestLocalRuntimeConfig
9 passed

tests/xiangta/test_runtime_config.py + test_copywriting_minimax_gateway.py + test_suggestions_api.py
82 passed

full xiangta suite: 831 passed + 7 pre-existing SQLite failures
```

## 未真实调用 MiniMax

本任务未进行任何真实 MiniMax API 调用。

## 下一步

`P18-XIANGTA-MINIMAX-COPYWRITING-EVAL-C10E` — 真实 MiniMax 手工联调与 10-case 情绪效果评估。

C10E 联调前必须：
1. 人工打开 MiniMax text-chat-openai 官方文档
2. 确认 base URL / endpoint path
3. 确认 auth header 格式
4. 确认 model 字段有效值
5. 确认 request body 必填字段
6. 确认 error response schema

## Follow-up cleanup（非阻塞）

- `admin_token` 在 `__repr__` 中也建议隐藏（当前已隐藏 apiKey，但 admin_token 未处理）
- `copywriting.minimaxBaseUrl` / `minimaxModel` flat 字段可在 C10E 稳定后移除，保留嵌套格式作为唯一路径

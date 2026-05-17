# apps/xiangta_runtime — XiangTa 本地 MVP Runtime

## 定位

XiangTa 本地开发运行入口（P17-XIANGTA-RUNTIME-B8-1），让 H5 和 `/api/xiangta/*` 可以在同一个 FastAPI app 下同源运行。

不修改 Voice Lab Core（`app/main.py`）。

## 路由结构

| 路径 | 说明 |
|---|---|
| `/` | 重定向到 `/h5/index.html` |
| `/h5/*` | H5 静态页面（`apps/xiangta-h5/` 目录） |
| `/api/xiangta/bootstrap` | XiangTa bootstrap API |
| `/api/xiangta/suggestions` | 文案建议 |
| `/api/xiangta/tts` | TTS（默认返回 400 no_provider，见下） |
| `/api/xiangta/letters` | 信笺历史 |
| `/api/xiangta/admin/config` | Admin 配置 |

## 启动命令

```bash
# 在项目根目录 voice_lab/ 下执行
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5173
```

访问：
- 主页面：<http://127.0.0.1:5173/>
- Bootstrap API：<http://127.0.0.1:5173/api/xiangta/bootstrap>
- H5 页面：<http://127.0.0.1:5173/h5/index.html>

> 注意：H5 `app.js` 使用 `API_BASE = ""`（相对路径），会请求 `/api/xiangta/*`，与本 runtime 同源，无 CORS 问题。

## MVP 限制

- **`/tts` 默认返回 `400 no_provider`**：runtime 没有注入 Core http_client，TTS 流程稳定降级。这是当前 MVP 预期行为，不是 bug。
- **`/letters` 进程内内存**：重启丢失，不适合生产。
- **`/suggestions` 模板版**：不调用真实 LLM。
- **不接真实 Provider / LLM**。真实 Provider 接入是后续独立阶段。

## 本地调试

```bash
# 单独测试 bootstrap
curl http://127.0.0.1:5173/api/xiangta/bootstrap | python -m json.tool

# 测试 suggestions
curl -X POST http://127.0.0.1:5173/api/xiangta/suggestions \
  -H "Content-Type: application/json" \
  -d '{"recipient":"lover","scene":"miss","rawText":"好想你呀今天"}' | python -m json.tool
```

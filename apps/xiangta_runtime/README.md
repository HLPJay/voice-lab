# apps/xiangta_runtime — XiangTa 本地 MVP Runtime

## 定位

XiangTa 本地开发运行入口（P17-XIANGTA-RUNTIME-B8-1），让 H5 和 `/api/xiangta/*` 在同一个 FastAPI app 下同源运行。

**不修改 Voice Lab Core（`app/main.py`）。**

## 架构关系

```
apps/xiangta_runtime  — 运行入口（壳），挂载路由和静态文件
apps/xiangta-h5      — 静态前端（HTML/JS/CSS）
src/xiangta          — 产品后端服务层（routes, services, schemas）
app/**               — Voice Lab Core 底座（独立运行）
```

apps 是应用壳，src/xiangta 是产品服务层，app 是音频能力底座。

## 路由结构

| 路径 | 说明 |
|---|---|
| `/` | 重定向到 `/h5/index.html` |
| `/h5/*` | H5 静态页面（`apps/xiangta-h5/` 目录） |
| `/api/xiangta/bootstrap` | XiangTa bootstrap API |
| `/api/xiangta/suggestions` | 文案建议（模板版） |
| `/api/xiangta/tts` | TTS（B9：支持 profileId 直传 Core render） |
| `/api/xiangta/core/profiles` | 读取 Core profiles（B9 新增） |
| `/api/xiangta/letters` | 信笺历史（进程内内存） |
| `/api/xiangta/admin/*` | Admin 配置管理 |
| `/api/voice/*` | **不在 XiangTa runtime**，属于 Core 服务（port 8000） |

## 启动命令

### 终端 1：Voice Lab Core

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 终端 2：XiangTa Runtime

**方法一：环境变量（推荐本地开发）**

PowerShell：
```powershell
$env:XIANGTA_CORE_BASE_URL="http://127.0.0.1:8000"
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5174
```

CMD：
```cmd
set XIANGTA_CORE_BASE_URL=http://127.0.0.1:8000
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5174
```

Linux / macOS：
```bash
export XIANGTA_CORE_BASE_URL=http://127.0.0.1:8000
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5174
```

**方法二：runtime.json（无需环境变量）**

编辑 `src/xiangta/configs/runtime.json`：
```json
{
  "core": {
    "enabled": true,
    "baseUrl": "http://127.0.0.1:8000",
    "timeoutSecs": 20
  }
}
```

然后直接启动：
```bash
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5174
```

**优先级**：环境变量 > runtime.json > 代码默认值（`core.enabled=false`）

访问：
- 主页面：<http://127.0.0.1:5174/>
- Bootstrap API：<http://127.0.0.1:5174/api/xiangta/bootstrap>
- Core profiles：<http://127.0.0.1:5174/api/xiangta/core/profiles>
- H5 页面：<http://127.0.0.1:5174/h5/index.html>

> H5 `app.js` 使用 `API_BASE = ""`（相对路径），会请求 `/api/xiangta/*`，与本 runtime 同源，无 CORS 问题。

## B9 Core Audio Link

B9 已打通完整链路：

```
H5
→ GET /api/xiangta/core/profiles
→ Core GET /api/voice/profiles
→ H5 coreProfileSelect 展示人设
→ POST /api/xiangta/tts {profileId, text, ...}
→ Core HTTP POST /api/voice/render
→ Core 返回 audio_asset.url
→ VoiceLabGateway.absolute_url() 转换为 Core 绝对 URL
→ XiangTa 返回 audioUrl
→ H5 <audio controls> 播放
```

## 注意事项

- **XiangTa runtime 不挂载 Core**。Core 运行在独立进程（port 8000），XiangTa 通过 `XIANGTA_CORE_BASE_URL` 环境变量配置的 HTTP 地址访问。
- **XiangTa runtime 不代理 Core assets**。audioUrl 由 `CoreHttpClient.absolute_url()` 转换为 `http://127.0.0.1:8000/api/voice/assets/...`，浏览器直接请求 Core。
- **`/favicon.ico 404` 非阻塞**。浏览器自动请求，不影响 TTS 和 audio 播放。
- **`/letters` 进程内内存**。重启丢失，不适合生产。
- **`/suggestions` 模板版**。不调用真实 LLM。

## 本地调试

```bash
# 测试 bootstrap
curl http://127.0.0.1:5174/api/xiangta/bootstrap | python -m json.tool

# 测试 Core profiles
curl http://127.0.0.1:5174/api/xiangta/core/profiles | python -m json.tool

# 测试 suggestions
curl -X POST http://127.0.0.1:5174/api/xiangta/suggestions \
  -H "Content-Type: application/json" \
  -d '{"recipient":"lover","scene":"miss","rawText":"好想你呀今天"}' | python -m json.tool

# 测试 TTS（需先配置 XIANGTA_CORE_BASE_URL）
curl -X POST http://127.0.0.1:5174/api/xiangta/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"想念你","voicePreset":"female-gentle","tone":"gentle","recipient":"lover","scene":"miss","profileId":"<core_profile_id>"}' | python -m json.tool
```

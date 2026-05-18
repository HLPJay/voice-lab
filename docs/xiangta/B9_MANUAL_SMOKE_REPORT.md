# B9 Manual Smoke Report

## 阶段结论

**P17-XIANGTA-CORE-AUDIO-LINK-B9 手工 smoke 已通过。**

XiangTa 产品层已能通过 Core 上层 HTTP API 获取 profiles、调用 render、返回可播放 audioUrl。
Core 未被修改。

---

## 启动方式

### 终端 1：Voice Lab Core

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 终端 2：XiangTa Runtime

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

### 页面访问

```
http://127.0.0.1:5174/
```

---

## 验收链路

### 1. Core profiles 读取

```
GET http://127.0.0.1:8000/api/voice/profiles
```
→ Core 返回 active profiles 列表

### 2. XiangTa profiles API

```
GET http://127.0.0.1:5174/api/xiangta/core/profiles
```
→ XiangTa 返回 `{"ok": true, "data": {"profiles": [...], "total": N, "source": "core"}}`

### 3. H5 展示

- `coreProfileSelect` 下拉框正确显示 Core profiles
- 选择 profile 后，payload 包含 `profileId`

### 4. TTS 生成

```
POST http://127.0.0.1:5174/api/xiangta/tts
Body: { "text": "想念你", "voicePreset": "female-gentle", "tone": "gentle", "recipient": "lover", "scene": "miss", "profileId": "<selected_profile_id>" }
```
→ 返回 `{"ok": true, "data": {"status": "completed", "audioUrl": "http://127.0.0.1:8000/api/voice/assets/...", "durationMs": N}}`

### 5. audioUrl 转换

- Core 返回相对路径 `/api/voice/assets/<asset_id>/download`
- VoiceLabGateway 通过 CoreHttpClient.absolute_url() 转换为 `http://127.0.0.1:8000/api/voice/assets/...`
- H5 `<audio controls src="http://127.0.0.1:8000/...">` 可直接播放

### 6. H5 音频播放

- `<audio controls>` 元素正确渲染
- 音频可正常播放
- 无 CORS 问题（音频直接请求 Core 域名）

---

## 已修复问题

| 修复 | 问题 | 解决 |
|---|---|---|
| B9-FIX1 | H5 renderTtsResult 重复渲染 | 添加 `div.innerHTML = ""` 清空逻辑 |
| B9-FIX1 | profileId 路径 tone 异常穿透 | tone_preset.resolve() 包装 try-except PresetNotFoundError |
| B9-FIX2 | Core HTTP URL 重复拼接 | VoiceLabGateway 不再传 core_base_url，CoreHttpClient 持有 base_url |
| B9-FIX3 | Core audioUrl 相对路径 H5 无法播放 | VoiceLabGateway 调用 http_client.absolute_url() 转换为绝对 URL |

---

## 非阻塞问题

### favicon.ico 404

```
GET /favicon.ico HTTP 404
```

是浏览器自动请求导致的非阻塞噪音。
不影响 profiles、TTS、audio 播放。
后续 H5 polish 可通过 `<link rel="icon" href="data:,">` 或正式 favicon 处理。

---

## 遗留问题

### 1. Core base URL 配置

当前 Core base URL 仍通过 `XIANGTA_CORE_BASE_URL` 环境变量配置。
后续可升级为 `runtime.json` + env override。

### 2. profile → voicePreset 映射

当前 H5 直接选择 Core profile（profileId）。
后续需产品化为 voicePreset → coreProfileId 映射，通过 Admin 接口配置。

### 3. TTS 同步链路

当前 POST /api/xiangta/tts 是同步请求，Core render 完成后才返回。
后续需设计异步 TTS task orchestration：

```
POST /api/xiangta/tts/tasks  → 立即返回 taskId
GET  /api/xiangta/tts/tasks/{taskId}  → 查询状态
```

### 4. 当前不承诺内容

当前 B9 不承诺：
- 多人 SaaS
- 高并发
- 任务恢复
- 任务取消
- 后台队列
- 多用户权限
- 真实 Provider cost guard（confirm_cost 行为待确认）

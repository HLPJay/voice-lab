# P20: Core Voice Binding Smoke Report

## 阶段结论

**P20-CORE-VOICE-BINDING-SMOKE 验证完成。**

Admin Voice Binding 配置页到 H5 Step 3 真实链路已可闭环：
`Core profiles` → `Admin binding page` → `voicePreset coreProfileId` → `H5 Step 3 selection` → `/api/xiangta/tts/tasks` → `Core render` → `audioUrl` → `H5 playback`

---

## 1. 必要运行参数

| 参数 | 说明 |
|------|------|
| `XIANGTA_CORE_BASE_URL` | Core HTTP 地址，如 `http://127.0.0.1:8000` |
| `XIANGTA_CORE_TIMEOUT_SECS` | Core 请求超时，默认 `20` |
| `XIANGTA_ADMIN_ENABLED` | `true` 启用 Admin API |
| `XIANGTA_FEATURE_TTS_TASK_ENABLED` | `true` 启用 TTS task API |

**Admin Token 配置方式**（二选一）：

方式 A：环境变量
```
XIANGTA_ADMIN_TOKEN=change-me-local-only
```

方式 B：本地私有配置文件 `configs/xiangta.runtime.local.json`
```json
{
  "admin": {
    "enabled": true,
    "token": "change-me-local-only"
  }
}
```

**优先级**：`XIANGTA_ADMIN_TOKEN` 环境变量 > `configs/xiangta.runtime.local.json` admin.token

**说明**：
- `XIANGTA_CORE_BASE_URL` 用于连接 Core
- `XIANGTA_ADMIN_ENABLED=true` 后 Admin API 才可用
- Admin Token 通过 `X-XiangTa-Admin-Token` 请求头传入
- formal H5 不需要知道 `coreProfileId`
- 测试不需要真实 Provider API key
- 不要把真实 token 写入 `src/xiangta/configs/runtime.json`
- 不要把真实 token 提交到仓库

---

## 2. 启动前检查

```bash
git branch --show-current
git rev-parse --short HEAD
```

确认当前分支是：

```
p18/xiangta-product-api
```

---

## 3. 配置示例

### PowerShell

```powershell
$env:XIANGTA_CORE_BASE_URL="http://127.0.0.1:8000"
$env:XIANGTA_CORE_TIMEOUT_SECS="20"
$env:XIANGTA_ADMIN_ENABLED="true"
$env:XIANGTA_ADMIN_TOKEN="change-me-local-only"
$env:XIANGTA_FEATURE_TTS_TASK_ENABLED="true"
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5174
```

### Linux / macOS

```bash
export XIANGTA_CORE_BASE_URL=http://127.0.0.1:8000
export XIANGTA_CORE_TIMEOUT_SECS=20
export XIANGTA_ADMIN_ENABLED=true
export XIANGTA_ADMIN_TOKEN=change-me-local-only
export XIANGTA_FEATURE_TTS_TASK_ENABLED=true
python -m uvicorn apps.xiangta_runtime.main:app --reload --host 127.0.0.1 --port 5174
```

---

## 4. Admin 绑定流程

```
1.  打开 /h5/admin-voice-bindings.html
2.  输入 Admin Token（XIANGTA_ADMIN_TOKEN 的值）
3.  点击"保存 Token"
4.  点击"刷新"
5.  确认 Core 已连接（状态显示 profiles 数量 > 0）
6.  选择一个 Core profile 绑定到 female-gentle
7.  点击"保存绑定"
8.  刷新页面
9.  确认 female-gentle 显示"已绑定"徽章
10. 确认 src/xiangta/configs/voice_mappings.json 已写入 coreProfileId
```

---

## 5. H5 正式链路流程

```
1.  打开 /h5/index.html
2.  选择关系（恋人）和场景（想念）
3.  输入文案（至少4字）
4.  点击"帮我整理表达"
5.  选择一条建议
6.  进入第 3 步（生成语音）
7.  确认已绑定声线可选（显示"已绑定"徽章）
8.  确认未绑定声线被禁用（显示"待绑定"或"绑定失效"徽章）
9.  点击"生成语音"
10. Network 检查 /api/xiangta/tts/tasks payload
11. payload 必须包含：text, voicePreset, tone, recipient, scene
12. payload 不得包含：profileId
13. payload 不得包含：coreProfileId
14. 如果 Core render 成功，H5 显示 audio player
```

### formal H5 payload 字段（已验证）

```js
{
  text: String,        // 用户输入/建议文案
  voicePreset: String,  // 如 "female-gentle"
  tone: String,         // 如 "gentle"
  recipient: String,    // 如 "lover"
  scene: String,        // 如 "miss"
}
```

dev mode 额外字段：

```js
profileId: String  // 仅在 ?mode=dev 且用户选择了 Core profile 时传入
```

---

## 6. 失败场景

### 6.1 Core 未连接

- **Admin 页面**：Core 状态显示"未连接"，无法加载 profiles 列表
- **H5 Step 3**：声线显示"绑定失效"或"未绑定"，`allBound=false`
- **TTS API**：返回 `status=failed`，`errorKind=no_provider`

### 6.2 Admin Token 错误

- **Admin API**：返回 HTTP 403，`{"ok": false, "errorKind": "admin_forbidden"}`

### 6.3 voicePreset 未绑定（placeholder coreProfileId）

- **H5 Step 3**：该声线显示"待绑定"徽章，`bound=false`，formal mode 禁用
- **全部未绑定时**：声线区域下方显示提示"当前还没有绑定真实声音，请先到 Admin 配置页绑定 Core profile。"
- **TTS API**：返回 `status=failed`，`errorKind=voice_preset_not_bound`，`message="当前声音尚未绑定 Core profile，请先在 Admin 配置页绑定。"`

### 6.4 绑定的 Core profile 已不存在

- **H5 Step 3**：该声线显示"绑定失效"徽章，`bound=true`，`coreAvailable=false`，formal mode 禁用
- **TTS API**：返回 `status=failed`，`errorKind=voice_preset_not_bound`

### 6.5 Core render 返回错误

- **TTS API**：返回 `status=failed`，`errorKind` 可能是 `tts_failed` 或 `no_provider`

### 6.6 audioUrl 为空

- **H5**：显示"语音暂未生成，可先保存文字信笺"，底部显示保存信笺入口

---

## 7. 验证检查清单

```
[ ] git branch 显示 p18/xiangta-product-api
[ ] Admin 页面可以刷新并加载 Core profiles
[ ] 可以将 Core profile 绑定到 female-gentle 并保存
[ ] src/xiangta/configs/voice_mappings.json 中 female-gentle.coreProfileId 已更新
[ ] H5 Step 3 中 female-gentle 显示"已绑定"
[ ] H5 Step 3 中未绑定声线显示"待绑定"且禁用
[ ] 全部未绑定时，声线区域下方显示提示
[ ] formal H5 Network payload 不含 profileId
[ ] dev mode H5 可以选择 Core profile 直通
[ ] TTS task 返回 completed 且有 audioUrl（Core 可用时）
[ ] TTS task 返回 failed 且 errorKind=voice_preset_not_bound（未绑定时）
```

# Admin Voice Binding Page — P19

把 Core profiles 绑定到 XiangTa 四种产品声音类型的配置流程。

## 概述

通过 Admin Web 配置页把 Voice Lab Core 人设绑定到 XiangTa voicePreset，完成 TTS 链路闭环：

```
Core profiles
  → Admin voice binding page
  → voice_mappings.json coreProfileId
  → H5 Step 3 voicePreset selection
  → Backend resolves voicePreset → coreProfileId
  → Core render
  → H5 audio playback
```

## 必要运行参数

| 参数 | 说明 |
|---|---|
| `XIANGTA_CORE_BASE_URL` | Core 服务地址，如 `http://127.0.0.1:8000`。配置后启用 Core 连接。 |
| `XIANGTA_CORE_TIMEOUT_SECS` | Core 请求超时（秒），默认 20 |
| `XIANGTA_ADMIN_ENABLED` | 设为 `true` 才允许 Admin API |
| `XIANGTA_ADMIN_TOKEN` | Admin 认证 Token，通过请求头 `X-XiangTa-Admin-Token` 传入 |
| `XIANGTA_FEATURE_DEV_CORE_PROFILE_SELECT` | 设为 `true` 开启 Dev Mode profile 下拉框 |

> **注意**：不需要真实 Provider（TTS/MiniMax）API key。XiangTa 本身不持有 TTS provider key，TTS 路由由 Core 决策。

## 关键 API

| API | 方法 | Admin Token | 说明 |
|---|---|---|---|
| `/api/xiangta/core/profiles` | GET | 否 | 获取 Core 已有人设（安全字段） |
| `/api/xiangta/admin/voice-mappings` | GET | 是 | 获取全部 voice mapping（含 coreProfileId） |
| `/api/xiangta/admin/voice-mappings/{id}` | PUT | 是 | 更新 voice mapping（绑定 coreProfileId） |
| `/api/xiangta/voice-bindings/status` | GET | 否 | formal H5 读取绑定状态（不暴露 coreProfileId） |
| `/api/xiangta/tts/tasks` | POST | 否 | 创建 TTS 任务，payload 含 voicePreset |

## voice_mappings.json 字段

| 字段 | 说明 |
|---|---|
| `id` | voicePreset id（如 `female-gentle`） |
| `label` | 产品声线名称 |
| `desc` | 声线描述 |
| `genderStyle` | `female` / `male` |
| `suitableRecipients` | 适合的接收人 |
| `recommendedScenes` | 推荐的场景 |
| `defaultTone` | 默认语气 |
| `enabled` | 是否启用 |
| `sortOrder` | 排序顺序 |
| **`coreProfileId`** | **绑定的 Core profile id（目标配置项）** |
| `providerPolicy` | 固定为 `default` |
| `renderOverrides` | 渲染参数覆盖（白名单字段） |
| `notes` | 备注 |

### coreProfileId 有效值判断

以下值视为**未绑定（placeholder）**：

```python
None
""
"<core_profile_id_from_core_profiles>"
" <space>..."
任何包含 `<` 或 `>` 的字符串
以 `todo` 开头的字符串（不区分大小写）
```

## renderOverrides 白名单

第一版页面不开放 `renderOverrides` 编辑。以下字段在白名单中，后续可扩展：

```
speed, vol, pitch, emotion, audio_format, need_subtitle
```

## providerPolicy 约束

第一版固定写入 `providerPolicy = "default"`。

**禁止**写入：
- `minimax`
- `xiaomi_mimo`

原因：真实 provider 由 Core profile / Core 默认策略决定，XiangTa 层不选择 provider。

## 手工验证步骤

### 场景 A：Core 未连接

```bash
# 不配置 XIANGTA_CORE_BASE_URL
python -m uvicorn src.xiangta.main:app --reload
# 打开 http://localhost:8000/h5/admin-voice-bindings.html
# 页面应显示 "Core 未连接"，但 voice mappings 仍可读取
```

### 场景 B：正常绑定

```bash
# 1. 配置 Core
export XIANGTA_CORE_BASE_URL=http://127.0.0.1:8000
export XIANGTA_ADMIN_ENABLED=true
export XIANGTA_ADMIN_TOKEN=my-secret-token

# 2. 启动 XiangTa
python -m uvicorn src.xiangta.main:app --reload

# 3. 打开 Admin 配置页
http://localhost:8000/h5/admin-voice-bindings.html

# 4. 输入 Token，点击刷新
# 应看到 Core profiles 列表和四种 voicePreset 绑定状态

# 5. 选择一个 Core profile，保存
# voice_mappings.json 中对应项的 coreProfileId 被写入

# 6. 打开正式 H5，走完整流程
# Step 3 应显示 "已绑定" badge
# 点击生成语音，Network 检查 payload：
#   - 含 voicePreset
#   - 不含 profileId（formal H5）
#   - 不含 coreProfileId
```

### 场景 C：验证 TTS 错误处理

```bash
# 选择未绑定 voicePreset，尝试生成 TTS
# 期望：HTTP 200，task.status="failed"，message 明确：
#   "当前声音尚未绑定 Core profile，请先在 Admin 配置页绑定。"
# 不期望：HTTP 500
```

## 前端行为总结

### Admin 配置页（`admin-voice-bindings.html`）

- 输入 Admin Token → 保存到 sessionStorage
- 刷新 → 加载 Core profiles + voice mappings
- 每个 voicePreset 显示：
  - 下拉框：Core profile 列表（显示 name · gender · tone · active）
  - 保存按钮：PUT `/api/xiangta/admin/voice-mappings/{id}`
  - 状态 badge：未绑定 / 已绑定 / 绑定失效 / Core 未连接

### Formal H5 Step 3（`app.js`）

- 进入 Step 3 时调用 `GET /api/xiangta/voice-bindings/status`
- 每个声音选项显示：
  - 已绑定 → 绿色 badge，可选
  - 待绑定 → 黄色 badge，禁用
  - 绑定失效 → 红色 badge，禁用
- 未绑定 voicePreset 时，"生成语音"按钮禁用
- 如果当前选中的变成未绑定，自动切换到第一个已绑定

### 禁止在 Formal H5 中出现的

- `coreProfileId` 字符串（严禁）
- `profileId` 直传（formal H5 模式严禁，dev mode 除外）

## 路由出口

- **正式 H5**：仅传 `voicePreset` → backend 解析到 `coreProfileId`
- **Dev Mode**：可传 `profileId` 直通（绕过 voicePreset 映射）

## 文件清单

| 文件 | 说明 |
|---|---|
| `apps/xiangta-h5/admin-voice-bindings.html` | Admin 配置页 HTML |
| `apps/xiangta-h5/admin-voice-bindings.js` | Admin 配置页 JS |
| `apps/xiangta-h5/admin-voice-bindings.css` | Admin 配置页 CSS |
| `configs/voice_mappings.json` | 四种 voicePreset 配置（初始含 placeholder） |
| `src/xiangta/services/product_service.py` | 新增 `get_voice_binding_status()` |
| `src/xiangta/api/routes.py` | 新增 `GET /voice-bindings/status` |
| `src/xiangta/api/schemas.py` | 新增 `VoiceBindingStatusItem` 等 |
| `src/xiangta/services/error_translator.py` | 错误 kind 改为 `voice_preset_not_bound` |
| `src/xiangta/config/product_config_models.py` | 允许 `core_profile_id` 为空 |

## 测试覆盖

见 `tests/xiangta/`：

1. `voice_bindings_status` 不返回 `coreProfileId`
2. placeholder 判断（空 / `<...>` / `todo`）
3. 已绑定 + Core 有该 profile → `coreAvailable=true`
4. 已绑定 + Core 无该 profile → `coreAvailable=false`
5. Core 不可用 → 接口不 500
6. `PUT voice-mappings/{id}` 写入合法 `coreProfileId`
7. 非法 `coreProfileId` 或 placeholder 被 writer 拒绝
8. Admin API 无 token → 403
9. TTS 未绑定 voicePreset → `voice_preset_not_bound`，message 明确
10. Admin 页面存在性 + JS 调用正确 API

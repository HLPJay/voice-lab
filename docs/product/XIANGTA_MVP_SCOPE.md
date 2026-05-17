# 想Ta了 · MVP 范围定义

> P17 阶段目标：把设计稿变成真实可用的第一版。

---

## MVP 主路径（必须完成）

```
Home 选对象 + 场景
  → Input 写原始想法（≥4字）
  → Suggestions AI 整理 3 条风格建议
  → Voice 选声线 + 语气
  → 生成真实 TTS 音频（MiniMax）
  → Letter 展示信笺 + 播放器
  → 保存到本地信笺夹
  → History 查看历史，支持收藏筛选
```

全程无登录，无云同步，数据存 localStorage。

---

## MVP 包含

| 功能 | 说明 |
|---|---|
| 5 个场景 | 想念 / 道歉 / 感谢 / 安慰 / 晚安 |
| 4 个对象 | 恋人 / 父母 / 朋友 / 自己 |
| 3 种风格 | 克制 / 温柔 / 真诚 |
| 4 种声线 | 温柔女声 / 温柔男声 / 清亮女声 / 成熟男声 |
| LLM 文案生成 | 基于用户输入生成 3 条建议 |
| TTS 语音合成 | MiniMax speech-2.5-hd |
| 本地信笺夹 | localStorage CRUD + 收藏过滤 |
| 分享图导出 | Canvas 渲染信笺图（可截图转发） |
| Provider 状态展示 | 实时显示连接状态 / 配额 |
| 错误友好化 | 配额满、断网、生成失败均有可读提示 |

---

## MVP 不包含（明确排除）

| 功能 | 排除原因 |
|---|---|
| 用户登录 / 注册 | 增加门槛，MVP 不需要账户 |
| 云同步 / 服务端信笺存储 | 本地够用，隐私更安全 |
| 支付 / 订阅计费 | 不在第一版考虑范围 |
| 多用户 / SaaS | 单设备体验优先 |
| 自动发送（微信 / 短信） | 产品原则：不替用户决定发送 |
| 声音克隆 / 自定义声线 | 增加技术复杂度，不是核心价值 |
| 聊天记录分析 | 涉及隐私，不采集 |
| 多轮对话 | 不是聊天产品 |
| 推送通知 | MVP 不需要 |
| 图片 / 文件附件 | 文字 + 语音已足够 |

---

## 阶段拆分建议

### A0（本阶段，P17-XIANGTA-INIT-A0）
固定 Core 基线，新建骨架，写文档。不实现业务。

### A1 — 配置协议 + Bootstrap 只读接口 ✅
- `configs/*.json` 只保留产品语义与 `core_binding_key`，不含 Provider 参数
- `preset_mapper.resolve_binding()` 输出 CoreBindingRequest，不输出 Provider 参数
- `GET /api/xiangta/bootstrap` 可用，返回配置快照
- `GET /api/xiangta/provider/status` 返回 `not_integrated`
- 不接真实 TTS，不调用真实 Provider
- 测试：66 个 tests 全通过

### A2 — Gateway Contract Dry-run
- `voice_lab_gateway.py` 完整接口定义，含 contract 注释
- `preset_mapper.resolve_binding()` 实现（读取 JSON，返回 CoreBindingRequest）
- 单元测试：验证 preset_mapper 不返回 Provider 参数
- 不调用真实 MiniMax / MiMo

### A3 — 真实 Core TTS 接入
- `tts_orchestrator.py` 实现 TTS 任务调度
- `voice_lab_gateway.generate_tts()` 通过 Core 稳定入口调用真实 TTS
- `POST /api/xiangta/tts` 路由可用
- E2E Mock 测试（不调用真实 MiniMax）

### A4 — LLM 文案生成
- `prompts/*.md` 填充 Prompt 模板
- `copywriting_service.py` 实现 LLM 调用
- `POST /api/xiangta/suggestions` 路由可用
- E2E Mock 测试

### A5 — 前端集成 + 联调
- `app.html` 前端接入产品 API（替换 EXPRESSION_BANK mock）
- 真实 TTS 音频替换 `_silentWav()`
- HistoryScreen 播放真实音频
- 全路径手机真机验证

### A5 — 打磨 + 准生产
- 错误状态完整覆盖
- Provider 状态轮询
- 分享图导出测试
- PWA 安装配置

---

## 验收标准（A4 完成时）

1. 用户写一段话 → 得到 3 条 AI 整理的建议
2. 选定风格 → 配声线 → 点"生成语音" → 听到真实音频
3. 保存后在信笺夹可见，支持按收藏筛选
4. 手机浏览器全程流畅，无控制台报错
5. 配额满 / 断网时有友好提示，不崩溃

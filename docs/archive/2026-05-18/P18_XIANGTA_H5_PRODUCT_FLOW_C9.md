# P18-XIANGTA-H5-PRODUCT-FLOW-C9

## 实现内容

- H5 从步骤式 smoke 页面改为 screen-based mobile product flow
- 5 个 screen：home/compose/suggest/voice/history
- 每次只显示一个主 screen，使用 `showScreen()` 切换
- sceneGrid/recipientGrid 以 choice-chip 形式在首页展示
- 正式 TTS 主路径接入 `/api/xiangta/tts/tasks`
- `generateTtsTask()` + `pollTtsTask()` 实现 task polling
- `generateTts()` 保留为 dev-only alias
- `setBusy()` 按钮防重复点击锁
- `saveLetter()` 保存信笺成功后显示 toast
- `loadLetters()` / `renderLetters()` 历史记录，含 audio player
- 保留 formal/dev mode 分离，`coreProfileSelect` 在 devPanel 中
- formal mode 不暴露 Core/profileId
- `applyModeUi()` 控制 devPanel 显隐
- 移动端样式：hero-card、choice-chip、bottom-actions、screen fade-in、toast

## 测试覆盖

- 15 tests in `tests/xiangta/test_h5_product_flow.py`
- 静态 contract 测试：screen 结构、screen state/showScreen、TTS task API、polling、button lock、history endpoint、styles

## 未实现项

- 登录/支付/会员/分享
- 真实下载
- 真实 LLM/TTS provider
- 录音上传/音频克隆
- 多用户/分页/删除/收藏
- 复杂动画/PWA/Service Worker
- React/Vue/Vite/路由框架

## 下一步 C10

P18-XIANGTA-PRODUCT-INTEGRATION-SMOKE-C10：产品主路径集成 smoke 测试

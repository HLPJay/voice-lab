# P18-XIANGTA-H5-DEV-FORMAL-MODE-C5

## 实现内容

### index.html
- 将 `coreProfileSelect` 包裹在 `div#devPanel.hidden` 内
- 默认 formal mode 隐藏 Dev Panel

### app.js
- 新增 `getAppMode()` 函数，读取 `?mode=dev` 参数
- 新增 `state.mode`，默认 `"formal"`
- 新增 `applyModeUi()` 函数，切换 devPanel 显隐和 `body[data-mode]`
- `loadBootstrap()` 改为 dev mode 才调用 `loadCoreProfiles()`
- `generateTts()` 改为 dev mode 才传 `profileId`
- `DOMContentLoaded` 初始化时调用 `applyModeUi()`

### styles.css
- 新增 `.dev-panel` 样式（dashed warn border）
- 保留 `.hidden { display: none !important; }`

## 测试覆盖

`tests/xiangta/test_h5_formal_dev_mode.py` (10 tests):
1. index.html 包含 devPanel
2. coreProfileSelect 位于 devPanel 内部
3. devPanel 有 hidden class
4. app.js 默认 mode 是 formal
5. app.js 支持 ?mode=dev
6. app.js applyModeUi 切换 devPanel hidden
7. app.js formal mode 不无条件调用 loadCoreProfiles
8. app.js profileId 只在 dev mode 设置
9. styles.css 存在 .hidden
10. styles.css 存在 .dev-panel

## 未实现项

- 完整手机端设计稿
- React / Vue / Vite
- Storage
- TTS task
- LLM

## 下一步

P18-XIANGTA-STORAGE-FOUNDATION-C6
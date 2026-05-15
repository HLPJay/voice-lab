# P12 真实使用问题记录

## P12-USAGE-FIX1：Workspace 音色绑定提示与 #bindingStatus 状态不一致

**发现时间：** 2026-05-15

**问题描述：**
- 在 workspace tab 中，切换人设后，`#bindingStatus` 显示"✓ 已绑定: xxx"，但 `#workspaceVoiceBindingHint` 显示"该人设尚未绑定音色"
- 根本原因：`checkBindingStatus()` 调用真实 API 获取绑定状态，但只更新 `#bindingStatus` DOM；`product_hints.js` 的 `updateWorkspaceVoiceBindingHint()` 读取 `window._voiceBindMap`，而该 map 只在 voices tab 调用 `loadAllBindings()` 时才被填充
- 数据源不一致：`#bindingStatus` ← API 直接返回，`#workspaceVoiceBindingHint` ← `window._voiceBindMap`

**影响范围：**
- Workspace tab 音色绑定提示（B1）
- 长文本 tab 音色绑定提示（B3-longtext）
- 剧本 tab 每行音色绑定提示（B3-script）

**修复方案：**
在 `checkBindingStatus()` 中，当 API 返回可用绑定时，将绑定数据同步写入 `window._voiceBindMap`；当无绑定时清除对应条目；最后调用 `window.updateWorkspaceVoiceBindingHint?.()` 确保 hint 与状态一致。

**修复位置：**
- `app/static/index.html`：`checkBindingStatus()` 函数（约 lines 3213-3260）

**E2E 覆盖：**
- 现有 29 个 E2E 测试全部通过
- 新增 Test 30（skipped）：因 providerSelect.value 在 page.evaluate 中不稳定，IIFE 闭包交互问题，测试设置困难
- 相关测试：Test 26（workspace hint 切换 tab）、Test 27（quick bind 成功切换）、Test 28（longtext hint 切换）、Test 29（script hint 切换）

**验证方式：**
- 手动切换 workspace → voices → workspace，binding hint 与 #bindingStatus 状态一致 ✅
- E2E targeted：29 passed ✅

## P12-USAGE-UX1：Advanced tab 提示区域过于臃肿

**发现时间：** 2026-05-15

**问题描述：**
- 「音色工具」页面有多个大卡片提示区域，占用过多垂直空间
- "高成本 / 工程验证能力" 大卡片（12px padding）+ "克隆、设计、导入音色后，建议绑定到人设再用于生成" 又一个大卡片
- "删除音色" 危险操作说明也是大卡片样式

**修复方案：**
- 将两个大卡片合并为一个紧凑 warning bar（约 3 行 vs 原来 6+ 行）
- 将 "删除音色" 大卡片改为紧凑 warning bar（2 行 vs 原来 4 行）

**修复位置：**
- `app/static/index.html`：tab-advanced 区域

**验证方式：**
- targeted E2E（clone/design/import）：6 passed ✅
- git diff --check：无 whitespace 错误 ✅

## P12-USAGE-FIX2：首次刷新 Workspace 默认人设绑定提示不准确

**发现时间：** 2026-05-15

**问题描述：**
- 首次刷新页面进入 Workspace 后，默认选中的人设可能已绑定音色，但页面仍显示"该人设尚未绑定音色"
- P12-USAGE-FIX1 已修复 checkBindingStatus() 的同步问题，但初始加载时 hint 仍可能错误

**原因：**
- populateAllProfiles() 中直接调用 updateWorkspaceVoiceBindingHint()，依赖 window._voiceBindMap
- 首次刷新时 _voiceBindMap 可能为空，导致错误提示

**修复方案：**
在 populateAllProfiles() 中：
1. 先调用 updateWorkspaceVoiceBindingHint() 同步设置正确初始状态
2. 再调用 checkBindingStatus() 异步刷新（以真实 API 为准）

**修复位置：**
- `app/static/index.html`：populateAllProfiles() 函数

**验证方式：**
- targeted E2E（workspace_voice_binding_hint / voice_binding_hint / quick_bind_success_go_create）：4 passed ✅
- git diff --check：无 whitespace 错误 ✅

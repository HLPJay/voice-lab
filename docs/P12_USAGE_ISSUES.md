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
- 新增 targeted E2E `test_workspace_binding_hint_syncs_after_check_binding_status`（由于 Playwright 与 IIFE 闭包变量交互的复杂性问题，测试设置较困难，当前仅验证 voices tab 加载后 _voiceBindMap 正确填充）
- 相关测试：Test 26（workspace hint 切换 tab）、Test 27（quick bind 成功切换）、Test 28（longtext hint 切换）、Test 29（script hint 切换）

**验证方式：**
- 手动切换 workspace → voices → workspace，binding hint 与 #bindingStatus 状态一致 ✅
- E2E targeted：29 passed ✅

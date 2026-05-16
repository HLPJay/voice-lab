# P16-WORKSPACE-RESTORE-B1-CHECK：workspace context 保存与完整恢复复核

## 1. 阶段背景

执行 P16-WORKSPACE-RESTORE-B1 实现复核。
远端提交 `4f75e84 feat: restore workspace context from recent samples (P16-WORKSPACE-RESTORE-B1)` 已确认。

## 2. 远端提交核验

```
4f75e84 feat: restore workspace context from recent samples
4ffe648 docs: verify workspace sample restore design
6f62662 docs: audit workspace sample restore design
202b792 docs: verify cancellation fix
22849ad fix: cancellation confirmation semantics and loading state
a7b1f7e docs: verify cancellation state-machine audit
9e15521 docs: audit real usage issues
```

B1 commit 涉及文件：
- `app/static/js/context_store.js` — normalizeWorkspaceContext
- `app/static/index.html` — buildWorkspaceRestoreContext + 4条保存路径
- `app/static/js/sample_sidebar.js` — restoreWorkspaceContext 等
- `docs/agent/NEXT_TASKS.md`
- `tests/test_workspace_restore_static.py`

未涉及 API/core/providers/repositories —— 范围正确。

## 3. ContextStore workspace type 复核

`normalizeWorkspaceContext` 字段检查：

| 字段 | 状态 |
|---|---|
| full_text | ✅ 保存完整文本 |
| provider | ✅ |
| profile_id | ✅ |
| profile_name | ✅ |
| model | ✅ |
| voice_id | ✅ |
| voice_name | ✅ |
| gen_mode | ✅ 限制 single/async/stream/variants |
| variant_count | ✅ 仅 variants 下保存，非 variants 为 null |
| audio_format | ✅ 限制 mp3/wav/flac |
| output_format | ✅ 限制 hex/url |
| need_subtitle | ✅ |
| params.speed/vol/pitch/emotion | ⚠️ 见 BLOCKER-2 |
| job_id / asset_id / download_url | ✅ 字符串或 null |

`normalizeContext` 中 type === 'workspace' 分支存在 ✅
longtext/script 分支未被破坏 ✅

## 4. index.html 保存链路复核

`buildWorkspaceRestoreContext` 字段读取检查：

| 字段 | 读取方式 | 状态 |
|---|---|---|
| full_text | textInput.value | ✅ |
| provider | providerSelect.value | ✅ |
| profile_id | profileSelect.value | ✅ |
| gen_mode | document.querySelector('input[name="genMode"]:checked') | ✅ |
| variant_count | ⚠️ document.getElementById('variantCountInput') | ❌ BLOCKER-1 |
| audio_format | audioFormat.value | ✅ |
| output_format | outputFormat.value | ✅ |
| need_subtitle | needSubtitle.checked | ✅ |
| params | paramSpeed/Vol/Pitch/Emotion.value | ⚠️ 见 BLOCKER-2 |

四条 workspace 生成路径 ContextStore.pushContext 调用：

| 路径 | context_id 来源 | 与 SampleStore 一致 |
|---|---|---|
| workspace_sync | syncJobId \|\| syncAssetId | ✅ |
| workspace_async | asyncJobId \|\| audio.id | ✅ |
| workspace_stream | streamJobId \|\| streamAssetId | ✅ |
| workspace_variant | variantJobId \|\| v.audio_asset_id | ✅ |

所有路径均用 try/catch 包裹 ✅

## 5. SampleStore 轻量性复核

`safePushWorkspaceSample` sample 对象字段：
- `context_id: extra.context_id || null` ✅
- 无 full_text ✅
- 无完整 params ✅

SampleStore 保持轻量 metadata ✅

## 6. SampleSidebar 恢复逻辑复核

新增 helper：
- `isWorkspaceSource()` ✅ 覆盖全部 4 个 source
- `switchToWorkspaceTab()` ✅
- `restoreWorkspaceContextById()` ✅
- `restoreWorkspaceContext()` ✅

`buildCard()` 逻辑：
- workspace + context_id: `data-context-id` + "恢复工作台" ✅
- 无 context_id: `data-text` + "填入工作台" ✅
- batch_longtext/batch_script: 无 fill 按钮 ✅

`bindActionEvents()` 逻辑：
- 有 `data-context-id` → `restoreWorkspaceContextById()` ✅
- 无 `data-context-id` 有 `data-text` → `fillTextInput()` ✅

## 7. restoreWorkspaceContext 行为复核

`restoreWorkspaceContext(context)` 字段恢复：

| 字段 | 恢复方式 | 状态 |
|---|---|---|
| textInput | setValueIfPresent | ✅ |
| providerSelect | 直接 .value + dispatch | ✅ |
| profileSelect | .value + setTimeout 再次设置 | ✅ |
| audioFormat | setValueIfPresent | ✅ |
| outputFormat | setValueIfPresent | ✅ |
| needSubtitle | setCheckedIfPresent | ✅ |
| genMode | querySelector + checked + dispatch | ✅ |
| variantCountInput | ⚠️ setValueIfPresent('variantCountInput', ...) | ❌ BLOCKER-1 |
| paramSpeed | ⚠️ setValueIfPresent('paramSpeed', NaN?) | ❌ BLOCKER-2 |
| paramVol | 同上 | ❌ BLOCKER-2 |
| paramPitch | 同上 | ❌ BLOCKER-2 |

- 不调用 handleGenerate ✅
- 不调用 fetch ✅
- 不自动提交 ✅
- switchToWorkspaceTab() 在 setTimeout(0) 内 ✅

## 8. 多版本 context_id 复核

`workspace_variant` 路径：所有 variant 共用同一个 `variantContextId = variantJobId || v.audio_asset_id`。

ContextStore.pushContext 每次调用写入/覆盖同一个 context_id（upsert 逻辑），getContext 返回最新保存的那条。

多个 variant 样本共用同一 context_id —— 最后生成的 variant 覆盖前面的，符合预期（同一工作台配置）。

## 9. longtext/script 回归复核

`restoreLongtextContext` / `restoreScriptContext` / `applyLongtextContextToForm` 均未被修改 ✅
`sample-detail-restore-btn` / `sample-detail-restore-script-btn` 保留 ✅

## 10. 测试结果

```
tests/test_workspace_restore_static.py     47 passed
tests/test_sample_sidebar_static.py        256 passed
tests/test_existing_function_regression_static.py  (subset of above)
tests/test_cancel_confirmation_static.py   15 passed
```

注：test_context_store_static.py 的 TestContextStoreBehavior（29项）因 jsdom 未安装全部失败 —— 与本次修改无关，是既有环境问题。

**静态测试覆盖不足**：测试仅检查字符串 'variantCount' 存在于函数体，未验证元素 ID 正确性，导致 BLOCKER-1 未被测试捕获。

## 11. 非阻塞观察项

- **OBS-1**: `params.emotion` 空值时 normalizeWorkspaceContext 存 `''`（空字符串）而非 `null`；restoreWorkspaceContext 读回 `''` —— 语义上可接受但不一致
- **OBS-2**: `profile_name` 写入 ContextStore 但 restoreWorkspaceContext 未用于任何 DOM 操作 —— 信息仅存储，无实际用途
- **OBS-3**: 浏览器 `type="number"` 保护下 paramSpeed/Vol/Pitch 非法输入概率极低，BLOCKER-2 实际触发门槛高

## 12. 复核结论

**未通过 —— 存在 2 个阻塞问题**

### BLOCKER-1：variantCount 元素 ID 错误

**位置**：`buildWorkspaceRestoreContext` (index.html:2516) 和 `restoreWorkspaceContext` (sample_sidebar.js:884)

**问题**：
- `buildWorkspaceRestoreContext` 使用 `document.getElementById('variantCountInput')`
- `restoreWorkspaceContext` 使用 `setValueIfPresent('variantCountInput', ...)`
- 实际 HTML 元素 ID 为 `variantCount`（无 Input 后缀）
- `variantCountInput` 在 index.html 中是全局变量（指向 `document.getElementById('variantCount')`），但 `getElementById` 查找 DOM ID 找不到

**影响**：用户选择 variants 模式并设置版本数量后恢复时，variant_count 始终为 3（catch fallback），用户选择的 4 或 5 被忽略。

**修复方向**：将 `document.getElementById('variantCountInput')` 改为 `variantCountInput`（使用全局变量）或 `document.getElementById('variantCount')`；将 `setValueIfPresent('variantCountInput', ...)` 改为 `setValueIfPresent('variantCount', ...)`。

### BLOCKER-2：paramSpeed/Vol/Pitch 非法值保存为 NaN

**位置**：`buildWorkspaceRestoreContext` (index.html:2527-2531)

**问题**：
```javascript
var speed = null;
try { var sp = document.getElementById('paramSpeed').value; if (sp) speed = parseFloat(sp); } catch (e) {}
```
- 若 `sp = "abc"`（极非法输入），`parseFloat("abc")` 返回 `NaN`
- NaN 被存入 ContextStore params
- restore 时 `setValueIfPresent('paramSpeed', NaN)` → `el.value = String(NaN)` = `"NaN"`

**注意**：`type="number"` 浏览器原生保护使触发概率极低，但通过 JS 或 DevTools 可绕过。

**修复方向**：在 `buildWorkspaceRestoreContext` 的 parseFloat 后增加 `if (isNaN(speed)) speed = null;`

## 13. 当前阶段

```
P16-WORKSPACE-RESTORE-B1-CHECK：未通过 ⚠️
```

## 14. 下一阶段

```
P16-WORKSPACE-RESTORE-B1-FIX1：修复 workspace restore 复核发现的问题
```

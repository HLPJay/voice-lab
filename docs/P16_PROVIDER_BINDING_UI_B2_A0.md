# P16-PROVIDER-BINDING-UI-B2-A0：Provider-first profile/binding UI 设计

## 1. 阶段背景

- **任务**: Provider-first profile/binding UI 设计
- **分支**: `p16/real-usage-issues`
- **设计日期**: 2026-05-16

### 前置阶段

- `P16-PROVIDER-MODEL-BINDING-CLOSE` ✅
- `NEXT-PRIORITY-REVIEW` ✅

### 当前核心问题

Workspace 已经能展示当前 binding 的 provider/model/voice，但 UI 仍然允许用户先选一个当前 Provider 下没有 binding 的人设。体验是：先选错，再被 binding guard 拦截。

## 2. 当前代码事实

### 2.1 Provider/Profile 选择器结构

**DOM 位置** (`index.html` line ~1336-1350):

```html
<!-- providerSelect 在前，profileSelect 在后 -->
<select id="providerSelect">...</select>
<select id="profileSelect">...</select>
```

**代码定义** (`index.html` line ~2307-2308):

```javascript
const profileSelect = document.getElementById('profileSelect');
const providerSelect = document.getElementById('providerSelect');
```

**结论**: DOM 上 provider 在前，但代码中两者是并列获取，无严格先后顺序。

### 2.2 populateProfileSelect 函数

**位置**: `index.html` line ~2201-2219

```javascript
function populateProfileSelect(selectEl, selectedId = '') {
  // 全量填充，不按 provider 过滤
  profiles.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.name;
    selectEl.appendChild(opt);
  });
}
```

**共用调用点**:
- `populateAllProfiles()` → `profileSelect`（workspace）
- `bindingProfileSelect`（binding 管理）
- `newBindingProfile`（创建绑定）

**结论**: `populateProfileSelect` 是共用函数，如果全局改过滤逻辑，会影响 binding 管理、Batch、Script 等多个模块。B2 应优先新增 workspace 专用 helper。

### 2.3 Provider/Profile change 事件

**位置** (`index.html` line ~2409-2410):

```javascript
providerSelect.addEventListener('change', () => {
  checkBindingStatus();
  updateCostHint();
  updateWorkspaceVoiceBindingHint();
});
profileSelect.addEventListener('change', () => {
  checkBindingStatus();
  updateWorkspaceVoiceBindingHint();
});
```

**结论**: Provider 和 Profile change 都会触发 `checkBindingStatus()`，但当前 populateProfileSelect 不按 provider 过滤。

### 2.4 window._voiceBindMap 结构

**结构**: `voice_id -> bindings[]`

```javascript
{
  voiceId: [
    {
      id: b.id || null,
      binding_id: b.id || null,
      profile_id: profileId,
      provider: provider,
      model: b.model || null,
      status: 'available',
      provider_voice_id: voiceId,
      voice_id: voiceId,
      provider_voice_name: b.provider_voice_name || null,
      voice_name: b.provider_voice_name || b.voice_name || null,
    }
  ]
}
```

**B2 结论**: 不应改变 `_voiceBindMap` 的 key 结构。

### 2.5 Binding status 查询

**函数**: `checkBindingStatus()` (`index.html` line ~4160-4229)

- 查询: `/api/voice/profiles/{profileId}/bindings`
- 过滤: `provider + status='available'`
- 逻辑: **profile → provider** 查询，不是 provider → profiles 查询

### 2.6 isWorkspaceBindingAvailable guard

**位置**: `index.html` line ~4079-4081, 被 `handleGenerate()` 调用 (line ~3356)

```javascript
function isWorkspaceBindingAvailable() {
  return workspaceBindingAvailable === true;
}
```

**guard 调用** 在 `handleGenerate()` 最开头（`checkBindingStatus()` 之后）。

**结论**: guard 仍必须保留作为最后防线。

### 2.7 参数区 DOM 结构

**位置** (`index.html` line ~1368-1393):

```html
<div class="form-group full-width">
  <label>语音参数（可选，不填使用绑定默认值）</label>
  <div class="param-row">
    <div class="param-item">
      <input type="number" id="paramSpeed" ...>
    </div>
    <div class="param-item">
      <input type="number" id="paramVol" ...>
    </div>
    <div class="param-item">
      <input type="number" id="paramPitch" ...>
    </div>
    <div class="param-item">
      <select id="paramEmotion">...</select>
    </div>
  </div>
</div>
```

**B2 结论**: 可以通过禁用 `.param-row` 或其子元素来整体静音参数区。不应清空用户输入。

### 2.8 生成按钮

**位置**: `index.html` 内 `handleGenerate()` 函数

**结论**: B2 可以增加 UI 禁用/提示，但不能移除 `handleGenerate` guard。B2 禁用参数区时生成按钮应同时禁用或保持 guard + 明确提示。

## 3. 当前问题

| 问题 | 说明 |
|---|---|
| Profile-first UI | populateProfileSelect 全量填充，不按 provider 过滤 |
| 先选错再拦截 | 用户可选无 binding profile，生成时被 guard 拦截 |
| 参数区不受约束 | 无 binding 时参数仍可编辑，用户可能误以为有效 |
| binding detail 不透明 | 无法快速看出当前 provider 下哪些 profile 有 binding |

## 4. Profile 下拉策略对比

| 方案 | 描述 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| A | 隐藏无 binding profile | 最不易误选 | 用户以为 profile 丢失 | ❌ |
| B | 全部显示，无 binding 禁用 | 不丢 profile | disabled option 提示不统一 | ⚠️ 兜底 |
| C | 全部显示，标记"未绑定当前 Provider" | 最透明 | 仍可选中需引导 | ✅ 推荐 |

**推荐**: 方案 C 为主，方案 B 兜底。不隐藏 profile。

**标记文案**:
```
旁白女声
旁白男声（未绑定当前 Provider）
客服音色（未绑定当前 Provider）
```

## 5. UI 状态机

### 状态定义

| 状态 | 条件 | profileSelect | bindingStatus | 参数区 | 生成按钮 |
|---|---|---|---|---|---|
| S1 | provider 未选择 | 全量，可选 | 空 | 禁用 | 禁用 |
| S2 | provider 已选，provider 下无任何 binding | 全量，标记未绑定 | 空或"无可用绑定" | 禁用 | 禁用 |
| S3 | provider 已选，profile 未选 | 全量，标记未绑定 | 空 | 禁用 | 禁用 |
| S4 | provider+profile 已选，该 provider 下无 binding | 全量，当前 profile 标记未绑定 | "该人设未绑定当前 Provider" | 禁用 | 禁用 |
| S5 | provider+profile 已选，binding available | 全量，当前 profile 正常 | "✓ 已绑定: voice · provider/model" | 可用 | 可用 |
| S6 | binding status API error | 保持 | "绑定状态检查失败" | 禁用 | 禁用 |

### 状态文案

```
S2/S3: "当前 Provider 下暂无可用人设绑定，请到「绑定管理」创建绑定，或切换 Provider。"
S4: "该人设未绑定当前 Provider，请到「绑定管理」创建绑定。"
S6: "绑定状态检查失败，请重试或切换 Provider。"
```

## 6. 参数区策略

| 场景 | 文本输入 | 参数区 | 生成按钮 |
|---|---|---|---|
| 无 binding (S2/S3/S4) | 保持可编辑 | 禁用 + 静音提示 | 禁用 |
| 有 binding (S5) | 保持可编辑 | 恢复可用 | 可用 |
| API error (S6) | 保持可编辑 | 禁用 | 禁用 |

**原则**: 不清空用户文本，只禁用执行入口。

## 7. Provider 切换行为

1. **Provider 切换后**: 刷新 workspace profile 下拉的可用性标记（重新检查 `_voiceBindMap`）
2. **如果当前 profile 在新 provider 下无 binding**: 保留 profile 选择，显示未绑定提示，参数区禁用
3. **如果当前 profile 在新 provider 下有 binding**: 立即展示 binding detail
4. **不清空**: 用户文本、参数值、生成模式

## 8. Mock 场景

- Provider = mock 时，只根据 mock 下 available bindings 判断 profile 可用性
- mock **不 fallback** minimax
- mock 下无 binding 时，显示空状态：

```
当前 Provider 下暂无可用人设绑定。
请到「绑定管理」创建 mock 绑定，或切换 Provider。
```

## 9. 与 B1 / Capability UI 的关系

### 与 B1 的关系

B1 已完成：
- `currentWorkspaceBindingInfo` + `getCurrentWorkspaceBindingInfo()`
- binding hint 展示 `voiceLabel · provider/modelLabel`
- ContextStore/SampleStore 保存 `binding_id/model/provider_voice_id`

B2 基于 B1：
- B2 不再解决"能不能看到 binding/model"
- B2 解决"当前 provider 下哪些 profile/binding 可选、可执行"

### 与 Capability UI 的关系

```
B2: provider → profile/binding 可用性
Capability UI: provider/model → 功能参数可用性
```

**分层结论**: 如果没有 binding，就没有确定的 model，也就不能准确应用 capability。**Capability UI 应在 B2 后评估**。

## 10. B2 最小实现建议

### 应纳入

```text
1. 新增 workspace 专用 helper：getWorkspaceProfileBindingState(provider, profileId)
   → 返回 'available' | 'unbound' | 'no-provider' | 'error'

2. 新增 workspace 专用 helper：refreshWorkspaceProfileAvailability()
   → 遍历 _cachedProfiles，检查每个 profile 在当前 provider 下是否有 binding
   → 更新 profileSelect options 文案（添加/移除"未绑定当前 Provider"标记）

3. Provider change 后调用 refreshWorkspaceProfileAvailability()

4. Profile change 后刷新 bindingStatus 和参数区状态

5. 无 binding 时禁用参数区或视觉静音

6. 无 binding 时生成按钮禁用或保持 guard + 明确提示

7. 保留 handleGenerate guard（最后防线）

8. 新增静态测试
```

### 不应纳入

```text
1. 不新增 model 下拉
2. 不改 resolve_binding
3. 不改后端/API
4. 不改 schema
5. 不改 Batch/Script
6. 不改 clone/design/import/audition
7. 不做 capability 参数禁用
8. 不做 binding_id 精确执行
9. 不全局修改 populateProfileSelect（影响 binding 管理等模块）
```

## 11. 实现文件边界建议

### 应允许修改

```text
app/static/index.html
tests/test_provider_binding_ui_static.py
docs/*
```

### 谨慎修改

```text
app/static/js/product_hints.js（可能需要读取 binding state）
```

### 默认不改

```text
profile_binding.js
provider_capabilities.js
context_store.js
sample_store.js
sample_sidebar.js
batch_shared.js
audition_records.js
voice_clone.js
voice_design.js
voice_import.js
```

**理由**: B2 应优先控制 Workspace 局部，不扩散到全局 profile/binding 工具。

## 12. 交互点表

| 交互点 | 当前行为 | 目标行为 | B2 实现 | 风险 | 备注 |
|---|---|---|---|---|---|
| Provider 下拉 | 并列选择 | Provider-first，切换后刷新 profile 可用性 | ✅ | 需确保 _voiceBindMap 已加载 | |
| Profile 下拉 | 全量显示，不标记 | 标记"未绑定当前 Provider" | ✅ | 方案 C 为主 | 不隐藏 profile |
| Binding status | 展示 binding detail | 保持，展示逻辑不变 | ❌ | | B1 已实现 |
| 参数区 | 无约束，可编辑 | 无 binding 时禁用 | ✅ | 不清空用户文本 | |
| 生成按钮 | 有 guard | 禁用或保持 guard + 明确提示 | ✅ | 保留 handleGenerate guard | |
| 文本输入 | 无约束 | 保持可编辑 | ❌ | | B2 不改变文本输入 |
| 最近样本 restore | 恢复 provider/profile/binding | 重新校验 binding，不信任历史 context | ⚠️ | 依赖 B2 后评估 | |
| Mock 空状态 | 无特殊处理 | 显示"无可用人设绑定" | ✅ | mock 不 fallback | |
| Provider 切换 | 刷新 bindingStatus | 刷新 profile 可用性标记 + bindingStatus | ✅ | | |
| Profile 切换 | 刷新 bindingStatus | 刷新 bindingStatus + 参数区状态 | ✅ | | |
| API error | 显示"绑定状态检查失败" | 禁用参数区 + 生成按钮 | ✅ | 保持 guard | |

## 13. 风险清单

| ID | 风险 | 缓解措施 |
|---|---|---|
| P16-BINDING-UI-RISK-001 | 当前 profile-first UI 容易让用户选择当前 Provider 下无 binding 的人设 | B2 实现方案 C 标记 |
| P16-BINDING-UI-RISK-002 | 无 binding 时参数区仍可编辑，用户可能误以为参数有效 | B2 禁用参数区 + 提示 |
| P16-BINDING-UI-RISK-003 | Provider 切换后，如果 profile 可用性没有同步更新，可能展示旧 binding 状态 | B2 在 provider change 时刷新可用性 |
| P16-BINDING-UI-RISK-004 | 直接隐藏无 binding profile 可能让用户以为 profile 丢失 | B2 采用方案 C，不隐藏 |
| P16-BINDING-UI-RISK-005 | 最近样本 restore 后，provider/profile/binding 状态需要重新校验，不能只相信历史 context | B2 后评估；restore 应触发 checkBindingStatus |
| P16-BINDING-UI-RISK-006 | 禁用生成按钮可能与 setLoading/confirm 逻辑冲突，需要保留 handleGenerate guard | B2 保留 guard 作为最后防线 |
| P16-BINDING-UI-RISK-007 | 全局修改 populateProfileSelect 可能影响绑定管理、Batch、Script 等模块 | B2 新增 workspace 专用 helper，不全局改 populateProfileSelect |

## 14. 设计结论

**核心语义**:
- Provider 是第一约束
- 当前 Provider 下无 binding 的 profile 应标记"未绑定当前 Provider"，不应隐藏
- 无 binding 时参数区禁用/提示，生成按钮禁用
- 保留 handleGenerate guard 作为最后防线
- B2 不做 capability 参数禁用，不新增 model 下拉，不改后端

**后续路线**:
```
B2-A0 (design) → B2 (implement) → B2-CHECK → Capability-UI-B1
```

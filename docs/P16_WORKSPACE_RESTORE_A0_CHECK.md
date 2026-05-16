# P16-WORKSPACE-RESTORE-A0-CHECK：Workspace 最近样本完整恢复方案复核

## 1. 阶段背景

P16-WORKSPACE-RESTORE-A0 完成了 workspace 最近样本完整恢复方案审查。本阶段对 A0 结论进行代码事实复核，判断是否可以进入 P16-WORKSPACE-RESTORE-B1 实现阶段。

## 2. 远端状态核验

```
6f62662 docs: audit workspace sample restore design (P16-WORKSPACE-RESTORE-A0)
202b792 docs: verify cancellation fix (P16-CANCEL-FIX1-CHECK)
22849ad fix: cancellation confirmation semantics and loading state (P16-CANCEL-FIX1)
a7b1f7e docs: verify cancellation state-machine audit
9e15521 docs: audit real usage issues
```

p16/real-usage-issues 相对 dev ahead by 5，behind by 0。状态正常。

## 3. A0 文档复核

`P16_WORKSPACE_RESTORE_A0.md` 完整记录了：
- 当前问题（fillTextInput 只填文本，不恢复参数）
- SampleSidebar 当前行为（sample-btn-fill 只有 data-text）
- SampleStore 当前字段（无 full_text/genMode/speed 等）
- Workspace 写入链路（buildWorkspaceSampleContext 缺失参数字段）
- ContextStore 扩展可行性（可新增 workspace type）
- 方案 A vs B 对比（推荐 B）
- workspace context 字段设计
- 旧样本兼容策略
- UI 恢复流程
- B1 实现边界参考

**结论**：A0 文档结构完整，内容准确。✅

## 4. SampleSidebar 事实复核

### 4.1 fillTextInput

`sample_sidebar.js` lines 457-466：

```javascript
function fillTextInput(text) {
  var input = document.getElementById('textInput');
  if (input) {
    input.value = text;
    input.focus();
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }
}
```

- 只写 `textInput.value` ✅
- 不恢复 provider / profile_id / genMode / speed / vol / pitch / emotion 等 ✅
- 不读 sample_id / 不读完整 sample ✅

### 4.2 buildCard sample-btn-fill

`sample_sidebar.js` line 234：

```html
<button class="sample-btn-fill"
  data-text="..."
  title="填入工作台">↓</button>
```

- 只有 `data-text` 属性 ✅
- 无 `data-provider` / `data-profile-id` / `data-gen-mode` 等 ✅

### 4.3 bindActionEvents

`sample_sidebar.js` lines 315-319：

```javascript
if (target.classList.contains('sample-btn-fill') && text) {
  fillTextInput(decodeURIComponent(text));
  return;
}
```

- 只读 `data-text` ✅
- 不传递 context_id / provider / profile 等 ✅

**复核结论**：A0 对 SampleSidebar 的判断全部准确。✅

## 5. SampleStore 字段复核

`sample_store.js` lines 68-103 `normalizeSample` 返回字段：

```
sample_id / created_at / source / job_id / batch_id / segment_id /
asset_id / download_url / text_preview（上限100字） /
profile_id / profile_name / provider / model /
voice_id / voice_name / duration_ms / audio_format / status / tags / context_id
```

**缺失字段**（A0 记录准确）：
- full_text ❌（未保存）
- output_format ❌（未保存）
- need_subtitle ❌（未保存）
- genMode ❌（未保存）
- variant_count ❌（未保存）
- speed ❌（未保存）
- vol ❌（未保存）
- pitch ❌（未保存）
- emotion ❌（未保存）

**text_preview 上限 100 字**：`TEXT_PREVIEW_MAX = 100`，A0 描述准确。✅

**复核结论**：A0 对 SampleStore 的字段判断全部准确。✅

## 6. Workspace 写入链路复核

`index.html` lines 2457-2493 `buildWorkspaceSampleContext`：

保存字段：`text_preview`（100字截断）/ `profile_id` / `profile_name` / `provider` / `model` / `job_id` / `audio_format` / `voice_id` / `voice_name`

**缺失**：`full_text` / `output_format` / `need_subtitle` / `genMode` / `variant_count` / `speed` / `vol` / `pitch` / `emotion`

`safePushWorkspaceSample`（lines 2495-2543）直接将 `_workspaceSampleContext` 字段写入 SampleStore，无补充字段。

**现有 `_workspaceSampleContext` 不适合作为完整恢复来源**，因为 `text_preview` 上限 100 字，无法恢复完整文本。✅

**复核结论**：A0 对写入链路的判断准确。✅

## 7. ContextStore 扩展可行性复核

`context_store.js`：
- MAX_CONTEXTS = 50 ✅
- `normalizeContext` 对 `type === 'longtext'` 调用 `normalizeLongtextContext` ✅
- `normalizeContext` 对 `type === 'script'` 调用 `normalizeScriptContext` ✅
- 未知 type 分支直接 return minimal fields，不抛错 ✅

**扩展 workspace type 可行**：
1. 新增 `normalizeWorkspaceContext(input, out)` 函数
2. 在 `normalizeContext` 中添加 `else if (type === 'workspace')` 分支

**复核结论**：ContextStore 可扩展，方案 B 可行。✅

## 8. 方案对比复核

**方案 A（扩展 SampleStore）**：
- 优点：实现简单 ✅
- 缺点：SampleStore 变重 / localStorage 占用增加 / 与 longtext/script 机制不一致 / text_preview 100字仍无法解决完整文本 ✅

**方案 B（扩展 ContextStore）**：
- 优点：机制一致 / SampleStore 保持轻量 / full_text 可完整保存 / 扩展性好 ✅
- 缺点：需新增 normalize 函数 / 需在生成成功时写入 / 需新增 restore 函数 ✅

**方案 B 优于方案 A**：
1. longtext/script 已用 ContextStore，机制一致
2. SampleStore 定位为 metadata，不应塞完整文本和参数
3. full_text 可完整保存，不受 100 字限制

**复核结论**：推荐方案 B 合理。✅

## 9. Workspace context 字段复核

A0 推荐字段（lines 174-207）：

| 字段 | 是否必需 | 备注 |
|---|---|---|
| context_id | 是 | 唯一标识 |
| type='workspace' | 是 | 类型标记 |
| source | 是 | 记录来源 |
| created_at | 是 | 时间戳 |
| full_text | 是 | 完整文本，区别于100字限制 |
| provider | 是 | 核心配置 |
| profile_id | 是 | 核心配置 |
| gen_mode | 是 | 单条/异步/流式/多版本 |
| variant_count | 是（variants） | 仅多版本用 |
| audio_format | 是 | 输出配置 |
| output_format | 是 | 输出配置 |
| need_subtitle | 是 | 输出配置 |
| params.speed/vol/pitch/emotion | 是 | 语音参数 |
| job_id | 否 | 追踪用 |
| asset_id | 否 | 追踪用 |
| download_url | 否 | 追踪用 |

**额外可保存但非恢复必需的字段**：model / voice_id / voice_name / profile_name — B1 可选择性保存，不影响恢复逻辑。

**命名一致性**：ContextStore 内部使用 snake_case，DOM 恢复时映射到对应 id/name/value。✅

**复核结论**：workspace context 字段完整，覆盖所有恢复参数。✅

## 10. 旧样本兼容策略复核

A0 策略：
- 旧样本（无 `context_id`）：`fillTextInput(text_preview)`，行为不变 ✅
- 新样本（有 `workspace_context_id`）：`restoreWorkspaceContext(context)`，完整恢复 ✅

**需保证不破坏**：
- longtext 详情恢复（已有 `context_id → 详情面板 → restoreLongtextContext`）✅
- script 详情恢复（已有 `context_id → 详情面板 → restoreScriptContext`）✅
- batch 样本不显示 fill（`canShowFill(sourceRaw)` 逻辑不受影响）✅
- 侧边栏播放/下载/删除/复制按钮 ✅

**复核结论**：旧样本兼容策略清晰，不破坏现有功能。✅

## 11. UI 恢复流程复核

A0 列出 17 个恢复步骤（lines 243-263）：

1. 切换到 workspace Tab ✅
2. 恢复 textInput（full_text）✅
3. 恢复 providerSelect ✅
4. 恢复 profileSelect ✅
5. 恢复 audioFormat ✅
6. 恢复 outputFormat ✅
7. 恢复 needSubtitle.checked ✅
8. 恢复 genMode radio ✅
9. 恢复 variantCount（仅 variants）✅
10. 恢复 paramSpeed ✅
11. 恢复 paramVol ✅
12. 恢复 paramPitch ✅
13. 恢复 paramEmotion ✅
14. 触发 input/change 事件 ✅
15. 不自动提交 ✅
16. 不调用 MiniMax ✅
17. 可选 toast 提示 ✅

**恢复只恢复表单，不自动生成**。✅

**复核结论**：UI 恢复流程完整。✅

## 12. B1 实现边界

### B1 建议纳入

1. `context_store.js`：新增 `normalizeWorkspaceContext` / 在 `normalizeContext` 中添加 workspace 分支
2. `index.html`：handleGenerate 成功后写入 ContextStore workspace context
3. `sample_store.js`：确保 `pushSample` 时写入 `context_id`
4. `sample_sidebar.js`：`buildCard` 传递 `context_id` 给 fill 按钮 / `bindActionEvents` 新增 `restoreWorkspaceContext` / 新增 `restoreWorkspaceContext` 函数
5. 旧样本无 `context_id` 时继续 `fillTextInput` 降级
6. 新增静态测试覆盖 workspace context 字段
7. 不自动提交
8. 不调用真实 MiniMax

### B1 不纳入

- 后端 API / 服务端创作记录
- Provider / Mock 问题
- Capability 动态 UI
- 多版本等待态
- 剧本扩展
- 统计模块
- SampleStore 大 schema 扩展

### 后期待办

**P17-CREATION-RECORD-A0**：服务端创作记录与恢复 API 设计。当前 workspace restore 是前端本地最近样本恢复，不是跨设备/长期/服务端创作记录系统。

## 13. Provider / Mock 问题后置复核

A0 记录 **P16-PROVIDER-OBS-001**：Provider / Mock / Capability / 新大模型适配属于 Provider 架构边界问题，后续启动 P16-PROVIDER-BOUNDARY-A0。✅

本阶段未展开 Provider / Mock 修复。✅

## 14. 复核结论

**通过**。A0 对所有代码事实判断准确：
- SampleSidebar fillTextInput 只填文本，不恢复参数 ✅
- SampleStore 缺失 full_text/genMode/speed/vol/pitch/emotion 等字段 ✅
- buildWorkspaceSampleContext 无完整文本和参数 ✅
- ContextStore 可扩展 workspace type ✅
- 推荐方案 B（扩展 ContextStore）合理 ✅
- workspace context 字段完整 ✅
- 旧样本兼容策略清晰 ✅
- UI 恢复流程完整 ✅
- B1 实现边界清晰 ✅
- Provider / Mock 问题已后置 ✅

**存在阻塞问题**：否

## 15. 当前阶段推进

- 当前阶段：P16-WORKSPACE-RESTORE-A0-CHECK
- 下一阶段：P16-WORKSPACE-RESTORE-B1

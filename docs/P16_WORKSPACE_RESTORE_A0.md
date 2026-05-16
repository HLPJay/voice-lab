# P16-WORKSPACE-RESTORE-A0：Workspace 最近样本完整恢复方案审查

## 1. 阶段背景

用户真实使用中发现：右侧最近样本点击 ↓ 后只能恢复文本，不能恢复工作台参数（provider / profile / speed / vol / pitch / emotion / genMode 等）。

当前 `fillTextInput()` 只写入 `#textInput`，本质是"填入文本"而非"恢复工作台"。

本阶段只做审查和方案设计，不实现功能代码。

## 2. 当前代码事实

### 2.1 SampleSidebar fillTextInput

**文件**：`app/static/js/sample_sidebar.js` lines 457-466

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

**结论**：当前 ↓ 按钮是"填入文本"，不是"恢复工作台配置"。不恢复任何参数。

### 2.2 sample-btn-fill 按钮构建

**文件**：`app/static/js/sample_sidebar.js` line 234

```html
<button class="sample-btn-fill"
  data-text="..."   <!-- 只有 text，没有其他字段 -->
  title="填入工作台">↓</button>
```

**buildCard** 只传递 `data-text`，不传递 `provider` / `profile_id` / `genMode` 等。

### 2.3 bindActionEvents 点击处理

**文件**：`app/static/js/sample_sidebar.js` lines 315-319

```javascript
if (target.classList.contains('sample-btn-fill') && text) {
  fillTextInput(decodeURIComponent(text));
  return;
}
```

只读 `data-text`，调用 `fillTextInput(text)`。

## 3. 当前问题确认

| 问题 | 确认 |
|---|---|
| fillTextInput 只写入 textInput | ✅ 确认 |
| fillTextInput 不恢复 provider | ✅ 确认 |
| fillTextInput 不恢复 profile_id | ✅ 确认 |
| fillTextInput 不恢复 audio_format | ✅ 确认 |
| fillTextInput 不恢复 output_format | ✅ 确认 |
| fillTextInput 不恢复 need_subtitle | ✅ 确认 |
| fillTextInput 不恢复 genMode | ✅ 确认 |
| fillTextInput 不恢复 variant_count | ✅ 确认 |
| fillTextInput 不恢复 speed / vol / pitch / emotion | ✅ 确认 |
| sample-btn-fill 只携带 data-text | ✅ 确认 |

**结论**：workspace 最近样本当前只能"填入文本"，不能"恢复工作台配置"。

## 4. SampleStore 当前字段能力

**文件**：`app/static/js/sample_store.js` lines 68-103

**已保存字段**：

```
sample_id / created_at / source / job_id / batch_id / segment_id /
asset_id / download_url / text_preview（上限100字） /
profile_id / profile_name / provider / model /
voice_id / voice_name / duration_ms / audio_format / status / tags / context_id
```

**当前不保存**：

```
full_text / output_format / need_subtitle /
genMode / variant_count / speed / vol / pitch / emotion / workspace_params
```

**关键限制**：`text_preview` 最多 100 字，不能作为完整文本恢复来源。

## 5. Workspace 样本写入链路

**文件**：`app/static/index.html` lines 2457-2543

**buildWorkspaceSampleContext**（lines 2457-2493）保存：

```
text_preview（截断至100字）/ profile_id / profile_name /
provider / model / job_id / audio_format / voice_id / voice_name
```

**safePushWorkspaceSample**（lines 2495-2543）将上述字段写入 SampleStore。

**缺失字段**：`full_text`（完整文本）/ `output_format` / `need_subtitle` / `genMode` / `variant_count` / `speed` / `vol` / `pitch` / `emotion`。

**现有 `_workspaceSampleContext` 不适合作为完整恢复来源**，因为 `text_preview` 最多 100 字，无法恢复完整原始文本。

## 6. ContextStore 扩展可行性

**文件**：`app/static/js/context_store.js`

**当前能力**：
- MAX_CONTEXTS：50
- 支持 type=longtext（含 full_text / params / segment_strategy 等）
- 支持 type=script（含 lines / params 等）
- 不支持 type=workspace（unknown type 返回 minimal fields）
- `normalizeContext` 对未知 type 不抛错，只返回基础字段

**扩展可行性**：ContextStore 可扩展。

新增 `type=workspace` 需要：
1. 新增 `normalizeWorkspaceContext(input, out)` 函数
2. 在 `normalizeContext` 中添加 `else if (type === 'workspace')` 分支

## 7. 方案对比

### 方案 A：扩展 SampleStore

在 SampleStore sample entry 中增加 `workspace_params` / `full_text` 等可选字段。

**优点**：实现简单，点击最近样本可直接恢复。

**缺点**：
- SampleStore 从轻量 metadata 存储变为上下文存储
- localStorage 占用增加
- 与 longtext/script 的恢复机制不一致（两者用 ContextStore）
- 未来字段继续增加时 SampleStore 会变重
- 100 字 text_preview 仍无法解决完整文本恢复

### 方案 B：扩展 ContextStore（推荐）

为 workspace 生成保存 `context_id`。ContextStore 中保存完整 workspace context。SampleStore 只保存 `context_id` 引用。

**优点**：
1. longtext/script 已经使用 ContextStore 实现完整恢复，机制一致
2. SampleStore 保持轻量 metadata 定位
3. 上下文和样本 metadata 职责清晰
4. 旧样本可降级为只填入文本
5. 未来新增 workspace 参数不需要污染 SampleStore
6. full_text 可完整保存，不受 100 字限制

**缺点**：
- 需要新增 workspace context normalize 逻辑
- 需要在 workspace 生成成功后写入 ContextStore
- 需要新增 restoreWorkspaceContext 逻辑
- 需要修改 sample-btn-fill 的 data 属性传递 context_id

## 8. 推荐方案

**推荐方案 B：扩展 ContextStore，新增 workspace context 类型。**

理由：
1. longtext/script 已用 ContextStore，机制一致
2. SampleStore 当前定位是最近样本 metadata，不适合塞完整文本和参数
3. workspace 完整恢复本质也是 context restore
4. 可以保持 SampleStore 轻量
5. 旧样本没有 context_id 时保留"填入文本"降级

## 9. 推荐 workspace context 字段

```javascript
{
  context_id: "job_id 或 sample_id 或 generated id",
  type: "workspace",
  source: "workspace_sync | workspace_async | workspace_stream | workspace_variant",
  created_at: "ISOString",

  // 完整文本（full_text，区别于 text_preview 的 100 字限制）
  full_text: "完整输入文本",

  // 核心配置
  provider: "mock | minimax | ...",
  profile_id: "声音人设 ID",
  gen_mode: "single | async | stream | variants",
  variant_count: 3,

  // 输出配置
  audio_format: "mp3 | wav | flac",
  output_format: "hex | url",
  need_subtitle: true,

  // 语音参数
  params: {
    speed: 1.0,
    vol: 1.0,
    pitch: 0,
    emotion: "neutral",
  },

  // 追踪字段（不作为恢复必需）
  job_id: "job_xxx",
  asset_id: "audio_xxx",
  download_url: "/api/voice/assets/xxx/download"
}
```

**字段说明**：
- `full_text` 用于完整恢复文本（区别于 `text_preview` 的 100 字上限）
- `provider` / `profile_id` 用于恢复核心配置
- `gen_mode` 用于恢复单条/异步/流式/多版本模式
- `variant_count` 仅多版本使用
- `audio_format` / `output_format` / `need_subtitle` 恢复输出配置
- `params`（speed/vol/pitch/emotion）恢复语音参数
- `job_id` / `asset_id` / `download_url` 用于追踪，不作为恢复必需字段

## 10. 旧样本兼容策略

**旧 workspace 样本**（没有 `context_id`）：
- 点击 ↓ 仍执行当前 `fillTextInput(text_preview)`
- 只恢复文本，行为不变

**新 workspace 样本**（有 `workspace_context_id`）：
- 按钮语义可升级为"恢复工作台"
- 点击 ↓ → 从 ContextStore 读取 workspace context → 恢复完整配置

**按钮策略建议**：

| 样本类型 | 按钮 title | 行为 |
|---|---|---|
| 旧样本（无 context_id） | "填入文本" | fillTextInput(text_preview) |
| 新样本（有 workspace context_id） | "恢复工作台" | restoreWorkspaceContext(context) |

**需保证不破坏**：
- longtext 详情恢复（已有 context_id → 详情面板）
- script 详情恢复（已有 context_id → 详情面板）
- batch 样本不显示 fill 的规则

## 11. UI 恢复流程

恢复 workspace context 时应做到：

```
1. 切换到 workspace Tab
2. 恢复 textInput（full_text，不是 text_preview）
3. 恢复 providerSelect
4. 恢复 profileSelect
5. 恢复 audioFormat
6. 恢复 outputFormat
7. 恢复 needSubtitle.checked
8. 恢复 genMode radio（single/async/stream/variants）
9. 恢复 variantCount（仅 variants）
10. 恢复 paramSpeed
11. 恢复 paramVol
12. 恢复 paramPitch
13. 恢复 paramEmotion
14. 触发 input/change 事件
15. 不自动提交
16. 不调用 MiniMax
17. 可选：toast 轻量提示"已恢复工作台配置"
```

**恢复只恢复表单，不自动生成。**

## 12. 不进入范围

本阶段不处理：
- Provider / Mock / 新大模型能力边界问题
- 多版本等待态
- 剧本扩展
- 统计模块
- 后端/API
- SampleStore schema 强制变更
- ContextStore schema 强制变更

## 13. Provider / Mock / 新大模型能力问题后置观察

**P16-PROVIDER-OBS-001**：
Provider / Mock / Capability / 新大模型适配属于 Provider 架构边界问题，不进入当前 workspace restore 修复范围。后续应单独启动 Provider Boundary 阶段处理。

**建议后续阶段名**：
```
P16-PROVIDER-BOUNDARY-A0：Provider / Mock / Capability / Future Model Adapter Boundary Audit
```

## 14. 下一阶段建议

| 后续阶段 | 内容 | 前提 |
|---|---|---|
| P16-WORKSPACE-RESTORE-A0-CHECK | 复核 workspace restore 设计文档 | P16-WORKSPACE-RESTORE-A0 完成 |
| P16-WORKSPACE-RESTORE-B1 | 实现 workspace context save/detail/restore | P16-WORKSPACE-RESTORE-A0-CHECK 完成 |
| P16-PROVIDER-BOUNDARY-A0 | Provider / Mock / Capability / Future Model Boundary Audit | Backlog，Provider 问题专项 |
| P16-VARIANTS-UX-FIX1 | 多版本试音等待态 | 可后置 |
| P13-HISTORY-SECURITY-FIX1 | escape history text snippet | 小型安全债 |

## 15. 实现边界参考（P16-WORKSPACE-RESTORE-B1）

以下为下一阶段实现时需要改动的文件（仅供设计参考，本阶段不修改）：

**需要改动**：
- `app/static/index.html`：handleGenerate 中写入 ContextStore workspace context
- `app/static/js/sample_sidebar.js`：buildCard 传递 context_id；bindActionEvents 新增 restoreWorkspaceContext；新增 restoreWorkspaceContext 函数
- `app/static/js/context_store.js`：新增 normalizeWorkspaceContext；在 normalizeContext 中添加 workspace 分支

**不需要改动**：
- `app/static/js/sample_store.js` schema（只需确保 pushSample 时写入 context_id）
- 后端 API
- Provider 逻辑

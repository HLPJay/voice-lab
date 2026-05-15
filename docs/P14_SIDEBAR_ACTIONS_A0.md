# P14-SIDEBAR-ACTIONS-A0：侧边栏按钮显示策略设计

**日期：2026-05-16**
**前提：P14-CONTEXT-B2-CLOSE 完成**

## 1. 背景

P14-CONTEXT-B2 已完成长文本 context 保存与详情查看。SampleSidebar 样本卡片当前有 6 个操作按钮（播放、下载、详情、复制文本、填入工作台、删除）。后续 P14-CONTEXT-B3 将增加"长文本一键回填"能力。如果不先设计按钮显示策略，卡片操作区会继续变得拥挤，影响可用性。

本阶段只做设计审查，不实现代码。

## 2. 当前按钮事实

### 2.1 按钮渲染逻辑（`buildCard` 函数）

| 按钮 | 显示条件 | 触发 |
|------|---------|------|
| 播放 ▶ | `isSafeAudioUrl(download_url)` — download_url 以 `/api/` `http://` `https://` 开头，非 blob: | `playSample(sampleId)` |
| 下载 ⇩ | 同播放条件 | `<a download>` 直接跳转 |
| 详情 ⓘ | `sample.context_id` 存在 | `showSampleDetail(sampleId)` |
| 复制文本 ⎘ | 无条件 | `copyText(text)` |
| 填入工作台 ↓ | 无条件 | `fillTextInput(text)` — 写入 `#textInput` |
| 删除 ✕ | 无条件 | `deleteSample(sampleId)` |

**当前无条件显示的按钮**：复制文本、填入工作台、删除（共 3 个）
**当前有条件显示的按钮**：播放、下载（依赖 download_url）、详情（依赖 context_id）

### 2.2 当前 CSS 布局

```css
.sample-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
/* 按钮尺寸统一 26×26px，flex-wrap 允许换行 */
```

### 2.3 样本来源类型（`sourceLabel`）

```javascript
{
  workspace_sync: '单条',
  workspace_async: '异步',
  workspace_stream: '流式',
  workspace_variant: '多版本',
  audition: '试听',
  batch_longtext_merged: '长文合并',
  batch_script_merged: '剧本合并',
  batch_longtext_segment: '长文分段',  // 不常用
  batch_script_segment: '剧本分段',      // 不常用
}
```

## 3. 当前问题分析

### 3.1 按钮密度过高

当前最多同时显示 6 个按钮（播放、下载、详情、复制、填入、删除）。`flex-wrap: wrap` 在窄屏下会自动换行，但一行 2～3 个按钮时已显得拥挤。

### 3.2 语义重叠

- **复制文本** 和 **填入工作台** 都只处理 `text_preview`，功能高度重叠
- **详情**（读 full_text）和 **填入工作台**（写 text_preview）面向不同用户意图，不应并列平铺

### 3.3 危险操作视觉权重过高

删除按钮（✕）与其他操作按钮样式相同，视觉权重没有区分。在没有二次确认（batch 级有 `window.confirm`，单卡删除直接调用 `deleteSample`）的情况下，误点风险存在。

### 3.4 后续 B3 会增加第 7 个按钮

P14-CONTEXT-B3 的"长文本一键回填"如果也做成平铺按钮，卡片操作区会达到 7 个按钮，无法接受。

### 3.5 移动端可用性

在 `flex-wrap: wrap` 下，6 个按钮在窄屏（< 400px）下会变成 3 行。按钮区高度增加，但 sidebar 本身有 `max-height` 限制，可能导致部分卡片不可见。

### 3.6 没有安全 download_url 时的退化

没有 `download_url` 时，播放和下载都不显示，此时只剩详情、复制、填入、删除 4 个按钮。但详情只在有 `context_id` 时才显示，可能只剩 3 个。这与有 audio 时显示 6 个按钮之间存在巨大体验落差。

## 4. 按钮分层策略

### 4.1 分层原则

```
主操作（Primary）：每张卡片必有，视觉最突出
  → 播放 ▶  — 核心交互，无替代方案
  → 详情 / 恢复 — 揭示完整内容，语义丰富

平铺次操作（Flat Secondary）：每张卡片可见，但视觉权重低于主操作
  → 下载 ⇩  — 有 download_url 时显示，频率低于播放

更多菜单（More Menu）：收纳低频操作，减少视觉噪音
  → 复制文本
  → 填入工作台
  → 删除（低视觉权重或放入确认）

危险操作（Danger）：删除不与其他操作平权
```

### 4.2 推荐平铺按钮上限

**每张卡片最多 4 个平铺按钮**：播放、详情/恢复、下载、"更多"

超过 4 个的操作全部收入"更多"菜单。

### 4.3 "更多"菜单设计

使用 CSS `:hover` 或 `click` 切换的 inline dropdown，不依赖额外 JS 框架：

```css
.sample-btn-more {
  position: relative;
}
.sample-more-menu {
  display: none;
  position: absolute;
  right: 0;
  top: 100%;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 100;
}
.sample-btn-more:hover .sample-more-menu,
.sample-btn-more.open .sample-more-menu {
  display: block;
}
```

菜单内每个操作占一行，包含图标和文字标签。

## 5. 按样本类型制定显示策略

### 5.1 workspace_sync / workspace_async / workspace_stream / workspace_variant

| 操作 | 显示策略 |
|------|---------|
| 播放 | 有 safe download_url 时显示 |
| 下载 | 有 safe download_url 时显示 |
| 详情 | 有 context_id 时显示（通常无） |
| 恢复 | 无 — workspace 样本无 context，不支持恢复 |
| 复制 | 始终显示 → 入"更多"菜单 |
| 填入 | 始终显示 → 入"更多"菜单（写 `#textInput`） |
| 删除 | 始终显示 → 入"更多"菜单，确认后删除 |

**说明**：workspace 样本没有关联 context_id（`context_id = null`），详情按钮不显示。复制和填入工作台对 workspace 样本有意义（将生成文本填回工作区）。

### 5.2 audition

| 操作 | 显示策略 |
|------|---------|
| 播放 | 有 safe download_url 时显示 |
| 下载 | 有 safe download_url 时显示 |
| 详情 | 有 context_id 时显示（通常无） |
| 恢复 | 无 |
| 复制 | 入"更多"菜单 |
| 填入 | 入"更多"菜单 |
| 删除 | 入"更多"菜单 |

**说明**：audition 样本通常没有 context_id，详情按钮不显示。

### 5.3 batch_longtext_merged

| 操作 | 显示策略 |
|------|---------|
| 播放 | 有 safe download_url 时显示 |
| 下载 | 有 safe download_url 时显示 |
| 详情 | 有 context_id 时显示（通常有，B2 已实现） |
| 恢复（B3） | B3 阶段：在详情面板内增加"恢复到长文本"按钮 |
| 复制 | 入"更多"菜单 |
| 填入 | 无意义（长文本不写入 `#textInput`）→ 不显示 |
| 删除 | 入"更多"菜单 |

**说明**：`batch_longtext_merged` 样本有 `context_id`，详情按钮显示。B3 的回填功能**不新增平铺按钮**，而是放在详情面板底部。

### 5.4 batch_script_merged

| 操作 | 显示策略 |
|------|---------|
| 播放 | 有 safe download_url 时显示 |
| 下载 | 有 safe download_url 时显示 |
| 详情 | 有 context_id 时显示（C1 阶段实现后） |
| 恢复（C2） | C2 阶段：在详情面板内增加"恢复到剧本"按钮 |
| 复制 | 入"更多"菜单 |
| 填入 | 无意义（剧本不写入 `#textInput`）→ 不显示 |
| 删除 | 入"更多"菜单 |

**说明**：C1 阶段实现后，`batch_script_merged` 才有 context_id。

### 5.5 batch_longtext_segment / batch_script_segment

| 操作 | 显示策略 |
|------|---------|
| 播放 | 有 safe download_url 时显示 |
| 下载 | 有 safe download_url 时显示 |
| 详情 | 有 context_id 时显示 |
| 其他操作 | 谨慎处理，segment 是中间态，复制/填入意义有限 |

**说明**：segment 样本是 batch 的单个片段，通常由系统生成，用户直接操作的频率极低。

### 5.6 旧样本（无 context_id）

| 操作 | 显示策略 |
|------|---------|
| 播放/下载 | 正常显示（依赖 download_url） |
| 详情 | 不显示（无 context_id） |
| 复制/填入/删除 | 入"更多"菜单 |

**说明**：旧样本指 P14-CONTEXT-B2 实现前已存在的 SampleStore 条目，ContextStore 中无对应记录。这些样本的详情按钮不出现，但播放/下载/复制/填入/删除功能完全正常。

## 6. 推荐方案

### 6.1 方案名称

**v1 按钮分层 + 详情面板内回填**（推荐）

### 6.2 核心规则

1. **平铺按钮最多 4 个**：播放、详情、下载、"更多"
2. **"更多"菜单**收纳：复制文本、填入工作台、删除
3. **删除**在"更多"菜单内，视觉权重低（灰色小字），不需要二次确认图标
4. **详情面板**是 longtext/script 恢复的唯一入口，B3/C2 的回填不新增平铺按钮
5. **没有 safe download_url**：播放和下载都不显示，不影响其他按钮布局

### 6.3 平铺按钮显示规则

```
播放   ▶  ：有 safe download_url
详情   ⓘ  ：有 context_id（longtext/script context）
下载   ⇩  ：有 safe download_url
更多   ⋯  ：始终显示（菜单内至少 1 个操作时）
```

### 6.4 "更多"菜单操作清单

```
├── 复制文本      — 始终显示
├── 填入工作台    — 有 context_id 的样本不显示（无意义）
└── 删除          — 始终显示，低视觉权重
```

### 6.5 B3 回填策略（不在本 A0 范围）

详情面板底部增加（仅当 `context.type === 'longtext'`）：

```
[恢复到长文本]  ← 放在详情面板底部，不新增平铺按钮
```

点击后：
1. 关闭详情面板
2. 切换到 Batch > 长文本 tab
3. 恢复 `#batchText = context.full_text`
4. 恢复 `#batchProfile = context.profile_id`
5. 恢复 provider / audio_format / need_subtitle 等参数
6. 不自动提交

### 6.6 不采用"升级详情为恢复按钮"方案的原因

如果直接将详情按钮升级为"恢复"按钮，workspace/audition 样本（无 context_id）将完全无法触发详情查看。只有 longtext/script 样本才需要恢复功能，详情查看是所有样本的通用需求。

### 6.7 不采用"第 7 个平铺按钮"方案的原因

6 个按钮已拥挤，7 个按钮在视觉上无法接受。"更多"菜单可以优雅地收纳低频操作，同时保持主操作区简洁。

## 7. 后续阶段拆分

```
P14-SIDEBAR-ACTIONS-B1：侧边栏按钮分层与更多菜单实现
  - CSS 实现更多菜单 dropdown
  - 重构 buildCard，平铺按钮最多 4 个
  - bindActionEvents 支持更多菜单点击
  - 填入工作台在 longtext/script 样本上不显示
  - 删除移入更多菜单，视觉权重降低

P14-CONTEXT-B3：长文本一键回填
  - 在 showSampleDetail 中，当 context.type === 'longtext' 时
  - 详情面板底部显示"恢复到长文本"按钮
  - 实现 fillLongtextContext(context) 函数
  - 切换到 Batch > 长文本 tab
  - 恢复字段值，不自动提交

P14-CONTEXT-C1-A0：剧本 context 保存与详情查看前置审查

P14-CONTEXT-C1：剧本 context 保存与详情查看实现

P14-CONTEXT-C2：剧本一键回填
```

## 8. B0 结论

### 设计决策

- 平铺按钮上限 4 个：播放、详情、下载、更多
- "更多"菜单收纳：复制文本、填入工作台、删除
- 回填功能放在详情面板内，不新增平铺按钮
- 填入工作台对 longtext/script 样本不显示（无意义）
- 删除在更多菜单内，视觉低权重

### 阶段状态

A0 完成，建议进入 P14-SIDEBAR-ACTIONS-B1 实现。

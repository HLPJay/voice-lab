# P10 产品打磨计划

## P10-PRODUCT-A0 产品打磨优先级审查

**审查时间：** 2026-05-15

**产品定位：** 本地 Web App / 单用户 AI 音频创作工作台

---

## 1. 当前产品能力矩阵

| 功能 | 状态 | 产品化程度 |
|---|---|---|
| 同步 T2A（workspace） | ✅ 可用 | 高 |
| 异步 T2A（workspace） | ✅ 可用 | 高 |
| 流式 T2A（workspace） | ✅ 可用 | 中 |
| 长文本批量（longtext tab） | ✅ 可用 | 高 |
| 剧本科本批量（script tab） | ✅ 可用 | 高 |
| 音色试听（voices tab） | ✅ 可用 | 中 |
| 历史记录（history tab） | ✅ 可用 | 高（P8-4 完成） |
| 桌面宽屏布局 | ✅ 可用 | 中（P8-UX1 完成） |
| localStorage 任务恢复 | ✅ 可用 | 中（P8-5 完成） |
| 声音克隆（advanced/clone） | ✅ 可用 | 低 |
| 声音设计（advanced/design） | ✅ 可用 | 低 |
| 音色导入（advanced/import） | ✅ 可用 | 低 |
| 绑定管理（advanced/bindings） | ✅ 可用 | 低 |
| Admin 统计 | ✅ 可用 | 内部 |
| 移动端 H5 | ❌ 未做 | 不优先 |

---

## 2. 实际用户主流程审查

### 2.1 单条旁白生成流程（主流程）

```
进入工作台（默认 tab）
↓
选择人设（profile select）
↓
输入文本（text input）
↓
选择/切换音色（在右侧 audition workstation 选择）
↓
点击"生成"按钮
↓
等待结果（同步/异步/流式）
↓
播放音频
↓
下载音频 / 查看字幕
↓
任务进入历史记录
```

**当前问题：**
- 音色选择入口在右侧 audition workstation，但入口不明显
- 没有"先选音色再输入文本"的引导
- 音色 tab 是独立 tab，用户需要跳转离开当前流程

### 2.2 音色管理流程

```
进入音色 tab（voices tab）
↓
浏览音色列表（按 provider/voice_type 筛选）
↓
点击音色行 → 自动填入 audition workstation
↓
或：点击"快速绑定" → 绑定到人设
↓
导入音色 / 克隆音色 / 设计音色（advanced tab）
```

**当前问题：**
- 音色 tab 和创作工作台分离，流程不连贯
- 没有"音色工作台"的概念引导
- clone/design/import 入口在 advanced tab，入口深

### 2.3 长文本批量流程

```
进入长文本 tab
↓
选择人设
↓
输入长文本（支持分段策略）
↓
选择音色
↓
配置参数（speed/vol/pitch/emotion）
↓
点击"生成批量任务"
↓
查看进度面板
↓
等待完成
↓
播放/下载
↓
任务进入历史记录
```

**当前问题：**
- 批量任务和音色管理没有联动
- 批量音色选择需要跳转到 voices tab 选完再回来

### 2.4 剧本科本批量流程

```
进入剧本 tab
↓
添加台词行（角色 + 文本）
↓
为每行选择人设
↓
选择音色
↓
点击"生成批量任务"
↓
查看进度面板
↓
等待完成
↓
播放/下载
```

**当前问题：**
- 剧本格式模板没有预设场景
- 批量音色选择同样需要跳转

---

## 3. 产品打磨优先级评估

### 3.1 优先级 1：主流程打磨（workspace 入口优化）

**理由：** 80% 用户使用单条旁白生成，workspace 是默认 tab，优化价值最高

**具体问题：**
- 音色入口在右侧 audition workstation，入口不直观
- 新用户不知道"先选音色再输入文本"
- profile 选择器在页面顶部，不在主要工作流内

**建议方案（轻量，不改架构）：**
- 在 workspace tab 增加音色快捷选择区（放在文本输入上方或下方）
- 显示当前选中音色名称和"切换音色"按钮
- audition workstation 保持不变，避免和 voices tab 功能重复

**风险：** 低（仅改 UI 布局，不改业务逻辑）

**E2E 需求：** `test_workspace_voice_quick_select`

### 3.2 优先级 2：音色工作台与创作流程联动

**理由：** 音色是核心创作资源，当前 voices tab 孤立于创作流程之外

**具体问题：**
- 用户在 voices tab 选中音色后，需要跳转到 workspace 继续创作
- 批量任务（长文本/剧本）同样需要跳转选音色
- 没有"音色 → 输入文本 → 生成"的连贯引导

**建议方案：**
- 在 voices tab 增加"快速创作"入口（选中音色后直接跳转 workspace 并带入音色）
- 或者在 workspace 增加"从音色列表选择"的 inline 入口

**风险：** 中（涉及 tab 间跳转逻辑）

### 3.3 优先级 3：历史记录与当前任务联动

**理由：** P8-4 已完成历史 card 化，但历史和当前创作流程仍分离

**具体问题：**
- 用户生成后需要主动切换到 history tab 查看历史
- 没有"最近生成"快捷入口

**建议方案（轻量）：**
- 在 workspace 顶部增加"最近任务"快捷入口（3条），点击可快速恢复
- 或在结果区增加"查看同类历史"快捷入口

**风险：** 低

### 3.4 优先级 4：Batch 音色选择优化

**理由：** 长文本和剧本批量都依赖音色选择，当前需要跨 tab 操作

**具体问题：**
- 长文本 tab 和剧本 tab 的音色选择需要跳转到 voices tab
- 没有音色快速切换能力

**建议方案：**
- 在长文本/剧本 tab 内增加音色快速选择区（类似 workspace 的 audition workstation）
- 复用已有的 `populateVoiceSelect` / `loadVoices`

**风险：** 中（需确保批量 tab 和 voices tab 音色状态同步）

### 3.5 优先级 5：Advanced 功能入口整理

**理由：** clone/design/import 在 advanced tab，入口深但功能已完整

**具体问题：**
- 新用户不知道 advanced tab 里有 clone/design
- 入口文案不引导

**建议方案（轻量）：**
- Advanced tab 重命名为更明确的名称（如"音色工具"）
- 在 voices tab 增加 clone/design 快捷引导

**风险：** 低

### 3.6 优先级 6：First-time user guidance

**理由：** 当前没有任何 onboarding，用户进来不知道从哪开始

**建议方案（极轻量）：**
- Workspace tab 增加简短引导文案（如"输入文本，选择人设和音色，点击生成"）
- Profile 为空时显示"请先到设置添加人设"

**风险：** 极低

---

## 4. 不应该继续投入的方向

### 4.1 移动端 H5 适配

**原因：**
- 产品定位为"本地 Web App / 单用户"
- 当前主要使用场景是桌面端
- H5 适配成本高，收益低
- 建议等用户量上来后再评估

### 4.2 创作模板 / 场景入口

**原因：**
- 当前剧本格式完全靠用户自己编辑
- 模板需要内容运营，不适合当前阶段
- 建议先打磨基础体验再考虑模板

### 4.3 SaaS 多用户功能

**原因：**
- 产品定位不含多用户
- 需要完整的用户/session/credential 体系
- 当前阶段不引入

### 4.4 开放 API 平台

**原因：**
- 复杂度高
- 当前阶段不做

### 4.5 桌面 App 打包（Electron/Tauri）

**原因：**
- 当前 Web App 已可用
- 打包需要额外工程化成本
- 等 Web 版验证后再评估

---

## 5. P10 任务排序建议

| 优先级 | 任务 | 风险 | 预计工作量 |
|---|---|---|---|
| 1 | Workspace 音色快捷选择区 | 低 | 小 |
| 2 | Voices tab 快速创作联动 | 中 | 中 |
| 3 | Batch tab 音色快速选择 | 中 | 中 |
| 4 | 简化 onboarding 文案 | 极低 | 极小 |
| 5 | Advanced tab 重命名 | 极低 | 极小 |
| 6 | 历史最近任务快捷入口 | 低 | 小 |

**建议节奏：** 逐个任务执行，每个任务一个小 commit，附带 E2E。

---

## 6. P10 与前端模块化的关系

P10 产品打磨**不依赖**前端模块化，可以并行推进。

P9 的结论是暂停前端模块化，转产品打磨。两者独立。

P10 打磨过程如需改动 JS 逻辑，应在当前 index.html 架构内修改，不引入新的模块化变更。

---

## 7. 后续阶段

| 阶段 | 内容 | 前提 |
|---|---|---|
| P10 | 产品打磨（轻量 UX 改进） | 无 |
| P11 | 后端能力增强（如有需求） | 用户反馈 |
| P12 | 本地 App 打包评估 | P10 完成 |
| 后续 | SaaS / 多用户 | 产品验证后 |

---

## 8. 附录：P8 产品化已完成清单

以下功能已完成产品化打磨，无需继续投入：

- ✅ 同步/异步/流式结果卡片化（P8-3）
- ✅ 历史任务 card 化（P8-4B）
- ✅ 历史播放入口安全降级（P8-4C）
- ✅ 历史下载入口安全降级（P8-4D）
- ✅ 历史搜索/筛选（P8-4E）
- ✅ 桌面宽屏布局（P8-UX1）
- ✅ localStorage 任务恢复（P8-5）
- ✅ 高消费动作二次确认（P8-FIX7）
- ✅ 顶部用量状态条（P8-UX2/UX3）
- ✅ 音色选择/试听工作站（P8-2）
- ✅ 前端信息架构重组（P8-1）
- ✅ 声音克隆/设计/导入模块抽离（P9-FE1）

---

## P10-PRODUCT-B0：Workspace 音色快捷选择区边界审查

**审查时间：** 2026-05-15

**性质：** 文档记录，不改业务代码，不新增 UI，不迁移模块

---

### B0 审查范围

- Workspace tab 当前 DOM 结构
- profile / provider / textInput / generate button 位置关系
- 当前选中音色状态的来源
- B1 最小实现方案边界

---

### 当前 Workspace tab DOM 结构

```
tab-workspace
├── hint card ("创作工作台" 说明)
├── card: "文案输入" — textarea#textInput
└── card: "配置"
    ├── profileSelect — 人设下拉（绑定 voice 用的 profile）
    ├── providerSelect
    ├── audioFormat
    ├── outputFormat
    ├── 语音参数（speed/vol/pitch/emotion）
    ├── 生成模式（单条/异步/流式/多版本）
    └── needSubtitle
```

**注意：** Audition workstation（auditionSelectedBanner / auditionSelected）不在 workspace tab 内，而是渲染在 voices tab（`#voiceListResults` 内部）。

---

### 两个独立的音色选择系统

| 系统 | 用途 | 状态变量 | 所在 tab |
|---|---|---|---|
| Profile binding | Workspace 生成音频 | `profileSelect.value` | workspace |
| Voice audition | Voices tab 试听预览 | `window._auditionSelectedVoiceId` | voices |

**关键发现：**

- `handleGenerate`（workspace 生成）使用 `profileSelect.value`，该 profile 需先绑定 voice
- 用户需要在 voices tab 用 `bindVoiceToProfile` 将 voice 绑定到 profile
- Audition workstation 的 `_auditionSelectedVoiceId` 是试听系统，和 workspace 生成流程是不同的概念
- Workspace tab 内无任何当前选中音色的视觉提示

---

### 当前音色绑定流程

```
workspace：选择 profile（需已有 voice 绑定）
voices tab：选择 voice → 点击"绑定到人设" → 绑定 voice 到 profile
workspace：选择该 profile → 生成音频
```

用户常见困惑：选了 profile 后不知道还需要绑定 voice，或者不知道去哪绑定 voice。

---

### B1 最小实现方案

**不改：**
- `handleGenerate` — 使用 `profileSelect.value`，无需改动
- `bindVoiceToProfile` — 已完整可用
- 后端 API — 无需改动
- voice list / voice table — 不改动

**只新增（workspace "配置" card 内）：**
- 在 `profileSelect` 下方增加轻量"当前音色"提示区
- 显示当前选中 profile 已绑定的 voice（从 `_voiceBindMap` 读取）
- 无 voice 绑定时显示"该人设尚未绑定音色"
- 增加"去选择音色"按钮，点击切换到 voices tab

**按钮实现：**
```javascript
document.querySelector('.tab-btn[data-tab="voices"]').click();
```
不新增跨 tab 状态联动，不改 `window._auditionSelectedVoiceId`。

**B1 验收标准：**
1. workspace 的"配置"区显示当前 profile 绑定的 voice（如果有）
2. "去选择音色"按钮切换到 voices tab
3. `handleGenerate` 行为不变
4. 不调用真实 MiniMax API

**B1 E2E 需求：** 可选（聚焦展示，不改生成链路）

---

### B1 影响范围

| 文件 | 改动 |
|---|---|
| `app/static/index.html` | 仅在 workspace "配置" card 的 `profileSelect` 下方增加提示区 HTML 和事件绑定 |
| 后端 API | 无 |
| E2E | 可选 |

---

### B0 审查结论

B1 可按上述最小方案执行，不改生成链路，不改 voice list，不改后端。主要是增加 UI 引导，减少用户困惑。

---

## P10-PRODUCT-B1：Workspace 音色快捷选择区实现

**执行时间：** 2026-05-15

### 实现内容

**新增 DOM：** `#workspaceVoiceBindingHint`（位于 workspace "配置" card 的 `profileSelect` 下方）

**新增函数：** `updateWorkspaceVoiceBindingHint()`
- 读取 `profileSelect.value` 和 `providerSelect.value`
- 从 `window._voiceBindMap` 查找当前 profile 在当前 provider 下是否有已绑定 voice
- 有绑定：显示"当前音色：voice_id (model)"
- 无绑定：显示"该人设尚未绑定音色" + "去选择音色"按钮

**事件绑定：**
- `profileSelect.addEventListener('change')` → `updateWorkspaceVoiceBindingHint()`
- `providerSelect.addEventListener('change')` → `updateWorkspaceVoiceBindingHint()`
- `populateAllProfiles()` 末尾调用 `updateWorkspaceVoiceBindingHint()`
- workspace tab 切换回调：`loadProfiles(true).then(...).then(updateWorkspaceVoiceBindingHint)`

**按钮实现：** 使用 `addEventListener` 动态绑定，不使用内联 `onclick`（避免 HTML 属性中转义引号问题）

### B1 验收结果

| 验收项 | 结果 |
|---|---|
| workspace 的"配置"区显示当前 profile 绑定的 voice（如果有） | ✅ |
| 无绑定时显示"该人设尚未绑定音色" | ✅ |
| "去选择音色"按钮切换到 voices tab | ✅ |
| `handleGenerate` 行为不变 | ✅ |
| 不调用真实 MiniMax API | ✅ |

### E2E

- `test_workspace_voice_binding_hint_switches_to_voices` — mock profiles/bindings/capabilities，验证 hint 显示"尚未绑定音色"，点击"去选择音色"切换到 voices tab
- **结果：26 passed**

### E2E 输出

- `tests/e2e/test_frontend_capabilities.py` — 新增 Test 26

---

## P10-PRODUCT-B2：Voices tab 快速创作联动 — 边界审查

**审查时间：** 2026-05-15

**性质：** 文档记录，不改业务代码，不迁移模块

---

### B2 审查范围

- Voices tab 现有绑定成功后的提示流程
- `quickBindVoice` 成功消息文本（line 3894）
- 绑定成功后用户是否需要手动切换到 workspace tab
- B2 最小实现方案边界

---

### 当前绑定成功后的流程

`quickBindVoice`（line 3894）绑定成功后显示：
```
✓ 绑定成功。现在可以回到创作工作台，选择该声音人设进行生成。
```

**问题：**
- 只有文本提示，没有可点击的"去创作"按钮
- 用户需要自己切换到 workspace tab
- 引导路径断裂

---

### B2 最小实现方案

**不改：**
- `handleGenerate` — 不改生成链路
- `bindVoiceToProfile` — 已完整可用
- 后端 API — 无需改动
- voice list / voice table — 不改动

**只新增（quickBindVoice 成功消息中）：**
- 在成功消息文本后增加"去创作"按钮
- 点击切换到 workspace tab

**实现方式：**
```javascript
// 成功消息中增加按钮（line 3894 附近）
msgEl.innerHTML = `<div style="background:#f0fff4;border:1px solid #c6f6d5;border-radius:6px;padding:8px 10px;font-size:0.78rem;color:#2f855a">
  ✓ 绑定成功。现在可以回到创作工作台，选择该声音人设进行生成。
  <button type="button" id="quickBindGoCreateBtn" style="margin-left:8px;font-size:0.75rem;padding:2px 8px;cursor:pointer">去创作</button>
</div>`;
// 绑定按钮事件
document.getElementById('quickBindGoCreateBtn').addEventListener('click', function() {
  var wsBtn = document.querySelector('.tab-btn[data-tab="workspace"]');
  if (wsBtn) wsBtn.click();
});
```

**验收标准：**
1. 绑定成功后显示"去创作"按钮
2. 点击"去创作"切换到 workspace tab
3. `handleGenerate` 行为不变
4. 不调用真实 MiniMax API

---

### B2 影响范围

| 文件 | 改动 |
|---|---|
| `app/static/index.html` | 仅在 quickBindVoice 成功消息内增加按钮和事件绑定 |
| 后端 API | 无 |
| E2E | 可选（聚焦展示，不改生成链路） |

---

### B0 审查结论

B2 可按上述最小方案执行，不改生成链路，不改绑定逻辑。主要是将文本提示升级为可点击按钮，减少用户操作步骤。

---

## P10-PRODUCT-B2-A0：Voices tab 快速创作联动 — 边界审查（简化版）

**审查时间：** 2026-05-15

**结论：** B2 可行，方案已在上节确定。实现时仅在 quickBindVoice 成功消息中增加"去创作"按钮，点击切换到 workspace tab。

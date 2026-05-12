# P8: 前端 UX 修复 — 内联创建人设 + 音色试听工作台 + 绑定反馈闭环 + 分页

## 背景

P7 实现了跨模块数据关联，但前端测试发现四类交互断点：

1. **音色管理 Tab 没有创建人设入口**：用户在音色列表点击「绑定到人设」时，如果没有可用人设，只弹 `alert` 提示去绑定管理 Tab 创建。声音克隆 / 声音设计的快速绑定面板也有同样问题。
2. **音色列表无法试听**：查询到的音色列表只能看到名称和绑定状态，无法试听和评估每个音色的效果。
3. **绑定操作没有反馈闭环**：绑定成功后只显示一行小字，音色列表的「绑定状态」列没有实时刷新，用户感知不到绑定已生效。删除音色需要手动输入 voice_id，没有跟列表联动。
4. **音色列表无分页**：查询结果硬编码 `slice(0, 50)` 截断显示，无法查看后续音色，无法设置每页数量。

## 修改范围

仅修改 `app/static/index.html`，纯前端变更，无后端改动。

---

## 问题 1：内联创建人设

### 1.1 音色管理 Tab — `quickBindVoice()` 函数 (约第 1909 行)

**当前行为**：如果 `profiles.length === 0`，执行 `alert(...)` 并 `return`，用户被卡住。

**目标行为**：

- 删除 `alert` + `return` 分支
- 无论是否有已有人设，都展示绑定面板
- 在人设下拉 `<select>` 旁边添加一个「+ 新建」按钮
- 点击「+ 新建」展开一个内联创建表单（折叠式，不跳转 Tab），包含：
  - 人设 ID（必填，`placeholder="如 narrator_female"`）
  - 人设名称（必填，`placeholder="如 女性旁白"`）
  - 「确认创建」按钮
- 创建成功后：
  - 调用 `await loadProfiles(true)` 刷新全局缓存
  - 重新 `populateProfileSelect()` 填充当前面板的下拉
  - 自动选中刚创建的人设 ID
  - 折叠创建表单
  - 显示绿色提示「人设已创建：xxx」

**API 调用**：
```js
POST /api/voice/profiles
Body: { "id": "xxx", "name": "xxx" }
```

### 1.2 声音克隆结果面板 — `handleCloneVoice()` 中快速绑定区 (约第 2128 行)

与 1.1 相同的逻辑：在 `cloneBindProfile` 下拉旁添加「+ 新建」按钮和折叠式创建表单。

### 1.3 声音设计结果面板 — `handleDesignVoice()` 中快速绑定区 (约第 2280 行)

与 1.1 相同的逻辑：在 `designBindProfile` 下拉旁添加「+ 新建」按钮和折叠式创建表单。

### 1.4 提取公共函数

三处逻辑完全相同，应提取为可复用函数：

```js
/**
 * 在指定容器内渲染「+ 新建人设」按钮和折叠表单。
 * @param {HTMLElement} container - 按钮插入的父容器
 * @param {HTMLSelectElement} selectEl - 创建成功后需要刷新的下拉框
 * @param {string} idPrefix - 元素 ID 前缀，避免 DOM ID 冲突（如 'quick', 'clone', 'design'）
 */
function renderInlineCreateProfile(container, selectEl, idPrefix) { ... }
```

---

## 问题 2：音色试听工作台

在音色列表表格**上方**添加一个独立的「试听工作台」面板，作为统一的试听入口。不在每行内联播放，而是用一个专属区域做试听 + 标注。

### 2.1 试听工作台 UI 布局

在 `voiceListResults` 容器和查询按钮之间，在音色列表加载完成后，渲染一个固定的试听面板 `#voiceAuditionPanel`：

```
┌─────────────────────────────────────────────────────────────────┐
│  试听工作台                                                      │
│                                                                 │
│  试听文本：[________________________ 可编辑 textarea ___________] │
│                                                                 │
│  当前选中：（无）         模型：[speech-2.8-hd ▾]  [▶ 生成试听]   │
│                                                                 │
│  ┌─ 试听结果 ────────────────────────────────────────────────┐  │
│  │  (空)                                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ 试听记录 ────────────────────────────────────────────────┐  │
│  │  voice_id      │ 文本摘要 │ 音频     │ 评分  │ 备注  │ 操作│  │
│  │  narrator_male │ 你好这是… │ [▶ 播放] │ ★★★★☆│ 音质好│ [删]│  │
│  │  ...           │ ...      │ ...      │ ...   │ ...   │ ... │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                 [清空全部记录]    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 音色列表中的「试听」按钮

在 `renderVoiceTable()` 中，操作列（现有「绑定到人设」旁边）增加一个「试听」按钮：

```html
<button class="btn-sm audition-btn"
  data-voice-id="${voiceId}"
  data-name="${voiceName}"
  data-provider="${provider}">试听</button>
```

点击后的行为：
1. 将该音色填入试听工作台的「当前选中」位置（显示 voice_id + 名称）
2. 自动滚动到试听工作台
3. 如果试听文本已填写，自动聚焦「生成试听」按钮（不自动触发，让用户确认文本后手动点击）

### 2.3 试听文本输入

- 使用 `<textarea>` 而不是 `<input>`，支持多行文本
- 默认值：`"你好，这是一段测试语音。欢迎使用语音合成服务。"`
- 行高 2 行，可拖拽扩展
- 试听文本在整个页面生命周期内保持，切换音色不清空

### 2.4 生成试听逻辑

点击「生成试听」按钮后：

1. **前置检查**：
   - 必须已选中一个音色（否则提示「请先在下方音色列表点击试听按钮选择音色」）
   - 试听文本不能为空
2. **检查绑定状态**：
   - 查 `window._voiceBindMap`，看当前选中 voice_id 是否已绑定到某个人设
   - **已绑定**：直接使用绑定的 `profile_id` 和 `provider`
   - **未绑定**：在工作台内展示一个人设选择区（下拉框 + 「+ 新建」按钮），让用户选择或新建人设后再生成
3. **调用 API**：
   ```js
   POST /api/voice/render
   Body: { "text": "...", "profile_id": "...", "provider": "minimax" }
   ```
4. **展示结果**：
   - 在「试听结果」区显示 `<audio>` 播放器，自动播放
   - 显示基本信息：时长、voice_id
5. **自动添加到试听记录**：生成成功后，自动在「试听记录」表格中追加一行（详见 2.5）

### 2.5 试听记录表格 + 本地标注

试听记录表格保存本次会话中所有试听过的音色效果，方便对比。

**每行字段**：

| 字段 | 来源 | 说明 |
|------|------|------|
| voice_id | 自动填入 | 音色 ID（code 样式显示） |
| 音色名称 | 自动填入 | 来自音色列表的 name |
| 文本摘要 | 自动截取 | 试听文本前 15 字 + `…` |
| 音频 | 自动填入 | `<audio>` 播放器（mini 样式，仅 controls） |
| 评分 | **用户标注** | 5 星评分（点击星星切换，默认无评分） |
| 备注 | **用户标注** | 可编辑 `<input>`，`placeholder="添加备注…"` |
| 操作 | - | 「删除」按钮，删除该行记录 |

**数据存储**：
- 使用 JS 数组 `window._auditionRecords = []` 保存在内存
- 每条记录结构：
  ```js
  {
    voiceId: string,
    voiceName: string,
    text: string,        // 完整试听文本
    audioUrl: string,    // /api/voice/assets/... 的路径
    rating: number|null, // 1-5 或 null
    note: string,        // 用户备注
    timestamp: number,   // Date.now()
  }
  ```
- 页面刷新后清空（纯会话级，不持久化到后端）
- 同一个 voice_id + 同一段文本 再次试听，追加新行（不覆盖旧的），方便对比不同文本下同一音色的效果

**表格底部**：
- 显示记录总数：`共 N 条试听记录`
- 「清空全部记录」按钮（需 `confirm` 确认）

### 2.6 评分交互

- 5 个星星图标（可用 Unicode `★` / `☆`），排成一行
- 点击第 N 个星星 → 设置评分为 N（1-5）
- 再次点击已选中的星星 → 取消评分（设为 null）
- 星星颜色：选中 `#f6ad55`（橙色），未选中 `#e2e8f0`（灰色）
- hover 时预览效果（hover 第 3 颗 → 前 3 颗高亮）

### 2.7 试听工作台的显示/隐藏

- 音色列表加载完成后才显示试听工作台（`renderVoiceTable` 执行后）
- 如果列表为空，不显示工作台
- 工作台位于音色列表表格的正上方

---

## 问题 3：绑定操作反馈闭环 + 操作列增强

### 3.1 绑定成功后刷新列表绑定状态

**当前行为**：`quickBindVoice()` 绑定成功后，只在 `quickBindMsg` 里显示一行小绿字 `"绑定成功: xxx → xxx"`。音色列表的「绑定状态」列仍然显示旧状态（如「未绑定」），用户必须重新查询才能看到变化。

**目标行为**：绑定成功后，执行以下刷新动作：

1. 显示明显的成功提示（保留现有绿色文字即可）
2. **实时刷新绑定状态列**：调用 `loadAllBindings()` 重新加载 `window._voiceBindMap`，然后更新当前音色行的绑定状态 `<td>` 内容
3. 具体实现方式：
   ```js
   // 绑定成功后
   window._voiceBindMap = await loadAllBindings();
   // 找到当前行并更新绑定状态列
   const row = document.querySelector(`tr[data-voice-id="${voiceId}"]`);
   if (row) {
     const statusCell = row.querySelector('.bind-status-cell');
     const boundProfiles = window._voiceBindMap[voiceId];
     statusCell.innerHTML = boundProfiles && boundProfiles.length > 0
       ? `<span style="color:#2f855a;font-size:0.78rem">已绑定: ${boundProfiles.join(', ')}</span>`
       : `<span style="color:#ed8936;font-size:0.78rem">未绑定</span>`;
   }
   ```
4. 需要为表格行和绑定状态列添加 `data-voice-id` 属性和 `.bind-status-cell` class，方便定位。

**修改位置**：
- `renderVoiceTable()` 中为 `<tr>` 添加 `data-voice-id="${voiceId}"`
- 绑定状态 `<td>` 添加 `class="bind-status-cell"`
- `quickBindVoice()` 绑定成功回调中加入刷新逻辑
- 声音克隆 / 声音设计的快速绑定成功回调同理

### 3.2 音色列表操作列增强

**当前行为**：操作列只有一个「绑定到人设」按钮。删除音色是页面底部一个独立表单，需要手动输入 voice_id。

**目标行为**：操作列根据音色类型显示不同按钮：

| 音色类型 | 操作按钮 |
|----------|----------|
| system（系统音色） | `[试听]` `[绑定到人设]` |
| voice_cloning（克隆音色） | `[试听]` `[绑定到人设]` `[删除]` |
| voice_generation（设计音色） | `[试听]` `[绑定到人设]` `[删除]` |

- 系统音色不可删除，不显示删除按钮
- 克隆 / 设计音色可删除，显示红色「删除」按钮
- 删除按钮点击后弹出 `confirm("确定删除音色 xxx？此操作不可恢复")`
- 确认后调用：
  ```js
  DELETE /api/voice/provider-voices/${provider}/${voiceId}?voice_type=${voiceType}
  ```
- 删除成功后：从列表中移除该行（DOM 直接删除，不重新查询），显示短暂提示
- 删除失败：红色提示错误信息

**修改位置**：
- `renderVoiceTable()` 中根据 `v.voice_type` 条件渲染操作按钮
- 新增 `handleDeleteVoiceFromList(voiceId, provider, voiceType, rowEl)` 函数

### 3.3 删除音色表单联动（可选优化）

底部的「删除音色」独立表单保留，但增加一个小优化：
- 如果用户在音色列表点击某行，自动将 `voice_id` 填入底部删除表单的输入框
- 这是次要优化，如果实现复杂可跳过

---

## 问题 4：音色列表分页

### 4.1 当前问题

- `handleListVoices()` 中 `voices.slice(0, 50)` 硬编码截断，超过 50 条的音色完全不可见
- `renderVoiceTable()` 中同样 `voices.slice(0, 50)`
- 底部只显示 `"显示前 50 条（共 N 条），请用搜索过滤"` 提示，无法翻页

### 4.2 分页控件

在音色列表表格的**下方**渲染分页控件 `#voicePagination`：

```
共 128 条音色  每页：[20 ▾]  ← 上一页  第 1/7 页  下一页 →
```

**控件元素**：
- **总数显示**：`共 N 条音色`（来自 `window._loadedVoices.length`，搜索后显示过滤结果数）
- **每页条数选择**：`<select>` 下拉，选项 `[20, 50, 100, 全部]`，默认 `20`
  - 选择「全部」时一次显示所有音色
  - 切换每页条数后重置到第 1 页
- **翻页按钮**：「← 上一页」和「下一页 →」
  - 第 1 页时禁用「上一页」
  - 最后一页时禁用「下一页」
- **页码显示**：`第 X/Y 页`

### 4.3 分页状态

用全局变量管理分页状态：
```js
window._voicePagination = {
  currentPage: 1,
  pageSize: 20,     // 默认每页 20 条
  totalItems: 0,    // 过滤后的总数
};
```

### 4.4 修改 renderVoiceTable()

**当前签名**：`renderVoiceTable(voices, provider, total, voiceBindMap)`

**改造逻辑**：
1. 删除 `voices.slice(0, 50)` 硬编码
2. 根据 `_voicePagination.currentPage` 和 `_voicePagination.pageSize` 计算当前页的切片范围
3. 如果 `pageSize === 'all'`，显示全部
4. 渲染表格后，在表格下方渲染分页控件
5. 翻页按钮的 `onclick` 修改 `_voicePagination.currentPage` 后重新调用 `renderVoiceTable()`

### 4.5 搜索与分页联动

`filterVoiceList()` 函数过滤后：
1. 重置 `_voicePagination.currentPage = 1`
2. 更新 `_voicePagination.totalItems = filtered.length`
3. 将过滤后的完整数组传给 `renderVoiceTable()`，由 `renderVoiceTable` 内部分页

### 4.6 删除底部旧提示

删除现有的 `"显示前 50 条（共 N 条），请用搜索过滤"` 提示，改由分页控件替代。

---

## 样式要求

- 试听工作台整体用 `.card` 样式包裹，标题用 `.card-title`
- 「+ 新建」按钮使用 `btn-sm` 样式，文字为 `+ 新建`
- 内联创建表单背景色 `#fffbeb`（浅黄），圆角 `6px`，`padding: 8px`
- 折叠动画不要求（`display:none / block` 切换即可）
- 试听按钮使用 `btn-sm` 样式
- 试听记录表格复用 `.voice-table` 样式
- 评分星星 `font-size: 1.1rem`，`cursor: pointer`，间距 `2px`
- 备注输入框：无边框底线风格，`border: none; border-bottom: 1px dashed #cbd5e0`，聚焦时 `border-bottom-color: #4299e1`
- 「当前选中」显示区：选中时绿色背景 `#f0fff4`，未选中时灰色文字
- 删除按钮使用 `btn-sm` 样式 + `color: #e53e3e`
- 分页控件整体 `display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 12px; font-size: 0.82rem`
- 翻页按钮使用 `btn-sm` 样式，禁用时 `opacity: 0.4; cursor: not-allowed`
- 每页条数 `<select>` 使用与其他下拉框一致的样式

## 测试验证

完成后请验证以下场景：

1. **内联创建人设**
   - 无任何人设时，在音色管理 Tab 点击「绑定到人设」→ 应显示面板（含「+ 新建」），不再弹 alert
   - 点击「+ 新建」→ 创建人设 → 下拉框自动刷新并选中新人设
   - 声音克隆成功后，快速绑定面板的「+ 新建」同样可用
   - 声音设计成功后，快速绑定面板的「+ 新建」同样可用

2. **试听工作台**
   - 查询音色列表后，试听工作台出现在表格上方
   - 点击任意音色的「试听」按钮 → 工作台填入该音色，页面滚动到工作台
   - 修改试听文本 → 点击生成 → 音频播放 → 自动记录到试听记录表
   - 切换另一个音色试听 → 试听文本保持不变，新记录追加
   - 星星评分可点击切换、取消
   - 备注可输入保存（行内编辑，输入即保存）
   - 删除单条记录、清空全部记录均可用
   - 未绑定的音色试听时，工作台内显示人设选择（含「+ 新建」）

3. **绑定反馈闭环**
   - 绑定成功后，音色列表中该行的「绑定状态」列立即刷新为「已绑定: xxx」
   - 克隆/设计音色行显示「删除」按钮，系统音色行不显示
   - 点击删除 → confirm 确认 → 该行从列表中消失
   - 声音克隆 / 声音设计面板绑定成功后也有同样的状态刷新

4. **分页**
   - 默认显示 20 条 / 页，总数 > 20 时显示分页控件
   - 点击「下一页」→ 表格切换到第 2 页内容
   - 切换每页条数（20 / 50 / 100 / 全部）→ 重置到第 1 页，表格更新
   - 搜索过滤后 → 分页重置到第 1 页，总数更新为过滤后数量
   - 第 1 页时「上一页」禁用，最后一页时「下一页」禁用
   - 选择「全部」→ 所有音色一页显示，翻页按钮隐藏

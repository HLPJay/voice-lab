# P8-2 音色选择 / 试听工作台

## 1. 当前基线

- 仓库：HLPJay/voice-lab
- 分支：dev
- 前置阶段：P8-1E 已完成
- 最新提交：93c8d28 p8-1e close frontend architecture acceptance gaps
- 当前目标：进入 P8-2，但 P8-2A 只做审查

## 2. P8-2 产品目标

P8-2 的目标是把"音色"tab 从音色管理入口整理成**音色选择 / 试听工作台**。

目标用户流程：

```
查看音色
↓
搜索 / 筛选
↓
选择音色
↓
输入试听文本
↓
生成试听
↓
播放试听结果
↓
绑定到人设
↓
在创作工作台中使用
```

## 3. 当前音色区 DOM id

按功能分类整理：

### 3.1 音色查询

| DOM id | 用途 |
|---|---|
| `voiceProvider` | Provider 选择 |
| `voiceType` | 音色类型筛选（全部/系统音色/克隆音色/设计音色） |
| `listVoicesBtn` | 查询音色按钮 |
| `voiceSearch` | 搜索过滤输入框 |
| `voiceListResults` | 音色列表结果容器（动态插入 audition workstation + table + pagination） |
| `pageSizeSelect` | 每页数量选择 |
| `voicePagination` | 分页容器 |

### 3.2 试听工作台（动态渲染在 voiceListResults 内）

| DOM id | 用途 |
|---|---|
| `voiceAuditionPanel` | 试听工作台面板 |
| `auditionText` | 试听文本输入 |
| `auditionSelected` | 试听选中状态显示 |
| `auditionModel` | 试听模型选择 |
| `auditionProfileSelectWrap` | 试听人设选择包装（选中绑定音色后显示） |
| `auditionProfileSelect` | 试听人设下拉 |
| `auditionGenBtn` | 生成试听按钮 |
| `auditionResult` | 试听结果展示区 |

### 3.3 试听记录

| DOM id | 用途 |
|---|---|
| `auditionRecordsPanel` | 试听记录面板 |
| `auditionCount` | 试听记录数 |
| `auditionClearBtn` | 清空全部记录按钮 |
| `auditionRecordsTable` | 试听记录表格 |

### 3.4 快速绑定（动态渲染在 voiceListResults 内）

| DOM id | 用途 |
|---|---|
| `quickBindPanel` | 快速绑定弹出面板 |
| `quickBindProfileSel` | 快速绑定人设选择 |
| `quickBindModelSel` | 快速绑定模型选择 |
| `quickBindConfirm` | 确认绑定按钮 |
| `quickBindCancel` | 取消绑定按钮 |
| `quickBindMsg` | 快速绑定消息 |

### 3.5 人设与绑定

| DOM id | 用途 | 所在位置 |
|---|---|---|
| `newProfileId` | 新建人设 ID | tab-advanced/subtab-bindings |
| `newProfileName` | 新建人设名称 | tab-advanced/subtab-bindings |
| `newProfileDesc` | 新建人设描述 | tab-advanced/subtab-bindings |
| `newProfileGender` | 新建人设性别 | tab-advanced/subtab-bindings |
| `newProfileAge` | 新建人设年龄 | tab-advanced/subtab-bindings |
| `createProfileResult` | 创建人设结果 | tab-advanced/subtab-bindings |
| `bindingProfileSelect` | 绑定查询人设选择 | tab-advanced/subtab-bindings |
| `bindingListResults` | 绑定列表结果 | tab-advanced/subtab-bindings |
| `newBindingProfile` | 创建绑定人设 | tab-advanced/subtab-bindings |
| `newBindingProvider` | 创建绑定 Provider | tab-advanced/subtab-bindings |
| `newBindingModel` | 创建绑定模型 | tab-advanced/subtab-bindings |
| `newBindingVoiceId` | 创建绑定 voice_id | tab-advanced/subtab-bindings |
| `newBindingPriority` | 创建绑定优先级 | tab-advanced/subtab-bindings |
| `newBindingParams` | 创建绑定参数 | tab-advanced/subtab-bindings |
| `createBindingResult` | 创建绑定结果 | tab-advanced/subtab-bindings |

### 3.6 高风险操作

| DOM id | 用途 | 所在位置 |
|---|---|---|
| `deleteProvider` | 删除音色 Provider | tab-voices（有问题：应该在高级区） |
| `deleteVoiceId` | 删除音色 voice_id | tab-voices（有问题：应该在高级区） |
| `deleteVoiceType` | 删除音色类型 | tab-voices（有问题：应该在高级区） |
| `deleteResults` | 删除结果 | tab-voices（有问题：应该在高级区） |

## 4. 当前音色区 JS 函数

| 函数 | 用途 | 依赖 DOM | 风险 |
|---|---|---|---|
| `handleListVoices()` | 查询音色列表 | voiceProvider, voiceType, listVoicesBtn, voiceListResults | 低风险，纯查询 |
| `filterVoiceList()` | 搜索过滤音色 | voiceSearch, voiceListResults | 低风险，纯前端过滤 |
| `renderVoiceTable()` | 渲染音色表格 | voiceListResults | 低风险，纯渲染 |
| `handlePageSizeChange()` | 改变每页数量 | pageSizeSelect | 低风险，纯 UI 状态 |
| `handlePrevPage()` | 上一页 | voiceListResults | 低风险，纯 UI 状态 |
| `handleNextPage()` | 下一页 | voiceListResults | 低风险，纯 UI 状态 |
| `handleVoiceDeleteFromList()` | 从列表删除音色 | voiceListResults, deleteProvider, deleteVoiceType | **高风险**：直接调用删除 API，且 DOM 在 tab-voices |
| `refreshVoiceBindStatus()` | 刷新音色绑定状态 | voiceListResults | 中风险，涉及绑定 API |
| `renderAuditionWorkstation()` | 渲染试听工作台 HTML | voiceListResults | 低风险，纯渲染 |
| `updateAuditionSelected()` | 更新试听选中状态 | auditionSelected, auditionProfileSelectWrap, auditionProfileSelect | 低风险，纯 UI 状态 |
| `setupAuditionWorkstation()` | 设置试听工作台事件委托 | voiceListResults | 低风险，事件绑定 |
| `renderAuditionRecords()` | 渲染试听记录 | auditionRecordsTable, auditionCount | 低风险，纯渲染 |
| `handleGenerateAudition()` | 生成试听 | auditionText, auditionSelected, auditionModel, auditionResult | **中风险**：产生真实 API 消耗（guardedJsonFetch, highRisk=true） |
| `quickBindVoice()` | 快速绑定音色（弹出面板） | voiceListResults | 中风险，涉及绑定 API |
| `bindVoiceToProfile()` | 执行绑定 | newBindingProfile, newBindingProvider | 中风险，涉及绑定 API |
| `handleCreateProfile()` | 创建人设 | newProfileId, newProfileName, createProfileResult | 中风险，涉及创建 API |
| `handleListBindings()` | 查询绑定列表 | bindingProfileSelect, bindingListResults | 低风险，纯查询 |
| `handleCreateBinding()` | 创建绑定 | newBindingProfile, newBindingProvider, newBindingModel, newBindingVoiceId, createBindingResult | 中风险，涉及创建 API |
| `handleDeleteBinding()` | 删除绑定 | bindingListResults | 高风险，涉及删除 API |
| `handleDeleteVoice()` | 删除音色（tab-voices 内直接入口） | deleteProvider, deleteVoiceId, deleteVoiceType, deleteResults | **高风险**：删除音色，所在位置不当 |

## 5. 当前 API endpoint 依赖

从代码中整理当前音色区涉及的 endpoint：

| 功能 | endpoint | 调用函数 | 高风险 |
|---|---|---|---|
| 音色列表查询 | `GET /api/voice/provider-voices?provider=X&voice_type=Y` | `handleListVoices()` | 否 |
| 音色试听 | `POST /api/voice/provider-voices/preview?provider=X` | `handleGenerateAudition()` | **是**（confirm_cost=false 但 highRisk=true） |
| 人设列表 | `GET /api/voice/profiles` | `loadProfiles()` | 否 |
| 人设创建 | `POST /api/voice/profiles` | `handleCreateProfile()` | 中 |
| 绑定列表 | `GET /api/voice/profiles/{profileId}/bindings` | `handleListBindings()`, `loadAllBindings()` | 否 |
| 绑定创建 | `POST /api/voice/profiles/{profileId}/bindings` | `bindVoiceToProfile()`, `handleCreateBinding()` | 中 |
| 绑定删除 | `DELETE /api/voice/bindings/{bindingId}` | `handleDeleteBinding()` | 高 |
| 删除音色 | `POST /api/voice/voices/delete?provider=X` | `handleVoiceDeleteFromList()` | **高** |
| 成本估算 | `POST /api/voice/cost/estimate` | `updateCostHint()` | 否 |

## 6. 当前用户路径

### 6.1 查询音色

1. 选择 Provider（voiceProvider）
2. 选择音色类型（voiceType，筛选 system/voice_cloning/voice_generation）
3. 点击"查询音色"（listVoicesBtn）
4. handleListVoices() → fetch /api/voice/provider-voices
5. renderVoiceTable() 渲染音色列表（包含 audition workstation）
6. loadAllBindings() 加载所有绑定用于展示绑定状态

### 6.2 搜索音色

1. 在 voiceSearch 输入关键词
2. oninput="filterVoiceList()" 触发
3. 前端本地过滤 window._loadedVoices
4. renderVoiceTable() 重新渲染

### 6.3 选择音色

1. 在音色列表中点击"试听"按钮
2. setupAuditionWorkstation() 事件委托处理
3. updateAuditionSelected(voiceId, voiceName) 更新选中状态
4. window._auditionSelectedVoiceId 设置

### 6.4 生成试听

1. 输入试听文本（auditionText）
2. 选择模型（auditionModel）
3. 点击"生成试听"（auditionGenBtn）
4. handleGenerateAudition() → guardedJsonFetch → /api/voice/provider-voices/preview
5. 展示 audio player 或错误信息
6. 追加到 window._auditionRecords
7. renderAuditionRecords()

### 6.5 查看试听记录

1. 试听记录面板（auditionRecordsPanel）始终显示
2. window._auditionRecords 数组存储
3. renderAuditionRecords() 渲染表格
4. auditionClearBtn 清空全部记录

### 6.6 快速绑定

1. 在音色列表中点击"绑定"按钮
2. quickBindVoice() → 弹出面板 quickBindPanel
3. 选择/创建人设
4. 选择模型
5. 点击确认 → bindVoiceToProfile()
6. refreshVoiceBindStatus() 刷新绑定状态

### 6.7 创建人设

位于 tab-advanced/subtab-bindings：
1. 填写 newProfileId, newProfileName 等
2. handleCreateProfile() → POST /api/voice/profiles

### 6.8 删除音色

**路径存在问题**：删除音色在 tab-voices 内，不在高级 tab：
1. 填写 deleteProvider, deleteVoiceId, deleteVoiceType
2. handleDeleteVoice() → POST /api/voice/voices/delete
3. **风险**：高风险操作混在普通音色选择流程中

## 7. 当前问题与风险

### 7.1 高风险操作位置不当

**删除音色（handleDeleteVoice / handleVoiceDeleteFromList）在 tab-voices 内**，不在高级 tab。

删除音色是高风险不可逆操作：
- 应移入 tab-advanced（与克隆/设计同级）
- 或至少增加 confirm 提示

### 7.2 音色区功能过多

当前 tab-voices 承担了：
- 音色查询
- 音色搜索过滤
- 音色试听
- 试听记录
- 快速绑定
- 删除音色（高风险）
- 绑定状态展示

信息密度过高，用户容易迷失。

### 7.3 试听成本风险

`handleGenerateAudition()` 使用 `guardedJsonFetch(..., highRisk: true)` 但 `confirm_cost: false`。

真实 MiniMax provider 下试听会产生成本：
- 建议增加 mini cost hint
- 或在高成本警告区明确说明

### 7.4 快速绑定误操作风险

quickBindVoice() 直接弹出面板覆盖音色列表：
- 用户可能误点绑定按钮
- 绑定成功/失败消息短暂显示后消失
- 没有明显的"取消"二次确认

### 7.5 绑定管理入口分散

- 快速绑定在 tab-voices（轻量入口）
- 完整绑定管理在 tab-advanced/subtab-bindings

这是合理的分层，但需要明确告知用户。

### 7.6 P8-2B 不应改后端 API

本阶段只整理前端信息架构和交互流程：
- 不改 API endpoint
- 不改 fetch 请求地址
- 不改 JS function behavior（只改 DOM 结构和展示）

### 7.7 音色区 DOM 强耦合

voiceListResults 是动态容器，里面混合了：
- 试听工作台（voiceAuditionPanel）
- 音色表格（voiceTable）
- 分页（pagination）
- 快速绑定面板（quickBindPanel）

改动时需要非常小心，避免破坏其他部分。

## 8. P8-2 分阶段建议

| 阶段 | 目标 | 不做 |
|---|---|---|
| P8-2A | 现状审查与文档化 | 不改代码 |
| P8-2B | 音色 tab 信息架构整理 | 不改 API 和 JS 行为 |
| P8-2C | 试听工作台产品化 | 不改后端 |
| P8-2D | 轻量绑定入口整理 | 不改克隆/设计 |
| P8-2E | 验收与健康检查收口 | - |

## 9. P8-2A 执行记录

### 执行命令

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -8
grep DOM scan -> /tmp/p8_2_voice_dom_scan.txt
grep JS scan -> /tmp/p8_2_voice_js_scan.txt
grep API scan -> /tmp/p8_2_voice_api_scan.txt
git diff --check
python -m pytest tests/ -x -q
```

### 验证结果

- git status -sb：干净（## dev...origin/dev）
- git log --oneline -8：正常
- git diff --check：无 whitespace error
- python -m pytest tests/ -x -q：375 passed, 6 skipped

### 扫描结果摘要

- DOM scan：音色区涉及 30+ DOM id
- JS scan：音色区涉及 20+ JS 函数
- API scan：涉及 9 个不同 endpoint

## 10. P8-2A 验收结果

- 375 passed, 6 skipped
- 未执行真实 MiniMax smoke test（审查阶段不需要消耗额度）

## 11. P8-2A 结论

P8-2A 只完成审查和文档化，不修改前端，不修改后端。下一步建议进入 P8-2B：音色 tab 信息架构整理。

**关键发现摘要**：

1. **删除音色在 tab-voices**，应移入 tab-advanced
2. **试听工作台动态渲染在 voiceListResults 内部**，DOM 结构耦合
3. **快速绑定是弹出面板**，用户体验需优化
4. **tab-voices 承担了 6+ 功能**，信息密度过高
5. **tab-advanced/subtab-bindings 已有完整绑定管理**，快速绑定和绑定管理应有区分
6. **试听产生成本但 confirm_cost=false**，需在高成本警告中体现
7. **所有 DOM id 和 JS function behavior 应保留**，P8-2B 只做架构整理

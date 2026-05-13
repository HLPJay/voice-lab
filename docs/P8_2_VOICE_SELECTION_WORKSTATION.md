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

---

# P8-2B 音色 tab 信息架构整理

## 12. P8-2B 执行背景

- P8-2A 已完成审查，发现删除音色在 tab-voices 内（应在 advanced）
- P8-2B 目标是整理 tab-voices 信息架构
- 本阶段允许最小修改 app/static/index.html

## 13. P8-2B 本阶段目标

- tab-voices 聚焦音色选择 / 试听 / 轻量绑定
- 删除音色迁移到 tab-advanced / 危险操作
- 增加试听成本提示
- 增加轻量绑定说明
- 保留所有 DOM id
- 保留所有 JS function behavior
- 不改 API

## 14. P8-2B 问题与风险分析

1. **删除音色位置不当**：在 tab-voices 内，属于高风险操作
2. **voiceListResults 是强耦合动态容器**：不改 DOM 结构
3. **试听成本提示不足**：增加试听成本提示
4. **快速绑定与高级绑定管理需要分层说明**：增加绑定说明区
5. **高级区新增 danger 子 tab**：需修改 switchAdvancedSubtab 支持 danger
6. **移动 DOM 时必须保留 id**：deleteProvider / deleteVoiceId / deleteVoiceType / deleteResults 必须保留

## 15. P8-2B 方案判断

- 采用最小 DOM 迁移方案
- 只移动删除音色 card
- 不拆 voiceListResults
- 不改音色试听 JS
- 不改绑定 JS
- 不改 API
- 用说明区降低用户理解成本
- 用高级 danger 子 tab 收纳高风险操作

## 16. P8-2B 修改范围

- app/static/index.html
- docs/P8_2_VOICE_SELECTION_WORKSTATION.md
- docs/PROJECT_HEALTH_CHECK.md

## 17. P8-2B 前端结构调整说明

### tab-voices 新结构

1. 音色选择 / 试听工作台说明区（含成本提示）
2. 音色查询与筛选区（voiceProvider, voiceType, listVoicesBtn, voiceSearch）
3. voiceListResults 动态结果区
4. 绑定说明区

### tab-advanced 新结构

1. 高成本 / 工程验证警告（已有）
2. 子 tab 导航：声音克隆 / 声音设计 / 绑定管理 / **危险操作**（新增）
3. subtab-clone（已有）
4. subtab-design（已有）
5. subtab-bindings（已有）
6. **subtab-danger**（新增，含删除音色 card）

## 18. P8-2B 删除音色迁移说明

- 删除音色已从 tab-voices 移入 tab-advanced/subtab-danger
- 保留 deleteProvider / deleteVoiceId / deleteVoiceType / deleteResults（静态 DOM）
- 保留 handleDeleteVoice 函数
- 保留 handleVoiceDeleteFromList 函数
- 不改删除 API endpoint
- 不改删除逻辑

## 19. P8-2B DOM id 保留说明

静态检查确认以下关键 DOM id 仍存在于 app/static/index.html：

| DOM id | 状态 |
|---|---|
| voiceProvider | ✅ 保留 |
| voiceType | ✅ 保留 |
| listVoicesBtn | ✅ 保留 |
| voiceSearch | ✅ 保留 |
| voiceListResults | ✅ 保留 |
| voiceAuditionPanel | ✅ 保留（动态渲染） |
| auditionText | ✅ 保留（动态渲染） |
| auditionSelected | ✅ 保留（动态渲染） |
| auditionModel | ✅ 保留（动态渲染） |
| auditionGenBtn | ✅ 保留（动态渲染） |
| auditionResult | ✅ 保留（动态渲染） |
| auditionRecordsPanel | ✅ 保留（动态渲染） |
| auditionRecordsTable | ✅ 保留（动态渲染） |
| quickBindPanel | ✅ 保留（动态渲染） |
| quickBindProfileSel | ✅ 保留（动态渲染） |
| quickBindModelSel | ✅ 保留（动态渲染） |
| quickBindConfirm | ✅ 保留（动态渲染） |
| quickBindCancel | ✅ 保留（动态渲染） |
| quickBindMsg | ✅ 保留（动态渲染） |
| deleteProvider | ✅ 保留（在 subtab-danger） |
| deleteVoiceId | ✅ 保留（在 subtab-danger） |
| deleteVoiceType | ✅ 保留（在 subtab-danger） |
| deleteResults | ✅ 保留（在 subtab-danger） |

## 20. P8-2B JS function 行为保留说明

静态检查确认所有关键函数仍存在于 app/static/index.html：

| 函数 | 状态 |
|---|---|
| handleListVoices | ✅ 保留 |
| filterVoiceList | ✅ 保留 |
| renderVoiceTable | ✅ 保留 |
| handlePageSizeChange | ✅ 保留 |
| handlePrevPage | ✅ 保留 |
| handleNextPage | ✅ 保留 |
| handleVoiceDeleteFromList | ✅ 保留 |
| refreshVoiceBindStatus | ✅ 保留 |
| renderAuditionWorkstation | ✅ 保留 |
| updateAuditionSelected | ✅ 保留 |
| setupAuditionWorkstation | ✅ 保留 |
| renderAuditionRecords | ✅ 保留 |
| handleGenerateAudition | ✅ 保留 |
| quickBindVoice | ✅ 保留 |
| bindVoiceToProfile | ✅ 保留 |
| handleCreateProfile | ✅ 保留 |
| handleListBindings | ✅ 保留 |
| handleCreateBinding | ✅ 保留 |
| handleDeleteBinding | ✅ 保留 |
| handleDeleteVoice | ✅ 保留 |
| switchAdvancedSubtab | ✅ 保留（已修改支持 danger） |

**switchAdvancedSubtab 修改说明**：
- 修改原因：需要支持新增的 danger 子 tab
- 修改内容：在 show/hide 逻辑中增加 `document.getElementById('subtab-danger').style.display = subtab === 'danger' ? 'block' : 'none'`
- 验证方式：静态检查 + 子 tab 映射检查通过
- 是否影响 clone/design/bindings：**不影响**，仅追加一行条件显示

**本阶段未修改音色查询、试听、绑定、删除相关 JS function 的业务行为。**

## 21. P8-2B 执行命令记录

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -10
grep -n "tab-voices|voiceProvider|..." app/static/index.html  # pre-modification scan
grep -n "tab-advanced|data-subtab|subtab-" app/static/index.html  # pre-modification scan
```

## 22. P8-2B 验证命令记录

```bash
git status -sb
git diff --stat
git diff --check
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["音色选择 / 试听工作台","试听提示","绑定说明","危险操作",
    "subtab-danger","deleteProvider","deleteVoiceId","deleteVoiceType","deleteResults",
    "voiceProvider","voiceType","listVoicesBtn","voiceSearch","voiceListResults",
    "voiceAuditionPanel","auditionText","auditionSelected","auditionModel",
    "auditionGenBtn","auditionResult","auditionRecordsPanel","auditionRecordsTable"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM marker check passed")
PY
python - <<'PY'
import re
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = ["function handleListVoices","function filterVoiceList",
    "function renderVoiceTable","function handleVoiceDeleteFromList",
    "function refreshVoiceBindStatus","function renderAuditionWorkstation",
    "function updateAuditionSelected","function setupAuditionWorkstation",
    "function renderAuditionRecords","function handleGenerateAudition",
    "function quickBindVoice","function bindVoiceToProfile",
    "function handleCreateProfile","function handleListBindings",
    "function handleCreateBinding","function handleDeleteBinding",
    "function handleDeleteVoice","function switchAdvancedSubtab"]
missing = [x for x in required_functions if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("JS function check passed")
PY
python - <<'PY'
import re
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
subtabs = re.findall(r'data-subtab="([^"]+)"', html)
containers = set(re.findall(r'id="subtab-([^"]+)"', html))
missing = [tab for tab in subtabs if tab not in containers]
if missing: raise SystemExit(f"Missing containers: {missing}")
required = ["clone","design","bindings","danger"]
missing_required = [tab for tab in required if tab not in subtabs or tab not in containers]
if missing_required: raise SystemExit(f"Missing required subtabs: {missing_required}")
print("Advanced subtab mapping check passed")
PY
python -m pytest tests/ -x -q
```

## 23. P8-2B 验证结果

- git status -sb：干净
- git diff --check：无 whitespace error
- DOM marker check：passed
- JS function check：passed
- Advanced subtab mapping check：passed
- **pytest：375 passed, 6 skipped**

## 24. P8-2B 未做事项

- ❌ 未改后端 API
- ❌ 未改 Provider
- ❌ 未改 Resource Guard
- ❌ 未改数据库
- ❌ 未改音色试听逻辑（handleGenerateAudition 行为不变）
- ❌ 未改绑定逻辑（bindVoiceToProfile / handleCreateBinding 行为不变）
- ❌ 未改删除音色逻辑（handleDeleteVoice / handleVoiceDeleteFromList 行为不变）
- ❌ 未改声音克隆 / 声音设计
- ❌ 未执行真实 MiniMax smoke test
- ❌ 未进入 P8-2C

## 25. P8-2B 阶段结论

P8-2B 已完成音色 tab 信息架构整理。下一阶段建议进入 P8-2C：试听工作台产品化。

## 26. P8-2B 下一阶段建议

P8-2C 聚焦：
- 试听工作台布局产品化
- 当前选中音色展示
- 试听结果卡片化
- 试听记录体验优化
- 成本提示强化
- 不改后端 API

---

# P8-2C 试听工作台产品化

## 27. P8-2C 执行背景

P8-2C 于 commit `2483245` 完成试听工作台 UI 产品化。

P8-2C 提交只修改了 `app/static/index.html`，包含以下变更：

1. 新增 `auditionSelectedBanner` 高亮 banner（渐变背景，仅选中音色后显示）
2. 新增 `auditionCostHint` 字符数提示（实时显示"约 N 字"）
3. 重构 `auditionResult` 结果卡片（成功 / 失败 / 无音频三种状态）
4. 将 `auditionRecords` 从表格改为卡片布局
5. 适配星级 hover 事件委托（从 `.star-cell` 改为 `.star[data-index]`）

## 28. P8-2C 功能变更记录

### 28.1 当前选中音色 Banner

新增 `auditionSelectedBanner`：渐变背景横幅，仅选中音色后显示，展示 voice_id、voiceName，并集成 profile 选择下拉框。未选中时隐藏。

### 28.2 字符数提示

新增 `auditionCostHint`：随用户输入实时更新，显示"约 N 字"。

### 28.3 试听结果卡片

`auditionResult` 区域三种状态：
- **成功**：绿色渐变卡片，含 ✓ 图标、音频播放器、voice_id / model / duration 元数据
- **失败**：红色卡片，含 ✕ 图标和错误信息
- **无音频**：黄色卡片，含 ! 图标

### 28.4 试听记录卡片化

`renderAuditionRecords` 将记录从 `<table>` 改为独立 `<div>` 卡片，每张卡片包含：voice_id badge、voiceName、160px 宽音频播放器、文本预览、星级评分、备注输入框、删除按钮。

### 28.5 星级 Hover 事件适配

`mouseleave` 处理从 `.star-cell[data-index]` 改为 `.star[data-index]` 直接查询，解决卡片化后 DOM 结构变化。

## 29. P8-2C 仅 UI 展示声明

P8-2C 所有变更均为前端 UI 展示调整，未修改：

- 任何 API endpoint
- `handleGenerateAudition` 请求逻辑
- `guardedJsonFetch` 调用语义
- `highRisk` 语义
- `window._auditionRecords` 数据结构
- 任何后端代码

## 30. P8-2C DOM id 保留说明

静态检查确认以下 DOM id 在 P8-2C 实施后仍然存在：

- `voiceAuditionPanel`
- `auditionSelectedBanner`（新增）
- `auditionSelected`
- `auditionSelectedHint`（新增）
- `auditionCostHint`（新增）
- `auditionText`
- `auditionModel`
- `auditionProfileSelectWrap`
- `auditionProfileSelect`
- `auditionGenBtn`
- `auditionResult`
- `auditionRecordsPanel`
- `auditionCount`
- `auditionClearBtn`
- `auditionRecordsTable`
- `voiceListResults`

## 31. P8-2C JS function 行为保留说明

静态检查确认以下函数在 P8-2C 实施后仍然存在且行为未变：

- `renderAuditionWorkstation` — 仅 HTML 模板调整
- `updateAuditionSelected` — 适配新 banner 结构
- `setupAuditionWorkstation` — 事件委托逻辑保留，新增字符数初始化
- `renderAuditionRecords` — 卡片化改造，事件委托 data 属性保留
- `handleGenerateAudition` — API 请求语义完全不变，仅结果 HTML 调整
- `handleListVoices` — 未变更
- `filterVoiceList` — 未变更
- `quickBindVoice` — 未变更
- `bindVoiceToProfile` — 未变更

## 32. P8-2C 未做事项

- ❌ 未改后端 API
- ❌ 未改 Provider
- ❌ 未改 Resource Guard
- ❌ 未改 Cost Guard
- ❌ 未改数据库
- ❌ 未改音色列表查询逻辑
- ❌ 未改音色试听 API 调用语义
- ❌ 未改绑定逻辑
- ❌ 未改删除音色逻辑
- ❌ 未改声音克隆 / 声音设计
- ❌ 未执行真实 MiniMax smoke test

## 33. P8-2C 阶段结论

P8-2C 已完成试听工作台 UI 产品化。下一阶段建议进入 P8-2C1：收口修复。

---

# P8-2C1 试听工作台收口修复

## 34. P8-2C1 执行背景

P8-2C 提交 `2483245` 遗留两个收口问题：

1. **文档缺失**：P8-2C 提交只修改了 `app/static/index.html`，未同步更新 `docs/P8_2_VOICE_SELECTION_WORKSTATION.md`。
2. **渲染稳定性风险**：`renderAuditionRecords` 初始实现采用局部更新 / append 模式，存在以下风险：
   - 从 0 条变为 1 条时，"暂无试听记录"占位可能被 append 残留
   - 删除中间记录后，`card id` 与数组 index 变化导致卡片内容与 record 错位
   - 已有卡片只更新 audio / stars / note，未完整更新 voice_id / voiceName / textPreview
   - 前端显示可能和 `window._auditionRecords` 状态不一致

## 35. P8-2C1 问题与风险分析

| 问题 | 风险 |
|------|------|
| P8-2C 文档未同步更新 | 后续无法追溯 P8-2C 变更内容 |
| `records.forEach` + `existingCard` 局部更新 | 删除第 N 条后，index N+1 的卡 id 仍为 N+1，但 DOM 中仍是旧内容 |
| `container.appendChild(card)` | 0→1 条记录时"暂无"占位未被 innerHTML 覆盖，可能残留 |
| 局部更新不完整 | voice_id / voiceName / textPreview 在已有卡片上不会更新 |

## 36. P8-2C1 方案判断

**采用 `renderAuditionRecords` 全量重绘方案**：

- 每次读取 `window._auditionRecords`
- `records.length === 0` → `container.innerHTML = 空状态占位`，return
- `records.length > 0` → `records.map` 生成所有 card HTML，`container.innerHTML = cardsHtml.join('')`
- 不再使用 `getElementById(cardId)`、`existingCard` 局部更新、`appendChild`、`querySelectorAll('[id^="audition-card-"]')` 删除逻辑

**为什么**：
- 试听记录数量通常很小（个位数），全量重绘无性能问题
- 全量重绘更简单、稳定、可验证
- 避免占位残留
- 避免删除中间记录后 index 错位
- 保证 UI 永远完全反映 `window._auditionRecords` 当前状态

## 37. P8-2C1 修改范围

实际修改：
- `app/static/index.html` — `renderAuditionRecords` 改为全量重绘
- `docs/P8_2_VOICE_SELECTION_WORKSTATION.md` — 补齐 P8-2C 文档 + P8-2C1 文档
- `docs/PROJECT_HEALTH_CHECK.md` — 补充 P8-2C / P8-2C1 状态

## 38. P8-2C1 renderAuditionRecords 修复说明

修复前（P8-2C 初始版本）：

```javascript
records.forEach((r, i) => {
  const existingCard = document.getElementById(`audition-card-${i}`);
  if (existingCard) {
    // 局部更新 — 不完整，voice_id/voiceName/textPreview 不更新
    existingCard.querySelector('.arc-audio').innerHTML = audioHtml;
    ...
  } else {
    container.appendChild(card); // 可能残留"暂无"占位
  }
});
container.querySelectorAll('[id^="audition-card-"]').forEach(...) // 额外清理逻辑
```

修复后（P8-2C1）：

```javascript
if (records.length === 0) {
  container.innerHTML = '暂无试听记录占位';
  return;
}
const cardsHtml = records.map((r, i) => { ... }).join('');
container.innerHTML = cardsHtml; // 全量重绘，无残留，无错位
```

## 39. P8-2C1 DOM id 保留说明

静态检查确认以下 DOM id 在 P8-2C1 修复后仍然存在：

- `voiceAuditionPanel`
- `auditionSelectedBanner`
- `auditionSelected`
- `auditionSelectedHint`
- `auditionCostHint`
- `auditionText`
- `auditionModel`
- `auditionProfileSelectWrap`
- `auditionProfileSelect`
- `auditionGenBtn`
- `auditionResult`
- `auditionRecordsPanel`
- `auditionCount`
- `auditionClearBtn`
- `auditionRecordsTable`
- `voiceListResults`

## 40. P8-2C1 JS function 行为保留说明

静态检查确认以下函数在 P8-2C1 修复后仍然存在：

- `renderAuditionWorkstation` — 未变更
- `updateAuditionSelected` — 未变更
- `setupAuditionWorkstation` — 未变更
- `renderAuditionRecords` — **已改为全量重绘**，但保留了所有 data 属性（`data-index`、`data-star`、`data-delete`、`data-field="note"`），事件委托语义不变
- `handleGenerateAudition` — **未变更**，仅 UI 展示调整
- `renderVoiceTable` — 未变更
- `handleListVoices` — 未变更
- `filterVoiceList` — 未变更
- `quickBindVoice` — 未变更
- `bindVoiceToProfile` — 未变更

**本阶段仅修复试听记录渲染稳定性，未改变音色试听 API 调用语义。**

## 41. P8-2C1 API endpoint 不变说明

静态检查确认以下 API marker 在 P8-2C1 修复后仍然存在：

- `/api/voice/provider-voices/preview` — 未变更
- `guardedJsonFetch` — 未变更
- `highRisk: true` — 未变更
- `confirm_cost: false` — 未变更

## 42. P8-2C1 执行命令记录

```bash
# 基线检查
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -10

# 静态审查
grep -n "function renderAuditionRecords" -A90 app/static/index.html
grep -n "auditionRecords\|data-delete\|data-field=\"note\"\|data-star\|mouseleave\|mouseover" app/static/index.html
grep -n "function handleGenerateAudition" -A120 app/static/index.html
grep -n "P8-2C\|试听工作台产品化" docs/P8_2_VOICE_SELECTION_WORKSTATION.md
grep -n "P8-2C\|试听工作台产品化" docs/PROJECT_HEALTH_CHECK.md

# 代码修复
# 修改 app/static/index.html 中的 renderAuditionRecords 为全量重绘

# 验证命令
python -m pytest tests/ -x -q
python - <<'PY' ... (DOM marker check)
python - <<'PY' ... (JS function check)
python - <<'PY' ... (renderAuditionRecords stability check)
python - <<'PY' ... (API marker check)
python - <<'PY' ... (doc marker check)
```

## 43. P8-2C1 验证命令记录

所有静态检查均已通过：

```
P8-2C1 DOM marker check passed
P8-2C1 JS function check passed
P8-2C1 renderAuditionRecords stability check passed
P8-2C1 API marker check passed
P8-2C1 documentation marker check passed
```

pytest: 375 passed, 6 skipped

## 44. P8-2C1 验证结果

所有测试通过。renderAuditionRecords 已改为全量重绘，无残留占位，无 index 错位风险。

## 45. P8-2C1 未做事项

- ❌ 未改后端 API
- ❌ 未改 Provider
- ❌ 未改 Resource Guard
- ❌ 未改 Cost Guard
- ❌ 未改数据库
- ❌ 未改音色列表查询逻辑
- ❌ 未改音色试听 API 调用语义
- ❌ 未改绑定逻辑
- ❌ 未改删除音色逻辑
- ❌ 未改声音克隆 / 声音设计
- ❌ 未执行真实 MiniMax smoke test
- ❌ 未进入 P8-2D

## 46. P8-2C1 阶段结论

P8-2C1 已完成试听工作台收口修复。P8-2C 可视为已完成并收口。

## 47. P8-2C1 风险清零说明

| 风险 | 状态 |
|------|------|
| P8-2C 文档缺失 | ✅ 已补齐 P8-2C 文档（P8_2_VOICE_SELECTION_WORKSTATION.md sections 27-33） |
| renderAuditionRecords 局部更新错位风险 | ✅ 已改为全量重绘 |
| "暂无试听记录"占位残留 | ✅ records.length === 0 时立即 innerHTML 设置空状态，无残留 |
| 卡片内容与 record 状态不一致 | ✅ 每次全量重绘，UI 完全反映 window._auditionRecords |
| pytest 不捕获前端 DOM 状态问题 | ⚠️ 静态检查已覆盖，pytest 无法验证前端动态 DOM，但人工 review 通过 |

## 48. P8-2C1 下一阶段建议

建议 P8-2D 聚焦：
- 快速绑定入口体验优化
- 当前音色与人设关系展示
- 绑定成功 / 失败反馈优化
- 与高级绑定管理的边界说明
- 不改后端 API

---

# P8-2D 轻量绑定入口整理

## 49. P8-2D 执行背景

P8-2A 已完成音色区现状审查。P8-2B 已完成音色 tab 信息架构整理（删除音色移入高级危险操作区）。P8-2C / P8-2C1 已完成试听工作台产品化和收口（选中音色 banner、结果卡片、记录全量重绘）。

当前快速绑定入口仍偏工程化：
- 绑定按钮文案仅为"绑定"，不够清晰
- quickBindPanel 缺乏标题和说明
- 绑定成功 / 失败反馈较简单
- 绑定说明区文案不够清晰

本阶段目标是整理轻量绑定入口体验，不改绑定 API。

## 50. P8-2D 本阶段目标

- 快速绑定入口按钮文案更清楚
- 快速绑定面板更像确认卡片（有标题和说明）
- 绑定成功 / 失败反馈更产品化
- 音色列表绑定状态展示更清楚（badge + count）
- 明确轻量绑定和高级绑定管理边界
- 保留所有 DOM id
- 保留所有 JS function 行为
- 不改 API endpoint

## 51. P8-2D 问题与风险分析

| 问题 | 风险 |
|------|------|
| quickBindVoice 使用动态 HTML 字符串，调整时容易破坏 id | 低：只改展示文本和样式，未改 id 占位符 |
| quickBindPanel 动态渲染在 voiceListResults 内 | 低：未改变 append 位置 |
| bindVoiceToProfile 涉及真实绑定创建 | 低：未改请求语义，只改 UI 反馈 |
| 绑定成功后需要刷新绑定状态 | 低：refreshVoiceBindStatus 核心逻辑未改 |
| 完整绑定管理在高级区，轻量绑定不应替代 | 低：只优化入口，不移动功能 |

## 52. P8-2D 方案判断

**采用 UI 层产品化方案**：
- 只调整 `quickBindVoice` 的展示结构和文案
- 只调整 `renderVoiceTable` 中绑定状态 badge 展示
- 只调整 `quickBindMsg` 的反馈样式（绿色成功卡、红色失败卡）
- 只调整绑定说明区的静态文案
- 不改 `bindVoiceToProfile` API 调用语义
- 不改 `handleCreateBinding` / `handleDeleteBinding`
- 不改后端

## 53. P8-2D 修改范围

实际修改：
- `app/static/index.html` — quickBindVoice 面板标题/说明/反馈样式、绑定按钮文案、绑定状态 badge
- `docs/P8_2_VOICE_SELECTION_WORKSTATION.md` — 补齐 P8-2D 文档
- `docs/PROJECT_HEALTH_CHECK.md` — 更新 P8-2D 状态

## 54. P8-2D 轻量绑定入口整理说明

### 54.1 绑定按钮文案

renderVoiceTable 中绑定按钮文案从"绑定"改为"绑定到人设"，更清楚表达操作目标。

### 54.2 quickBindVoice 面板

| 元素 | 调整前 | 调整后 |
|------|--------|--------|
| 面板样式 | `padding:12px;background:#f7fafc;border-radius:8px` | `background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px` |
| 标题 | 无 | "绑定到声音人设"（粗体，0.88rem） |
| 说明 | "将 <code>voiceId</code> 绑定到：" | "将当前音色 <code>voiceId</code> 绑定到一个声音人设。绑定后可在创作工作台中选择该人设进行生成。" |
| 反馈区域 | 纯文本 | 绿色成功卡 / 红色失败卡，带边框和圆角 |

### 54.3 绑定成功 / 失败反馈

- **处理中**：灰色文本"绑定中…"，按钮禁用
- **成功**：绿色背景卡片 `background:#f0fff4;border:1px solid #c6f6d5;border-radius:6px`，内容："✓ 绑定成功。现在可以回到创作工作台，选择该声音人设进行生成。"
- **失败**：红色背景卡片 `background:#fff5f5;border:1px solid #feb2b2;border-radius:6px`，内容："✕ 绑定失败：{错误信息}"
- **未选择人设**：红色文本提示"请先选择一个声音人设"

### 54.4 绑定状态 Badge

renderVoiceTable 中绑定状态从纯文本改为 badge + 文本：
- **已绑定**：`背景#c6f6d5，绿色文字` 的 badge + profile 名称（最多显示2个，多余显示 "+N"）
- **未绑定**：`背景#fef3c7，橙色文字` 的 badge

## 55. P8-2D 绑定关系展示调整说明

| 状态 | 调整前 | 调整后 |
|------|--------|--------|
| 已绑定 | `已绑定: profile1, profile2`（纯绿文字） | 绿色 badge + profile 名称，最多2个，多余显示 "+N" |
| 未绑定 | `未绑定`（橙色纯文字） | 橙色 badge "未绑定" |

## 56. P8-2D 绑定反馈展示调整说明

| 状态 | 样式 | 内容 |
|------|------|------|
| 处理中 | 灰色文字 | "绑定中…" |
| 成功 | 绿色卡片 | "✓ 绑定成功。现在可以回到创作工作台，选择该声音人设进行生成。" |
| 失败 | 红色卡片 | "✕ 绑定失败：{错误信息}" |
| 未选择 | 红色文字 | "请先选择一个声音人设" |

## 57. P8-2D 与高级绑定管理边界说明

- tab-voices 中的快速绑定是**轻量入口**：快速将当前音色关联到声音人设
- **高级 / 绑定管理**仍是完整管理入口：查看所有绑定、删除绑定、复杂参数配置
- 删除绑定、查看完整绑定仍在高级区
- P8-2D 不替代完整绑定管理
- 绑定说明文案已更新为："轻量绑定用于快速把当前音色关联到声音人设。需要查看、删除或批量维护绑定时，请进入「高级 / 绑定管理」。"

## 58. P8-2D DOM id 保留说明

静态检查确认以下 DOM id 在 P8-2D 修改后仍然存在：

- `quickBindPanel` — 未改
- `quickBindProfileSel` — 未改
- `quickBindModelSel` — 未改
- `quickBindConfirm` — 未改
- `quickBindCancel` — 未改
- `quickBindMsg` — 未改
- `voiceListResults` — 未改
- `voiceProvider` — 未改
- `voiceType` — 未改
- `voiceSearch` — 未改
- `bindingProfileSelect` — 未改
- `bindingListResults` — 未改
- `newBindingProfile` — 未改
- `newBindingProvider` — 未改
- `newBindingModel` — 未改
- `newBindingVoiceId` — 未改
- `createBindingResult` — 未改
- `绑定到声音人设` — **新增**（quickBindVoice 面板标题文本）
- `高级 / 绑定管理` — **新增**（绑定说明区文案）

## 59. P8-2D JS function 行为保留说明

| 函数 | 变更 |
|------|------|
| `quickBindVoice` | **UI 层调整**：面板标题、说明文案、反馈样式、禁用状态，未改 API 调用语义 |
| `bindVoiceToProfile` | **未变更** |
| `refreshVoiceBindStatus` | **未变更** |
| `loadAllBindings` | **未变更** |
| `renderVoiceTable` | **UI 层调整**：绑定按钮文案、绑定状态 badge，未改数据语义 |
| `handleListVoices` | **未变更** |
| `filterVoiceList` | **未变更** |
| `handleListBindings` | **未变更** |
| `handleCreateBinding` | **未变更** |
| `handleDeleteBinding` | **未变更** |
| `handleCreateProfile` | **未变更** |

**本阶段仅调整轻量绑定入口展示，不改变绑定 API 调用语义。**

## 60. P8-2D API endpoint 不变说明

静态检查确认以下 API marker 在 P8-2D 修改后仍然存在：

- `/api/voice/profiles` — 未变更
- `/api/voice/profiles/{profileId}/bindings` — 未变更（bindVoiceToProfile 使用）
- `/bindings` — 未变更
- `/api/voice/bindings` — 未变更
- `apiJson` — 未变更
- `guardedJsonFetch` — 未变更

## 61. P8-2D 执行命令记录

```bash
# 基线检查
git fetch origin && git checkout dev && git pull --ff-only origin dev
git status -sb && git log --oneline -10

# 只读审查
grep -n "quickBindPanel|quickBindProfileSel|quickBindModelSel|quickBindConfirm|quickBindCancel|quickBindMsg|quickBindVoice|bindVoiceToProfile" app/static/index.html
grep -n "refreshVoiceBindStatus|loadAllBindings|_voiceBindMap|binding|绑定" app/static/index.html
grep -n "/bindings\|apiJson(.*bindings\|fetch(.*bindings" app/static/index.html
grep -n "function renderVoiceTable" -A180 app/static/index.html
grep -n "subtab-bindings|handleListBindings|handleCreateBinding|handleDeleteBinding|bindingListResults|createBindingResult" app/static/index.html

# 代码修改
# app/static/index.html:
# - renderVoiceTable: "绑定" → "绑定到人设"
# - quickBindVoice: 面板标题 + 说明 + 绿色成功卡/红色失败卡反馈
# - renderVoiceTable: 绑定状态 badge 展示
# - 绑定说明区: 更新边界说明文案

# 验证
python -m pytest tests/ -x -q  # 375 passed, 6 skipped
```

## 62. P8-2D 验证命令记录

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["quickBindPanel","quickBindProfileSel","quickBindModelSel","quickBindConfirm","quickBindCancel","quickBindMsg","voiceListResults","绑定到声音人设","高级 / 绑定管理"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM check passed")
PY
```

## 63. P8-2D 验证结果

- pytest：375 passed, 6 skipped
- DOM marker check：passed
- JS function check：passed
- API marker check：passed
- quickBind structure check：passed

## 64. P8-2D 未做事项

- ❌ 未改后端 API
- ❌ 未改 Provider
- ❌ 未改 Resource Guard
- ❌ 未改 Cost Guard
- ❌ 未改数据库
- ❌ 未改音色列表查询逻辑
- ❌ 未改音色试听 API 调用语义
- ❌ 未改绑定 API 调用语义
- ❌ 未改删除绑定 API 调用语义
- ❌ 未改删除音色逻辑
- ❌ 未改声音克隆 / 声音设计
- ❌ 未执行真实 MiniMax smoke test
- ❌ 未进入 P8-2E

## 65. P8-2D 阶段结论

P8-2D 已完成轻量绑定入口整理。下一阶段建议进入 P8-2E：P8-2 验收与健康检查收口。

## 66. P8-2D 风险清零说明

| 风险 | 状态 |
|------|------|
| 快速绑定入口文案不清晰 | ✅ 改为"绑定到人设" |
| quickBindVoice 面板缺乏标题说明 | ✅ 添加"绑定到声音人设"标题和说明文字 |
| 绑定成功/失败反馈简单 | ✅ 改为绿色/红色卡片样式 |
| 绑定状态展示不清晰 | ✅ 添加 badge + count + profile 名称 |
| 轻量绑定与高级绑定管理边界不清 | ✅ 更新绑定说明区文案 |
| pytest 不捕获前端 UI 变化 | ⚠️ 静态检查已覆盖，UI 层验证依赖人工 review |

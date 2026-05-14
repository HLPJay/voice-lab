# P8-FIX1 前端回归缺陷排查与修复下发指令

## 0. 安全输出要求

本任务禁止输出任何真实鉴权信息、密钥、令牌、会话信息、请求头、隐私数据或生产配置原文。

如扫描到相关内容，只记录文件路径、字段名、风险类型和修复建议，具体值统一写为 `<REDACTED>`。

不要复述完整日志、完整 `.env`、完整请求头或完整生产配置。

如平台拦截输出，请改为更短的脱敏摘要。

---

## 1. 当前项目

项目名称：Voice Lab

仓库地址：

    https://github.com/HLPJay/voice-lab/tree/dev

基线分支：

    dev

当前阶段：

    P8-FIX1 前端回归缺陷排查与修复

前置阶段：

    P8-4F 历史记录和下载体验验收与健康检查收口已完成

当前已知问题：

1. 前端"长文本 / 剧本"导航入口存在，但模块内容没有显示。
2. 历史模块无法播放历史数据。
3. 历史模块无法识别新增历史，或新增任务不容易刷新出来。
4. 需要排查当前前端是否还有其他 DOM / JS / tab 断点。
5. 需要提出并执行一轮安全、小步、可验证的前端修复。

---

## 2. 当前问题初步判断

### 2.1 长文本 / 剧本模块缺失

当前导航中存在：

```html
<button class="tab-btn" data-tab="longtext">长文本</button>
<button class="tab-btn" data-tab="script">剧本</button>
```

但需要检查是否存在：

```html
<div class="tab-content" id="tab-longtext">...</div>
<div class="tab-content" id="tab-script">...</div>
```

如果导航存在而内容区不存在，则这是 P0 级前端结构缺陷。

要求：

- 不允许简单删除导航入口。
- 应恢复 `tab-longtext` 和 `tab-script` 内容区。
- 应尽量从 git 历史恢复原批量长文本 / 批量剧本 DOM 和 JS。
- 如果原实现已丢失，则基于当前后端已有 batch API 和 schema 做最小可用前端恢复。

---

### 2.2 历史播放 / 下载不可用

当前历史 card 已有播放区和下载区，但播放 / 下载依赖：

```text
audio_asset
audio_asset_id
asset_id
```

当前 `/api/voice/jobs` 返回的 `VoiceJobRead` 不包含音频资产字段。

因此：

```text
历史播放 / 下载不可用不是纯前端 bug。
```

本阶段前端只做：

- 保留安全降级提示。
- 不伪造播放入口。
- 不伪造下载入口。
- 在文档中记录后端遗留。

真正修复应进入：

```text
P8-BE1：历史任务返回音频资产字段
```

---

### 2.3 新增历史不易识别

P8-4E 引入 `_historyJobs` 前端缓存以支持本地搜索 / 筛选。

这会带来体验问题：

```text
页面已打开时新生成任务后，历史列表不会自动知道有新任务。
```

本阶段应增加轻量"刷新历史"入口。

目标：

- 增加 `historyRefreshBtn`
- 增加 `refreshHistory()` 函数
- 点击后重新拉取 `/api/voice/jobs?limit=10&offset=0`
- 清空 `_historyJobs`
- 重置 `_historyOffset`
- 保留或重置筛选条件需要在文档中明确
- 不改后端 API
- 不改 `/api/voice/jobs` 查询参数

---

## 3. 本阶段目标

P8-FIX1 目标：

1. 修复长文本 tab 内容缺失。
2. 修复剧本 tab 内容缺失。
3. 恢复或重建批量长文本前端入口。
4. 恢复或重建批量剧本前端入口。
5. 增加历史刷新入口。
6. 做一次全局 tab / DOM / JS 完整性检查。
7. 明确历史播放 / 下载的后端字段遗留。
8. 更新缺陷修复文档。
9. 更新 `docs/PROJECT_HEALTH_CHECK.md`。
10. 运行全量测试。
11. 提交修复。

---

## 4. 本阶段允许修改的文件

允许修改：

- app/static/index.html
- docs/P8_FIX1_FRONTEND_REGRESSION_REPAIR.md
- docs/PROJECT_HEALTH_CHECK.md

如需要增加静态检查脚本，允许新增：

- scripts/check_frontend_integrity.py

但如果新增脚本，必须：

- 不引入新依赖
- 不访问外部网络
- 只做静态检查
- 写入文档说明

---

## 5. 本阶段禁止修改的内容

禁止修改：

- Provider
- MiniMax Provider Adapter
- Resource Guard
- Cost Guard
- 数据库模型
- 数据库迁移
- 音频生成主逻辑
- WebSocket 流式逻辑
- 同步生成 API
- 异步生成 API
- 多版本生成 API
- 下载 API
- 声音克隆逻辑
- 声音设计逻辑
- 音色试听逻辑
- 绑定逻辑
- 登录 / 用户体系
- BYOK
- 队列 / worker
- React / Vue / 构建工具

本阶段不要修复历史播放 / 下载的后端字段问题。该问题记录为：

```text
P8-BE1：历史任务返回音频资产字段
```

---

## 6. 严格限制

必须遵守：

1. 必须基于 dev 分支。
2. 不允许基于 main 分支。
3. 不切 React / Vue。
4. 不引入构建工具。
5. 不拆分 `index.html`。
6. 不改 MiniMax 调用。
7. 不执行真实 MiniMax smoke test。
8. 不改 `/api/voice/jobs` 返回结构。
9. 不改 `/api/voice/assets/{assetId}/download`。
10. 不新增服务端搜索 / 筛选。
11. 不新增历史删除。
12. 不新增历史详情页。
13. 不伪造历史播放入口。
14. 不伪造历史下载入口。
15. 如果 git status 不干净，停止并报告。
16. 如果测试失败，停止并报告。
17. 所有问题、方案、命令、验证结果必须写入文档。
18. 完成后不要继续 P8-5 / P8-BE1 / P8-UX1。
19. P8-5 / P8-BE1 / P8-UX1 需要单独下发新指令。

---

## 7. 准备与基线检查

执行：

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -30
```

要求：

- 当前分支必须是 dev。
- 工作区必须干净。
- 最近提交中应能看到 P8-4F 收口提交。
- 如果不满足，停止并报告。

---

## 8. 修改前只读审查

### 8.1 Tab 完整性检查

执行：

```bash
python - <<'PY'
from pathlib import Path
import re

html = Path("app/static/index.html").read_text(encoding="utf-8")

tabs = re.findall(r'data-tab="([^"]+)"', html)
ids = set(re.findall(r'id="([^"]+)"', html))

missing = []
for tab in tabs:
    expected = f"tab-{tab}"
    if expected not in ids:
        missing.append((tab, expected))

print("tabs:", tabs)
print("missing tab content:", missing)

if missing:
    raise SystemExit(f"Missing tab content containers: {missing}")
PY
```

预期当前可能失败，尤其是：

```text
longtext -> tab-longtext
script -> tab-script
```

如果失败，记录到 `docs/P8_FIX1_FRONTEND_REGRESSION_REPAIR.md`。

---

### 8.2 长文本 / 剧本功能扫描

执行：

```bash
grep -n "tab-longtext\|tab-script\|longtext\|script\|批量\|长文本\|剧本\|batch" app/static/index.html
```

执行：

```bash
grep -R "LongtextBatchRequest\|ScriptBatchRequest\|BatchSubmitResponse\|BatchStatusResponse\|/batch\|batch/" app tests -n
```

目标：

- 找出当前后端 batch endpoint。
- 找出当前前端是否仍有 batch JS。
- 判断是 DOM 缺失、JS 缺失，还是 API 调用缺失。

要求：

- 不要猜 endpoint。
- 必须以当前代码 grep 结果为准。
- 文档中记录实际 endpoint。

---

### 8.3 从 git 历史查找原批量前端实现

执行：

```bash
git log --oneline -- app/static/index.html
```

然后逐个检查近期 P8-1 / P7 相关提交中的原实现：

```bash
git show <commit>:app/static/index.html | grep -n "批量\|长文本\|剧本\|batch\|longtext\|script" -C 5
```

要求：

- 优先从历史版本恢复原有 DOM id 和 JS 函数。
- 不要重新发明一套与后端不一致的前端。
- 如果找到原批量生成区域，应拆分为：
  - `tab-longtext`
  - `tab-script`
- 如果原批量生成区域是一个合并 tab，也要按当前 P8 信息架构拆成两个 tab。

---

### 8.4 历史播放 / 下载字段检查

执行：

```bash
grep -n "class VoiceJobRead" -A30 app/domain/schemas.py
grep -n "def list_jobs\|@router.get(\"/jobs" -A80 app/api/voice_jobs.py
grep -n "getHistoryAudioAssetId\|historyAudioPlaybackHtml\|historyDownloadEntryHtml" -A80 app/static/index.html
```

记录：

- `VoiceJobRead` 当前字段。
- `/api/voice/jobs` 当前返回字段。
- 前端 `getHistoryAudioAssetId(job)` 当前判断逻辑。
- 为什么历史播放 / 下载当前只能降级提示。

不得在本阶段修改后端。

---

### 8.5 新增历史识别问题检查

执行：

```bash
grep -n "let _historyJobs\|let _historySearch\|let _historyStatusFilter\|function loadHistory\|function loadMoreHistory\|function renderHistoryList" app/static/index.html
```

记录：

- `_historyJobs` 缓存逻辑。
- `loadHistory(0)` 是否重置缓存。
- `loadMoreHistory()` 是否 append。
- 当前是否有刷新历史按钮。
- 当前是否有 `refreshHistory()` 函数。

如果没有刷新入口，记录为 P1 问题。

---

### 8.6 全局 DOM / JS 断点检查

执行：

```bash
python - <<'PY'
from pathlib import Path
import re

html = Path("app/static/index.html").read_text(encoding="utf-8")

defined_functions = set(re.findall(r'function\s+([A-Za-z_$][\w$]*)\s*\(', html))
defined_ids = set(re.findall(r'id="([^"]+)"', html))

event_handlers = []
for attr in ["onclick", "oninput", "onchange", "onkeyup", "onblur"]:
    for value in re.findall(attr + r'="([^"]+)"', html):
        m = re.match(r'\s*([A-Za-z_$][\w$]*)\s*\(', value)
        if m:
            event_handlers.append((attr, m.group(1), value))

missing_functions = [
    (attr, fn, value)
    for attr, fn, value in event_handlers
    if fn not in defined_functions
]

id_refs = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', html))
missing_ids = sorted(x for x in id_refs if x not in defined_ids)

print("defined functions:", len(defined_functions))
print("inline handlers:", len(event_handlers))
print("missing handler functions:", missing_functions)
print("getElementById refs:", len(id_refs))
print("missing DOM ids:", missing_ids)

if missing_functions or missing_ids:
    raise SystemExit("Frontend integrity check failed")
PY
```

如果失败，记录缺失项。

注意：

- 如果某些 ID 是动态生成的，必须在文档中说明。
- 不要盲目删除引用。
- 优先恢复 DOM 或函数。

---

## 9. 修复任务 A：恢复 tab-longtext

### 9.1 要求

必须新增：

```html
<div class="tab-content" id="tab-longtext">
  ...
</div>
```

放置位置建议：

```text
tab-workspace 之后
tab-script 之前
```

或者：

```text
workspace -> longtext -> script -> voices -> history -> advanced
```

必须与导航顺序一致。

### 9.2 内容要求

长文本 tab 至少包含：

- 模块标题：`长文本生成`
- 说明文案
- 长文本输入 textarea
- profile 选择
- provider 选择
- 音频格式
- 返回格式
- 分段策略
- 最大分段字符数
- 段落间静音
- 是否生成字幕
- 提交按钮
- 批量任务状态 / 结果区域

### 9.3 DOM id 要求

优先恢复历史版本已有 DOM id。

如果历史版本没有明确 id，可使用以下命名：

```text
longtextInput
longtextProfileSelect
longtextProviderSelect
longtextAudioFormat
longtextOutputFormat
longtextSegmentStrategy
longtextMaxSegmentChars
longtextSilenceMs
longtextNeedSubtitle
longtextSubmitBtn
longtextResultsArea
```

如果原来已有不同 id，必须优先用原 id，避免破坏旧 JS。

### 9.4 JS 要求

必须存在长文本提交函数，例如：

```text
handleLongtextBatchSubmit()
```

或者恢复历史版本真实函数名。

该函数必须：

- 读取长文本 tab DOM
- 调用当前后端 batch submit endpoint
- 使用当前后端真实 endpoint
- 不调用不存在的 endpoint
- 不执行真实 MiniMax smoke test
- 显示提交结果
- 记录 batch_id
- 如已有 batch status 逻辑，则恢复轮询；如没有，则先显示"任务已提交，可在后续阶段完善轮询"

---

## 10. 修复任务 B：恢复 tab-script

### 10.1 要求

必须新增：

```html
<div class="tab-content" id="tab-script">
  ...
</div>
```

放置位置建议：

```text
tab-longtext 之后
tab-voices 之前
```

必须与导航顺序一致。

### 10.2 内容要求

剧本 tab 至少包含：

- 模块标题：`多角色剧本`
- 说明文案
- 剧本输入 textarea
- 剧本格式说明
- provider 选择
- 音频格式
- 返回格式
- 角色 profile 绑定说明
- 段落间静音
- 是否生成字幕
- 提交按钮
- 批量任务状态 / 结果区域

### 10.3 剧本输入格式建议

第一版可以采用 JSON Lines 或简单文本格式，但必须与当前后端 `ScriptBatchRequest` 对齐。

后端 schema 是：

```text
script: list[ScriptLine]
ScriptLine: role, text, profile_id, params
```

如果前端用文本格式，必须解析成该结构。

推荐输入格式：

```text
旁白|deep_night_programmer|这里是旁白文本
角色A|deep_night_programmer|你好，这是角色A
角色B|deep_night_programmer|你好，这是角色B
```

解析规则：

```text
role|profile_id|text
```

要求：

- 空行忽略。
- 每行必须至少三段。
- text 不能为空。
- 解析失败时显示友好错误。
- 不调用 API。

### 10.4 DOM id 要求

优先恢复历史版本已有 DOM id。

如果历史版本没有明确 id，可使用：

```text
scriptInput
scriptProviderSelect
scriptAudioFormat
scriptOutputFormat
scriptSilenceMs
scriptNeedSubtitle
scriptSubmitBtn
scriptResultsArea
```

### 10.5 JS 要求

必须存在剧本提交函数，例如：

```text
handleScriptBatchSubmit()
```

或者恢复历史版本真实函数名。

该函数必须：

- 读取剧本 tab DOM
- 解析剧本输入
- 组装 `ScriptBatchRequest`
- 调用当前后端 batch submit endpoint
- 使用当前后端真实 endpoint
- 不调用不存在的 endpoint
- 显示提交结果
- 记录 batch_id
- 如已有 batch status 逻辑，则恢复轮询；如没有，则先显示"任务已提交，可在后续阶段完善轮询"

---

## 11. 修复任务 C：历史刷新入口

### 11.1 新增 DOM

在历史工具栏中新增按钮：

```html
<button id="historyRefreshBtn" class="btn-sm" onclick="refreshHistory()">刷新历史</button>
```

放置建议：

```text
historySearch
historyStatusFilter
historyClearFilters
historyRefreshBtn
historyFilterHint
```

### 11.2 新增函数

新增：

```js
async function refreshHistory() {
  _historyJobs = [];
  _historyOffset = 0;
  _historyTotal = 0;
  _historyLoading = false;
  document.getElementById("historyList").innerHTML = "";
  updateHistoryFilterHint();
  await loadHistory(0);
}
```

是否清空筛选：

建议第一版 **保留当前筛选条件**。

原因：

```text
用户可能正在筛选某类状态，刷新后仍希望保留筛选。
```

但必须在文档中记录。

### 11.3 保留语义

不得改变：

- `loadHistory(offset)` 请求语义
- `_historyJobs` 本地缓存语义
- `_historyOffset`
- `_historyTotal`
- `_historyLoading`
- 本地搜索 / 筛选逻辑

---

## 12. 修复任务 D：轻量 UI 可用性问题

本阶段只做非常低风险 UI 修复。

### 12.1 隐藏桌面 tab 横向滚动条

当前截图中导航右侧出现明显滚动控件。

允许增加 CSS：

```css
.tab-nav {
  scrollbar-width: none;
}
.tab-nav::-webkit-scrollbar {
  display: none;
}
```

要求：

- 不改变 tab 切换逻辑。
- 不影响移动端横向滚动。
- 只隐藏滚动条视觉。

### 12.2 主流程卡片可点击

将主流程卡片变成轻量入口：

- 单段旁白：切换到 workspace 并聚焦 `textInput`
- 长文本生成：切换到 longtext
- 多角色剧本：切换到 script

允许新增：

```js
function switchTab(tabName) { ... }
function focusWorkspaceText() { ... }
```

如果当前已有 tab 切换逻辑，优先复用，不重复实现。

要求：

- 不破坏现有 tab 按钮点击。
- 不改变业务 API。
- 不做复杂动画。

### 12.3 配置区 bindingStatus 位置

如果当前 `bindingStatus` 作为 grid item 导致布局错位，可改为 full-width 提示区。

要求：

- 保留 `id="bindingStatus"`。
- 不改绑定状态刷新逻辑。
- 只改 CSS / HTML 位置。

---

## 13. 必须新增文档

新增：

```text
docs/P8_FIX1_FRONTEND_REGRESSION_REPAIR.md
```

文档必须包含：

# P8-FIX1 前端回归缺陷排查与修复

## 1. 背景

记录：

- P8-4 已收口。
- 用户反馈前端存在长文本 / 剧本不显示、历史无法播放、历史无法识别新增任务等问题。
- 本阶段目标是修复前端回归缺陷，不继续新功能。

## 2. 问题清单

必须记录表格：

| 问题 | 类型 | 优先级 | 根因 | 是否本阶段修复 |
|---|---|---|---|---|

必须包含：

- 长文本 tab 内容缺失
- 剧本 tab 内容缺失
- 历史播放无法使用
- 历史下载无法使用
- 新增历史不易识别
- tab 导航滚动条视觉问题
- 前端 DOM / JS 完整性风险

## 3. Tab 完整性审查

记录：

- 所有 data-tab
- 对应 tab-content
- 修复前缺失项
- 修复后结果

## 4. 长文本模块修复说明

记录：

- 是否从 git 历史恢复
- 使用哪些 DOM id
- 使用哪些 JS 函数
- 使用哪个后端 endpoint
- 是否改后端 API：否

## 5. 剧本模块修复说明

记录：

- 是否从 git 历史恢复
- 使用哪些 DOM id
- 使用哪些 JS 函数
- 使用哪个后端 endpoint
- 剧本输入格式
- 是否改后端 API：否

## 6. 历史播放 / 下载问题说明

必须记录：

- 当前 `/api/voice/jobs` 不返回音频资产字段。
- 当前 `VoiceJobRead` 不包含 `audio_asset_id` / `audio_asset`。
- 前端无法凭空播放历史音频。
- 本阶段不改后端。
- 遗留到 `P8-BE1：历史任务返回音频资产字段`。

## 7. 历史刷新入口修复说明

记录：

- 新增 `historyRefreshBtn`
- 新增 `refreshHistory()`
- 刷新时重置哪些状态
- 是否保留筛选条件
- 是否改 API：否

## 8. 轻量 UI 修复说明

记录：

- tab-nav 滚动条隐藏
- 主流程卡片可点击
- bindingStatus 布局优化
- 是否影响业务逻辑：否

## 9. DOM / JS 完整性检查

记录：

- 所有 inline handler 是否有对应 function
- 所有 getElementById 是否有对应 DOM id
- 是否存在动态 id 特例
- 检查结果

## 10. API endpoint 不变说明

记录：

- 未改同步生成 API
- 未改异步生成 API
- 未改流式 API
- 未改 batch API
- 未改 `/api/voice/jobs`
- 未改下载 API

## 11. 未处理事项

必须记录：

- 未改后端历史资产字段
- 未解决历史播放 / 下载真正可用问题
- 未做 P8-BE1
- 未做 P8-UX1
- 未做 P8-5
- 未拆分 index.html
- 未引入 React / Vue

## 12. 验证命令

记录所有实际执行命令。

## 13. 验证结果

记录测试结果。

## 14. 阶段结论

必须写：

    P8-FIX1 已完成前端回归缺陷修复。长文本 / 剧本 tab 内容已恢复，历史刷新入口已补充，前端 DOM / JS 完整性已通过静态检查。历史播放 / 下载真正可用仍依赖 P8-BE1：历史任务返回音频资产字段。

## 15. 下一阶段建议

建议：

1. P8-BE1：历史任务返回音频资产字段
2. P8-UX1：桌面宽屏布局与响应式适配
3. P8-5：localStorage 最近任务恢复

---

## 14. 更新 PROJECT_HEALTH_CHECK.md

更新：

```text
docs/PROJECT_HEALTH_CHECK.md
```

加入：

- P8-FIX1：前端回归缺陷排查与修复已完成 / 执行中
- 长文本 / 剧本 tab 内容缺失已修复
- 历史刷新入口已补充
- 历史播放 / 下载仍依赖 P8-BE1
- P8-BE1：历史任务返回音频资产字段
- P8-UX1：桌面宽屏布局与响应式适配
- P8-5：localStorage 最近任务恢复

---

## 15. 静态验证命令

### 15.1 git 检查

```bash
git status -sb
git diff --stat
git diff --check
```

---

### 15.2 Tab 完整性检查

```bash
python - <<'PY'
from pathlib import Path
import re

html = Path("app/static/index.html").read_text(encoding="utf-8")
tabs = re.findall(r'data-tab="([^"]+)"', html)
ids = set(re.findall(r'id="([^"]+)"', html))

missing = []
for tab in tabs:
    expected = f"tab-{tab}"
    if expected not in ids:
        missing.append((tab, expected))

if missing:
    raise SystemExit(f"Missing tab content containers: {missing}")

required_tabs = [
    "tab-workspace",
    "tab-longtext",
    "tab-script",
    "tab-voices",
    "tab-history",
    "tab-advanced",
]

missing_required = [x for x in required_tabs if x not in ids]
if missing_required:
    raise SystemExit(f"Missing required tabs: {missing_required}")

print("P8-FIX1 tab integrity check passed")
PY
```

---

### 15.3 DOM marker 检查

```bash
python - <<'PY'
from pathlib import Path

html = Path("app/static/index.html").read_text(encoding="utf-8")

required = [
    "tab-workspace",
    "tab-longtext",
    "tab-script",
    "tab-voices",
    "tab-history",
    "tab-advanced",
    "historyRefreshBtn",
    "historySearch",
    "historyStatusFilter",
    "historyList",
    "loadMoreHistory",
]

missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing required DOM markers: {missing}")

print("P8-FIX1 DOM marker check passed")
PY
```

---

### 15.4 JS function 检查

```bash
python - <<'PY'
from pathlib import Path
import re

html = Path("app/static/index.html").read_text(encoding="utf-8")

required_functions = [
    "handleGenerate",
    "toggleHistory",
    "loadHistory",
    "loadMoreHistory",
    "refreshHistory",
    "renderHistoryList",
    "filterHistoryJobs",
    "historyJobCardHtml",
    "historyAudioPlaybackHtml",
    "historyDownloadEntryHtml",
    "apiJson",
    "guardedJsonFetch",
]

missing = []
for fn in required_functions:
    if f"function {fn}" not in html and f"async function {fn}" not in html:
        missing.append(fn)

if missing:
    raise SystemExit(f"Missing required functions: {missing}")

print("P8-FIX1 JS function check passed")
PY
```

---

### 15.5 Inline handler / DOM id 完整性检查

```bash
python - <<'PY'
from pathlib import Path
import re

html = Path("app/static/index.html").read_text(encoding="utf-8")

defined_functions = set(re.findall(r'function\s+([A-Za-z_$][\w$]*)\s*\(', html))
defined_functions.update(re.findall(r'async\s+function\s+([A-Za-z_$][\w$]*)\s*\(', html))
defined_ids = set(re.findall(r'id="([^"]+)"', html))

event_handlers = []
for attr in ["onclick", "oninput", "onchange", "onkeyup", "onblur"]:
    for value in re.findall(attr + r'="([^"]+)"', html):
        m = re.match(r'\s*([A-Za-z_$][\w$]*)\s*\(', value)
        if m:
            event_handlers.append((attr, m.group(1), value))

missing_functions = [
    (attr, fn, value)
    for attr, fn, value in event_handlers
    if fn not in defined_functions
]

id_refs = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', html))
missing_ids = sorted(x for x in id_refs if x not in defined_ids)

if missing_functions:
    raise SystemExit(f"Missing inline handler functions: {missing_functions}")
if missing_ids:
    raise SystemExit(f"Missing getElementById DOM ids: {missing_ids}")

print("P8-FIX1 inline handler / DOM id integrity check passed")
PY
```

---

### 15.6 Batch API marker 检查

必须先通过 grep 确认实际 endpoint，然后把实际 marker 填入检查脚本。

示例：

```bash
grep -R "LongtextBatchRequest\|ScriptBatchRequest\|BatchSubmitResponse\|BatchStatusResponse\|/batch\|batch/" app tests -n
```

然后执行：

```bash
python - <<'PY'
from pathlib import Path

html = Path("app/static/index.html").read_text(encoding="utf-8")

required = [
    "tab-longtext",
    "tab-script",
    "longtext",
    "script",
]

missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing batch frontend markers: {missing}")

print("P8-FIX1 batch frontend marker check passed")
PY
```

如果本项目实际 endpoint 是 `/api/voice/batch/submit`，则额外检查：

```bash
python - <<'PY'
from pathlib import Path

html = Path("app/static/index.html").read_text(encoding="utf-8")

required = [
    "/api/voice/batch/submit",
    "/api/voice/batch/",
]

missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing batch API markers: {missing}")

print("P8-FIX1 batch API marker check passed")
PY
```

如果实际 endpoint 不同，以当前代码为准，不要强行写不存在的 endpoint。

---

### 15.7 历史刷新语义检查

```bash
python - <<'PY'
from pathlib import Path

html = Path("app/static/index.html").read_text(encoding="utf-8")

required = [
    "historyRefreshBtn",
    "function refreshHistory",
    "_historyJobs = []",
    "_historyOffset = 0",
    "loadHistory(0)",
]

missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing history refresh markers: {missing}")

print("P8-FIX1 history refresh check passed")
PY
```

---

### 15.8 历史播放 / 下载遗留检查

```bash
python - <<'PY'
from pathlib import Path

schemas = Path("app/domain/schemas.py").read_text(encoding="utf-8")
html = Path("app/static/index.html").read_text(encoding="utf-8")

required_html = [
    "getHistoryAudioAssetId",
    "当前历史记录未返回可播放音频资产",
    "当前历史记录未返回可下载音频资产",
]

missing_html = [x for x in required_html if x not in html]
if missing_html:
    raise SystemExit(f"Missing history fallback markers: {missing_html}")

if "class VoiceJobRead" not in schemas:
    raise SystemExit("VoiceJobRead schema not found")

print("P8-FIX1 history playback/download limitation check passed")
PY
```

---

### 15.9 文档标记检查

```bash
python - <<'PY'
from pathlib import Path

doc = Path("docs/P8_FIX1_FRONTEND_REGRESSION_REPAIR.md").read_text(encoding="utf-8")
health = Path("docs/PROJECT_HEALTH_CHECK.md").read_text(encoding="utf-8")

required_doc = [
    "P8-FIX1 前端回归缺陷排查与修复",
    "问题清单",
    "Tab 完整性审查",
    "长文本模块修复说明",
    "剧本模块修复说明",
    "历史播放 / 下载问题说明",
    "历史刷新入口修复说明",
    "DOM / JS 完整性检查",
    "API endpoint 不变说明",
    "阶段结论",
]

required_health = [
    "P8-FIX1",
    "前端回归缺陷排查与修复",
    "P8-BE1",
    "历史任务返回音频资产字段",
    "P8-UX1",
    "P8-5",
]

missing_doc = [x for x in required_doc if x not in doc]
missing_health = [x for x in required_health if x not in health]

if missing_doc:
    raise SystemExit(f"Missing FIX1 doc markers: {missing_doc}")
if missing_health:
    raise SystemExit(f"Missing health check markers: {missing_health}")

print("P8-FIX1 documentation marker check passed")
PY
```

---

## 16. 全量测试

执行：

```bash
python -m pytest tests/ -x -q
```

要求：

- 测试必须通过。
- 如果测试失败，停止并报告。
- 不允许带失败提交。

---

## 17. 不执行真实 MiniMax smoke test

本阶段不执行真实 MiniMax smoke test。

原因：

- 本阶段是前端回归缺陷修复。
- 不涉及 MiniMax Provider 改造。
- 不需要消耗真实 MiniMax 额度。

必须写入文档。

---

## 18. 提交

如果所有验证通过：

```bash
git add app/static/index.html docs/P8_FIX1_FRONTEND_REGRESSION_REPAIR.md docs/PROJECT_HEALTH_CHECK.md
```

如果新增了静态检查脚本：

```bash
git add scripts/check_frontend_integrity.py
```

提交：

```bash
git commit -m "p8-fix1 repair frontend regression issues"
git push origin dev
```

提交后：

```bash
git status -sb
git log --oneline -20
```

---

## 19. 最终输出报告要求

完成后输出报告，必须包含：

1. 当前分支
2. 新增提交 hash
3. 修改文件清单
4. 本次修复的问题清单
5. 长文本 tab 修复说明
6. 剧本 tab 修复说明
7. 历史刷新入口修复说明
8. 历史播放 / 下载不可用原因说明
9. DOM / JS 完整性检查结果
10. API endpoint 不变说明
11. 执行过的验证命令
12. 测试结果
13. 是否执行真实 MiniMax smoke test
14. 本阶段未做事项
15. 当前遗留项
16. 下一阶段建议

最终结论必须写：

    P8-FIX1 已完成。长文本 / 剧本 tab 内容已恢复，历史刷新入口已补充，前端 DOM / JS 完整性已通过静态检查。历史播放 / 下载真正可用仍依赖 P8-BE1：历史任务返回音频资产字段。

本次完成后不要继续执行 P8-BE1、P8-UX1 或 P8-5。

P8-BE1 / P8-UX1 / P8-5 需要单独下发新指令。

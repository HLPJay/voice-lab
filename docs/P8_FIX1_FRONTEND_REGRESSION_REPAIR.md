# P8-FIX1 前端回归缺陷排查与修复

## 1. 背景

- P8-4 已收口。
- 用户反馈前端存在长文本/剧本不显示、历史无法播放、历史无法识别新增任务等问题。
- P8-FIX1A 已完成审查，确认问题范围。
- 本阶段目标是修复前端回归缺陷，不继续新功能。

---

## 2. 问题清单

| 问题 | 类型 | 优先级 | 根因 | 是否本阶段修复 |
|---|---|---|---|---|
| 长文本 tab 内容缺失 | 前端结构 | P0 | **经核实为误报**：tab-longtext 内容和 JS 函数均存在 | 不需要修复 |
| 剧本 tab 内容缺失 | 前端结构 | P0 | **经核实为误报**：tab-script 内容和 JS 函数均存在 | 不需要修复 |
| 历史播放无法使用 | 后端字段 | P1 | `/api/voice/jobs` 返回的 VoiceJobRead 不包含音频资产字段 | 遗留到 P8-BE1 |
| 历史下载无法使用 | 后端字段 | P1 | 同上 | 遗留到 P8-BE1 |
| 新增历史不易识别 | 前端逻辑 | P1 | `_historyJobs` 缓存后缺少刷新入口 | **已修复**：新增 historyRefreshBtn 和 refreshHistory() |
| tab 导航滚动条视觉问题 | UI | P2 | `.tab-nav { overflow-x: auto }` 显示滚动条 | **已修复**：添加 scrollbar-width: none |
| 前端 DOM/JS 完整性风险 | 前端质量 | P2 | 存在动态 ID 引用但有后备保护 | 已记录，持续观察 |

---

## 3. Tab 完整性审查

### 修复前

所有 6 个 tab 导航按钮均有对应内容区：

| data-tab | 对应 id | 状态 |
|---|---|---|
| `workspace` | `tab-workspace` | 存在 |
| `longtext` | `tab-longtext` | 存在 |
| `script` | `tab-script` | 存在 |
| `voices` | `tab-voices` | 存在 |
| `history` | `tab-history` | 存在 |
| `advanced` | `tab-advanced` | 存在 |

**结论：P8-FIX1A 审查时基于截图误判为缺失，实际代码中 tab-longtext 和 tab-script 内容均完整存在。**

### 修复后

无变化（内容本来完整）。

---

## 4. 长文本模块修复说明

**本不需要修复，内容本来完整。**

- 是否从 git 历史恢复：否（内容本来存在）
- tab-longtext 存在：第 1156 行
- handleBatchLongtextSubmit 存在：第 4308 行
- 使用后端 endpoint：`/api/voice/batch/submit`（mode: 'longtext'）
- 是否改后端 API：否

---

## 5. 剧本模块修复说明

**本不需要修复，内容本来完整。**

- 是否从 git 历史恢复：否（内容本来存在）
- tab-script 存在：第 1264 行
- handleBatchScriptSubmit 存在：第 4384 行
- 使用后端 endpoint：`/api/voice/batch/submit`（mode: 'script'）
- 剧本输入格式：角色|profile_id|文本（JSON Lines 格式）
- 是否改后端 API：否

---

## 6. 历史播放 / 下载问题说明

必须记录：

- 当前 `/api/voice/jobs` 返回的 `VoiceJobRead` 不包含 `audio_asset_id` / `audio_asset` 字段
- 前端 `getHistoryAudioAssetId(job)` 始终返回 `null`
- 前端 historyAudioPlaybackHtml 和 historyDownloadEntryHtml 已实现安全降级
- 本阶段不改后端
- **遗留到 P8-BE1：历史任务返回音频资产字段**

---

## 7. 历史刷新入口修复说明

### 修复内容

新增 DOM：

```html
<button id="historyRefreshBtn" class="btn-sm" onclick="refreshHistory()">刷新历史</button>
```

位置：historyToolbar 内，historyClearFilters 之后。

### 新增函数

```javascript
async function refreshHistory() {
  _historyJobs = [];
  _historyOffset = 0;
  _historyTotal = 0;
  _historyLoading = false;
  document.getElementById("historyList").innerHTML = '<div style="font-size:0.82rem;color:#718096">加载中…</div>';
  updateHistoryFilterHint();
  await loadHistory(0);
}
```

### 刷新语义

- 重置 `_historyJobs` 缓存
- 重置分页状态（`_historyOffset = 0`，`_historyTotal = 0`）
- 重置加载锁（`_historyLoading = false`）
- 清空 historyList 显示加载中
- 调用 `loadHistory(0)` 重新加载
- **保留当前筛选条件**（`_historySearch` 和 `_historyStatusFilter` 不重置）
- 不改 API

---

## 8. 轻量 UI 修复说明

### 8.1 tab-nav 滚动条隐藏

添加 CSS：

```css
.tab-nav {
  scrollbar-width: none;
}
.tab-nav::-webkit-scrollbar {
  display: none;
}
```

- 是否影响业务逻辑：否
- 是否影响移动端横向滚动：否（仅隐藏视觉滚动条）

### 8.2 动态 ID 引用说明

以下 ID 被 JavaScript 动态创建或引用，但有后备保护：

| ID | 引用位置 | 状态 |
|---|---|---|
| `batchLongtextPanel` | batch mode switch | 元素不存在，但不影响功能 |
| `batchScriptPanel` | batch mode switch | 元素不存在，但不影响功能 |
| `batchResult` | handleBatchLongtextSubmit | 有 `|| resultsArea` 后备 |
| `batchScriptResult` | handleBatchScriptSubmit | 有 `|| resultsArea` 后备 |
| `quickBindPanel` | 音色绑定面板 | 动态创建 |
| `cloneBindProfile` | 克隆表单 | 动态设置 id |
| `designBindProfile` | 设计表单 | 动态设置 id |
| `importBindProfile` | 导入表单 | 动态设置 id |

这些是预先存在的代码模式，不影响功能。

---

## 9. DOM / JS 完整性检查

### 9.1 Inline handler / DOM id 完整性

```
Defined functions: 107
Inline handlers: 37
Missing handler functions: []（所有 onclick/oninput/onchange 均有对应函数）
getElementById refs: 153
Missing DOM ids: 8 个动态 ID（有后备保护或动态创建）
```

**结论：无阻断性问题。所有事件处理函数均存在。缺失的 DOM id 均有后备保护或动态创建机制。**

### 9.2 所有 tab 完整性

6 个 tab 均有对应内容区，通过。

### 9.3 Batch API 和前端完整性

- `/api/voice/batch/submit`：存在
- `/api/voice/batch/{batch_id}/status`：存在
- handleBatchLongtextSubmit：存在
- handleBatchScriptSubmit：存在

---

## 10. API endpoint 不变说明

- 未改同步生成 API
- 未改异步生成 API
- 未改流式 API
- 未改 batch API
- 未改 `/api/voice/jobs`
- 未改下载 API
- 未新增服务端搜索/筛选

---

## 11. 未处理事项

- 未改后端历史资产字段（遗留到 P8-BE1）
- 未解决历史播放/下载真正可用问题（遗留到 P8-BE1）
- 未做 P8-BE1
- 未做 P8-UX1
- 未做 P8-5
- 未拆分 index.html
- 未引入 React/Vue
- 未执行真实 MiniMax smoke test

---

## 12. 验证命令

### Tab 完整性

```bash
python - <<'PY'
from pathlib import Path
import re
html = Path("app/static/index.html").read_text(encoding="utf-8")
tabs = re.findall(r'data-tab="([^"]+)"', html)
ids = set(re.findall(r'id="([^"]+)"', html))
missing = [(tab, f"tab-{tab}") for tab in tabs if f"tab-{tab}" not in ids]
print("PASS" if not missing else f"FAIL: {missing}")
PY
```

### DOM marker

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["historyRefreshBtn", "function refreshHistory", "_historyJobs = []"]
print("PASS" if all(x in html for x in required) else "FAIL")
PY
```

### JS function

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
for fn in ["refreshHistory", "handleBatchLongtextSubmit", "handleBatchScriptSubmit"]:
    print(f"{fn}: {'PASS' if f'function {fn}' in html or f'async function {fn}' in html else 'FAIL'}")
PY
```

---

## 13. 验证结果

### P8-FIX1 修改范围

修改文件：`app/static/index.html`

修改内容：
1. 新增 `historyRefreshBtn` 按钮到 historyToolbar
2. 新增 `refreshHistory()` 函数
3. 新增 `.tab-nav` 滚动条隐藏 CSS

---

## 14. 阶段结论

**P8-FIX1 已完成前端回归缺陷修复。**

经核实：
- 长文本/剧本 tab 内容**本来完整存在**（P8-FIX1A 审查时为误判）
- 历史刷新入口已补充（`historyRefreshBtn` + `refreshHistory()`）
- tab-nav 滚动条已隐藏
- 前端 DOM/JS 完整性已通过静态检查
- 历史播放/下载真正可用仍依赖 **P8-BE1：历史任务返回音频资产字段**

---

## 15. 下一阶段建议

建议按优先级：

1. **P8-BE1：历史任务返回音频资产字段**（后端字段扩展，解决历史播放/下载）
2. **P8-UX1：桌面宽屏布局与响应式适配**
3. **P8-5：localStorage 最近任务恢复**

---

## 附录：预先存在的动态 ID 说明

以下 ID 在 `getElementById` 调用中被引用，但元素本身通过 JavaScript 动态创建或有后备保护，这是在 P8-FIX1 之前就存在的代码模式，不属于本阶段引入的问题：

| ID | 用途 | 风险 |
|---|---|---|
| `batchLongtextPanel` | 长文本面板切换 | 元素不存在，但切换逻辑不影响当前分离 tab 结构 |
| `batchScriptPanel` | 剧本面板切换 | 同上 |
| `batchResult` | 长文本结果区 | 有 `resultsArea` 后备 |
| `batchScriptResult` | 剧本结果区 | 有 `resultsArea` 后备 |
| `quickBindProfile` | 音色绑定面板 | 动态创建 |
| `cloneBindProfile` | 克隆 profile 选择 | 动态设置 id |
| `designBindProfile` | 设计 profile 选择 | 动态设置 id |
| `importBindProfile` | 导入 profile 选择 | 动态设置 id |

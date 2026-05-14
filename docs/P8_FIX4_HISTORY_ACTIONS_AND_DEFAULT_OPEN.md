# P8-FIX4 历史页操作行与默认展开修复

## 1. 背景

用户反馈历史页存在以下体验问题：

- 历史 tab 内部默认折叠，用户需要再点击一次才能看到历史
- "复制"按钮语义不清，用户不知道复制的是什么
- 无音频资产时只显示"无资产"文字，没有操作按钮位
- 删除按钮没有真实后端支持但前端没有禁用

---

## 2. 问题分析

| 问题 | 原因 | 影响 | 本阶段处理 |
|---|---|---|---|
| 历史 tab 默认折叠 | `historyArea` 设置 `display:none` | 用户需要两次点击才能看到历史 | 已修复：移除 display:none，history tab 激活时自动展开 |
| 历史记录二次折叠 | `historyToggle` 标题有 `onclick="toggleHistory()"` | 用户点击标题反而收起历史 | 已修复：移除标题的 onclick，不再作为折叠主入口 |
| 标题显示折叠箭头 | `toggleHistory()` 设置 `历史记录 ▾` / `历史记录 ▴` | 用户看到箭头以为还有折叠层 | 已修复：标题文本改为"历史记录"，不显示箭头 |
| "复制"按钮语义不清 | 按钮只显示"复制" | 用户不知道复制的是 job_id | 已修复：改为"复制 ID"，增加 `title="复制 job_id"` |
| 无资产时缺少按钮位 | 只显示"无资产"文字 | 用户看不到播放/下载按钮位置 | 已修复：改为显示 disabled 播放/下载按钮 |
| 删除按钮无后端支持 | 后端没有 DELETE `/api/voice/jobs/{job_id}` | 前端点击后无响应或假删除 | 已修复：按钮设置为 disabled，提示后端暂未支持 |

---

## 3. 修复内容

### Fix A: 历史 tab 默认展开

1. 移除 `historyArea` 的 `style="display:none"`
2. 移除 `historyToggle` 的 `onclick="toggleHistory()"`
3. 移除 `historyToggle` 的 `style="cursor:pointer"`
4. 标题文本从"历史记录 ▾"改为"历史记录"
5. 在 tab 切换逻辑中新增 `tab === 'history'` 回调，激活时自动加载历史（如果列表为空）

```javascript
if (tab === 'history') {
  const area = document.getElementById('historyArea');
  if (area) area.style.display = 'block';
  if (_historyJobs.length === 0) {
    loadHistory(0);
  }
}
```

### Fix B: 复制按钮语义明确

按钮文案从"复制"改为"复制 ID"，并增加 `title="复制 job_id"`：

```html
<button onclick="copyJobId('${escJs(rawJobId)}', this)"
  title="复制 job_id"
  style="...">复制 ID</button>
```

### Fix C: 播放/下载按钮状态

当 `assetId` 存在时，显示可用按钮：

```html
<span>${audioPlayerHtml(assetId)}</span>
<span style="margin-left:6px">${downloadBtnHtml(assetId)}</span>
```

当 `assetId` 不存在时，显示 disabled 按钮：

```html
<button class="btn-sm" disabled title="当前历史记录未返回可播放音频资产">播放</button>
<button class="btn-sm" disabled title="当前历史记录未返回可下载音频资产">下载</button>
```

### Fix D: 删除按钮禁用

删除按钮已设置为 disabled，并调用 `showHistoryDeleteUnsupported()` 提示用户：

```html
<button onclick="showHistoryDeleteUnsupported()"
  style="...cursor:not-allowed" disabled>删除</button>
```

---

## 4. 复制 ID 功能说明

- 复制的是 `job_id`
- 用于排查问题、定位任务、反馈问题
- 不复制全文
- 不调用后端
- 使用 `navigator.clipboard.writeText` API

---

## 5. 播放/下载状态说明

- `getHistoryAudioAssetId(job)` 返回 assetId 时，播放/下载可用
- 没有 assetId 时，播放/下载置灰（disabled）
- 当前 `/api/voice/jobs` 仍未返回音频资产字段，所以多数历史任务会显示 disabled
- P8-BE1 完成后，这些按钮可自动启用

---

## 6. 删除能力说明

- 当前后端没有 DELETE `/api/voice/jobs/{job_id}`
- 本阶段不做真实删除
- 不做前端假删除（不从 `_historyJobs` 删除记录来假装删除）
- 真实删除进入 P8-BE2

---

## 7. API endpoint 不变说明

- `/api/voice/jobs` - 未改
- `/api/voice/assets/` - 未改
- 未新增 DELETE endpoint
- 未改其他 API

---

## 8. DOM/JS 保留说明

以下元素和函数保持不变：

- `historySearch` - 本地搜索输入框
- `historyStatusFilter` - 状态筛选下拉框
- `historyRefreshBtn` - 刷新历史按钮
- `historyClearFilters` - 清空筛选按钮
- `loadMoreHistory` - 加载更多函数
- `historyJobCardHtml` - 历史卡片渲染函数
- `getHistoryAudioAssetId` - 获取音频资产 ID 函数
- `copyJobId` - 复制 job_id 函数
- `loadHistory` - 加载历史函数
- `renderHistoryList` - 渲染历史列表函数
- `toggleHistory` - 折叠函数（保留但不再作为主入口）

---

## 9. 验证命令

### 9.1 历史默认展开检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ['id="historyArea"', 'id="historyToggle"', 'id="historyRefreshBtn"']
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
if 'id="historyArea" style="display:none"' in html:
    raise SystemExit("historyArea should not default to display:none")
if "历史记录 ▾" in html or "历史记录 ▴" in html:
    raise SystemExit("history title should not show collapse arrow")
if 'onclick="toggleHistory()"' in html:
    raise SystemExit("history title should not use toggleHistory as primary interaction")
print("PASS")
PY
```

### 9.2 历史操作按钮 marker 检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["getHistoryAudioAssetId(job)", "复制 ID", "复制 job_id",
    "当前历史记录未返回可播放音频资产", "当前历史记录未返回可下载音频资产",
    "后端暂未支持历史任务删除"]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
print("PASS")
PY
```

### 9.3 无资产时按钮禁用检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["disabled", "当前历史记录未返回可播放音频资产",
    "当前历史记录未返回可下载音频资产"]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
if "/api/voice/assets/undefined" in html:
    raise SystemExit("Must not generate undefined asset download URL")
print("PASS")
PY
```

### 9.4 历史 API 不变检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["/api/voice/jobs", "limit=10", "offset="]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit(f"Missing: {missing}")
print("PASS")
PY
```

---

## 10. 验证结果

### 10.1 静态检查

- history default open check: PASS
- history action marker check: PASS
- no fake delete check: PASS
- disabled playback/download check: PASS
- history API unchanged check: PASS

### 10.2 pytest

```
375 passed, 6 skipped
```

---

## 11. 未处理事项

- P8-BE1：历史任务返回音频资产字段
- P8-BE2：历史任务删除接口
- P8-UX1：桌面宽屏布局与响应式适配
- P8-5：localStorage 最近任务恢复
- 历史播放/下载真正可用（依赖 P8-BE1）
- 历史删除真正可用（依赖 P8-BE2）

---

## 12. 阶段结论

**P8-FIX4 已完成。** 历史 tab 已改为默认展开，历史操作行已明确区分播放、下载、复制 ID 和删除。播放/下载在无音频资产时置灰不可点，真实历史删除仍需后续 P8-BE2 后端接口支持。

---

## 13. 不执行真实 MiniMax smoke test

本阶段只修复前端历史页交互，不涉及 Provider，不消耗真实 MiniMax 额度，因此不执行真实 MiniMax smoke test。

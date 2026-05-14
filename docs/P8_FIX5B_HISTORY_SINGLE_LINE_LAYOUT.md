# P8-FIX5B 历史记录严格单行表格化修复

## 1. 背景

用户反馈当前历史记录仍然没有达到"一条任务一行"的目标。

当前表现：
```
第一行：任务类型 / 状态 / 时间 / 文本 / job_id
第二行：播放 / 下载 / 复制 ID / 删除按钮
```

操作按钮掉到了第二行。

## 2. 问题分析

| 问题 | 原因 | 影响 | 修复方案 |
|---|---|---|---|
| 操作按钮掉到第二行 | `.history-row` 使用 `flex-wrap: wrap` | 宽度不足时按钮自动换行 | 改为 grid 单行布局，移除 flex-wrap |
| 文本列可能撑开行 | `.history-text` 无 `min-width: 0` | grid 子项默认取 min-content | 添加 `min-width: 0` 允许收缩 |
| job_id 列可能撑开 | `.history-job-id` 有 `max-width: 120px` | 固定宽导致其他列被挤压 | 改为 `min-width: 0` 允许收缩 |
| 操作按钮可能换行 | `.history-actions` 缺少 `white-space: nowrap` | 按钮内部文本或间隙导致换行 | 添加 `white-space: nowrap` |
| 窄屏下历史不可用 | 无移动端降级 | 固定 grid 在窄屏下溢出 | 添加 `@media (max-width: 760px)` 降级 |

## 3. 修复内容

- `.history-row` 从 `display: flex` + `flex-wrap: wrap` 改为 `display: grid` + `grid-template-columns`
- `.history-actions` 添加 `white-space: nowrap` 和 `justify-content: flex-end`
- `.history-actions .btn-sm` 新增压缩样式（padding: 4px 8px, font-size: 0.76rem）
- `.history-text` 添加 `min-width: 0` 允许 grid 收缩
- `.history-job-id` 移除 `max-width: 120px`，改为 `min-width: 0`
- 新增 `@media (max-width: 760px)` 移动端降级（grid 改为 1 列）
- 播放器懒展开逻辑保持不变

## 4. 修改后历史行结构

```
类型 | 状态 | 时间 | 文本预览（省略） | job_id（省略） | 播放 / 下载 / 复制 ID / 删除
```

所有列固定在单行内，操作按钮组固定在最后一列。

## 5. 播放器展开说明

- 默认不显示播放器
- 点击"播放"后展开播放器到 `history-audio-row`
- 再点"播放"收起播放器
- 展开播放器时允许占用下一行（history-audio-row 从 `display:none` 变为 `display:block`）
- 默认历史列表仍保持一条任务一行

## 6. API endpoint 不变说明

- 未改后端 API
- 未改 `/api/voice/jobs`
- 未改 `/api/voice/assets`
- 未改删除接口
- 未改生成接口

## 7. 未处理事项

- 未做 P8-BE3（历史任务与资产物理清理）
- 未做 P8-UX1（桌面宽屏布局）
- 未做 P8-5（localStorage 最近任务恢复）

## 8. 验证命令

### 8.1 history-row grid 检查

```bash
python - <<'PY'
from pathlib import Path
import re
html = Path("app/static/index.html").read_text(encoding="utf-8")
match = re.search(r"\.history-row\s*\{([^}]*)\}", html, re.S)
block = match.group(1)
assert "display: grid" in block, ".history-row must use display:grid"
assert "flex-wrap" not in block, ".history-row must not use flex-wrap"
assert "grid-template-columns" in block, ".history-row must define grid-template-columns"
print("PASS")
PY
```

### 8.2 history-actions nowrap 检查

```bash
python - <<'PY'
from pathlib import Path
import re
html = Path("app/static/index.html").read_text(encoding="utf-8")
match = re.search(r"\.history-actions\s*\{([^}]*)\}", html, re.S)
block = match.group(1)
assert "display: inline-flex" in block
assert "white-space: nowrap" in block
print("PASS")
PY
```

### 8.3 省略号检查

```bash
python - <<'PY'
from pathlib import Path
import re
html = Path("app/static/index.html").read_text(encoding="utf-8")
for selector in [".history-text", ".history-job-id"]:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", html, re.S)
    block = match.group(1)
    for marker in ["overflow: hidden", "text-overflow: ellipsis", "white-space: nowrap"]:
        assert marker in block, f"{selector} missing {marker}"
print("PASS")
PY
```

### 8.4 historyJobCardHtml 结构检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function historyJobCardHtml")
end = html.find("function historyEmptyStateHtml", start)
block = html[start:end]
for marker in ["history-row", "history-type", "history-time", "history-text", "history-job-id", "history-actions", "history-audio-row"]:
    assert marker in block, f"missing {marker}"
assert "audioPlayerHtml(assetId)" not in block, "audioPlayerHtml must not be in historyJobCardHtml"
print("PASS")
PY
```

### 8.5 播放器懒展开检查

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
start = html.find("function toggleHistoryAudio")
end = html.find("function", start + 10)
block = html[start:end]
for marker in ["audioPlayerHtml(assetId)", "classList.contains('visible')", "classList.add('visible')", "classList.remove('visible')"]:
    assert marker in block, f"missing {marker}"
print("PASS")
PY
```

## 9. 验证结果

- history-row grid 检查: PASS
- history-actions nowrap 检查: PASS
- 省略号检查: PASS
- historyJobCardHtml 结构检查: PASS
- 播放器懒展开检查: PASS
- pytest: 384 passed, 6 skipped

## 10. 手工验证要求（浏览器）

1. 历史 tab 正常打开
2. 历史记录默认一条任务一行
3. 播放 / 下载 / 复制 ID / 删除按钮在同一行
4. 按钮没有掉到第二行
5. 文本预览过长时显示省略号
6. job_id 过长时显示省略号
7. 点击播放后展开播放器
8. 再点击播放后收起播放器
9. 无资源时播放 / 下载 disabled
10. 有资源时播放 / 下载可用

## 11. 阶段结论

**P8-FIX5B 已完成。** 历史记录已从 flex 换行布局调整为 grid 单行布局，播放 / 下载 / 复制 ID / 删除操作位固定在同一行右侧。文本预览和 job_id 使用省略号，播放器仍保持点击后懒展开。未改后端 API。
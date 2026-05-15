# P15-STATS-B1-A0：轻量本地统计面板实现前置审查

## 1. 阶段背景

P15-STATS-A0 设计已完成，P15-STATS-A0-CHECK 通过。当前阶段为 P15-STATS-B1-A0，在正式实现 stats_store.js 和 stats.js 前，审查并锁定实现范围、文件边界、加载顺序和测试策略。

## 2. 当前代码事实

### 2.1 Tab 结构

现有 Tab（index.html lines 1302-1307）：

| data-tab | 名称 | content id |
|---|---|---|
| workspace | 创作工作台 | tab-workspace |
| longtext | 长文本 | tab-longtext |
| script | 剧本 | tab-script |
| voices | 音色 | tab-voices |
| history | 历史 | tab-history |
| advanced | 音色工具 | tab-advanced |

**尚无 `stats` Tab**。B1 实现时需新增 button 和 content container。

### 2.2 脚本加载顺序

当前关键加载顺序（index.html lines 2070-2072）：

```html
<script src="/static/js/sample_store.js"></script>
<script src="/static/js/context_store.js"></script>
<script src="/static/js/sample_sidebar.js"></script>
```

B1 建议加载顺序：

```html
<script src="/static/js/sample_store.js"></script>
<script src="/static/js/context_store.js"></script>
<script src="/static/js/stats_store.js"></script>  <!-- B1 新增 -->
<script src="/static/js/sample_sidebar.js"></script>
<script src="/static/js/stats.js"></script>        <!-- B1 新增 -->
```

**约束**：`stats_store.js` 必须在 `sample_store.js` 和 `context_store.js` 之后加载。

### 2.3 Tab 切换逻辑

Tab 切换逻辑（index.html lines 2090-2107）：

```javascript
document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    if (btn.classList.contains('active')) return;
    const content = document.getElementById('tab-' + tab);
    if (!content) {
      console.warn('Missing tab content: tab-' + tab);
      return;
    }
    // ...remove active from all...
    btn.classList.add('active');
    content.classList.add('active');
  });
});
```

**关键**：切换时检查 `document.getElementById('tab-' + tab)` 是否存在。若 content 不存在则 warn 并拒绝切换。B1 新增 button 时必须同步新增 content container。

## 3. B1 实现目标

B1 第一版目标：

- 新增 `stats_store.js`：纯计算模块，只读 SampleStore + ContextStore
- 新增 `stats.js`：统计 Tab 渲染和事件绑定
- index.html 新增统计 Tab button 和 content container
- 不改后端，不改 Store schema，不调用 MiniMax
- 不引入图表库，不做趋势图

## 4. 文件边界

| 文件 | 操作 |
|---|---|
| `app/static/js/stats_store.js` | 新增 |
| `app/static/js/stats.js` | 新增 |
| `app/static/index.html` | 修改（只加 button / container / CSS / script 标签） |
| `app/static/js/sample_store.js` | 不改 |
| `app/static/js/context_store.js` | 不改 |
| `app/static/js/sample_sidebar.js` | 不改 |
| `app/api/*` | 不改 |
| `app/services/*` | 不改 |

## 5. stats_store.js 职责

### 5.1 职责定义

```
纯计算模块，只读 SampleStore + ContextStore。
不写 localStorage，不调用 fetch，不依赖 DOM。
```

### 5.2 暴露 API

```javascript
window.StatsStore = {
  getSampleStats: getSampleStats,    // 计算 A 级指标
  getContextStats: getContextStats,  // 计算 B 级指标
  getAll: getAll,                    // 合并 A + B
  formatDuration: formatDuration,    // ms → "X小时Y分钟Z秒"
  groupCount: groupCount            // array → {value: count} 排序数组
};
```

### 5.3 边界要求

| 要求 | 说明 |
|---|---|
| 输入异常不抛错 | try/catch 包裹所有计算 |
| SampleStore 不存在 | 返回空统计对象 |
| ContextStore 不存在 | 返回空统计对象 |
| created_at 非法 | 跳过该条，不影响整体 |
| duration_ms 为 null | 跳过，不参与时长聚合 |
| provider/profile/source 为空 | 归入 unknown |

### 5.4 getSampleStats 返回结构

```javascript
{
  total: number,
  today: number,
  last7days: number,
  last30days: number,
  bySource: [{value, count}],       // 降序
  byProvider: [{value, count}],
  byProfileName: [{value, count}],  // null → unknown
  byAudioFormat: [{value, count}],
  totalDurationMs: number | null,
  avgDurationMs: number | null,
  withContextId: number,
  withAssetId: number,
  withDownloadUrl: number
}
```

### 5.5 getContextStats 返回结构

```javascript
{
  total: number,
  longtextCount: number,
  scriptCount: number,
  longtextTotalChars: number,
  longtextAvgChars: number,
  scriptTotalLines: number,
  scriptAvgLines: number,
  scriptUniqueRoles: number,
  subtitleEnabledRatio: number | null,
  byAudioFormat: [{value, count}],
  bySegmentStrategy: [{value, count}],
  coverage: number  // 有 context_id 的样本数 / 样本总数
}
```

## 6. stats.js 职责

### 6.1 职责定义

```
渲染统计 Tab 内容。
绑定刷新按钮。
调用 StatsStore.getAll() 并渲染。
监听 storage event 刷新统计。
```

### 6.2 暴露 API

```javascript
window.StatsPanel = {
  init: init,      // 绑定刷新按钮等
  render: render,  // 调用 StatsStore.getAll() 并渲染
  refresh: refresh // 重新 render
};
```

### 6.3 边界要求

| 要求 | 说明 |
|---|---|
| 不写 localStorage | 只读 |
| 不调用 fetch | 纯前端 |
| 不修改 SampleStore | 只读 |
| 不修改 ContextStore | 只读 |
| 不依赖 SampleSidebar | 独立模块 |

### 6.4 渲染内容

```
统计总览：样本总数 / 今日 / 近7天 / 近30天
生成类型分布：source 归并展示
Provider / Profile Top
音频资产：有 asset_id / download_url / 总时长 / 平均时长
上下文：context 总数 / longtext 数 / script 数 / 覆盖率
数据边界说明（固定文案）
刷新按钮
```

## 7. index.html 修改范围

### 7.1 允许修改项

仅限以下四项，不在此列的一律禁止：

1. **Tab button**：在 advanced 后面新增 `<button class="tab-btn" data-tab="stats">统计</button>`
2. **Content container**：在 tab-advanced 后面新增 `<div class="tab-content" id="tab-stats"></div>`
3. **CSS**：在 `.tab-content` 相关样式区域新增 stats 面板样式
4. **Script 标签**：在 sample_sidebar.js 之后新增 stats_store.js 和 stats.js 加载
5. **初始化调用**：在 `window.SampleSidebar.init();` 后新增 `window.StatsPanel && window.StatsPanel.init && window.StatsPanel.init();`

### 7.2 禁止修改项

```
禁止把统计计算逻辑写入 index.html
禁止修改既有 tab 按钮或 content
禁止修改 sample_store.js / context_store.js 引用位置
禁止修改生成链路
禁止修改 SampleSidebar 逻辑
```

## 8. 第一版展示范围

### 8.1 必须展示

- 统计总览（5 项）：样本总数 / 今日 / 近7天 / 近30天 / 上下文总数
- 生成类型分布（8 类）：单条 / 异步 / 流式 / 多版本 / 试听 / 长文本 / 剧本 / 其他
- Provider Top3
- Profile Top5
- 音频资产观察：有 asset_id（有占比）/ 有 download_url（有占比）/ 总时长 / 平均时长
- 上下文观察：context 总数 / longtext 数 / script 数 / 覆盖率

### 8.2 source 归并映射

| source | 显示类别 |
|---|---|
| workspace_sync | 单条 |
| workspace_async | 异步 |
| workspace_stream | 流式 |
| workspace_variant | 多版本 |
| audition | 试听 |
| batch_longtext_merged / batch_longtext_segment | 长文本 |
| batch_script_merged / batch_script_segment | 剧本 |
| 其他 | 其他 |

### 8.3 不展示

- 图表（折线图 / 饼图）
- 复杂筛选器
- 导出按钮
- 失败排行榜
- 成本估算

## 9. 数据边界提示

UI 必须展示以下固定文案（出现在统计 Tab 顶部或底部）：

```
统计基于当前浏览器 localStorage 中最近样本与上下文：
SampleStore 最多 200 条，ContextStore 最多 50 条。
删除浏览器数据或更换设备后统计会变化，不代表全量历史。
```

## 10. 测试策略

### 10.1 stats_store 测试

新增 `tests/test_stats_store_static.py`，覆盖：

```
stats_store.js 文件存在
IIFE + 'use strict'
window.StatsStore 存在
包含 getSampleStats / getContextStats / getAll / formatDuration / groupCount
不调用 fetch / guardedJsonFetch / MiniMax
不调用 localStorage.setItem
不调用 SampleStore.pushSample / ContextStore.pushContext
处理 null duration_ms 时不抛错
provider/source 为空时归入 unknown
created_at 非法时不抛错
```

### 10.2 stats_panel 测试

新增 `tests/test_stats_panel_static.py`，覆盖：

```
index.html 包含 data-tab="stats" button
index.html 包含 id="tab-stats" container
index.html 加载 stats_store.js script 标签
index.html 加载 stats.js script 标签
stats.js 文件存在
window.StatsPanel 存在
包含 init / render / refresh
render 调用 StatsStore.getAll
不调用 fetch / localStorage.setItem / MiniMax
渲染结果包含数据边界文案
```

### 10.3 回归测试

确认既有的 SampleSidebar / SampleStore / ContextStore / batch 链路不受影响。

## 11. 不进入范围

```
不做图表库（ECharts / Chart.js）
不做折线图 / 饼图 / 环形图
不做复杂筛选器
不做导出功能
不做后端统计 API
不做数据库表
不做全量资产扫描
不做成本估算
不做失败原因排行榜
不做 Provider 成功率
不做多用户 / SaaS 统计
不改 SampleStore schema
不改 ContextStore schema
不写 localStorage（StatsStore 只读）
不调用真实 MiniMax
```

## 12. 风险与观察项

| 风险 | 缓解 |
|---|---|
| duration_ms 大面积为 null 导致时长统计无意义 | UI 标注"仅统计带时长样本"，B1 可降级时长指标为"仅展示有值样本数" |
| source 枚举扩展导致归并后落入"其他" | 定期更新归并映射表，不做动态发现 |
| 切换 Tab 时 content 不存在导致 warn | B1 实现时必须同步加 button + container |
| storage event 触发后 StatsPanel 未刷新 | stats.js 必须监听 storage event 并调用 refresh |

## 13. 审查结论

| 问题 | 结论 |
|---|---|
| B1 是否可以进入实现 | 是 |
| B1 是否只做本地轻量统计 | 是，纯前端只读 |
| B1 是否需要后端 | 否 |
| B1 是否需要改 Store schema | 否 |
| B1 是否需要调用 MiniMax | 否 |
| B1 需要新增哪些文件 | stats_store.js + stats.js |
| B1 可以修改哪些现有文件 | index.html（仅加 button/container/CSS/script 标签） |
| B1 测试覆盖哪些方面 | stats_store contract / stats_panel contract / 回归 |
| B1 不进入哪些范围 | 图表 / 后端 / SaaS / 成本估算 |

**结论**：B1 实现范围明确且受控，可以进入 P15-STATS-B1 实现。

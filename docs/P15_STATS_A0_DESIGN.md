# P15-STATS-A0：后期统计能力设计

## 0. 当前决策更新（2026-05-16）

**由于管理面板（admin.html）已有服务端统计能力，且 P15-B1 本地统计不是当前必要功能，P15-STATS-B1 暂不实现，转入 Backlog。**

详细决策记录见 `docs/P15_STATS_BACKLOG.md`。

## 1. 阶段背景

P14 完成了"最近样本 → 详情 → 恢复"创作闭环，SampleSidebar 已作为常驻入口就位。

在继续下一个功能方向前，需要先设计后期统计模块，明确应该统计什么、从哪里取数、如何展示。

当前阶段是纯设计，不实现功能代码。

## 2. 统计模块定位

**P15 统计模块不是替代创作工作台主线。**

当前产品主线：

```
文本 / 长文本 / 剧本
  ↓
生成音频
  ↓
保存样本
  ↓
查看详情
  ↓
恢复继续编辑
```

P15 统计模块定位为：

- **创作行为统计**：生成量、来源分布、Provider/Profile 使用频率
- **本地资产观察**：asset_id / download_url 覆盖率、总时长
- **可恢复上下文统计**：longtext / script context 数量和内容规模

用途：回答"我生成了多少？哪些模式用得最多？context 积累了多少？"

## 3. 当前可用数据源

### 3.1 SampleStore

| 属性 | 值 |
|---|---|
| localStorage key | `voice_lab_recent_samples_v1` |
| 最大保留数量 | 200 条 |
| 是否依赖后端 | 否 |
| 是否保存 audio blob | 否 |
| 是否保存敏感数据 | 否 |

**核心字段**（可用于统计）：

| 字段 | 类型 | 用途 |
|---|---|---|
| `sample_id` | string | 计数 |
| `created_at` | ISO8601 | 时间范围过滤 |
| `source` | string | 来源分布 |
| `provider` | string | Provider 分布 |
| `profile_id` / `profile_name` | string | Profile 分布 |
| `audio_format` | string | 格式分布 |
| `duration_ms` | number | 时长统计 |
| `status` | string | 完成率 |
| `context_id` | string | context 覆盖率 |
| `asset_id` | string | 资产覆盖率 |
| `download_url` | string | URL 可用率 |
| `job_id` / `batch_id` / `segment_id` | string | 批次追踪 |

**source 枚举参考**：

- `workspace_sync`
- `workspace_async`
- `workspace_stream`
- `workspace_variant`
- `audition`
- `batch_longtext_merged`
- `batch_script_merged`
- `batch_longtext_segment`
- `batch_script_segment`
- `unknown`

### 3.2 ContextStore

| 属性 | 值 |
|---|---|
| localStorage key | `voice_lab_sample_context_v1` |
| 最大保留数量 | 50 条 |
| 是否依赖后端 | 否 |
| 是否保存 audio blob | 否 |
| 是否依赖 SampleStore | 否 |

**longtext context 字段**：

- `context_id` / `batch_id`
- `created_at`
- `full_text`（字数统计）
- `provider`
- `profile_id`
- `segment_strategy`
- `max_segment_chars`
- `silence_between_ms`
- `audio_format`
- `need_subtitle`
- `params`（speed/vol/pitch/emotion）

**script context 字段**：

- `context_id` / `batch_id`
- `created_at`
- `lines`（行数统计，角色数估算）
- `provider`
- `silence_between_ms`
- `audio_format`
- `need_subtitle`

### 3.3 现有前端页面结构

**当前 Tab 列表**：

| data-tab | 名称 |
|---|---|
| workspace | 创作工作台 |
| longtext | 长文本 |
| script | 剧本 |
| voices | 音色 |
| history | 历史 |
| advanced | 音色工具 |

**无统计 Tab**。

**结论**：统计模块推荐作为独立 Tab（推荐 Tab 名称：`统计`，内部阶段名：`stats`），不放入 SampleSidebar。SampleSidebar 继续作为最近样本和恢复入口。

### 3.4 后端 / API 观察

现有 API 文件（只读审查，不修改）：

| 文件 | 潜在统计用途 |
|---|---|
| `voice_assets.py` | 未来全量资产统计 |
| `voice_jobs.py` | 未来任务级统计 |
| `voice_cost.py` | 未来成本估算 |
| `runtime_status.py` | Provider 可用性监控 |
| `admin.py` | 未来管理后台统计 |

**当前判断**：这些 API 本阶段只记录存在，不依赖。P15-B1 纯前端 localStorage 统计，不需要调用任何后端接口。

## 4. 指标分级

### 4.1 A 级：P15-B1 可直接实现

基于 SampleStore 直接计算，无需新接口：

| # | 指标 | 计算方式 |
|---|---|---|
| 1 | 最近样本总数 | `SampleStore.getSamples().length` |
| 2 | 今日生成样本数 | filter `created_at` date === today |
| 3 | 最近 7 天生成数 | filter `created_at` within 7 days |
| 4 | 最近 30 天生成数 | filter `created_at` within 30 days |
| 5 | 按 source 分布 | groupBy `source` |
| 6 | 按 provider 分布 | groupBy `provider` |
| 7 | 按 profile_name 分布 | groupBy `profile_name` |
| 8 | 按 audio_format 分布 | groupBy `audio_format` |
| 9 | 总 duration_ms | sum `duration_ms`（过滤 null） |
| 10 | 平均 duration_ms | 总时长 / 有时长样本数 |
| 11 | 有 context_id 的样本数 | filter `context_id !== null` |
| 12 | 有 asset_id 的样本数 | filter `asset_id !== null` |
| 13 | 有 download_url 的样本数 | filter `download_url !== null` |

### 4.2 B 级：可基于 ContextStore 辅助实现

基于 ContextStore 计算，与 SampleStore 交叉分析：

| # | 指标 | 计算方式 |
|---|---|---|
| 1 | context 总数 | `ContextStore.getContexts().length` |
| 2 | longtext context 数量 | filter `type === 'longtext'` |
| 3 | script context 数量 | filter `type === 'script'` |
| 4 | longtext 总字数 | sum `full_text.length`（longtext only） |
| 5 | longtext 平均字数 | 总字数 / longtext 数量 |
| 6 | script 总行数 | sum `lines.length`（script only） |
| 7 | script 平均行数 | 总行数 / script 数量 |
| 8 | script 角色数估算 | unique roles across all script contexts |
| 9 | subtitle 开启比例 | longtext 中 `need_subtitle === true` 比例 |
| 10 | audio_format 分布 | groupBy `audio_format`（contexts） |
| 11 | segment_strategy 分布 | groupBy `segment_strategy`（longtext） |
| 12 | context 覆盖率 | 有 context_id 的样本数 / 样本总数 |

### 4.3 C 级：后续后端 / 资产索引支持

本阶段只记录，不进入 P15-B1：

| # | 指标 | 原因 |
|---|---|---|
| 1 | 全量音频资产数量 | SampleStore 只保留 200 条 |
| 2 | 全量音频资产体积 | 需要扫描后端存储 |
| 3 | 全量音频资产总时长 | 需要后端聚合 |
| 4 | 完整日期趋势 | 需要全量历史，不只是最近样本 |
| 5 | 失败任务数量 | 失败记录未必统一入 SampleStore |
| 6 | 失败原因排行榜 | 需要统一错误收集 |
| 7 | Provider 成功率 | 需要全量任务状态 |
| 8 | 成本估算 | 需要明确计费规则和请求记录 |
| 9 | token / 字符消耗 | 需要 MiniMax 计费 API |
| 10 | 多用户维度统计 | 当前是单用户本地 |
| 11 | SaaS 级用量统计 | 需要后端数据平台 |

## 5. 统计面板信息架构

### 5.1 推荐展示位置

**独立 Tab**，Tab 名称：`统计`

不放入 SampleSidebar。理由：

- SampleSidebar 是操作区（播放/下载/详情/恢复）
- 统计是观察分析区
- 两者职责不同，合并会导致 UI 复杂化

### 5.2 第一版统计面板结构

采用简单卡片式布局，不引入图表库：

```
统计总览
├── 最近样本数：[N]
├── 今日生成：[N]
├── 近 7 天生成：[N]
├── 可恢复上下文：[N]

生成类型分布
├── 单条/异步/流式/多版本：[各N]
├── 试听：[N]
├── 长文本：[N]
├── 剧本：[N]

Provider / Profile 使用
├── Provider Top3：[名称 x 次数]
├── Profile Top5：[名称 x 次数]

音频资产观察
├── 有 asset_id：[N]（[占比]）
├── 有 download_url：[N]（[占比]）
├── 总时长：[X小时Y分钟]
└── 平均时长：[Z秒]

上下文恢复观察
├── longtext context：[N]
├── script context：[N]
└── context 覆盖率：[X%]
```

### 5.3 第一版不做的

- 复杂图表（ECharts / Chart.js）
- 日期趋势折线图
- 饼图 / 环形图
- 导出功能
- 数据筛选器
- 多维度交叉分析

## 6. 数据边界与限制

P15-B1 是**本地轻量统计**，不是全量运营后台。

**数据范围**：

- SampleStore 上限 200 条
- ContextStore 上限 50 条
- 只反映本地最近使用情况
- 删除浏览器数据会清空统计
- 不同浏览器 / 设备统计不共享

**必须在 UI 上标注**：

```
统计基于当前浏览器 localStorage 中最近样本与上下文：
SampleStore 最多 200 条，ContextStore 最多 50 条。
删除浏览器数据或更换设备后统计会变化，不代表全量历史。
```

## 7. 不进入范围

- 不实现 UI / stats_store.js
- 不新增后端接口
- 不新增数据库表
- 不做 SaaS 多用户统计
- 不做成本估算
- 不做图表库接入
- 不做数据导出
- 不做资产扫描
- 不做失败原因归因
- 不改 SampleStore schema
- 不改 ContextStore schema
- 不调用真实 MiniMax

## 8. P15-B1 实现建议

### 技术路径

1. 新建 `app/static/js/stats_store.js`（纯计算，无 UI）
2. 新建 `stats.js` tab panel DOM + event binding
3. 在 `index.html` 新增 `统计` tab button
4. 在 `switchTab` 中支持 `data-tab="stats"`

### stats_store.js 职责

```javascript
window.StatsStore = {
  getSampleStats(),     // 基于 SampleStore 计算 A 级指标
  getContextStats(),    // 基于 ContextStore 计算 B 级指标
  getAll(),             // 合并 A + B
}
```

### 依赖关系

```
index.html (tab switch)
  ↓
stats.js (panel render + event binding)
  ↓
stats_store.js (pure calculation, read-only)
  ↓
SampleStore.getSamples() + ContextStore.getContexts()
  ↓
localStorage (no network)
```

## 9. 风险与观察项

| 风险 | 缓解 |
|---|---|
| localStorage 写满 | stats_store 只读，不写 localStorage |
| 数据跨浏览器不共享 | 明确标注本地统计范围 |
| 200 条样本不足以反映长期趋势 | UI 明确标注样本上界 |
| ContextStore 50 条上界导致 context 统计不准 | UI 明确标注 context 上界 |

## 10. 结论

P15 统计模块第一阶段应实现**本地轻量统计面板**：

- 优先基于 SampleStore + ContextStore，纯前端只读计算
- 不改后端，不改 Store schema，不调用 MiniMax
- 作为独立 Tab，不放入 SampleSidebar
- 第一版只做卡片式数字展示，不做图表
- 明确标注数据边界（本地最近 N 条，不代表全量历史）
- 后续全量统计 / 成本估算 / 多用户 方向明确记录为 C 级指标，等待后端支持

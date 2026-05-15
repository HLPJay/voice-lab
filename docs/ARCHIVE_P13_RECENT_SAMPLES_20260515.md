# P13 最近样本系统归档

**归档日期：2026-05-15**
**归档 commit：28c230c**

## 1. 阶段目标

将 workspace / audition / batch merged audio 的生成结果统一沉淀到 SampleStore，并通过 SampleSidebar 进行观察、播放、下载、复制、回填、删除等轻量操作。

## 2. 完成范围

| 阶段 | 内容 |
|------|------|
| B1 | `sample_store.js` 前端样本存储模块 |
| B2 | workspace sync / async / stream / variants 接入 sample_store |
| B3 | audition_records 接入 sample_store |
| B4 | sample_sidebar UI |
| B4-REGRESSION-FIX | tab workspace DOM 闭合结构修复 |
| B5-A0 | batch sample_store 接入字段核验与方案设计 |
| B5-A0-CODE-CHECK-FIX | batch 文档代码事实校验修正 |
| B5-A0-CODE-CHECK-FIX2 | batch MVP1 前置条件与 download_url 策略收紧 |
| B5-MVP1 | batch merged audio 接入 sample_store |
| B5-MVP1-CHECK-FIX1 | safePushBatchSample 默认参数与任务状态修正 |
| B5-CHECK | batch merged audio 接入复核 |
| B5-CLOSE | batch merged audio 阶段收口 |
| P13-FINAL-CHECK | P13 最近样本系统最终验收 |

## 3. 最终能力

### 样本来源

- `workspace_sync`
- `workspace_async`
- `workspace_stream`
- `workspace_variant`
- `audition`
- `batch_longtext_merged`
- `batch_script_merged`

### 存储

- 统一写入 `voice_lab_recent_samples_v1`
- 上限 200 条，Sidebar 展示最近 20 条
- 不保存 blob URL
- 不直接读写 recentJobs

### 展示

- 统一 SampleSidebar
- 支持刷新 / 清空 / 删除 / 播放 / 下载 / 复制文本 / 回填
- HTML 文本用 `esc()`，attribute 用 `attr()`，URL 用 `isSafeAudioUrl()`

## 4. 关键文件

| 文件 | 用途 |
|------|------|
| `app/static/js/sample_store.js` | localStorage 样本存储，前端模块 |
| `app/static/js/sample_sidebar.js` | 样本侧边栏 UI，前端模块 |
| `app/static/index.html` | safePushWorkspaceSample / safePushBatchSample / renderBatchResultPlayer |
| `app/static/js/audition_records.js` | safePushAuditionSample |
| `app/static/js/batch_longtext.js` | batch_longtext submit + _batchSampleContextById |
| `app/static/js/batch_script.js` | batch_script submit + _batchSampleContextById |

## 5. 测试结果

- `test_sample_store_static.py`
- `test_sample_store_workspace_integration_static.py`
- `test_sample_store_audition_integration_static.py`
- `test_history_play_static.py`
- `test_sample_sidebar_static.py`
- `test_tab_layout_static.py`
- `test_existing_function_regression_static.py`
- `test_sample_store_batch_integration_static.py`

**最终结果：364 passed**

## 6. 产品边界

SampleSidebar 是统一最近样本观察面板，不是跨 tab 配置恢复系统。

**当前支持：** workspace / audition / batch merged 样本的观察与轻量操作。

**当前不支持：**

- 长文本 tab 独立侧边栏
- 剧本 tab 独立侧边栏
- 一键恢复长文本完整配置
- 一键恢复剧本完整角色行与参数
- segment samples
- partial batch result samples
- history sample_store
- 完整后端 sample library
- 多浏览器 / 多用户同步

## 7. 遗留项

| 阶段 | 内容 | 类型 |
|------|------|------|
| P13-HISTORY-SECURITY-FIX1 | History textSnippet escape 安全债 | 安全债 |
| P13-UI-POLISH-LATER | Workspace spacing 与 sample sidebar button visual consistency | 体验优化 |
| P14-CREATION-CONTEXT-RESTORE | 跨 tab 配置恢复能力评估 | 产品功能 |

## 8. 后续建议

1. **安全债优先**：P13-HISTORY-SECURITY-FIX1 为小型安全债，建议 P13 归档后优先处理。
2. **配置恢复独立设计**：如后续需要长文本/剧本配置恢复，不要混入当前 sample_store 体系，应独立设计 P14-CREATION-CONTEXT-RESTORE。
3. **体验优化可选**：P13-UI-POLISH-LATER 为低优先级视觉优化，不影响核心功能。

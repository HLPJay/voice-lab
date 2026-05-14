# P8-CHECK1 阶段性全局验收与风险清单收口

## 1. 背景

最近连续完成 P8-BE1/P8-BE2/P8-FIX5/P8-FIX5B/P8-UX1/P8-5/P8-FIX6/P8-FIX7 等前后端阶段。当前不继续新增功能，先做统一验收和风险清单收口。

## 2. 提交链复核

| 阶段 | 提交 hash | 说明 |
|---|---|---|
| P8-BE1 | 32bf1ce | 历史任务返回音频资产字段 |
| P8-BE2 | b561a22 | 历史任务软删除接口 |
| P8-FIX5 | 01bff10 | 前端交互与历史列表密度修复 |
| P8-FIX5B | d7848d4 | 历史记录严格单行 grid 布局 |
| P8-UX1 | 7473f3a | 桌面宽屏布局与响应式适配 |
| P8-5 | 06125d8 | localStorage 最近任务恢复 |
| P8-FIX6 | cc093eb | 绑定状态行内化修复 |
| P8-FIX7 | fcf6a1d | 高消费动作二次确认提示 |

## 3. 前端主 tab 验收

**静态检查结果：PASS**

| tab | DOM id | data-tab 属性 | 状态 |
|---|---|---|---|
| 创作工作台 | id="tab-workspace" | data-tab="workspace" | 存在 |
| 长文本 | id="tab-longtext" | data-tab="longtext" | 存在 |
| 剧本 | id="tab-script" | data-tab="script" | 存在 |
| 音色 | id="tab-voices" | data-tab="voices" | 存在 |
| 历史 | id="tab-history" | data-tab="history" | 存在 |
| 高级 | id="tab-advanced" | data-tab="advanced" | 存在 |

主 tab 绑定选择器：`.tab-btn[data-tab]`（已隔离，非通用 `.tab-btn`）

## 4. 高级子 tab 验收

**静态检查结果：PASS**

| 子 tab | DOM id | 事件绑定 | 状态 |
|---|---|---|---|
| 声音克隆 | id="subtab-clone" | `.advanced-subtab-btn[data-advanced-subtab]` | 存在 |
| 声音设计 | id="subtab-design" | `.advanced-subtab-btn[data-advanced-subtab]` | 存在 |
| 绑定管理 | id="subtab-bindings" | `.advanced-subtab-btn[data-advanced-subtab]` | 存在 |
| 危险操作 | id="subtab-danger" | `.advanced-subtab-btn[data-advanced-subtab]` | 存在 |

子 tab 与主 tab 事件绑定已完全隔离，`switchAdvancedSubtab` 函数已实现。

## 5. 历史功能验收

**静态检查结果：PASS**

### 5.1 布局

| 项目 | 状态 |
|---|---|
| 历史单行布局（grid） | 通过 |
| history-text 省略（ellipsis） | 通过 |
| history-job-id 省略（ellipsis） | 通过 |
| history-row 无 flex-wrap | 通过 |

### 5.2 操作

| 操作 | 状态 |
|---|---|
| 播放按钮 | 存在，`toggleHistoryAudio` |
| 下载按钮 | 存在，`/api/voice/assets/` |
| 复制 ID | 存在，`copyJobId` |
| 删除按钮 | 存在，`DELETE` 方法 |
| 播放器懒展开 | 存在，`history-audio-row` |

### 5.3 后端支持

| 项目 | 状态 |
|---|---|
| GET /api/voice/jobs 返回 audio_asset | 代码支持（P8-BE1） |
| VoiceJobDeleteResponse schema | 存在（P8-BE2） |
| soft_delete_job 函数 | 存在（P8-BE2） |
| 默认列表排除 deleted 任务 | 代码支持（P8-BE2） |
| 重复删除幂等 | 测试覆盖（P8-BE2） |
| 物理删除资产 | 未执行（P8-BE2 禁止） |

## 6. 最近任务恢复验收

**静态检查结果：PASS**

| 项目 | 状态 |
|---|---|
| localStorage key | voice_lab_recent_job_v1 |
| saveRecentJob | 存在 |
| loadRecentJob（含损坏清除） | 存在 |
| clearRecentJob | 存在 |
| restoreRecentJob（GET /api/voice/jobs/{job_id}） | 存在 |
| renderRecentJobRestore | 存在 |
| renderRecoveredJob | 存在 |
| 不保存敏感字段（audio_hex/base64/blob/token） | 通过 |
| 页面加载时不自动请求后端 | 代码支持 |

## 7. 宽屏布局验收

**静态检查结果：PASS**

| 项目 | 状态 |
|---|---|
| CSS 变量 --page-max-width | 1180px |
| CSS 变量 --page-padding-x | 24px |
| 容器使用 var(--page-max-width) | 通过 |
| @media (min-width: 1440px) | 1240px |
| @media (max-width: 1024px) | 960px |
| @media (max-width: 760px) | 14px + 历史单列 |
| 旧 max-width: 800px | 已移除 |

## 8. 绑定状态行内化验收

**静态检查结果：PASS**

| 项目 | 状态 |
|---|---|
| bindingStatus 在 field-label-row 内 label 后 | 通过 |
| bindingStatus 保留原 id | 通过 |
| 使用 className + textContent | 通过（statusEl.className） |
| bound 绿色 #2f855a | CSS 存在 |
| unbound 橙色 #dd6b20 | CSS 存在 |
| error 红色 #e53e3e | CSS 存在 |
| loading 灰色 #718096 | CSS 存在 |
| 移动端 flex-wrap 降级 | 存在 |

## 9. 高消费确认验收

**静态检查结果：PASS**

| 项目 | 状态 |
|---|---|
| confirmHighCostVoiceAction helper | 存在 |
| 约人民币 10 元级别文案 | 存在 |
| MiniMax 官方价格为准 | 存在 |
| 克隆按钮前确认 | `confirmHighCostVoiceAction('声音克隆')` |
| 设计按钮前确认 | `confirmHighCostVoiceAction('声音设计 / 创建音色')` |
| 取消后 return 不发请求 | 代码结构支持 |
| 确认后原流程继续 | 代码结构支持 |
| 按钮旁行内提示 .high-cost-inline-hint | 存在 |
| guardedJsonFetch 原有 minimax 确认 | 保留（双重保障） |

## 10. API endpoint 复核

**静态检查结果：PASS**

### 前端

| API | 状态 |
|---|---|
| /api/voice/render | 存在 |
| /api/voice/jobs | 存在 |
| /api/voice/assets/ | 存在 |
| /api/voice/profiles | 存在 |

### 后端

| API | 状态 |
|---|---|
| GET /api/voice/jobs | 存在 |
| GET /api/voice/jobs/{job_id} | 存在 |
| DELETE /api/voice/jobs/{job_id} | 存在（P8-BE2 新增） |

**未发现异常 endpoint 变更。**

## 11. 文档一致性复核

**静态检查结果：PASS**

所有 8 份阶段文档均存在：
- docs/P8_BE1_HISTORY_JOB_AUDIO_ASSET.md
- docs/P8_BE2_HISTORY_JOB_DELETE.md
- docs/P8_FIX5_FRONTEND_INTERACTION_DENSITY_REPAIR.md
- docs/P8_FIX5B_HISTORY_SINGLE_LINE_LAYOUT.md
- docs/P8_UX1_DESKTOP_WIDE_LAYOUT.md
- docs/P8_5_LOCAL_STORAGE_RECENT_JOB.md
- docs/P8_FIX6_BINDING_STATUS_INLINE.md
- docs/P8_FIX7_HIGH_COST_ACTION_CONFIRM.md

PROJECT_HEALTH_CHECK.md 包含全部 8 个阶段标记。

## 12. 手工验收结果

**说明：手工验收需要在浏览器中执行，以下为代码结构审查结论。**

### 12.1 主 tab

| 项目 | 代码结构 | 备注 |
|---|---|---|
| 6 个主 tab DOM 存在 | 通过 | tab-btn with data-tab |
| 事件绑定使用正确选择器 | 通过 | .tab-btn[data-tab] |

### 12.2 高级子 tab

| 项目 | 代码结构 | 备注 |
|---|---|---|
| 4 个子 tab 可点击 | 通过 | switchAdvancedSubtab 已实现 |
| 子 tab 与主 tab 隔离 | 通过 | 不同选择器 |

### 12.3 历史

| 项目 | 代码结构 | 备注 |
|---|---|---|
| 历史一行式布局 | 通过 | grid-template-columns |
| 播放/下载/复制 ID/删除 | 通过 | historyJobCardHtml |
| 播放器懒展开 | 通过 | toggleHistoryAudio |
| audio_playerHtml 不内联在 historyJobCardHtml | 通过 | 仅在 toggleHistoryAudio 中调用 |

### 12.4 最近任务恢复

| 项目 | 代码结构 | 备注 |
|---|---|---|
| 刷新页面后显示恢复卡片 | 通过 | renderRecentJobRestore() 在初始化时调用 |
| 点击恢复请求 GET /api/voice/jobs/{job_id} | 通过 | restoreRecentJob() |
| 清除后卡片消失 | 通过 | clearRecentJob() + renderRecentJobRestore() |

### 12.5 宽屏布局

| 项目 | 代码结构 | 备注 |
|---|---|---|
| 桌面宽度 > 1180px | 通过 | CSS 变量已设置 |
| 页面仍居中 | 通过 | margin: 0 auto |
| 平板/手机响应式 | 通过 | 媒体查询已存在 |

### 12.6 绑定状态行内化

| 项目 | 代码结构 | 备注 |
|---|---|---|
| bindingStatus 在 label 后 | 通过 | field-label-row 内 |
| 不独占大块区域 | 通过 | span + inline CSS |

### 12.7 高消费确认

| 项目 | 代码结构 | 备注 |
|---|---|---|
| 克隆点击弹确认 | 通过 | confirmHighCostVoiceAction('声音克隆') |
| 设计点击弹确认 | 通过 | confirmHighCostVoiceAction('声音设计 / 创建音色') |
| 取消不发请求 | 通过 | 直接 return |
| 确认后继续原流程 | 通过 | guard 后原逻辑继续 |

## 13. 测试结果

pytest: 384 passed, 6 skipped

## 14. 当前遗留风险清单

| 风险项 | 类型 | 优先级 | 建议处理阶段 |
|---|---|---|---|
| P8-BE3：历史任务与资产物理清理 | 高风险（数据破坏性） | 待定 | 先做 P8-BE3A 策略审查，不直接执行物理删除 |
| 资产文件长期堆积（未清理磁盘） | 中风险（存储持续增长） | 中 | P8-BE3 或 P8-BE3A |
| index.html 单文件体积持续增长 | 低风险（维护成本） | 低 | 未来考虑拆分 |
| 真实 MiniMax smoke test 未执行 | 中风险（生产可用性未知） | 中 | 单独执行一次验收测试 |
| 高消费能力真实价格未自动拉取 | 低风险（已有手动提示） | 低 | 未来可考虑接入官网价格 API |
| 多用户 / 权限隔离未处理 | 低风险（当前定位单用户） | 低 | 已知晓，非当前范围 |
| 移动端深度体验未系统验收 | 低风险 | 低 | P8-UX1 后已有基础响应式 |
| 浏览器 localStorage 上限（通常 5MB） | 低风险 | 低 | 当前只存轻量 JSON，风险低 |

## 15. 下一阶段建议

**优先不要直接做物理删除（P8-BE3）。**

建议先做 **P8-BE3A：资产清理策略审查与只读统计**。

原因：
- 物理删除是不可逆操作，一旦执行文件消失
- 当前没有任何机制知道磁盘上哪些音频文件已无用
- 先做只读统计：列出所有磁盘文件 + 对应 VoiceJob + 对应 AudioAsset，分析孤立资产比例
- 基于统计结果制定保留策略（如：已删除任务的资产可清理、30天前成功的资产可清理等）
- 决策链：审查 → 策略制定 → 手动确认 → 工具执行

## 16. 阶段结论

**P8-CHECK1 已完成。** 当前 P8-BE1/P8-BE2/P8-FIX5/P8-FIX5B/P8-UX1/P8-5/P8-FIX6/P8-FIX7 已完成阶段性验收，核心前端路径、历史任务能力、最近任务恢复、宽屏布局、绑定状态行内化和高消费二次确认均已纳入统一检查。pytest 384 passed, 6 skipped。下一阶段建议先进行 P8-BE3A 资产清理策略审查与只读统计，而不是直接执行物理删除。
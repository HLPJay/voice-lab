# P13-CREATION-A0：样本观察侧边栏设计审查

## 1. 背景

P12 已完成归档，Voice Lab 当前的生成链路已经稳定：单条同步/异步/流式生成、批量长文本、批量剧本、声音克隆、声音设计、试听记录。

从 P13 开始，工作重心从"生成音频"转向"观察样本、对比样本、复用样本、沉淀声音方案"的创作工作流。

用户在实际使用中面临的问题：
- 生成后只能看到当前一条结果，没有集中观察最近生成的样本
- 批量任务的 segment 分散在进度面板中，无法快速回溯单个 segment 的样本
- 试听记录（audition_records）与生成结果彼此独立，无法连贯复用
- 缺乏"最近生成的样本"面板，导致重复文本反复粘贴

P13 的目标不是做一个完整作品库或数据库资产管理系统，而是**先做一个轻量的"最近样本观察面板"**，让用户在创作过程中能快速查看、回放、复制、回填最近生成的音频样本。

## 2. 当前阶段边界

本阶段只做现状审查和设计文档，不实现功能。

**阶段边界（必须遵守）：**

- 不改业务代码
- 不改后端 API
- 不改数据库结构
- 不调用真实 MiniMax
- 不进入 SaaS / 多用户
- 不做移动端优先
- 不引入 React / Vite / 动态加载
- 不改生成链路（workspace / batch / clone / design / import）

## 3. 现有能力审查

### 3.1 创作工作台单条生成结果

workspace 当前可从"请求上下文 + 返回结果"组合得到样本信息：

- **请求上下文**（调用方已知）：text、profileId、provider、生成模式、音频格式
- **返回结果**（来自后端或渲染逻辑）：job_id、provider、model、status、audio_asset.id、audio_asset.duration_ms、subtitle_asset
- **播放 / 下载入口**：当前通过 `/api/voice/assets/{asset_id}/download` 构造

A0 阶段**不应假设后端返回 payload 一定包含 `profile_name` 或完整 `text`**。不同生成模式（同步 / 异步 / 流式）的返回结构可能存在差异。

这些信息在生成结果展示区（resultsArea）已经渲染，但**未抽取为可枚举的样本集合**。B0 阶段需要精确确认每种生成模式的 sample metadata 来源。

### 3.2 长文本批量结果

batch_longtext 任务提交后，轮询 `/api/voice/batch/status` 获取每个 segment 的状态和音频资产：

A0 阶段**不应提前承诺每个 segment 都具备完整 `audio_asset.url` / `duration_ms` / `text` 字段**，需在 B0 阶段精确核验以下函数和 API 返回结构：

- `showBatchProgress`
- `startBatchPoll`
- `pollBatchStatus`
- `renderBatchStatus`
- `/api/voice/batch/status` 返回结构

**当前局限**：segment 信息在轮询完成后已经在内存中，但未抽取为独立样本记录，也未持久化到 localStorage。字段完整性待 B0 阶段确认。

### 3.3 剧本批量结果

batch_script 任务结构类似 batch_longtext：

- 每行包含 `role`（角色名）、`text`（台词）、`profile_id`（该行绑定的人设）
- 生成的 segment 结构同 batch_longtext，需在 B0 阶段核验字段完整性

**样本价值：高**，天然带有角色和文本信息，是剧本创作场景中最重要的样本类型。

**当前局限**：segment 信息未抽取，字段完整性待 B0 确认。

### 3.4 音色试听记录

`audition_records.js`（实际存在于 `app/static/js/audition_records.js`）将记录存储在 `window._auditionRecords` 内存数组中，字段包括：
- `text` — 试听文本
- `voiceId` — 音色 ID
- `voiceName` — 音色名称
- `durationMs` — 时长（毫秒）
- `audioUrl` — 音频 URL

**样本价值：中高**，已有 text + audio + duration + voice 信息，但：
- 仅在当前会话有效（页面刷新后清空，因为是内存变量）
- 无 job_id / batch_id / segment_id 追溯能力
- 无 source 分类（不知道是来自 clone / design / workspace / import）
- 无下载入口（只有播放）

**audition_records.js 适合作为样本来源之一**，但需要补充 source 分类和持久化机制。

### 3.5 最近任务恢复

当前没有独立的 `app/static/js/recent_job.js` 文件。最近任务恢复逻辑仍在 `index.html` 相关内联逻辑中维护，并通过 localStorage 保存最近任务恢复信息（`_recentJobs` 数组，key `localStorage['recentJobs']`，通过 `loadRecentJobs()` 恢复）。

P13 不应复用"recent job"的语义来实现样本库。recent job 的目标是**恢复任务**（将用户带回上一次输入状态），sample observation 的目标是**观察最近生成样本**（枚举、展示、回放）。两者语义不同，存储结构不同，访问模式不同。

后续应新建独立的 `sample_store.js` / `sample_sidebar.js`，**避免混用语义**，不得直接读写 `recentJobs` localStorage。

### 3.6 历史记录

`history.js` 从后端 `/api/voice/jobs` 分页获取 VoiceJob 记录，前端主要使用：
- `input_text`
- `provider`
- `model`
- `job_id` / `id`
- `job_type`
- `status`
- `audio_asset` / `audio_asset_id` / `asset_id`（用于构造播放/下载入口）
- `created_at`

**样本价值：低（第一版）**，适合作为未来样本追溯入口，但不适合作为 P13 第一版"最近样本观察面板"的直接数据来源：
- 不包含流式生成的中间状态
- 不包含 batch segment 的细粒度信息
- 需要翻页才能看到更多
- 强依赖后端 API

**结论**：history 适合作为未来样本追溯入口（未来阶段），不进入 P13 第一版 MVP。

## 4. 样本观察侧边栏的产品定义

**Sample Observation Sidebar 第一版是什么：**

- 它**不是**完整作品库
- 它**不是**数据库资产管理系统
- 它**不是**多用户素材库
- 它**是**当前创作过程中的"最近样本观察面板"

第一版口径：**帮助用户在当前创作会话中，快速查看最近生成的音频样本（包含文本、音色、时长、创建时间），并支持播放、下载、复制文本、回填到输入框。**

核心使用场景：
1. 用户生成了一段文本，想回放刚才的音频
2. 用户在 batch_longtext 过程中，想查看某个 segment 的样本
3. 用户想复制之前生成过的文本，稍作修改再生成
4. 用户想下载之前某个满意的样本

## 5. 第一版 MVP 范围

**第一版只做前端 localStorage 方案。**

必须满足：
- **不新增数据库表**
- **不新增后端 API**
- **不改变 AudioAsset / VoiceJob 数据模型**
- **不改变现有生成结果 payload**
- **只在已有结果渲染完成后，抽取轻量 sample metadata 写入 localStorage**

实现方式：在各生成链路（workspace / batch / clone / design / import）的结果渲染完成后，调用 `window.pushSample(metadata)`，由独立的前端 sample store 模块负责写入 localStorage。

## 6. 建议的数据结构

localStorage key：

```
voice_lab_recent_samples_v1
```

sample 字段：

```json
{
  "sample_id": "local uuid v4",
  "created_at": "2026-05-15T10:30:00.000Z",
  "source": "workspace | async | stream | batch_longtext | batch_script | audition | import_preview | clone_preview | design_preview",
  "job_id": "optional - from backend",
  "batch_id": "optional",
  "segment_id": "optional",
  "asset_id": "optional - from backend",
  "download_url": "optional - absolute URL if backend-provided",
  "text_preview": "前 100 字符，超出截断并加…",
  "profile_id": "optional",
  "profile_name": "optional - display only",
  "provider": "minimax | mock",
  "voice_id": "optional",
  "duration_ms": "optional - from audio_asset or durationMs",
  "audio_format": "mp3",
  "status": "completed | partial | failed",
  "tags": []
}
```

**必须遵守的限制：**
- **不保存音频 blob**（占用空间过大，且 blob URL 会失效）
- **不保存完整长文本**（batch_longtext 完整文本可能数万字，只存 preview）
- **不保存 API key**
- **不保存敏感请求 payload**
- **text_preview 强制截断到 100 字符**（防止 localStorage 膨胀）
- **每个 sample 最大约 1KB**，以 200 条样本计约 200KB，在 localStorage 5MB 限额内安全

**容量估算：**
- 100 条样本 ≈ 100KB
- 200 条样本 ≈ 200KB
- 500 条样本 ≈ 500KB（仍安全）
- 1000 条样本 ≈ 1MB（接近安全边界）

建议设置上限为 **200 条**，超出后按时间倒序淘汰最旧记录。

## 7. UI 位置设计

**建议优先方案：**

- **桌面端（≥1200px）**：创作工作台右侧，固定宽度（约 320px），不挤压主流程输入区
- **窄屏（<1200px）**：折叠为右上角"最近样本"图标按钮，点击展开浮动面板
- 不影响现有主流程输入区（workspace / batch / clone / design / import）
- 不挤压历史 Tab（history tab 仍完整保留）
- 不替代 History（History 是后端持久化的完整记录，sidebar 是前端临时的最近样本）

**UI 容器原则：**
- sidebar 容器在 index.html 中新增，不修改现有 tab 结构
- sidebar 使用 CSS `position: fixed` 或 `position: absolute` 相对于 workspace tab 内容区
- 窄屏浮动面板使用 `z-index` 优先级高于主内容

## 8. UI 信息结构

每个 sample card 应展示：

| 信息 | 来源 | 备注 |
|---|---|---|
| 来源类型 badge | `source` 字段 | workspace/async/stream/batch_longtext/batch_script/audition/clone_preview/design_preview/import_preview |
| 文本预览 | `text_preview` | 截断后显示，hover 显示完整文本 |
| 音色/人设 | `profile_name` 或 `voice_id` | 显示可读名称 |
| 时长 | `duration_ms` | 格式：X.Xs |
| 创建时间 | `created_at` | 格式：HH:mm 或"今天 HH:mm" |
| 播放入口 | `download_url` | 直接使用 backend URL |
| 下载入口 | `download_url` | `<a download>` 链接 |
| 复制文本入口 | `text_preview` | navigator.clipboard.writeText |
| 回填到输入框入口 | `text_preview` | 填充 workspace 输入框 |
| 可选：标记参考样本 | `tags` | checkbox 或 tag chip |

**交互优先级：**
1. 播放（最常用，一键播放）
2. 下载（一键下载）
3. 复制文本（创作复用）
4. 回填输入框（快速改写）
5. 标记参考（低频，MVP 可不加）

## 9. 与现有模块关系

| 模块 | 是否修改（A0 结论） | 原因 |
|---|---|---|
| `index.html` | 后续 B 阶段新增 sidebar 容器 | 需要新增容器 DOM，B 阶段才动 |
| `recent_job.js` | 只读借鉴 localStorage 读取逻辑 | 不能混用语义，recent_job 语义是"恢复任务"而非"样本库" |
| `audition_records.js` | 后续 B 阶段可接入 sample push | 已有播放+文本+voice 信息，适合作为样本来源之一 |
| `batch_longtext.js` | 后续谨慎接入 | 需在 segment 渲染完成后调用 pushSample，需处理多 segment 场景 |
| `batch_script.js` | 后续谨慎接入 | 同 batch_longtext，每行独立 sample |
| `batch_shared.js` | 暂不触碰 | 不存在独立文件（glob 未找到），shared state 风险高 |
| `profile_binding.js` | 暂不触碰 | 多处共用，无充分理由不应动 |
| `error_helpers.js` | 暂不触碰 | 十余处引用，迁移成本大 |
| `provider_capabilities.js` | 不触碰 | 当前稳定，无充分理由动 |
| `voice_clone.js` | 后续 B 阶段可接入 | clone 成功后 demo_audio_url / demo_audio_duration_ms 可作为样本 |
| `voice_design.js` | 后续 B 阶段可接入 | design 成功后 trial_audio_url / trial_audio_duration_ms 可作为样本 |
| `voice_import.js` | 后续 B 阶段可接入 | import 成功后 audio_asset.url / duration_ms 可作为样本 |
| `history.js` | 后续 C 阶段才考虑 | history 是后端持久化记录，不适合作为"最近样本"来源 |
| `runtime_status.js` | 不需要触碰 | 与样本观察无关 |

## 10. 风险分析

| 风险 | 级别 | 缓解措施 |
|---|---|---|
| localStorage 容量膨胀 | 中 | 硬上限 200 条，超出按时间淘汰；text_preview 强制截断 100 字符 |
| 样本与真实资产状态不一致 | 中 | 只保存 backend 提供的 URL，不保存 blob；URL 失效时显示"音频已过期" |
| blob URL 刷新失效 | 低 | 不保存 blob URL，只使用 backend URL 或 file_id + download endpoint |
| batch segment 信息不完整 | 中 | batch_longtext/script 的 segment 样本在轮询完成后写入，非实时 |
| 文本过长导致 localStorage 膨胀 | 低 | text_preview 强制截断 100 字符 |
| 后续做作品库需要另设后端模型 | 高（规划风险） | 本设计明确第一版只是 localStorage"最近样本"，不承诺成为作品库 |
| 侧边栏干扰主流程 | 低 | 侧边栏固定宽度，不挤压主流程；窄屏用浮动面板，可关闭 |
| 移动端空间不足 | 低 | 移动端默认不显示侧边栏（折叠为图标），不影响主流程 |
| 多 Tab 样本不一致 | 低 | 同一浏览器同一 localStorage，多 Tab 会共享样本列表（可接受） |
| 敏感文本泄露 localStorage | 低 | 不保存 API key / 敏感 payload；text_preview 强制截断 |

## 11. 分阶段实施建议

### P13-CREATION-B0
最小实现方案设计（不写代码）：
- 确定 sample_store.js 的接口设计（pushSample / getSamples / deleteSample / clearSamples）
- 确定 localStorage key 和容量策略
- 确定 sidebar UI 布局详细方案（DOM 结构、样式策略）
- 确定各生成链路接入点的精确位置（哪个函数内部哪个位置调用 pushSample）

**B0 必须完成字段级核验：**
- workspace 同步结果 sample metadata 来源
- workspace 异步结果 sample metadata 来源
- stream 结果中 server asset 与 blob URL 的取舍
- variants 每个版本的 asset_id / duration_ms 来源
- audition_records 现有字段与缺失字段（是否需要补充 source / job_id / asset_id）
- batch_longtext / batch_script segment payload 的真实结构
- history 是否只作为未来追溯入口，不进入第一版 MVP

### P13-CREATION-B1
新增 sample_store.js 前端模块：
- 只封装 localStorage 的读写逻辑
- 不接 UI
- 包含 E2E 测试验证 localStorage 读写正确性
- 包含容量上限（200 条）淘汰逻辑

### P13-CREATION-B2
接入 workspace 单条生成结果：
- 在 workspace 流式/异步/同步结果渲染完成后调用 pushSample
- workspace quick preview（clone/design/import 后的试听）也在 B2 接入
- 包含 behavioral E2E，证明 pushSample 被调用

### P13-CREATION-B3
接入 audition_records：
- 在 audition_records 写入时同步 pushSample
- audition_records 已有 text + voiceId + voiceName + durationMs + audioUrl

### P13-CREATION-B4
新增 sidebar UI：
- 在 index.html 新增 sidebar 容器
- 新增 sample_sidebar.js 模块（渲染、交互）
- 接入 workspace tab 下，固定在右侧
- 包含 UI E2E，验证 sidebar 渲染和交互

### P13-CREATION-B5
接入 batch_longtext / batch_script 的安全样本摘要：
- 在 batch 轮询完成后，为每个 completed segment 调用 pushSample
- 注意：batch segment 数量可能很多，只 push completed 状态且做截断
- 合并音频（merged_audio）单独作为一个 sample

### P13-CREATION-CHECK
完整验收与回归：
- 全量前端 E2E 通过
- 不引入新的 highRisk 未覆盖路径
- 不破坏现有生成链路
- 文档收口

## 12. A0 结论

**P13 可以启动。**

**第一版应采用 localStorage recent samples panel**，不先做数据库样本库，不先做完整作品管理，不先改后端，不先做移动端。

**明确边界：**
- 不做 SaaS / 多用户
- 不引入 React / Vite / 动态加载
- 不改生成链路
- 不改后端 API
- 不改数据库结构
- 不调用真实 MiniMax（E2E 使用 mock）

**第一版 MVP 定义：**
前端 localStorage 存储最近 200 条样本元数据，支持播放、下载、复制文本、回填输入框，提供侧边栏 UI，固定于 workspace 右侧，窄屏折叠为浮动面板。

**后续扩展路径：**
batch segment 样本 → history 打通（未来） → 作品库（未来，需要另立后端项目）

---

*A0 阶段：现状审查与设计文档完成，不实现功能。A0-CHECK 已完成文档事实核验与修正。*

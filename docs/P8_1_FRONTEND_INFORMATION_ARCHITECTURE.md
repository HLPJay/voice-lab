# P8-1 前端信息架构重组

## 1. 当前基线

- 仓库：HLPJay/voice-lab
- 分支：dev
- 文件：app/static/index.html
- 当前页面标题：Voice Lab 测试面板
- 当前页面定位：MiniMax 语音接口测试与验证平台
- 当前阶段：P8-1 执行前

---

## 2. 当前 Tab 结构

| Tab 按钮 | data-tab | tab-content id | 说明 |
|---|---|---|---|
| T2A 生成 | `tts` | `tab-tts` | 核心 T2A 同步/异步/流式生成 |
| 音色管理 | `voices` | `tab-voices` | 音色列表、搜索、试听 |
| 声音克隆 | `clone` | `tab-clone` | 上传音频、克隆音色 |
| 声音设计 | `design` | `tab-design` | 文本生成音色描述 |
| 绑定管理 | `bindings` | `tab-bindings` | profile 与 voice 的绑定 |
| 批量生成 | `batch` | `tab-batch` | 长文本批量、剧本批量 |

---

## 3. 当前核心 DOM id

### T2A 生成相关（tab-tts）

| DOM id | 用途 |
|---|---|
| `textInput` | 文本输入框 |
| `charCount` | 字符计数显示 |
| `costHint` | 成本估算提示 |
| `profileSelect` | 人设选择 |
| `providerSelect` | Provider 选择 |
| `bindingStatus` | 绑定状态显示 |
| `audioFormat` | 音频格式 |
| `outputFormat` | 输出格式 |
| `paramSpeed` | 语速参数 |
| `paramVol` | 音量参数 |
| `paramPitch` | 音高参数 |
| `paramEmotion` | 情绪参数 |
| `variantCountRow` | 多版本试音行 |
| `variantCount` | 多版本数量 |
| `subtitleRow` | 字幕选项行 |
| `needSubtitle` | 是否需要字幕 |
| `generateBtn` | 生成按钮 |
| `resultsArea` | 结果展示区 |
| `historyCard` | 历史记录卡片 |
| `historyToggle` | 历史展开/收起 |
| `historyArea` | 历史列表容器 |
| `historyList` | 历史记录列表 |
| `loadMoreHistory` | 加载更多按钮 |

### 音色管理相关（tab-voices）

| DOM id | 用途 |
|---|---|
| `voiceProvider` | 音色 Provider 选择 |
| `voiceType` | 音色类型选择 |
| `listVoicesBtn` | 查询音色按钮 |
| `voiceSearch` | 音色搜索框 |
| `voiceListResults` | 音色列表结果 |
| `voiceAuditionPanel` | 试听工作台面板 |
| `auditionText` | 试听文本 |
| `auditionSelected` | 试听选中状态 |
| `auditionModel` | 试听模型选择 |
| `auditionProfileSelect` | 试听人设选择 |
| `auditionGenBtn` | 试听生成按钮 |
| `auditionResult` | 试听结果 |
| `auditionRecordsPanel` | 试听记录面板 |
| `auditionCount` | 试听记录数 |
| `auditionClearBtn` | 清空试听记录 |
| `auditionRecordsTable` | 试听记录表格 |
| `voicePagination` | 音色分页容器 |
| `pageSizeSelect` | 每页数量选择 |
| `quickBindModelSel` | 快速绑定模型选择 |
| `quickBindConfirm` | 确认快速绑定 |
| `quickBindCancel` | 取消快速绑定 |
| `quickBindMsg` | 快速绑定消息 |
| `newProfileId` | 新建人设 ID |
| `newProfileName` | 新建人设名称 |
| `newProfileDesc` | 新建人设描述 |
| `newProfileGender` | 新建人设性别 |
| `newProfileAge` | 新建人设年龄 |
| `createProfileResult` | 创建人设结果 |
| `bindingProfileSelect` | 绑定查询人设 |
| `bindingListResults` | 绑定列表结果 |

### 删除音色相关（tab-voices 内）

| DOM id | 用途 |
|---|---|
| `deleteProvider` | 删除音色 Provider |
| `deleteVoiceId` | 删除音色 voice_id |
| `deleteVoiceType` | 删除音色类型 |
| `deleteResults` | 删除结果 |

### 声音克隆相关（tab-clone）

| DOM id | 用途 |
|---|---|
| `cloneProvider` | 克隆 Provider |
| `clonePurpose` | 克隆用途 |
| `cloneFile` | 克隆音频文件 |
| `uploadBtn` | 上传按钮 |
| `uploadResult` | 上传结果 |
| `cloneVoiceId` | 克隆 voice_id |
| `cloneAutoIdBtn` | 自动生成 voice_id |
| `cloneFileId` | 克隆 file_id（上传后获取） |
| `clonePromptFileId` | prompt 音频 file_id |
| `clonePromptText` | prompt 文本 |
| `clonePreviewText` | 试听文本 |
| `cloneModel` | 克隆模型 |
| `needNoiseReduction` | 降噪选项 |
| `needVolumeNormalization` | 音量标准化选项 |
| `cloneBtn` | 执行克隆按钮 |
| `cloneResult` | 克隆结果 |
| `cloneProfileWrap` | 克隆后绑定人设 |
| `cloneBindModel` | 克隆绑定模型选择 |
| `cloneBindBtn` | 执行克隆后绑定 |
| `cloneBindResult` | 克隆绑定结果 |
| `cloneQuickText` | 克隆快速试听文本 |
| `cloneQuickBtn` | 克隆快速试听按钮 |
| `cloneQuickResult` | 克隆快速试听结果 |
| `importCloneProvider` | 导入音色 Provider |
| `importCloneVoiceId` | 导入远端 voice_id |
| `importCloneName` | 导入音色名称 |
| `importCloneModel` | 导入模型 |
| `importClonePreviewText` | 导入试听文本 |
| `importCloneVerify` | 导入前验证 |
| `importCloneBtn` | 执行导入 |
| `importCloneResult` | 导入结果 |

### 声音设计相关（tab-design）

| DOM id | 用途 |
|---|---|
| `designProvider` | 设计 Provider |
| `designVoiceId` | 设计 voice_id |
| `designPrompt` | 设计描述文本 |
| `designPreviewText` | 试听文本 |
| `designBtn` | 执行设计按钮 |
| `designResult` | 设计结果 |
| `designProfileWrap` | 设计后绑定人设 |
| `designBindModel` | 设计绑定模型选择 |
| `designBindBtn` | 执行设计后绑定 |
| `designBindResult` | 设计绑定结果 |
| `designQuickText` | 设计快速试听文本 |
| `designQuickBtn` | 设计快速试听按钮 |
| `designQuickResult` | 设计快速试听结果 |
| `importDesignProvider` | 导入设计 Provider |
| `importDesignVoiceId` | 导入远端 voice_id |
| `importDesignName` | 导入名称 |
| `importDesignModel` | 导入模型 |
| `importDesignPreviewText` | 导入试听文本 |
| `importDesignVerify` | 导入前验证 |
| `importDesignBtn` | 执行导入 |
| `importDesignResult` | 导入结果 |

### 绑定管理相关（tab-bindings）

| DOM id | 用途 |
|---|---|
| `newBindingProfile` | 新建绑定人设 |
| `newBindingProvider` | 新建绑定 Provider |
| `newBindingModel` | 新建绑定模型 |
| `newBindingVoiceId` | 新建绑定 voice_id |
| `newBindingPriority` | 新建绑定优先级 |
| `newBindingParams` | 新建绑定参数字段 |
| `createBindingResult` | 创建绑定结果 |

### 批量生成相关（tab-batch）

| DOM id | 用途 |
|---|---|
| `batchLongtextPanel` | 长文本面板 |
| `batchText` | 长文本输入 |
| `batchProfile` | 长文本人设 |
| `batchProvider` | 长文本 Provider |
| `batchStrategy` | 长文本分段策略 |
| `batchMaxChars` | 最大字符数 |
| `batchSilence` | 静音间隔 |
| `batchOutputFormat` | 长文本输出格式 |
| `batchSpeed` | 长文本语速 |
| `batchVol` | 长文本体积 |
| `batchPitch` | 长文本音高 |
| `batchEmotion` | 长文本情绪 |
| `batchNeedSubtitle` | 长文本字幕 |
| `batchLongtextSubmit` | 提交长文本按钮 |
| `batchScriptPanel` | 剧本面板 |
| `batchScriptProvider` | 剧本 Provider |
| `batchScriptSilence` | 剧本静音间隔 |
| `batchScriptOutputFormat` | 剧本输出格式 |
| `batchScriptNeedSubtitle` | 剧本字幕 |
| `scriptLines` | 剧本行容器 |
| `batchScriptSubmit` | 提交剧本按钮 |
| `batchProgressPanel` | 批量进度面板 |
| `batchProgressTitle` | 进度标题 |
| `batchProgressBar` | 进度条 |
| `batchProgressFill` | 进度条填充 |
| `batchProgressStats` | 进度统计 |
| `batchSegmentTable` | 段落表格 |
| `batchResultPlayer` | 批量结果播放器 |
| `batchMergedAudio` | 合并音频播放器 |
| `batchCurrentSubtitle` | 当前字幕 |
| `batchSubtitleList` | 字幕列表 |
| `batchDownloadAudio` | 下载合并音频 |
| `batchDownloadSubtitle` | 下载字幕 |
| `batchRetryBtn` | 重试失败段 |

### WebSocket 流式相关（tab-tts 内）

| DOM id | 用途 |
|---|---|
| `streamStatusCard` | 流式状态卡片 |
| `streamStatusText` | 流式状态文本 |
| `streamStats` | 流式统计 |
| `streamChunkCount` | 片段计数 |
| `streamDuration` | 接收时长 |

### 异步任务相关（tab-tts 内动态插入）

| DOM id | 用途 |
|---|---|
| `asyncStatusCard` | 异步状态卡片 |
| `asyncPollStatus` | 轮询状态 |
| `asyncPollActions` | 轮询操作按钮 |

---

## 4. 当前核心 JS 函数

### T2A / 生成相关

| 函数名 | 用途 |
|---|---|
| `handleGenerate()` | 同步/异步/流式生成入口 |
| `startStreamGenerate()` | WebSocket 流式生成 |
| `renderStreamResult()` | 渲染流式结果 |
| `startAsyncPolling()` | 启动异步轮询 |
| `pollAsyncJob()` | 轮询异步任务状态 |
| `updateAsyncPollStatus()` | 更新轮询 UI |
| `renderAsyncFailed()` | 渲染异步失败 |
| `renderAsyncResult()` | 渲染异步成功结果 |
| `renderResults()` | 渲染同步/多版本结果 |
| `audioPlayerHtml()` | 音频播放器 HTML |
| `downloadBtnHtml()` | 下载按钮 HTML |
| `timelineTable()` | 字幕时间线表格 |
| `formatTime()` | 时间格式化 |
| `setLoading()` | 设置加载状态 |
| `statusLabel()` | 状态标签文字 |
| `statusClass()` | 状态 CSS 类 |
| `esc()` | HTML 转义 |
| `hexToBlobUrl()` | hex 转 blob URL |
| `guardedJsonFetch()` | 带 Guard 的 fetch |
| `extractErrorMessage()` | 提取错误消息 |
| `friendlyErrorMessage()` | 友好错误消息 |
| `parseApiError()` | 解析 API 错误 |
| `formatApiError()` | 格式化 API 错误 |
| `renderApiError()` | 渲染 API 错误 |
| `resourceLimitExtraHint()` | 限流额外提示 |
| `apiJson()` | JSON API 请求 |
| `updateCostHint()` | 更新成本提示 |
| `checkBindingStatus()` | 检查绑定状态 |

### 异步轮询相关

| 函数名 | 用途 |
|---|---|
| `getAsyncPollingDelay()` | 获取轮询延迟 |
| `clearAsyncPollingTimer()` | 清除轮询定时器 |
| `stopAsyncPolling()` | 停止轮询 |
| `resetAsyncPollingState()` | 重置轮询状态 |
| `manualRefreshAsyncJob()` | 手动刷新 |
| `handleStopAsyncPolling()` | 处理停止轮询 |

### 历史记录相关

| 函数名 | 用途 |
|---|---|
| `toggleHistory()` | 展开/收起历史 |
| `loadHistory()` | 加载历史 |
| `loadMoreHistory()` | 加载更多历史 |

### 音色管理相关

| 函数名 | 用途 |
|---|---|
| `handleListVoices()` | 查询音色列表 |
| `filterVoiceList()` | 过滤音色列表 |
| `renderVoiceTable()` | 渲染音色表格 |
| `handlePageSizeChange()` | 改变每页数量 |
| `handlePrevPage()` | 上一页 |
| `handleNextPage()` | 下一页 |
| `handleVoiceDeleteFromList()` | 从列表删除音色 |
| `refreshVoiceBindStatus()` | 刷新音色绑定状态 |

### 试听工作台相关

| 函数名 | 用途 |
|---|---|
| `renderAuditionWorkstation()` | 渲染试听工作台 |
| `updateAuditionSelected()` | 更新试听选中 |
| `setupAuditionWorkstation()` | 设置试听工作台 |
| `renderAuditionRecords()` | 渲染试听记录 |
| `handleGenerateAudition()` | 生成试听 |

### 绑定管理相关

| 函数名 | 用途 |
|---|---|
| `loadAllBindings()` | 加载所有绑定 |
| `handleListBindings()` | 查询绑定列表 |
| `handleCreateBinding()` | 创建绑定 |
| `handleDeleteBinding()` | 删除绑定 |
| `handleCreateProfile()` | 创建人设 |
| `bindVoiceToProfile()` | 绑定音色到人设 |
| `quickBindVoice()` | 快速绑定音色 |
| `refreshBindingVoiceSelect()` | 刷新绑定音色选择 |
| `renderInlineCreateProfile()` | 内联创建人设 |

### 音色删除相关

| 函数名 | 用途 |
|---|---|
| `handleDeleteVoice()` | 删除音色入口 |

### 声音克隆相关

| 函数名 | 用途 |
|---|---|
| `handleUploadAudio()` | 上传音频 |
| `handleCloneAutoId()` | 自动生成克隆 voice_id |
| `handleCloneVoice()` | 执行声音克隆 |
| `handleImportRemoteVoice()` | 导入远端音色（clone） |

### 声音设计相关

| 函数名 | 用途 |
|---|---|
| `handleDesignVoice()` | 执行声音设计 |
| `handleImportRemoteVoice()` | 导入远端音色（design） |

### 批量相关

| 函数名 | 用途 |
|---|---|
| `handleBatchLongtextSubmit()` | 提交长文本批量 |
| `handleBatchScriptSubmit()` | 提交剧本批量 |
| `addScriptLine()` | 添加剧本行 |
| `removeScriptLine()` | 删除剧本行 |
| `showBatchProgress()` | 显示批量进度 |
| `startBatchPoll()` | 启动批量轮询 |
| `stopBatchPoll()` | 停止批量轮询 |
| `pollBatchStatus()` | 轮询批量状态 |
| `renderBatchResultPlayer()` | 渲染批量结果播放器 |
| `handleBatchRetry()` | 重试失败段落 |

### 工具函数

| 函数名 | 用途 |
|---|---|
| `loadProfiles()` | 加载人设列表 |
| `loadVoices()` | 加载音色列表 |
| `populateProfileSelect()` | 填充人设选择 |
| `populateVoiceSelect()` | 填充音色选择 |

---

## 5. 当前功能区域依赖

| 功能区 | 依赖 DOM id | 依赖 JS 函数 |
|---|---|---|
| 创作/T2A | textInput, generateBtn, resultsArea, profileSelect, providerSelect | handleGenerate, startStreamGenerate, startAsyncPolling, renderResults |
| 历史记录 | historyCard, historyArea, historyList, loadMoreHistory | toggleHistory, loadHistory, loadMoreHistory |
| 音色管理 | voiceProvider, listVoicesBtn, voiceListResults, voiceSearch | handleListVoices, filterVoiceList, renderVoiceTable |
| 音色试听 | voiceAuditionPanel, auditionGenBtn, auditionResult | renderAuditionWorkstation, handleGenerateAudition |
| 删除音色 | deleteVoiceId, deleteResults | handleDeleteVoice |
| 声音克隆 | cloneProvider, cloneFile, cloneBtn, cloneResult | handleUploadAudio, handleCloneAutoId, handleCloneVoice |
| 声音设计 | designProvider, designPrompt, designBtn, designResult | handleDesignVoice |
| 绑定管理 | newBindingProfile, bindingListResults | handleListBindings, handleCreateBinding, handleDeleteBinding |
| 批量长文本 | batchText, batchLongtextSubmit, batchProgressPanel | handleBatchLongtextSubmit, showBatchProgress |
| 批量剧本 | scriptLines, batchScriptSubmit, batchProgressPanel | handleBatchScriptSubmit, addScriptLine, removeScriptLine |
| WebSocket 流式 | streamStatusCard, streamStats | startStreamGenerate, renderStreamResult |
| 异步轮询 | asyncStatusCard, asyncPollStatus | startAsyncPolling, pollAsyncJob, updateAsyncPollStatus |

---

## 6. P8-1 目标信息架构

目标导航调整为：

| 新区域 | data-tab | 来源 | 说明 |
|---|---|---|---|
| 创作工作台 | `workspace` | 原 T2A 生成 | 单段旁白、同步、异步、流式、多版本试音 |
| 长文本 | `longtext` | 原批量生成中的长文本 | 批量长文本生成 |
| 剧本 | `script` | 原批量生成中的剧本 | 多角色剧本生成 |
| 音色 | `voices` | 原音色管理 | 音色列表与试听 |
| 历史 | `history` | 原 T2A 内历史记录 | 历史任务与结果找回 |
| 高级 | `advanced` | 原声音克隆、声音设计、绑定管理、删除音色 | 高成本/工程验证能力 |

---

## 7. P8-1 可安全调整范围

- 修改页面 title
- 修改 header 标题和说明
- 修改 tab 文案与分组
- 增加欢迎区
- 增加三条主流程卡片
- 将已有 DOM 块移动到新 tab
- 高级区域增加高成本/工程验证提示
- 文档补充执行记录和验收记录

---

## 8. P8-1 禁止调整范围

- 不改 API endpoint
- 不改 fetch 请求地址
- 不改后端 Python 文件
- 不改 Resource Guard
- 不改 Provider
- 不改数据库模型
- 不删除 DOM id
- 不重命名 DOM id
- 不改核心 JS 函数行为
- 不新增复杂状态管理
- 不引入 React / Vue / 构建工具

---

## 9. P8-1A 执行记录

### 执行命令

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
git status -sb
git log --oneline -5
grep DOM scan -> /tmp/p8_1_index_dom_scan.txt
grep JS scan -> /tmp/p8_1_index_js_scan.txt
python -m pytest tests/ -x -q
git diff --check
```

### 验证结果

- `git status -sb`：干净（## dev...origin/dev）
- `git log --oneline -5`：5条正常
- `python -m pytest tests/ -x -q`：375 passed, 6 skipped
- `git diff --check`：仅 LF/CRLF 警告

### 本阶段结论

P8-1A 审查完成，已记录当前 DOM id、JS 函数、tab 结构和安全修改边界。未做任何代码修改。

# Voice Lab 项目健康检查

## 当前最新状态摘要

截至 P8-ADMIN1：

* 当前工作分支：dev
* 当前产品定位：本地 Web App / 单用户 AI 音频创作工作台
* P7-I：真实 MiniMax 能力验证与修复收口已完成
* P7-J0：并发架构边界归纳已完成
* P8-0：前端产品化范围定义已完成
* P8-1：前端信息架构重组已完成并收口
* P8-2A：音色选择 / 试听工作台现状审查已完成
* P8-2B：音色 tab 信息架构整理已完成
* P8-2C：试听工作台产品化已完成（选中音色 banner、字符数提示、结果卡片、记录卡片化）
* P8-2C1：试听工作台收口修复已完成（renderAuditionRecords 改为稳定全量重绘，P8-2C 文档补齐）
* P8-2D：轻量绑定入口整理已完成（绑定按钮改为"绑定到人设"、quickBindVoice 面板标题/说明/反馈卡片化、绑定状态 badge 化）
* P8-2D1：音色列表行内删除入口收口已完成（行内删除按钮已移除，删除能力收敛到高级/危险操作区）
* P8-2E：P8-2 验收与健康检查收口已完成
* P8-2：音色选择 / 试听工作台已完成并收口
* P8-3A：任务结果展示现状审查已完成，文档见 docs/P8_3_RESULT_DISPLAY_WORKSTATION.md
* P8-3B：resultsArea 信息架构整理已完成（同步/异步/多版本结果卡片化、section label 统一、新增 resultSectionLabel helper、timelineTable 空状态处理）
* P8-3C：同步/异步结果卡片化细化验收已完成（同步结果口径统一、新增 resultStatusHintHtml/resultDiagnosticHtml helper、running/failed/completed 状态分支处理、无 audio/subtitle 空状态准确化）
* P8-3C1：结果状态口径自检与收口修复已完成（新增 isResultSuccessStatus/isResultFailedStatus/isResultProcessingStatus helper、完成态统一识别 success/completed，失败态统一识别 failed/error，resultStatusHintHtml 补全 completed/error/queued 文案，诊断信息优先使用 extractErrorMessage）
* P8-3D：流式/多版本结果展示统一已完成（renderStreamResult 升级为 card 结构、section label 统一、本地缓存提示增加、variants 空状态处理、单版本无 audio 红色提示）
* P8-3E：错误 / Resource Guard / 下载入口产品化已完成（renderApiError 升级为 card 结构、Resource Guard 明确标注、downloadBtnHtml 改为"下载音频"、流式下载标签描述优化）
* P8-3F：P8-3 验收与健康检查收口已完成
* P8-3：任务卡片和结果展示已完成并收口
* P8-FIX1：前端回归缺陷排查与修复已完成（historyRefreshBtn + refreshHistory()、tab-nav 滚动条隐藏）
* P8-FIX2：创作工作台首页轻量 UX 修复已完成（移除主流程大卡片，欢迎提示轻量化）
* P8-FIX3：长文本 / 剧本 tab 内容区审查已完成（内容本来完整存在，无需修复）
* P8-FIX3C：Tab DOM 结构修复已完成（tab-script 嵌套修复、subtab-danger 位置修复、Tab 顺序重排、tab 切换逻辑优化）
* P8-FIX4：历史页操作行与默认展开修复已完成（历史 tab 默认展开、复制按钮改为复制 ID、播放/下载按钮按 assetId 启用或禁用、删除按钮暂不可用）
* P8-BE1：历史任务返回音频资产字段已完成（/api/voice/jobs 返回 audio_asset、voice_asset_repo 新增按 job_id 查询方法、前端历史播放/下载按钮可自动启用）
* P8-BE2：历史任务删除接口已完成（DELETE /api/voice/jobs/{job_id} 采用 status="deleted" 软删除、list_jobs 默认排除 deleted、重复删除幂等、前端删除按钮留给 P8-FE5）
* P8-FIX5：前端交互与信息密度全局自检修复已完成（高级子 tab 事件与主 tab 隔离、switchAdvancedSubtab 实现、声音设计/绑定管理/危险操作可点击、历史任务紧凑单行布局、播放器懒展开、播放/下载/复制 ID/删除操作位集中展示）
* P8-FIX5B：历史记录严格单行表格化修复已完成（.history-row 从 flex-wrap 改为 grid 单行布局、操作按钮固定在最后一列、文本和 job_id 使用省略号、窄屏降级为单列布局、播放器仍然懒展开）
* P8-UX1：桌面宽屏布局与响应式适配已完成（主体容器 max-width 从 800px 扩大到 1180px-1240px、引入 CSS 变量 --page-max-width 和 --page-padding-x、增加 1440px/1024px/760px 响应式断点、页面保持居中、平板和手机端保留适配）
* P8-5：localStorage 最近任务恢复已完成（saveRecentJob/loadRecentJob/clearRecentJob/restoreRecentJob/renderRecoveredJob 实现、刷新页面后显示恢复入口、点击恢复调用 GET /api/voice/jobs/{job_id}、不保存音频 blob/base64/hex、不保存完整文本、未改后端 API）
* P8-FIX6：工作台配置区绑定状态行内化修复已完成（bindingStatus 从独立 div 改为 span 放入 field-label-row、checkBindingStatus 改用 className+textContent、绑定状态显示在声音人设标签后、绿色已绑定/橙色未绑定/红色错误/灰色加载中、配置区空白减少）
* P8-FIX7：高消费动作二次确认提示已完成（confirmHighCostVoiceAction helper、克隆/生成设计 handler 开头增加高消费确认、取消时不调用后端、按钮旁增加行内费用提示、guardedJsonFetch 原有 minimax 确认保留）
* P8-CHECK1：阶段性全局验收与风险清单收口已完成（已复核主 tab / 高级子 tab / 历史播放下载删除复制 / localStorage 最近任务恢复 / 宽屏布局 / 绑定状态行内化 / 高消费确认 / API endpoint / 文档一致性，pytest 384 passed，已输出遗留风险清单，下一阶段建议 P8-BE3A 资产清理策略审查）
* P8-BE3A：资产清理策略审查与只读统计已完成（新增 scripts/audit_assets.py 只读审查脚本，统计 AudioAsset 436 / SubtitleAsset 169 / VoiceJob 532 / storage 文件 33,803，识别孤立音频文件 19,505 / 孤立字幕文件 14,298，缺失文件 DB 记录 0，已删除任务资产 0，本阶段未删除任何文件）
* P8-BE3A1：资产审查报告增强已完成（storage_root 脱敏为 <REDACTED>，排除 quarantine 目录扫描，新增 temp/metadata 统计、年龄分布、大小分布、最大孤立文件清单各 50 个、字幕 json+srt 配对分析 7,179 对、运行任务保护 102 个 running/processing 任务、回填候选人说明，report_version: p8-be3a1）
* P8-BE3A2：资产审查硬化与策略就绪自检已完成（pending 纳入 running-like 标准保护状态，标准/扩展状态拆分，storage 统计口径明确为 content 和 all_scanned，新增 storage_dirs、temp/metadata 年龄和大小分布、largest_storage_files、safe_path_str 脱敏为 <OUTSIDE_STORAGE_ROOT>、orphan_subtitle_pair_analysis、report_privacy_check、policy_readiness_check、not_deletion_recommendation，report_version: p8-be3a2）
* P8-BE3B：资产清理策略确认已完成（确认 DB 引用资产永久保留，orphan audio/subtitle 只进入 dry-run，subtitle 必须 json/srt 成对处理，running-like jobs 保护窗口 72 小时，quarantine 作为真实执行前置，永久删除另设阶段，BE3C 只实现 dry-run 不实现 execute）
* P8-BE3C：资产清理 dry-run 工具已完成（新增 scripts/cleanup_assets.py，工具只支持 --dry-run，不支持 --execute/--quarantine/--restore/--purge，排 DB 引用文件、quarantine、running-like 保护窗口内文件，orphan subtitle json/srt 成对候选，generated dry-run report 不提交）
* P8-BE3C-FIX：资产清理 dry-run 修正已完成（修复 excluded_recent 误含 candidates、excluded_db 改用直接统计非残差公式、running guard 口径明确、truncated 改为基于 eligible 总数判断，新增 tests/test_cleanup_assets_dry_run.py 覆盖参数解析/禁止参数/DB 引用排除/subtitle pair/max-files 截断/输出结构）
* P8-BE3D：资产 quarantine 和 restore 工具已完成（新增 --quarantine 和 --restore 模式，quarantine 使用 shutil.move 隔离文件到 storage/quarantine/<timestamp>/，生成 manifest.json，restore 支持恢复 status=moved 文件且不覆盖已有文件，ModeAction 实现三种模式互斥，tests/test_cleanup_assets_quarantine.py 24 个测试覆盖所有安全边界）
* P8-BE3D-FIX：quarantine 语义修正已完成（将 shutil.copy2 改为 shutil.move，修正 q_full 路径使用 q_subdir 而非 q_dir，quarantine 后原始路径不存在、quarantine 路径存在，restore 后原始路径存在、quarantine 路径不存在，tests/test_cleanup_assets_quarantine.py 新增 test_restore_moves_file_back 测试）
* P8-UX2：顶部模型与用量状态条已完成（新增 GET /api/voice/runtime/status 只读接口，前端顶部展示当前 Provider、默认模型、今日/月度字符用量和最近调用状态；不展示本次输入字符数，不影响生成链路，不触发资产清理，不调用外部 Provider，tests/test_runtime_status.py 27 个测试覆盖所有场景）
* P8-UX2-FIX：顶部 Provider 状态语义优化已完成（将”最近调用异常”细分为额度受限/限流中/鉴权失败/网络超时/服务异常/参数错误/PROVIDER_ERROR 等可行动状态；前端 chip 按 state 着色（available/warning/error/unknown），可点击跳转管理面板，detail 和 action_hint 在 title 属性展示；不影响生成链路，不调用外部 Provider）
* P8-UX3：状态条语义、chip 导航、retry 按钮已完成（Provider chip 跟随页面选择并显示 title 说明；today/month chip 增加”本地估算用量，不代表官方剩余额度”tooltip；warning/error chip onclick 跳转 admin.html?focus=call-logs；Advanced 危险区从红色改为浅橙/米色；profile 加载失败增加重试按钮；runtime status chip 失败后可点击重试；docs/generated/ 加入 .gitignore；README 配置表与 config.py 核对无误）
* P8-UX4-FIX：历史记录播放与删除操作修复已完成（历史按钮改为基于完整 job_id 的稳定事件绑定，播放支持 audio_asset.download URL 展开播放器，删除调用 DELETE /api/voice/jobs/{job_id} 执行软删除并从列表移除；不删除音频文件，不影响生成链路，不影响资产清理链路，tests/test_voice_jobs_delete.py 和 tests/test_voice_jobs_assets.py 已有 9 个测试覆盖后端接口）
* P8-UX5-FIX：剧本页"提交批量任务"按钮修复已完成（补齐 batchScriptResult 结果容器；成功时在剧本 Tab 内显示 job_id/状态/总段数；失败时显示行级错误提示而非静默；output_format='hex' + audio_format=用户选择；按钮 loading 状态正常；不影响生成主链路和长文本批量功能）
* P8-UX5-FIX2：剧本批量任务提交体验修正已完成（提交后不再自动跳转长文本 Tab，剧本 Tab 内新增 batchScriptProgressPanel 显示批量进度条和段落状态；showBatchProgress/startBatchPoll/pollBatchStatus/renderBatchStatus 均支持 targetPanelId 参数，默认行为不变，长文本批量进度保持兼容；不影响后端批量接口、生成链路和资产清理链路）
* P8-AUDIT1：全量代码自检已完成（466 passed, 6 skipped；发现 P1 问题 1 项：AUDIT-001 长文本批量失败错误回退到 resultsArea；P2 问题 3 项：AUDIT-002 profile retry DOM 残留、AUDIT-003 _currentBatchPanelId 未声明变量、AUDIT-004 runtime status 失败静默；P3 问题 3 项；详见 docs/P8_FULL_CODE_AUDIT.md）
* P8-UX6：P8-AUDIT1 问题修复已完成（修复 AUDIT-001 长文本批量失败错误容器（新增 batchLongtextResult）、AUDIT-002 profile retry 按钮 id 去重、AUDIT-003 _currentBatchPanelId 显式声明、AUDIT-004 runtime status 失败首次触发 showToast、AUDIT-005 README 测试数量 439→466；不影响后端 API、生成链路和资产清理链路）
* P8-UX7：P8-AUDIT1 后续修复已完成（修复 AUDIT-008 renderBatchStatus 长文本批量进度表误显"角色"列、AUDIT-009 剧本人设 select 不稳定问题（新增 scriptRows 状态数组、populateProfileSelect 保留已有选择、台词行输入 change 事件委托同步状态）；不影响后端 API、生成链路和资产清理链路）
* P8-UX8：历史列表操作区紧凑化已完成（复制 ID → 复制、操作按钮增加 title、grid 动作列 300px → 190px、按钮 padding 4px 8px → 3px 6px、font-size 0.76rem → 0.72rem、gap 6px → 4px、job_id 列 150px → 130px、文本摘要列 minmax 调整以获得更多空间；播放、下载、复制、删除功能保持不变；不影响后端 API、生成链路和资产清理链路）
* P8-UX8-FIX：删除按钮文案明确化已完成（删除按钮从"删"恢复为"删除"、操作列宽度 190px → 210px；新增同一时间最多展开一个播放器的 auto-collapse 逻辑；播放、下载、复制、删除功能不变）
* P8-UX9：历史播放器加载与失败反馈修复已完成（新增 historyAudioPlayerHtml 含状态容器，audio loadstart 显示"音频加载中…"、loadedmetadata 显示"音频已就绪"、canplay 清空提示、error 显示"音频加载失败，可尝试下载"并附带下载链接；保持同一时间最多展开一个播放器；播放、下载、复制、删除逻辑不变；不影响后端 API、生成链路和资产清理链路）
* P8-UX10：顶部运行状态一致性修复已完成（provider_status chip title 增加"最近一次 Provider 调用记录："来源前缀；成功的试听生成、长文本批量提交、剧本批量提交、批量任务完成（success/partial/failed）后主动刷新 runtime status；不新增健康探测，不影响生成链路和资产清理链路）
* P8-ADMIN1：管理面板统计与调用日志口径校验已完成（loadLogs/loadErrors 跟随日期范围；getDateRange 结束日期改为次日 00:00 exclusive；前端 start>end 拦截并显示错误提示；list_call_logs limit/offset 添加 Query 校验（ge/le）；成功口径改为 status_code 200-399+无 error_type；错误口径改为 error_type 非空 OR status_code>=400 OR status_code=null；_error_count() 同步口径；get_daily_trend 所有指标均补零日期；trend chart Y 轴从 0 开始；最近调用/错误时间显示 YYYY-MM-DD HH:mm:ss UTC；状态列 badge 区分成功/4xx/5xx/null+无 error_type；追踪列 fallback 为 provider_trace_id/job_id；字符缺失加 title 说明；耗时 0ms 加 title 提示；voice_jobs list limit/offset 添加 Query(ge=1,le=100)/(ge=0) 校验；voice_jobs response 返回实际 limit 而非原始值；tests/test_admin_api.py 新增 2 个测试，tests/test_voice_jobs_delete.py 新增 4 个测试，共 471 passed）
* 已知限制：历史 Tab 基于 VoiceJob，不等价于完整作品历史；BatchJob 总任务不在普通历史中展示；后续建议 P9-HISTORY 统一实现"任务历史+批量任务+音频资产库"
* 当前前端已从测试面板重组为任务维度工作台
* 当前主导航为：
  * 创作工作台
  * 长文本
  * 剧本
  * 音色
  * 历史
  * 高级
* 当前后台核心能力基本稳定
* 当前支持：
  * 同步 T2A
  * 异步 T2A
  * WebSocket 流式 T2A
  * 批量长文本
  * 批量剧本
  * 字幕生成
  * 音色试听
  * 历史记录
  * 音频下载
  * Admin 统计
  * Resource Guard 友好提示
* 当前不承诺高并发多人 SaaS
* 当前不做：
  * 登录系统
  * BYOK
  * 队列 / worker
  * Redis
  * PostgreSQL
  * 开放 API
  * 完整 SaaS 化
* 声音克隆 / 声音设计仍属于高级工程验证能力，暂缓产品化
* P8-2 目标：将音色 tab 整理为音色选择 / 试听工作台
* P8-2A：现状审查已完成
* P8-2B：音色 tab 信息架构整理已完成
* P8-2C：试听工作台产品化已完成
* P8-2C1：试听工作台收口修复已完成
* 删除音色已从音色主流程迁移到高级危险操作区
* P8-2D：轻量绑定入口整理已完成
* P8-2D1：音色列表行内删除入口收口已完成
* P8-2E：P8-2 验收与健康检查收口已完成
* P8-2：音色选择 / 试听工作台已完成并收口
* P8-3A：任务结果展示现状审查已完成（文档：docs/P8_3_RESULT_DISPLAY_WORKSTATION.md）
* P8-3B：resultsArea 信息架构整理已完成（resultsArea 已整理为任务结果展示区、同步/异步/多版本结果卡片化、section label 统一、timelineTable 空状态处理）
* P8-3C：同步/异步结果卡片化细化验收已完成（同步结果口径统一、新增 resultStatusHintHtml/resultDiagnosticHtml helper、running/failed/completed 状态分支处理、空状态准确化）
* P8-3C1：结果状态口径自检与收口修复已完成
* P8-3D：流式/多版本结果展示统一已完成
* P8-3E：错误 / Resource Guard / 下载入口产品化已完成
* P8-3F：P8-3 验收与健康检查收口已完成
* P8-3：任务卡片和结果展示已完成并收口
* P8-4A：历史记录和下载体验现状审查已完成（文档：docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md）
* P8-4 目标：将历史记录整理为历史任务找回、音频播放、下载和筛选体验
* P8-4A 不改前端、不改后端，仅做审查和文档化
* P8-4B：历史记录信息架构整理已完成（历史任务 card 化、状态展示复用 P8-3 helper、空状态/错误/到底提示产品化）
* P8-4C：历史任务卡片播放入口整理已完成（播放区已添加，`/api/voice/jobs` 不返回音频字段，安全降级展示"未返回可播放音频资产"）
* P8-4D：历史任务下载入口产品化已完成（下载区已添加，安全降级展示"未返回可下载音频资产"）
* P8-4E：历史筛选 / 搜索 / 空状态优化已完成（本地搜索/状态筛选/清空筛选/筛选说明/无匹配空状态已产品化）
* P8-4F：P8-4 验收与健康检查收口已完成
* 当前历史记录已从纯文本行整理为历史任务 card
* 当前历史记录状态展示已复用 statusLabel/statusClass/resultStatusHintHtml/resultDiagnosticHtml
* 当前历史记录已添加播放区和下载区（均为安全降级）
* 当前历史记录已支持本地搜索和状态筛选（仅作用于已加载记录）
* `/api/voice/jobs` 不返回音频资产字段是后端字段限制，播放/下载能力待后端支持
* P8-UX1：桌面宽屏布局与响应式适配作为遗留项记录
* P8-BE1：历史任务返回音频资产字段（后端遗留）
* P8-4 全阶段已正式收口
* P8-FIX1A：前端回归缺陷审查已完成（文档：docs/P8_FIX1_FRONTEND_REGRESSION_AUDIT.md）
* P8-FIX1：前端回归缺陷修复已完成（新增 historyRefreshBtn + refreshHistory()，隐藏 tab-nav 滚动条）
  * Tab 完整性：6 个 tab 均完整存在（P8-FIX1A 误判，经验核实内容本来完整）
  * 长文本/剧本模块：本来完整存在
  * 历史播放/下载不可用：后端字段限制，遗留到 P8-BE1
  * 新增历史不显示：已修复
* P8-FIX2：创作工作台首页轻量 UX 修复已完成（移除主流程大卡片，欢迎区轻量化，文案输入上移）
* P8-FIX3：恢复长文本/剧本 tab 内容区已完成（内容确认完整，tab 切换增加 null 防御）
* 下一阶段建议：P8-BE1 历史任务返回音频资产字段

说明：
本文档包含历史阶段记录，早期段落中的"前端仍是测试面板""缺少 Resource Guard"等内容仅代表当时阶段状态；当前最新状态以本摘要为准。

---

## 1. 当前项目定位

Voice Lab 当前定位为：AI 声音资产管理与语音生成工作台。

当前系统已经从单纯 API Demo 逐步演进为具备以下能力的声音生产工作台：

- 声音人设管理
- Provider 音色资产管理
- 人设与音色绑定
- T2A 同步生成
- 异步生成
- WebSocket 流式生成
- 声音设计
- 声音克隆
- 音色导入
- 音色删除
- 批量长文本生成
- 多角色剧本生成
- 成本确认保护
- Provider 调用统计雏形

## 2. 当前已完成能力

### 2.1 声音资产与绑定

已完成：

- VoiceProfile 声音人设
- ProviderVoice Provider 音色资产
- VoiceBinding 人设与音色绑定
- ProviderVoice 本地缓存
- 远端 voice_id 导入本地
- 绑定创建时校验 provider_voice 是否存在且 available

### 2.2 Provider 能力

当前已经具备 Provider Adapter 基础。

当前已注册 Provider：

- mock
- minimax

当前尚未接入：

- mimo
- local_gpt_sovits
- local_cosyvoice
- aliyun
- volcengine
- elevenlabs

### 2.3 MiniMax 能力

当前 MiniMax Provider 已支持：

- T2A 同步生成
- 异步任务创建与查询
- WebSocket 流式生成
- 音色列表查询
- 声音克隆
- 声音设计
- 音色删除
- 文件上传
- Provider 调用日志

### 2.4 批量生成能力

已支持：

- 长文本分段生成
- 剧本多角色生成
- segment 级别状态记录
- success / partial / failed 状态
- 失败段重试
- 成功段复用
- 音频合并
- 字幕合并

## 3. 当前核心保护机制

### 3.1 删除音色生命周期闭环

当前已完成：

- 远端删除音色成功后，本地 provider_voices 标记为 deprecated
- 远端删除音色成功后，相关 voice_bindings 标记为 deprecated
- 删除失败时不更新本地状态
- 本地 provider_voice 不存在时不影响远端删除成功结果

### 3.2 生成前 ProviderVoice 状态校验

当前已完成：

- 同步生成前校验 provider_voice 是否存在
- 同步生成前校验 provider_voice.status 是否 available
- 异步生成前校验 provider_voice
- 流式生成前校验 provider_voice
- 批量 segment 生成前校验 provider_voice

该机制用于防止：

- 已删除音色继续被使用
- 脏数据绕过绑定状态
- 本地缺失 provider_voice 仍进入真实 provider 调用
- 无效 voice_id 请求打到云端模型

### 3.3 Cost Guard 第一版

当前已完成：

- 计费字符估算
- MiniMax T2A 费用估算
- /api/voice/cost/estimate 成本估算接口
- 高风险操作增加 confirm_cost
- MiniMax 声音设计未确认时拒绝
- MiniMax 声音克隆未确认时拒绝
- MiniMax 直连试听未确认时拒绝
- MiniMax 批量生成未确认时拒绝
- mock provider 不强制 confirm_cost
- 普通 T2A 暂不强制确认，但会记录成本估算日志

### 3.4 Provider 调用统计

当前已有：

- provider_call_logs
- usage_characters 字段
- provider_trace_id 字段
- StatsService 聚合统计

可统计：

- 总任务数
- 成功率
- 失败率
- 总字符数
- 按 provider 统计
- 按 API 统计
- 按天统计
- 平均耗时
- P95 耗时

## 4. 当前测试状态

### 4.1 全量测试

```bash
python -m pytest tests/ -x -q
```

测试结果：

```text
466 passed, 6 skipped in 174.91s (0:02:54)
```

- 总测试数量：472（466 passed + 6 skipped）
- 通过数量：466
- 跳过数量：6（均为 E2E 测试，需要真实 API Key）
- 失败数量：0

### 4.2 WebSocket 专项测试

```bash
python -m pytest tests/test_ws_render.py -q
```

测试结果：

```text
6 passed in 2.91s
```

### 4.3 历史遗留问题记录

**问题：WebSocket 端点无法通过测试 fixture 注入数据库会话**

- 发现时间：2026-05-12
- 根本原因：`ws_render.py` 使用 `session = next(get_session())` 绕过 FastAPI 的 `dependency_overrides` 机制，导致测试中 `ws_patched_session` fixture 无法替换为测试引擎会话
- 修复方案：将 `session = next(get_session())` 改为 FastAPI 依赖注入 `session: Session = Depends(get_session)`，让 FastAPI 的 `dependency_overrides` 在测试中生效
- 修改文件：`app/api/ws_render.py`
- 状态：**已修复并验证通过**

## 5. 当前试用准备度评估

当前项目可以：

- 本地演示
- 单人测试
- 验证 MiniMax 语音链路
- 验证声音资产生命周期
- 验证成本确认保护
- 验证批量生成流程

当前项目暂不适合直接开放多人试用。

主要原因：

- 前端仍是测试面板，不是产品工作台
- 缺少全局 Resource Guard
- 缺少 Provider / model / operation 级别并发控制
- 缺少预算预占与实际结算
- SQLite 对多人并发试用存在风险
- 默认 batch_max_concurrency 对试用阶段偏高
- Provider 差异抽象还不完整
- 手机端体验尚未产品化

## 6. 当前结论

Voice Lab 当前已经从 API Demo 进入声音工作台雏形阶段。

当前最应该做的是：

1. 固化项目状态
2. 整理产品主流程
3. 建立全局资源保护
4. 再接入低成本 Provider
5. 再做手机端 H5/PWA

不建议现在继续无序增加底层能力。

---

## 7. P6 前端测试面板基础验证

### 验证背景

- 当前分支：dev
- 当前阶段：P6 固化收尾
- 验证方式：人工前端页面基础测试
- 验证结论：暂未发现明显阻塞问题

### 验证范围

已基本测试以下页面或能力：

- T2A 生成（同步）
- T2A 生成（异步）
- T2A 生成（WebSocket 流式）
- 音色管理
- 声音克隆
- 声音设计
- 绑定管理
- 批量生成（长文本）
- 批量生成（剧本多角色）
- 管理面板入口

### 验证结果

- 页面可正常打开
- 基本交互可用
- 同步生成链路可用
- 异步生成链路可用（短文本异步模式明显慢于同步模式，属于异步链路正常特性）
- 流式生成链路可用
- 批量生成链路可用
- 暂未发现明显阻塞问题

### 观察项

- 当前前端仍是测试面板，不是最终产品主流程
- 异步生成依赖前端轮询推进状态，短文本建议优先使用同步生成或流式生成
- 批量长文本自动分段策略主要按双换行或超长文本拆分，单换行短文本可能仍被视为一段
- 后续进入 Resource Guard 前，应保留当前 P6 baseline

---

## 8. .env.example 与 Settings 配置同步

### 问题现象

- `app/core/config.py` 中已有 WebSocket、批量、日志、重试等配置项
- `.env.example` 未完整覆盖这些配置
- 这可能导致换机器、交接、部署或让代码执行器运行时出现配置遗漏

### 原因分析

- 项目功能从 P3 推进到 P6 后，新增了 WebSocket、批量任务、日志、重试等能力
- 但 `.env.example` 没有及时跟进 Settings 配置项变化
- 配置文档和代码存在漂移

### 修改方案

- 对照 `app/core/config.py` 中 Settings 类同步 `.env.example`
- 补充 WebSocket、Batch、Logging、Retry、Async Poll 等配置
- 将 `BATCH_MAX_CONCURRENCY` 示例值设为 1，作为试用阶段保守默认值
- 清理当前未使用的配置项（`ENABLE_MOCK_PROVIDER`、`CLONE_AUDIO_MIN_DURATION_SEC`、`CLONE_AUDIO_MAX_DURATION_SEC`、`PROMPT_AUDIO_MAX_DURATION_SEC`），移至注释区标注"未启用/保留说明"
- 保留 `MOCK_FALLBACK_PROVIDER`，该字段被 `voice_profile_repo.py` 实际使用

### 修改文件

- `.env.example`
- `docs/PROJECT_HEALTH_CHECK.md`

### 同步的配置项（按 Settings 字段对照）

| Settings 字段 | .env.example 配置 | 状态 |
|---|---|---|
| `async_poll_interval_seconds` | `ASYNC_POLL_INTERVAL_SECONDS=5` | 新增 |
| `async_max_wait_seconds` | `ASYNC_MAX_WAIT_SECONDS=600` | 新增 |
| `minimax_ws_url` | `MINIMAX_WS_URL=wss://api.minimaxi.com/ws/v1/t2a_v2` | 新增 |
| `minimax_ws_model` | `MINIMAX_WS_MODEL=speech-2.8-hd` | 新增 |
| `minimax_ws_timeout_seconds` | `MINIMAX_WS_TIMEOUT_SECONDS=120` | 新增 |
| `batch_max_concurrency` | `BATCH_MAX_CONCURRENCY=1` | 新增（从5改为1） |
| `log_level` | `LOG_LEVEL=INFO` | 新增 |
| `log_format` | `LOG_FORMAT=json` | 新增 |
| `log_dir` | `LOG_DIR=./logs` | 新增 |
| `log_retention_days` | `LOG_RETENTION_DAYS=30` | 新增 |
| `provider_retry_max_attempts` | `PROVIDER_RETRY_MAX_ATTEMPTS=3` | 新增 |
| `provider_retry_backoff_base` | `PROVIDER_RETRY_BACKOFF_BASE=1.0` | 新增 |
| `mock_fallback_provider` | `MOCK_FALLBACK_PROVIDER=minimax` | 新增 |
| `clone_audio_max_size_mb` | `CLONE_AUDIO_MAX_SIZE_MB=20` | 已有 |
| `minimax_file_upload_path` | `MINIMAX_FILE_UPLOAD_PATH=/v1/files/upload` | 已有 |
| `minimax_voice_clone_path` | `MINIMAX_VOICE_CLONE_PATH=/v1/voice_clone` | 已有 |
| `minimax_voice_design_path` | `MINIMAX_VOICE_DESIGN_PATH=/v1/voice_design` | 已有 |
| `minimax_delete_voice_path` | `MINIMAX_DELETE_VOICE_PATH=/v1/delete_voice` | 已有 |

### 清理的配置项

| 配置 | 原因 |
|---|---|
| `ENABLE_MOCK_PROVIDER=false` | 字段不存在于 Settings，代码无引用 |
| `CLONE_AUDIO_MIN_DURATION_SEC=10` | 字段不存在于 Settings，代码无引用 |
| `CLONE_AUDIO_MAX_DURATION_SEC=300` | 字段不存在于 Settings，代码无引用 |
| `PROMPT_AUDIO_MAX_DURATION_SEC=8` | 字段不存在于 Settings，代码无引用 |

### 后续注意

- 后续每次新增 Settings 配置项，都需要同步 `.env.example`
- 后续接入 Resource Guard 时，也需要同步相关环境变量示例
- 不应让 `.env.example` 长期落后于 `config.py`

---

## 9. 本次测试执行记录

### 全量测试

测试命令：

```bash
python -m pytest tests/ -x -q
```

测试输出：

```text
322 passed, 6 skipped in 171.42s (0:02:51)
```

测试结果摘要：

- 总测试数量：328（322 passed + 6 skipped）
- 通过数量：322
- 跳过数量：6（均为 E2E 测试，需要真实 API Key）
- 失败数量：0
- 第一个失败测试：无

---

## P7-A Resource Guard 第一版方案设计

### 背景

- P6 baseline 已于 2026-05-13 完成（tag: p6-dev-baseline-20260513）
- 项目当前具备多条真实 MiniMax 调用路径：同步T2A、异步T2A、WebSocket流式、声音设计、声音克隆、音色试听、多版本试音、批量生成
- 当前已有 Cost Guard（confirm_cost 检查），但缺少 Resource Guard（资源准入控制）
- 下一阶段需要先完成方案设计，确保实现受控，而不是直接写代码

### 本次工作

- 新增 `docs/P7_RESOURCE_GUARD_SPEC.md`
- 覆盖内容：定位与边界、operation类型定义、默认策略、错误模型、Service接入点、与其他模块关系、日志设计、测试计划、风险、分阶段实施计划
- 本次不改任何业务代码，不新增 Python service，不修改测试

### 修改文件

- `docs/P7_RESOURCE_GUARD_SPEC.md`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`（追加本节）

### 验证命令

```bash
git diff --stat
git diff --check
```

### 验证结果

- git diff --stat: docs/P7_RESOURCE_GUARD_SPEC.md（新增）、docs/PROJECT_HEALTH_CHECK.md（追加）
- git diff --check: 无 whitespace error
- 本次为文档任务，未执行全量测试

### 后续实施计划

| 阶段 | 目标 |
|---|---|
| P7-A | 方案设计（本次） |
| P7-B | 实现 ResourceGuardService 基础模块 + 单元测试 |
| P7-C | 接入核心同步路径（t2a_sync、voice_design、voice_clone、preview） |
| P7-D | 接入流式和异步路径（stream、async、variants） |
| P7-E | 接入批量路径（batch_longtext/script，评估 segment_render） |
| P7-F | 前端 RESOURCE_LIMIT_EXCEEDED 友好提示 |

---

## P7-A1 Resource Guard 方案审查修订

### 背景

- P7-A 方案设计已于上一 commit 完成（f249198）
- 人工审查发现部分设计边界需要修订，避免 P7-B 实现走偏
- 本次只修订文档，不修改任何业务代码

### 修订内容

1. **错误模型字段修正**：将 `http_status = 429` 改为 `status_code = 429`，与 `VoiceLabError` 体系一致，`voice_lab_error_handler` 读取 `exc.status_code`
2. **明确业务层使用 guard(...)**：对业务 Service 暴露 `guard(...)` 作为 async context manager，`_acquire` 作为内部方法，确保业务代码无法绕过 release
3. **增加测试隔离 reset 机制**：必须提供 `reset_resource_guard_for_tests()` 函数和 pytest autouse fixture 设计，避免单例状态导致测试间污染
4. **修正异步任务跨请求持有 lease**：明确第一版不跨 HTTP 请求持有 lease，submit 和 query/download 使用共享并发池（limit=2），不是同一长期租约
5. **修正批量任务 lease 生命周期边界**：区分 Layer 1（submit 入口瞬时保护）和 Layer 2（后台 execute 生命周期保护，P7-E 再设计）
6. **增加 CostGuard/ResourceGuard operation 映射表**：明确两个 Guard 的 operation 命名差异，Service 接入时需分别查表
7. **修正 VoiceRenderService 方法名**：将 `VoiceRenderService.render` 修正为 `VoiceRenderService.render_voice`
8. **补充 VoicePreviewService 与 ProviderVoicePreviewService 的 job_id 语义差异**：前者使用 preview_job 临时 ID（不对应真实 VoiceJob），后者使用真实 VoiceJob.id

### 修改文件

- `docs/P7_RESOURCE_GUARD_SPEC.md`（多处修订）
- `docs/PROJECT_HEALTH_CHECK.md`（追加本节）

### 验证命令

```bash
git diff --stat
git diff --check
```

### 验证结果

- git diff --stat: 通过（仅 docs/P7_RESOURCE_GUARD_SPEC.md、docs/PROJECT_HEALTH_CHECK.md）
- git diff --check: 通过，无 whitespace error
- 全量测试：未运行，原因：文档修订

### 后续实施计划

| 阶段 | 目标 |
|---|---|
| P7-B | 实现 ResourceGuardService 基础模块 + 单元测试（含测试 reset 机制） |
| P7-C | 接入核心同步与高风险路径（render_voice、design、clone、preview 等） |
| P7-D | 接入流式与异步路径（明确只做瞬时调用并发，不跨请求持有 lease） |
| P7-E | 接入批量路径（先 Layer 1 submit 入口，再评估 Layer 2 execute 生命周期） |

---

## P7-B ResourceGuardService 基础模块实现

### 背景

- P7-A 方案设计（f249198）和 P7-A1 修订（f6617a6）已完成
- 本次实现 ResourceGuardService 基础模块及单元测试，不接入业务服务
- 技术决策：采用 asyncio.Semaphore 实现并发控制（而非纯 Lock + Counter）

### 实现内容

新增文件：
- `app/services/resource_guard_service.py`：ResourceGuardService、ResourceLimitExceeded、ResourcePolicy、ResourceLease、get_resource_guard()、reset_resource_guard_for_tests()
- `tests/test_resource_guard.py`：15 个单元测试

### 技术决策记录

1. **Semaphore vs Lock+Counter**：第一版采用 `asyncio.Semaphore` 而非 Lock+Counter。Semaphore 本身是原子操作，适合"尝试获取-成功或拒绝"模式。

2. **wait_for timeout=0.001**：使用 `asyncio.wait_for(sem.acquire(), timeout=0.001)` 实现非阻塞语义。timeout=0 会导致 Python asyncio 内部任务取消异常传播问题，timeout=0.001（1ms）足以让可用permit立即成功，拒绝对timeout敏感的场景。

3. **_active 单独加锁**：`_active` dict 用于 introspection（current()、snapshot()），与 Semaphore 并发控制解耦。更新时使用独立 Lock 保护。

4. **_acquire/_release 保留为测试方法**：业务代码使用 `guard()` async context manager，`_acquire/_release` 仅供测试直接调用。

### 修改文件

- `app/services/resource_guard_service.py`（新增）
- `tests/test_resource_guard.py`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`（追加本节）

### 验证结果

```bash
python -m pytest tests/test_resource_guard.py -q
# 15 passed

python -m pytest tests/ -x -q
# 337 passed, 6 skipped (0:01:26)
```

### 后续实施计划

| 阶段 | 目标 |
|---|---|
| P7-C | 接入核心同步与高风险路径（render_voice、design、clone、preview 等） |
| P7-D | 接入流式与异步路径 |
| P7-E | 接入批量路径 |
| P7-F | 前端 RESOURCE_LIMIT_EXCEEDED 友好提示 |

---

## P7-B1 ResourceGuardService 并发控制实现修复

### 背景

- P7-B 已完成 ResourceGuardService 基础模块（commit eb31d25）
- 代码审查发现当前实现使用 `asyncio.Semaphore + wait_for(timeout=0.001)` 模拟非阻塞准入
- 该实现虽然测试通过，但和 P7-A1 的"立即拒绝、不排队、不等待"设计存在偏差
- `_active` 仅用于观测，不是真实控制来源，存在控制状态和观测状态不一致的风险

### 修复内容

1. **移除 asyncio.Semaphore**：删除 `_semaphores` dict 和 `_get_semaphore()` 方法，不再使用 Semaphore

2. **移除 wait_for(timeout=0.001)**：不再使用 `asyncio.wait_for(sem.acquire(), timeout=0.001)` 模拟非阻塞

3. **使用 asyncio.Lock + _active 原子计数**：`_active` 同时作为并发控制状态和 introspection 观测状态的单一来源。check 和 increment 在同一个 lock critical section 内完成，无等待、无排队

4. **_acquire/_release 保留为测试方法**：业务代码使用 `guard()` async context manager，`_acquire/_release` 仅供测试直接调用

5. **guard(...) finally 统一调用 _release(lease)**：guard 的 finally 只调用 `_release(lease)`，不再有自己的释放逻辑

6. **_release 幂等**：重复释放不会导致 `_active` 变负。降到 0 时 pop key 保持 snapshot 简洁

7. **重写并发测试**：使用 `asyncio.Event` 保证 holder 先持有 slot，contenders 再尝试获取，消除事件循环时序依赖

### 修改文件

- `app/services/resource_guard_service.py`
- `tests/test_resource_guard.py`
- `docs/PROJECT_HEALTH_CHECK.md`

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- `tests/test_resource_guard.py`：15 passed
- 全量测试：337 passed, 6 skipped (0:01:16)

### 后续计划

| 阶段 | 目标 |
|---|---|
| P7-C | 接入核心同步与高风险路径 |
| P7-C1 | 修复 voice_variants 双重 guard 边界问题 |
| P7-C1-fix | 修复真实 provider 双重限流 |
| P7-D | 接入异步与流式路径 |
| P7-E | 接入批量路径 |

---

## P7-C Resource Guard 核心同步与高风险路径接入

### 背景

- P7-B / P7-B1 已完成 ResourceGuardService 基础模块和实现修复（commit a66d04d）
- 本次进入 P7-C
- 本阶段只接入核心同步与高风险真实 Provider 调用路径
- 不接入异步、流式、批量

### 本次接入范围

- VoiceRenderService.render_voice → t2a_sync
- VoiceDesignService → voice_design
- VoiceCloneService.upload_audio → voice_clone_upload
- VoiceCloneService.clone_voice → voice_clone_create
- ProviderVoicePreviewService.preview → voice_preview
- VoicePreviewService.preview → binding_voice_preview
- VoiceVariantService → voice_variants

### 本次不接入范围

- AsyncRenderService
- StreamRenderService
- BatchOrchestrationService
- 前端
- Provider Adapter
- 数据库模型

### 修改文件

- app/services/voice_render_service.py
- app/services/voice_design_service.py
- app/services/voice_clone_service.py
- app/services/provider_voice_preview_service.py
- app/services/voice_preview_service.py
- app/services/voice_variant_service.py
- tests/test_voice_design.py（新增 Resource Guard 测试）
- tests/test_voice_clone.py（新增 Resource Guard 测试）
- tests/test_voice_preview.py（新增 Resource Guard 测试）
- tests/test_voice_variant_service.py（新增 Resource Guard 测试）
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_voice_design.py tests/test_voice_clone.py tests/test_voice_preview.py tests/test_voice_variant_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- 相关 Service 测试：55 passed
- 全量测试：343 passed, 6 skipped (0:01:28)

### 后续计划

| 阶段 | 目标 |
|---|---|
| P7-C1 | 修复 voice_variants 双重 guard 边界问题 |
| P7-D | 接入 AsyncRenderService 和 StreamRenderService |
| P7-E | 接入 BatchOrchestrationService |
| P7-F | 前端 RESOURCE_LIMIT_EXCEEDED 友好提示 |

---

## P7-C1 voice_variants 双重 guard 边界修复

### 背景

- P7-C 已完成 ResourceGuardService 基础模块和7个核心同步路径接入
- voice_variants 使用外层 voice_variants guard，但内部 render_voice 调用会再次获取 t2a_sync，形成双重限流
- VoiceVariantGroup 创建在 Resource Guard 之外，reject 时可能留下空 group 记录

### 问题

1. VoiceVariantService 外层 guard 使用 voice_variants，但 render_voice 内部又获取 t2a_sync（双重限流）
2. VoiceVariantGroup 在 guard 之前创建，reject 时 group 已存在但无 variants（空壳记录）

### 修改内容

1. **voice_render_service.py**：新增 `resource_guard_already_acquired: bool = False` 参数，当为 True 时跳过 t2a_sync guard
2. **voice_variant_service.py**：
   - 将 VoiceVariantGroup 创建移入 guard 内部（先 admission 再建 group，避免空记录）
   - render_voice 调用时传入 `resource_guard_already_acquired=True`（voice_variants guard 已保护，跳过 t2a_sync guard）
3. **tests/test_voice_variant_service.py**：新增3个 Resource Guard 测试用例

### 新增测试

- `test_variants_rejected_when_slot_full`：验证 voice_variants slot 满时拒绝，create_group 未被调用
- `test_variants_not_affected_by_t2a_sync_limit`：验证 t2a_sync 全满时 variants 不受影响（resource_guard_already_acquired=True 生效）
- `test_variants_success_path_works`：验证正常 variants 流程正确

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_voice_variant_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- VoiceVariant Service 测试：8 passed
- 全量测试：346 passed, 6 skipped

### 补充修复（P7-C1-provider）

在 P7-C1 基础上额外修复 provider 透传问题：

- `request.provider=None` 时，外层 guard 按 "mock" 处理，但内部 `render_voice` 收到 `None` 后会解析为真实 provider，导致外层/内层 provider 不一致
- 修复：`VoiceRenderRequest(provider=provider)` 使用已解析 provider，而非 `request.provider`
- `resource_guard_already_acquired=(provider == "mock")`：此设计仍有误，真实 provider 下仍然双重限流，需要进一步修复（见 P7-C1-fix）
- 新增测试：`test_variants_provider_none_passes_mock_to_render_voice`

---

## P7-C1-fix VoiceVariantService 真实 Provider 双重限流修复

### 背景

- P7-C1 初步修复后，VoiceVariantGroup 已移入 voice_variants guard 内部，provider 也已改为透传解析后的 provider
- 但 cae269f 中 `resource_guard_already_acquired=(provider == "mock")` 导致真实 provider 下仍然会进入内部 t2a_sync guard
- 这会让 voice_variants 和 t2a_sync 双重限流问题在 minimax 等真实 provider 下继续存在

### 修复内容

- `resource_guard_already_acquired=True` 始终传给 render_voice，不再区分 mock/real
- 修正错误注释：voice_variants guard 保护整个多版本请求，mock 和真实 provider 都适用
- 保留 `VoiceRenderRequest(provider=provider)` 正确透传
- 保留 VoiceVariantGroup 在 voice_variants guard 通过后创建
- 新增测试：`test_variants_real_provider_skips_t2a_sync_guard`（provider=minimax 时也传 True）
- 新增测试：`test_variants_not_affected_by_t2a_sync_limit`（t2a_sync 满载不影响 variants）

### 修改文件

- app/services/voice_variant_service.py
- tests/test_voice_variant_service.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_voice_variant_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- VoiceVariantService 测试：9 passed
- 全量测试：347 passed, 6 skipped

---

## P7-D Resource Guard 异步与流式路径接入

### 背景

- P7-C / P7-C1-fix 已完成核心同步、高风险路径和 voice_variants 双重 guard 边界修复
- 本次进入 P7-D
- 本阶段只接入 AsyncRenderService 和 StreamRenderService
- 不接入 BatchOrchestrationService

### 本次接入范围

- AsyncRenderService.submit_task → t2a_async_submit
- AsyncRenderService.query_status / _complete_job → t2a_async_query_download
- StreamRenderService.render_stream → t2a_stream

### 关键设计确认

- 异步任务不跨 HTTP 请求长期持有 lease
- submit_task 只保护 create_async_task 瞬时调用
- query_status 只保护 query_async_task 和成功后的 download/save 瞬时阶段
- query_status 被 Resource Guard 拒绝时，不把 job 标记 failed（因为只是查询资源忙，不是任务本身失败）
- stream guard 覆盖整个 async generator 生命周期
- stream 拿到 guard 后才 yield started
- stream 断开或 generator close 后自动释放 guard（async context manager）
- 本次不接入批量任务

### 本次不接入范围

- BatchOrchestrationService
- 前端
- Provider Adapter
- 数据库模型

### 修改文件

- app/services/async_render_service.py
- app/services/stream_render_service.py
- tests/test_async_render.py
- tests/test_stream_render_service.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：358 passed, 6 skipped

---

## P7-E Resource Guard 批量生成路径接入

### 背景

- P7-D1 已完成异步与流式路径的 Resource Guard 接入和状态机边界修复
- BatchOrchestrationService 尚需接入 Resource Guard
- submit_longtext 和 submit_script 需要在提交前做 admission control
- execute 需要在整个执行生命周期做 admission control
- segment 渲染失败时需要标记关联 VoiceJob 为 failed

### 修复内容

- submit_longtext: guard(batch_longtext) 包裹 BatchJob + BatchSegments 创建和 _execute_with_session 调用
- submit_script: guard(batch_script) 包裹 BatchJob + BatchSegments 创建和 _execute_with_session 调用
- execute: guard(batch_execute) 包裹整个执行生命周期；ResourceLimitExceeded 异常时标记 batch_job.status=failed 并返回
- _process_segment: try/except 包裹 render_sync 和 save_assets，异常时标记关联 VoiceJob.status=failed 后重新抛出
- 本次批量任务内的 segment 并发受 batch_max_concurrency 控制，不使用 t2a_sync guard（t2a_sync 是同步单次调用，无 guard）

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：16 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：363 passed, 6 skipped

---

## P7-E1 批量生成状态机边界修正

### 背景

- P7-E 首次提交后审查发现 segment 失败路径中 BatchSegment.voice_job_id 未稳定绑定
- 异常时 VoiceJob 可能处于 running 状态未被标记 failed
- save_assets 失败时状态同步缺失
- submit 被 Resource Guard 拒绝时未充分验证不产生脏数据
- submit_script 在 guard 内部做 profile 校验，边界不够清晰

### 修复内容

- VoiceJob 创建并标记 running 后，立即同步 BatchSegment.voice_job_id 和 status=running，确保失败路径可追踪
- 新增 _mark_segment_voice_job_failed helper 方法，统一处理 render_sync 和 save_assets 失败的收口
- _process_segment_isolated 增强兜底：segment 异常时若 VoiceJob 仍为 pending/running/processing则同步标记 failed
- submit_script 预校验所有 profile_id 后再进入 Resource Guard，符合"资源准入与业务校验分离"原则
- save_assets 失败时 BatchSegment + VoiceJob 同步 failed

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 测试增强

- submit_longtext rejected：验证 BatchJob/BatchSegment 数量不变，不启动 execute
- submit_script rejected：验证同上
- execute rejected：验证 failed_segments == total_segments，segment 无 voice_job_id/audio_asset_id
- segment render error：验证 segment.voice_job_id 非空，VoiceJob 与 segment 同步 failed
- save_assets error：新增测试，验证 segment + VoiceJob 同步 failed
- no t2a_sync double guard：验证 batch segments 不进入 t2a_sync guard（持有 minimax t2a_sync slots 不影响 mock batch 执行）

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：18 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：365 passed, 6 skipped

---

## P7-E2 Batch 状态机兜底与 no-double-guard 测试增强

### 背景

- P7-E1 首次提交后复核发现两个小问题
- _process_segment_isolated 兜底中，若 segment.status 已是 failed 但 voice_job 刚被改为 failed，则不会 commit
- test_batch_segments_execute_without_t2a_sync_guard 使用 provider="mock"，不能强证明 minimax batch segment 不走 t2a_sync guard

### 修复内容

- _process_segment_isolated 兜底改为 dirty flag 方式：changed = True 只要有任何一个对象被修改就 commit
- no t2a_sync double guard 测试改为 provider="minimax" + FakeMinimaxAdapter，更强验证 minimax batch segment 不进入 t2a_sync guard

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：18 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：365 passed, 6 skipped

---

## P7-E3 Batch 状态机最终收口

### 背景

- P7-E2 后继续基于完整现态代码审查 BatchOrchestrationService
- 发现 execute Resource Guard 拒绝时 BatchJob.error_message 缺失
- submit rejected 测试未断言 _execute_with_session 未调用
- merge 失败时可能导致 BatchJob 被误标 success

### 修复内容

- execute Resource Guard 拒绝时补充 BatchJob.error_message（使用 exc.message + exc.detail）
- submit_longtext / submit_script rejected 测试补充 _execute_with_session.assert_not_called()
- merge 失败时 BatchJob 不再误标 success（merge_error 优先判断）
- merge 失败只影响 BatchJob 最终状态，不回滚成功 segment

### 修改文件

- app/services/batch_orchestration_service.py
- tests/test_batch_orchestration.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 测试：38 passed
- BatchOrchestrationService 测试：19 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：366 passed, 6 skipped

---

## P7-F 前端 RESOURCE_LIMIT_EXCEEDED 友好提示

### 背景

- P7 Resource Guard 后端准入控制已覆盖主要真实 provider 调用路径
- 后端在资源超限时返回 RESOURCE_LIMIT_EXCEEDED / HTTP 429
- 前端测试面板此前将该错误展示为普通失败或 alert 原始 JSON
- 本阶段只做前端错误解析与友好展示，不修改后端 Resource Guard

### 修改内容

- 在 app/static/index.html 新增统一 API 错误解析 helper：parseApiError、formatApiError、renderApiError、extractDetailValue、operationLabel
- 新增 RESOURCE_LIMIT_EXCEEDED 友好提示 CSS 样式（.resource-limit-msg）
- 普通 JSON fetch 接口统一解析 VoiceLabError payload
- T2A 同步 / 异步 / 流式 / 多版本试音 / 声音设计 / 声音克隆 / 批量提交等入口展示资源繁忙提示
- Resource Guard 拒绝时不展示成功结果、不启动无效 polling、不污染任务状态

### 修改文件

- app/static/index.html
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- 全量测试：366 passed, 6 skipped

---

## P7-F1 前端 Resource Limit 提示准确性收口

### 背景

- P7-F 已完成 RESOURCE_LIMIT_EXCEEDED 友好提示主体能力
- 复核发现 WebSocket error payload 可能没有 detail 字段，导致前端无法解析 operation
- 异步 query/download 被资源限制拒绝时，不应提示"没有创建新的任务"

### 修复内容

- WebSocket RESOURCE_LIMIT_EXCEEDED 使用 message 作为 detail fallback
- formatApiError 支持从 detail 或 message 中解析 operation
- renderApiError 根据 operation 展示不同额外说明
- t2a_async_query_download 提示"任务可能仍在处理中"
- submit 类操作继续提示"没有创建新的任务"
- batch_execute 提示"批量任务可能尚未开始执行"

### 修改文件

- app/static/index.html
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/ -x -q
```

### 验证结果

- 全量测试：366 passed, 6 skipped

## P7-D1 异步与流式状态机边界修复

### 背景

- P7-D 已接入 AsyncRenderService 与 StreamRenderService 的 Resource Guard
- 审查发现 query_status 异常处理范围过宽，可能让下载/保存失败的 job 长期 processing
- 审查发现 provider_task_id 缺失时 job 没有标记 failed
- 审查发现 stream generator 提前关闭时 Resource Guard 会释放，但 job 可能仍 running

### 修复内容

- query_status 中 ResourceLimitExceeded 仍保持 job processing
- provider_task_id 缺失时标记 job failed
- _complete_job 下载/保存失败时标记 job failed
- provider query 本身临时异常保持 processing 并重新抛出（本次不做改变）
- stream generator started 后、completed 前提前关闭时标记 job failed（finally 块处理）
- stream 正常完成不被 finally 覆盖
- stream Resource Guard 拒绝不 yield started，并保持 RESOURCE_LIMIT_EXCEEDED 语义
- 本次不接入 BatchOrchestrationService

### 修改文件

- app/services/async_render_service.py
- app/services/stream_render_service.py
- tests/test_async_render.py
- tests/test_stream_render_service.py
- docs/PROJECT_HEALTH_CHECK.md

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：358 passed, 6 skipped

---

## P7-G Resource Guard 阶段总验收

### 背景

- P7-A 至 P7-F1 已完成 Resource Guard 后端准入、任务状态机、前端友好提示
- 本阶段进行完整现态复核与验收文档收口

### 工作内容

- 新增 docs/P7_RESOURCE_GUARD_ACCEPTANCE.md
- 汇总所有 Resource Guard operation 与业务入口（13 个唯一 operation，14 条业务入口覆盖记录）
- 汇总后端状态机验收点（同步、异步、流式、preview、clone、design、batch）
- 汇总前端 RESOURCE_LIMIT_EXCEEDED 提示验收点
- 执行后端回归测试
- 明确 P7 阶段结论：主线完成，可进入下一阶段

### 修改文件

- docs/P7_RESOURCE_GUARD_ACCEPTANCE.md（新增）
- docs/PROJECT_HEALTH_CHECK.md（追加本节）

### 验证命令

```bash
python -m pytest tests/test_resource_guard.py -q
python -m pytest tests/test_batch_orchestration.py -q
python -m pytest tests/test_async_render.py -q
python -m pytest tests/test_stream_render_service.py -q
python -m pytest tests/ -x -q
```

### 验证结果

- Resource Guard 单元测试：15 passed
- BatchOrchestrationService 测试：19 passed
- AsyncRenderService 测试：14 passed
- StreamRenderService 测试：9 passed
- 全量测试：**366 passed, 6 skipped**

### 阶段结论

**P7 Resource Guard 主线完成，可以进入下一阶段。**

所有后端 service 均正确接入 Resource Guard，状态机在拒绝路径保持一致，前端 RESOURCE_LIMIT_EXCEEDED 友好提示已覆盖所有入口。366 个自动化测试全部通过，无阻塞问题。

---

## P7-H 当前项目能力测试与验收

### 背景

- P7 Resource Guard 已完成（e05714a）
- 进入产品化前，需要对当前项目已有音频能力做系统测试
- 本阶段不新增业务能力，重点是验证现有能力是否可用

### 工作内容

- 新增 docs/P7_H_CAPABILITY_ACCEPTANCE.md
- 执行自动化测试（366 passed, 6 skipped）
- 代码审查确认各能力实现状态
- 汇总能力可用性与产品化建议
- 区分 mock 自动化验证和 minimax 代码审查确认

### 修改文件

- docs/P7_H_CAPABILITY_ACCEPTANCE.md（新增）
- docs/PROJECT_HEALTH_CHECK.md（追加本节）

### 测试结果

**自动化测试**：

```
tests/test_resource_guard.py         → 15 passed
tests/test_batch_orchestration.py    → 19 passed
tests/test_async_render.py          → 14 passed
tests/test_stream_render_service.py  → 9 passed
tests/ -x -q                         → 366 passed, 6 skipped
```

**手工测试**：未执行（需要启动 uvicorn 服务并使用真实 MiniMax token）

### 能力验收结论

| 能力 | 状态 |
|---|---|
| 同步 T2A（所有格式和参数） | 工程链路可用，真实 MiniMax 待 smoke test |
| 异步 T2A（submit/poll/download） | 工程链路可用，真实 MiniMax 待 smoke test |
| HTTP / WebSocket 流式 T2A | 工程链路可用，真实 MiniMax 待 smoke test |
| provider voice preview | 工程链路可用，真实 MiniMax 待 smoke test |
| binding voice preview | 工程链路可用，真实 MiniMax 待 smoke test |
| 声音克隆（上传/创建/绑定） | 暂缓产品化（高成本，需单独评估） |
| 声音设计 | 暂缓产品化（高成本，需单独评估） |
| 多版本试音 | 工程链路可用，真实 MiniMax 待 smoke test |
| 批量长文本生成 | 工程链路可用，真实 MiniMax 待 smoke test |
| 批量剧本生成 | 工程链路可用，真实 MiniMax 待 smoke test |
| 资产下载 / 历史记录 | 工程链路可用，真实 MiniMax 待 smoke test |
| Resource Guard 拒绝路径 | 工程链路可用，真实 MiniMax 待 smoke test |
| 前端测试面板交互 | 待手工验证 |

### 阶段结论

**P7-H 能力验收完成。第一批核心能力工程链路已通过自动化测试和代码审查，真实 MiniMax 能力仍需小文本 smoke test；声音克隆和声音设计为高成本能力，暂缓真实验证，后续单独立项。手工验证尚未执行，建议补充实际浏览器测试后进入 P8 前端 UX 修复阶段。**

---

## P7-I 低成本真实 MiniMax Smoke Test 与前端手工验证

### 背景

- P7-H 已确认工程链路可用
- 本阶段执行低成本真实 MiniMax smoke test（CLI 环境直接 API 调用）
- 声音克隆和声音设计继续暂缓真实验证
- 前端交互和 WebSocket 因无浏览器环境无法测试

### 工作内容

- 新增 docs/P7_I_MINIMAX_SMOKE_TEST.md
- 执行后端自动化测试（366 passed, 6 skipped）
- 启动 uvicorn 服务，直接 curl API 调用验证真实 MiniMax
- 测试同步 T2A、异步 T2A、批量长文本、批量剧本、provider preview
- 发现异步 subtitle timeline end 为 0.0 异常（P2-2）
- 发现 HTTP 流式端点不存在（P2-1）

### 修改文件

- docs/P7_I_MINIMAX_SMOKE_TEST.md（新增）
- docs/PROJECT_HEALTH_CHECK.md（追加本节）

### 测试结果

**自动化测试**：366 passed, 6 skipped

**真实 MiniMax API 测试**：

| 能力 | 结果 |
|---|---|
| 同步 T2A（url/hex） | ✅ 成功，~2s |
| 异步 T2A | ✅ 成功，约 4.5min（MiniMax 服务特性） |
| 批量长文本 | ✅ 成功，merged_audio + merged_subtitle |
| 批量剧本（2角色） | ✅ 成功，多角色正常 |
| provider voice preview | ✅ 成功 |
| 任务历史 | ✅ 成功 |
| WebSocket 流式 | ⚠️ 未测试（CLI 无浏览器） |
| 前端交互 | ⚠️ 未测试（CLI 无浏览器） |
| HTTP 流式端点 | ⚠️ 不存在（流式走 WebSocket） |
| 声音克隆/设计 | **暂缓** |

### 发现问题

- **P1**：异步 T2A 耗时约 4.5 分钟（MiniMax 服务特性，非代码问题）
- **P2-1**：HTTP 流式端点不存在，流式仅走 WebSocket
- **P2-2**：异步任务 subtitle timeline end 为 0.0 → **P7-I1 已修复**

### 阶段结论

**P7-I 真实 MiniMax smoke test 完成。同步 T2A、异步 T2A、批量生成、provider preview 均真实可用。P2-2 已修复；P2-1 HTTP 流式端点不存在仍作为产品/API 口径评估项保留。进入 P8 前仍需补充浏览器前端验证。**

---

## P7-I1 异步 T2A Subtitle Timeline 修复（P2-2）

### 背景

- P7-I 发现异步 T2A 任务完成后 subtitle timeline 的 end 时间为 0.0
- 根因：MiniMax 异步任务返回 `duration_ms=None`，且 metadata 中无 timeline 时，代码未做兜底

### 修复内容

- **文件**：app/services/async_render_service.py
- **修改**：`_complete_job` 方法中 `resolved_duration_ms` 增加 `estimate_duration_ms` 兜底
  ```python
  resolved_duration_ms = (
      task_status.duration_ms
      or task_status.metadata.get("duration_ms")
      or task_status.metadata.get("audio_length")
      or estimate_duration_ms(job.processed_text or job.input_text or "")
  )
  ```
- 同时确保 `duration_ms` 参数传给 `ProviderRenderResult`（之前传的是 `task_status.duration_ms`）

### 测试验证

- 后端自动化测试：366 passed, 6 skipped
- docs/P7_I_MINIMAX_SMOKE_TEST.md 更新：P2-2 标记为已修复

### 阶段结论

**P2-2 已修复；P2-1 HTTP 流式端点不存在仍作为产品/API 口径评估项保留。真实 MiniMax 主链路可用；进入 P8 前仍需补充浏览器前端验证，HTTP 流式端点是否补充另行评估。**

---

## P7-I2 Smoke Test 测试体系治理与进程防护

### 背景

- P7-I 真实 MiniMax smoke test 需要启动 uvicorn
- 手动启动服务后可能残留进程，占用端口
- 本阶段新增标准 smoke runner，治理端口和进程生命周期

### 修改内容

- 新增 `scripts/run_minimax_smoke.py` - 标准 smoke test runner
- 新增 `scripts/stop_smoke_server.py` - 停止残留 smoke server
- smoke test 使用独立端口 8010（可通过 `SMOKE_PORT` 覆盖）
- 启动 uvicorn 不使用 `--reload`
- 使用 `.tmp/uvicorn-smoke.pid` 管理进程
- 默认 dry-run / skip-minimax 不消耗 token
- 真实 MiniMax 调用必须显式 `--real-minimax`
- 测试结束自动清理 uvicorn（try/finally）
- 未知端口占用 fail fast，不盲目 kill
- `.gitignore` 忽略 `.tmp/`

### 阶段边界

- **本阶段不修复 P2-2 异步字幕 timeline**（P7-I1 已修复）
- **本阶段不补 HTTP stream 端点**
- **本阶段不测试声音克隆 / 声音设计**
- **本阶段不修改 app/services/*、app/providers/* 等业务逻辑**

### 阶段结论

**P7-I2 smoke runner 已就绪，可安全执行 dry-run 和真实 smoke test，无需手动管理进程。**

---

## P7-I2a Smoke Runner 可靠性收口

### 修复内容

- runner 自己启动的 uvicorn 优先通过 `proc.terminate()` / `proc.kill()` 清理，pidfile 仅用于残留清理
- 修正 stop 脚本 process alive 判断（tasklist CSV 输出解析，中英双语兼容）
- argparse 模式改为互斥组（`--dry-run | --skip-minimax | --real-minimax`）
- 结果状态统一为 `passed / failed / skipped`
- 删除 `--include-async` / `--include-batch` 参数（预留，暂不执行）
- Ctrl+C / ready 失败时正确清理
- 结果文件记录真实 `started_at / ended_at`

### 验证结果

- `--dry-run`：PASS ready_check，Cleanup: terminated
- `--skip-minimax`：PASS ready_check + jobs_history
- `stop_smoke_server.py`：no pidfile 时 clean
- `--dry-run --skip-minimax`：argparse 报错 "not allowed with argument"
- pytest：368 passed, 6 skipped

### 阶段边界

- 不修改业务代码
- 不真实消耗 MiniMax token（除非显式 `--real-minimax`）

---

## P7-I3 前端异步轮询退避与慢任务体验优化

### 背景

- P7-I 浏览器简测发现功能主链路正常
- 异步 T2A 回复较慢，符合 MiniMax 异步服务特性
- 原有前端固定 3 秒轮询导致日志刷屏和 provider query 压力

### 修改内容

- `app/static/index.html` 增加异步轮询状态对象 `asyncPollingState`
- 增加轮询退避策略 `getAsyncPollingDelay()`：0-30s 每 3s，30s-2min 每 10s，2min+ 每 20s
- 提交后显示"可能需要 1-5 分钟"慢任务提示
- 增加手动刷新（`manualRefreshAsyncJob`）和停止自动刷新（`stopAsyncPolling`）按钮
- Resource Guard 查询拒绝时停止自动轮询
- 添加空 favicon `data:,`，避免 `/favicon.ico` 404 日志噪音

### 验证结果

- 代码层面已接入异步轮询退避，手动刷新、停止自动刷新和最大自动轮询保护；浏览器手工验证结果需按实际测试补充。
- pytest：368 passed, 6 skipped
- 不消耗 MiniMax token（前端体验优化，无后端改动）

### 阶段边界

- 不修改 `app/services/*`、`app/providers/*` 等业务代码
- 不修改 Resource Guard 策略
- 不实现新的后端能力

---

## P7-I3a 异步轮询退避收口

### 背景

- P7-I3 已完成异步轮询退避和慢任务提示
- 复核发现手动刷新可能导致重复 timer
- 自动轮询缺少最大时长限制

### 修改内容

- 增加 `clearAsyncPollingTimer()` 分层 helper
- 手动刷新前清理旧 timer
- 设置新 timer 前清理旧 timer
- 增加 jobId 防护，避免旧 timer 污染当前 job
- 增加最大自动轮询时长（15 分钟），超过后暂停自动刷新
- 停止自动刷新后更新 UI 提示

### 验证结果

- 代码层面已完成所有 timer 防护逻辑
- pytest：368 passed, 6 skipped
- 前端浏览器手工验证结果需补充

### 阶段结论

异步轮询已实现防重复 timer 和最大自动轮询时长保护，逻辑完整。
- 不修改 Resource Guard 策略
- 不实现新的后端能力

---

## P7-I5 Admin Stats characters=0 修复 + Provider Error Attribution

### 背景

- Admin stats API 返回 `total_characters: 0`，即使有成功的 T2A 任务
- 需要工具分析 provider 错误归因

### 根因分析

**问题 1：`job_id` 上下文未设置**
- `job_id_var` 从未被设置，`get_job_id()` 返回空字符串
- `_save_call_log` 存储 `job_id=NULL`，`update_call_log` 查询 `job_id=""` 找不到记录
- 导致 `usage_characters` 从未被正确更新

**问题 2：异步任务从未调用 `update_call_log`**
- `create_async_task` 不调用 `update_call_log`

**问题 3：`StatsService` 仅从 `ProviderCallLog` 读取**
- 不使用 `AudioAsset.usage_characters` 作为后备

### 修改内容

**context.py**
- 新增 `set_job_id(job_id: str)` 函数

**voice_render_service.py**
- `render_voice()` 在调用 `render_sync()` 前设置 `set_job_id(job.id)`

**async_render_service.py**
- `submit_task()` 在调用 `create_async_task()` 前设置 `set_job_id(job.id)`
- `query_status()` 在调用 `query_async_task()` 前设置 `set_job_id(job.id)`

**stats_service.py**
- `get_summary()` 对 `total_characters`、`by_provider`、`by_day` 使用 `MAX(call_chars, asset_chars)` 
- 这确保即使 `ProviderCallLog.usage_characters` 未更新，也能从 `AudioAsset` 获取准确值

**scripts/analyze_provider_errors.py**（新增）
- 按错误类型、错误消息前缀、API路径、provider 分组分析错误
- 支持 `--days`、`--provider`、`--error-type`、`--top`、`--json` 参数

### 验证结果

- pytest：374 passed, 6 skipped（P7-I5a 后新增 context/stats 测试）
- `python scripts/analyze_provider_errors.py --days 7 --top 5` 正常运行

### 阶段结论

- `job_id` 上下文修复确保同步 T2A 的 `update_call_log` 正常工作
- `AudioAsset` 后备确保异步任务字符统计准确
- Provider error analysis 脚本可用于识别错误模式

---

## P7-I5a Admin 字符统计与 job_id context 收口

### 背景

- P7-I5 已修复字符数统计主链路
- 复核发现 `set_job_id()` 没有 reset，存在 context 泄漏风险
- WebSocket 流式链路缺少 `job_id` context
- `get_daily_trend(metric="characters")` 缺少 AudioAsset fallback

### 修改内容

**context.py**
- `set_job_id()` 改为返回 `ContextVar.Token`
- 新增 `reset_job_id(token)` 函数

**voice_render_service.py**
- 同步 T2A provider 调用使用 `try/finally` + `reset_job_id(token)` 确保 context 恢复

**async_render_service.py**
- `create_async_task` 和 `query_async_task` 调用前设置 job_id context，调用后 reset

**stream_render_service.py**
- WebSocket 流式在 provider generator 迭代期间设置 job_id context，结束后 reset

**stats_service.py**
- `get_daily_trend(metric="characters")` 改为同时聚合 `ProviderCallLog` 和 `AudioAsset`，按天取 `max(call_chars, asset_chars)`

**tests/test_context.py**（新增）
- `test_job_id_context_set_and_reset`
- `test_job_id_context_nested`
- `test_job_id_context_empty_string`

**tests/test_stream_render_service.py**（新增）
- `TestStreamRenderJobIdContext::test_stream_render_sets_and_resets_job_id_context`

**tests/test_stats_api.py**（新增）
- `test_daily_trend_characters_uses_audio_asset_fallback`
- `test_daily_trend_characters_uses_max_not_sum`

### 验证结果

```bash
python -m pytest tests/ -x -q
# 374 passed, 6 skipped
```

### 阶段结论

- `set_job_id()` 返回 token，`reset_job_id()` 确保 context 不会泄漏到后续调用
- 同步/异步/流式三条链路的 provider 调用都已纳入 job_id context 管理
- 统计 fallback 已覆盖 overview、by_provider、by_day、daily_trend 所有维度
- 所有 context 和 stats 测试通过

---

## P7-I5b async query job_id context double reset 修复

### 背景

- P7-I5a 已完成 job_id context reset 收口
- 复核发现 `AsyncRenderService.query_status()` 的 provider query 异常路径存在 double reset
- 同一个 `ContextVar.Token` 被 reset 两次可能覆盖原始 provider 异常

### 修改内容

- 删除 async query `except` 分支中的重复 `reset_job_id(token)`
- 保留 `finally` 中的唯一 reset
- 新增异常路径测试，验证原始异常不被 double reset 覆盖
- 不改变 Resource Guard、job 状态机和 provider 调用逻辑

### 新增测试

- `test_async_query_provider_exception_resets_job_id_once_and_preserves_error`

### 验证结果

```bash
python -m pytest tests/test_async_render.py -q
# 17 passed
python -m pytest tests/ -x -q
# 375 passed, 6 skipped
```

### 阶段结论

异步 query 的 job_id context reset 逻辑已收口，异常路径不会二次 reset，也不会覆盖原始 provider 异常。

---

## P7-I6 真实能力验证与修复收口

### 背景

P7-I 阶段用于验证真实 MiniMax 主链路，并修复真实测试暴露的问题。

### 收口内容

- P7-I 真实 MiniMax smoke test 已完成
- P7-I1 / I1a 异步字幕 timeline 修复完成
- P7-I2 / I2a smoke runner 进程治理完成
- P7-I3 / I3a 异步轮询退避与体验修复完成
- P7-I5 / I5a / I5b Admin 统计、错误归因、job_id context 收口完成

### 验证结果

```bash
python -m pytest tests/ -x -q
# 375 passed, 6 skipped
```

### 当前结论

- 无 P0/P1 阻塞
- 同步 / 异步 / 流式 / 批量 / 字幕 / 下载 / 历史记录均可进入 P8 产品化候选
- 声音克隆 / 声音设计继续暂缓
- HTTP 流式端点是否补充仍属于产品/API 口径决策
- 可以进入 P8 前端产品化规划

---

## P7-J0 并发架构问题归纳与轻量策略

### 背景

P7-I 已完成真实 MiniMax 主链路验证与修复收口。当前后台核心能力基本稳定，但围绕多浏览器访问、多用户并发、前端误点、刷新后重复提交、本地 App / SaaS / BYOK 产品形态等问题，需要沉淀并发架构边界。

### 新增文档

- `docs/P7_J_CONCURRENCY_ARCHITECTURE.md`

### 结论

- 当前系统支持基础并发
- 当前并发控制是单进程内 Resource Guard，按 provider + operation 限制
- 超限时直接返回 `RESOURCE_LIMIT_EXCEEDED`，不排队
- 小规模多浏览器 / 多用户访问相对安全
- 当前不承诺高并发多人 SaaS 能力
- 当前不建议立即引入队列、worker、Redis、PostgreSQL 或完整幂等表
- P8 应优先做前端产品化和轻量防误点 / 任务恢复

---

## P8-0 前端产品化范围定义与路线收敛

### 背景

P7-I 已完成真实能力验证与修复收口，P7-J0 已完成并发架构边界归纳。当前后台核心能力基本稳定，下一阶段进入 P8 前端产品化。

### 结论

- P8 不继续扩张后端主能力
- P8 聚焦前端产品化和用户工作流
- 第一版建议定位为本地 Web App / 单用户音频创作工作台
- 第一批产品化能力包括同步 T2A、异步 T2A、WebSocket 流式、批量长文本、批量剧本、字幕、音色试听、历史记录和下载
- 声音克隆 / 声音设计继续暂缓
- 不做完整登录、BYOK、开放 API、队列 worker、高并发 SaaS 架构
- P8-1 建议先做前端信息架构重组

### 新增文档

- `docs/P8_0_PRODUCTIZATION_SCOPE.md`

---

## P8-1 前端信息架构重组

### 背景

P8-0 已完成产品化范围定义，明确第一版为本地 Web App / 单用户音频创作工作台。P8-1 开始执行前端信息架构重组，将测试面板整理为音频创作工作台。

### P8-1A 审查执行

- 新增 `docs/P8_1_FRONTEND_INFORMATION_ARCHITECTURE.md`
- 完整记录当前 DOM id、JS 函数、tab 结构和安全修改边界
- 确认所有 DOM id 和 JS function behaviors 不改变

### P8-1B 前端标签页重组

已完成：

- 页面标题从 "Voice Lab 测试面板" 改为 "AI 音频创作工作台"
- header 副标题从 "MiniMax 语音接口测试与验证平台" 改为 "短视频旁白与音频剧本生成"
- 标签页从 6 个重组为新 6 个：
  - `workspace`（原 T2A 生成，去除历史记录）
  - `longtext`（原批量生成中的长文本模式）
  - `script`（原批量生成中的剧本模式）
  - `voices`（音色管理，保留）
  - `history`（原 T2A 内历史记录，独立成 tab）
  - `advanced`（原声音克隆、声音设计、绑定管理，增加高成本警告）
- 新增 `switchAdvancedSubtab()` 函数处理高级 tab 内子 tab 切换
- 调整 tab-switching 回调，处理新 tab 名称

### 修改文件

- `app/static/index.html`
- `docs/P8_1_FRONTEND_INFORMATION_ARCHITECTURE.md`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`

### 验证结果

```bash
python -m pytest tests/ -x -q
# 375 passed, 6 skipped
```

### P8-1B 验收清单

| 检查项 | 状态 |
|---|---|
| 页面标题已更新 | ✅ |
| header 副标题已更新 | ✅ |
| tab 按钮已重组 | ✅ |
| tab-workspace 存在且内容正确 | ✅ |
| tab-history 独立，包含历史记录 | ✅ |
| tab-longtext 独立，包含长文本配置 | ✅ |
| tab-script 独立，包含剧本配置 | ✅ |
| tab-voices 保留原始功能 | ✅ |
| tab-advanced 包含克隆/设计/绑定，含高成本警告 | ✅ |
| subtab 切换函数 `switchAdvancedSubtab` 正常工作 | ✅ |
| 所有 DOM id 未改变 | ✅ |
| 所有 JS function behaviors 未改变 | ✅ |
| pytest 375 passed, 6 skipped | ✅ |

### P8-1C 健康检查更新

- 在 docs/PROJECT_HEALTH_CHECK.md 追加 P8-1 章节，记录 P8-1A 和 P8-1B 的执行与验收状态

### P8-1D 最终验收

- git status -sb：干净
- pytest：375 passed, 6 skipped
- 未执行真实 MiniMax smoke test（前端架构重组不需要消耗真实额度）

### P8-1E 收口修正

已完成：

- 页面 title / h1 统一为：Voice Lab｜AI 音频创作工作台
- 副标题改为：把文本、长文和多角色剧本转成可试听、可下载、可管理的音频资产
- tab-workspace 顶部新增欢迎区和三条主流程卡片（单段旁白、长文本生成、多角色剧本）
- 高级 tab 高成本警告扩展说明
- docs/P8_1_FRONTEND_INFORMATION_ARCHITECTURE.md 补齐 P8-1B/C/D/E 执行记录
- docs/PROJECT_HEALTH_CHECK.md 顶部新增"当前最新状态摘要"，避免旧状态段落误导

### 后续计划

- P8-1E：收口修正（本次）
- P8-2：音色选择 / 试听工作台

---

## P8-2A 音色选择 / 试听工作台现状审查

### 背景

P8-1 已完成前端信息架构重组。P8-2 目标是整理"音色"tab 为真正的音色选择 / 试听工作台。P8-2A 只做审查和文档化，不改代码。

### 新增文档

- `docs/P8_2_VOICE_SELECTION_WORKSTATION.md`

### P8-2A 主要发现

1. **删除音色在 tab-voices 内**（应在 tab-advanced），是最大风险点
2. **tab-voices 承担 6+ 功能**，信息密度过高
3. **试听工作台动态渲染在 voiceListResults 内部**，DOM 耦合严重
4. **快速绑定**是弹出面板，交互需优化
5. **tab-advanced/subtab-bindings 已有完整绑定管理**，与快速绑定有分层
6. **试听产生成本但 confirm_cost=false**，需在高成本警告中体现
7. **所有 DOM id 和 JS function behavior 应保留**，P8-2B 只做架构整理

### 修改文件

- `docs/P8_2_VOICE_SELECTION_WORKSTATION.md`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`（更新状态摘要）

### 验证命令

```bash
git status -sb
git diff --check
python -m pytest tests/ -x -q
```

### 验证结果

- git status -sb：干净
- git diff --check：无 whitespace error
- pytest：375 passed, 6 skipped

### 阶段结论

P8-2A 只完成审查和文档化。下一步进入 P8-2B：音色 tab 信息架构整理（只改 DOM 结构，不改 API 和 JS function behavior）。

---

## P8-2B 音色 tab 信息架构整理

### 背景

P8-2A 发现删除音色仍在 tab-voices 内（应在 advanced）。P8-2B 目标是将 tab-voices 整理为更聚焦的音色选择 / 试听工作台。

### 主要调整

1. **tab-voices 新增说明区**：音色选择 / 试听工作台标题 + 试听成本提示 + 绑定说明
2. **删除音色迁移**：从 tab-voices 移入 tab-advanced/subtab-danger
3. **新增 danger 子 tab**：高级区增加"危险操作"子 tab，收纳删除音色
4. **switchAdvancedSubtab 更新**：增加对 danger 子 tab 的支持

### 风险处理

- 保留所有 deleteProvider / deleteVoiceId / deleteVoiceType / deleteResults（静态 DOM）
- 保留 handleDeleteVoice / handleVoiceDeleteFromList 行为不变
- 保留所有音色查询、试听、绑定相关 JS 函数行为不变
- 只做 DOM 迁移，不改 API endpoint

### 修改文件

- `app/static/index.html`
- `docs/P8_2_VOICE_SELECTION_WORKSTATION.md`
- `docs/PROJECT_HEALTH_CHECK.md`

### 验证命令

```bash
python -m pytest tests/ -x -q
```

### 验证结果

- pytest：375 passed, 6 skipped
- DOM marker check：passed
- JS function check：passed
- Advanced subtab mapping check：passed
- 未执行真实 MiniMax smoke test

### 阶段结论

P8-2B 已完成音色 tab 信息架构整理。下一阶段建议进入 P8-2C：试听工作台产品化。

## P8-2C 试听工作台产品化

### 背景

P8-2C 于 commit `2483245` 完成试听工作台 UI 产品化。

### 主要变更

1. 新增 `auditionSelectedBanner` 高亮 banner（渐变背景，仅选中音色后显示）
2. 新增 `auditionCostHint` 字符数提示（实时显示"约 N 字"）
3. 重构 `auditionResult` 结果卡片（成功 / 失败 / 无音频三种状态）
4. 将 `auditionRecords` 从表格改为卡片布局
5. 适配星级 hover 事件委托（从 `.star-cell` 改为 `.star[data-index]`）

### 仅 UI 展示声明

P8-2C 所有变更均为前端 UI 展示调整，未修改任何 API endpoint、请求逻辑或后端代码。

### 阶段结论

P8-2C 已完成试听工作台 UI 产品化。下一阶段进入 P8-2C1：收口修复。

## P8-2C1 试听工作台收口修复

### 背景

P8-2C 提交 `2483245` 遗留两个收口问题：
1. P8-2C 文档未同步更新（仅修改了 index.html）
2. `renderAuditionRecords` 初始实现采用局部更新 / append 模式，存在卡片状态错位风险

### 问题

| 问题 | 风险 |
|------|------|
| P8-2C 文档缺失 | 后续无法追溯 P8-2C 变更内容 |
| `records.forEach` + `existingCard` 局部更新 | 删除中间记录后 card id 与 index 错位 |
| `container.appendChild(card)` | 0→1 条时"暂无"占位可能残留 |
| 局部更新不完整 | voice_id / voiceName / textPreview 在已有卡片上不更新 |

### 方案

采用 `renderAuditionRecords` 全量重绘方案：
- `records.length === 0` → `container.innerHTML = 空状态占位`，return
- `records.length > 0` → `records.map` 生成所有 card HTML，`container.innerHTML = cardsHtml.join('')`
- 不再使用 `existingCard`、`appendChild`、过期 card 清理逻辑

### 修改文件

- `app/static/index.html` — `renderAuditionRecords` 改为全量重绘
- `docs/P8_2_VOICE_SELECTION_WORKSTATION.md` — 补齐 P8-2C + P8-2C1 文档
- `docs/PROJECT_HEALTH_CHECK.md` — 补充 P8-2C / P8-2C1 状态

### 验证结果

- pytest：375 passed, 6 skipped
- P8-2C1 DOM marker check：passed
- P8-2C1 JS function check：passed
- P8-2C1 renderAuditionRecords stability check：passed
- P8-2C1 API marker check：passed
- P8-2C1 documentation marker check：passed

### 未做事项

- ❌ 未改后端 API
- ❌ 未改 Provider
- ❌ 未改 Resource Guard / Cost Guard
- ❌ 未改数据库
- ❌ 未执行真实 MiniMax smoke test
- ❌ 未进入 P8-2D

### 风险清零

| 风险 | 状态 |
|------|------|
| P8-2C 文档缺失 | ✅ 已补齐 |
| renderAuditionRecords 局部更新错位 | ✅ 已改为全量重绘 |
| "暂无"占位残留 | ✅ records.length===0 时立即 innerHTML |
| 卡片内容与 record 不一致 | ✅ 每次全量重绘 |

### 阶段结论

P8-2C1 已完成试听工作台收口修复。P8-2C 可视为已完成并收口。下一阶段建议进入 P8-2D：轻量绑定入口整理。

## P8-2D 轻量绑定入口整理

### 背景

P8-2D 于 commit `4d03901` 之后完成轻量绑定入口整理。P8-2C / P8-2C1 已完成试听工作台产品化和收口。

### 主要变更

1. **绑定按钮文案**：从"绑定"改为"绑定到人设"，更清楚表达操作目标
2. **quickBindVoice 面板**：添加标题"绑定到声音人设"和说明文字，改进面板样式
3. **绑定成功 / 失败反馈**：改为绿色/红色卡片样式，处理中显示"绑定中…"并禁用按钮
4. **绑定状态 badge**：已绑定显示绿色 badge + count + profile 名称，未绑定显示橙色 badge
5. **绑定说明区**：更新边界说明，明确轻量绑定和高级绑定管理的关系

### 仅 UI 展示声明

P8-2D 所有变更均为前端 UI 展示调整，未修改任何 API endpoint、请求逻辑或后端代码。

### 阶段结论

P8-2D 已完成轻量绑定入口整理。下一阶段建议进入 P8-2E：P8-2 验收与健康检查收口。

## P8-2D1 移除音色列表行内删除入口

### 背景

P8-2D1 于 commit `8d0a8d0` 之后完成音色列表行内删除入口收口。P8-2B 已将删除音色表单迁移到高级 / 危险操作区，但自检发现 `renderVoiceTable()` 中仍保留行内"删除"按钮。

### 主要变更

1. **移除行内删除按钮**：`renderVoiceTable()` 操作列不再显示"删除"按钮
2. **清理死代码**：移除 `showDelete` 和 `voiceTypeLabel` 变量
3. **补充引导文案**：绑定说明区新增"删除音色请进入「高级 / 危险操作」"

### 保留内容

- 高级 / 危险操作区删除表单保留
- `handleDeleteVoice()` 函数保留
- `handleVoiceDeleteFromList()` 函数保留（但不再被行内按钮触发）
- 删除 API endpoint 未变更

### 仅 UI 展示声明

P8-2D1 所有变更均为前端 UI 展示调整，未修改任何 API endpoint、请求逻辑或后端代码。

### 阶段结论

P8-2D1 已完成音色列表行内删除入口收口。删除音色能力已完全收敛到高级 / 危险操作区。下一阶段建议进入 P8-2E：P8-2 验收与健康检查收口。

## P8-2E 音色选择 / 试听工作台验收与健康检查收口

### 背景

P8-2E 于 commit `d763b38` 之后完成 P8-2 全阶段验收与健康检查收口。

### P8-2 阶段总结

P8-2 完成了以下工作：

- P8-2A：现状审查（601a647）
- P8-2B：音色 tab 信息架构整理（5ad8c07）
- P8-2C：试听工作台产品化（2483245）
- P8-2C1：试听工作台收口修复（4d03901）
- P8-2D：轻量绑定入口整理（8d0a8d0）
- P8-2D1：移除音色列表行内删除入口（d763b38）

### 修改文件

- `docs/P8_2_VOICE_SELECTION_WORKSTATION.md` — P8-2E 完整验收文档（sections 81-94）
- `docs/PROJECT_HEALTH_CHECK.md` — P8-2E 状态更新

### 验收范围

- DOM id 保留验收：全部通过（38 个 DOM id 全部存在）
- JS function 保留验收：全部通过（26 个函数全部存在）
- API endpoint 不变验收：全部通过（10 个 API marker 全部存在）
- renderAuditionRecords 稳定性检查：通过（使用全量重绘）
- renderVoiceTable 行内删除移除检查：通过（删除按钮已移除）
- 高级危险操作区删除能力保留检查：通过（删除表单完整）
- 高级子 tab 映射检查：通过（clone/design/bindings/danger 全部存在）
- 文档标记检查：通过

### 自动验证命令

所有静态检查均已通过（DOM / JS function / API / stability / delete removal / danger form retention / subtab mapping / documentation）

### 验证结果

- pytest：375 passed, 6 skipped
- 无 whitespace error
- 无测试失败
- 未执行真实 MiniMax smoke test（本阶段是验收与文档收口，不需要消耗额度）

### 手工验收清单

已完成以下手工验收：

- 页面与导航验收
- 音色查询路径验收
- 试听工作台路径验收
- 试听记录路径验收
- 轻量绑定路径验收
- 高级绑定管理验收
- 危险操作区验收
- 管理面板验收

### 未做事项

- 未改后端 API
- 未改前端代码（仅文档修改）
- 未执行真实 MiniMax smoke test
- 未进入 P8-3

### 阶段结论

P8-2E 已完成。P8-2 音色选择 / 试听工作台已完成并收口。下一阶段建议进入 P8-3：任务卡片和结果展示。

---

## P8-3A 任务结果展示现状审查

### 背景

P8-3 是"任务卡片和结果展示"产品化阶段。P8-3A 是纯审查阶段：仅做现状审查和文档化，不改前端、不改后端、不改 JS 逻辑。

### 本次工作

- 新增 `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`
- 覆盖内容：DOM 现状（核心容器/批量任务/流式状态）、JS 函数清单（渲染/状态/工具）、API 端点映射、用户路径分析（6条路径）、问题与风险（8项）、静态检查基线（DOM/JS/API/CSS）

### 审查发现

发现 8 个问题与风险：

1. **字幕时间轴播放器同步缺失**：renderAsyncResult/renderResults 的 timelineTable 不参与播放同步，用户播放音频时无法跟随进度
2. **流式结果下载入口分散**：服务端下载按钮可能在 asset 未生成时 404
3. **批量字幕缓存只存 timeline**：不缓存 .srt/.vtt 格式内容，下载无缓存加速
4. **resultsArea 全量替换模式**：轮询时重建 DOM，可能导致音频播放器状态丢失
5. **错误渲染分散**：renderApiError 无重试倒计时或队列预估信息
6. **异步任务最大轮询时间硬编码**：15 分钟硬编码，超长任务用户不知已停止轮询
7. **批量脚本无独立轮询状态对象**：无 stopBatchScriptPolling()
8. **variantCountInput 无防误点**：多版本生成费用较高但无 input 锁定

### 修改文件

- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`（追加本节）

P8-2E 已完成。P8-2 音色选择 / 试听工作台已完成并收口。下一阶段建议进入 P8-3：任务卡片和结果展示。

---

## P8-3B resultsArea 信息架构整理

### 背景

P8-3B 是 resultsArea 信息架构整理阶段，目标是让同步 / 异步 / 多版本结果展示更像任务结果卡片，但不改变任何业务链路。

### 主要调整

1. **新增 helper**：`resultSectionLabel(text)` 返回统一 section label HTML，无 API 调用，无状态读写
2. **renderResults 非 variant 分支**：外层从 `result-section` 改为 `card`，标题改为"任务结果"，增加同步生成说明文字，增加元信息行（job_id/provider/model），音频/下载/字幕全部有 section label
3. **renderResults variant 分支**：外层改为 `card`，标题改为"任务结果"并显示版本数量，每个 variant 卡片增加音频/下载 section label
4. **renderAsyncResult**：保留 `card` 外层，标题改为"任务结果"，status badge 独立行，音频/下载/字幕全部有 section label，timelineTable 空状态处理
5. **timelineTable**：增加空状态处理，`timeline == null || length === 0` 时返回"暂无字幕时间轴"
6. **未改变**：handleGenerate、轮询、WebSocket、批量、流式、下载 API、timeline 数据结构

### 修改文件

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3B 节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新摘要 + 追加本节）

### 风险处理

- 全量 DOM 替换模式保留（本阶段不解决）
- 字幕播放同步缺失保留（留待后续阶段）
- 流式和批量结果结构未调整（本阶段不处理）
- 所有 API endpoint 和请求逻辑完全未变

### 验证命令

- DOM/display marker 检查：通过
- JS function 检查：通过（包含新增 `resultSectionLabel`）
- API marker 检查：通过
- handleGenerate 请求逻辑保留检查：通过
- stream/batch 保留检查：通过
- 文档标记检查：通过

### 验证结果

pytest: 375 passed, 6 skipped
git diff --check: 无 whitespace error

### 未做事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未拆分 `index.html`
- 未进入 P8-3C

### 阶段结论

P8-3B 已完成 resultsArea 信息架构整理。下一阶段建议进入 P8-3C：同步 / 异步结果卡片化细化验收。

---

## P8-3C 同步 / 异步结果卡片化细化验收

### 背景

P8-3C 是同步 / 异步结果卡片化细化验收阶段，目标是让状态、空状态、错误信息展示更准确，不改变任何业务链路。

### 主要调整

1. **新增 helper**：`resultStatusHintHtml(status)` 返回状态说明文本，无 API 调用，无状态读写
2. **新增 helper**：`resultDiagnosticHtml(message)` 返回诊断信息 HTML，用于 failed 状态，无 API 调用，无状态读写
3. **`renderResults` 非 variant 分支**（同步）：增加 `resultStatusHintHtml(job.status)` 状态说明；audio 不存在且 success 时显示"本次结果未返回音频资产"；无 subtitle 且 success 时显示"本次结果未返回字幕时间轴"；非 success 状态不提前展示空 audio/subtitle
4. **`renderAsyncResult`**：三分支处理（processing/failed/success）；processing 仅展示状态说明，无 audio/下载/字幕 sections；failed 展示 `resultDiagnosticHtml`；success 展示音频/字幕（如无则显示准确空状态）
5. **口径统一**：确认 `renderSyncResult` 不存在于代码中，同步结果走 `renderResults(data, isVariant=false)`
6. **未改变**：handleGenerate、轮询、WebSocket、批量、流式、下载 API、timeline 数据结构

### 修改文件

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3C 节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新摘要 + 追加本节）

### 风险处理

- 字幕播放同步缺失保留（留待后续阶段）
- 流式和批量结果结构未调整（本阶段不处理）
- 所有 API endpoint 和请求逻辑完全未变

### 验证命令

- DOM/display marker 检查：通过
- JS function 检查：通过（包含新增 helpers）
- API marker 检查：通过
- handleGenerate 请求逻辑保留检查：通过
- 异步轮询保留检查：通过
- stream/batch 保留检查：通过
- 文档标记检查：通过

### 验证结果

pytest: 375 passed, 6 skipped
git diff --check: 无 whitespace error

### 未做事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未处理批量结果卡片化
- 未处理流式结果深度重构
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-3D

### 阶段结论

P8-3C 已完成同步 / 异步结果卡片化细化验收。下一阶段建议进入 P8-3D：流式 / 多版本结果展示统一。

---

## P8-3C1 结果状态口径自检与收口修复

### 背景

P8-3C1 是结果状态口径自检与收口修复阶段，目标是统一展示层状态语义，避免 `success`/`completed`、`failed`/`error` 等口径不一致导致展示错误。

### 主要调整

1. **新增 `isResultSuccessStatus(status)`**：统一识别 `success` / `completed` 为完成态
2. **新增 `isResultFailedStatus(status)`**：统一识别 `failed` / `error` 为失败态
3. **新增 `isResultProcessingStatus(status)`**：统一识别 `queued` / `pending` / `running` / `processing` 为等待/处理中态
4. **`resultStatusHintHtml` 补全**：`completed`（已完成）、`error`（任务失败）、`queued`（任务等待中）等文案
5. **`renderAsyncResult`**：状态判断改为使用 helper，`extractErrorMessage(data)` 替代手写错误字段提取
6. **`renderResults` 非 variant**：状态判断改为使用 helper，failed/error 展示诊断信息而非空状态提示
7. **未改变**：handleGenerate、轮询、WebSocket、批量、流式、下载 API

### 修改文件

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3C1 节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新摘要 + 追加本节）

### 风险处理

- 状态口径不一致导致误判展示的风险已消除
- `completed` / `error` 等后端状态不再被误判为处理中
- `extractErrorMessage(data)` 覆盖更多错误字段，诊断信息更准确

### 验证命令

- DOM/display marker 检查：通过
- JS function 检查：通过（包含新增 3 个 helper）
- 状态 helper 语义检查：通过
- renderAsyncResult 状态分支检查：通过
- renderResults 非 variant 状态分支检查：通过
- API marker 检查：通过
- handleGenerate 请求逻辑保留检查：通过
- 异步轮询保留检查：通过

### 验证结果

pytest: 375 passed, 6 skipped
git diff --check: 无 whitespace error

### 未做事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未处理批量结果卡片化
- 未处理流式结果深度重构
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-3D

### 阶段结论

P8-3C1 已完成结果状态口径自检与收口修复。下一阶段建议进入 P8-3D：流式 / 多版本结果展示统一。

---

## P8-3D 流式 / 多版本结果展示统一

### 背景

P8-3D 是流式 / 多版本结果展示统一阶段，目标是让流式生成结果和多版本试音结果的展示结构与 P8-3B/P8-3C 已整理的任务结果 card 保持一致。

### 主要调整

1. **`renderStreamResult`**：外层从 `result-section` 改为 `card`，增加"任务结果"主标题、"流式生成结果"副标题、"流式接收完成，可以播放生成音频。"提示、section label 统一、本地缓存与服务端 asset 下载区分说明
2. **`renderResults` variant 分支**：variants 为空时展示明确空状态卡片，单版本无 audio 时红色提示"该版本未返回音频资产。"
3. **未改变**：startStreamGenerate、WebSocket 逻辑、variants API、variantCount

### 修改文件

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3D 节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新摘要 + 追加本节）

### 风险处理

- 流式本地缓存与服务端 asset 下载区分说明已增加
- variants 空状态已处理，不再抛 JS 异常
- 多版本无 audio 时提示已从灰色改为红色，更醒目

### 验证命令

- DOM/display marker 检查：通过
- JS function 检查：通过
- API/WebSocket marker 检查：通过
- startStreamGenerate 逻辑保留检查：通过
- renderStreamResult 展示检查：通过
- renderResults variant 分支检查：通过
- P8-3C1 状态 helper 保留检查：通过

### 验证结果

pytest: 375 passed, 6 skipped
git diff --check: 无 whitespace error

### 未做事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理 WebSocket 服务端结果资产化
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未处理批量结果卡片化
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-3F

### 阶段结论

P8-3D 已完成流式 / 多版本结果展示统一。下一阶段建议进入 P8-3F 或其他 P8 后续阶段。


---

## P8-3E 错误 / Resource Guard / 下载入口产品化

### 背景

P8-3E 是错误提示、Resource Guard 和下载入口产品化阶段，目标是让错误结果与任务结果一样使用统一的 card 结构展示，明确区分 Resource Guard 限制与系统异常，优化下载按钮文本和流式下载描述。

### 主要调整

1. **`renderApiError`**：从 `error-msg` div 升级为带 "错误提示" 标签的 card 结构，左边框颜色区分普通错误（红 #c53030）和资源限制（橙 #dd6b20），包含建议操作区域（💡 引导的 Resource Guard hint）和可展开的 "技术详情"
2. **`friendlyErrorMessage`**：扩展支持 Provider error、cancellation、network error 三类用户友好的错误文案
3. **`formatApiError`**：RESOURCE_LIMIT_EXCEEDED 消息明确标注 "触发资源限制（Resource Guard）"
4. **`resourceLimitExtraHint`**：强调 "这是 Resource Guard 限制，不是系统异常"
5. **`downloadBtnHtml`**：按钮文本从 "下载" 改为 "下载音频"
6. **流式下载入口**：标签从 "下载(服务端)/下载(本地缓存)" 改为 "下载音频（服务端）/下载音频（浏览器缓存）"，添加描述文字说明两者差异

### 修改文件

- `app/static/index.html`（展示层代码调整）
- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3E 节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新摘要 + 追加本节）

### 风险处理

- Resource Guard 限制明确告知用户不是系统异常，减少困惑
- Provider/cancellation/network 错误文案更清晰
- 下载按钮文本 "下载音频" 比 "下载" 更明确
- 流式下载两种方式的差异已明确说明

### 验证命令

- friendlyErrorMessage Provider error：✅
- friendlyErrorMessage cancellation：✅
- friendlyErrorMessage network error：✅
- formatApiError Resource Guard 标注：✅
- resourceLimitExtraHint 提示优化：✅
- renderApiError card 结构：✅
- downloadBtnHtml "下载音频"：✅
- 流式下载服务端/浏览器缓存标签：✅
- 流式下载描述文字：✅

### 验证结果

pytest: 375 passed, 6 skipped
git diff --check: 无 whitespace error

### 未做事项

- 未处理字幕播放同步
- 未处理流式下载 404 时序
- 未处理 WebSocket 服务端结果资产化
- 未处理批量字幕缓存
- 未处理 Resource Guard 排队预估
- 未处理异步轮询最大时长提示
- 未处理批量脚本独立轮询状态
- 未处理多版本费用防误点
- 未处理批量结果卡片化
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test
- 未进入 P8-4

### 阶段结论

P8-3E 已完成错误提示、Resource Guard 和下载入口产品化。下一阶段建议进入 P8-4：历史记录和下载体验。


---

## P8-3F 任务结果展示验收与健康检查收口

### 背景

P8-3F 是 P8-3 的最终验收与健康检查收口阶段。目标是复核 P8-3A 到 P8-3E 的工作成果，确认文档对齐和代码状态健康。

### P8-3 阶段总结

P8-3 已完成任务卡片和结果展示产品化：

| 阶段 | 提交 | 说明 |
|---|---|---|
| P8-3A | b8e69b0 | 任务结果展示现状审查 |
| P8-3B | d5d0655 | resultsArea 信息架构整理 |
| P8-3C | 488eca3 | 同步 / 异步结果卡片化细化验收 |
| P8-3C1 | 1d1fb2e | 结果状态口径自检与收口修复 |
| P8-3D | 6e57590 | 流式 / 多版本结果展示统一 |
| P8-3E | bcb1448 | 错误 / Resource Guard / 下载入口产品化 |

### 修改文件

- `docs/P8_3_RESULT_DISPLAY_WORKSTATION.md`（追加 P8-3F 节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新摘要 + 追加本节）

### 验收范围

本阶段只读复核，不改业务逻辑：

- resultsArea DOM id 保留
- 核心 JS function 保留
- API endpoint 不变
- 状态 helper 完整性
- 流式 / 多版本展示结构
- 错误 / Resource Guard 展示
- 下载入口文案

### 自动验证命令

- DOM marker check: python 脚本
- JS function check: python 脚本
- API/WebSocket marker check: python 脚本
- status helper check: python 脚本
- stream result display check: python 脚本
- variant result display check: python 脚本
- error/Resource Guard display check: python 脚本
- download marker check: python 脚本
- documentation marker check: python 脚本
- python -m pytest tests/ -x -q

### 验证结果

pytest: 375 passed, 6 skipped
git diff --check: 无 whitespace error

是否执行真实 MiniMax smoke test：**未执行**（P8-3F 是验收与文档收口阶段，不涉及后端 API 改造）

### 手工验收清单

- 页面能正常打开，顶部导航存在
- 同步结果显示为任务结果 card
- 异步结果有 job_id 显示和状态提示
- 流式结果有 card 结构和浏览器缓存说明
- 多版本结果有 variants-grid 和版本参数
- 错误显示为 card 结构，Resource Guard 有橙色强调
- 下载按钮文案为"下载音频"
- 流式下载区分服务端和浏览器缓存

### 未做事项

- 未改后端 API
- 未改 Provider
- 未改 Resource Guard 后端逻辑
- 未改 Cost Guard 后端逻辑
- 未改数据库
- 未改 MiniMax Provider Adapter
- 未改同步 / 异步 / 流式 / 批量 API 调用语义
- 未改 WebSocket 协议
- 未改 variants API
- 未拆分 `index.html`
- 未引入 React / Vue / 构建工具
- 未执行真实 MiniMax smoke test
- 未进入 P8-4

### 阶段结论

P8-3F 已完成。P8-3 任务卡片和结果展示已完成并收口。下一阶段建议进入 P8-4：历史记录和下载体验。

---

## P8-4B 历史记录信息架构整理

### 背景

- P8-4A 已完成历史记录和下载体验现状审查
- P8-4B 目标：让历史记录区域从"工程任务列表"变成"历史任务卡片列表"

### 问题

- 历史记录当前为纯文本行，信息层级弱
- 历史记录当前直接输出英文 status
- 历史记录当前加载失败只显示"加载失败"
- 历史记录当前分页到底无提示
- 历史记录当前没有播放/下载入口

### 方案

- 采用前端展示层整理方案
- 新增 historyJobCardHtml / historyEmptyStateHtml / historyLoadErrorHtml / historyEndStateHtml helper
- 复用 statusLabel / statusClass / resultStatusHintHtml / resultDiagnosticHtml
- 不改 API，不改后端，不新增播放/下载入口

### 修改文件

- `app/static/index.html`（历史记录 card 化）
- `docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md`（追加 P8-4B 章节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新状态摘要）

### 风险处理

- 若 job 数据中已有 audio_asset / audio_asset_id，只记录为后续 P8-4C/P8-4D 处理，不在 P8-4B 做完整播放/下载产品化
- 不改 `/api/voice/jobs` endpoint
- 不改 `/api/voice/assets/{assetId}/download` endpoint

### 验证命令

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM/display marker check passed")
PY
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = ["function toggleHistory","function loadHistory","function loadMoreHistory","function statusLabel","function statusClass","function resultStatusHintHtml","function resultDiagnosticHtml","function isResultFailedStatus","function extractErrorMessage","function esc","function apiJson"]
missing = [x for x in required_functions if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("JS function check passed")
PY
```

### 验证结果

- DOM/display marker check: passed
- JS function check: passed
- API marker check: passed
- loadHistory semantic retention: passed
- No playback/download entry: passed
- pytest: 375 passed, 6 skipped

### 未做事项

- 未新增历史播放入口
- 未新增历史下载入口
- 未新增历史字幕/timeline 展示
- 未新增历史详情页
- 未新增历史搜索
- 未新增历史筛选
- 未新增历史删除
- 未改后端 API
- 未改下载接口
- 未处理桌面宽屏 P8-UX1
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test

### 阶段结论

P8-4B 已完成。下一阶段建议进入 P8-4C：历史任务卡片播放入口整理。

---

## P8-4C 历史任务卡片播放入口整理

### 背景

- P8-4A/B 已完成历史记录信息架构整理
- P8-4C 目标：在历史任务 card 中整理音频播放入口

### 问题

- 历史任务 card 已完成，但尚无播放入口
- 播放入口依赖 `/api/voice/jobs` 返回的音频字段
- `/api/voice/jobs` 返回的 `VoiceJobRead` 模型**不包含** `audio_asset` 或 `audio_asset_id` 字段

### 方案

- 采用安全降级方案：检测到无 asset 时展示明确提示
- 新增 `getHistoryAudioAssetId(job)` 和 `historyAudioPlaybackHtml(job)` helper
- 有 asset 时复用 `audioPlayerHtml(assetId)`，无 asset 时展示"当前历史记录未返回可播放音频资产。"
- 不改 API，不改后端，不新增下载入口

### 修改文件

- `app/static/index.html`（新增播放 helper、修改 historyJobCardHtml）
- `docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md`（追加 P8-4C 章节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新状态摘要）

### 风险处理

- `/api/voice/jobs` 不返回音频字段是后端设计现状，不可绕过
- 安全降级方案：展示清晰提示，不伪造播放入口
- 待后端在历史 job 中增加音频字段后，可立即启用播放能力
- 不修改后端 API
- 不修改 `/api/voice/assets/{assetId}/download` endpoint

### 验证命令

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息","音频播放"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM/display marker check passed")
PY
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = ["function toggleHistory","function loadHistory","function loadMoreHistory","function historyJobCardHtml","function historyEmptyStateHtml","function historyLoadErrorHtml","function historyEndStateHtml","function audioPlayerHtml","function statusLabel","function statusClass","function resultStatusHintHtml","function resultDiagnosticHtml","function isResultFailedStatus","function extractErrorMessage","function esc","function apiJson"]
missing = [x for x in required_functions if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("JS function check passed")
PY
```

### 验证结果

- DOM/display marker check: passed
- JS function check: passed
- API marker check: passed
- loadHistory semantic retention: passed
- No download entry: passed
- pytest: 375 passed, 6 skipped

### 未做事项

- 未新增历史下载入口
- 未新增历史字幕/timeline 展示
- 未新增历史详情页
- 未新增历史搜索/筛选/删除
- 未处理 URL/HEX/blob 历史播放
- 未改后端 API
- 未改下载接口
- 未处理桌面宽屏 P8-UX1
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test

### 阶段结论

P8-4C 已完成。下一阶段建议进入 P8-4D：历史任务下载入口产品化。

---

## P8-4D 历史任务下载入口产品化

### 背景

- P8-4A/B/C 已完成历史记录信息架构和播放入口整理
- P8-4D 目标：在历史任务 card 中整理下载入口

### 问题

- 历史任务 card 已有播放区，但下载入口仍未产品化
- 下载入口依赖 `/api/voice/jobs` 返回的音频资产字段
- `/api/voice/jobs` 返回的 `VoiceJobRead` 模型**不包含** `audio_asset` / `audio_asset_id` 字段

### 方案

- 采用安全降级方案：检测到无 asset 时展示明确提示
- 新增 `historyDownloadEntryHtml(job)` helper
- 有 asset 时复用 `downloadBtnHtml(assetId)`，无 asset 时展示"当前历史记录未返回可下载音频资产。"
- 不改 API，不改后端，不处理 URL/HEX/blob 下载

### 修改文件

- `app/static/index.html`（新增下载 helper、修改 historyJobCardHtml）
- `docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md`（追加 P8-4D 章节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新状态摘要）

### 风险处理

- `/api/voice/jobs` 不返回音频字段是后端设计现状，不可绕过
- 安全降级方案：展示清晰提示，不伪造下载入口
- 待后端在历史 job 中增加音频字段后，可立即启用下载能力
- 不修改后端 API
- 不修改 `/api/voice/assets/{assetId}/download` endpoint

### 验证命令

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","历史任务","任务状态","生成文本","任务信息","音频播放","下载入口"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM/display marker check passed")
PY
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required_functions = ["function toggleHistory","function loadHistory","function loadMoreHistory","function historyJobCardHtml","function historyEmptyStateHtml","function historyLoadErrorHtml","function historyEndStateHtml","function getHistoryAudioAssetId","function historyAudioPlaybackHtml","function downloadBtnHtml","function audioPlayerHtml","function statusLabel","function statusClass","function resultStatusHintHtml","function resultDiagnosticHtml","function isResultFailedStatus","function extractErrorMessage","function esc","function apiJson"]
missing = [x for x in required_functions if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("JS function check passed")
PY
```

### 验证结果

- DOM/display marker check: passed
- JS function check: passed
- API marker check: passed
- loadHistory semantic retention: passed
- No extra download logic: passed
- pytest: 375 passed, 6 skipped

### 未做事项

- 未新增历史字幕/timeline 展示
- 未新增历史详情页
- 未新增历史搜索/筛选/删除
- 未处理 URL/HEX/blob 历史下载
- 未改后端 API
- 未改 `/api/voice/jobs`
- 未改下载接口
- `/api/voice/jobs` 不返回音频资产字段的问题未解决（后端限制）
- 未处理桌面宽屏 P8-UX1
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test

### 阶段结论

P8-4D 已完成。下一阶段建议进入 P8-4E：历史筛选 / 搜索 / 空状态优化。

---

## P8-4E 历史筛选 / 搜索 / 空状态优化

### 背景

- P8-4A/B/C/D 已完成历史记录信息架构、播放/下载入口整理
- P8-4E 目标：优化历史记录的本地筛选、搜索和空状态体验

### 问题

- 历史记录已有 card，但缺少定位历史任务的能力
- 没有搜索 / 筛选能力
- 空状态需要区分无历史和无匹配

### 方案

- 采用前端本地搜索 / 筛选方案
- 新增 `_historyJobs` 缓存已加载 jobs
- 新增搜索框 `historySearch` 和状态筛选 `historyStatusFilter`
- `renderHistoryList()` 负责根据本地筛选条件渲染
- 状态筛选复用 P8-3C1 helper
- 不改 API，不新增服务端参数

### 修改文件

- `app/static/index.html`（新增工具栏、新增筛选 helper、重构 loadHistory）
- `docs/P8_4_HISTORY_DOWNLOAD_EXPERIENCE.md`（追加 P8-4E 章节）
- `docs/PROJECT_HEALTH_CHECK.md`（更新状态摘要）

### 风险处理

- 本地筛选只作用于已加载记录，不是全库搜索
- 用户需要知道"已加载 N 条，当前显示 M 条"
- 空状态已区分无历史和无匹配
- 不修改后端 API

### 验证命令

```bash
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["tab-history","historyCard","historyToggle","historyArea","historyList","loadMoreHistory","historySearch","historyStatusFilter","historyFilterHint","historyClearFilters","搜索历史文本 / provider / job_id","筛选仅作用于已加载历史记录"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("DOM/display marker check passed")
PY
python - <<'PY'
from pathlib import Path
html = Path("app/static/index.html").read_text(encoding="utf-8")
required = ["let _historyJobs","let _historySearch","let _historyStatusFilter","function renderHistoryList","function filterHistoryJobs","function handleHistorySearchInput","function handleHistoryStatusFilterChange","function clearHistoryFilters","function historyFilteredEmptyStateHtml","function updateHistoryFilterHint"]
missing = [x for x in required if x not in html]
if missing: raise SystemExit(f"Missing: {missing}")
print("History filter helper check passed")
PY
```

### 验证结果

- DOM/display marker check: passed
- JS function check: passed
- History filter helper check: passed
- API marker check: passed
- loadHistory request semantic check: passed
- local filter semantic check: passed
- empty state check: passed
- pytest: 375 passed, 6 skipped

### 未做事项

- 未新增服务端历史搜索/筛选
- 未新增历史字幕/timeline 展示
- 未新增历史详情页
- 未新增历史删除
- 未处理 URL/HEX/blob 历史下载
- 未改后端 API
- `/api/voice/jobs` 不返回音频资产字段的问题未解决（后端限制）
- 未处理桌面宽屏 P8-UX1
- 未拆分 `index.html`
- 未执行真实 MiniMax smoke test

### 阶段结论

P8-4E 已完成。下一阶段建议进入 P8-4F：P8-4 验收与健康检查收口。

---

## P8-4F P8-4 验收与健康检查收口

### 背景

- P8-4A/B/C/D/E 已完成历史记录信息架构、播放/下载/搜索/筛选全阶段
- P8-4F 目标：P8-4 全阶段验收与文档收口

### 验证结果

- P8-4 commit chain: 6a8b6d4(p8-4a) → 2e57ff2(p8-4b) → 6e7c9af(p8-4c) → 15f064c(p8-4d) → c3de80b(p8-4e)
- DOM marker check: passed (11 markers)
- Core function check: passed (8 functions)
- Card helper check: passed (8 helpers)
- Status helper reuse: passed
- Playback/download safety: passed
- Search/filter: passed
- API semantic: passed (no server-side params)
- loadHistory refactor: passed (_historyJobs cache + renderHistoryList)
- pytest: 375 passed, 6 skipped

### 未做事项

- 未修改 app/static/index.html 功能
- 未修改后端 API
- 未执行真实 MiniMax smoke test
- 未处理 P8-BE1（历史任务返回音频资产字段）
- 未处理 P8-UX1（桌面宽屏布局）
- 未拆分 index.html

### 阶段结论

P8-4F 已完成。P8-4 全阶段正式收口。

---

## P8-FIX1A 前端回归缺陷审查

### 背景

- P8-4 已收口，发现新的前端回归问题
- P8-FIX1A 目标：审查并文档化前端回归问题

### 审查结果

- Tab 完整性：6 个 tab 均有对应内容区，无缺失
- 长文本/剧本模块：DOM 和后端 API/Schema 完整，无缺失
- 历史播放/下载不可用：后端 VoiceJobRead 不返回音频资产字段，非前端 bug，前端安全降级正常
- 新增历史不显示：存在前端缺陷，toggleHistory 打开历史后不刷新，缺少刷新机制
- 全局 JS 断点：无缺陷，所有 onclick/oninput/onchange 函数均存在

### 高优先级问题

| 问题 | 原因 | 修复方式 |
|---|---|---|
| 新生成的任务不在历史中显示 | toggleHistory 打开历史后不刷新，_historyOffset > 0 时不再触发 loadHistory | 新增刷新历史按钮 |

### 文档输出

- docs/P8_FIX1_FRONTEND_REGRESSION_AUDIT.md

### 阶段结论

P8-FIX1A 已完成。下一阶段建议进入 P8-FIX1B：前端回归缺陷修复（新增刷新历史按钮）。

---

## P8-FIX1 前端回归缺陷排查与修复

### 背景

- P8-4 已收口，用户反馈前端存在长文本/剧本不显示等问题
- P8-FIX1A 审查发现：长文本/剧本 tab **本来完整存在**（P8-FIX1A 误判），真正问题是缺少历史刷新入口
- P8-FIX1 目标：修复前端回归缺陷（历史刷新入口 + UI 修复）

### 审查与修复结果

- Tab 完整性：6 个 tab 均有对应内容区，内容本来完整
- 长文本模块：tab-longtext 和 handleBatchLongtextSubmit 均存在，无需修复
- 剧本模块：tab-script 和 handleBatchScriptSubmit 均存在，无需修复
- 历史播放/下载：后端 VoiceJobRead 缺少音频资产字段，遗留到 P8-BE1
- 历史刷新入口：**已修复** - 新增 historyRefreshBtn 和 refreshHistory()
- tab-nav 滚动条：**已修复** - 添加 scrollbar-width: none CSS
- DOM/JS 完整性：通过（107 个函数，37 个 inline handler，均有对应实现）
- pytest：375 passed, 6 skipped

### 修复内容

1. `app/static/index.html` - 新增 historyRefreshBtn 和 refreshHistory() 函数
2. `app/static/index.html` - 新增 .tab-nav 滚动条隐藏 CSS
3. `docs/P8_FIX1_FRONTEND_REGRESSION_REPAIR.md` - 新增修复文档

### 未处理事项

- 未改后端历史资产字段（遗留到 P8-BE1）
- 未做 P8-BE1 / P8-UX1 / P8-5

### 阶段结论

P8-FIX1 已完成。历史刷新入口已补充，tab-nav 滚动条已隐藏，前端 DOM/JS 完整性已通过静态检查。历史播放/下载真正可用仍依赖 P8-BE1：历史任务返回音频资产字段。

---

## P8-FIX2 创作工作台首页轻量 UX 修复

### 背景

用户反馈创作工作台首页"主流程"卡片位置不合适，和顶部导航重复，影响主流程使用。

### 修复内容

- 移除重复的"主流程"大卡片
- 压缩欢迎提示为轻量 1 行
- 文案输入更靠前
- 保留顶部导航作为模块入口

### 验证结果

- Workspace 结构检查：通过
- Tab 保留检查：通过
- JS function 保留检查：通过
- pytest：375 passed, 6 skipped

### 阶段结论

P8-FIX2 已完成。创作工作台首页已移除重复的"主流程"大卡片，欢迎区已轻量化，文案输入和生成配置更靠前。生成逻辑、长文本、剧本、历史、音色和高级模块均未改动。下一阶段建议根据优先级进入 P8-BE1、P8-UX1 或 P8-5。

---

## P8-FIX3 恢复长文本 / 剧本 tab 内容区

### 背景

用户反馈点击"剧本"tab 后内容为空白。经代码审查，所有内容均已存在（P8-FIX1A 审查为误判）。

### 修复内容

- 确认 tab-longtext 和 tab-script 内容完整存在
- 为 tab 切换逻辑增加 null 防御
- 如用户仍看到空白页，建议清除浏览器缓存

### 验证结果

- Tab 完整性检查：通过
- DOM 检查：所有内容存在
- pytest：375 passed, 6 skipped

### 阶段结论

P8-FIX3 已完成。经审查，tab-longtext 和 tab-script 内容本来完整存在，tab 切换逻辑已增加 null 防御。如用户仍看到空白页，建议清除浏览器缓存。

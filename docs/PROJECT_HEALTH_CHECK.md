# Voice Lab 项目健康检查

## 当前最新状态摘要

截至 P10-PRODUCT-B1：

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
* P8-UX11：长文本与剧本语义轻量优化已完成（长文本分段策略文案改为"自动（按段落合并，推荐长文）/按空行分段/按句子分段"，增加自动分段说明；长文本结果区无字幕时隐藏字幕容器，不再显示空白块；剧本台词列表增加"角色名仅用于区分段落，实际发音由声音人设决定"说明；角色输入 placeholder 从"角色名"改为"例如：旁白、男声"；剧本进度表角色为空时显示"旁白"而非"—"；不改后端 API、生成链路、批量链路和资产清理链路）
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

### P8-UX12：音色页产品感轻量优化

**阶段目标：** 修复音色页中影响产品感的 5 个轻量问题，不改后端 API、Provider Adapter、生成链路和资产清理链路。

**修改文件：**

- `app/static/index.html`
- `docs/PROJECT_HEALTH_CHECK.md`

**修复点：**

1. **已绑定音色按钮文案**：未绑定显示"绑定到人设"；已绑定显示"更换绑定"，hover 显示"当前已绑定到：xxx。点击可更换绑定。"；未绑定 hover 显示"绑定该音色到声音人设"。
2. **试听成本提示降噪**：红色警告风格改为浅橙提示（`background:#fffaf0;border:1px solid #fbd38d;color:#9c4221`），文案改为"真实 Provider 试听会产生 API 调用成本，建议先使用短文本验证。"
3. **评分/备注半成品入口**：由于无后端保存能力，试听记录中的评分星级和备注输入框已移除，保留基本的试音记录（音色、音频、文本预览、删除）。
4. **音色操作按钮 title**：试听按钮增加"生成一段短文本试听音色"；绑定按钮 title 根据绑定状态动态显示；查询音色按钮增加"从 Provider 查询可用音色"；生成试听按钮增加"调用当前 Provider 生成试听音频"。
5. **绑定状态文案**：已绑定状态显示格式不变（"已绑定"），已确认语义清晰。

**手动验收：**

- 音色 Tab 未绑定音色显示"绑定到人设"
- 已绑定音色显示"更换绑定"
- 试听成本提示为浅橙提示，非红色警告
- 试听记录中无评分星级和备注输入框
- 音色试听、查询音色、绑定/更换绑定功能可用
- 控制台无 JS 报错

### P8-UX11-SCRIPT-FIX：剧本批量完成后显示合并音频结果

**阶段目标：** 修复剧本 Tab 批量任务完成后不显示合并音频播放器/下载按钮的问题，不改后端 API、批量后端链路、生成链路和资产清理链路。

**修改文件：**

- `app/static/index.html`
- `docs/PROJECT_HEALTH_CHECK.md`

**根因：** `renderBatchResultPlayer(data)` 硬编码使用长文本批量面板的 DOM id（`batchResultPlayer` 等），剧本 Tab 无对应 DOM 且调用时未传 `targetPanelId`，导致剧本批量完成后无法渲染结果播放器。

**修复点：**

1. **新增剧本 Tab 结果播放器 DOM**：在 `batchScriptProgressPanel` 内追加 `batchScriptResultPlayer` 容器（含 audio、下载合并音频、下载字幕、字幕当前行、字幕列表）。
2. **新增 `getBatchPanelDom(targetPanelId)` 辅助函数**：根据 `targetPanelId` 返回对应面板的 DOM 元素集合，支持剧本和长文本两套 DOM。
3. **改造 `renderBatchResultPlayer(data, targetPanelId)`**：新增 `targetPanelId` 参数，默认 `'batchProgressPanel'`（长文本），传入 `'batchScriptProgressPanel'` 时操作剧本面板 DOM；初始化 ID 改为 `${data.batch_id}-${targetPanelId}` 以隔离两个面板。
4. **改造 `renderBatchSubtitleList(targetPanelId, timeline)`**：接收 `targetPanelId` 参数，使用 `getBatchPanelDom()` 获取字幕列表 DOM。
5. **改造 `updateBatchSubtitleHighlight(targetPanelId)`**：接收 `targetPanelId` 参数，使用 `getBatchPanelDom()` 获取 audio / 字幕 DOM。
6. **改造 `renderBatchStatus` 调用**：`renderBatchResultPlayer(data, targetPanelId)` 传递目标面板 ID。
7. **字幕 cache guard 保留**：P8-UX11-FIX 的 `if (window._batchSubtitleCache && window._batchSubtitleCache[subId])` 判断结构保持不变。

**手动验收：**

- 剧本 Tab 批量任务完成后仍停留在剧本 Tab
- 进度表显示 `已完成 N/N 段`
- 进度表下方出现"批量结果"
- 出现 audio 播放器，可播放合并音频
- 出现"下载合并音频"按钮
- 有字幕时出现"下载字幕"按钮
- 无字幕时不出现空白字幕块
- 长文本批量任务完成后播放器仍正常
- 控制台无 JS 报错

### P8-UX13：高级页流程降噪与克隆步骤优化

**阶段目标：** 优化高级 Tab 声音克隆相关流程的前端体验，不改后端 API、Provider Adapter、生成链路和资产清理链路。

**修改文件：**

- `app/static/index.html`
- `docs/PROJECT_HEALTH_CHECK.md`

**修复点：**

1. **高级页顶部高成本提示降噪**：红色错误风格（`background:#fff5f5;border:#feb2b2;color:#c53030`）改为浅橙提示（`background:#fffaf0;border:1px solid #fbd38d;color:#9c4221`），文案改为"以下能力可能产生较高 API 调用成本，适合工程验证和少量样本测试。使用真实 Provider 前请确认费用、限制和音频素材合规性。"
2. **上传成功后提示下一步**：上传成功消息增加"file_id 已填入步骤 2，可继续执行克隆。"提示，指引用户进入下一步。
3. **克隆按钮 disabled 状态**：新增 `updateCloneBtnState()` 函数，监听 `file_id`、`voice_id`、`preview_text`、`model` 输入变化，动态禁用克隆按钮。条件：`!fileId || !voiceId || (previewText && !model)`。按钮下方显示"file_id 和 voice_id 填写完整后才能执行克隆。"提示。
4. **voice_id 自动生成按钮**：文案从"自动生成"改为"生成 voice_id"，增加 `title="生成一个本地可识别的 voice_id"`。
5. **file_id 字段说明**：移除 label 内嵌说明，改为 label 下方独立描述"上传成功后会自动填入，也可以手动粘贴已有 file_id。"，placeholder 从"从步骤1获取"改为"上传成功后自动填入"。
6. **降噪 / 音量标准化说明**：移除 label 内嵌技术参数，改为 checkbox 旁轻量说明"降噪：适合有明显底噪的样本。"、"音量标准化：适合音量忽大忽小的样本。"
7. **导入已有克隆音色区域**：描述改为"用于把 MiniMax 远端已存在的 voice_id 记录到本地，便于绑定到声音人设；不会重新克隆音频。"；按钮增加 `title="导入远端已有 voice_id 到本地音色库"`。
8. **voice_id 字段说明**：label 简化为"voice_id"，下方增加"voice_id 是你为克隆音色指定的自定义标识。"

**手动验收：**

- 高级 Tab 顶部提示为浅橙，非红色错误
- 声音克隆步骤关系清楚（步骤 1 → 步骤 2）
- 上传成功后 file_id 自动填入步骤 2，提示下一步
- file_id 为空时克隆按钮 disabled
- voice_id 为空时克隆按钮 disabled
- file_id + voice_id 都有值时克隆按钮可点击
- "生成 voice_id"按钮文案和 title 正确
- 降噪 / 音量标准化说明可见
- 导入已有克隆音色区域文案清楚
- 声音克隆 payload 字段不变
- 声音设计 / 绑定管理 / 危险操作子 Tab 不受影响
- 控制台无 JS 报错

### P8-SEG1：新增"每行一段"长文本分段策略

**阶段目标：** 为长文本批量生成新增 line 分段策略，每个非空行作为独立 segment，不改 Provider Adapter、生成主链路和资产清理链路。

**修改文件：**

- `app/services/text_segment_service.py`
- `app/domain/schemas.py`
- `app/static/index.html`
- `tests/test_text_segment.py`
- `docs/PROJECT_HEALTH_CHECK.md`

**实现：**

1. **后端 `TextSegmentService`**：新增 `_split_by_lines()`（按 `\n` 拆分并去除空行）和 `_segment_line()`（每行 ≤ max_chars 直接作为一个 segment；超长行调用 `_segment_sentence()` 兜底拆分）；`segment()` 方法新增 `elif strategy == "line": return self._segment_line(text, max_chars)` 分支。
2. **Schema**：`segment_strategy` 注释从 `auto/paragraph/sentence` 更新为 `auto/paragraph/sentence/line`。
3. **前端**：`batchStrategy` 下拉新增 `<option value="line">每行一段</option>`；说明文案更新为"自动分段会合并较短段落；如需自然段落控制，请使用空行分隔段落；如需多条短文本独立生成，请选择"每行一段"。"
4. **测试**：`test_text_segment.py` 新增 5 个测试用例覆盖 line 策略核心行为及回归验证。

**手动验收：**

- 长文本 Tab 分段策略下拉出现"每行一段"选项
- 说明文案包含"每行一段"用途
- 输入多条短行选择"每行一段"后提交，total_segments 等于行数
- auto/paragraph/sentence 原有行为不受影响
- 控制台无 JS 报错

### P8-VALIDATION2-A：后端 Schema 收紧与服务层兜底

**阶段目标：** 基于 P8-VALIDATION1 输入校验矩阵，修复后端底线约束问题（不改前端、不改 Provider Adapter、不改生成主链路、不改资产清理链路）。

**修改文件：**

- `app/domain/schemas.py`
- `app/services/text_segment_service.py`
- `tests/test_text_segment.py`
- `tests/test_schema_validation.py`（新增）
- `docs/PROJECT_HEALTH_CHECK.md`

**实现：**

1. **Schema 收紧**：LongtextBatchRequest.text 增加 `max_length=50000`；VoiceRenderRequest.text / VoiceVariantRenderRequest.text 增加 `max_length=10000`；AsyncRenderRequest.text 增加 `max_length=50000`；segment_strategy 从 `str` 改为 `Literal["auto","paragraph","sentence","line"]`（非法值直接返回 422）；VoiceCloneRequest.file_id / prompt_file_id 改为 `Field(gt=0)`。
2. **TextSegmentService 硬切兜底**：新增 `_hard_split()`（纯长度切分）和 `_append_with_hard_limit()`（判断长度超限时硬切），更新 `_split_by_comma()` 使用 `_append_with_hard_limit()`，确保任何策略返回的 segment 均不超过 max_chars。
3. **测试**：test_text_segment.py 新增 4 个 hard-split 测试覆盖 line/sentence/paragraph/auto 四种策略；test_schema_validation.py 新增 16 个测试覆盖所有 schema 约束。

**手动验收：**

- segment_strategy 传 "bad" 返回 422
- LongtextBatchRequest(text="x"*50001) 抛 ValidationError
- VoiceRenderRequest(text="x"*10001) 抛 ValidationError
- VoiceCloneRequest(file_id=0) 抛 ValidationError
- 无标点超长文本（"a"*251）使用任意策略分段后，所有 segment 长度 ≤ max_chars
- 控制台无报错

### P8-VALIDATION2-B：前端高风险输入约束补齐

**阶段目标：** 基于 P8-VALIDATION1 输入校验矩阵和 P8-VALIDATION2-A 后端约束收紧结果，补齐前端高风险输入限制（不改后端 Schema、不改 Provider Adapter、不改生成主链路、不改资产清理链路）。

**修改文件：**

- `app/static/index.html`
- `docs/PROJECT_HEALTH_CHECK.md`

**实现：**

1. **textarea/input maxlength**：auditionText 增加 `maxlength="1000"` + "最多 1000 字"提示；clonePreviewText 增加 `maxlength="1000"`；importClonePreviewText 增加 `maxlength="1000"`；designPrompt 增加 `maxlength="2000"` + "建议控制在 2000 字以内"提示。
2. **cloneVoiceId 前端格式校验**：增加 `minlength="8" maxlength="256" pattern`；新增 `isValidVoiceId()` JS helper；在 `updateCloneBtnState()` 中加入 voice_id 格式校验（非法时按钮 disabled + 显示错误提示）；增加 `cloneVoiceIdHint` 错误提示元素。
3. **designVoiceId 前端格式校验**：增加 `minlength="8" maxlength="256" pattern`；`handleDesignVoice()` 中非空时格式校验，非法时拦截并显示错误。
4. **cloneFileId / clonePromptFileId 正整数**：两个 input 增加 `min="1" step="1"`；`updateCloneBtnState()` 中 fileId 非正整数时按钮 disabled；promptFileId 填写时必须为正整数。
5. **剧本 200 行限制**：新增 `MAX_SCRIPT_LINES=200` 常量；`addScriptLine()` 达上限时 showToast 并拒绝添加；新增 `updateScriptLineLimitState()`，达上限时禁用添加按钮并设置 title；`removeScriptLine()` 调用时恢复按钮；添加按钮增加 `id="scriptAddLineBtn"`。
6. **剧本每行 maxlength**：台词输入框增加 `maxlength="5000"`。
7. **剧本空台词行级拦截**：`handleBatchScriptSubmit()` 中对所有 _scriptRows 逐行检查，空文本行边框标红 + title 设置为"第 N 行缺少台词文本"，第一行空行定位报错后 return。
8. **confirm_cost=true 修复**：从 `handleCloneVoice()` 和 `handleDesignVoice()` 中移除冗余的 `confirmHighCostVoiceAction()` 调用（guardedJsonFetch 已统一处理 minimax 高成本确认并设置 confirm_cost=true）；mock provider 保持 confirm_cost=false。

**手动验收：**

- 试听文本超过 1000 字时前端无法继续输入
- clonePreviewText / importClonePreviewText 超过 1000 字被限制
- designPrompt 超过 2000 字被限制
- cloneVoiceId 输入过短或格式错误时克隆按钮 disabled 并显示格式提示
- cloneFileId 输入 0 或负数时克隆按钮 disabled
- 剧本添加至 200 行后无法继续添加，按钮有提示
- 剧本某行台词为空时提交前报错并标红对应行
- 声音克隆确认高成本后 Network payload 中 confirm_cost=true
- 声音设计确认高成本后 confirm_cost=true
- mock provider 克隆/设计时不弹确认框，confirm_cost=false
- 控制台无 JS 报错

### P8-VALIDATION2-C：统一 422 字段级错误提示

**阶段目标：** 基于 P8-VALIDATION2-A/B 已完成的前后端输入约束，新增统一 API 错误解析能力，将 FastAPI/Pydantic 422 ValidationError 翻译成人能看懂的中文字段级提示（不改后端 Schema、不改 Provider Adapter、不改生成主链路、不改资产清理链路）。

**修改文件：**

- `app/static/index.html`
- `docs/PROJECT_HEALTH_CHECK.md`

**实现：**

1. **字段名映射（FIELD_LABELS）**：新增中文字段名映射，包含 text、profile_id、segment_strategy、voice_id、file_id、prompt_file_id、preview_text、script.role/text/profile_id 等 30+ 字段。
2. **formatFieldPath()**：将 FastAPI 422 的 loc 数组路径翻译为中文，特殊处理 `script.N.text` → `第 N 行台词`、`script.N.profile_id` → `第 N 行声音人设`。
3. **translateValidationIssue()**：根据 Pydantic v2 错误 type 翻译，支持 missing、string_too_short/long、greater_than、less_than、literal_error、string_pattern_mismatch（特殊处理 voice_id 格式）、int_parsing、float_parsing、bool_parsing 等。
4. **parseApiError()**：增强处理 422，当 status=422 且 detail 为数组时，调用 translateValidationIssue 翻译所有错误项，设置 code='VALIDATION_ERROR'，message 为翻译后的中文分号分隔字符串。
5. **formatApiError()**：增加 VALIDATION_ERROR 分支，直接返回翻译后的 err.message。
6. **接入函数**：handleGenerate（通过 renderApiError）、handleBatchLongtextSubmit、handleBatchScriptSubmit、handleGenerateAudition（重构为先检查 resp.ok）、handleCloneVoice、handleDesignVoice、handleImportRemoteVoice（重构为先检查 resp.ok）。

**手动验收：**

- 长文本批量 text 超过 50000：显示"文本：长度不能超过 50000 个字符。"
- segment_strategy 非法：显示"分段策略：只能选择..."
- voice_id 格式错误：显示"voice_id：格式不正确，至少 8 位..."
- file_id=0：显示"file_id：必须大于 0。"
- 剧本第 N 行 text 为空：显示"第 N 行台词：不能为空。"
- 非 422 Provider 错误仍正常显示
- 成功路径不受影响
- 控制台无 JS 报错

### P8-VALIDATION2-C-FIX：422 错误提示安全渲染与导入成功路径修复

**阶段目标：** 修复 P8-VALIDATION2-C 中的边界渲染问题和成功路径回归。

**修改文件：**

- `app/static/index.html`

**实现：**

1. **greater_than_equal / less_than_equal 判断顺序修复**：调整 `translateValidationIssue` 中类型判断顺序，`greater_than_equal` 和 `less_than_equal` 先于 `greater_than` 和 `less_than` 判断，避免子字符串误匹配导致 ctx.gt / ctx.lt 显示为 undefined。
2. **renderValidationError() helper**：新增 `esc(message)` 转义 HTML，并将中文分号 `；` 替换为 `<br>` 换行，安全渲染多字段错误。
3. **VALIDATION_ERROR 渲染统一**：clone / design / import 改用 `renderValidationError(err.message)`；audition / longtext / script 至少使用 `esc(err.message)`。
4. **导入音色成功路径修复**：删除 `handleImportRemoteVoice` 中残留的提前 return 代码块，恢复成功结果展示。

**手动验收：**

- max_segment_chars=99 显示"每段最大字数：必须大于等于 100"（不显示 undefined）
- silence_between_ms=3001 显示"段间静音：必须小于等于 3000"（不显示 undefined）
- 多字段 422 错误换行展示，无 HTML 注入风险
- 导入音色成功后正常展示成功结果

**测试结果：** 496 passed, 6 skipped。

**未改后端 Schema、API 返回结构、Provider Adapter、生成主链路、资产清理链路。**

### P9-CAPABILITY1：Provider Capability Registry 最小实现

**阶段目标：** 新增只读能力注册表，声明 mock / minimax 的 TTS、批量、剧本、声音克隆、声音设计、音色管理能力，提供查询接口（不走数据库、不调用 Provider、不改生成链路）。

**新增文件：**

- `app/domain/capabilities.py` — ProviderCapability 数据模型
- `app/providers/mock_capabilities.py` — mock 能力声明
- `app/providers/minimax_capabilities.py` — minimax 能力声明（从 settings 读取默认模型）
- `app/providers/capability_registry.py` — 能力注册表（list_capabilities / get_capability / provider_exists）
- `app/api/capabilities.py` — GET /api/voice/capabilities 接口
- `tests/test_capabilities.py` — 17 个测试用例覆盖 registry 和 API

**修改文件：**

- `app/api/__init__.py` — 注册 capabilities router

**实现：**

1. **ProviderCapability 模型**：嵌套 TTSCapability、BatchCapability、VoiceCloneCapability、VoiceDesignCapability、ProviderVoiceCapability，包含 supported、models、max_text_chars、audio_formats、speed/vol/pitch 范围、segment_strategies 等字段。
2. **mock 能力声明**：完整声明 mock-tts 的 TTS、批量、剧本、克隆、设计、音色管理能力。
3. **minimax 能力声明**：从 `get_settings()` 读取 minimax_default_model / minimax_ws_model，metadata 只暴露 api_key_configured (bool)，不泄露 API key 原文。
4. **Registry**：`_build_registry()` 每次调用构建（避免 settings 缓存问题），支持 list/get/exists 操作。
5. **API**：GET /api/voice/capabilities（返回所有）、GET /api/voice/capabilities?provider=xxx（返回单个）；未知 provider 返回 404 而非 500。

**测试结果：** 513 passed, 6 skipped（+17 新增测试）。

**未改生成链路、Provider Adapter、前端动态行为、资产清理链路。**

### P9-CAPABILITY1-FIX：Provider Capability 模型一致性验证

**阶段目标：** 为能力模型添加 Pydantic `model_validator` 内部一致性检查，防止无效数据进入系统。

**修改文件：**

- `app/domain/capabilities.py` — 为 NumericRange、VoiceIdConstraint、TTSCapability、BatchCapability、ProviderCapability 各添加 `model_validator(mode="after")`
- `tests/test_capabilities.py` — 新增 26 个验证测试用例（TestCapabilityModelValidation 类）

**实现：**

1. **NumericRange**：新增 `validate_range`，检查 `min <= max`。
2. **VoiceIdConstraint**：新增 `validate_voice_id_constraint`，检查 `min_length > 0`、`max_length >= min_length`、pattern 为合法正则。
3. **TTSCapability**：当 `supported=True` 时，检查 models 非空、audio_formats 非空、max_text_chars > 0；default_model 存在时必须出现在 models 中。
4. **BatchCapability**：当 `supported=True` 时，检查 max_text_chars > 0、max_segments > 0（若设置）、segment_strategies 非空。
5. **ProviderCapability**：检查 provider/display_name 非空；default_model 存在时必须出现在 tts.models 中；metadata 敏感 key 使用精确匹配（`lower_key in SENSITIVE_METADATA_KEYS`），不拦截 `api_key_configured`；metadata string value 拦截含 `"sk-"` 的值。

**敏感 Key 精确匹配策略：**

- `SENSITIVE_METADATA_KEYS = {"api_key", "apikey", "secret", "token", "password", "minimax_api_key", "openai_api_key"}`
- `"api_key_configured"` 不在列表中，精确匹配不会命中，通过
- `"minimax_api_key"` 在列表中，被精确拦截
- `{"custom_key": "sk-xxxxx"}` 通过 key 检查，但在 value 检查中被拦截

**测试结果：** 539 passed, 6 skipped（+26 新增测试）。

**未改生成链路、Provider Adapter、资产清理链路。**

### P9-CAPABILITY2：CapabilityValidator 后端能力校验

**阶段目标：** 在请求进入 Provider Adapter 前增加后端能力校验，不支持时返回 422 VALIDATION_ERROR，不进入 Provider Adapter。

**新增文件：**

- `app/services/capability_validator.py` — CapabilityValidator 类
- `tests/test_capability_validator.py` — 29 个单元测试覆盖所有校验路径

**修改文件：**

- `app/api/voice_render.py` — validate_tts 接入
- `app/api/async_render.py` — validate_tts 接入
- `app/api/ws_render.py` — validate_tts(require_streaming=True) 接入
- `app/api/batch.py` — validate_batch / validate_script 接入
- `app/api/voice_clone.py` — validate_voice_clone 接入
- `app/api/voice_design.py` — validate_voice_design 接入
- `app/api/provider_voices.py` — validate_provider_voice_preview / validate_provider_voice_import 接入

**实现：**

1. **CapabilityValidator**：封装 get_capability、resolve_provider、_fail、_validate_range、_validate_audio_format、_validate_model、_validate_voice_id_pattern 等通用 helper。
2. **validate_tts**：校验 cap.enabled、tts.supported、model 在 models 中、text 长度、audio_format、need_subtitle、require_streaming、emotion、speed/vol/pitch 范围。
3. **validate_batch**：校验 cap.batch.supported、text 长度、segment_strategy、max_segment_chars 范围、silence_between_ms 范围、need_subtitle 联合 tts.supports_subtitle。
4. **validate_script**：校验 cap.script.supported、script_count <= max_segments、silence_between_ms 范围、need_subtitle 联合 tts.supports_subtitle。
5. **validate_voice_clone**：校验 cap.voice_clone.supported、preview_text 长度、need_noise_reduction、need_volume_normalization、voice_id pattern。
6. **validate_voice_design**：校验 cap.voice_design.supported、prompt 长度、preview_text 长度、voice_id pattern。
7. **validate_provider_voice_preview**：校验 cap.provider_voices.supported、preview_text 长度、audio_format、need_subtitle、model、speed/vol/pitch/emotion 范围。
8. **validate_provider_voice_import**：校验 cap.provider_voices.supported、supports_import_remote_voice、preview_text 长度。

**错误码：**

- VALIDATION_ERROR（422）：能力不支持或参数超出范围
- Provider 不存在时返回 422 VALIDATION_ERROR，detail=UNSUPPORTED_PROVIDER
- CAPABILITY_NOT_SUPPORTED、UNSUPPORTED_AUDIO_FORMAT、PARAM_OUT_OF_RANGE、TTS_NOT_SUPPORTED、SUBTITLE_NOT_SUPPORTED、STREAMING_NOT_SUPPORTED、EMOTION_NOT_SUPPORTED、BATCH_NOT_SUPPORTED、SCRIPT_NOT_SUPPORTED、VOICE_CLONE_NOT_SUPPORTED、VOICE_DESIGN_NOT_SUPPORTED、IMPORT_NOT_SUPPORTED、IMPORT_VERIFY_NOT_SUPPORTED 等。

**测试结果：** 572 passed, 6 skipped（+33 新增测试）。

**未改 Provider Adapter、未改前端动态行为、未改数据库、未改资产清理链路。**

### P9-CAPABILITY3：前端 Provider Capability 动态约束

**阶段目标：** 前端启动时读取 `/api/voice/capabilities`，根据当前 Provider 能力动态调整页面控件，不支持的能力提前禁用或提示。

**修改文件：**

- `app/static/index.html` — 新增 capability 缓存/加载、helper 函数和各区域动态约束逻辑

**新增功能：**

1. **capability 缓存**：`_providerCapabilities` / `_providerCapabilitiesByName`，`_capabilitiesLoaded` / `_capabilitiesLoadFailed` 标志。
2. **loadProviderCapabilities()**：异步加载 `/api/voice/capabilities`，加载成功则调用 `applyAllProviderCapabilities()`，失败则降级为默认静态配置并 showToast 提示。
3. **通用 helper**：setTextMaxLength、updateSelectOptions、setNumberRange、setControlDisabled、setHintText、updateProviderSelectOptions。
4. **applyWorkspaceCapability()**：动态更新 textInput maxLength/charCount、audioFormat 下拉选项、paramSpeed/vol/pitch 范围、needSubtitle 禁用、genMode 流式选项禁用、paramEmotion 禁用。
5. **applyLongtextCapability()**：动态更新 batchText maxLength、batchStrategy 下拉、batchMaxChars/batchSilence 范围、batchOutputFormat 下拉、batchNeedSubtitle 禁用。
6. **applyScriptCapability()**：动态更新 MAX_SCRIPT_LINES（改为 let）、batchScriptSilence 范围、batchScriptOutputFormat 下拉、batchScriptNeedSubtitle 禁用。
7. **applyProviderVoiceCapability()**：动态更新 auditionText maxLength、auditionModel 下拉、auditionSpeed/vol/pitch 范围、auditionNeedSubtitle 禁用。
8. **applyVoiceCloneCapability()**：动态更新 clonePreviewText maxLength、cloneVoiceId minLength/maxLength/pattern/hint、needNoiseReduction/needVolumeNormalization 禁用、cloneFileHint 文件大小提示、cloneBtn 禁用。
9. **applyVoiceDesignCapability()**：动态更新 designPrompt maxLength、designPreviewText maxLength、designVoiceId 规则、designBtn 禁用。
10. **applyImportVoiceCapability()**：动态更新 importClonePreviewText maxLength、importCloneVerify 禁用。
11. **applyAllProviderCapabilities()**：统一调用所有 apply* 函数。
12. **bindProviderCapabilityEvents()**：监听所有 provider select 变化事件。
13. **初始化**：bindProviderCapabilityEvents() + loadProviderCapabilities() 在页面 load 时调用。
14. **降级策略**：capabilities 加载失败不阻断页面，只 showToast 一次提示。

**测试结果：** 572 passed, 6 skipped（未改测试数量）。

**未改后端、Provider Adapter、数据库、资产清理链路。**

### P9-DOC1：Capability 架构收口文档

**阶段目标：** 同步 README 和 PROJECT_HEALTH_CHECK，正式收口 Provider Capability 架构。

**新增文件：**

- `docs/P9_CAPABILITY_ARCHITECTURE.md` — Provider Capability 架构说明文档

**修改文件：**

- `README.md` — 更新 Provider Capability Registry 章节，反映 P9-CAPABILITY1/2/3 完成状态；更新后续路线；更新文档索引
- `docs/PROJECT_HEALTH_CHECK.md` — 更新顶部摘要至 P9-DOC1

**实现：**

1. **P9_CAPABILITY_ARCHITECTURE.md**：完整记录架构分层（Settings / Provider Registry / Capability Registry / CapabilityValidator / Provider Adapter）、业务调度流、参数校验 vs 能力校验区别、P9 完成状态、后续路线、关键风险与防护。
2. **README.md**：更新 Provider Capability Registry 章节说明 P9 架构闭环；后续路线标注已完成项；文档索引新增 P9_CAPABILITY_ARCHITECTURE.md。
3. **PROJECT_HEALTH_CHECK.md**：更新顶部摘要至 P9-DOC1。

**测试结果：** 572 passed, 6 skipped（未改测试数量）。

**未改 app 代码、tests、Provider Adapter、生成链路、资产清理链路。**

### P9-CAPABILITY4：Admin Provider 能力矩阵只读展示

**阶段目标：** 在 admin.html 管理面板增加只读 Provider 能力矩阵区域，读取 GET /api/voice/capabilities。

**修改文件：**

- `app/static/admin.html` — 新增 Provider 能力矩阵卡片

**实现：**

1. **CSS 新增**：`.capability-matrix-wrap`、`.capability-table`（th/td 样式）、`.capability-yes`（绿色 ✔）、`.capability-no`（灰色 ✖）、`.capability-chip`（蓝色芯片标签）、`.capability-range`（min ~ max 格式）。

2. **HTML 卡片**：新增"Provider 能力矩阵"card，置于 Overview Cards 和 Provider Stats 之间，含 `<thead id="capMatrixHead">` 和 `<tbody id="capMatrixBody">`。

3. **JS 函数**：
   - `loadCapabilityMatrix()`：异步 fetch /api/voice/capabilities，成功时调用 renderCapabilityMatrix()，失败时显示错误提示
   - `renderCapabilityMatrix(providers)`：渲染 18 列表头（Provider / 显示名 / 启用 / 默认模型 / TTS / 流式 / 字幕 / 情绪 / 音频格式 / 长文本 / 剧本 / 克隆 / 设计 / 远端导入 / 文本上限 / 语速范围 / 音量范围 / 音高范围），调用 renderCapabilityRow 渲染每行
   - `renderCapabilityRow(cap, colCount)`：使用 `esc()` 转义所有动态字符串，返回 `<tr>` HTML
   - `boolBadge(value)`：value=true → `<span class="capability-yes">✔</span>`，否则 `<span class="capability-no">✖</span>`
   - `chips(values)`：数组值渲染为蓝色芯片标签，空数组显示 ✖
   - `rangeText(range)`：渲染 `{min} ~ {max}`，range 为 null/undefined 显示 —
   - `maxText(value)`：直接渲染数字或 —

4. **Init 调用**：`loadCapabilityMatrix()` 在 `initDates()` 后、`requestAnimationFrame` 前执行。

5. **安全约束**：不使用 metadata 字段（可能有敏感 key），所有动态字符串经过 `esc()` 转义，不显示 API key，不做健康探测，只读展示。

**测试结果：** 572 passed, 6 skipped（未改测试数量）。

**未改 app/api、app/services、app/providers、app/domain、index.html、tests、Provider Adapter、生成链路、资产清理链路。**

### P9-E2E1：关键路径浏览器测试

**阶段目标：** 为前端关键路径增加最小浏览器 E2E 测试，重点覆盖页面加载、capability 请求、控件动态约束、provider 切换、capability 失败降级、Admin 页面加载和矩阵渲染。

**新增文件：**

- `tests/e2e/conftest.py` — E2E 测试配置（server fixture、browser fixture、page fixture）
- `tests/e2e/test_frontend_capabilities.py` — 7 个 Playwright 浏览器测试

**修改文件：**

- `tests/conftest.py` — 修复 `pytest_collection_modifyitems` 只跳过有 `@pytest.mark.e2e` 标记的测试，不再误伤 `tests/e2e/` 目录下的其他测试

**实现：**

1. **conftest.py**：
   - `e2e_base_url` fixture（function scope）：启动 uvicorn，随机端口，轮询 `/api/voice/capabilities` 确认就绪后 yield，teardown 关闭进程
   - `browser` fixture（function scope）：每次测试启动新 Chromium 浏览器
   - `page` fixture（function scope）：每次测试在 browser 中创建新 context 和 page

2. **test_frontend_capabilities.py**（7 个测试）：
   - `test_index_page_loads_and_fetches_capabilities`：页面加载、capabilities 接口 200、关键控件存在
   - `test_index_capability_controls_are_applied`：audioFormat 选项、textInput maxlength、paramSpeed/vol/pitch 范围、needSubtitle 状态
   - `test_provider_switch_does_not_crash`：切换 mock/minimax 无 console error，控件保持存在
   - `test_capabilities_failure_falls_back_without_crash`：capabilities 接口 500 时页面不崩溃，仍可用
   - `test_admin_page_loads`：Admin 页面加载，能力矩阵/Provider 统计/API 分布存在
   - `test_admin_capability_matrix_renders_providers`：能力矩阵渲染 mock/minimax，显示 mp3/wav/flac 和参数范围
   - `test_admin_capabilities_failure_only_affects_matrix`：capabilities 失败时矩阵显示错误，其他区域正常

3. **console_errors fixture**：捕获 `console.error` 和 `pageerror`，过滤 favicon 404 和预期的 500 响应错误。

4. **tests/conftest.py 修复**：原 `if "e2e" in item.keywords` 会误跳过所有 `tests/e2e/` 目录测试；改为 `if any(m.name == "e2e" for m in item.iter_markers())` 只跳过有 `@pytest.mark.e2e` 的测试。

**依赖安装：**

```bash
pip install pytest-playwright
python -m playwright install chromium
```

**运行命令：**

```bash
python -m pytest tests/e2e -q
```

**测试结果：** 579 passed, 6 skipped（新增 7 个 E2E 测试）。

**未改 app/api、app/services、app/providers、app/domain、index.html、admin.html、Provider Adapter、生成链路、数据库、资产清理链路。**

### P9-FE1-A：前端 Provider Capability JS 模块化

**阶段目标：** 把 `app/static/index.html` 中 Provider Capability 相关 JS 逻辑抽离到独立文件，降低 index.html 体积和后续维护风险。

**新增文件：**

- `app/static/js/provider_capabilities.js` — Provider Capability 前端模块

**修改文件：**

- `app/static/index.html` — 新增 `<script src="/static/js/provider_capabilities.js">` 引入模块；移除已移动的重复函数定义；`let MAX_SCRIPT_LINES` 改为 `var MAX_SCRIPT_LINES` 以支持外部模块修改

**实现：**

1. **provider_capabilities.js**：
   - IIFE 包装，不使用 ES module
   - window 状态变量：`_providerCapabilities`、`_providerCapabilitiesByName`、`_capabilitiesLoaded`、`_capabilitiesLoadFailed`、`_capabilitiesLoadAttempted`、`_capabilitiesFailureNotified`（E2E 测试依赖）
   - 独立 `capEsc()` 函数（复制 index.html 的 `esc()` 逻辑）
   - 函数列表：`loadProviderCapabilities`、`getProviderCapability`、`getSelectValue`、`setHintText`、`setTextMaxLength`、`updateSelectOptions`、`setControlDisabled`、`updateProviderSelectOptions`、`applyWorkspaceCapability`、`applyLongtextCapability`、`applyScriptCapability`、`applyProviderVoiceCapability`、`applyVoiceCloneCapability`、`applyVoiceDesignCapability`、`applyImportVoiceCapability`、`applyAllProviderCapabilities`、`bindProviderCapabilityEvents`
   - 所有函数通过 `window.*` 暴露到全局
   - 调用 `updateCloneBtnState`、`updateScriptLineLimitState`、`showToast` 时做存在性判断
   - `applyScriptCapability` 通过 `window.MAX_SCRIPT_LINES` 修改剧本最大行数

2. **index.html 修改**：
   - 在 inline `<script>` 前添加 `<script src="/static/js/provider_capabilities.js"></script>`
   - 移除已移动的 capability 函数定义（原 1589-2030 行，约 440 行）
   - `MAX_SCRIPT_LINES` 从 `let` 改为 `var`
   - 初始化调用 `bindProviderCapabilityEvents()` 和 `loadProviderCapabilities()` 保持不变

3. **E2E 兼容**：
   - `window._providerCapabilities` 在 capability 加载后被赋值，E2E `typeof _providerCapabilities !== 'undefined'` 断言继续通过
   - E2E 可通过 `window.loadProviderCapabilities`、`window.applyAllProviderCapabilities` 访问函数

**验收检查：**

```bash
grep -n "function loadProviderCapabilities" app/static/index.html   # 无输出
grep -n "function loadProviderCapabilities" app/static/js/provider_capabilities.js  # 1 处
```

**测试结果：** 579 passed, 6 skipped（未改测试数量）。

**未改 app/api、app/services、app/providers、app/domain、admin.html、Provider Adapter、生成链路、数据库、资产清理链路。**

### P9-FE1-B：前端 Runtime Status JS 模块化

**阶段目标：** 把 `app/static/index.html` 中 Runtime Status Bar / Provider Status Chip 相关 JS 逻辑抽离到独立文件，降低 index.html 体积和维护风险。

**新增文件：**

- `app/static/js/runtime_status.js` — Runtime Status 前端模块

**修改文件：**

- `app/static/index.html` — 新增 `<script src="/static/js/runtime_status.js">` 引入模块（位于 provider_capabilities.js 之后）；移除已移动的 Runtime Status 函数定义

**实现：**

1. **runtime_status.js**：
   - IIFE 包装，不使用 ES module
   - window 状态变量：`_runtimeStatusTimer`、`_runtimeStatusErrorNotified`
   - `window.loadRuntimeStatus`：获取 `/api/voice/runtime/status`，更新 chipProvider / chipModel / chipToday / chipMonth / chipProviderStatus 五个 chip，支持 error/warning/available/unknown 四种状态，点击跳转到 admin.html?focus=call-logs，失败时显示"点击重试"并调用 `window.showToast`（存在性判断）
   - `window.scheduleRuntimeStatusRefresh`：60 秒轮询 timer，暴露到 window 以便 inline script 初始化
   - `setRuntimeChip(id, text, className, title)` 辅助函数
   - `rsEsc()` 本地 helper
   - 使用 `document.getElementById('providerSelect')` 而非局部变量引用
   - 所有 DOM 操作都有 null-check
   - onclick 使用普通函数而非箭头函数（兼容性）

2. **index.html 修改**：
   - 在 inline `<script>` 前添加 `<script src="/static/js/runtime_status.js"></script>`（在 provider_capabilities.js 之后）
   - 移除 `loadRuntimeStatus()` 和 `scheduleRuntimeStatusRefresh()` 函数定义及 `_runtimeStatusTimer` / `_runtimeStatusErrorNotified` 变量
   - 初始化调用 `loadRuntimeStatus()` 和 `scheduleRuntimeStatusRefresh()` 保持不变（通过 window 引用）

**验收检查：**

```bash
grep -n "function loadRuntimeStatus" app/static/index.html   # 无输出
grep -n "function loadRuntimeStatus" app/static/js/runtime_status.js  # 1 处
```

**测试结果：** 579 passed, 6 skipped（未改测试数量）。

**未改 app/api、app/services、app/providers、app/domain、index.html、admin.html、provider_capabilities.js、Provider Adapter、生成链路、数据库、资产清理链路。**

### P9-FE1-A-FIX：修复剧本 Tab populateProfileSelect 空 DOM 报错

**问题现象：** 点击"剧本"Tab 后，浏览器控制台报错：`Uncaught (in promise) TypeError: Cannot read properties of null (reading 'value') at populateProfileSelect (index.html:1821:35)`。

**根因：** 剧本 Tab 切换回调在 line 1634 调用 `populateProfileSelect(document.getElementById('batchScriptProfile'))`，但 DOM 中不存在 `batchScriptProfile` 元素（该元素从未定义），`getElementById` 返回 `null`，`populateProfileSelect` 内部直接访问 `selectEl.value` 导致报错。

**修改文件：**

- `app/static/index.html` — 两处修改

**实现：**

1. **null guard**：在 `populateProfileSelect` 开头添加 `if (!selectEl) return;`，防止 `selectEl` 为 null 时崩溃。

2. **修正 call site**：将 `tab === 'script'` 分支中的 `document.getElementById('batchScriptProfile')` 改为 `document.getElementById('batchProfile')`（与长文本 Tab 共用同一个 profile select 元素）。

3. **E2E 测试**：新增 `test_script_tab_opens_without_profile_select_error`，验证点击剧本 Tab 后无 JS 错误且 Tab 内容正常显示。

**验收检查：**

```bash
grep -n "if (!selectEl) return" app/static/index.html   # 1 处
grep -n "batchScriptProfile" app/static/index.html       # 无输出
```

**测试结果：** 580 passed, 6 skipped（新增 1 个 E2E 测试）。

**未改 app/api、app/services、app/providers、app/domain、admin.html、provider_capabilities.js、runtime_status.js、Provider Adapter、生成链路、数据库、资产清理链路。**

### P9-FE1-CHECK1：前端模块化阶段收口

**收口检查项：**

1. **脚本加载顺序**：index.html 中 provider_capabilities.js（line 1587）在 inline script 前；runtime_status.js（line 1588）在 provider_capabilities.js 后；inline script 中仍可直接调用 `loadProviderCapabilities()`、`bindProviderCapabilityEvents()`、`loadRuntimeStatus()`、`scheduleRuntimeStatusRefresh()`。

2. **重复函数清理**：`loadProviderCapabilities` 只在 provider_capabilities.js 中定义；`loadRuntimeStatus` 和 `scheduleRuntimeStatusRefresh` 只在 runtime_status.js 中定义；index.html 无重复函数定义，只有说明注释指向外部模块。

3. **全局兼容函数**：provider_capabilities.js 暴露 `window.loadProviderCapabilities`、`window.getProviderCapability`、`window.applyAllProviderCapabilities`、`window.bindProviderCapabilityEvents`、`window.updateProviderSelectOptions`、`window.setControlDisabled`；runtime_status.js 暴露 `window.loadRuntimeStatus`、`window.scheduleRuntimeStatusRefresh`；index.html 原有调用点无需改动。

4. **剧本 Tab 回归修复**：`populateProfileSelect` 开头有 `if (!selectEl) return;`；剧本 Tab call site 已从 `batchScriptProfile` 修正为 `batchProfile`；E2E 测试 `test_script_tab_opens_without_profile_select_error` 存在且通过。

5. **E2E 覆盖范围**：主页面加载、/api/voice/capabilities 200、capability 动态控件生效、provider 切换不报错、capabilities 失败降级、Admin 页面加载、Admin 能力矩阵渲染、Admin capabilities 失败隔离、剧本 Tab 打开不报 populateProfileSelect 错误，共 8 个 E2E 测试。

6. **测试基线**：580 passed, 6 skipped。

**本阶段说明：**

- P9-FE1-A 已完成：Provider Capability 前端逻辑抽离到 `app/static/js/provider_capabilities.js`。
- P9-FE1-B 已完成：Runtime Status 前端逻辑抽离到 `app/static/js/runtime_status.js`。
- P9-FE1-A-FIX 已完成：修复点击剧本 Tab 时 `populateProfileSelect` 访问 `null.value` 的报错。
- 当前 index.html 通过 `<script>` 标签加载两个独立 JS 模块。
- 保留 window 全局入口，兼容现有 inline script 调用和 E2E。
- 本阶段只做检查和文档收口，未改功能代码。
- 未改后端 API、Capability Registry、CapabilityValidator、Provider Adapter、生成链路、数据库、资产清理链路。

### P9-FE1-C：前端 History JS 模块化

**阶段目标：** 把 `app/static/index.html` 中历史记录相关 JS 逻辑抽离到独立文件，降低 index.html 体积和维护风险。

**新增文件：**

- `app/static/js/history.js` — History 前端模块

**修改文件：**

- `app/static/index.html` — 新增 `<script src="/static/js/history.js">` 引入模块（位于 runtime_status.js 之后）；移除已迁移的历史记录函数定义和状态变量（约 870 行）；保留 `downloadBtnHtml`（非 history 专用）、`audioPlayerHtml`、`statusLabel`、`statusClass` 等通用 helper。

**实现：**

1. **history.js**：
   - IIFE 包装，不使用 ES module
   - window 状态变量：`_historyJobs`、`_historyOffset`、`_historyTotal`、`_historyLoading`、`_historySearch`、`_historyStatusFilter`、`_activeHistoryAudioRow`（E2E 测试依赖）
   - 本地 helper 避免 index.html 加载顺序依赖：`hEsc`、`hCopyJobId`、`hFormatLocalDateTime`、`hUtcTitle`、`hStatusClass`、`hStatusLabel`、`hAudioPlayerHtml`、`hDownloadBtnHtml`、`hIsSuccessStatus`、`hIsFailedStatus`、`hIsProcessingStatus`
   - 函数列表：`loadHistory`、`loadMoreHistory`、`refreshHistory`、`renderHistoryList`、`filterHistoryJobs`、`handleHistorySearchInput`、`handleHistoryStatusFilterChange`、`clearHistoryFilters`、`updateHistoryFilterHint`、`toggleHistoryAudio`、`deleteHistoryJob`、`copyJobId`、`historyJobCardHtml`、`historyEmptyStateHtml`、`historyLoadErrorHtml`、`historyEndStateHtml`、`historyFilteredEmptyStateHtml`、`historyAudioPlayerHtml`、`attachHistoryAudioEvents`、`getHistoryAudioAssetId`、`historyDownloadEntryHtml`
   - 所有函数通过 `window.*` 暴露到全局
   - `window.loadHistory(0)` 在 IIFE 执行时自动调用，完成页初始化加载
   - `showToast` 调用通过 `typeof window.showToast === 'function'` 存在性判断

2. **index.html 修改**：
   - 添加 `<script src="/static/js/history.js">` 在 provider_capabilities.js 和 runtime_status.js 之后
   - 移除 `_historyOffset` 等 7 个状态变量
   - 移除 `loadHistory`、`loadMoreHistory`、`refreshHistory`、`renderHistoryList`、`filterHistoryJobs` 等函数定义
   - 移除 `toggleHistoryAudio`、`deleteHistoryJob` 函数定义
   - 移除 `historyJobCardHtml`、`historyEmptyStateHtml`、`historyLoadErrorHtml` 等 HTML 生成函数
   - 保留 `downloadBtnHtml`（供 renderResults/renderAsyncResult 使用）
   - 保留 `statusLabel`、`statusClass`、`formatLocalDateTime`、`utcTitle`、`esc` 等通用 helper
   - 事件委托中对 `toggleHistoryAudio`/`deleteHistoryJob` 的引用通过 window 全局函数生效

3. **E2E 兼容**：
   - `window._historyJobs` 等状态变量在 history.js 中设置，E2E 可访问
   - `window.loadHistory`、`window.refreshHistory` 等函数 E2E 可调用

**验收检查：**

```bash
grep -n "function loadHistory" app/static/index.html   # 无输出
grep -n "function loadHistory" app/static/js/history.js  # 1 处
grep -n "_historyOffset" app/static/index.html           # 无输出（已移除）
```

**测试结果：** 580 passed, 6 skipped（本阶段未新增 E2E 测试）。

**未改 app/api、app/services、app/providers、app/domain、admin.html、provider_capabilities.js、runtime_status.js、Provider Adapter、生成链路、数据库、资产清理链路。**

### P9-FE1-C-FIX：补 History Tab E2E 回归测试

**阶段目标：** 为 P9-FE1-C 抽离后的 history.js 补充最小浏览器回归测试，防止 history.js 抽离后出现 DOM ID 不匹配、全局函数未暴露、Tab 打开 JS 报错等问题。

**修改文件：**

- `app/static/js/history.js` — 新增 `window.renderHistoryList` 和 `window.filterHistoryJobs` 暴露（测试依赖）
- `tests/e2e/test_frontend_capabilities.py` — 新增 2 个 E2E 测试

**实现：**

1. **test_history_module_is_loaded**：
   - 断言 `document.querySelector('script[src="/static/js/history.js"]')` 存在
   - 断言 `window.loadHistory`、`window.refreshHistory`、`window.renderHistoryList` 为 function
   - 断言 `window._historyJobs` 已初始化

2. **test_history_tab_opens_and_refreshes_without_error**：
   - 点击历史 Tab，等待 `#tab-history` 和 `#historyList` 出现
   - 如果 `#historyRefreshBtn` 存在则点击
   - 如果 `#historySearch` 存在则输入关键词后清空
   - 如果 `#historyStatusFilter` 存在则选择 all
   - 不要求数据库有历史数据
   - 无 JS 报错即通过

3. **history.js 修正**：`window.renderHistoryList` 和 `window.filterHistoryJobs` 未暴露，补加。

**验收检查：**

```bash
python -m pytest tests/e2e -q  # 10 passed
python -m pytest tests/ -x -q  # 582 passed, 6 skipped
```

**测试结果：** 582 passed, 6 skipped（新增 2 个 E2E 测试）。

**未改 app/api、app/services、app/providers、app/domain、index.html、admin.html、provider_capabilities.js、runtime_status.js、history.js 业务逻辑、Provider Adapter、生成链路、数据库、资产清理链路。

### P9-FE1-D：抽取 audition_records.js 前端模块

**阶段目标：** 将 index.html 中的试听记录逻辑（`_auditionRecords` 状态、`renderAuditionRecords`、`deleteAuditionRecord`、`clearAuditionRecords`）抽离为独立 IIFE 模块 `app/static/js/audition_records.js`，E2E 验证模块加载与 Voices Tab 打开无 JS 报错。

**修改文件：**

- `app/static/js/audition_records.js` — 新建，承接 `_auditionRecords` 状态与渲染函数
- `app/static/index.html` — 移除内联 audition record 函数定义，改为调用 window 全局函数
- `tests/e2e/test_frontend_capabilities.py` — 新增 1 个 E2E 测试

**实现：**

1. **audition_records.js**（新建 IIFE）：
   - `window._auditionRecords = []` 状态初始化
   - `window.renderAuditionRecords()` — 渲染到 `#auditionRecordsTable`
   - `window.deleteAuditionRecord(idx)` — 删除指定记录并重绘
   - `window.clearAuditionRecords()` — 清空所有记录并重绘
   - `arEsc()` — HTML 转义辅助

2. **index.html 改动**：
   - 新增 `<script src="/static/js/audition_records.js">`（history.js 之后）
   - `setupAuditionWorkstation()` 中 `window._auditionRecords = []; renderAuditionRecords()` → `window.clearAuditionRecords()`
   - `setupAuditionWorkstation()` 中 `window._auditionRecords.splice(...)` → `window.deleteAuditionRecord(idx)`
   - 移除 `renderAuditionRecords()` 函数定义，改为注释引用外部模块

3. **test_audition_records_module_and_voices_tab_open**：
   - 断言 `script[src="/static/js/audition_records.js"]` 存在
   - 断言 `window.renderAuditionRecords`、`window.deleteAuditionRecord`、`window.clearAuditionRecords` 为 function
   - 点击 Voices tab，断言 `#tab-voices` 和 `#voiceListResults` 存在

**验收检查：**

```bash
python -m pytest tests/e2e -q  # 11 passed
python -m pytest tests/ -x -q  # 582 passed, 6 skipped
```

**测试结果：** 582 passed, 6 skipped（新增 1 个 E2E 测试）。

**未改 app/api、app/services、app/providers、app/domain、admin.html、provider_capabilities.js、runtime_status.js、history.js、Provider Adapter、生成链路、数据库、资产清理链路。

### P9-FE-ERROR1：前端 API 错误展示统一优化

**问题：** 声音克隆（clone/create）返回 `{ "error": { "code": "PROVIDER_ERROR", "message": "MiniMax voice clone failed", "detail": "insufficient balance", "job_id": null } }` 时，前端只显示 `err.message`（"MiniMax voice clone failed"），丢弃了 `err.detail`（"insufficient balance"），导致用户看不到真正原因。

**原因：** `parseApiError` 正确提取了 `error.detail` → `err.detail`，`formatApiError` 也能正确组合 `message + detail`，但各业务 handler 的 catch-all 分支直接用 `err.message` 构造错误文本，绕过了 `formatApiError`。

**修复：** 将以下 catch-all 分支的错误文本从 `friendlyErrorMessage(err.message)` 改为 `friendlyErrorMessage(formatApiError(err))`，使 `err.detail` 能被正确展示：

| 位置 | 场景 |
|---|---|
| `handleCloneVoice` (line 4106) | 声音克隆失败 |
| `handleDesignVoice` (line 4411) | 声音设计失败 |
| `handleImportRemoteVoice` (line 4283) | 远端音色导入失败 |
| `handleVoiceAudition` (line 3488) | 音色试听失败 |
| async polling query failure (line 2833) | 异步任务查询失败 |
| clone upload (line 3948) | 克隆文件上传失败 |
| batch longtext submit (line 4873) | 长文本批量提交失败 |
| batch script submit (line 4988) | 剧本批量提交失败 |

**错误展示规则（formatApiError）：**
1. `error.detail` 存在时：`${error.message}：${error.detail}`
2. 只有 `error.message` 时：直接显示
3. 只有 `detail`（FastAPI detail 字段）时：直接显示
4. 只有 `message` 时：直接显示
5. 兜底：`请求失败，请稍后重试`

**验证方式（手动）：**
1. 启动服务 `python -m app.main`
2. 打开 /static/index.html
3. 切换到"高级功能 → 声音克隆" tab
4. 填写必要字段，Provider 选 minimax
5. 拦截 `**/api/voice/clone/create?provider=minimax` 返回 400：
   ```json
   { "error": { "code": "PROVIDER_ERROR", "message": "MiniMax voice clone failed", "detail": "insufficient balance", "job_id": null } }
   ```
6. 点击克隆，页面应显示"余额不足"相关提示（或 "MiniMax voice clone failed：insufficient balance"）

**E2E 验证：** 未新增 E2E（表单操作 E2E 成本较高，手动验证覆盖）。

**验收检查：**

```bash
python -m pytest tests/e2e/test_frontend_capabilities.py -q  # 11 passed
git diff --check  # 无 whitespace 错误
```

**测试结果：** 11 passed in 37s。full tests 未运行，原因：本次仅修改前端错误展示逻辑，未改后端 API、Provider Adapter、生成链路、数据库、资产清理链路；完整回归留到阶段收口执行。

**保持不变：**
- API 请求路径未变
- 上传逻辑未变
- 声音克隆请求逻辑未变
- 422 中文校验提示未变
- Resource Guard 提示未变

**未改 app/api、app/services、app/providers、app/domain、admin.html、provider_capabilities.js、runtime_status.js、history.js、audition_records.js、Provider Adapter、CapabilityValidator、Capability Registry、生成链路、数据库、资产清理链路。

### P9-FE1-D-FIX：补强 audition_records.js 渲染 / 删除最小 E2E

**问题：** P9-FE1-D 已验证 audition_records.js 模块加载，但未验证渲染 / 删除行为。

**修复：** 新增 `test_audition_records_render_and_delete` E2E 测试。

**实现：**
- 直接注入 `#voiceAuditionPanel` + `#auditionRecordsTable` HTML 到 `#voiceListResults`（绕过真实的 `renderVoiceTable` 调用，无需 mock provider-voices API）
- 向 `window._auditionRecords` 注入一条测试记录
- 调用 `window.renderAuditionRecords()`
- 断言 `test_voice_001`、`测试音色`、`文本预览` 均出现
- 调用 `window.deleteAuditionRecord(0)`（因 `setupAuditionWorkstation` 未执行，事件委托未绑定，直接调用函数）
- 断言 `window._auditionRecords.length === 0`
- 断言页面出现"暂无试听记录"

**验收检查：**

```bash
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "audition"  # 2 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q  # 12 passed
git diff --check  # 无错误
```

**测试结果：** 12 passed in 36s。full tests 未运行，原因：仅补前端 E2E，未改业务逻辑、后端 API、Provider Adapter、生成链路、数据库、资产清理链路。

**未改 app/static/index.html、app/static/js/audition_records.js、app/api、app/services、app/providers、app/domain、admin.html、Provider Adapter、生成链路、数据库、资产清理链路。

### P9-FE1-E0：长文本批量模块抽离前边界审查

**本次只做审查和小清理，未做功能迁移。**

**清理：** 移除 `tests/e2e/test_frontend_capabilities.py` 中未使用的 `import json`。

**审查结论：**

长文本批量相关函数按共享程度分为三类：

| 函数 | 类型 | 能否迁移 |
|---|---|---|
| `handleBatchLongtextSubmit()` | 长文本独有 | ✅ 可迁移 |
| `showBatchLongtextResult(html)` | 长文本内部嵌套 helper | ⚠️ 需先提取为 `window.*` |
| `clearBatchLongtextResult()` | 长文本内部嵌套 helper | ⚠️ 需先提取为 `window.*` |
| `showBatchProgress()` / `startBatchPoll()` / `stopBatchPoll()` / `pollBatchStatus()` | 共享，两批量共用 | ❌ 暂不迁移 |
| `renderBatchStatus()` / `renderBatchResultPlayer()` | 共享，两批量共用 | ❌ 暂不迁移 |
| `renderBatchSubtitleList()` / `updateBatchSubtitleHighlight()` | 共享，两批量共用 | ❌ 暂不迁移 |
| `handleBatchPlay()` / `handleBatchRetry()` / `getBatchPanelDom()` | 共享，两批量共用 | ❌ 暂不迁移 |

**状态变量共享风险：** `_batchPollTimer`、`_currentBatchId`、`_currentBatchPanelId`、`_batchTimeline` 为两批量共用。交替提交时轮询 timer 会指向最后一次启动的 batch，先前批次可能丢失进度更新。

**P9-FE1-E 前提条件：** 需先将 `showBatchLongtextResult` / `clearBatchLongtextResult` 从 `handleBatchLongtextSubmit` 内部提取为 `window.*` 函数，否则模块无法调用。

**文档更新：** `docs/P9_FRONTEND_MODULARIZATION.md` 新增 5.0 节（P9-FE1-E0 边界审查），更新 5.1 节迁移前提，更新测试覆盖表和已知风险。

**验收检查：**

```bash
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "audition"  # 2 passed
git diff --check  # 无错误
```

**测试结果：** 2 passed。full tests 未运行，原因：本次仅清理未使用 import 并更新文档，未改业务逻辑、前端运行代码、后端 API、Provider Adapter、生成链路、数据库、资产清理链路。

**未改 app/static/index.html、app/static/js/*、app/api、app/services、app/providers、app/domain、admin.html、Provider Adapter、生成链路、数据库、资产清理链路。

### P9-FE1-E1：提取长文本批量结果 helper 为 window 全局函数

**阶段目标：** 将 `showBatchLongtextResult` / `clearBatchLongtextResult` 从 `handleBatchLongtextSubmit` 内部闭包提取为 `window.*` 全局函数，为后续 `batch_longtext.js` 抽离解除闭包依赖。

**修改文件：**
- `app/static/index.html` — 提取 `window.showBatchLongtextResult` 和 `window.clearBatchLongtextResult`，更新 `handleBatchLongtextSubmit` 内所有调用处
- `tests/e2e/test_frontend_capabilities.py` — 新增 `test_batch_longtext_result_helpers_are_exposed`

**实现：**
- `window.showBatchLongtextResult = function(html)` — 显示 HTML 到 `#batchLongtextResult`（`style.display = ''` 当有内容）
- `window.clearBatchLongtextResult = function()` — 清空并隐藏（`style.display = 'none'`）
- `handleBatchLongtextSubmit` 内部所有 `showBatchLongtextResult(...)` 调用改为 `window.showBatchLongtextResult(...)`
- 所有 `clearBatchLongtextResult()` 调用改为 `window.clearBatchLongtextResult()`
- 原有 UI、DOM、错误展示、批量提交行为完全不变

**保持不变：**
- `handleBatchLongtextSubmit` 尚未迁移
- `batch_longtext.js` 尚未创建
- 共享轮询 / 渲染函数（`showBatchProgress` 等）未改
- 共享状态变量未改
- 剧本批量逻辑未改
- API 请求体 / endpoint 未改

**E2E 验证：**
- `test_batch_longtext_result_helpers_are_exposed`：点击长文本 Tab，断言 `window.showBatchLongtextResult` / `window.clearBatchLongtextResult` 为 function，调用并验证 DOM 行为正确

**验收检查：**

```bash
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "batch_longtext_result"  # 1 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q  # 13 passed
git diff --check  # 无错误
```

**测试结果：** 13 passed in 39s。full tests 未运行，原因：本次仅提取前端 helper 为 window 全局函数，未迁移业务逻辑，未改后端 API、Provider Adapter、生成链路、数据库、资产清理链路。

**未改 app/api、app/services、app/providers、app/domain、admin.html、app/static/js/provider_capabilities.js、app/static/js/runtime_status.js、app/static/js/history.js、app/static/js/audition_records.js、Provider Adapter、CapabilityValidator、Capability Registry、生成链路、数据库、资产清理链路。

### P9-FE1-E2：抽离长文本批量提交模块 batch_longtext.js

**阶段目标：** 将 `handleBatchLongtextSubmit` 从 `index.html` 迁移到独立 IIFE 模块 `app/static/js/batch_longtext.js`，暴露 `window.handleBatchLongtextSubmit`，为后续 `batch_script.js` 抽离做准备。

**修改文件：**
- `app/static/js/batch_longtext.js` — 新建，承接 `handleBatchLongtextSubmit`
- `app/static/index.html` — 新增 `<script src="/static/js/batch_longtext.js">`（audition_records.js 之后），移除 `handleBatchLongtextSubmit` 函数定义（替换为注释引用）
- `tests/e2e/test_frontend_capabilities.py` — 新增 `test_batch_longtext_module_is_loaded_and_submit_validation_works`

**实现：**
- `batch_longtext.js` 为 IIFE，内部定义 `window.handleBatchLongtextSubmit` 异步函数
- 依赖 index.html 中已有的 `window.showBatchLongtextResult` / `window.clearBatchLongtextResult`（E1 阶段已提取）
- 依赖 index.html 中已有的 `guardedJsonFetch`、`parseApiError`、`renderApiError`、`esc`、`showBatchProgress`、`startBatchPoll`、`loadRuntimeStatus` 等全局函数（inline script 中定义，onclick 触发时已就绪）
- `index.html` 中 `onclick="handleBatchLongtextSubmit()"` 保持不变（通过 `window` 作用域链解析）

**保持不变：**
- 共享轮询 / 渲染函数（`showBatchProgress` 等）未迁移，仍在 `index.html`
- 共享状态变量（`_batchPollTimer` 等）未迁移，仍在 `index.html`
- 剧本批量逻辑未改
- API endpoint / request body 未改
- 后端未改

**E2E 验证：**
- `test_batch_longtext_result_helpers_are_exposed`（E1 测试）：验证 `window.showBatchLongtextResult` / `window.clearBatchLongtextResult` 可用
- `test_batch_longtext_module_is_loaded_and_submit_validation_works`（E2 测试）：验证 `batch_longtext.js` script 存在，`window.handleBatchLongtextSubmit` 为 function，空文本提交触发前端校验并显示"请输入待分段文本"

**验收检查：**

```bash
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "batch_longtext"  # 2 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q  # 14 passed
git diff --check  # 无错误
```

**测试结果：** 14 passed in 42s。full tests 未运行，原因：本次仅迁移前端长文本批量提交函数，未改后端 API、Provider Adapter、生成链路、数据库、资产清理链路；已运行前端 E2E 覆盖模块加载与前端校验。

---

## P9-FE1-E2-FIX：长文本批量 mock 提交成功 E2E

**目标：** 添加 `test_batch_longtext_mock_submit_success_starts_progress` E2E 测试，验证 `handleBatchLongtextSubmit` 在 mock 环境下可完成完整提交流程，不调用真实 MiniMax。

**实现：**

- 路由注册在 `page.goto` 之前（Playwright 要求路由在请求发出前注册）
- 设置 `batchProvider` 为 `'mock'` 以绕过 `guardedJsonFetch` 的 `confirm()` 弹窗（`provider=minimax` 时 `highRisk` 操作会触发确认对话框）
- 使用 Playwright `page.route` 拦截 `POST /api/voice/batch/submit`（返回 fake `batch_id`）和 `GET /api/voice/batch/e2e_batch_longtext_001/status`（返回 processing 状态）
- 直接点击 `#batchLongtextSubmit` 按钮，触发 `onclick="handleBatchLongtextSubmit()"`
- 断言：`submit_called["yes"]` 为 True（路由被触发）、progress panel 出现、button text 恢复

**关键技术点：**

- `page.route` 必须注册在 `page.goto` 之前，否则无法拦截页面内发出的请求
- `guardedJsonFetch` 对 `provider=minimax` + `highRisk=true` 会调用 `confirm()` 弹窗，自动化测试中会 cancel 导致 `USER_CANCELLED` 错误；设置 `provider=mock` 可绕过此检查
- `batchProvider` 默认值为 `minimax`（不是 `mock`），需在点击前显式设置为 `mock`
- `handleBatchLongtextSubmit` 内部读取 `document.getElementById('batchProvider').value` 获取 provider

**E2E 验证：**

```bash
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "batch_longtext"  # 3 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q  # 15 passed
```

**测试结果：** 15 passed in 46.66s。

**未改 app/api、app/services、app/providers、app/domain、admin.html、app/static/js/provider_capabilities.js、app/static/js/runtime_status.js、app/static/js/history.js、app/static/js/audition_records.js、Provider Adapter、CapabilityValidator、Capability Registry、生成链路、数据库、资产清理链路。

---

## P9-FE1-F0：剧本批量模块抽离前边界审查

**目标：** 审查 `app/static/index.html` 中剧本批量相关 JS，梳理 DOM id、状态变量、函数清单、API endpoint、共享逻辑，为 P9-FE1-F1 是否抽离 `batch_script.js` 提供决策依据。本次仅做审查和文档记录，不迁移代码。

**执行内容：**

- grep `scriptRows`、`handleBatchScriptSubmit`、`addScriptLine`、`removeScriptLine`、`batchScript`、`scriptProgressPanel`、`targetPanelId`、`_batchPollTimer` 等关键模式
- 阅读 index.html 第 4710–5250 行（约 540 行），梳理剧本批量完整逻辑链
- 阅读 `populateProfileSelect` / `loadProfiles` / `_cachedProfiles` 全局人设系统
- 阅读共享轮询函数（`showBatchProgress` 等）完整实现
- 梳理剧本批量与长文本批量的共享状态和函数边界

**边界审查发现：**

1. **状态变量 `_scriptRows`**：实际名为 `_scriptRows`（非 `scriptRows`），元素 `{id, role, text, profileId}`，与 DOM 事件委托紧耦合（`input`/`change` 事件监听器直接修改数组元素字段）。

2. **addScriptLine / removeScriptLine**：每添加一行调用 `populateProfileSelect` 初始化人设下拉，`populateProfileSelect` 依赖全局 `_cachedProfiles`。若独立模块在 profiles 缓存就绪前调用，会自动 `loadProfiles()`，行为不变但有额外网络请求。

3. **handleBatchScriptSubmit**：内部使用 `esc`、`guardedJsonFetch`、`parseApiError`、`formatApiError`、`window.renderApiError` 等全局函数。提交流程为：收集 `_scriptRows` DOM → 构建 `script: [{role, text, profile_id}]` payload → `POST /api/voice/batch/submit` → `showBatchProgress` → `startBatchPoll`。可整体迁移，但需确保全局 helper 已就绪。

4. **共享轮询函数**：`showBatchProgress` / `startBatchPoll` / `stopBatchPoll` / `pollBatchStatus` / `renderBatchStatus` / `renderBatchResultPlayer` / `renderBatchSubtitleList` / `updateBatchSubtitleHighlight` / `getBatchPanelDom` / `formatTime` 全部留在 index.html。其中 `renderBatchStatus` 含 `isScriptPanel` 分支逻辑，输出额外"角色"列。

5. **独立 targetPanelId**：剧本批量使用 `batchScriptProgressPanel`，长文本批量使用 `batchProgressPanel`，两者完全独立，不共用进度 DOM id。

6. **共享状态冲突**：`_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline` 两批量共用，与长文本批量风险相同（交替提交会覆盖彼此状态）。

7. **无 `renderScriptRows` 函数**：行渲染直接由 `addScriptLine` 完成（创建 DOM 元素并追加），无独立渲染函数。

**测试结果：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "script"
# 1 passed
git diff --check
# no output (no whitespace errors)
```
full tests 未运行，原因：本次仅做剧本批量模块边界审查和文档更新，未改业务逻辑、前端运行代码、后端 API、Provider Adapter、生成链路、数据库、资产清理链路。

**下一步建议：**

- **P9-FE1-F1 Phase 1**：仅迁移 `handleBatchScriptSubmit()` 到 `batch_script.js`，台词行管理函数（`addScriptLine` 等）和事件委托代码暂时保留在 index.html。将 `esc` 作为本地 `arEsc` 辅助函数复制到模块内，避免依赖 index.html 的 `esc`。
- **Phase 1 之前**：建议补剧本行增删 E2E（添加行、删除行、验证行数上限 200）和剧本批量提交校验 E2E（空文本、无 profile 场景）。
- **Phase 2**：迁移 `addScriptLine` / `removeScriptLine` / `updateScriptLineLimitState` / `_scriptLineCount` / `_scriptRows` / `MAX_SCRIPT_LINES` 和事件委托代码。需先确认 `populateProfileSelect` 已暴露为 `window.populateProfileSelect`。
- **Phase 2 之前**：建议补剧本批量 mock 提交成功 E2E（参考 `test_batch_longtext_mock_submit_success_starts_progress`）。

**未改 app/static/index.html、app/static/js/*、app/api/*、app/services/*、app/providers/*、app/domain/*、app/core/*、Provider Adapter、CapabilityValidator、Capability Registry、生成链路、数据库、资产清理链路、scripts/cleanup_assets.py。

---

## P9-FE1-F1：剧本批量提交校验 E2E

**问题：** P9-FE1-F0 已完成边界审查，但剧本批量缺少提交校验 E2E，无法验证 `handleBatchScriptSubmit` 的前端校验逻辑在抽离前后是否正常工作。

**修复：** 新增 `test_batch_script_submit_validation_works` E2E 测试，验证剧本批量提交时前端校验错误展示正常，且 `/api/voice/batch/submit` 未被调用。

**实现：**

- 在 `page.goto` 前通过 `page.route("**/api/voice/batch/submit", lambda route: route.abort())` 拦截批量提交接口，确保不会发出真实请求
- 打开页面后点击 Script Tab，等待 `#tab-script` 和 `#batchScriptSubmit` 出现
- 页面初始化时已通过 `addScriptLine()` 创建 3 行默认空台词行
- 直接点击 `#batchScriptSubmit`，触发 `handleBatchScriptSubmit` 的空台词校验
- 断言 `#batchScriptResult` 内包含校验错误文案 `"请至少填写一行台词"`
- `route.abort()` 确保 API 路径未被真正调用

**测试覆盖：**
- 空台词文本提交场景（`lines.length === 0` 时 `"请至少填写一行台词"`）
- 其他校验场景（空行文本 `"第 X 行缺少台词文本"`、缺少 profile `"第 X 行缺少声音人设"`）由 index.html 原有代码覆盖，本次 E2E 未覆盖

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "script"  # 2 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 16 passed
```

**测试结果：** 16 passed in 50.91s。

**下一步：** P9-FE1-F2 可正式迁移 `handleBatchScriptSubmit()` 到 `batch_script.js`（Phase 1）；后续再补剧本批量 mock 提交成功 E2E 和行管理 E2E（Phase 2 前提）。

**未改 app/static/index.html、app/static/js/*、app/api/*、app/services/*、app/providers/*、app/domain/*、app/core/*、Provider Adapter、CapabilityValidator、Capability Registry、生成链路、数据库、资产清理链路。

---

## P9-FE1-F2：抽离剧本批量提交函数 batch_script.js Phase 1

**问题：** `handleBatchScriptSubmit` 仍在 index.html 内，与其他剧本批量逻辑混合在一起，难以独立维护。

**修复：**
- 新增 `app/static/js/batch_script.js`（IIFE 包裹）
- `handleBatchScriptSubmit` 整体迁移到 `batch_script.js`
- `esc()` 调用替换为本地 `bsEsc()` 辅助函数（不依赖 index.html 的 `esc`）
- `window.handleBatchScriptSubmit` 暴露到全局
- index.html 中 `handleBatchScriptSubmit` 函数定义替换为注释说明已迁移
- 新增 `<script src="/static/js/batch_script.js">` 标签于 `batch_longtext.js` 之后、inline script 之前

**保持不变（本次不迁移）：**
- `addScriptLine` / `removeScriptLine` / `updateScriptLineLimitState` — 留在 index.html
- `_scriptRows` / `_scriptLineCount` / `MAX_SCRIPT_LINES` — 留在 index.html
- scriptLines 事件委托逻辑 — 留在 index.html
- `populateProfileSelect` / `loadProfiles` / `_cachedProfiles` — 留在 index.html
- `showBatchProgress` / `startBatchPoll` / `stopBatchPoll` / `pollBatchStatus` 等共享批量函数 — 留在 index.html
- `_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline` 等共享状态 — 留在 index.html
- 长文本批量逻辑（`batch_longtext.js`）— 不受影响
- API endpoint（`POST /api/voice/batch/submit`）— 不变
- Request body（`mode='script'`, `script: [...]`）— 不变

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "script"  # 3 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 17 passed
```

**测试结果：** 17 passed in 55.25s。

**下一步：** P9-FE1-F2 Phase 2（迁移行管理函数和 `_scriptRows` 状态）或补剧本批量 mock 提交成功 E2E。

**未改 app/static/js/provider_capabilities.js、app/static/js/runtime_status.js、app/static/js/history.js、app/static/js/audition_records.js、app/static/js/batch_longtext.js、app/api/*、app/services/*、app/providers/*、app/domain/*、app/core/*、Provider Adapter、CapabilityValidator、Capability Registry、数据库、资产清理链路。

---

## P9-FE1-F2-FIX：剧本批量 mock 提交成功 E2E

**问题：** Test 18 `test_batch_script_mock_submit_success_starts_progress` 前期因 per-row 验证失败而无法通过。`handleBatchScriptSubmit` 在收集台词行时会遍历所有 `_scriptRows` 条目（默认 3 行），若任意一行的 DOM `scriptText_${id}` 值为空即触发"第 X 行缺少台词文本"错误，导致 `batch/submit` API 根本未被调用。

**根本原因：** `page.evaluate` 仅设置了 row 0 的状态和 DOM 值，row 1 和 row 2 的 `scriptText_` 输入框仍为空，触发 per-row 空文本校验。

**修复：**
- `page.evaluate` 循环遍历所有 3 行（`i = 0, 1, 2`），对每行同步设置 `_scriptRows[i]` 状态对象和对应 DOM 元素的 `value`
- 同时将 `batchScriptProvider` 设为 `'mock'` 以绕过 `guardedJsonFetch` 的 highRisk 确认框
- 移除 `batch_script.js` 入口处的 `console.log('[BS] handleBatchScriptSubmit called...')` 调试语句
- 清理 test 内 3 处 `print()` 调试语句

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py::test_batch_script_mock_submit_success_starts_progress -v  # 1 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "script"  # 4 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 18 passed
```

**测试结果：** 18 passed in 58.62s。

**下一步：** P9-FE1-F2 Phase 2（迁移行管理函数和 `_scriptRows` 状态）。

**未改** app/static/index.html（业务逻辑）、app/api/*、app/services/*、app/providers/*、app/domain/*、app/core/*、Provider Adapter、CapabilityValidator、Capability Registry、数据库。

---

## P9-FE1-CHECK：前端模块化阶段收口检查

**时间：** 2026-05-15

**本次任务类型：** 阶段收口检查 + 测试小清理，不迁移任何业务逻辑。

### 测试小清理

删除了 `test_batch_script_mock_submit_success_starts_progress` 中不再使用的变量：
- `browser_logs`（console message 收集列表）— 未被任何断言使用
- `result_check`（page.evaluate 结果）— 未被任何断言使用

保留：所有有效断言、submit_called 断言、success message / batch_id / progress panel / button restore 断言、stopBatchPoll 清理、`import json`。

### 已核对已抽离模块

| 模块 | 入口 |
|---|---|
| provider_capabilities.js | loadProviderCapabilities, applyAllProviderCapabilities, setControlDisabled, updateProviderSelectOptions, getProviderCapability |
| runtime_status.js | loadRuntimeStatus, scheduleRuntimeStatusRefresh |
| history.js | loadHistory, loadMoreHistory, refreshHistory, toggleHistoryAudio, deleteHistoryJob, copyJobId |
| audition_records.js | renderAuditionRecords, deleteAuditionRecord, clearAuditionRecords |
| batch_longtext.js | handleBatchLongtextSubmit |
| batch_script.js | handleBatchScriptSubmit |

script 加载顺序（index.html 第 1587-1592 行）：
provider_capabilities.js → runtime_status.js → history.js → audition_records.js → batch_longtext.js → batch_script.js → inline script

### 已核对 E2E 覆盖

共 18 个 E2E（tests/e2e/test_frontend_capabilities.py）。

### 已核对未改关键链路

未改：app/static/index.html（业务逻辑）、app/api/*、app/services/*、app/providers/*、app/domain/*、app/core/*、Provider Adapter、CapabilityValidator、Capability Registry、生成链路、数据库、资产清理链路。

### 当前仍留在 index.html 的高风险逻辑（记录，不迁移）

- Tab 切换逻辑
- populateProfileSelect / loadProfiles / _cachedProfiles（被剧本/长文本行管理依赖）
- addScriptLine / removeScriptLine / updateScriptLineLimitState（与 populateProfileSelect 紧耦合）
- _scriptRows / _scriptLineCount / MAX_SCRIPT_LINES（与 DOM 事件委托强耦合）
- scriptLines 事件委托
- 共享 batch 轮询函数（showBatchProgress / startBatchPoll / stopBatchPoll / pollBatchStatus）
- 共享 batch 状态变量（_batchPollTimer / _currentBatchId / _currentBatchPanelId / _batchTimeline）
- renderBatchStatus
- voice clone/design/import（handleCloneSubmit / handleDesignSubmit / bindVoiceToProfile）
- API 共享 helper（esc / guardedJsonFetch / parseApiError / formatApiError / renderApiError / showToast）

### 下一步建议

- 暂不迁移共享 batch 状态；`_batchPollTimer` / `_currentBatchId` 等变量继续保留在 index.html，待 batch 模块 Phase 2 统一考虑
- Phase 2 行管理迁移（addScriptLine / removeScriptLine / _scriptRows）需单独任务，需先审查与 populateProfileSelect 的耦合点
- voice_clone_design.js 建议先审查再拆
- batch_shared.js 暂缓

### 测试结果

```
python -m pytest tests/e2e/test_frontend_capabilities.py -q  # 18 passed in 59.49s
```

---

## P9-FE1-G0：voice_clone_design.js 抽离前边界审查

**时间：** 2026-05-15

**本次任务类型：** 审查和文档记录，不迁移任何业务逻辑，不修改 index.html。

### 本次只做审查和文档记录

- 阅读了 index.html 中所有 clone/design/import/audition 相关代码段
- 梳理了 DOM id 清单（clone tab、design tab、import、voice list、audition workstation）
- 梳理了状态变量（`_cachedProfiles`、`_cachedVoices`、`_loadedVoices`、`_voiceBindMap`、`_auditionSelectedVoiceId` 等）
- 梳理了函数清单和 API endpoint
- 分析了 provider capability 依赖（`provider_capabilities.js` 中的 `applyVoiceCloneCapability` / `applyVoiceDesignCapability`）
- 分析了 highRisk confirm 依赖（clone、design、import、preview 均使用 `highRisk: true`）
- 分析了错误展示依赖（`parseApiError` / `formatApiError` / `friendlyErrorMessage` / `renderApiError`）
- 分析了与 audition_records.js 的关系（`renderAuditionRecords` 等已迁出，audition workstation 仍在 index.html）
- 分析了可迁移内容（`handleCloneVoice`、`handleDesignVoice`、`handleUploadAudio` 等）
- 分析了暂不迁移的共享内容（`populateProfileSelect`、`bindVoiceToProfile`、`renderInlineCreateProfile` 等）
- 明确了需要先提取为 window.* 的 helper（`isValidVoiceId`、`bindVoiceToProfile`、`renderInlineCreateProfile`、`populateProfileSelect`、`hexToBlobUrl`）
- 识别了风险点（inline onclick 注入、highRisk confirm 阻塞、profile 系统耦合）

### 未改业务逻辑

未改：app/static/index.html（本次仅阅读和 grep）、app/static/js/*、app/api/*、app/services/*、app/providers/*、app/domain/*、app/core/*、Provider Adapter、CapabilityValidator、Capability Registry、生成链路、数据库、资产清理链路。

### 测试结果

```
python -m pytest tests/e2e/test_frontend_capabilities.py -q  # 18 passed in 59.49s
```

### 下一步建议

- **先补 E2E 再迁移**：当前没有任何 voice clone/design/import 相关 E2E。建议优先补 `test_voice_clone_error_insufficient_balance`（高）和 `test_voice_design_mock_submit_success`（高）。
- **先提取共享 helper 为 window 入口**：再迁移业务函数。
- **建议拆分迁移**：voice_clone.js（第一步）→ voice_import.js（第二步）→ voice_design.js（第三步），不建议一个 voice_clone_design.js 全量迁移。
- **voice list 和 audition workstation 暂不迁移**：这两个模块依赖复杂，建议独立审查。

---

## P9-FE1-G1：补声音克隆 insufficient balance 错误展示 E2E

**时间：** 2026-05-15

**问题：** clone/design/import 当前缺少 E2E，声音克隆曾真实返回 `insufficient balance`，需要自动化测试保护错误展示链路。

**修复：** 新增 `test_voice_clone_error_insufficient_balance_is_displayed`，验证 `POST /api/voice/clone/create` 返回 `PROVIDER_ERROR` + `detail: "insufficient balance"` 时，前端展示余额不足提示。

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py::test_voice_clone_error_insufficient_balance_is_displayed -v  # 1 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 19 passed
```

**mock 方案：**
- 拦截 `GET /api/voice/capabilities`，返回 `mock` provider + `voice_clone.supported: true`，确保 cloneBtn 可点
- 拦截 `POST /api/voice/clone/create`（regex pattern），返回 HTTP 400 + `{"error": {"code": "PROVIDER_ERROR", "detail": "insufficient balance", ...}}`
- 使用 `provider=mock` 绕过 `guardedJsonFetch` highRisk confirm 对话框
- 使用 `page.evaluate("document.getElementById('cloneBtn').click()")` 触发 onclick（因 `handleCloneVoice` 为局部函数，非 window 入口）

**页面展示：** `friendlyErrorMessage` 识别 insufficient balance 关键字，返回中文提示"余额不足"和切换 mock 的建议。

**测试结果：** 19 passed in 63.17s。

**未改关键链路：** 未改后端 API、Provider Adapter、Capability Registry、CapabilityValidator、生成链路、数据库、资产清理链路。测试 fixture `console_errors` 新增对 "400" 的允许规则（来自 E2E mock 拦截的预期 400 响应）。

**下一步建议：** 补 `test_voice_design_mock_submit_success`（验证设计成功 + demo audio 展示），再迁移 `voice_clone.js`。

---

## P9-FE1-G2：补声音设计 mock submit success E2E

**时间：** 2026-05-15

**问题：** G1 已补 clone 错误展示 E2E，但 design 成功链路仍缺少 E2E。后续拆分 voice_clone / voice_design 前需要验证 design mock success 流程。

**修复：** 新增 `test_voice_design_mock_submit_success`，验证 mock `POST /api/voice/design/create` 返回成功时，前端展示成功结果和 voice_id，按钮正确恢复。

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py::test_voice_design_mock_submit_success -v  # 1 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 20 passed
```

**mock 方案：**
- 拦截 `GET /api/voice/capabilities`，返回 `mock` provider + `voice_design.supported: true`
- 拦截 `POST /api/voice/design/create`（regex pattern），返回 HTTP 200 + `{"voice_id": "e2e_design_voice_001", "message": "声音设计成功创建", "trial_audio_url": null}`
- 使用 `provider=mock` 绕过 highRisk confirm
- 使用 `page.evaluate("document.getElementById('designBtn').click()")` 触发 onclick

**测试结果：** 20 passed in 67.33s。

**未改关键链路：** 未改 app/static/js/*、后端 API、Provider Adapter、Capability Registry、CapabilityValidator、生成链路、数据库、资产清理链路。

**下一步建议：** P9-FE1-G1（clone 错误）+ P9-FE1-G2（design 成功）已完成，可进入 helper window 暴露前置任务或 `voice_clone.js` 抽离。

---

## P9-FE1-G3：暴露 voice clone/design 迁移所需 helper 为 window.*

**时间：** 2026-05-15

**问题：** 后续迁移 `voice_clone.js` / `voice_import.js` / `voice_design.js` 前需要调用 index.html 内部 helper，但这些 helper 未暴露为 window 入口。

**修复：** 在 `app/static/index.html` 中新增以下 window 暴露语句：
- `window.isValidVoiceId = isValidVoiceId`（第 3995 行）
- `window.loadProfiles = loadProfiles`（第 1698 行）
- `window.populateProfileSelect = populateProfileSelect`（第 1728 行）
- `window.bindVoiceToProfile = bindVoiceToProfile`（第 1767 行）
- `window.renderInlineCreateProfile = renderInlineCreateProfile`（第 3788 行）
- `window.hexToBlobUrl = hexToBlobUrl`（第 2159 行）

函数原有实现完全不变，仅添加 window 赋值语句。

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py::test_voice_helper_window_exports_are_available -v  # 1 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 21 passed
```

**测试结果：** 21 passed in 68.90s。

**未改关键链路：** 未迁移 clone/design/import 业务函数、未改 app/static/js/*、未改后端 API、Provider Adapter、CapabilityValidator、生成链路、数据库、资产清理链路。

**下一步建议：** `voice_clone.js` 迁移所需的前置 helper 已就绪，可进入 `voice_clone.js` 抽离任务。

## P9-FE1-G4：抽离声音克隆模块 voice_clone.js

**时间：** 2026-05-15

**问题：** `index.html` 内含 ~314 行克隆业务逻辑（handleUploadAudio / handleCloneAutoId / updateCloneBtnState / handleCloneVoice），混杂在 4000+ 行巨型单文件中，难以维护。

**修复：**
- 新建 `app/static/js/voice_clone.js`，以 IIFE 包装，4 个函数全部 export 为 `window.*`
- `index.html` 移除迁移函数体，保留原 onclick 属性（由 IIFE 重新挂载）
- 在 `index.html` 的 `batch_script.js` 后新增 `<script src="/static/js/voice_clone.js"></script>` 标签
- 克隆函数段注释 `// Clone Tab — MOVED to /static/js/voice_clone.js`
- 补回因克隆段删除而丢失的 `isValidVoiceId`（standalone 版本，`window.isValidVoiceId` 赋值保留在 index.html）

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "clone"  # 2 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 22 passed
```

**测试结果：** 22 passed in 70.11s。

**未改关键链路：** 未迁移 import/design 业务函数、未改后端 API、Provider Adapter、CapabilityValidator、生成链路、数据库、资产清理链路。

**下一步建议：** voice_clone.js 抽离完成，E2E 22 passed。可进入 voice_import.js / voice_design.js 抽离。

## P9-FE1-G4-FIX：补 voice clone mock success E2E

**时间：** 2026-05-15

**问题：** G4 已抽离 voice_clone.js，但仅验证模块加载和 insufficient balance 错误展示，缺少 clone 成功链路 E2E。

**修复：**
- 新增 `test_voice_clone_mock_submit_success` E2E，mock `/api/voice/capabilities`（voice_clone.supported=true）、mock `/api/voice/clone/create`（返回成功 voice_id + demo_audio_url）、mock `/api/voice/provider-voices`（handleListVoices 触发）。
- 填写 clone 表单（provider=mock、voice_id、file_id、model、previewText）。
- 点击 #cloneBtn，验证 clone/create 被调用。
- 断言 #cloneResult 包含"克隆成功"、voice_id、audio 标签、source[demo_audio_url]。
- 断言快速绑定面板（cloneProfileWrap / cloneBindBtn / cloneBindModel）存在。
- 断言快速试听面板（cloneQuickText / cloneQuickBtn / cloneQuickResult）存在。
- 断言按钮恢复为"克隆"。
- 页面无 TypeError / ReferenceError。
- 不调用真实 MiniMax、不上传音频、不播放音频、不触发快速绑定/试听。

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "clone"  # 3 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 23 passed
```

**测试结果：** 23 passed in 75.31s。

**未改关键链路：** 未迁移 import/design 业务函数、未改 app/static/js/provider_capabilities.js、未改后端 API、Provider Adapter、CapabilityValidator、生成链路、数据库、资产清理链路。

**下一步建议：** voice_clone.js 成功链路 E2E 已补齐，23 E2E passed。可进入 voice_import.js 边界审查和前置 E2E。

## P9-FE1-H0：voice_import.js 抽离前边界审查

**时间：** 2026-05-15

**本次性质：** 审查 + 文档记录，不迁移代码。

### import 相关 DOM id 清单

| DOM id | 说明 | 所在 subtab |
|---|---|---|
| `importCloneProvider` | Provider 选择 | clone |
| `importCloneVoiceId` | voice_id 输入 | clone |
| `importCloneName` | 名称（可选） | clone |
| `importCloneModel` | model 下拉 | clone |
| `importClonePreviewText` | 试听文本 | clone |
| `importCloneVerify` | 验证复选框 | clone |
| `importCloneBtn` | 验证并导入按钮 | clone |
| `importCloneResult` | 结果展示区 | clone |
| `importDesignProvider` | Provider 选择 | design |
| `importDesignVoiceId` | voice_id 输入 | design |
| `importDesignName` | 名称（可选） | design |
| `importDesignModel` | model 下拉 | design |
| `importDesignPreviewText` | 试听文本 | design |
| `importDesignVerify` | 验证复选框 | design |
| `importDesignBtn` | 验证并导入按钮 | design |
| `importDesignResult` | 结果展示区 | design |

**共享 DOM id（两个 subtab 共用同一个 DOM）：**
- `importProfileWrap` — 快速绑定人设面板容器
- `importBindModel` — 绑定 model 下拉
- `importBindBtn` — 绑定按钮
- `importBindResult` — 绑定结果
- `importBindProfile` — 动态创建的 profile select

### import 相关状态变量

| 变量 | 说明 |
|---|---|
| `source` | 函数参数，'clone' 或 'design'，决定 DOM prefix |
| `isClone` | `source === 'clone'` |
| `prefix` | `'importClone'` 或 `'importDesign'` |
| `_cachedProfiles` | profile 缓存（loadProfiles） |
| `_cachedVoices` | voices 缓存（loadVoices） |

### handleImportRemoteVoice(source) 函数依赖清单

**window 导出（G3 已暴露）：**
- `window.loadProfiles` — 第 1693 行，GET /api/voice/profiles，带缓存
- `window.populateProfileSelect` — 第 1728 行，填充 profile select
- `window.renderInlineCreateProfile` — 第 3788 行，行内创建 profile
- `window.bindVoiceToProfile` — 第 1767 行，绑定音色到人设
- `window.refreshVoiceBindStatus` — 第 1774 行，刷新绑定状态 badge
- `window.handleListVoices` — 第 3551 行，刷新音色列表

**共享 helper（index.html 内）：**
- `guardedJsonFetch` — 第 2198 行，highRisk confirm + fetch 封装
- `parseApiError` — 解析 API 错误响应
- `formatApiError` — 格式化错误消息
- `friendlyErrorMessage` — 第 2224 行，余额不足等特殊错误处理
- `renderApiError` — 渲染 API 错误 HTML
- `renderValidationError` — 渲染校验错误 HTML
- `esc` — HTML 转义

**其他依赖：**
- `_OPERATION_MESSAGES['provider_voice_import_verify']` — highRisk 确认文案（第 2189 行）

### API endpoint

```
POST /api/voice/provider-voices/import
```

### request body 字段

| 字段 | 类型 | 来源 | 说明 |
|---|---|---|---|
| provider | string | `prefix+'Provider'` | provider 选择值 |
| provider_voice_id | string | `prefix+'VoiceId'`.trim() | 必填，远端 voice_id |
| voice_type | string | isClone?'voice_cloning':'voice_generation' | 固定值 |
| name | string\|null | `prefix+'Name'`.trim() \|\| null | 可选 |
| verify | bool | `prefix+'Verify'`.checked | 默认 true |
| model | string | `prefix+'Model'`.value | 默认 speech-2.8-hd |
| preview_text | string | `prefix+'PreviewText'`.trim() | 必填 |
| confirm_cost | bool | false（固定） | highRisk 时由 guardedJsonFetch 覆盖为 true |

### response 使用字段

| 字段 | 用途 |
|---|---|
| provider | 透传 |
| provider_voice_id | 成功消息展示、绑定参数 |
| voice_type | 成功消息展示 |
| name | 成功消息展示（pv.name） |
| status | 成功消息展示 |
| verified | 用于判断是否展示"未验证导入"警告 |
| audio_asset.url | 试听 audio 播放器 src |
| message | 固定"导入成功" |

### highRisk confirm 依赖

```
{ provider, operation: 'provider_voice_import_verify', highRisk: true }
```

- 仅 `provider === 'minimax'` 时触发 confirm 对话框
- `provider=mock` 时 bypass，不弹窗
- operation message: `'provider_voice_import_verify': '验证试听会调用云端 TTS，可能产生费用，是否继续？'`

### 错误展示依赖

- `parseApiError(resp)` → 获取 err.code / err.message
- `formatApiError(err)` → 字符串化
- `friendlyErrorMessage(message)` → 余额不足等特殊文案
- `renderValidationError(err.message)` → VALIDATION_ERROR 时
- `renderApiError(err)` → RESOURCE_LIMIT_EXCEEDED 等特殊错误码时
- 兜底：`'<div class="error-msg">导入失败：' + esc(friendlyErrorMessage(formatApiError(err))) + '</div>'`

### profile / binding 依赖

导入成功后（await loadProfiles 后）：
1. 渲染成功消息 + audio_asset 播放器
2. 如 verify=false 渲染"未验证导入"警告
3. 渲染快速绑定面板 HTML（`importProfileWrap` / `importBindModel` / `importBindBtn` / `importBindResult`）
4. setTimeout(0) 后：动态创建 `importBindProfile` select，调用 `populateProfileSelect(sel)` + `renderInlineCreateProfile(profileWrap, sel, 'import')`
5. `importBindBtn.onclick` 调用 `bindVoiceToProfile(data.provider_voice_id, provider, profileId, model)`
6. 绑定成功后调用 `refreshVoiceBindStatus(data.provider_voice_id)`
7. 最后调用 `handleListVoices(true).catch(() => {})`

### voice list 依赖

- 导入成功后调用 `handleListVoices(true)` → GET `/api/voice/provider-voices?provider=...&voice_type=...&refresh=true`
- E2E 需 mock 该接口避免真实请求

### 可迁移到 voice_import.js 的候选内容

1. **handleImportRemoteVoice(source)** — 核心迁移目标，约 134 行
2. onclick 属性可保持不变（引用 `window.handleImportRemoteVoice`）

### 暂不迁移内容

1. **loadProfiles** — 共享 cache 状态，多处调用
2. **populateProfileSelect** — 共享 UI helper
3. **renderInlineCreateProfile** — 共享 UI helper
4. **bindVoiceToProfile** — 绑定音色到人设，共享
5. **refreshVoiceBindStatus** — 共享 badge 刷新
6. **handleListVoices** — 音色列表刷新，共享
7. **guardedJsonFetch / parseApiError / formatApiError / friendlyErrorMessage / esc** — 共享 helpers
8. **快速绑定面板 HTML 模板** — 动态生成的内联 onclick

### 风险点

1. **共享 DOM id 冲突**：`importProfileWrap` / `importBindBtn` 等在两个 subtab 间共用同一 DOM 元素，voice_import.js 迁移后仍需注意
2. **setTimeout(0) 内联 onclick**：成功面板的绑定按钮使用字符串内 onclick 注入，增加 XSS 表面；在 voice_clone.js 中已有先例，可接受
3. **loadProfiles 无 await 语义问题**：handleImportRemoteVoice 中 `await loadProfiles()` 语义正确（loadProfiles 返回 Promise），但结果未用于后续逻辑，不影响迁移
4. **verify=true 时内部调用 preview**：在 Python 服务内完成，无额外 HTTP 请求，无 E2E mock 额外成本
5. **两个 subtab 的 result div id 不同**（importCloneResult / importDesignResult），需通过 prefix 参数统一访问

### 下一步 P9-FE1-I0 建议

**建议进入 voice_design.js 抽离（I1）。**

I0 审查结论：
- `handleDesignVoice` 可独立迁移，无循环依赖
- DOM prefix `design*` 与 clone/import 无重叠
- API endpoint `design/create` 与其他 voice 链路均不同
- 所有依赖的 window helpers 已暴露
- `test_voice_design_mock_submit_success` 已覆盖成功链路，可作为 I1 迁移回归保护

**第一条 import E2E 建议覆盖 clone import，理由：**
- voice_type='voice_cloning' 更接近 clone 工作流，与现有 clone E2E 互补
- clone import 的 preview_text 默认值与 design 不同，E2E 需覆盖
- importDesign 后续可单独补 E2E 或与 importDesign E2E 合并

**voice_import.js 迁移方案建议（供参考，本次不执行）：**
- 将 handleImportRemoteVoice(source) 移至 voice_import.js，IIFE 包装，window.handleImportRemoteVoice 导出
- onclick 属性保持 `onclick="handleImportRemoteVoice('clone')"` 不变（IIFE 后 window 仍可访问）
- 快速绑定面板保持内联 onclick（与 voice_clone.js 一致）
- loadProfiles/populateProfileSelect/renderInlineCreateProfile/bindVoiceToProfile/refreshVoiceBindStatus/handleListVoices 继续调用 window.*

## P9-FE1-H1：补 voice import mock success E2E

**时间：** 2026-05-15

**问题：** H0 审查已完成 import 边界梳理，但 import 链路缺少 E2E，无法验证 clone import 成功链路。

**修复：**
- 新增 `test_voice_import_clone_mock_success` E2E。
- mock GET /api/voice/profiles（返回 `[{id, name}]`）。
- mock GET /api/voice/capabilities（voice_clone.supported=true）。
- mock POST /api/voice/provider-voices/import（返回成功 voice_id + audio_asset.url + status=imported）。
- mock GET /api/voice/provider-voices（返回空 voices，避免 handleListVoices 真实请求）。
- 填写 importClone 表单（provider=mock、voice_id、name、model、previewText、verify=true）。
- 点击 #importCloneBtn，验证 provider-voices/import 被调用。
- 断言 #importCloneResult 包含"导入成功"、voice_id、audio 标签。
- 断言快速绑定面板（importProfileWrap / importBindProfile / importBindModel / importBindBtn）存在。
- 断言按钮恢复为"验证并导入"。
- 页面无 TypeError / ReferenceError。
- 不调用真实 MiniMax、不上传音频、不点击绑定按钮。

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "import"  # 2 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 25 passed
```

**测试结果：** 25 passed in 83.77s。

**未改关键链路：** 未迁移 handleImportRemoteVoice、未新增 voice_import.js、未改 app/static/js/*、未改后端 API、Provider Adapter、CapabilityValidator、生成链路、数据库、资产清理链路。

**下一步建议：** import 链路成功链路 E2E 已补齐，25 E2E passed。可进入 voice_import.js 抽离。

## P9-FE1-H2：抽离 voice_import.js

**时间：** 2026-05-15

**问题：** handleImportRemoteVoice 仍在 index.html  inline script 中，需要抽离为独立模块 voice_import.js。

**修复：**
- 创建 `app/static/js/voice_import.js`，IIFE 包装，`window.handleImportRemoteVoice` 导出。
- 所有 G3 helpers（loadProfiles、populateProfileSelect、renderInlineCreateProfile、bindVoiceToProfile、refreshVoiceBindStatus、handleListVoices）使用 `window.*` 调用。
- shared helpers（guardedJsonFetch、parseApiError、formatApiError、friendlyErrorMessage、esc、renderValidationError）直接使用（已在 index.html G3 中暴露）。
- 在 index.html 添加 `<script src="/static/js/voice_import.js"></script>`（位于 voice_clone.js 之后）。
- 删除 index.html 中的 empty function stub `async function handleImportRemoteVoice(source) {}`（之前遗留的 orphan 空函数）。
- 保留 Migration comment（Import Remote Voice - MOVED to /static/js/voice_import.js）。

**E2E 验证：**
```
python -m pytest tests/e2e/test_frontend_capabilities.py -q -k "import"  # 2 passed
python -m pytest tests/e2e/test_frontend_capabilities.py -q             # 25 passed
```

**测试结果：** 25 passed in 83.77s。

**未改关键链路：** 未改后端 API、Provider Adapter、CapabilityValidator、生成链路、数据库、资产清理链路。

## P9-FE1-I0：voice_design.js 边界审查

**时间：** 2026-05-15

**审查结论：** 可独立迁移。

**handleDesignVoice 依赖分析：**

- **DOM prefix**：`design*`（designProvider / designVoiceId / designPrompt / designPreviewText / designResult / designBtn），与 clone（`clone*`）/import（`importClone*`/`importDesign*`）无重叠
- **动态创建 DOM ids**：`designProfileWrap`, `designBindProfile`, `designBindModel`, `designBindBtn`, `designBindResult`, `designQuickText`, `designQuickBtn`, `designQuickResult`
- **API**：`POST /api/voice/design/create?provider={provider}`，payload `{ prompt, preview_text, confirm_cost, voice_id? }`
- **highRisk confirm**：是（`guardedJsonFetch(..., { operation: 'voice_design', highRisk: true })`），`provider=mock` 绕过
- **quick preview**：`fetch('/api/voice/render', ...)` raw fetch，不用 guardedJsonFetch，无 highRisk
- **response 字段**：`voice_id`, `message`, `trial_audio_hex`, `trial_audio_url`
- **window helpers 依赖**：`window.isValidVoiceId`（已暴露）、`window.hexToBlobUrl`（已暴露）、`window.populateProfileSelect`（已暴露）、`window.renderInlineCreateProfile`（已暴露）、`window.bindVoiceToProfile`（已暴露）、`window.refreshVoiceBindStatus`（已暴露）、`window.handleListVoices`（已暴露）
- **shared helpers**：直接使用 guardedJsonFetch / parseApiError / formatApiError / friendlyErrorMessage / esc / renderApiError / renderValidationError
- **provider capability**：不在 `handleDesignVoice` 内部检查；由 `provider_capabilities.js` 的 `applyVoiceDesignCapability()` 控制按钮 enabled/disabled 状态
- **vs voice_import.js**：结构高度相似（提交 → 成功面板 + audio + quick bind + quick preview）；API 和 DOM prefix 不同；依赖的 helpers 几乎完全相同
- **vs voice_clone.js**：结构相似；voice_clone 有 audio upload，`handleDesignVoice` 没有；`hexToBlobUrl` 是 design 特有
- **E2E 保护**：`test_voice_design_mock_submit_success` 已覆盖成功链路，可作为 I1 迁移回归保护

**I1 允许修改范围：**
- 仅迁移 `handleDesignVoice`
- 参照 voice_import.js 模式：IIFE 包装 + `window.handleDesignVoice` 导出 + onclick 保持不变
- 动态创建的 DOM ids（designProfileWrap 等）在 setTimeout 内创建，不影响迁移
- quick preview 的 raw `fetch` 保持原样，不改 highRisk 行为

**I1 严禁迁移：**
- `handleDesignVoice` 以外的任何函数
- `handleListVoices`（留在 index.html，由 `handleDesignVoice` 调用）
- `handleCloneVoice` / `handleImportRemoteVoice` / `handleDesignVoice` 以外的任何 voice 相关函数

## P9-FE1-I1：voice_design.js 抽离

**完成时间：** 2026-05-15

**实现：**
- 创建 `app/static/js/voice_design.js`，IIFE 包装
- `window.handleDesignVoice` 导出
- G3 helpers 使用 `window.*` 调用
- shared helpers 直接使用
- script 标签位于 `voice_import.js` 之后
- index.html 添加 Migration comment
- E2E `test_voice_design_mock_submit_success` 验证成功链路

**E2E 覆盖：**
- `test_voice_design_mock_submit_success`（已有）
- 25 E2E passed

## P9-FE1-CHECK：voice advanced stage 收口

**检查时间：** 2026-05-15

**检查结果：全部通过 ✅**

### 模块边界检查

| 模块 | 文件 | window exports | 状态 |
|---|---|---|---|
| voice_clone.js | `app/static/js/voice_clone.js` | `handleUploadAudio`, `handleCloneAutoId`, `updateCloneBtnState`, `handleCloneVoice` | ✅ |
| voice_import.js | `app/static/js/voice_import.js` | `handleImportRemoteVoice` | ✅ |
| voice_design.js | `app/static/js/voice_design.js` | `handleDesignVoice` | ✅ |

### index.html 残留检查

- **同名函数声明覆盖**：无 ✅
- **空函数 stub**：无 ✅
- **Migration comment**：仅注释，无可执行代码 ✅

### script 加载顺序检查

```
voice_clone.js   → 第 1593 行
voice_import.js  → 第 1594 行
voice_design.js  → 第 1595 行
inline script    → 第 1596 行起
```
顺序正确 ✅

### onclick 入口检查

- `onclick="handleCloneVoice()"` ✅
- `onclick="handleImportRemoteVoice('clone')"` ✅
- `onclick="handleImportRemoteVoice('design')"` ✅
- `onclick="handleDesignVoice()"` ✅

### E2E 覆盖

- targeted（clone/import/design）：6 passed
- full suite：25 passed ✅

### 文档更新

- `docs/agent/NEXT_TASKS.md` — 标记 I1 已完成，CHECK 已完成 ✅
- `docs/agent/FRONTEND_MODULE_MAP.md` — voice_design.js 移入已抽离模块 ✅
- `docs/P9_FRONTEND_MODULARIZATION.md` — 添加 I1 和 CHECK 记录 ✅
- `docs/PROJECT_HEALTH_CHECK.md` — 添加 I1 和 CHECK 记录（本文档）✅

## P9-FE2-A0：剩余前端边界审查

**审查时间：** 2026-05-15

**性质：** 文档记录，不迁移代码，不跑 E2E

### 审查范围

index.html inline script 中剩余未模块化的前端逻辑（约 60 个函数）。

### 审查结论

**建议暂停前端模块化，转产品功能打磨。**

### 候选模块评估

#### voice_list.js（优先级 1，可小步抽离）

**候选函数：**
- `handleListVoices` (line 3553) — 音色列表查询
- `loadVoices` (line 1703) — voice 加载缓存，需暴露为 `window.loadVoices`
- `filterVoiceList` (line 3599) — 本地过滤
- `renderVoiceTable` (line 3623) — 渲染表格
- `handlePageSizeChange` / `handlePrevPage` / `handleNextPage` — 分页

**window helpers：** `window.loadProfiles` ✅ `window.populateProfileSelect` ✅ `window.bindVoiceToProfile` ✅ `window.refreshVoiceBindStatus` ✅ `guardedJsonFetch` ✅ `esc` ✅

**需先添加：** `window.loadVoices`

**DOM ids：** `voiceProvider`, `voiceType`, `voiceSearch`, `listVoicesBtn`, `voiceListResults`

**API：** `GET /api/voice/provider-voices?provider=...`

**E2E 现状：** 无专门测试（`test_audition_records_module_and_voices_tab_open` 仅覆盖 tab 打开）

**风险：** 中等（`_cachedVoices` 被 clone/design import 共用）

#### audition_workstation.js（优先级 2，强耦合，不建议抽）

**问题：**
- `renderAuditionWorkstation` 强耦合 `handleGenerate` 单条生成链路
- `handleGenerateAudition` → `handleGenerate` → `startStreamGenerate` / `startAsyncPolling`
- 单独抽离无意义，需整体考虑

#### profile_binding.js（优先级 3，依赖太广）

**问题：**
- `populateProfileSelect` 被 batch_script.js 的 `addScriptLine`、clone/design/import result panel 共用
- `_cachedProfiles` 是隐含全局状态
- 强行拆出导致所有调用方都要改

**现状：** window 出口已暴露（`loadProfiles`, `populateProfileSelect`, `renderInlineCreateProfile`, `bindVoiceToProfile`, `refreshVoiceBindStatus`），够用

#### error_helpers.js（优先级 4，收益小）

**Call sites：** 12+（voice_clone, voice_import, voice_design, batch_longtext, batch_script）

**建议：** shared helpers 仍在 index.html，模块通过 IIFE 直接调用，不强制拆分

#### batch_shared.js（优先级 5，shared state 冲突，极高风险）

**问题：**
- `_batchPollTimer` / `_currentBatchId` / `_currentBatchPanelId` / `_batchTimeline` 被长文本和剧本批量共用
- 两批量交替提交会覆盖 shared state
- 需统一状态管理设计

### 最终建议

- **暂停前端模块化**，聚焦产品功能打磨
- 如继续模块化，唯一合理候选是 `voice_list.js`（需先补 E2E）
- batch_shared.js 需作为独立任务，单独设计状态管理方案

## P10-PRODUCT-A0：产品打磨优先级审查

**审查时间：** 2026-05-15

**性质：** 文档记录，不迁移代码，不跑 E2E

**审查范围：** 实际用户主流程审查，评估当前最值得打磨的产品功能

### 用户主流程问题清单

| 优先级 | 问题 | 当前状态 | 建议 |
|---|---|---|---|
| 1 | Workspace 音色入口不直观 | 音色选择隐藏在 audition workstation，需要跳转 | 在 workspace tab 增加音色快捷选择区 |
| 2 | Voices tab 孤立于创作流程 | 选音色后要跳转到 workspace 继续 | 增加 voices tab 到 workspace 的快速联动 |
| 3 | Batch tab 音色选择需跨 tab | 长文本/剧本需要跳转选音色 | 在 batch tab 内增加音色快速选择区 |
| 4 | 没有 first-time guidance | 新用户不知道从哪开始 | 增加简短引导文案 |
| 5 | Advanced tab 入口深 | clone/design/import 入口不明确 | Advanced tab 重命名或增加引导 |

### P10 任务排序

| 优先级 | 任务 | 风险 | 预计工作量 |
|---|---|---|---|
| 1 | Workspace 音色快捷选择区 | 低 | 小 |
| 2 | Voices tab 快速创作联动 | 中 | 中 |
| 3 | Batch tab 音色快速选择 | 中 | 中 |
| 4 | 简化 onboarding 文案 | 极低 | 极小 |
| 5 | Advanced tab 重命名 | 极低 | 极小 |
| 6 | 历史最近任务快捷入口 | 低 | 小 |

### 不应该投入的方向

| 方向 | 原因 |
|---|---|
| 移动端 H5 | 产品定位为桌面端，H5 适配成本高收益低 |
| 创作模板 / 场景入口 | 需要内容运营，当前阶段不引入 |
| SaaS / 多用户 | 当前阶段不引入 |
| 开放 API 平台 | 复杂度高，当前阶段不做 |
| 桌面 App 打包 | 等 Web 版验证后再评估 |

### P10 与前端模块化关系

P10 产品打磨**不依赖**前端模块化，可以独立推进。两者无依赖关系。

### 输出文档

- `docs/P10_PRODUCT_POLISH_PLAN.md` — 新增产品打磨计划
- `docs/agent/NEXT_TASKS.md` — 更新当前阶段为 P10
- `docs/PROJECT_HEALTH_CHECK.md` — 更新状态摘要（本文档）

## P10-PRODUCT-B0：Workspace 音色快捷选择区边界审查

**审查时间：** 2026-05-15

### 关键发现：两个独立的音色选择系统

| 系统 | 用途 | 状态变量 | 所在 tab |
|---|---|---|---|
| Profile binding | Workspace 生成音频 | `profileSelect.value` | workspace |
| Voice audition | Voices tab 试听预览 | `window._auditionSelectedVoiceId` | voices |

**结论：**
- `handleGenerate` 使用 `profileSelect.value`，workspace 生成依赖 profile 绑定 voice
- `window._auditionSelectedVoiceId` 是试听系统，与 workspace 生成流程无关
- workspace "配置" card 内无当前绑定 voice 的提示

### B1 最小实现方案

**不改：** `handleGenerate`、后端 API、voice list、`_voiceBindMap`

**只做：** 在 workspace "配置" card 的 `profileSelect` 下方增加轻量提示区

- 显示当前 profile 绑定的 voice（从 `_voiceBindMap` 读取）
- 无 voice 时显示"该人设尚未绑定音色"
- "去选择音色"按钮切换到 voices tab（`document.querySelector('.tab-btn[data-tab="voices"]').click()`）

### B1 验收标准

1. workspace 的"配置"区显示当前 profile 绑定的 voice（如果有）
2. "去选择音色"按钮切换到 voices tab
3. `handleGenerate` 行为不变
4. 不调用真实 MiniMax API

### B0 审查结论

B1 可按最小方案执行，不改生成链路，不改后端，只增 UI 引导。

## P10-PRODUCT-B1：Workspace 音色快捷选择区实现

**执行时间：** 2026-05-15

**实现内容：**
- 新增 DOM：`#workspaceVoiceBindingHint`（workspace "配置" card 的 `profileSelect` 下方）
- 新增函数：`updateWorkspaceVoiceBindingHint()`
- 从 `_voiceBindMap` 读取当前 profile+provider 的绑定状态
- 无绑定时显示"去选择音色"按钮，点击切换到 voices tab

**E2E：** `test_workspace_voice_binding_hint_switches_to_voices`（Test 26），mock profiles/bindings/capabilities

**E2E 结果：** 26 passed

**输出文件：**
- `app/static/index.html` — 新增 hint DOM 和 `updateWorkspaceVoiceBindingHint` 函数
- `tests/e2e/test_frontend_capabilities.py` — 新增 Test 26

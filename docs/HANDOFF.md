# 当前状态与接手说明

## 项目概览

Voice Lab 是一个可扩展的声音生成中台，已完成 P0-P3 四个阶段，覆盖 MiniMax T2A 全系列接口 + 生产级可观测性。

## 当前状态

- **分支**：main（稳定）/ dev（开发）
- **测试**：234 passed, 6 skipped (e2e)
- **Python**：3.11+
- **技术栈**：FastAPI + SQLModel + SQLite + httpx + websockets

## 已完成阶段

### P0：项目基础
- FastAPI 应用骨架、SQLModel 数据模型
- 单条 T2A 同步生成、多版本试音
- 资产保存与下载、Mock Provider 完整闭环

### P1：Voice Catalog + Binding
- Provider Voice 列表同步（refresh 机制）
- VoiceBinding CRUD（软删除、优先级、duplicate 检查）
- T2A 响应解析硬化（hex/url/subtitle）
- 集成一致性审查（枚举、白名单、错误码统一）

### P2：MiniMax 全接口
- 异步 T2A（提交 + 轮询 + 自动下载）
- Voice Clone（上传 + 克隆）
- Voice Design（文字描述生成声音）
- Voice Delete（克隆/设计声音删除）
- 统一 4-Tab 测试面板
- E2E 真实 API 测试套件

### P3：日志管理、可观测性与报告分析
- 结构化 JSON 日志 + 日志文件按天轮转
- request_id 全链路传播（contextvars + ASGI 中间件）
- Provider 调用日志（9 个 HTTP 调用自动记录）
- 错误处理增强（自动日志 + 500 安全响应）
- Provider 调用审计表（provider_call_logs）
- 审计查询 API（过滤/分页/排序）
- 统计聚合 API（总览/按 provider/按 API/按天趋势）
- 管理面板 admin.html（可视化仪表板）
- 错误重试（指数退避，502/503/504 + 超时自动重试）
- 健康检查增强（数据库/存储/Provider 三维检查）

### P4：T2A WebSocket 流式语音生成
- StreamAudioChunk 基类 + MiniMax/Mock WebSocket 适配器
- StreamRenderService（验证 → RenderPlan → VoiceJob → 流式 chunk → 保存 AudioAsset）
- WebSocket 端点 `/api/voice/ws/render`（消息流：connected → started → audio_chunk × N → completed）
- 前端流式播放器（T2A Tab 新增"流式生成"模式，base64 chunk 拼接后播放）
- 集成测试（8 个端到端测试覆盖完整链路 + 边界条件）

### P5：前端产品功能增强
- T2A 参数调节（语速/音量/音调/情绪）+ 音频格式选择 + 流式模式字幕隐藏
- 绑定管理 Tab（查看/创建/删除 VoiceBinding，第 5 个 Tab）
- 音色列表增强（搜索过滤 + 一键绑定到人设 + 50 条截断）
- Job 列表 API（GET /api/voice/jobs 过滤/分页）+ T2A 历史记录面板
- 流式错误 detail 传播（MiniMax 原始 status_msg 透传到前端和日志）

### P6：批量编排引擎（长文本 + 多角色剧本）
- 文本分段服务（auto/paragraph/sentence 三种策略）
- 批量编排 Service（串行生成 + 单段失败不阻断 + retry 重试）
- 音频合并（pydub 拼接 + 段间静音 + 字幕时间轴偏移）
- 批量 API（submit/status/download/retry 四个端点）
- 前端批量生成 Tab（长文本模式 + 剧本模式 + 进度轮询 + 合并播放）

## API 端点一览

### 语音生成
```
POST /api/voice/render                        同步 T2A
POST /api/voice/render/async                  异步 T2A 提交
GET  /api/voice/render/async/{id}/status      异步状态轮询
WS   /api/voice/ws/render                     流式 T2A（WebSocket）
POST /api/voice/variants/render               多版本试音
GET  /api/voice/jobs                          任务列表（过滤/分页）
POST /api/voice/batch/submit                  批量任务提交（长文本/剧本）
GET  /api/voice/batch/{id}/status             批量任务进度
GET  /api/voice/batch/{id}/download           批量合并音频下载
POST /api/voice/batch/{id}/retry              重试失败段
```

### 声音管理
```
POST /api/voice/clone/upload                  上传克隆音频
POST /api/voice/clone/create                  执行克隆
POST /api/voice/design/create                 文字生成声音
POST /api/voice/voices/delete                 删除声音
GET  /api/voice/provider-voices               音色列表
```

### Profile & Binding
```
GET/POST /api/voice/profiles                  声音人设
GET/POST /api/voice/profiles/{id}/bindings    绑定管理
PATCH/DELETE /api/voice/bindings/{id}         绑定修改
```

### 任务与资产
```
GET  /api/voice/jobs/{job_id}                 任务详情
GET  /api/voice/assets/{id}                   资产元信息
GET  /api/voice/assets/{id}/download          下载文件
```

### 管理与运维
```
GET  /health                                  快速探活
GET  /health/detail                           详细健康检查
GET  /api/admin/call-logs                     调用审计查询
GET  /api/admin/stats/summary                 统计聚合总览
GET  /api/admin/stats/daily                   每日趋势
```

## 前端入口

- 测试面板：`/static/index.html`（6-Tab：T2A / 音色管理 / 克隆 / 设计 / 绑定管理 / 批量生成）
- 管理面板：`/static/admin.html`（统计仪表板 + 调用日志 + 趋势图）

## 启动方式

```bash
pip install -r requirements.txt
cp .env.example .env  # 编辑填入 MINIMAX_API_KEY
uvicorn app.main:app --reload
```

## 测试

```bash
python -m pytest tests/ -x -q           # Mock 测试（234 passed）
python -m pytest tests/ -m e2e -x -v    # 真实 API 测试（需 API Key）
```

## 未完成项

| 项目 | 说明 | 优先级 |
|------|------|--------|
| ~~P2-E T2A WebSocket~~ | ~~已在 P4 完成~~ | ~~完成~~ |
| 多 Provider 适配 | OpenAI TTS / Azure / ElevenLabs | 中 |
| 批量任务编排 | 多段文本→多音频→合并 | 中 |
| 多用户/租户 | 独立平台层模块 | 按需 |
| 额度/计费 | 独立平台层模块 | 按需 |
| API Key 管理 | 独立平台层模块 | 按需 |
| 对象存储 | 替换本地 storage | 按需 |

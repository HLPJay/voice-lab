# P7-I 真实 MiniMax 能力验证与修复收口报告

---

## 1. 阶段背景

P7-H 已确认工程链路可用，但真实 MiniMax 能力待 smoke test。
P7-I 的目标是用低成本方式验证真实能力，并修复验证过程中暴露的问题。

本阶段不做大规模产品开发，不测试高成本声音克隆/声音设计，重点是能力验证、边界修复、统计修复和测试体系治理。

---

## 2. 验收基线

| 项目 | 详情 |
|---|---|
| 验收基线 commit | `62b8ee8` |
| 分支 | dev |
| 测试时间 | 2026-05-13 |
| 测试方式 | 真实 MiniMax smoke test + mock 自动化测试 + 浏览器手工验证 |

---

## 3. 真实 MiniMax Smoke Test 结论

| 能力 | 真实 MiniMax 是否测试 | 结果 | 备注 |
|---|---:|---|---|
| 同步 T2A | 是 | ✅ 通过 | url / hex / 音频资产可用 |
| 异步 T2A | 是 | ✅ 通过 | 曾发现 subtitle end=0.0，已修复 |
| 批量长文本 | 是 | ✅ 通过 | merged audio / subtitle 可用 |
| 批量剧本 | 是 | ✅ 通过 | 多角色分段正常 |
| provider voice preview | 是 | ✅ 通过 | audio_asset.url 正常 |
| WebSocket 流式 | 是，浏览器简测 | ✅ 通过 | ws_complete / stream_render_success |
| 音频播放 / 下载 | 是 | ✅ 通过 | 浏览器 206 Partial Content 正常 |
| 任务历史 | 是 | ✅ 通过 | API 正常 |
| Admin 统计 | 是，手工检查 | ✅ 通过（历史数据受限） | 新数据可统计，历史缺失通过 AudioAsset fallback 尽量补齐 |
| 声音克隆 | 否 | ⏸ 暂缓 | 高成本，后续单独立项 |
| 声音设计 | 否 | ⏸ 暂缓 | 高成本，后续单独立项 |

---

## 4. 自动化测试结果

```bash
python -m pytest tests/test_resource_guard.py -q   # 15 passed
python -m pytest tests/test_batch_orchestration.py -q  # 19 passed
python -m pytest tests/test_async_render.py -q        # 17 passed
python -m pytest tests/test_stream_render_service.py -q # 12 passed
python -m pytest tests/test_stats_api.py -q            # 11 passed
python -m pytest tests/ -x -q                         # 375 passed, 6 skipped
```

---

## 5. 修复项总览

### P7-I1 / P7-I1a：异步字幕 timeline 修复

- **问题**：异步 T2A subtitle timeline end=0.0
- **原因**：MiniMax async query 未返回 duration_ms 时 fallback 为 0
- **修复**：使用 `estimate_duration_ms()` 兜底
- **测试**：补充 duration 缺失与 provider timeline 优先测试
- **结论**：✅ 已关闭

### P7-I2 / P7-I2a：Smoke Runner 进程治理

- **问题**：smoke test 启动 uvicorn 可能残留进程，占用端口
- **修复**：
  - 新增 smoke runner (`scripts/run_minimax_smoke.py`)
  - 使用独立端口 8010
  - 不使用 `--reload`
  - pidfile 管理
  - 默认不真实调用 MiniMax
  - `--real-minimax` 才允许真实调用
  - runner 自己启动的进程使用 `proc.terminate()` / `proc.kill()` 清理
- **结论**：✅ 已关闭

### P7-I3 / P7-I3a：异步轮询与慢任务体验

- **问题**：异步任务耗时较长，前端固定 3 秒轮询导致日志刷屏
- **修复**：
  - 3s / 10s / 20s 退避轮询
  - 慢任务提示
  - 手动刷新
  - 停止自动刷新
  - 最大自动轮询 15 分钟
  - 防重复 timer
  - 旧 job timer 不污染当前 job
  - favicon 404 噪音处理
- **结论**：✅ 已关闭

### P7-I5 / I5a / I5b：Admin 字符统计与错误归因

- **问题**：
  - Admin 总字符数 / Provider 字符数显示为 0
  - Provider API 错误数需要归因
  - job_id context 存在泄漏风险
- **根因**：
  - provider call log 未正确关联 job_id（context 从未设置）
  - `update_call_log` 找不到对应记录（查询 `job_id=""` 但存储的是 `NULL`）
  - `usage_characters` 没写回
- **修复**：
  - provider 调用前设置 `job_id` context
  - `set_job_id()` 返回 `ContextVar.Token`
  - `reset_job_id(token)` 防止 context 泄漏
  - 同步 / 异步 / 流式 provider 调用全部 `try/finally` reset
  - Admin 字符统计增加 `AudioAsset.usage_characters` fallback
  - daily trend characters 增加 fallback
  - 新增 `scripts/analyze_provider_errors.py`
  - 修复 async query double reset
- **结论**：✅ 已关闭

---

## 6. 当前能力状态总表

| 能力 | 当前状态 | 是否建议进入 P8 |
|---|---:|---:|
| 同步 T2A | 可进入产品化候选 | 是 |
| 异步 T2A | 可进入产品化候选，但需提示耗时 | 是 |
| WebSocket 流式 T2A | 可进入产品化候选 | 是 |
| 批量长文本 | 可进入产品化候选 | 是 |
| 批量剧本 | 可进入产品化候选 | 是 |
| 字幕生成 | 可进入产品化候选 | 是 |
| 资产下载 / 播放 | 可进入产品化候选 | 是 |
| 任务历史 | 可进入产品化候选 | 是 |
| Admin 统计 | 可作为内部运维能力 | 是，内部使用 |
| Resource Guard | 可继续保留 | 是 |
| Smoke Runner | 可作为测试基础设施 | 是 |
| 声音克隆 | 暂缓 | 否 |
| 声音设计 | 暂缓 | 否 |
| HTTP 流式端点 | 产品/API 口径待决策 | 暂不进入 |

---

## 7. 当前剩余问题

### P0

```
无
```

### P1

```
无
```

### P2

```
HTTP 流式端点不存在，当前流式能力通过 WebSocket 提供。是否补充 HTTP stream 需要产品/API 口径决策。
历史 ProviderCallLog.job_id=NULL 的旧数据无法完整回填，当前通过 AudioAsset fallback 尽量补齐。
Admin 字符统计当前使用 max(call_chars, asset_chars) 阶段性兜底，如需财务级精确统计，后续应按 job_id 粒度去重。
```

### P3

```
cost estimate 请求可进一步 debounce 优化。
profiles 加载可进一步缓存和去重。
Admin 面板仍是内部测试/运维面板，非正式产品后台。
前端仍是单文件 HTML，长期可维护性一般。
```

### 暂缓

```
声音克隆真实验证暂缓。
声音设计真实验证暂缓。
```

---

## 8. 是否进入 P8

**结论**：可以进入 P8，但 P8 应聚焦产品化体验，不应继续扩张后端能力。

**建议 P8 范围**：
1. 前端 UX 整理
2. 音色选择 / 试听工作台
3. 任务结果展示优化
4. 历史记录和下载体验优化
5. H5 / 移动端适配评估
6. 产品化入口梳理

**不建议 P8 立刻做**：
```
声音克隆
声音设计
更多 Provider
复杂多租户
大规模商业计费
```

---

## 9. 阶段最终结论

P7-I 阶段完成。真实 MiniMax 主链路已通过低成本 smoke test 和浏览器简测验证；验证过程中发现的异步字幕、测试进程、异步轮询、Admin 统计、job_id context 等问题均已修复并补充测试。当前无 P0/P1 阻塞问题，可以进入 P8 前端产品化规划阶段。
# Voice Lab 项目健康检查

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

本次执行测试命令：

```bash
python -m pytest tests/ -x -q --ignore=tests/test_ws_render.py
```

测试结果：待执行后填写。

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

## 7. 本次测试执行记录

测试命令：

```bash
python -m pytest tests/ -x -q --ignore=tests/test_ws_render.py
```

测试输出：

```text
300 passed, 6 skipped in 104.64s (0:01:44)
```

测试结果摘要：

- 总测试数量：306（300 passed + 6 skipped）
- 通过数量：300
- 跳过数量：6（均为 E2E 测试，需要真实 API Key）
- 失败数量：0
- 第一个失败测试：无

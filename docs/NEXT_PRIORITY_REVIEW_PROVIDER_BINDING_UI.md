# NEXT-PRIORITY-REVIEW：选择 Provider-first profile/binding UI 设计

## 1. 当前状态

Voice Lab 项目已完成 Provider / Model / VoiceBinding 最小增强阶段（P16-PROVIDER-MODEL-BINDING-* 系列）。

**当前阶段**: `p16/real-usage-issues` 分支，`NEXT-PRIORITY-REVIEW` 阶段

## 2. 已完成阶段

| 阶段 | 内容 | 状态 |
|---|---|---|
| P16-PROVIDER-MODEL-BINDING-A0 | Provider / Model / VoiceBinding 全链路审查 | ✅ |
| P16-PROVIDER-MODEL-BINDING-A0-CHECK | 全链路审查复核 | ✅ |
| P16-PROVIDER-MODEL-BINDING-B1-A0 | 最小 model/binding 可见性与恢复增强前置设计 | ✅ |
| P16-PROVIDER-MODEL-BINDING-B1 | 实现最小 model/binding 可见性与恢复增强 | ✅ |
| P16-PROVIDER-MODEL-BINDING-B1-CHECK | 验证最小增强实现通过 | ✅ |
| P16-PROVIDER-MODEL-BINDING-CLOSE | Provider / Model / VoiceBinding 最小增强阶段收口 | ✅ |

## 3. 当前核心问题

### P16-PROVIDER-MODEL-BINDING-B1 已解决的问题

- ✅ workspace binding hint 展示 voiceLabel + provider/modelLabel
- ✅ `currentWorkspaceBindingInfo` + `normalizeWorkspaceBindingInfo()` + `getCurrentWorkspaceBindingInfo()` 统一 helper
- ✅ `_voiceBindMap` 写入完整 binding 字段（id/binding_id/provider_voice_id/voice_name/model）
- ✅ `buildWorkspaceRestoreContext` 保存 binding_id/model/provider_voice_id/voice_name
- ✅ ContextStore workspace context 保存 binding_id/provider_voice_id
- ✅ SampleStore workspace sample 保存 binding_id/provider_voice_id

### 仍存在的问题

1. **Workspace 仍然是 profile-first UI**：用户先选 profile，后选 provider；或者 profile + provider 并列选择，没有明确 Provider 为第一约束。

2. **用户可以选择当前 Provider 下无 binding 的人设**：虽然 `isWorkspaceBindingAvailable()` guard 会在生成时拦截，但用户体验是"先选错，再看到无绑定提示"。

3. **参数区不受 binding 可用性约束**：即使当前 Provider 下无 binding，speed/vol/pitch/emotion 等参数仍可编辑，用户可能误以为这些参数会生效。

4. **无 binding 时 model/voice 字段没有明确禁用或空状态提示**。

## 4. 为什么不直接进入 Capability UI

原后续候选：

```
P16-PROVIDER-CAPABILITY-UI-B1：capability-driven provider/model UI
```

但 Capability UI 解决的是：

```
当前 provider/model 支持哪些功能参数（speed 范围、emotion 是否支持、stream 是否支持等）
```

**前提条件**：

```
如果当前 provider 下没有可用 binding，则还谈不上展示 model capability、参数范围、stream/subtitle/emotion 是否支持。
```

**结论**：

```
Provider-first binding UI 是 Capability UI 的前置条件。
必须先解决"当前 provider 下哪些人设/binding 可用"的问题，
才能进一步解决"该 provider/model 支持哪些参数"的问题。
```

## 5. 推荐下一阶段

**P16-PROVIDER-BINDING-UI-B2-A0**

完整名称：

```
P16-PROVIDER-BINDING-UI-B2-A0：Provider-first profile/binding UI 设计
```

一句话目标：

```
设计工作台 Provider-first 的人设与 binding 选择逻辑：先选 Provider，
再根据 Provider 下 available bindings 决定哪些人设可选、禁用、标记或隐藏。
```

## 6. Provider-first UI 核心语义

### 6.1 Provider-first 选择顺序

**当前行为**：

```
profileSelect + providerSelect 并列或无明确顺序
```

**目标行为**：

```
Provider first
    ↓
可用人设 / binding（根据 Provider 下 available bindings 过滤）
    ↓
binding 详情（model / voice_name / provider_voice_id）
    ↓
参数区（按当前 provider/model 能力适配）
    ↓
生成
```

### 6.2 Profile 下拉策略

三种方案：

| 方案 | 描述 | 风险 |
|---|---|---|
| A | 隐藏无 binding 的 profile | 用户可能以为 profile 丢失 |
| B | 全部展示，无 binding 的 profile 禁用 | 较安全，但列表可能很长 |
| C | 全部展示，标记"当前 Provider 下未绑定" | 推荐，透明且不丢失用户配置 |

**推荐方案 C 或 B**，不推荐直接隐藏。

**推荐文案**：

```
未绑定当前 Provider
请到「绑定管理」为该人设创建绑定
```

### 6.3 无 Binding 时参数区处理

| 元素 | 建议处理 |
|---|---|
| 文本输入 | 保持可编辑 |
| 生成按钮 | 禁用或 guard + 明确提示 |
| 参数区（speed/vol/pitch/emotion） | 禁用并显示提示 |
| 生成模式选择 | 禁用或保持但显示提示 |

**原则**：不自动清空用户文本，只禁用执行入口。

### 6.4 Binding detail 展示

有 binding 时展示：

```
人设：xxx
Provider：minimax
Model：speech-2.8-hd
Voice：xxx
```

### 6.5 Mock 场景

Provider = mock 时：

- 只展示/启用 mock 下有 available binding 的 profile
- 如果 mock 下没有任何 binding：显示空状态

**空状态文案**：

```
当前 Provider 下暂无可用人设绑定。
请到「绑定管理」创建 mock 绑定，或切换 Provider。
```

### 6.6 Provider 切换行为

同一个 profile 可以在 minimax 下有 binding，但在 mock 下没有 binding。

切换 provider 后，profile 的可用性应**立即更新**。

## 7. 后续阶段路线

```
P16-PROVIDER-BINDING-UI-B2-A0  (design)
    ↓
P16-PROVIDER-BINDING-UI-B2     (implement)
    ↓
P16-PROVIDER-BINDING-UI-B2-CHECK
    ↓
P16-PROVIDER-CAPABILITY-UI-B1  (capability-driven UI，在 binding 可用性基础上)
    ↓
其他后续 backlog
```

## 8. 决策结论

**选定下一阶段**：`P16-PROVIDER-BINDING-UI-B2-A0：Provider-first profile/binding UI 设计`

**决策理由**：

1. 用户实际使用中暴露的最基础问题是"先选错人设，再看到无绑定提示"
2. Provider-first binding UI 是 Capability UI 的前置条件
3. B1 已完成 binding 可见性增强，具备设计 Provider-first UI 的基础
4. B2-A0 是设计阶段，不改代码，风险可控

**B2-A0 范围**：

- 审查 index.html / product_hints.js / profile_binding.js 等文件
- 设计 Provider-first 选择顺序方案
- 输出 Profile 下拉策略推荐
- 输出参数区处理方案
- 输出风险清单
- 不改功能代码

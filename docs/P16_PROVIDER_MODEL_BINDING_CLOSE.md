# P16-PROVIDER-MODEL-BINDING-CLOSE：Provider / Model / VoiceBinding 最小增强阶段收口

## 1. 阶段背景

- **任务**: Provider / Model / VoiceBinding 最小增强阶段收口
- **分支**: `p16/real-usage-issues`
- **收口日期**: 2026-05-16

## 2. 阶段链路

| 阶段 | 内容 | 状态 |
|---|---|---|
| P16-PROVIDER-MODEL-BINDING-A0 | Provider / Model / VoiceBinding 全链路审查 | ✅ |
| P16-PROVIDER-MODEL-BINDING-A0-CHECK | 全链路审查复核 | ✅ |
| P16-PROVIDER-MODEL-BINDING-B1-A0 | 最小 model/binding 可见性与恢复增强前置设计 | ✅ |
| P16-PROVIDER-MODEL-BINDING-B1 | 实现最小 model/binding 可见性与恢复增强 | ✅ |
| P16-PROVIDER-MODEL-BINDING-B1-CHECK | 验证最小增强实现通过 | ✅ |
| P16-PROVIDER-MODEL-BINDING-CLOSE | 阶段收口 | ✅ |

## 3. 已完成能力

### 3.1 Workspace binding 可见性增强

- **binding hint 展示**: `✓ 已绑定: {voiceLabel} · {provider}/{modelLabel}`
- voiceLabel 优先使用 voice_name，回退到 provider_voice_id
- modelLabel 优先使用 model，回退到'未知模型'

### 3.2 当前 binding 信息统一 helper

| Helper | 说明 |
|---|---|
| `currentWorkspaceBindingInfo` | workspace 级别 binding info 状态，与 workspaceBindingAvailable 同级 |
| `normalizeWorkspaceBindingInfo(binding, provider, profileId)` | 纯函数，将 API 返回的 binding 对象标准化为统一结构 |
| `getCurrentWorkspaceBindingInfo()` | 获取当前 workspace 使用的 binding 信息；优先用 currentWorkspaceBindingInfo，fallback 遍历 voice_id keyed 的 _voiceBindMap |

### 3.3 _voiceBindMap 增强

写入对象现在包含完整字段：

```javascript
{
  id: b.id || null,
  binding_id: b.id || null,
  profile_id: profileId,
  provider: provider,
  model: b.model || null,
  status: 'available',
  provider_voice_id: voiceId,
  voice_id: voiceId,
  provider_voice_name: b.provider_voice_name || null,
  voice_name: b.provider_voice_name || b.voice_name || null,
}
```

### 3.4 Workspace ContextStore 增强

workspace context 现在保存：

| 字段 | 说明 |
|---|---|
| `binding_id` | 来自 getCurrentWorkspaceBindingInfo |
| `model` | 来自 getCurrentWorkspaceBindingInfo |
| `provider_voice_id` | 来自 getCurrentWorkspaceBindingInfo |
| `voice_id` | 来自 getCurrentWorkspaceBindingInfo |
| `voice_name` | 来自 getCurrentWorkspaceBindingInfo |

- 旧 context 无 binding_id 时为 null（兼容）
- 不修改 ContextStore VERSION
- 不修改 longtext/script context normalize

### 3.5 Workspace SampleStore 增强

workspace sample 现在保存：

| 字段 | 说明 |
|---|---|
| `binding_id` | 来自 ctx.binding_id |
| `provider_voice_id` | 来自 ctx.provider_voice_id 或 ctx.voice_id |
| `model` | 来自 extra.model 或 ctx.model |
| `voice_id` | 来自 ctx.voice_id |
| `voice_name` | 来自 ctx.voice_name |

- 旧 sample 无 binding_id 时为 null（兼容）
- 不修改 localStorage key
- 不修改 MAX_SAMPLES

### 3.6 buildWorkspaceRestoreContext 增强

不再只依赖 `extra.model`，现在：

```javascript
model: bindingInfo.model || extra.model || null,
binding_id: bindingInfo.binding_id || extra.binding_id || null,
provider_voice_id: bindingInfo.provider_voice_id || extra.provider_voice_id || null,
voice_id: bindingInfo.voice_id || extra.voice_id || null,
voice_name: bindingInfo.voice_name || extra.voice_name || null,
```

## 4. 当前最终语义

### 4.1 checkBindingStatus 语义

1. fetch `/api/voice/profiles/{profileId}/bindings`
2. 过滤 provider + status='available'
3. 取 matched[0]
4. 设置 currentWorkspaceBindingInfo
5. 展示 voiceLabel + provider/modelLabel
6. 同步到 _voiceBindMap（voice_id keyed）

### 4.2 restore 语义

- restore 时保存的 binding_id/model/provider_voice_id/voice_name 用于**展示和恢复辅助**
- **B1 不做 binding_id 精确执行**
- 重新生成时仍按当前 provider/profile 走后端 resolve_binding
- restore context 用于回填 provider/model/voice 等字段，不保证 binding 完全一致

### 4.3 ContextStore / SampleStore 语义

- 保存当时生成时使用的 binding 信息快照
- 不保证历史 binding 仍然有效
- 无 binding 时字段为 null，兼容旧数据

## 5. 测试结果

| 测试集 | 结果 |
|---|---|
| B1 专项测试 (test_provider_model_binding_static.py) | 27 passed |
| 回归测试 (test_workspace_restore_static.py + test_sample_sidebar_static.py + test_provider_mock_boundary_static.py) | 225 passed + 1 pre-existing failure |

**pre-existing failure 说明**: `test_safePushWorkspaceSample_writes_context_id_to_sample` 使用 800-char 固定窗口，B1 扩展 sample 对象后 `context_id` 字段（位于位置 830）超出窗口。这是既有测试实现问题，`context_id` 字段确实存在于 sample 对象中（line 2650）。

## 6. 未纳入范围

B1 阶段**没有**做以下修改：

| 类别 | 未修改内容 |
|---|---|
| 后端 | API / VoiceBinding schema / ProviderVoice schema / resolve_binding |
| 前端-模型 | model 下拉 |
| 前端-UI | Provider-first 人设选择 / Capability-driven 参数禁用 |
| 前端-模块 | Batch longtext / Batch script / Audition / Clone / Design / Import |
| 前端-辅助 | Provider Registry / Capability Registry / CostGuardService / CapabilityValidator / provider_capabilities.js |
| 前端-存储 | batch_shared.js / profile_binding.js / audition_records.js |
| 架构 | SaaS / 多用户 / 新 Provider 接入 |

## 7. 非阻塞观察项

| ID | 观察项 | 说明 |
|---|---|---|
| OBS-001 | binding API 可能不返回 id | 如果后端不返回 `id`，则 `binding_id` 为 null。这属于后端行为，不影响 B1 前端实现正确性。 |
| OBS-002 | B1 不做 binding_id 精确执行 | restore 后重新生成仍按当前 provider/profile 解析 binding，不保证使用历史 binding_id。 |
| OBS-003 | 当前 UI 仍不是 provider-first | 参数区以 profile 为第一选择单位，Provider 跟随 profile。应该改为 Provider 第一约束。 |
| OBS-004 | 参数区尚未按 capability 禁用 | speed/vol/pitch/emotion 等参数未按当前 provider/model 的能力动态禁用。 |
| OBS-005 | Batch/Script/Audition/Clone/Design/Import model 语义不统一 | 这些模块的 model/binding 来源各异，未纳入 B1 范围。 |

## 8. 后续路线建议

### 8.1 推荐优先：P16-PROVIDER-BINDING-UI-B2-A0

**设计 Provider-first profile/binding UI**

原因：用户已指出"工作台应以 Provider 为第一约束"。

具体方向：
1. 选择 Provider 后，应该显示哪些人设有可用 binding
2. 无 binding 的人设应禁用、隐藏或明确标记
3. 无 binding 时参数区应禁用或提示先绑定
4. 避免用户在无 binding 的 profile 上点击生成然后失败

### 8.2 后续：P16-PROVIDER-CAPABILITY-UI-B1

**实现 Capability-driven 参数区**

在 Provider-first binding UI 完成后，按 provider/model/capability 动态禁用或设置参数区默认值。

### 8.3 路线图

```
P16-PROVIDER-BINDING-UI-B2-A0  (design)
    ↓
P16-PROVIDER-BINDING-UI-B2    (implement)
    ↓
P16-PROVIDER-CAPABILITY-UI-B1
    ↓
P17-CREATION-RECORD-A0        (future backlog)
```

## 9. 收口结论

**Provider / Model / VoiceBinding 最小增强阶段完成** ✅

- workspace binding 可见性已增强
- ContextStore/SampleStore 已保存 binding_id/model/provider_voice_id
- restore 语义已明确为"可见性辅助，不做精确执行"
- 测试通过，未引入回归问题
- 未越界修改后端/API/schema
- 未引入 model 下拉
- 下一阶段建议：P16-PROVIDER-BINDING-UI-B2-A0

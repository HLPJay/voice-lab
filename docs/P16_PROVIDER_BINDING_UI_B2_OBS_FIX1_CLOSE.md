# P16-PROVIDER-BINDING-UI-B2-OBS-FIX1-CLOSE：Provider-first UI 观察项修复阶段收口

## 1. 阶段背景

OBS-FIX1 修复了两个 Provider-first UI 的非阻塞观察项，提升了 workspace binding 状态的准确性。

前置阶段：
- `P16-PROVIDER-BINDING-UI-B2-CLOSE`：Provider-first profile/binding UI 阶段收口 ✅
- `NEXT-PRIORITY-REVIEW`：选择 Provider-first UI 观察项修复 ✅
- `P16-PROVIDER-BINDING-UI-B2-OBS-FIX1`：修复 Provider-first UI 观察项 ✅
- `P16-PROVIDER-BINDING-UI-B2-OBS-FIX1-CHECK`：验证 Provider-first UI 观察项修复 ✅

## 2. 阶段链路

| 阶段 | 状态 |
|---|---|
| P16-PROVIDER-BINDING-UI-B2-CLOSE | ✅ 完成 |
| NEXT-PRIORITY-REVIEW | ✅ 完成 |
| P16-PROVIDER-BINDING-UI-B2-OBS-FIX1 | ✅ 完成 |
| P16-PROVIDER-BINDING-UI-B2-OBS-FIX1-CHECK | ✅ 复核通过 |
| P16-PROVIDER-BINDING-UI-B2-OBS-FIX1-CLOSE | 🔄 当前阶段 |

## 3. 修复内容

### OBS-1 修复：_voiceBindMap 非全量

**修复前**：
`refreshWorkspaceProfileAvailability()` 依赖 `_voiceBindMap` 判断 profile 是否绑定当前 Provider；但 `_voiceBindMap` 可能只包含当前 profile 的 binding，不一定是全量缓存。

**修复后**：
新增 `refreshWorkspaceBindingMap()`，在 workspace profile 标记前预填充全量 `_voiceBindMap`：
- 调用 `loadAllBindings()` 生成全量 `provider_voice_id` keyed `_voiceBindMap`
- 带 `workspaceBindingMapLoading` 并发保护，防止连续触发时重复并发请求
- 失败时保留已有 `window._voiceBindMap`
- 只查询本地后端 `/api/voice/profiles/{id}/bindings`，不调用真实 MiniMax

关键实现语义：
```
refreshWorkspaceBindingMap()
- 调用 loadAllBindings()
- 写入 window._voiceBindMap
- 带 workspaceBindingMapLoading 并发保护
- 失败时保留已有 window._voiceBindMap
```

### OBS-2 修复：provider/profile change 状态同步

**修复前**：
`profileSelect` change 未 await `checkBindingStatus()`，`updateWorkspaceBindingUiState()` 可能短暂使用旧 `workspaceBindingAvailable`。

**修复后**：
`providerSelect` 和 `profileSelect` change handler 改为 async handler：

```
providerSelect change：
await refreshWorkspaceBindingMap()
refreshWorkspaceProfileAvailability()
await checkBindingStatus()
updateCostHint()
updateWorkspaceVoiceBindingHint()

profileSelect change：
await checkBindingStatus()
updateWorkspaceBindingUiState()
updateWorkspaceVoiceBindingHint()
```

## 4. 当前最终语义

OBS-FIX1 完成后，Provider-first UI 最终稳定语义：

```
Provider 是 Workspace 第一约束。
Profile 下拉的"未绑定当前 Provider"标记基于全量 binding map。
Provider 切换后会先刷新 binding map，再刷新 profile 可用性标记。
Profile 切换后等待 binding 状态检查完成，再更新参数区和生成按钮状态。
无 binding 时参数区和生成按钮禁用。
handleGenerate guard 仍作为最后防线。
```

## 5. 测试结果

- OBS-FIX1 专项测试: 22 passed ✅
- B2 静态测试: 28 passed ✅
- 合计: 50 passed ✅
- 回归测试: 252 passed
- Pre-existing failure: `test_safePushWorkspaceSample_writes_context_id_to_sample` (1 个，与 OBS-FIX1 无关)

说明：`test_safePushWorkspaceSample_writes_context_id_to_sample` 为既有固定窗口测试问题，不计入本阶段阻塞。

## 6. 未纳入范围

OBS-FIX1 没有做：

```
后端/API 修改
VoiceBinding schema 修改
ProviderVoice schema 修改
resolve_binding 修改
model 下拉
Capability UI
binding_id 精确执行
Batch longtext 改造
Batch script 多角色 binding 改造
Audition model 来源统一
Clone / Design / Import model 来源统一
Provider Registry / Capability Registry 改造
声音人设删除/停用模块
SaaS / 多用户
```

## 7. 新发现：声音人设删除/停用模块缺失

用户已指出当前前端缺少删除声音人设模块。

代码事实：
```
当前后端 voice_profiles API 只有：
GET /profiles
POST /profiles

当前 VoiceProfileService 只有：
list()
create()

当前 list_profiles() 按 VoiceProfile.is_active == True 过滤，
说明具备软删除/停用的字段基础，
但还没有 delete/deactivate API 和前端入口。
```

后续候选阶段：
```
P16-VOICE-PROFILE-DELETE-A0：声音人设删除/停用方案设计
```

建议语义：
```
优先做"停用人设"，不是物理删除。
VoiceProfile.is_active = False。
关联 VoiceBinding 标记为 deprecated 或 unavailable。
历史任务、最近样本、已生成音频不删除。
```

**本阶段只记录为后续候选，不实现。**

## 8. 后续路线建议

收口后进入：`NEXT-PRIORITY-REVIEW：下一阶段优先级确认`

三个候选方向：

**候选一：P16-PROVIDER-CAPABILITY-UI-B1**
```
实现 capability-driven provider/model UI：
stream/subtitle/emotion/audio_format/参数范围动态启用或禁用。
适合场景：继续推进多 Provider / 多模型接入的前端能力适配。
```

**候选二：P16-VOICE-PROFILE-DELETE-A0**
```
声音人设删除/停用方案设计。
补齐 VoiceProfile 生命周期管理。
适合场景：先补基础管理能力，解决当前前端缺少删除人设的问题。
```

**候选三：P17-CREATION-RECORD-A0**
```
服务端创作记录和恢复 API 设计。
适合场景：从前端本地 ContextStore / SampleStore 逐步走向服务端记录。
```

推荐优先级：
```
如果继续围绕多大模型接入，优先 P16-PROVIDER-CAPABILITY-UI-B1。
如果先补产品基础管理能力，优先 P16-VOICE-PROFILE-DELETE-A0。
```

建议本次收口后暂不直接决定，交给 NEXT-PRIORITY-REVIEW。

## 9. 收口结论

Provider-first UI 观察项修复阶段完成 ✅

- OBS-1 已修复：全量 binding map 预填充
- OBS-2 已修复：provider/profile change async/await
- 无阻塞问题
- 无新增非阻塞观察项
- handleGenerate guard 保留
- 测试通过

**下一阶段**：`NEXT-PRIORITY-REVIEW：下一阶段优先级确认`

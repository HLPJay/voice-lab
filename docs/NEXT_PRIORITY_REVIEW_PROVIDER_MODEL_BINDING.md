# NEXT-PRIORITY-REVIEW：选择 Provider / Model / VoiceBinding 全链路审查作为下一阶段

## 1. 当前状态

- **分支**：`p16/real-usage-issues`
- **当前阶段**：`NEXT-PRIORITY-REVIEW`
- **刚完成**：`P16-PROVIDER-MOCK-CLOSE`（Provider mock boundary 阶段收口）

## 2. 已完成阶段

| 阶段 | 结论 |
|---|---|
| `P16-PROVIDER-BOUNDARY-A0` | 发现 RISK-001/002/006（mock fallback、CostGuard 绕过、前端 unbound） |
| `P16-PROVIDER-BOUNDARY-A0-CHECK` | 通过 |
| `P16-PROVIDER-MOCK-FIX1` | 代码修复完成 |
| `P16-PROVIDER-MOCK-FIX1-CHECK` | 复核通过 |
| `P16-PROVIDER-MOCK-CLOSE` | 阶段收口完成 |

## 3. 为什么不直接进入 Capability UI B1

原 Next 表推荐：`P16-PROVIDER-CAPABILITY-UI-B1`（capability-driven provider UI）

**结论：不应直接进入。原因：**

1. **Capability UI 只解决表层问题**：P16-PROVIDER-CAPABILITY-UI-B1 解决的是"前端按 provider 能力禁用功能"——但这建立在音色模块数据关系已经清晰的前提下。

2. **更底层的问题是数据关系不完整**：`VoiceBinding` 已包含 `provider / model / provider_voice_id`，但业务选择层（resolve_binding、执行层、展示层、恢复层）还没有统一 model 作为显式维度。

3. **只做 Capability UI 会遗漏横向模块**：如果不先审查 model binding，直接做 capability UI，只会处理 workspace 下拉，遗漏 batch/script/audition/clone/design/import 等模块中的 provider+model 语义。

4. **新 Provider 接入需要完整链路**：后续 OpenAI / Azure / ElevenLabs 接入时，真正需要统一的是 `provider → model → voice → binding → render plan` 的完整链路。Capability UI 无法替代这个基础工作。

## 4. 当前代码事实

### 4.1 VoiceBinding 数据结构

```python
class VoiceBinding(SQLModel, table=True):
    id: str                    # 主键
    profile_id: str             # 索引
    provider: str               # 提供商
    model: str                  # 模型
    provider_voice_id: str     # 提供商音色 ID
    params_json: str = "{}"    # 参数
    priority: int = 1          # 优先级
    status: str                 # available
    created_at: str
    updated_at: str
```

**结论**：绑定数据层已经是 `profile_id + provider + model + provider_voice_id` 的复合关系，不只是 `profile + provider`。

### 4.2 绑定创建逻辑

`VoiceBindingService.create_profile_binding()` 调用 `find_duplicate_binding()` 时按以下维度判断重复：

```python
duplicate = find_duplicate_binding(
    session,
    profile_id=profile_id,
    provider=request.provider,
    model=request.model,
    provider_voice_id=request.provider_voice_id,
)
```

**结论**：创建绑定时，`model` 已经是与 `provider`、`provider_voice_id` 并列的一等字段，`provider + model + provider_voice_id` 共同唯一确定一个绑定。

### 4.3 绑定解析逻辑

`resolve_binding(session, profile_id, provider)` 当前签名：

```python
def resolve_binding(session: Session, profile_id: str, provider: str) -> tuple[VoiceBinding, str]:
```

按 `profile_id + provider + available status` 查询，按 `priority + created_at` 排序取第一条。

**结论**：执行解析层**没有**显式传入 `model`，以 `provider` 为粒度取第一条 available binding。

### 4.4 执行使用逻辑

`VoiceRenderService.render_voice()` 使用：

```python
binding.model
binding.provider_voice_id
binding.params_json
```

构建 `RenderPlan`，最终执行语义为：

```
resolved_provider + binding.model + binding.provider_voice_id + binding.params_json
```

**结论**：执行层**已经**使用 `model`，但 model 在选择层、展示层、恢复层还未统一。

## 5. 核心问题：Provider / Model / VoiceBinding 数据关系

### 5.1 当前关系（数据层）

```
VoiceProfile (人设)
  └── VoiceBinding (人设在某 Provider + Model + ProviderVoice 上的绑定)
        ├── profile_id
        ├── provider       ← 不只是 provider，是 provider + model + provider_voice_id 的绑定
        ├── model
        ├── provider_voice_id
        └── params_json
```

### 5.2 当前关系（执行层）

```
resolve_binding(profile_id, provider)
  → 返回 profile_id + provider 下 priority 最高的 available binding
  → 使用 binding.model + binding.provider_voice_id + binding.params_json 执行
```

### 5.3 核心缺口

| 层次 | 当前状态 | 缺口 |
|---|---|---|
| **数据层** | VoiceBinding 已有 provider + model + provider_voice_id | ✅ 完整 |
| **创建层** | create_binding 按 provider+model+provider_voice_id 排重 | ✅ 完整 |
| **解析层** | resolve_binding 只按 profile+provider，没有 model 参数 | ❌ model 未显式 |
| **执行层** | 使用 binding.model | ✅ 完整 |
| **选择层（workspace）** | provider 下拉，没有 model 下拉 | ❌ model 缺失 |
| **展示层** | binding status 显示 provider+voice_id，没有 model | ❌ model 缺失 |
| **恢复层（ContextStore）** | 保存 provider+profile_id，没有 binding_id | ❌ model 缺失 |
| **横向模块（batch/script/audition）** | 各模块独立，部分没有 model | ❌ 不一致 |

## 6. 所有使用音色模块的覆盖范围

下一阶段 A0 必须横向审查以下所有入口：

| # | 入口 | 当前状态 |
|---|---|---|
| 1 | Workspace 单条同步生成 | provider 下拉，无 model 下拉 |
| 2 | Workspace 异步生成 | provider 下拉，无 model 下拉 |
| 3 | Workspace 流式生成 | provider 下拉，无 model 下拉 |
| 4 | Workspace 多版本试音 variants | provider 下拉，无 model 下拉 |
| 5 | Batch longtext 长文本生成 | provider 下拉，无 model 下拉 |
| 6 | Batch script 剧本多角色生成 | profile+voice 绑定，无 provider/model 下拉 |
| 7 | Voices tab 音色查询 | 按 provider 查询 voice list |
| 8 | Voices tab 音色试音 | provider_voice_id 试音，无 model 参数 |
| 9 | Voices tab 绑定到人设 | provider+provider_voice_id+model 创建绑定 |
| 10 | Voices tab 更换绑定 | 更新 provider_voice_id，model 不变 |
| 11 | Binding management / 绑定管理 | 展示 provider+model+provider_voice_id |
| 12 | Provider voices 查询/导入/删除 | 按 provider 过滤 voice list |
| 13 | Audition workstation / 试音工作台 | 已有 model 感知 |
| 14 | Voice clone quick preview | 使用 binding.model |
| 15 | Voice design quick preview | 使用 binding.model |
| 16 | Voice import quick preview | 使用 binding.model |
| 17 | SampleStore 最近样本记录 | 保存 provider+profile_id，无 binding_id |
| 18 | ContextStore workspace restore | 保存 provider+profile_id，无 binding_id |
| 19 | ContextStore longtext restore | 保存 provider+profile_id，无 binding_id |
| 20 | ContextStore script restore | 保存 per-role provider+profile_id，无 binding_id |
| 21 | History / Admin / Job 记录 | 展示 provider，无 model 展示 |

## 7. 推荐下一阶段

**正式名称**：`P16-PROVIDER-MODEL-BINDING-A0`

**完整名称**：Provider / Model / VoiceBinding 全链路审查

**一句话目标**：审查所有音色绑定、选择音色、使用音色、恢复音色配置的入口，统一 Provider / Model / ProviderVoice / VoiceProfile / VoiceBinding 的数据关系和业务规则。

## 8. 后续阶段路线

```
NEXT-PRIORITY-REVIEW (当前) → P16-PROVIDER-MODEL-BINDING-A0 → P16-PROVIDER-MODEL-BINDING-A0-CHECK
    → P16-PROVIDER-MODEL-BINDING-B1 (minimal: 展示+保存 binding_id/model, restore 升级)
    → P16-PROVIDER-CAPABILITY-UI-B1 (完整 capability-driven provider/model UI)
    → P16-VARIANTS-UX-FIX1 (多版本等待态)
    → P17-CREATION-RECORD-A0 (服务端创作记录)
```

## 9. 决策结论

**下一阶段**：`P16-PROVIDER-MODEL-BINDING-A0`

**理由**：
- Provider 语义安全已修复（mock boundary 已闭环）
- Capability UI 的前提是 model binding 关系已统一
- 当前 `VoiceBinding` 数据层完整，但业务选择层、展示层、恢复层、横向模块尚未统一 model
- 直接跳入 Capability UI 会遗漏 batch/script/audition/clone/design 等模块
- 新 Provider 接入需要完整链路审查作为基础

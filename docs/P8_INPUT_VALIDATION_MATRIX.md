# P8 输入校验矩阵

## 1. 审查范围

本审查覆盖 Voice Lab 项目以下模块的前端控件约束、后端 Pydantic Schema 约束和服务层兜底逻辑的一致性：

- 创作工作台（单条生成）
- 长文本批量
- 剧本批量
- 音色试听（Provider Voice Preview）
- 声音克隆
- 声音设计
- 导入已有远端音色
- 历史 / Admin

**审查性质**：只读审查，未修改任何代码。

## 2. 总体结论

| 等级 | 数量 | 说明 |
|---|---|---|
| P0 | 3 | 会导致真实 Provider 费用损失、错误调用、或资源耗尽 |
| P1 | 5 | 会导致正常用户输入触发 422/500，任务失败 |
| P2 | 6 | 体验不一致、错误提示不够清晰、用户困惑 |
| P3 | 5 | 文案 / placeholder / 注释不一致 |

**合计问题：19 个**

## 3. 约束矩阵

### 3.1 创作工作台（单条生成）

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 1.1 | text | textarea#textInput | `maxlength="9500"`, `min_length=1` | `Field(min_length=1)` 无 `max_length` | - | **P0**：后端无 max_length，绕过前端后可提交超长文本，耗尽资源或导致 Provider 异常 | P0 | 后端 `VoiceRenderRequest.text` 增加 `max_length=10000` | P8-VALIDATION2-A |
| 1.2 | speed | input#paramSpeed | `min=0.5, max=2.0, step=0.05` | `Field(ge=0.5, le=2.0)` | - | 一致 | - | - | - |
| 1.3 | vol | input#paramVol | `min=0.1, max=10.0, step=0.1` | `Field(ge=0.1, le=10.0)` | - | 一致 | - | - | - |
| 1.4 | pitch | input#paramPitch | `min=-12, max=12, step=1` | `Field(ge=-12, le=12)` | - | 一致 | - | - | - |
| 1.5 | variant_count | input#variantCount | `min=1, max=5` | `Field(ge=1, le=5)` | 前端 `Math.min(5, Math.max(1, count))` 二次 clamping | 一致 | - | - | - |
| 1.6 | confirm_cost | payload | 前端 `confirmHighCostVoiceAction` 对话框显示，但 payload 固定为 `false` | `confirm_cost: bool = False` | `cost_guard.require_confirmed()` 检查 | **P0**：对话框显示但 `confirm_cost=false`，真实 Provider 调用前用户未真正确认；对话框本身有提示作用，但不符合 `confirm_cost` 语义 | P0 | `confirmHighCostVoiceAction` 返回 true 时 payload 应设置 `confirm_cost: true` | P8-VALIDATION2-B |
| 1.7 | audio_format | select | `mp3/wav/flac` | `Literal["mp3", "wav", "flac"]` | - | 一致 | - | - | - |
| 1.8 | output_format | select | `hex/url` | `Literal["hex", "url"]` | - | 一致 | - | - | - |

### 3.2 长文本批量

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 2.1 | text | textarea#batchText | `maxlength="50000"`, `min_length=1` | `Field(min_length=1)` 无 `max_length` | `TextSegmentService.segment()` 按 `max_chars` 拆分 | **P0**：后端无 max_length，50000 字文本通过后会被 `max_chars=2000` 拆成约 25 段，但后端本身无输入保护 | P0 | `LongtextBatchRequest.text` 增加 `max_length=50000` | P8-VALIDATION2-A |
| 2.2 | segment_strategy | select#batchStrategy | `auto/paragraph/sentence/line` | `str = "auto"` 无 Literal（仅注释） | `TextSegmentService.segment()` 对未知 strategy 抛 `ValueError` | **P0**：无 Literal 约束，非法值（如 `"auto1"`）通过 Pydantic 验证后到达服务层抛出 `ValueError` → API 返回 500 而非 422 | P0 | 改为 `Literal["auto", "paragraph", "sentence", "line"]` | P8-VALIDATION2-A |
| 2.3 | max_segment_chars | input#batchMaxChars | `min=100, max=5000, step=100` | `Field(ge=100, le=5000)` | `TextSegmentService.segment()` 使用此参数 | 一致 | - | - | - |
| 2.4 | silence_between_ms | input#batchSilence | `min=0, max=3000, step=100` | `Field(ge=0, le=3000, default=300)` | 用于段间静音时长 | 一致 | - | - | - |
| 2.5 | line 策略超长行兜底 | - | - | - | `_segment_line()` 调用 `_segment_sentence()` 对超长行兜底 | `_segment_sentence` 内部 `len(line) <= max_chars` 判断依赖 `splitlines()` 结果行长，不跨行合并 | **P1**：若某行无任何句子边界标点且超过 `max_chars`，可能仍然产出超长 segment | P1 | `_segment_line` 超长行兜底增加逗号拆分（复用 `_split_by_comma`） | P8-VALIDATION2-A |
| 2.6 | confirm_cost | payload | `confirm_cost: false`（长文本批量不弹确认框） | `confirm_cost: bool = False` | `cost_guard.require_confirmed()` | 前端未弹确认框，符合默认 false | - | - | - |

### 3.3 剧本批量

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 3.1 | script (行数) | JS 动态添加行 | 无前端行数上限（用户可无限添加） | `Field(min_length=1, max_length=200)` | - | **P1**：用户可添加超过 200 行，到达后端返回 422，但前端无提示 | P1 | 前端 `_scriptRows` 增加到 200 行时禁用"添加行"按钮，或弹窗提示 | P8-VALIDATION2-B |
| 3.2 | script[].text | input#scriptText_${id} | 无 maxlength | `Field(min_length=1)` 无 max_length | - | **P1**：单行无限长，到达后端无报错但可能影响 Provider | P1 | 前端每行 `scriptText` 增加 `maxlength="5000"` | P8-VALIDATION2-B |
| 3.3 | script[].role | input#scriptRole_${id} | 无约束 | `role: str`（无约束） | - | **P2**：前后端均无 role 格式约束，role 为空字符串时后端不报错（空字符串 ≠ null），前端显示"旁白"但 payload 一致 | P2 | 后端 `ScriptLine.role` 增加 `min_length=1` 或前端在 `handleBatchScriptSubmit` 前校验 role 非空 | P8-VALIDATION2-A |
| 3.4 | silence_between_ms | input#batchScriptSilence | `min=0, max=3000, step=100` | `Field(ge=0, le=3000, default=500)` | - | 一致（注意默认值 500 vs 长文本默认 300，前端默认值也是 500） | - | - | - |
| 3.5 | confirm_cost | payload | `confirm_cost: false`（剧本批量不弹确认框） | `confirm_cost: bool = False` | - | 一致 | - | - | - |
| 3.6 | script 每行 text 空值 | input#scriptText_${id} | 无行级空值提示 | `Field(min_length=1)` | - | **P2**：某行 text 为空时，前端不拦截，到达后端返回 422，但错误显示在整个批量结果区而非该行 | P2 | 前端 `handleBatchScriptSubmit` 提交前检查每行 text 非空，定位到行级提示 | P8-VALIDATION2-B |

### 3.4 音色试听（Provider Voice Preview）

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 4.1 | text | textarea#auditionText | 无 maxlength | `Field(min_length=1, max_length=1000)` | - | **P1**：前端无 maxlength，用户可输入超 1000 字，到达后端 422 | P1 | 前端 `auditionText` 增加 `maxlength="1000"` | P8-VALIDATION2-B |
| 4.2 | provider_voice_id | 来自音色列表（data attribute） | 来自音色列表，无前端输入 | `Field(min_length=1)` | - | 一致（来自选择非用户输入） | - | - | - |
| 4.3 | model | select | 固定 speech-2.8-hd 等 | `model: str = "speech-2.8-hd"` | - | 一致 | - | - | - |
| 4.4 | speed/vol/pitch | 与创作工作台相同 | 与创作工作台相同 | 与创作工作台相同 | - | 一致 | - | - | - |
| 4.5 | confirm_cost | payload | `confirm_cost: provider === 'minimax'` | `confirm_cost: bool = False` | `cost_guard.require_confirmed()` | **P0**：单条试听（mock/minimax）payload confirm_cost=false，不弹确认框；但预览服务 `preview_service.preview()` 内部是否真正校验 confirm_cost 待确认 | P0 | 确认 preview_service 对 minimax 是否强制校验 confirm_cost；若需要，前端应传 `confirm_cost: true` | P8-VALIDATION2-A |

### 3.5 声音克隆

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 5.1 | voice_id | input#cloneVoiceId | 无 maxlength/minlength，无 pattern 校验 | `Field(min_length=8, max_length=256, pattern=^[a-zA-Z]...)` | `model_validator` 无额外校验 | **P0**：前端无格式校验，用户输入 "abc" 触发后端 pattern 校验失败 → 422，用户困惑 | P0 | 前端 `cloneVoiceId` 增加 `minlength="8"`，blur 时增加 regex 前端预校验并显示友好提示 | P8-VALIDATION2-B |
| 5.2 | file_id | input#cloneFileId | `type="number"` 无 min 限制 | `file_id: int`（无 gt=0） | - | **P1**：前端允许输入 0 或负数，到达后端不报错（Provider 层才可能失败），用户困惑 | P1 | 后端 `VoiceCloneRequest.file_id` 改为 `Field(gt=0)`；前端 `cloneFileId` 增加 `min="1"` | P8-VALIDATION2-A |
| 5.3 | prompt_file_id | input#clonePromptFileId | `type="number"` 无 min 限制 | `prompt_file_id: int \| None`（无 gt=0） | - | **P1**：同上，可填 0 或负数 | P1 | 后端 `prompt_file_id` 改为 `Field(gt=0)` | P8-VALIDATION2-A |
| 5.4 | preview_text | textarea#clonePreviewText | 无 maxlength | `Field(default=None, max_length=1000)` | - | **P1**：前端无 maxlength，可输入 > 1000 字，到达后端 422 | P1 | 前端 `clonePreviewText` 增加 `maxlength="1000"` | P8-VALIDATION2-B |
| 5.5 | model | input#cloneModel | 无约束（可选） | `model: str \| None` | `model_validator`：若 preview_text 有值但 model 为空则报错 | **P1**：前端 `updateCloneBtnState()` 只在 preview_text 有值且 model 为空时禁用按钮，但若 model 已填后用户清空，仍可提交导致后端报错 | P1 | `updateCloneBtnState()` 中 model 变化也应触发重新校验；或后端对 model 可选做更严格限制 | P8-VALIDATION2-B |
| 5.6 | confirm_cost | payload | `confirm_cost: false`（handleCloneVoice 固定 false） | `confirm_cost: bool = False` | `cost_guard.require_confirmed()` | **P0**：`confirmHighCostVoiceAction('声音克隆')` 对话框显示后 payload 仍 `confirm_cost: false`；对话框本身有提示作用但不符合 confirm_cost 语义 | P0 | 对话框确认后 payload 设置 `confirm_cost: true` | P8-VALIDATION2-B |
| 5.7 | prompt_file_id + prompt_text 成对 | JS 手动校验 | 手动 if 校验 | `model_validator`：两者必须同时填写或同时留空 | - | 一致（前后端均有成对校验） | - | - | - |

### 3.6 声音设计

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 6.1 | prompt | textarea#designPrompt | 无 maxlength | `Field(min_length=1)` 无 max_length | - | **P1**：前端无 maxlength，理论上可输入无限长 prompt；后端无限制可能传极大文本到 Provider | P1 | 前端 `designPrompt` 增加 `maxlength="2000"` | P8-VALIDATION2-B |
| 6.2 | preview_text | textarea#designPreviewText | `maxlength="500"` | `Field(min_length=1, max_length=500)` | - | 一致（maxlength=500 在前后端均一致） | - | - | - |
| 6.3 | voice_id | input#designVoiceId | 无约束（可选，不填自动生成） | `Field(min_length=8, max_length=256, pattern=...)` | - | **P1**：用户可输入任意格式 voice_id 触发后端 pattern 校验失败 | P1 | 前端 `designVoiceId` 增加 `minlength="8"` 和 pattern 前端预提示 | P8-VALIDATION2-B |
| 6.4 | confirm_cost | payload | `confirm_cost: false` | `confirm_cost: bool = False` | `cost_guard.require_confirmed()` | **P0**：`handleDesignVoice` 中对话框显示后 payload 仍 `confirm_cost: false` | P0 | 对话框确认后 payload 设置 `confirm_cost: true` | P8-VALIDATION2-B |

### 3.7 导入已有远端音色

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 7.1 | provider_voice_id | input#importCloneVoiceId | 无 minlength/pattern | `Field(min_length=1)` | - | **P1**：后端只有 min_length=1，无 min_length=8 或 pattern（与 clone voice_id 不同）；前端无格式提示，用户可能填短字符串或错误格式 | P1 | 后端 `ProviderVoiceImportRequest.provider_voice_id` 增加 `min_length=8` 与 clone 保持一致；或前端增加格式提示 | P8-VALIDATION2-A |
| 7.2 | preview_text | input#importClonePreviewText | 无 maxlength | `Field(default="你好，这是导入音色试听。", min_length=1, max_length=1000)` | - | **P1**：前端无 maxlength | P1 | 前端 `importClonePreviewText` 增加 `maxlength="1000"` | P8-VALIDATION2-B |
| 7.3 | voice_type | select | `voice_cloning/voice_generation` | `Literal["voice_cloning", "voice_generation"]` | - | 一致 | - | - | - |

### 3.8 历史 / Admin

| 编号 | 字段 | 前端控件 | 前端约束 | 后端约束 | 服务层 | 当前问题 | 风险 | 修复建议 | 阶段 |
|---|---|---|---|---|---|---|---|---|---|
| 8.1 | voice_jobs limit | JS 传参 | `limit=20` 默认，最新 P8-TIME1 约束 1-100 | `Query(ge=1, le=100)` | - | 一致（前端默认 20 在 1-100 范围内） | - | - | - |
| 8.2 | voice_jobs offset | JS 传参 | 无显式约束 | `Query(ge=0)` | - | 一致 | - | - | - |
| 8.3 | admin call_logs limit | JS 传参 | 无显式前端限制 | `Query(ge=1, le=200)` | - | **P2**：前端无显式 limit 约束，用户可传任意值（虽然 API 兜底校验） | P2 | 前端 queryVoicesWithDateRange / loadLogs 等处显式使用 API 约束范围内的 limit | P8-VALIDATION2-B |
| 8.4 | admin date range | input[type=date] | `validateDateRange()` 前端校验 start <= end | - | 后端 start/end 为 UTC ISO 字符串 | 一致（本地日期转 UTC 已通过 P8-TIME1 修复） | - | - | - |
| 8.5 | admin offset | JS 传参 | 无显式约束 | `Query(ge=0)` | - | 一致 | - | - | - |

## 4. 高风险问题清单

### 4.1 P0 问题（必须修复）

**P0-1：`confirm_cost: false` 导致真实 Provider 调用未真正确认**
- 位置：所有高成本操作（clone、design、preview）的 `handleCloneVoice()`、`handleDesignVoice()`、`handleAuditionSubmit()` 等
- 现象：对话框弹出但 payload `confirm_cost=false`，用户以为确认了就没事，实际后端 cost guard 收到 `confirm_cost=false`
- 潜在影响：真实 MiniMax 调用绕过费用确认

**P0-2：`segment_strategy` 无 Literal 类型约束**
- 位置：`LongtextBatchRequest.segment_strategy: str = "auto"`
- 现象：非法值通过 Pydantic 验证后在 `TextSegmentService.segment()` 抛出 `ValueError` → API 500
- 修复：改为 `Literal["auto", "paragraph", "sentence", "line"]`

**P0-3：长文本 `text` 无 `max_length`**
- 位置：`LongtextBatchRequest.text: str = Field(min_length=1)`
- 现象：前端 `maxlength="50000"` 可绕过，巨大文本到达后端
- 修复：增加 `max_length=50000`

### 4.2 P1 问题（应该修复）

**P1-1：`file_id`/`prompt_file_id` 无 `gt=0` 约束** → 改为 `Field(gt=0)`
**P1-2：前端 `cloneVoiceId` 无格式校验** → 增加 `minlength="8"` + 前端 regex 提示
**P1-3：前端 `clonePreviewText` 无 `maxlength=1000`** → 补齐
**P1-4：剧本行数无前端上限** → 200 行时禁用添加
**P1-5：`designVoiceId` 无格式校验** → 同 clone voice_id

### 4.3 P2 问题（建议修复）

**P2-1**：422 错误前端未区分字段级错误，统一显示为 `<div class="error-msg">`
**P2-2**：剧本 script 行 text 空值无行级提示
**P2-3**：`importCloneVoiceId` 无 min_length=8 限制（与 clone voice_id 规则不一致）
**P2-4**：admin 前端 call_logs limit 无显式约束
**P2-5**：`batchScriptSilence` 默认值 500 与前端默认值 500 一致，但 schema default 是 500（长文本是 300），前后端一致无需修改
**P2-6**：ScriptLine.role 为空字符串时，前端显示"旁白"但 payload 提交空字符串，后端不报错（允许空 role）

## 5. 推荐修复阶段

### P8-VALIDATION2-A：后端 Schema 收紧与服务层兜底
**目标**：修复所有 P0 和 P1 后端问题

涉及文件：
- `app/domain/schemas.py`
- `app/services/text_segment_service.py`

修改内容：
1. `LongtextBatchRequest.text` 增加 `max_length=50000`
2. `segment_strategy` 改为 `Literal["auto", "paragraph", "sentence", "line"]`
3. `VoiceCloneRequest.file_id` 改为 `Field(gt=0)`
4. `VoiceCloneRequest.prompt_file_id` 改为 `Field(gt=0)`
5. `ProviderVoiceImportRequest.provider_voice_id` 增加 `min_length=8`
6. `_segment_line` 超长行兜底增加逗号拆分

风险：低（收紧已有约束，不改变行为）

### P8-VALIDATION2-B：前端高风险输入约束补齐
**目标**：修复所有 P1 和 P2 前端问题

涉及文件：
- `app/static/index.html`

修改内容：
1. `textInput` 增加 `maxlength="10000"`（配合后端）
2. `batchText` 增加显式 `maxlength="50000"`
3. `auditionText` 增加 `maxlength="1000"`
4. `clonePreviewText` 增加 `maxlength="1000"`
5. `importClonePreviewText` 增加 `maxlength="1000"`
6. `designPrompt` 增加 `maxlength="2000"`
7. `cloneVoiceId` 增加 `minlength="8"` 和前端 regex 提示
8. `designVoiceId` 增加 `minlength="8"` 前端提示
9. 剧本行数超过 200 时禁用添加行按钮
10. 剧本行 text 空值行级拦截
11. `confirm_cost` 对话框确认后设为 `true`
12. `batchScriptText` 每行增加 `maxlength="5000"`

风险：低（只增加约束，不改变现有逻辑）

### P8-VALIDATION2-C：统一 422 字段级错误提示
**目标**：改进错误展示体验

涉及文件：
- `app/static/index.html`

修改内容：
1. `parseApiError()` 或 `renderApiError()` 支持 Pydantic 字段级错误结构
2. 字段级错误显示在对应输入框下方，不统一显示在结果区
3. 克隆/设计/导入 API 错误识别 422 并展示字段归属

风险：中（涉及错误处理重构，需充分测试）

## 6. 附录：关键文件索引

| 模块 | 后端 Schema | API 文件 | 服务层 | 前端控件 |
|---|---|---|---|---|
| 单条生成 | `VoiceRenderRequest` | `voice_render.py` | `voice_render_service.py` | `#textInput`, `#paramSpeed`, `#paramVol`, `#paramPitch` |
| 长文本批量 | `LongtextBatchRequest` | `batch.py` | `batch_orchestration_service.py` | `#batchText`, `#batchStrategy`, `#batchMaxChars`, `#batchSilence` |
| 剧本批量 | `ScriptBatchRequest`+`ScriptLine` | `batch.py` | `batch_orchestration_service.py` | `#batchScriptSilence`, `scriptLines` 动态行 |
| 音色试听 | `ProviderVoicePreviewRequest` | `provider_voices.py` | `provider_voice_preview_service.py` | `#auditionText`, `#auditionModel` |
| 声音克隆 | `VoiceCloneRequest` | `voice_clone.py` | `voice_clone_service.py` | `#cloneVoiceId`, `#cloneFileId`, `#clonePreviewText`, `#cloneModel` |
| 声音设计 | `VoiceDesignRequest` | `voice_design.py` | `voice_design_service.py` | `#designPrompt`, `#designPreviewText`, `#designVoiceId` |
| 导入音色 | `ProviderVoiceImportRequest` | `provider_voices.py` | `provider_voice_import_service.py` | `#importCloneVoiceId`, `#importClonePreviewText` |
| 历史 Jobs | `voice_jobs.py` Query | `voice_jobs.py` | - | History Tab JS |
| Admin 日志 | `admin.py` Query | `admin.py` | `stats_service.py` | `#startDate`, `#endDate`, `admin.html` |

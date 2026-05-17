# XiangTa Admin Config Write Boundary

> 文档阶段：P17-XIANGTA-ADMIN-CONFIG-B4-2
> 本文档为 B4-3 写接口实现提供设计边界、校验规则和安全约束。
> 本文档不实现任何接口，只产出设计规范。

---

## 1. 背景与当前状态

XiangTa 产品层当前配置存储在 `src/xiangta/configs/` 下的 JSON 文件：

```text
voice_mappings.json   — 音色与 Core profile 的映射关系
tone_presets.json     — 音调预设列表
recipients.json       — 收件人选项
scenes.json           — 场景选项
```

配置读取由 `ProductConfigRepository` 负责。
写入逻辑尚未实现。
当前所有 Admin 端点均为只读。

---

## 2. B4-1 已完成能力

已实现只读 Admin API：

| 端点 | 描述 |
|---|---|
| `GET /api/xiangta/admin/config` | 返回全量配置快照（含 coreProfileId） |
| `GET /api/xiangta/admin/voice-mappings` | 返回所有音色映射（含 Core/Admin 字段） |
| `GET /api/xiangta/admin/tone-presets` | 返回所有音调预设（含 renderOverrides） |

Admin API 可以暴露 `coreProfileId / providerPolicy / renderOverrides`。
用户端 `GET /bootstrap` 通过 `PublicVoicePreset` 投影，不暴露这些字段。

---

## 3. 写接口目标与非目标

### 目标（B4-3 范围）

- 修改已有 voice mapping 的字段（PUT existing）
- 启用/禁用 voice mapping（PATCH enabled）
- 修改已有 tone preset 的字段（PUT existing）
- 启用/禁用 tone preset（PATCH enabled）
- 字段格式校验和禁止字段过滤
- 原子写入（temp file → rename replace）
- 写入前自动备份

### 非目标（B4-3 不做）

- 新增 voice mapping（create）
- 新增 tone preset（create）
- 物理删除任何配置项
- Core profiles 存在性校验（需要 VoiceLabGateway 接 Core）
- 认证系统
- Admin 前端页面
- DB 化配置存储
- 多人并发 SaaS 写入保障

---

## 4. 当前配置模型

### 4.1 ProductVoiceMapping

```python
@dataclass(frozen=True)
class ProductVoiceMapping:
    id: str                          # 不可为空，唯一标识
    label: str                       # 不可为空
    desc: str                        # 不可为空
    gender_style: str | None         # female / male / None
    suitable_recipients: list[str]   # ["lover", "friend", ...]
    recommended_scenes: list[str]    # ["miss", "night", ...]
    default_tone: str                # 引用已存在 tone id
    enabled: bool                    # True / False
    sort_order: int                  # 显示排序
    core_profile_id: str             # 不可为空，Core profile 标识
    provider_policy: str | None      # default / mock / None
    render_overrides: dict           # 白名单字段
    notes: str | None                # 备注
```

JSON 键名（camelCase）：

```json
{
  "id": "female-gentle",
  "label": "温柔女声",
  "desc": "适合想念、晚安、轻声表达",
  "genderStyle": "female",
  "suitableRecipients": ["lover", "friend"],
  "recommendedScenes": ["miss", "night"],
  "defaultTone": "gentle",
  "enabled": true,
  "sortOrder": 10,
  "coreProfileId": "<placeholder>",
  "providerPolicy": "default",
  "renderOverrides": {},
  "notes": "..."
}
```

当前 `coreProfileId` 全部为占位值 `<core_profile_id_from_core_profiles>`。
GAP-B2-001 已登记此问题（发现于 B2-A0）。

### 4.2 TonePreset

```python
@dataclass(frozen=True)
class TonePreset:
    id: str                        # 不可为空
    label: str                     # 不可为空
    desc: str                      # 不可为空
    style_hint: str                # 不可为空，copywriting 语义提示
    copywriting_style: str | None  # 可选，文案风格标识
    render_overrides: dict         # 白名单字段
    enabled: bool                  # True / False
    sort_order: int                # 显示排序
```

当前 JSON 键名（snake_case）：

```json
{
  "id": "gentle",
  "label": "温柔",
  "desc": "更柔和、更靠近一点",
  "style_hint": "soft",
  "enabled": true
}
```

注意：当前 tone_presets.json 未包含 `sort_order` / `render_overrides` / `copywriting_style` 字段，
读取时由 `_to_tone_preset()` 在 repository 层提供默认值。
写接口必须保证写入文件后这些默认值行为不变（即写后仍可正常读取）。

### 4.3 ProductLimits

```python
@dataclass(frozen=True)
class ProductLimits:
    max_raw_text_chars: int = 500
    max_tts_chars: int = 500
    max_suggestions: int = 3
    allow_real_provider: bool = False
    default_audio_format: str = "mp3"
    need_subtitle_default: bool = True
```

Limits 当前硬编码，B4-3 不做 Limits 写入。

---

## 5. Admin 写接口 API Contract

### 5.1 Voice Mapping APIs

**PUT /api/xiangta/admin/voice-mappings/{id}**
更新已有 voice mapping 的完整字段（除 id 外全部可写）。

Request body：
```json
{
  "label": "温柔女声",
  "desc": "适合想念、晚安、轻声表达",
  "genderStyle": "female",
  "suitableRecipients": ["lover", "friend"],
  "recommendedScenes": ["miss", "night"],
  "defaultTone": "gentle",
  "enabled": true,
  "sortOrder": 10,
  "coreProfileId": "xiangta_female_gentle_v1",
  "providerPolicy": "mock",
  "renderOverrides": {},
  "notes": "updated"
}
```

Response (200)：
```json
{
  "ok": true,
  "data": { /* updated AdminVoiceMappingItem */ }
}
```

Error responses: `invalid_input` / `config_not_found` / `invalid_render_override` / `write_failed`

---

**PATCH /api/xiangta/admin/voice-mappings/{id}/enabled**
仅切换 enabled 状态。

Request body：
```json
{ "enabled": false }
```

Response (200)：
```json
{
  "ok": true,
  "data": { "id": "female-gentle", "enabled": false }
}
```

---

### 5.2 Tone Preset APIs

**PUT /api/xiangta/admin/tone-presets/{id}**
更新已有 tone preset 的完整字段（除 id 外全部可写）。

Request body：
```json
{
  "label": "温柔",
  "desc": "更柔和、更靠近一点",
  "styleHint": "soft",
  "copywritingStyle": null,
  "renderOverrides": {},
  "enabled": true,
  "sortOrder": 20
}
```

Response (200)：
```json
{
  "ok": true,
  "data": { /* updated AdminTonePresetItem */ }
}
```

---

**PATCH /api/xiangta/admin/tone-presets/{id}/enabled**
仅切换 enabled 状态。

Request body：
```json
{ "enabled": false }
```

Response (200)：
```json
{
  "ok": true,
  "data": { "id": "gentle", "enabled": false }
}
```

---

### 5.3 暂不实现的接口

| 端点 | 原因 |
|---|---|
| `POST /admin/voice-mappings` | create 需要 coreProfileId 来自 Core，B4-4 再做 |
| `POST /admin/tone-presets` | create 可 B4-4 再做 |
| `DELETE /admin/voice-mappings/{id}` | 不做物理删除；用 enabled=false 替代 |
| `DELETE /admin/tone-presets/{id}` | 同上 |
| `POST /admin/config/reload` | 当前不需要热重载，B4-4 评估 |

---

## 6. 字段校验规则

### 6.1 voiceMappings 校验

| 字段 | 规则 |
|---|---|
| `id` | 只读，不允许通过 PUT body 修改 |
| `label` | 必填，非空字符串，最长 50 字符 |
| `desc` | 必填，非空字符串，最长 200 字符 |
| `genderStyle` | nullable；若填写必须是 `"female"` / `"male"` |
| `suitableRecipients` | list[str]，元素必须是已知 recipientId；可为空列表 |
| `recommendedScenes` | list[str]，元素必须是已知 sceneId；可为空列表 |
| `defaultTone` | 必填，必须引用已存在的 tone id |
| `enabled` | 必须是 boolean |
| `sortOrder` | 必须是 int，>= 0 |
| `coreProfileId` | 必填，非空字符串；B4-3 只做格式校验，不校验 Core 存在性 |
| `providerPolicy` | nullable；若填写只允许 `"default"` / `"mock"` |
| `renderOverrides` | dict，所有 key 必须在白名单内（见 6.3） |
| `notes` | nullable；若填写最长 500 字符 |

### 6.2 tonePresets 校验

| 字段 | 规则 |
|---|---|
| `id` | 只读，不允许通过 PUT body 修改 |
| `label` | 必填，非空字符串，最长 50 字符 |
| `desc` | 必填，非空字符串，最长 200 字符 |
| `styleHint` | 必填，非空字符串 |
| `copywritingStyle` | nullable |
| `renderOverrides` | dict，所有 key 必须在白名单内（见 6.3） |
| `enabled` | 必须是 boolean |
| `sortOrder` | 必须是 int，>= 0 |

### 6.3 renderOverrides 白名单

写入 `renderOverrides` 时，只允许以下字段：

```text
speed          float | None    语速系数
vol            float | None    音量系数
pitch          int | None      音调偏移
emotion        str | None      情感标签
audio_format   str | None      音频格式（如 "mp3"）
need_subtitle  bool | None     是否需要字幕
```

任何不在白名单内的 key 都应返回 `invalid_render_override` 错误，
并在错误信息中列出非法字段名（不泄露 stack trace 或路径）。

### 6.4 禁止字段

以下字段严禁出现在写接口 request body 中，
出现则返回 `invalid_input` 并列出非法字段名：

```text
api_key
minimax_api_key
mimo_api_key
provider_api_key
provider_voice_id
binding_id
params_json
model
voice_id
model_id
sample_rate
bitrate
secret
env
stack_trace
raw_config
```

---

## 7. Core profile 校验边界

**B4-3 策略（本地格式校验）：**

- `coreProfileId` 必须非空字符串，格式上满足 `\S+`（无空白）即可。
- 不调用 Core `GET /api/voice/profiles` 进行存在性校验。
- 占位值 `<core_profile_id_from_core_profiles>` 格式上不满足合法格式（含 `<>`），应拒绝写入。

**B4-4 策略（接 Core 校验）：**

- 通过 `VoiceLabGateway.get_voice_profiles()` 调用 Core `GET /api/voice/profiles`。
- `coreProfileId` 必须是 Core 返回的已知 profile id。
- XiangTa 不直接查 Core ORM / repository / DB。
- VoiceLabGateway 做 in-process fake 支持，测试中不调用真实 Core。

**合法 coreProfileId 格式示例（B4-3 接受）：**

```text
xiangta_female_gentle_v1
deep_night_programmer
profile_001
```

**不合法格式（B4-3 拒绝）：**

```text
<core_profile_id_from_core_profiles>   含有 < >
                                       空字符串
   padded                              前后有空白
```

---

## 8. 写入与原子性策略

**写入流程（ProductConfigWriter）：**

```text
1. 验证输入字段（格式校验 + 禁止字段过滤）
2. 读取当前 JSON 文件到内存
3. 在内存中应用变更（find by id + update fields）
4. 将变更后的数组序列化为 JSON（indent=2，ensure_ascii=False，按 sortOrder 排序）
5. 写入临时文件 {filename}.tmp 同目录
6. 备份原文件为 {filename}.bak
7. 原子 rename：{filename}.tmp → {filename}
8. 返回更新后的配置快照
```

**关键细节：**

- 临时文件写完后调用 `f.flush(); os.fsync(f.fileno())` 确保落盘
- rename 在 POSIX 上是原子的；Windows 上用 `os.replace()`（也是原子的）
- 备份文件只保留最近一个（每次写入覆盖 `.bak`）
- JSON 序列化排序：`sort_keys=False`（保留字段顺序），按 `sortOrder` 对数组排序
- 序列化时不删除现有字段（如 `notes`、`renderOverrides` 保留即使为空）

**回滚：**

- 写入失败（文件系统错误）时，临时文件不会 rename，原文件不变
- 如果 rename 后发现数据损坏（后续读取失败），可手动从 `.bak` 恢复
- B4-3 不实现自动回滚 API；B4-4 评估是否需要

---

## 9. 备份与回滚策略

**文件命名：**

```text
voice_mappings.json      — 当前生效配置
voice_mappings.json.bak  — 最近一次写入前的备份
voice_mappings.json.tmp  — 写入临时文件（正常完成后不存在）
```

**B4-3 最小备份策略：**

- 每次写入前，将当前 JSON 覆盖备份到 `.bak`
- 只保留最近一个 `.bak`，不做版本历史
- `.bak` 文件不纳入 git 跟踪（`configs/*.bak` 加入 `.gitignore`）

**手动回滚命令（文档说明）：**

```bash
cp src/xiangta/configs/voice_mappings.json.bak \
   src/xiangta/configs/voice_mappings.json
```

**B4-4 扩展（不在 B4-3 范围）：**

- `GET /admin/config/history` — 查看写入历史
- `POST /admin/config/rollback` — 回滚到上一个版本

---

## 10. 并发写入策略

**MVP 约束（B4-3）：**

XiangTa 当前为单用户本地 Web App，不承诺多人并发 SaaS 写配置。

**B4-3 实现策略：**

- 使用 `threading.Lock()` 模块级全局锁保护写文件操作
- 一次只允许一个写请求修改配置文件
- 读操作不加锁（允许读写并发，文件系统原子 rename 保护读的一致性）

```python
import threading

_config_write_lock = threading.Lock()

class ProductConfigWriter:
    def write_voice_mapping(self, id: str, data: dict) -> dict:
        with _config_write_lock:
            # ... validate, read, apply, write, backup, replace
```

**B4-4 扩展（多用户 / 多进程）：**

- 使用 `fcntl.flock` 文件锁（Linux/Mac）
- 或引入 DB 存储（SQLite / PostgreSQL），移除 JSON 文件写入风险
- 不在 B4-3 范围内

---

## 11. 错误响应策略

**错误类型：**

| errorKind | 含义 | HTTP 状态码 |
|---|---|---|
| `invalid_input` | 请求字段格式错误或缺失必填字段 | 400 |
| `config_not_found` | 指定 id 不存在 | 404 |
| `duplicate_id` | create 时 id 已存在（B4-4） | 409 |
| `invalid_core_profile` | coreProfileId 格式非法 | 400 |
| `invalid_render_override` | renderOverrides 包含非白名单字段 | 400 |
| `write_failed` | 文件写入失败（磁盘 / 权限） | 500 |
| `conflict` | 并发写入冲突（B4-4） | 409 |
| `unknown` | 未分类错误 | 500 |

**错误响应格式（复用现有 ErrorResponse schema）：**

```json
{
  "ok": false,
  "errorKind": "invalid_render_override",
  "message": "renderOverrides 包含非法字段：api_key, secret",
  "retryable": false
}
```

**安全约束：**

- 错误消息不得包含文件系统绝对路径
- 不得泄露 stack trace
- 不得泄露 API key / env 变量
- 不得泄露 provider internal config
- 对于 500 错误，返回通用消息，详细错误只记录服务器日志

---

## 12. 用户端字段隔离

Admin 写接口修改的是内部 JSON 文件，但用户端接口通过以下机制保持隔离：

1. **PublicVoicePreset 投影**：`ProductConfigRepository.list_public_voice_presets()` 将 `ProductVoiceMapping` 投影为 `PublicVoicePreset`，只保留 `id / label / desc / gender_style / suitable_recipients / recommended_scenes / default_tone / enabled`。
2. **VoicePresetItem schema**：用户端 Pydantic schema 不包含 `coreProfileId / providerPolicy / renderOverrides / sortOrder / notes`。
3. **BootstrapData schema**：`voicePresets` 字段类型为 `list[VoicePresetItem]`，Pydantic 在序列化时自动过滤多余字段。

Admin 写接口修改 JSON 后，用户端下次请求 `/bootstrap` 时会读取最新文件，但仍通过上述投影层隔离。

**测试保障（B4-3 必须包含）：**

- 修改 voice mapping 后，`GET /bootstrap` 仍不暴露 `coreProfileId / providerPolicy / renderOverrides`
- 修改 tone preset 后，`GET /bootstrap` 的 `tonePresets` 仍不暴露 `renderOverrides`

---

## 13. 推荐模块拆分

```text
src/xiangta/
├── config/
│   ├── product_config_models.py       ← 现有，不改
│   ├── product_config_repository.py   ← 现有，只读，不改
│   └── product_config_writer.py       ← B4-3 新增
│                                         原子写文件逻辑
│                                         validate + write + backup + replace
├── services/
│   ├── admin_config_service.py        ← B4-3 新增
│   │                                     业务规则：校验 + 调 writer
│   │                                     不直接处理文件 IO
│   └── product_service.py             ← 现有，新增 admin write 方法门面
├── api/
│   ├── schemas.py                     ← 现有，新增写接口 request schema
│   └── routes.py                      ← 现有，新增 PUT / PATCH 路由
└── ...
```

**职责划分：**

| 模块 | 职责 |
|---|---|
| `ProductConfigWriter` | 文件 IO：读、校验格式、写临时文件、备份、rename |
| `AdminConfigService` | 业务规则：字段校验、禁止字段过滤、调 writer、返回快照 |
| `ProductService` | 门面：转发 admin write 请求到 AdminConfigService |
| `routes.py` | HTTP 层：解析请求、调 service、序列化响应 |

---

## 14. B4-3 最小实现范围

**必须实现：**

```text
✓ src/xiangta/config/product_config_writer.py
  - validate_voice_mapping_update(data) → 校验输入
  - validate_tone_preset_update(data) → 校验输入
  - update_voice_mapping(id, data) → 原子写
  - update_tone_preset(id, data) → 原子写
  - toggle_voice_mapping_enabled(id, enabled) → 原子写
  - toggle_tone_preset_enabled(id, enabled) → 原子写

✓ src/xiangta/services/admin_config_service.py
  - AdminConfigService(writer, repository)
  - update_voice_mapping(id, data) → dict
  - update_tone_preset(id, data) → dict
  - toggle_voice_mapping_enabled(id, enabled) → dict
  - toggle_tone_preset_enabled(id, enabled) → dict

✓ src/xiangta/api/schemas.py (新增 request models)
  - AdminVoiceMappingUpdateRequest
  - AdminTonePresetUpdateRequest
  - AdminToggleEnabledRequest

✓ src/xiangta/api/routes.py (新增路由)
  - PUT /api/xiangta/admin/voice-mappings/{id}
  - PATCH /api/xiangta/admin/voice-mappings/{id}/enabled
  - PUT /api/xiangta/admin/tone-presets/{id}
  - PATCH /api/xiangta/admin/tone-presets/{id}/enabled

✓ tests/xiangta/test_admin_config_write_api.py
  - PUT / PATCH 200 成功路径
  - config_not_found 404
  - invalid_render_override 400
  - invalid_core_profile 400
  - forbidden fields 400
  - write isolation: bootstrap 用户端不泄露
  - no app/** import
  - no real API key

✓ tests/xiangta/test_admin_config_writer.py
  - atomic write (temp file → rename)
  - backup creation
  - rollback on failure (simulate write error)
  - duplicate id handling
  - sort order preservation
  - JSON round-trip stability
```

**测试写文件时使用临时目录（`tmp_path` fixture），不修改正式 configs。**

---

## 15. B4-3 禁止事项

```text
✗ 不实现 create（POST）接口
✗ 不实现物理 delete 接口
✗ 不接 Core profiles 存在性校验
✗ 不修改 voice_mappings.json / tone_presets.json 正式文件（测试用 tmp_path）
✗ 不实现认证系统
✗ 不实现 Admin 前端页面
✗ 不引入新的 DB 表或 ORM
✗ 不修改 app/**
✗ 不读取真实 API key
✗ 不调用真实 Provider
✗ routes.py 不包含文件 IO 逻辑
✗ ProductService 不包含文件 IO 逻辑
```

---

## 16. 测试策略

### 16.1 单元测试（不依赖 HTTP）

```text
test_admin_config_writer.py
- test_update_voice_mapping_writes_temp_then_renames
- test_update_voice_mapping_creates_backup
- test_update_voice_mapping_rollback_on_write_error
- test_update_voice_mapping_preserves_sort_order
- test_update_voice_mapping_rejects_forbidden_fields
- test_update_voice_mapping_rejects_invalid_render_override
- test_update_voice_mapping_rejects_empty_core_profile_id
- test_update_voice_mapping_rejects_placeholder_core_profile_id
- test_update_voice_mapping_not_found_raises
- test_toggle_voice_mapping_enabled
- test_toggle_tone_preset_enabled
- test_update_tone_preset_writes_and_reads_back
- test_json_round_trip_stable (写入后读取结果等价)
- test_concurrent_writes_use_lock (单线程验证锁行为)
```

### 16.2 API 集成测试

```text
test_admin_config_write_api.py
- test_put_voice_mapping_200
- test_put_voice_mapping_404_not_found
- test_put_voice_mapping_400_invalid_core_profile_id
- test_put_voice_mapping_400_forbidden_field_api_key
- test_put_voice_mapping_400_invalid_render_override
- test_patch_voice_mapping_enabled
- test_put_tone_preset_200
- test_patch_tone_preset_enabled
- test_bootstrap_still_hides_core_fields_after_write
- test_no_real_api_keys_required
- test_response_does_not_expose_file_paths
- test_response_does_not_expose_stack_trace
```

### 16.3 边界测试

```text
test_boundary_contract.py (新增)
- test_admin_config_writer_does_not_import_app_modules
- test_admin_config_service_does_not_import_app_modules
- test_admin_config_service_does_not_call_core
- test_admin_config_writer_does_not_read_env
```

---

## 17. Open Gaps

| Gap ID | 问题 | 影响 | 建议处理 |
|---|---|---|---|
| GAP-B2-001 | `voice_mappings.json` 中 `coreProfileId` 全部为占位值 `<core_profile_id_from_core_profiles>` | B4-3 写接口会拒绝占位值，写入前需手动更新占位值为真实 profile id | B4-4 接 Core profiles API 后统一处理 |
| GAP-B4-001 | 当前配置存储仍为 JSON 文件，写接口需要原子写 / 备份 / 并发锁 | 单用户 MVP 可用，多人并发有数据丢失风险 | B4-3 实现 threading.Lock + atomic rename；B4-4 评估 DB 化 |
| GAP-B4-002 | coreProfileId 正式合法性校验需要 Core profiles public API / VoiceLabGateway 支持 | B4-3 只做格式校验，无法防止写入语义上不存在的 profile id | B4-4 通过 VoiceLabGateway.get_voice_profiles() 接 Core 校验 |
| GAP-B4-003 | tone_presets.json 当前不含 `sort_order` / `render_overrides` / `copywriting_style` 字段 | 写接口写入这些字段后，旧格式读取行为不变（repository 层有 default 值），但文件格式会改变 | B4-3 写入时补全这些字段（以 default 值填充未出现的字段） |

---

## 18. 结论

B4-2 确立了以下边界：

1. **B4-3 做：** update existing voice mappings / tone presets，PATCH enabled，原子写文件，threading.Lock，本地格式校验，禁止字段过滤，bootstrap 用户端字段隔离测试。
2. **B4-3 不做：** create，delete，Core profiles 校验，认证，前端，DB 化。
3. **B4-4 做：** create mapping，Core profiles 存在性校验（接 VoiceLabGateway），评估 DB 化。
4. **架构边界不变：** AdminConfigService / ProductConfigWriter 不得 import `app.*`，不得读取 `os.environ`，不得调用真实 Provider。

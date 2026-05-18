# P17 XiangTa Storage Design C3

## 1. 阶段定位

当前 XiangTa 已打通 Core 音频链路（B9），但所有业务数据仍为进程内内存存储。

**C3 只做存储设计，不做实现。**

| 里程碑 | 说明 |
|---|---|
| C2 | Runtime Config 设计（已完成） |
| **C3** | **Storage 设计（当前任务）** |
| C4 | TTS Task Orchestration 设计 |
| C9 | Storage Foundation 实现（SQLite + repositories） |

**短期目标**：SQLite MVP。本地单用户，不引入 Redis/Celery。

**长期目标**：PostgreSQL 多用户 SaaS。

**不实现的约束**：
- 不实现登录、不实现多租户、不实现权限系统
- 数据模型必须预留 `user_id nullable`
- 不存真实 Provider API key
- 不复制 Core binding detail

---

## 2. 当前存储问题

| # | 问题 | 影响 |
|---|---|---|
| 1 | `LetterService` 使用 `_LETTERS: list[dict]` 模块级全局变量 | 重启服务后所有信笺丢失 |
| 2 | 无 TTS 任务持久状态 | 无 taskId 查询、无异步状态跟踪 |
| 3 | 文案生成（`/suggestions`）无记录 | LLM 接入后无法排查问题 |
| 4 | `voice_mappings.json` 全为 `<core_profile_id_from_core_profiles>` 占位符 | GAP-B2-001，B9 H5 直接选 profileId 是临时路径 |
| 5 | 无 `user_id` 数据隔离字段 | 多用户场景无法按用户过滤数据 |
| 6 | 无软删除（`deleted_at`） | 数据无法恢复，无法保留审计轨迹 |
| 7 | 无 migration 版本治理 | schema 变更无法追踪 |
| 8 | 无统一 repository 边界 | 各 service 直接操作内存/JSON，耦合高 |

---

## 3. Storage Scope

### 近期应设计

| 表 | 用途 | 实现时机 |
|---|---|---|
| `letters` | 信笺存储 | C9-1 |
| `tts_tasks` | TTS 任务状态 | C9-2（配合 C10 Task Queue） |
| `copywriting_jobs` | 文案生成记录 | C9-3（配合 C5/C11 LLM） |
| `voice_preset_mappings` | voicePreset → coreProfileId 映射 | C9-4（配合 C7 Profile Mapping） |
| `schema_migrations` | migration 版本记录 | C9 |

### 可选或后置

| 表 | 用途 | 结论 |
|---|---|---|
| `app_settings` | 动态配置 | 短期不实现，继续用 `runtime.json` + env |
| `users` | 用户体系 | 短期不实现，user_id 预留到各表 |
| `audit_logs` | 操作审计 | 后置，多人部署时考虑 |
| `provider_usage_logs` | Provider 调用记录 | 后置 |

### 明确不做

```
不存真实 Provider API key
不复制 Core provider 配置
不存 Core binding detail
不存 provider_voice_id
不存 params_json
不存 stack trace
```

---

## 4. 数据库选择

### 推荐：SQLite MVP

**原因**：
- 本地单用户，SQLite 足够
- 零部署依赖，`sqlite3` 为 Python 标准库
- 文件即数据库，适合 H5 + local runtime 场景
- 迁移到 PostgreSQL 有成熟路径（SQLite → JSON export → PostgreSQL import）

**SQLite 限制（当前可接受）**：
- 并发写入能力弱 → 单用户无并发写入问题
- 无行级锁 → 本地单用户可接受
- 无全文搜索 → 短期不需要

### 后续升级 PostgreSQL 触发条件

```
多用户
并发写入增多
远程部署
Admin 多人管理
需要全文搜索或更强查询能力
```

### ORM 选型建议

评估顺序（由 C9 实现阶段决定）：
1. **SQLModel**（如项目已有依赖，且与 SQLAlchemy 兼容）
2. **SQLAlchemy Core**（如仅需要 SQL 构造器，不需要 ORM 全部功能）
3. **sqlite3 标准库**（如不想引入额外依赖，轻量级迁移）

**优先复用项目已有依赖，避免新增过重依赖。**

---

## 5. 表设计

### 5.1 `letters` 表

信笺是用户创作内容的核心实体。

```sql
CREATE TABLE letters (
    letter_id       TEXT    NOT NULL    PRIMARY KEY,
    user_id         TEXT    NULL,
    recipient       TEXT    NOT NULL,
    scene           TEXT    NOT NULL,
    style           TEXT    NULL,
    raw_text        TEXT    NOT NULL,
    final_text      TEXT    NOT NULL,
    voice_preset   TEXT    NULL,
    profile_id      TEXT    NULL,
    tone            TEXT    NULL,
    audio_url       TEXT    NULL,
    duration_ms     INTEGER NULL,
    title           TEXT    NULL,
    favorited       INTEGER NOT NULL    DEFAULT 0,
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    deleted_at      TEXT    NULL
);

CREATE INDEX idx_letters_user_created_at ON letters(user_id, created_at DESC);
CREATE INDEX idx_letters_deleted_at     ON letters(deleted_at);
CREATE INDEX idx_letters_favorited     ON letters(favorited);
CREATE INDEX idx_letters_scene         ON letters(scene);
```

**字段说明**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `letter_id` | TEXT PK | `L_` + 10位随机字符，当前与 `LetterService` 一致 |
| `user_id` | TEXT NULL | 预留；当前单用户可为 NULL 或 `"local"` |
| `recipient` | TEXT | 枚举：`lover` / `family` / `friend` / `self` |
| `scene` | TEXT | 枚举：`miss` / `sorry` / `thanks` / `comfort` / `night` |
| `style` | TEXT NULL | `restrained` / `gentle` / `sincere` |
| `raw_text` | TEXT | 用户输入原始心情 |
| `final_text` | TEXT | 最终发送文案 |
| `voice_preset` | TEXT NULL | `female-gentle` / `male-gentle` / ... |
| `profile_id` | TEXT NULL | B9 直接路径，H5 可选；未来由 mapping 间接填充 |
| `tone` | TEXT NULL | `gentle` / `restrained` / ... |
| `audio_url` | TEXT NULL | Core 返回的可播放绝对 URL（B9-FIX3） |
| `duration_ms` | INTEGER NULL | 音频时长，Core 返回 |
| `title` | TEXT NULL | 用户自定义标题 |
| `favorited` | INTEGER | 0/1，替代 bool（SQLite 原生不支持 bool） |
| `created_at` | TEXT | ISO 8601 UTC |
| `updated_at` | TEXT | ISO 8601 UTC |
| `deleted_at` | TEXT NULL | 软删除时间戳；NULL = 未删除 |

**安全边界**：
- 不存音频二进制，只存 `audio_url`
- `audio_url` 是 Core 返回的绝对 URL，指向 Core 资产
- XiangTa 不复制 Core asset 文件

**与现有 `LetterService` 的关系**：
- 当前 `letter_id` 生成逻辑：`"L_" + random10`，DB 设计兼容
- 当前无 `profile_id` 字段（现有 schema 无），DB 需兼容
- 当前无 `style` 字段（现有 schema 无），DB 需兼容

---

### 5.2 `tts_tasks` 表

TTS 任务状态表，C4 Task Orchestration 设计的存储基础。

```sql
CREATE TABLE tts_tasks (
    task_id          TEXT    NOT NULL    PRIMARY KEY,
    user_id          TEXT    NULL,
    status           TEXT    NOT NULL,
    text             TEXT    NOT NULL,
    recipient        TEXT    NULL,
    scene            TEXT    NULL,
    voice_preset     TEXT    NULL,
    profile_id       TEXT    NULL,
    tone             TEXT    NULL,
    audio_url        TEXT    NULL,
    duration_ms      INTEGER NULL,
    error_kind       TEXT    NULL,
    error_message    TEXT    NULL,
    retryable        INTEGER NOT NULL    DEFAULT 0,
    request_id       TEXT    NULL,
    created_at       TEXT    NOT NULL,
    started_at       TEXT    NULL,
    completed_at     TEXT    NULL,
    failed_at        TEXT    NULL,
    cancelled_at     TEXT    NULL,
    expired_at       TEXT    NULL,
    updated_at       TEXT    NOT NULL
);

CREATE INDEX idx_tts_tasks_user_created_at ON tts_tasks(user_id, created_at DESC);
CREATE INDEX idx_tts_tasks_status         ON tts_tasks(status);
CREATE INDEX idx_tts_tasks_request_id    ON tts_tasks(request_id);
CREATE INDEX idx_tts_tasks_created_at    ON tts_tasks(created_at);
```

**状态定义**：

| 状态 | 说明 |
|---|---|
| `queued` | 任务已创建，等待执行（C4 实现后） |
| `running` | 正在调用 Core render |
| `completed` | Core render 成功，`audio_url` 已返回 |
| `failed` | Core render 失败或超时 |
| `cancelled` | 用户主动取消（C4 实现后） |
| `expired` | 任务超时未完成（默认 30 分钟 TTL） |

**字段说明**：

| 字段 | 说明 |
|---|---|
| `task_id` | `T_` + 10位随机字符；C4 实现后改为 UUID |
| `status` | 状态机，见上表 |
| `text` | TTS 文案内容 |
| `audio_url` | Core 返回的绝对 URL（B9-FIX3） |
| `error_kind` | `XiangTaError.kind`，不存 Core 原始异常 |
| `error_message` | 用户可理解错误文案，不存 stack trace |
| `retryable` | 0/1；来自 `XiangTaError.retryable` |
| `request_id` | 可观测性预留，关联 API 请求日志 |

**C3 设计、C4 设计、C9-2 实现的关系**：
- C3 只设计表结构
- C4 设计异步 API + queue 策略
- C9-2 才实现 task table 落地

---

### 5.3 `copywriting_jobs` 表

文案生成任务记录，L LM 接入后建议记录，便于排查和审计。

```sql
CREATE TABLE copywriting_jobs (
    request_id        TEXT    NOT NULL    PRIMARY KEY,
    user_id           TEXT    NULL,
    recipient         TEXT    NOT NULL,
    scene            TEXT    NOT NULL,
    raw_text         TEXT    NOT NULL,
    mode             TEXT    NOT NULL,
    provider          TEXT    NULL,
    status           TEXT    NOT NULL,
    suggestions_json  TEXT    NULL,
    error_kind       TEXT    NULL,
    error_message    TEXT    NULL,
    fallback_used    INTEGER NOT NULL    DEFAULT 0,
    created_at       TEXT    NOT NULL,
    completed_at     TEXT    NULL,
    updated_at       TEXT    NOT NULL
);

CREATE INDEX idx_copywriting_jobs_user_created_at ON copywriting_jobs(user_id, created_at DESC);
CREATE INDEX idx_copywriting_jobs_status           ON copywriting_jobs(status);
CREATE INDEX idx_copywriting_jobs_provider         ON copywriting_jobs(provider);
```

**状态定义**：

| 状态 | 说明 |
|---|---|
| `pending` | 任务已创建，等待执行 |
| `completed` | 生成成功，`suggestions_json` 已填充 |
| `failed` | 生成失败 |
| `fallback` | LLM 失败，已 fallback 到模板 |

**字段说明**：

- `suggestions_json`：存校验后的 `SuggestionsData` 结构，不存 LLM 原始长日志
- `prompt` 原文是否落库要谨慎，避免用户隐私问题；当前模板版可不落库
- `fallback_used`：标记是否使用了模板 fallback，用于分析 LLM 质量

---

### 5.4 `voice_preset_mappings` 表

voicePreset → coreProfileId 映射表，未来替代 `voice_mappings.json`。

```sql
CREATE TABLE voice_preset_mappings (
    id                           TEXT    NOT NULL    PRIMARY KEY,
    label                        TEXT    NOT NULL,
    desc                         TEXT    NULL,
    core_profile_id              TEXT    NOT NULL,
    enabled                      INTEGER NOT NULL    DEFAULT 1,
    sort_order                  INTEGER NOT NULL    DEFAULT 0,
    recommended_scenes_json     TEXT    NOT NULL    DEFAULT '[]',
    suitable_recipients_json     TEXT    NOT NULL    DEFAULT '[]',
    default_tone                 TEXT    NULL,
    provider_policy              TEXT    NULL,
    render_overrides_json       TEXT    NOT NULL    DEFAULT '{}',
    notes                        TEXT    NULL,
    created_at                   TEXT    NOT NULL,
    updated_at                   TEXT    NOT NULL
);

CREATE INDEX idx_voice_preset_mappings_enabled_sort ON voice_preset_mappings(enabled, sort_order);
CREATE INDEX idx_voice_preset_mappings_core_profile_id ON voice_preset_mappings(core_profile_id);
```

**与 `voice_mappings.json` 的关系**：

- `voice_mappings.json` 可作为 seed 数据来源
- `core_profile_id` 必须来自 Core `GET /api/voice/profiles`，不允许写占位符
- 普通 H5 未来不直接暴露 `core_profile_id`（通过 voicePreset 间接）
- Admin 可以通过 `/admin/*` 接口管理映射（C7 设计）

**迁移策略**：
- 初期可继续保留 JSON，DB 作为后续实现目标
- `ProductConfigWriter` 当前写 JSON；未来替换为 DB repository

---

### 5.5 `schema_migrations` 表

Migration 版本追踪。

```sql
CREATE TABLE schema_migrations (
    version      TEXT    NOT NULL    PRIMARY KEY,
    description  TEXT    NOT NULL,
    applied_at   TEXT    NOT NULL,
    checksum     TEXT    NULL
);
```

**Migration runner 策略**：
- 启动时自动检测未应用的 migration
- 每个 migration 为顺序编号的 Python 文件（如 `001_initial.sql`）
- `applied_at` 记录 UTC 时间
- `checksum` 可选，用于校验文件完整性
- 失败时：停止启动并报错（不允许带不一致 schema 启动）

---

### 5.6 `app_settings` 表（不实现，留存设计）

短期不实现。`runtime.json` + env 覆盖足够。

未来如需 Admin 动态配置：

```sql
CREATE TABLE app_settings (
    key         TEXT    NOT NULL    PRIMARY KEY,
    value_json  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL,
    updated_by  TEXT    NULL
);
```

---

## 6. Repository / Service 分层设计

### 推荐目录结构

```
src/xiangta/
  storage/
    __init__.py
    database.py        # 连接管理、session
    migrations.py      # migration runner
    repositories/
      __init__.py
      letter_repository.py
      tts_task_repository.py
      copywriting_job_repository.py
      voice_preset_mapping_repository.py
```

**命名说明**：使用 `storage/` 而非 `repositories/`，避免与已有的 `config/product_config_repository.py` 混淆。

### 各层职责

| 层 | 职责 |
|---|---|
| `database.py` | SQLite 连接、session 管理 |
| `migrations.py` | 迁移 runner、版本校验 |
| `*_repository.py` | 单表 CRUD、查询、pagination |
| `LetterService` | 业务逻辑，委托 `LetterRepository` |
| `TtsOrchestrator` | 不感知存储，输出结果 |
| API routes | 不直接访问 repository，通过 service |

### 接口契约（未来实现时保持兼容）

```python
class LetterRepository(Protocol):
    async def create(self, data: dict) -> LetterRecord: ...
    async def list(self, user_id: str | None, limit: int, offset: int) -> list[LetterRecord]: ...
    async def get(self, letter_id: str) -> LetterRecord | None: ...
    async def soft_delete(self, letter_id: str) -> bool: ...
    async def count(self, user_id: str | None) -> int: ...
```

### 重要约束

```
ProductService 不直接访问 SQLite
API routes 不直接访问 SQLite
H5 不知道存储实现
CopywritingService → optional CopywritingJobRepository（LLM 接入后才落地）
VoicePresetMappingService → JSON repository now, DB repository later
```

---

## 7. Migration 策略

### MVP Migration Runner（C9 实现）

不引入 Alembic，用简单 Python migration runner。

```
migrations/
  __init__.py
  runner.py
  001_initial.sql
  002_add_tts_tasks.sql
  ...
```

**`runner.py` 逻辑**：
1. 读取 `schema_migrations` 表所有已 applied 版本
2. 扫描 `migrations/*.sql` 文件，排序
3. 对每个未 applied 的文件：执行 SQL，写入 `schema_migrations`
4. 全部 applied 后才启动 API

**失败策略**：任一 migration 失败则拒绝启动，不允许带不一致 schema 运行。

### SQL 或 Python migrations

| 方案 | 优点 | 缺点 |
|---|---|---|
| `.sql` 文件 | DBA 可审阅，标准SQL可移植 | 无条件逻辑 |
| Python 文件 | 可含数据迁移逻辑 | 绑定 Python 版本 |

**推荐**：`.sql` 为主；如需数据迁移，用 Python 文件（`002_backfill_*.py`）。

---

## 8. 数据安全与隐私

| 原则 | 实现方式 |
|---|---|
| 不存 API key | 所有表不包含 `api_key` 相关字段 |
| 不存 Provider secret | `provider_voice_id` / `params_json` 不进入 XiangTa 存储 |
| 不存 stack trace | `error_kind` + `error_message` 存产品错误文案 |
| 软删除 | `deleted_at IS NULL` 过滤；不物理删除用户数据 |
| 用户文本隔离 | `user_id` 字段预留；本地单用户可用 `"local"` |
| 导出/删除 | 未来用户系统需提供数据导出/注销路线图 |

---

## 9. 与 Core Asset 的边界

**核心原则**：

```
Core 负责音频文件保存和下载。
XiangTa 只保存 Core 返回的 audio_url / duration_ms / task metadata。
XiangTa 不复制 Core audio asset。
XiangTa 不直接访问 Core 文件系统。
```

**当前 B9 链路**：
```
H5 → POST /api/xiangta/tts {profileId, text}
→ VoiceLabGateway → Core HTTP POST /api/voice/render
→ Core 返回 audio_asset.url（相对路径）
→ CoreHttpClient.absolute_url() 转为 http://127.0.0.1:8000/api/voice/assets/...
→ XiangTa 存 absolute audio_url
→ H5 <audio controls> 直接请求 Core
```

**后续 asset retention**（不实现，先记录）：
- 如需长期保存音频，由 XiangTa 自己下载 Core asset 并存到自己的存储
- 不在当前 C3/C9 范围

---

## 10. 分页与查询设计

### `GET /api/xiangta/letters`

```python
# 当前实现（LetterService.list）
limit: 1-100, 默认50
offset: >= 0, 默认0
排序: created_at DESC

# C9 实现时增强
额外过滤：
  - favorited: bool | None
  - scene: str | None
  - recipient: str | None
  - created_at_after: ISO8601 | None
  - created_at_before: ISO8601 | None
```

**SQL 草案**：
```sql
SELECT * FROM letters
WHERE deleted_at IS NULL
  AND (:user_id IS NULL OR user_id = :user_id)
  AND (:favorited IS NULL OR favorited = :favorited)
  AND (:scene IS NULL OR scene = :scene)
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;
```

### `GET /api/xiangta/tts/tasks/{task_id}`

```
当前（同步返回）：
  POST /api/xiangta/tts → TtsData{taskId, status, audioUrl, ...}

C4 设计后（异步查询）：
  GET /api/xiangta/tts/tasks/{taskId}
  → {taskId, status, audioUrl?, durationMs?, errorKind?, errorMessage?, createdAt}
```

---

## 11. user_id 预留策略

**设计原则**：

```
当前不实现用户注册。
当前 user_id nullable。
本地单用户：user_id = NULL 或 "local"。
未来接入用户系统后：所有查询必须加 user_id 过滤。
```

**迁移注意**：

当前 `LetterService.create()` 不传 `user_id`：
```python
# 当前
record = { ..., "user_id": None }

# C9 实现时
record = { ..., "user_id": user_id or "local" }
```

**安全提醒**：

```
在实现用户系统前，不要把本地数据接口暴露到公网。
Admin API 无鉴权（CA-01 deferred），生产前必须处理。
```

---

## 12. 实现阶段拆分

| 阶段 | 任务 | 类型 | 说明 |
|---|---|---|---|
| C3 | Storage Design | **Design** | 当前任务 |
| C4 | TTS Task Orchestration Design | Design | async API + queue strategy |
| C5 | LLM Copywriting Design | Design | gateway + fallback |
| C6 | Error Contract Design | Design | 统一错误 schema |
| C7 | Profile Mapping Design | Design | voicePreset → coreProfileId |
| C8 | H5 Design Alignment | Design | 前端适配新 API |
| C9 | Storage Foundation | **Implementation** | database.py + migration runner |
| C9-1 | Letter Persistence | Implementation | LetterRepository 替代内存 |
| C9-2 | TTS Task Persistence | Implementation | 配合 C10 |
| C9-3 | Copywriting Job Persistence | Implementation | 配合 C5/C11 |
| C9-4 | Voice Mapping DB Migration | Implementation | 配合 C7 |
| C10 | TTS Task MVP | Implementation | async API + in-memory queue |
| C11 | LLM Copywriting MVP | Implementation | gateway + template fallback |

**C3 完成后建议**：

```
不要立即实现 Storage Foundation（C9）。
建议先完成 C4 TTS Task Orchestration Design，
因为 task table 设计和 queue 策略相互依赖。
先设计 C4，再统一决定 C9-2 实现顺序。
```

---

## 13. SQL DDL 草案（完整）

```sql
-- ============================================================
-- XiangTa Storage Schema — SQLite DDL Draft (C3)
-- ============================================================

CREATE TABLE letters (
    letter_id       TEXT    NOT NULL    PRIMARY KEY,
    user_id         TEXT    NULL,
    recipient       TEXT    NOT NULL,
    scene           TEXT    NOT NULL,
    style           TEXT    NULL,
    raw_text        TEXT    NOT NULL,
    final_text      TEXT    NOT NULL,
    voice_preset   TEXT    NULL,
    profile_id      TEXT    NULL,
    tone            TEXT    NULL,
    audio_url       TEXT    NULL,
    duration_ms     INTEGER NULL,
    title           TEXT    NULL,
    favorited       INTEGER NOT NULL    DEFAULT 0,
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    deleted_at      TEXT    NULL
);

CREATE INDEX idx_letters_user_created_at ON letters(user_id, created_at DESC);
CREATE INDEX idx_letters_deleted_at     ON letters(deleted_at);
CREATE INDEX idx_letters_favorited     ON letters(favorited);
CREATE INDEX idx_letters_scene         ON letters(scene);

-- ──────────────────────────────────────────────────────────

CREATE TABLE tts_tasks (
    task_id          TEXT    NOT NULL    PRIMARY KEY,
    user_id          TEXT    NULL,
    status           TEXT    NOT NULL,
    text             TEXT    NOT NULL,
    recipient        TEXT    NULL,
    scene            TEXT    NULL,
    voice_preset     TEXT    NULL,
    profile_id       TEXT    NULL,
    tone             TEXT    NULL,
    audio_url        TEXT    NULL,
    duration_ms      INTEGER NULL,
    error_kind       TEXT    NULL,
    error_message    TEXT    NULL,
    retryable        INTEGER NOT NULL    DEFAULT 0,
    request_id       TEXT    NULL,
    created_at       TEXT    NOT NULL,
    started_at       TEXT    NULL,
    completed_at     TEXT    NULL,
    failed_at        TEXT    NULL,
    cancelled_at     TEXT    NULL,
    expired_at       TEXT    NULL,
    updated_at       TEXT    NOT NULL
);

CREATE INDEX idx_tts_tasks_user_created_at ON tts_tasks(user_id, created_at DESC);
CREATE INDEX idx_tts_tasks_status         ON tts_tasks(status);
CREATE INDEX idx_tts_tasks_request_id    ON tts_tasks(request_id);
CREATE INDEX idx_tts_tasks_created_at    ON tts_tasks(created_at);

-- ──────────────────────────────────────────────────────────

CREATE TABLE copywriting_jobs (
    request_id        TEXT    NOT NULL    PRIMARY KEY,
    user_id           TEXT    NULL,
    recipient         TEXT    NOT NULL,
    scene             TEXT    NOT NULL,
    raw_text          TEXT    NOT NULL,
    mode              TEXT    NOT NULL,
    provider          TEXT    NULL,
    status            TEXT    NOT NULL,
    suggestions_json  TEXT    NULL,
    error_kind        TEXT    NULL,
    error_message     TEXT    NULL,
    fallback_used     INTEGER NOT NULL    DEFAULT 0,
    created_at         TEXT    NOT NULL,
    completed_at      TEXT    NULL,
    updated_at         TEXT    NOT NULL
);

CREATE INDEX idx_copywriting_jobs_user_created_at ON copywriting_jobs(user_id, created_at DESC);
CREATE INDEX idx_copywriting_jobs_status          ON copywriting_jobs(status);
CREATE INDEX idx_copywriting_jobs_provider        ON copywriting_jobs(provider);

-- ──────────────────────────────────────────────────────────

CREATE TABLE voice_preset_mappings (
    id                           TEXT    NOT NULL    PRIMARY KEY,
    label                        TEXT    NOT NULL,
    desc                         TEXT    NULL,
    core_profile_id              TEXT    NOT NULL,
    enabled                      INTEGER NOT NULL    DEFAULT 1,
    sort_order                   INTEGER NOT NULL    DEFAULT 0,
    recommended_scenes_json       TEXT    NOT NULL    DEFAULT '[]',
    suitable_recipients_json     TEXT    NOT NULL    DEFAULT '[]',
    default_tone                 TEXT    NULL,
    provider_policy              TEXT    NULL,
    render_overrides_json        TEXT    NOT NULL    DEFAULT '{}',
    notes                        TEXT    NULL,
    created_at                   TEXT    NOT NULL,
    updated_at                   TEXT    NOT NULL
);

CREATE INDEX idx_voice_preset_mappings_enabled_sort      ON voice_preset_mappings(enabled, sort_order);
CREATE INDEX idx_voice_preset_mappings_core_profile_id  ON voice_preset_mappings(core_profile_id);

-- ──────────────────────────────────────────────────────────

CREATE TABLE schema_migrations (
    version      TEXT    NOT NULL    PRIMARY KEY,
    description  TEXT    NOT NULL,
    applied_at   TEXT    NOT NULL,
    checksum     TEXT    NULL
);
```

---

## 14. 交叉引用

- **C1 Backend Capability Plan**：`docs/xiangta/BACKEND_CAPABILITY_PLAN_C1.md` — 定义了 storage 需求和表结构草案
- **C2 Runtime Config**：已实现；storage 配置在 `runtime.json` 的 `storage` section
- **C4 TTS Task Orchestration**：依赖 `tts_tasks` 表设计；C4 设计应与 C3 一致
- **C7 Profile Mapping**：依赖 `voice_preset_mappings` 表设计
- **C9 Storage Foundation**：实现此文档中的 DDL 和 repository 分层
- **GAP-B2-001**：`voice_mappings.json` 全为占位符；解决依赖 C7 Profile Mapping

---

## 15. 与 C1 BACKEND_CAPABILITY_PLAN 的关系

C1 中的 Storage Plan（章节 5）为本 C3 设计的直接输入。

| C1 定义 | C3 决策 |
|---|---|
| `letters` 表字段 | 完全采用，增加 `profile_id` / `style` 兼容性字段 |
| `tts_tasks` 表字段 | 完全采用 |
| `copywriting_jobs` 表字段 | 完全采用 |
| `voice_preset_mappings` 字段 | 完全采用 |
| `app_settings` 表 | 短期不实现，继续用 `runtime.json` |
| SQLite → PostgreSQL 升级路径 | C3 补充 PostgreSQL 触发条件 |
| Repository 分层 | C3 补充 `storage/` 目录结构和 `database.py` 职责 |

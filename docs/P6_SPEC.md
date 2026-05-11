# P6 规范：批量编排引擎（长文本 + 多角色剧本）

## 目标

在 Voice Lab 现有单条 T2A 能力上，新增批量编排层，支持两种场景：

1. **长文本模式**：一篇长文本自动分段，同一 Profile 批量生成，音频合并为完整文件
2. **多角色剧本模式**：按角色标注的剧本，每句分配不同 Profile，逐句生成，合并为完整对话音频

两种模式共享同一个编排引擎，区别仅在于输入解析和 Profile 分配策略。

---

## 核心概念

### BatchJob（批量任务）

```
BatchJob
├── id: batch_xxx
├── mode: "longtext" | "script"
├── status: pending → running → success / failed
├── segments: [Segment, Segment, ...]    # 分段列表
├── merged_audio_asset_id               # 合并后的完整音频
├── merged_subtitle_asset_id            # 合并后的完整字幕
└── progress: {total: 10, completed: 7, failed: 0}
```

### Segment（分段）

```
Segment
├── index: 0, 1, 2, ...                # 顺序
├── text: "这段文字..."                  # 分段文本
├── profile_id: "narrator"              # 该段使用的 Profile
├── role: "旁白" | "角色A" | null        # 角色名（剧本模式）
├── voice_job_id: "job_xxx"             # 对应的 VoiceJob
├── audio_asset_id: "audio_xxx"         # 生成的音频
├── status: pending → success / failed
└── params: {speed: 0.9, emotion: "sad"} # 该段特定参数覆盖
```

---

## 输入格式

### 长文本模式

```json
{
  "mode": "longtext",
  "text": "很长的文章...",
  "profile_id": "deep_night_programmer",
  "provider": "minimax",
  "output_format": "mp3",
  "segment_strategy": "auto",
  "max_segment_chars": 2000,
  "params": {"speed": 0.9}
}
```

`segment_strategy`:
- `auto`（默认）：按段落 + 句子智能分段，每段不超过 `max_segment_chars`
- `paragraph`：按空行分段
- `sentence`：按句号/问号/感叹号分段

### 多角色剧本模式

```json
{
  "mode": "script",
  "script": [
    {"role": "旁白", "text": "夜深了，城市安静下来。", "profile_id": "narrator"},
    {"role": "程序员", "text": "这个 bug 终于找到了！", "profile_id": "programmer", "params": {"emotion": "happy"}},
    {"role": "旁白", "text": "他长舒一口气，靠在椅背上。", "profile_id": "narrator"},
    {"role": "产品经理", "text": "等等，需求又改了。", "profile_id": "pm", "params": {"emotion": "neutral"}}
  ],
  "provider": "minimax",
  "output_format": "mp3",
  "silence_between_ms": 500
}
```

每个 script 条目可以指定不同的 `profile_id` 和独立的 `params` 覆盖。

---

## 架构设计

### 层次结构

```
API Layer
  POST /api/voice/batch/submit          提交批量任务
  GET  /api/voice/batch/{id}/status     查询进度
  GET  /api/voice/batch/{id}/download   下载合并音频

Service Layer
  BatchOrchestrationService             编排主逻辑
  TextSegmentService                    长文本分段
  AudioMergeService                     音频合并（pydub）

Domain Layer
  BatchJob model (SQLModel)             批量任务表
  BatchSegment model (SQLModel)         分段表
  BatchJobCreate / BatchJobStatus       请求/响应 Schema

Provider Layer
  (复用现有 adapter.render_sync)         单段生成
```

### 执行流程

```
提交 BatchJob
    │
    ├── longtext: TextSegmentService.segment(text, strategy) → segments
    ├── script: 直接映射 script[] → segments
    │
    ▼
BatchOrchestrationService.execute(batch_job)
    │
    ├── 遍历 segments（串行，保证顺序）
    │   ├── 构建 RenderPlan
    │   ├── 调用 adapter.render_sync(plan)
    │   ├── 保存 AudioAsset
    │   ├── 更新 segment 状态
    │   └── 更新 progress
    │
    ├── 全部完成后
    │   ├── AudioMergeService.merge(audio_paths, silence_ms) → merged.mp3
    │   ├── 合并字幕时间轴（偏移累加）
    │   └── 保存合并后的 AudioAsset + SubtitleAsset
    │
    └── 更新 BatchJob 状态 → success
```

### 为什么串行而非并行？

1. MiniMax API 有并发限制，并行可能触发 429
2. 串行保证音频段的生成顺序稳定
3. 失败时可以精确知道哪一段失败，重试更简单
4. 后续可优化为受限并发（semaphore=2-3），但 P6 先做串行

### 失败策略

- 单段失败时：标记该 segment 为 failed，继续生成后续段
- 全部完成后：如果有 failed 段，BatchJob 状态为 `partial`（部分成功）
- 合并时跳过 failed 段（合并可用的段）
- 提供重试接口：`POST /api/voice/batch/{id}/retry` 只重新生成 failed 的段

---

## 模块拆解

### P6-A：数据模型 + Schema + 文本分段

**新增/修改文件**：

| 文件 | 操作 |
|------|------|
| `app/models/batch_job.py` | **新建** |
| `app/domain/schemas.py` | 修改（新增 BatchJob 相关 Schema） |
| `app/domain/enums.py` | 修改（新增 JobType.batch_render, BatchStatus） |
| `app/services/text_segment_service.py` | **新建** |
| `tests/test_text_segment.py` | **新建** |

#### `app/models/batch_job.py`

```python
class BatchJob(SQLModel, table=True):
    __tablename__ = "batch_jobs"

    id: str = Field(primary_key=True)
    mode: str                              # "longtext" | "script"
    status: str = "pending"                # pending/running/success/partial/failed
    provider: str | None = None
    output_format: str = "mp3"
    total_segments: int = 0
    completed_segments: int = 0
    failed_segments: int = 0
    merged_audio_asset_id: str | None = None
    merged_subtitle_asset_id: str | None = None
    silence_between_ms: int = 300          # 段间静音（毫秒）
    config_json: str = "{}"                # 原始请求参数
    error_message: str | None = None
    created_at: str
    updated_at: str


class BatchSegment(SQLModel, table=True):
    __tablename__ = "batch_segments"

    id: str = Field(primary_key=True)
    batch_job_id: str = Field(index=True)
    index: int                             # 顺序号
    text: str
    profile_id: str
    role: str | None = None                # 角色名（剧本模式）
    params_json: str = "{}"                # 该段参数覆盖
    status: str = "pending"                # pending/running/success/failed
    voice_job_id: str | None = None
    audio_asset_id: str | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str
```

#### `app/domain/schemas.py` 新增

```python
class LongtextBatchRequest(BaseModel):
    mode: str = "longtext"
    text: str = Field(min_length=1)
    profile_id: str = "deep_night_programmer"
    provider: str | None = None
    output_format: str = "mp3"
    segment_strategy: str = "auto"         # auto/paragraph/sentence
    max_segment_chars: int = Field(default=2000, ge=100, le=5000)
    silence_between_ms: int = Field(default=300, ge=0, le=3000)
    params: dict = Field(default_factory=dict)
    need_subtitle: bool = True

class ScriptLine(BaseModel):
    role: str
    text: str = Field(min_length=1)
    profile_id: str
    params: dict = Field(default_factory=dict)

class ScriptBatchRequest(BaseModel):
    mode: str = "script"
    script: list[ScriptLine] = Field(min_length=1, max_length=200)
    provider: str | None = None
    output_format: str = "mp3"
    silence_between_ms: int = Field(default=500, ge=0, le=3000)
    need_subtitle: bool = True

class BatchSubmitResponse(BaseModel):
    batch_id: str
    mode: str
    total_segments: int
    status: str
    message: str = "批量任务已提交"

class BatchSegmentStatus(BaseModel):
    index: int
    role: str | None = None
    text_preview: str               # 前30字
    status: str
    duration_ms: int | None = None
    audio_asset_id: str | None = None
    error_message: str | None = None

class BatchStatusResponse(BaseModel):
    batch_id: str
    mode: str
    status: str
    total_segments: int
    completed_segments: int
    failed_segments: int
    segments: list[BatchSegmentStatus]
    merged_audio: dict | None = None    # {"id": "audio_xxx", "url": "/api/voice/assets/xxx/download"}
    merged_subtitle: dict | None = None
    total_duration_ms: int | None = None
    created_at: str
    updated_at: str
```

#### `app/services/text_segment_service.py`

```python
class TextSegmentService:
    def segment(
        self, text: str, strategy: str = "auto", max_chars: int = 2000
    ) -> list[str]:
        """将长文本拆分为多个段落，每段不超过 max_chars 字符。"""
```

分段策略：
- **paragraph**：按 `\n\n` 分段，超长段再按句号切分
- **sentence**：按 `。！？!?` 分段
- **auto**：先按段落分，段落超过 max_chars 再按句子切分，句子超过 max_chars 再按逗号/分号切分

每个策略的输出都是 `list[str]`，保证每段 ≤ max_chars 且不为空。

#### 测试：`tests/test_text_segment.py`（8 个）

- test_segment_auto_short_text（短文本不分段）
- test_segment_auto_by_paragraph（按段落分）
- test_segment_auto_long_paragraph_splits（超长段落按句子切）
- test_segment_paragraph_strategy
- test_segment_sentence_strategy
- test_segment_preserves_order（分段后拼接 == 原文去空白）
- test_segment_max_chars_respected（每段 ≤ max_chars）
- test_segment_empty_text_raises

### P6-B：编排 Service + 音频合并

**新增/修改文件**：

| 文件 | 操作 |
|------|------|
| `app/services/batch_orchestration_service.py` | **新建** |
| `app/services/audio_merge_service.py` | **新建** |
| `tests/test_audio_merge.py` | **新建** |
| `tests/test_batch_orchestration.py` | **新建** |

#### `app/services/audio_merge_service.py`

```python
from pydub import AudioSegment

class AudioMergeService:
    def merge(
        self,
        audio_paths: list[str],
        silence_between_ms: int = 300,
        output_format: str = "mp3",
    ) -> str:
        """合并多个音频文件，段间插入静音。返回合并后文件路径。"""
        
    def merge_timelines(
        self,
        timelines: list[list[dict]],
        durations_ms: list[int],
        silence_between_ms: int = 300,
    ) -> list[dict]:
        """合并多段字幕时间轴，偏移量累加。"""
```

合并逻辑：
1. 依次加载每个音频文件（pydub.AudioSegment.from_file）
2. 段间插入 silence_between_ms 毫秒静音（AudioSegment.silent）
3. 导出为目标格式
4. 字幕时间轴：每段的 start/end 加上前面所有段的 duration + silence 偏移

#### `app/services/batch_orchestration_service.py`

```python
class BatchOrchestrationService:
    async def submit_longtext(self, session, request: LongtextBatchRequest) -> BatchSubmitResponse:
        """提交长文本批量任务：分段 → 创建 BatchJob + Segments → 后台执行。"""
        
    async def submit_script(self, session, request: ScriptBatchRequest) -> BatchSubmitResponse:
        """提交剧本批量任务：映射 script → 创建 BatchJob + Segments → 后台执行。"""

    async def execute(self, session, batch_job_id: str) -> None:
        """执行批量任务：逐段生成 → 合并 → 更新状态。"""

    async def get_status(self, session, batch_job_id: str) -> BatchStatusResponse:
        """查询批量任务进度。"""

    async def retry_failed(self, session, batch_job_id: str) -> BatchSubmitResponse:
        """重试失败的段。"""
```

execute() 核心逻辑：
1. 加载 BatchJob + 所有 BatchSegment（按 index 排序）
2. 遍历 pending/failed 的 segment：
   - 验证 profile + binding
   - 构建 RenderPlan
   - 创建 VoiceJob
   - 调用 `adapter.render_sync(plan)`
   - 保存 AudioAsset
   - 更新 segment（status, voice_job_id, audio_asset_id, duration_ms）
   - 更新 BatchJob progress
   - 单段异常：捕获，标记 segment failed，继续
3. 收集成功段的音频路径
4. 调用 AudioMergeService.merge() 合并
5. 保存合并后的 AudioAsset + SubtitleAsset
6. 更新 BatchJob 状态

**执行方式**：submit 方法创建 BatchJob 后，用 `asyncio.create_task` 在后台执行 `execute()`。前端通过轮询 status 获取进度。

#### 测试

`tests/test_audio_merge.py`（4 个）：
- test_merge_two_wav_files
- test_merge_with_silence
- test_merge_timelines_offset
- test_merge_empty_list

`tests/test_batch_orchestration.py`（6 个）：
- test_submit_longtext_creates_batch_and_segments
- test_submit_script_creates_batch_and_segments
- test_execute_batch_generates_all_segments
- test_execute_batch_merges_audio
- test_execute_batch_partial_failure
- test_get_status_returns_progress

### P6-C：API 端点

**新增/修改文件**：

| 文件 | 操作 |
|------|------|
| `app/api/batch.py` | **新建** |
| `app/api/__init__.py` | 修改（注册 batch router） |
| `tests/test_batch_api.py` | **新建** |

```python
# app/api/batch.py
router = APIRouter()

@router.post("/batch/submit")
async def submit_batch(request: LongtextBatchRequest | ScriptBatchRequest, ...):
    """提交批量任务。根据 mode 字段分发。"""

@router.get("/batch/{batch_id}/status")
async def batch_status(batch_id: str, ...):
    """查询批量任务进度。"""

@router.get("/batch/{batch_id}/download")
async def batch_download(batch_id: str, ...):
    """下载合并后的音频文件。"""

@router.post("/batch/{batch_id}/retry")
async def batch_retry(batch_id: str, ...):
    """重试失败的段。"""
```

端点注册：`api_router.include_router(batch.router, prefix="/api/voice", tags=["batch"])`

测试 `tests/test_batch_api.py`（6 个）：
- test_submit_longtext_returns_batch_id
- test_submit_script_returns_batch_id
- test_status_returns_progress
- test_download_after_complete
- test_submit_empty_text_rejected
- test_submit_script_empty_lines_rejected

### P6-D：前端批量任务面板

**修改文件**：

| 文件 | 操作 |
|------|------|
| `app/static/index.html` | 修改（新增第 6 个 Tab） |

新增「批量生成」Tab，包含：

#### 模式切换

```
○ 长文本模式  ○ 剧本模式
```

#### 长文本模式 UI

- 大文本框（输入长文本）
- Profile 选择、Provider 选择
- 分段策略下拉（自动/段落/句子）
- 段间静音滑块（0-3000ms）
- 语音参数（复用 P5-A 的控件）
- 「提交」按钮

#### 剧本模式 UI

- 动态表单：每行一个条目（角色名 + 台词 + Profile 选择）
- 「+ 添加一行」按钮
- 段间静音滑块
- 「提交」按钮

#### 进度展示

- 提交后显示进度卡片：
  - 进度条（completed / total）
  - 分段列表表格（序号 / 角色 / 文本摘要 / 状态 / 时长）
  - 轮询刷新（3 秒间隔）
- 完成后：
  - 播放合并音频
  - 下载链接
  - 「重试失败段」按钮（如有失败）

---

## 分轮实施计划

| 轮次 | 编号 | 内容 | 改动范围 |
|------|------|------|----------|
| 1 | A | 数据模型 + Schema + 文本分段 | models, schemas, enums, text_segment_service, 8 tests |
| 2 | B | 编排 Service + 音频合并 | batch_orchestration_service, audio_merge_service, 10 tests |
| 3 | C | API 端点 | batch.py, __init__.py, 6 tests |
| 4 | D | 前端批量任务面板 | index.html |

---

## 新增依赖

无。pydub 已在 requirements.txt 中（当前已安装）。ffmpeg 由 imageio-ffmpeg 提供。

---

## 文件变更汇总

| 文件 | 操作 | 所属轮次 |
|------|------|----------|
| `app/models/batch_job.py` | 新建 | A |
| `app/domain/schemas.py` | 修改 | A |
| `app/domain/enums.py` | 修改 | A |
| `app/services/text_segment_service.py` | 新建 | A |
| `tests/test_text_segment.py` | 新建 | A |
| `app/services/batch_orchestration_service.py` | 新建 | B |
| `app/services/audio_merge_service.py` | 新建 | B |
| `tests/test_audio_merge.py` | 新建 | B |
| `tests/test_batch_orchestration.py` | 新建 | B |
| `app/api/batch.py` | 新建 | C |
| `app/api/__init__.py` | 修改 | C |
| `tests/test_batch_api.py` | 新建 | C |
| `app/static/index.html` | 修改 | D |

---

## 与现有架构的关系

```
现有单条 T2A:   POST /api/voice/render         → adapter.render_sync()
新增批量编排:   POST /api/voice/batch/submit    → BatchOrchestrationService
                                                   ├── TextSegmentService (分段)
                                                   ├── adapter.render_sync() × N (逐段)
                                                   ├── AudioMergeService (合并)
                                                   └── AssetService (保存)
```

批量编排复用现有的 Profile → Binding → RenderPlan → Provider 链路，不修改任何现有模块。新增的是"分段 + 循环调用 + 合并"的编排层。

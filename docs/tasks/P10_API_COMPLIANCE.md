# P10: MiniMax 官方 API 合规修正

## 背景

基于 MiniMax 官方文档链接逐一核对，发现 P9 修复后仍有多处与官方接口规范不一致。本轮按官方文档精确修正，不加新功能。

## 修改范围

后端 Python 文件，涉及 schemas / adapter / services。前端无改动。

---

## Commit 1：Clone 上传校验按官方规则修正

### 1a. 去掉 `.flac` 扩展名

**文件**：`app/services/voice_clone_service.py`，约第 22 行

**当前代码**：
```python
allowed_extensions = {".mp3", ".wav", ".m4a", ".flac"}
```

**官方规则**：
- voice_clone 上传：mp3、m4a、wav
- prompt_audio 上传：mp3、m4a、wav

**修改**：
```python
allowed_extensions = {".mp3", ".wav", ".m4a"}
```

同步修改 `allowed_mime_prefixes`，去掉 `"audio/flac"` 和 `"audio/x-flac"`：
```python
allowed_mime_prefixes = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4"}
```

### 1b. 增加音频时长校验（基于 purpose 区分）

**文件**：`app/services/voice_clone_service.py`

**官方规则**：
- `voice_clone`：时长 10 秒 ~ 300 秒，大小 ≤ 20MB
- `prompt_audio`：时长 < 8 秒，大小 ≤ 20MB

**修改**：

在已有的扩展名 + MIME 校验之后，增加时长校验。使用 `pydub` 或 `mutagen` 解析音频时长（选择项目中已有的依赖）。如果两个库都没有安装，使用 Python 标准库 `wave` 处理 `.wav`，对 `.mp3` / `.m4a` 跳过时长校验并在日志中记录 warning。

```python
# 时长校验逻辑（伪代码）
duration_sec = _probe_audio_duration(file_data, ext)
if duration_sec is not None:
    if purpose == "voice_clone":
        if duration_sec < 10 or duration_sec > 300:
            raise VoiceLabError("音频时长不符合要求", f"voice_clone 需要 10-300 秒，当前 {duration_sec:.1f} 秒")
    elif purpose == "prompt_audio":
        if duration_sec >= 8:
            raise VoiceLabError("音频时长不符合要求", f"prompt_audio 需要小于 8 秒，当前 {duration_sec:.1f} 秒")

# 文件大小校验
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB
if len(file_data) > MAX_UPLOAD_SIZE:
    raise VoiceLabError("音频文件过大", f"最大 20MB，当前 {len(file_data) / 1024 / 1024:.1f}MB")
```

**注意**：`_probe_audio_duration()` 作为私有方法，放在 `voice_clone_service.py` 内部。如果无法解析则返回 `None`，不阻止上传（让 MiniMax 服务端做最终校验）。

---

## Commit 2：Clone / Design 官方参数修正

### 2a. `voice_id` 正则补上末位限制

**文件**：`app/domain/schemas.py`

**官方要求**：
- 长度 [8, 256]
- 首字符必须为英文字母
- 允许数字、字母、-、_
- **末位字符不可为 `-` 或 `_`**

**当前正则**：`^[a-zA-Z][a-zA-Z0-9_-]*$` — 不限制末位

**修改**：将 `VoiceCloneRequest.voice_id` 和 `VoiceDesignRequest.voice_id` 的正则都改为：

```python
pattern=r"^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
```

含义：首位字母，末位字母或数字，中间允许字母/数字/-/_。对于长度恰好为 1 的情况由 `min_length=8` 兜底，所以实际匹配的最短串是 8 位（首位字母 + 中间 6 位任意 + 末位字母或数字）。

两处修改位置：
- 第 212 行 `VoiceCloneRequest.voice_id`
- 第 234 行 `VoiceDesignRequest.voice_id`

### 2b. Clone `preview_text` 传入时要求 `model` 必填

**文件**：`app/domain/schemas.py`，`VoiceCloneRequest` 类

**官方要求**：提供 `text` 字段时，`model` 必传。

**修改**：使用 Pydantic `model_validator` 添加联动校验：

```python
from pydantic import model_validator

class VoiceCloneRequest(BaseModel):
    voice_id: str = Field(min_length=8, max_length=256, pattern=r"^[a-zA-Z](?:[a-zA-Z0-9_-]*[a-zA-Z0-9])?$")
    file_id: int
    prompt_file_id: int | None = None
    prompt_text: str | None = None
    preview_text: str | None = Field(default=None, max_length=1000)
    model: str | None = None
    language_boost: str | None = None
    need_noise_reduction: bool = False
    need_volume_normalization: bool = False

    @model_validator(mode="after")
    def check_preview_requires_model(self):
        if self.preview_text and not self.model:
            raise ValueError("preview_text 需要同时指定 model（官方要求：提供 text 时 model 必传）")
        return self
```

### 2c. Voice Design 删除 `model` 字段

**文件**：

1. `app/domain/schemas.py`，`VoiceDesignRequest` 类（约第 231 行）
   - 删除 `model: str | None = None`

2. `app/providers/minimax_speech_adapter.py`，`design_voice()` 方法（约第 627 行）
   - 方法签名删除 `model` 参数
   - 删除 `if model: payload["model"] = model` 这两行

3. `app/services/voice_design_service.py`，第 19-20 行
   - 调用改为 `await adapter.design_voice(request.prompt, request.preview_text, request.voice_id)`
   - 不再传 `request.model`

4. `app/api/voice_clone.py`（如有 design 端点调用 model）
   - 检查并删除相关 model 传递

---

## Commit 3：Async / Batch 格式字段拆分

### 3a. `AsyncRenderRequest` 拆分格式

**文件**：`app/domain/schemas.py`，`AsyncRenderRequest` 类（约第 175 行）

**当前**：
```python
output_format: str = "hex"
```

**修改**：
```python
output_format: Literal["hex", "url"] = "hex"
audio_format: Literal["mp3", "wav", "flac"] = "mp3"
```

**联动修改** `app/services/async_render_service.py`：
- `audio_params["format"]` 使用 `request.audio_format`
- `plan.output_format` 使用 `request.output_format`（已经是 Literal["hex","url"]）

### 3b. `LongtextBatchRequest` / `ScriptBatchRequest` 拆分格式

**文件**：`app/domain/schemas.py`

**LongtextBatchRequest**（约第 276 行）：
```python
# 当前
output_format: str = "mp3"
# 修改为
output_format: Literal["hex", "url"] = "hex"
audio_format: Literal["mp3", "wav", "flac"] = "mp3"
```

**ScriptBatchRequest**（约第 296 行）：
```python
# 当前
output_format: str = "mp3"
# 修改为
output_format: Literal["hex", "url"] = "hex"
audio_format: Literal["mp3", "wav", "flac"] = "mp3"
```

**联动修改** `app/services/batch_orchestration_service.py`：

当前 `_process_segment()` 方法（约第 396 行）中 `audio_params["format"]` 直接使用 `output_format` 参数：
```python
audio_params = {
    "format": output_format,  # 错误：这里混用了 output_format 和 audio_format
    ...
}
```

需要将 `audio_format` 也传入 `_process_segment()` / `_process_segment_isolated()`，或者将 batch_job 上存储的格式拆分。

具体修改方案：

1. `BatchJob` 模型（如果有 `output_format` 字段）需要同时存储 `audio_format`
2. `submit_longtext()` 和 `submit_script()` 里 `batch_job.output_format` 改为只存 `"hex"/"url"`
3. 新增 `batch_job.audio_format` 存储 `"mp3"/"wav"/"flac"`
4. `_run_batch()` 里 `output_format = batch_job.output_format` 改为读取两个字段
5. `_process_segment()` 里 `audio_params["format"] = audio_format`，`plan.output_format = output_format`

**如果 `BatchJob` 模型没有 `audio_format` 列**：需要执行数据库迁移或使用 `config` dict 存储。最简方案是将 `audio_format` 存入已有的 `config` JSON 字段（如果 BatchJob 有的话），避免加列。

### 3c. 异步查询 file_id 优先级调整

**文件**：`app/providers/minimax_speech_adapter.py`，`query_async_task()` 方法（约第 502 行）

**当前逻辑**：
```python
file_url = body.get("file_url") or body.get("audio_url")  # 先找直接 URL
if status == "success" and not file_url:                    # 找不到才走 file_id
    file_id = body.get("file_id")
    if file_id:
        file_url = await self._retrieve_file_url(file_id)
```

**官方文档**：异步 T2A 完成后通过 `file_id` 调用 `files/retrieve` 获取 `download_url` 是主路径。

**修改**：`file_id` 作为主路径，直接 URL 字段作为兜底：
```python
file_url = None
if status == "success":
    # 主路径：file_id → files/retrieve → download_url
    file_id = body.get("file_id")
    if file_id:
        file_url = await self._retrieve_file_url(file_id)
    # 兜底：直接读取 URL 字段
    if not file_url:
        file_url = body.get("file_url") or body.get("audio_url")
```

---

## Commit 4：项目文档更新

### 4a. 更新 README 或内部文档

在项目文档中明确记录以下官方 API 约束：

1. Voice Clone 上传格式：只支持 mp3/m4a/wav，不支持 flac
2. Voice Clone voice_id：末位不可为 `-` 或 `_`
3. Voice Clone：`preview_text` → 官方字段 `text`；传 `text` 时 `model` 必传
4. Voice Design：官方接口不支持 `model` 字段
5. Get Voice 返回：`language` / `gender` 不保证返回，仅作可选字段兼容读取
6. Async T2A：`file_id` → `files/retrieve` 是官方主路径
7. WebSocket：官方支持多个 `task_continue`；当前项目 MVP 一次性提交完整 text

### 4b. README 测试数更新

执行 `python -m pytest tests/ -x -q` 获取最新通过数，更新 README。

---

## 不在本轮范围内

| 编号 | 内容 | 原因 |
|------|------|------|
| WS 多段 continue | 官方支持多个 task_continue 顺序发送 | 当前 MVP 够用，归入 P-future |
| BatchJob 数据库迁移 | 如果 Batch 拆格式需要加列 | 优先用 config JSON 字段方案避免迁移 |

---

## 测试方案

### 新增测试

1. **1a 测试**：`voice_clone_service.upload_audio()` 上传 `.flac` 文件应被拒绝（VoiceLabError）
2. **1b 测试**：
   - mock `_probe_audio_duration` 返回 5 秒，purpose="voice_clone" → 报错"时长不符合要求"
   - mock 返回 15 秒，purpose="voice_clone" → 通过
   - mock 返回 9 秒，purpose="prompt_audio" → 报错
   - mock 返回 6 秒，purpose="prompt_audio" → 通过
   - 文件大小超过 20MB → 报错
3. **2a 测试**：
   - `VoiceCloneRequest(voice_id="abcd1234-")` → Pydantic ValidationError（末位 `-`）
   - `VoiceCloneRequest(voice_id="abcd1234_")` → Pydantic ValidationError（末位 `_`）
   - `VoiceCloneRequest(voice_id="abcd1234")` → 通过
   - `VoiceDesignRequest(voice_id="abcd1234-")` → ValidationError
4. **2b 测试**：
   - `VoiceCloneRequest(preview_text="你好", model=None, ...)` → ValidationError "preview_text 需要同时指定 model"
   - `VoiceCloneRequest(preview_text="你好", model="speech-2.8-hd", ...)` → 通过
   - `VoiceCloneRequest(preview_text=None, model=None, ...)` → 通过（不传 text 时 model 不强制）
5. **2c 测试**：`VoiceDesignRequest(prompt="...", preview_text="...")` 不应有 `model` 属性，或构造时传 `model` 报错
6. **3a 测试**：
   - `AsyncRenderRequest(output_format="mp3")` → Pydantic Literal 拒绝
   - `AsyncRenderRequest(output_format="hex", audio_format="mp3")` → 通过
7. **3b 测试**：
   - `LongtextBatchRequest(output_format="mp3", ...)` → Pydantic Literal 拒绝
   - `ScriptBatchRequest(output_format="mp3", ...)` → Pydantic Literal 拒绝

### 已有测试不可回归

```bash
python -m pytest tests/ -x -q
# 期望：所有已有测试继续通过
```

## 验证清单

- [ ] 1a: 上传 .flac → 400 错误
- [ ] 1b: voice_clone 时长 < 10 秒 → 报错；prompt_audio ≥ 8 秒 → 报错；> 20MB → 报错
- [ ] 2a: voice_id 末位 `-` 或 `_` → 422 校验失败
- [ ] 2b: preview_text 非空但 model 为空 → 422 校验失败
- [ ] 2c: VoiceDesignRequest 无 model 字段；adapter 不传 model
- [ ] 3a: AsyncRenderRequest output_format 只接受 hex/url
- [ ] 3b: Batch 请求 output_format 只接受 hex/url；audio_format 独立传递
- [ ] 3c: 异步查询以 file_id → files/retrieve 为主路径
- [ ] 4a: 文档已更新官方 API 约束
- [ ] 4b: README 测试数已更新

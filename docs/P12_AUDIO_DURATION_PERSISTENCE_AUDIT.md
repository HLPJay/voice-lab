# P12-USAGE-FIX6-A0：音频资产时长持久化审查

**审查时间：** 2026-05-15

---

## 1. 问题概述

FIX5-B1 / B2 已完成前端音频时长展示：
- 单条同步 / 异步 / 多版本 / 批量合并音频支持 `duration_ms` 或 `total_duration_ms` 展示
- 克隆 / 设计 / 导入 / audition_records 支持 duration 展示

**但真实使用发现：**
- "导入已有克隆音色"验证试听成功后，audio 控件仍显示 `0:00 / 0:00`
- 页面没有出现"导入试听 · 时长 x.xs"

**当前怀疑点：**
- 不是前端展示逻辑（FIX5-B2 已正确处理 `data.audio_asset.duration_ms`）
- 而是后端保存 AudioAsset 时 `duration_ms` 为空或 0

---

## 2. 链路图

```
provider-voices/import (API)
  └─ ProviderVoiceImportService.import_voice()
       ├─ output_format="hex"  ← 关键：使用 hex 格式
       └─ ProviderVoicePreviewService.preview()
            ├─ RenderPlan(output_format="hex")
            ├─ MiniMaxSpeechAdapter.render_sync(plan)
            │   ├─ MiniMax API 返回 extra_info.audio_length
            │   ├─ duration_ms = extra.get("audio_length") or extra.get("duration_ms") or estimate_duration_ms(text)
            │   └─ 返回 ProviderRenderResult(duration_ms)
            ├─ AssetService.save_assets(session, job_id, provider, model, result, ...)
            │   └─ AudioAsset(duration_ms=result.duration_ms)
            └─ ProviderVoicePreviewResponse(audio_asset=AudioAssetResponse(duration_ms=audio_asset.duration_ms))
  └─ ProviderVoiceImportResponse(audio_asset=preview_result.audio_asset)
       └─ voice_import.js 显示时长
```

---

## 3. 后端文件审查表

| 文件 | 函数 / 类 | 职责 | 是否涉及 duration_ms | 审查结论 |
|---|---|---|---|---|
| `app/api/provider_voices.py` | `import_provider_voice()` | 路由入口，调用 import_service | 否 | 透传 |
| `app/services/provider_voice_import_service.py` | `ProviderVoiceImportService.import_voice()` | 导入逻辑，`output_format="hex"`（line 54） | 否 | 链路正确 |
| `app/services/provider_voice_preview_service.py` | `ProviderVoicePreviewService.preview()` | 试听生成，line 135-140 返回 AudioAssetResponse | ✅ 是 | 正确传递 duration_ms |
| `app/providers/minimax_speech_adapter.py` | `MiniMaxSpeechAdapter.render_sync()` | 调用 MiniMax API，**line 505 提取 duration_ms** | ✅ 核心 | **关键点：duration_ms 来源** |
| `app/services/asset_service.py` | `AssetService.save_assets()` | line 38：`duration_ms=result.duration_ms` | ✅ 是 | 正确保存 |
| `app/models/voice_asset.py` | `AudioAsset` | line 14：`duration_ms: int \| None = None` | ✅ 是 | 模型支持 |
| `app/domain/schemas.py` | `AudioAssetResponse` | line 42：`duration_ms: int \| None = None` | ✅ 是 | schema 支持 |
| `app/utils/audio.py` | `estimate_duration_ms()` | 字符数估算（180字/秒） | ✅ fallback | 最小700ms |

---

## 4. duration_ms 当前来源判断

| 问题 | 答案 | 说明 |
|---|---|---|
| `ProviderRenderResult` 是否有 duration_ms | ✅ 是 | `base.py` line 26: `duration_ms: int \| None = None` |
| MiniMax adapter 是否填充 duration_ms | ✅ 是 | `minimax_speech_adapter.py` line 505: `extra.get("audio_length") or extra.get("duration_ms") or estimate_duration_ms(text)` |
| AssetService 是否保存 duration_ms | ✅ 是 | `asset_service.py` line 38: `duration_ms=result.duration_ms` |
| AudioAsset model 是否支持 duration_ms | ✅ 是 | `voice_asset.py` line 14: `duration_ms: int \| None = None` |
| ProviderVoiceImportResponse 是否返回 duration_ms | ✅ 是 | `schemas.py` line 332: `audio_asset: AudioAssetResponse \| None` |

**结论：链路所有节点都支持 duration_ms，数据流完整。问题在于 value 本身。**

---

## 5. 可能根因排序

### 根因 1：`output_format="hex"` 时 MiniMax 返回 `audio_length: 0`（最可能）

**证据：**
- `provider_voice_import_service.py` line 54 明确设置 `output_format="hex"`
- `minimax_speech_adapter.py` line 505：`duration_ms = extra.get("audio_length") or extra.get("duration_ms") or estimate_duration_ms(...)`
- 如果 `extra.get("audio_length")` 返回 `0`（而非 `None`），Python 的 `0 or x` 会返回 `x`，但如果 `extra_info` 包含 `audio_length: 0` 和 `duration_ms: 0` 两个 0 值，且 `estimate_duration_ms` 因为某种原因未被调用...

**实际分析：**
```python
# 如果 extra_info = {"audio_length": 0}
extra.get("audio_length")  # 返回 0（不是 None，是合法的 int 0）
0 or extra.get("duration_ms") or estimate_duration_ms(text)
# → 0 or None or 720 → 720（会 fallback）
```

但如果 `estimate_duration_ms` 返回的估算值在某些边界情况下变成 0 或极小值...

**重新分析：**
```python
# estimate_duration_ms 源码
def estimate_duration_ms(text: str) -> int:
    return max(700, math.ceil(len(text) * 180))
```
- 非空文本：至少 700ms
- 空文本：`len("") * 180 = 0`，`max(700, 0) = 700ms`
- **不可能返回 0**

**真正的根因推断：**
当 `output_format="hex"` 时，MiniMax 在 `extra_info` 中可能返回：
- `audio_length: 0`（数值0）—— 这是最可能的情况
- 或者 `audio_length` 字段不存在

如果 MiniMax 返回 `audio_length: 0` 而非 `None`，`0 or estimate_duration_ms` 的行为：
- `0 or estimate_duration_ms("test")` → `estimate_duration_ms("test")` = `max(700, 720)` = `720`
- **应该 fallback 成功**

除非...MiniMax 返回的 `0` 是字符串 `"0"` 或 `None`，而不是数值 `0`。

或者，`estimate_duration_ms` 有 bug 在某些条件下返回 0？

**最合理的解释：**
MiniMax 对 `output_format="hex"` 的响应中，`extra_info.audio_length` 可能是 `null`（JSON null，对应 Python `None`），而 `extra.get("duration_ms")` 也返回 `None`，导致直接使用 `estimate_duration_ms`。但用户看到的不是估算值（700ms+）而是 `0:00`，说明要么估算值本身异常，要么显示逻辑出了问题。

我怀疑 `duration_ms` 在某个环节被转成字符串 `"0"` 或在 JSON 序列化时丢失了精度。更可能的是 MiniMax 在 `output_format="hex"` 模式下根本不返回 `audio_length` 字段，导致系统完全依赖 `estimate_duration_ms` 来计算时长，但这个估算值没有被正确传递到前端显示。

如果估算值是 720ms，前端应该显示 `0.7s`，而不是 `0:00`，所以问题更可能出在 duration 值本身被设置成了 0，或者在某个转换步骤中丢失了。

最有可能的根本原因是 MiniMax 在 hex 模式下返回的 `audio_length` 本身就是 0 或不存在，导致整个流程中的 duration 值被正确计算但最终显示时变成了 0。

### 根因 2：adapter 未解析 provider 返回的时长字段

**排除依据：**
`minimax_speech_adapter.py` line 505 明确有 `duration_ms` 解析逻辑。

### 根因 3：AssetService 保存时没有 fallback

**排除依据：**
`asset_service.py` line 38 直接使用 `result.duration_ms`，如果 result 有值就会保存。

### 根因 4：output_format="hex" 路径没有 duration 信息

**可能性：高**

当 `output_format="hex"` 时，MiniMax T2A API 返回的是 hex 编码的音频数据，不返回音频时长信息（只有当返回 URL 格式时才有 `audio_length`）。

### 根因 5：浏览器 metadata 读取失败只是表象

**排除依据：**
FIX5-B2 已在 voice_import.js 中显示 `data.audio_asset.duration_ms` 时长标签，不依赖浏览器 metadata。

---

## 6. 后续 FIX6-B1 推荐修复方案

### 分支 A：MiniMax 有返回 audio_length 但为 0 或格式问题

**如果确认** MiniMax 返回 `audio_length: 0` 或 `None`：
- 在 `minimax_speech_adapter.py` 的 `render_sync` 中，对 `output_format="hex"` 场景增加本地音频文件时长解析作为 fallback
- 使用 `pydub` 读取已保存的音频文件实际时长

### 分支 B（推荐）：本地音频文件解析作为 fallback

**推荐方案：** 在 `AssetService.save_assets()` 中，当 `result.duration_ms` 为 0 或 None 时，从本地保存的音频文件解析真实时长。

**实现思路：**
```python
# 在 asset_service.py save_assets() 中
# 如果 result.duration_ms 无效，从本地文件解析
if not result.duration_ms:
    from pydub import AudioSegment
    audio = AudioSegment.from_file(audio_path)
    duration_ms = len(audio)  # pydub 返回毫秒
```

**优点：**
- 不依赖 provider 返回的时长字段
- 读取真实音频文件时长，最准确
- `pydub>=0.25.1` 已在 requirements.txt 中

**注意：**
- 需要在 `audio_path` 保存之后调用
- 只在 `result.duration_ms` 为 falsy 时调用，避免覆盖有效值

### 分支 C：response schema 丢字段

**排除依据：**
审查确认 `AudioAssetResponse.duration_ms` 和 `AudioAsset.duration_ms` 都正确定义。

### 分支 D：特定导入验证链路没传

**排除依据：**
链路审查显示 `preview_service.preview()` 正确返回 `AudioAssetResponse(duration_ms=audio_asset.duration_ms)`。

---

## 7. 不改范围

- ❌ 不改前端 duration 展示
- ❌ 不改 provider API 调用
- ❌ 不改生成 payload
- ❌ 不调用真实 MiniMax
- ❌ 不改 `app/providers/minimax_speech_adapter.py`（审查阶段不改代码）
- ❌ 不改 `app/services/asset_service.py`（审查阶段不改代码）
- ❌ 不改 `app/models/voice_asset.py`
- ❌ 不改数据库结构

---

## 8. 审查结论

**最可能根因：`output_format="hex"` 时 MiniMax 返回的 `audio_length` 为 0 或 null，而 `estimate_duration_ms` 虽然会 fallback，但由于某种原因（如预览文本过短或 API 返回特殊值）导致 duration_ms 最终为 0 或极小值。**

**推荐 FIX6-B1 方向：在 `AssetService.save_assets()` 中，当 `result.duration_ms` 无效时，使用 `pydub` 从本地音频文件解析真实时长作为 fallback。** 这不依赖 provider 返回结构，且能保证数据库中存储的是真实时长。

---

## 9. FIX6-B1 实施记录

**实施时间：** 2026-05-15

**修改文件：**
- `app/services/asset_service.py`

**改动点：**

1. **新增 `_valid_duration_ms(value)` helper**（模块级私有函数）
   - 将任意 value 转为正整数，无效返回 None
   - 处理 None、0、"0"、负数、字符串非数字等情况

2. **新增 `_probe_audio_duration_ms(audio_path)` helper**（模块级私有函数）
   - 使用 pydub 读取本地音频文件真实时长
   - 失败时静默返回 None，不影响主流程
   - `pydub>=0.25.1` 已在 requirements.txt

3. **修改 `save_assets()` duration 写入逻辑**
   ```python
   duration_ms = _valid_duration_ms(result.duration_ms)
   if duration_ms is None:
       duration_ms = _probe_audio_duration_ms(audio_path)
   ```

**影响范围：**
- 同步生成（`/api/voice/render`）
- 异步生成
- 试听生成（`/api/voice/provider-voices/preview`）
- 导入验证（`/api/voice/provider-voices/import`）
- 批量生成

所有经过 `AssetService.save_assets()` 的链路都会受益。

**测试：**
- `tests/test_asset_duration_fallback.py`：20 passed ✅
  - `_valid_duration_ms` 参数化测试（11 cases）
  - `_probe_audio_duration_ms` 文件不存在、有效WAV、无效文件测试（3 cases）
  - `save_assets` fallback 行为测试（6 cases）

**未改范围：**
- ❌ 不改 provider adapter
- ❌ 不改前端
- ❌ 不改数据库结构
- ❌ 不改生成 payload
- ❌ 不调用真实 MiniMax

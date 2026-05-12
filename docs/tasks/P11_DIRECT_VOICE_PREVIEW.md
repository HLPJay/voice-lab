# P11: 音色直连试听接口

## 背景

当前音色列表中的「试听」功能必须先将音色绑定到某个 profile，然后通过 `/api/voice/render`（走 `resolve_binding`）来生成音频。这导致：

1. **未绑定音色无法试听** — 用户浏览音色列表时，看到一个感兴趣的声音，必须先绑定才能听到效果
2. **已绑定音色试听可能错位** — 如果一个 profile 绑定了多个音色，`resolve_binding` 按优先级选择，试听到的不一定是用户选中的那个

需要一个直连试听接口，跳过 profile binding，直接用 `provider + provider_voice_id + model` 调用 Provider 生成音频。

## 修改范围

- 新增 1 个 API 端点
- 新增 1 个 Service 方法
- 新增 1 个 Schema
- 修改前端试听逻辑
- 不改动现有渲染链路

---

## 实现方案

### 1. 新增 Schema

**文件**：`app/domain/schemas.py`

```python
class ProviderVoicePreviewRequest(BaseModel):
    """直连试听请求 — 不走 profile binding，直接指定 provider_voice_id。"""
    provider: str = "minimax"
    provider_voice_id: str = Field(min_length=1)
    model: str = "speech-2.8-hd"
    text: str = Field(min_length=1, max_length=500)
    audio_format: Literal["mp3", "wav", "flac"] = "mp3"
    output_format: Literal["hex", "url"] = "hex"
    speed: float | None = Field(None, ge=0.5, le=2.0)
    vol: float | None = Field(None, ge=0.1, le=10.0)
    pitch: int | None = Field(None, ge=-12, le=12)
    emotion: str | None = None


class ProviderVoicePreviewResponse(BaseModel):
    audio_asset: AudioAssetResponse
    provider: str
    model: str
    provider_voice_id: str
```

### 2. 新增 Service 方法

**文件**：`app/services/voice_preview_service.py`（新文件）

核心逻辑：直接构造 `RenderPlan`，不走 `resolve_binding`，不创建 `VoiceJob`（试听是轻量操作，不需要完整的任务记录）。

```python
import json
from sqlmodel import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import (
    AudioAssetResponse,
    ProviderVoicePreviewRequest,
    ProviderVoicePreviewResponse,
)
from app.providers.registry import get_provider
from app.services.asset_service import AssetService
from app.services.text_preprocess_service import TextPreprocessService
from app.utils.id_generator import new_id


class VoicePreviewService:
    def __init__(self):
        self.preprocessor = TextPreprocessService()
        self.asset_service = AssetService()
        self.logger = get_logger("voice_preview")

    async def preview(
        self,
        session: Session,
        request: ProviderVoicePreviewRequest,
    ) -> ProviderVoicePreviewResponse:
        settings = get_settings()
        adapter = get_provider(request.provider)

        processed_text = self.preprocessor.preprocess(request.text)
        voice_params = {}
        if request.speed is not None:
            voice_params["speed"] = request.speed
        if request.vol is not None:
            voice_params["vol"] = request.vol
        if request.pitch is not None:
            voice_params["pitch"] = request.pitch
        if request.emotion is not None:
            voice_params["emotion"] = request.emotion

        audio_params = {
            "format": request.audio_format,
            "sample_rate": settings.default_sample_rate,
            "bitrate": settings.default_bitrate,
            "channel": settings.default_channel,
        }

        plan = RenderPlan(
            id=new_id("preview"),
            text=request.text,
            processed_text=processed_text,
            profile_id="__preview__",  # 标记为试听，不关联真实 profile
            provider=request.provider,
            model=request.model,
            provider_voice_id=request.provider_voice_id,
            voice_params=voice_params,
            audio_params=audio_params,
            subtitle=SubtitlePlan(enabled=False),
            output_format=request.output_format,
        )

        self.logger.info(
            "preview_start provider=%s voice_id=%s model=%s text_length=%d",
            request.provider, request.provider_voice_id, request.model, len(request.text),
        )

        result = await adapter.render_sync(plan)
        audio_asset, _ = self.asset_service.save_assets(
            session,
            job_id=new_id("preview_job"),  # 临时 ID，不落 VoiceJob 表
            provider=request.provider,
            model=request.model,
            result=result,
            audio_params=audio_params,
            subtitle_type="sentence",
        )

        self.logger.info(
            "preview_success provider=%s voice_id=%s duration_ms=%s",
            request.provider, request.provider_voice_id, result.duration_ms,
        )

        return ProviderVoicePreviewResponse(
            audio_asset=AudioAssetResponse(
                id=audio_asset.id,
                url=audio_asset.file_url,
                duration_ms=audio_asset.duration_ms,
                format=audio_asset.format,
            ),
            provider=request.provider,
            model=request.model,
            provider_voice_id=request.provider_voice_id,
        )
```

**关键设计决策**：

- `profile_id="__preview__"` — 不关联真实 profile，标记为试听用途
- 不创建 `VoiceJob` — 试听是临时操作，不需要任务跟踪（但音频资产仍然保存，方便后续播放）
- 不走 `resolve_binding` — 这是核心区别，直接使用请求中的 `provider_voice_id`
- 复用现有 `render_sync` 和 `asset_service` — 不重复造轮子

### 3. 新增 API 端点

**文件**：`app/api/provider_voices.py`（在现有文件中添加）

```python
from app.domain.schemas import ProviderVoicePreviewRequest, ProviderVoicePreviewResponse
from app.services.voice_preview_service import VoicePreviewService

preview_service = VoicePreviewService()


@router.post("/provider-voices/preview", response_model=ProviderVoicePreviewResponse)
async def preview_provider_voice(
    request: ProviderVoicePreviewRequest,
    session: Session = Depends(get_session),
):
    """直连试听 — 跳过 profile binding，直接用指定的 provider_voice_id 生成音频。"""
    return await preview_service.preview(session, request)
```

不需要修改 `app/api/__init__.py`，因为 `provider_voices.router` 已经注册。

### 4. 前端修改

**文件**：`app/static/index.html`

当前试听逻辑（已绑定 → 用绑定的 profile_id 调 `/api/voice/render`，未绑定 → 提示先绑定）。

改为：

```javascript
// 音色列表试听按钮点击
async function previewVoice(providerVoiceId, voiceName) {
    const text = window._auditionText || "你好，这是一段试听文本，用于展示这个音色的效果。";
    const provider = document.getElementById('voiceProvider')?.value || 'minimax';

    try {
        const resp = await fetch('/api/voice/provider-voices/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: provider,
                provider_voice_id: providerVoiceId,
                model: 'speech-2.8-hd',
                text: text,
                audio_format: 'mp3',
                output_format: 'hex',
            }),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error?.detail || err.error?.message || '试听失败');
        }

        const data = await resp.json();
        if (data.audio_asset?.url) {
            playAudio(data.audio_asset.url);
        }
    } catch (e) {
        showToast('试听失败: ' + e.message, 'error');
    }
}
```

这样无论音色是否绑定都能直接试听。

### 5. 试听文本入口

在音色管理的试听工作区中，如果已有 `window._auditionText` 输入框，直连试听直接读取；否则使用默认文本。这样用户可以自定义试听内容。

---

## 不在本轮范围内

| 编号 | 内容 | 原因 |
|------|------|------|
| 试听缓存 | 相同 voice_id + text 不重复调用 | 后续优化，MVP 先不缓存 |
| 试听限频 | 防止快速连点导致大量 API 调用 | 前端加 debounce 即可，不需要后端限流 |
| 试听任务记录 | 把试听也写入 VoiceJob | 试听是轻量探索行为，不需要完整任务记录 |

---

## 测试方案

### 新增测试

1. **API 测试**：`POST /api/voice/provider-voices/preview` 用 `provider=mock` 返回 200 + audio_asset
2. **Schema 测试**：
   - `ProviderVoicePreviewRequest(provider_voice_id="")` → ValidationError（min_length）
   - `ProviderVoicePreviewRequest(text="", ...)` → ValidationError
   - `ProviderVoicePreviewRequest(output_format="mp3", ...)` → Literal 拒绝
3. **Service 测试**：验证 `RenderPlan.profile_id == "__preview__"`，`provider_voice_id` 直接传入不经过 binding
4. **前端测试**：手动验证未绑定音色点击试听 → 能听到该音色的声音（不再提示"请先绑定"）

### 已有测试不可回归

```bash
python -m pytest tests/ -x -q
# 期望：所有已有测试继续通过
```

## 验证清单

- [x] 未绑定音色点击试听 → 直接生成音频播放（不提示"请先绑定"）
- [x] 已绑定音色点击试听 → 生成的音频确实是该音色（不是 profile 默认绑定的）
- [x] 自定义试听文本 → 生成的音频使用自定义文本
- [x] speed/vol/pitch/emotion 参数传入 → 生效
- [x] provider=mock → 200 + audio_asset
- [x] text 为空 → 422
- [x] provider_voice_id 为空 → 422

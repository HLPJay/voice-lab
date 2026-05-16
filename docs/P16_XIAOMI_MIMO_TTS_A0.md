# P16-XIAOMI-MIMO-TTS-A0：小米 MiMo speech-synthesis-v2.5 接入前置审查

## 1. 阶段目标

对小米 MiMo speech-synthesis-v2.5 进行接入前置审查，判断是否需要新增 `xiaomi_mimo_tts` adapter plugin，以及如何映射到当前 AdapterConfig / ProviderConfig / Capability 架构。

**本阶段不是实现阶段**，不直接实现 adapter，不接入业务链路。

## 2. 官方文档来源

**URL**: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5

## 3. 文档可访问性说明

**⚠️ 官方文档页面无法通过工具访问**

尝试通过 WebFetch 工具访问 `platform.xiaomimimo.com` 时，返回错误：
```
Unable to verify if domain platform.xiaomimimo.com is safe to fetch. This may be due to network restrictions or enterprise security policies blocking claude.ai.
```

**影响**：
- 无法获取 Xiaomi MiMo speech-synthesis-v2.5 API 的实际协议细节
- 无法确认鉴权方式、endpoint、请求/响应格式
- 无法确认能力边界（同步/异步/流式/字幕/clone/design）

**处理方案**：
- 本文档基于常见企业 TTS API 模式和 MiniMax 现有 adapter 结构进行初步分析
- 下一阶段（Probe）需要人工获取文档正文、截图或直接通过浏览器访问
- Probe 脚本设计为可手动执行，不依赖工具自动抓取

## 4. 当前系统架构回顾

### 4.1 现有 Adapter 模式

| adapter_type | class | 协议 |
|---|---|---|
| `mock` | MockSpeechAdapter | 固定返回 mock audio |
| `minimax` | MiniMaxSpeechAdapter | REST JSON + Bearer token |

### 4.2 关键接口

```python
class SpeechProvider(ABC):
    provider_name: str

    @abstractmethod
    async def render_sync(self, plan: RenderPlan) -> ProviderRenderResult: ...

    async def list_voices(self, voice_type: str = "all") -> list[ProviderVoiceRead]: ...

    async def delete_voice(self, provider_voice_id: str) -> dict: ...

    async def design_voice(self, prompt: str, preview_text: str, voice_id: str | None) -> dict: ...

    async def create_async_task(self, plan: RenderPlan) -> AsyncTaskResult: ...

    async def query_async_task(self, provider_task_id: str) -> AsyncTaskStatus: ...

    async def render_stream(self, plan: RenderPlan) -> AsyncGenerator[StreamAudioChunk]: ...
```

### 4.3 RenderPlan 关键字段

```python
class RenderPlan(BaseModel):
    text: str
    processed_text: str
    model: str
    output_format: str  # "mp3", "wav", "flac"
    provider_voice_id: str
    voice_params: dict  # speed, pitch, vol, emotion
    audio_params: dict  # format, sample_rate, bitrate
    subtitle: SubtitleConfig  # enabled, type
    language_boost: str | None
```

## 5. 基于常见模式的初步分析

由于无法访问官方文档，以下分析基于**常见企业 TTS API 模式**和**小米云服务通用鉴权方式**，**需要通过 Probe 测试验证**。

### 5.1 鉴权方式（初步判断）

基于小米云服务通用模式：

| 项目 | 初步判断 | 需要验证 |
|---|---|---|
| API Key 方式 | API Key + Secret Key | Probe 验证 |
| Header | `Authorization: Bearer {token}` 或 `Xiami-Token` | Probe 验证 |
| 是否需要 app_id | 可能需要 `app-id` / `group-id` | Probe 验证 |
| 时间戳 nonce | 企业级 API 通常需要 | Probe 验证 |
| 签名机制 | 可能需要 HMAC-SHA256 签名 | Probe 验证 |

### 5.2 Endpoint（初步判断）

| 项目 | 初步判断 | 需要验证 |
|---|---|---|
| base_url | `https://api.mimo.ai` 或 `https://tts.xiaomi-mimo.com` | Probe 验证 |
| speech synthesis path | `/v1/tts` 或 `/api/synthesis` | Probe 验证 |
| HTTP method | POST (REST JSON) | Probe 验证 |
| 是否 OpenAI-compatible | 通常不是 | Probe 验证 |

### 5.3 请求体字段（初步判断）

基于常见 TTS API 和 MiniMax 对比：

| 字段 | 初步判断 | 需要验证 |
|---|---|---|
| 文本字段 | `text` 或 `input` | Probe 验证 |
| 模型字段 | `model` 或 `engine` | Probe 验证 |
| 音色字段 | `voice` 或 `speaker` | Probe 验证 |
| 输出格式 | `format` / `output_format` | Probe 验证 |
| 语速 | `speed` 或 `rate` | Probe 验证 |
| 音量 | `volume` 或 `vol` | Probe 验证 |
| 音调 | `pitch` | Probe 验证 |
| 情绪/风格 | `emotion` / `style` | Probe 验证 |
| 语言 | `language` | Probe 验证 |
| 采样率 | `sample_rate` | Probe 验证 |
| 是否支持 SSML | 可能不支持 | Probe 验证 |
| 是否支持批量文本 | 可能不支持 | Probe 验证 |
| 是否支持字幕 | 可能不支持 | Probe 验证 |
| 是否支持流式 | WebSocket 可能不支持 | Probe 验证 |
| 是否支持异步任务 | 可能有 separate endpoint | Probe 验证 |

### 5.4 响应格式（初步判断）

| 项目 | 初步判断 | 需要验证 |
|---|---|---|
| 返回内容 | JSON with audio field | Probe 验证 |
| 音频返回方式 | base64 / url / hex | Probe 验证 |
| Content-Type | `application/json` | Probe 验证 |
| request_id | 应该有 | Probe 验证 |
| usage | 可能有 | Probe 验证 |
| duration | 可能有 | Probe 验证 |
| 错误响应结构 | `{code, message}` 或 `{error}` | Probe 验证 |

### 5.5 能力边界（初步判断）

基于企业级 TTS 通常能力：

| 能力 | 初步判断 | 需要验证 |
|---|---|---|
| 同步 TTS | 支持 | Probe 验证 |
| 异步 TTS | 可能支持 | Probe 验证 |
| 流式 TTS | 通常不支持 WebSocket | Probe 验证 |
| 字幕 | 通常不支持 | Probe 验证 |
| 声音克隆 | 通常不支持 | Probe 验证 |
| 声音设计 | 通常不支持 | Probe 验证 |
| 音色列表 | 可能支持 | Probe 验证 |
| 删除音色 | 通常不支持 | Probe 验证 |
| emotion/style | 可能支持 | Probe 验证 |
| speed/pitch/vol | 可能支持 | Probe 验证 |
| 最大文本长度 | 通常 5000-10000 字符 | Probe 验证 |
| audio_format | mp3/wav 常用 | Probe 验证 |

## 6. 与现有内部协议映射

### 6.1 初步映射分析

| 内部概念 | 当前 MiniMax | 初步判断 Xiaomi MiMo | 映射策略 |
|---|---|---|---|
| `render_sync` | ✅ 支持 | 应该支持 | 最小 B1 范围 |
| `render_stream` | ✅ 支持 WebSocket | 可能不支持 | B1 不实现 |
| `create_async_task` | ✅ 支持 | 可能不支持 | B1 不实现 |
| `query_async_task` | ✅ 支持 | 可能不支持 | B1 不实现 |
| `list_voices` | ✅ 支持 | 可能不支持 | B1 不实现 |
| `delete_voice` | ✅ 支持 | 通常不支持 | B1 不实现 |
| `clone_voice` | ✅ 支持 | 通常不支持 | B1 不实现 |
| `design_voice` | ✅ 支持 | 通常不支持 | B1 不实现 |
| `upload_voice_file` | ✅ 支持 | 可能不支持 | B1 不实现 |

### 6.2 需要 provider_params 的字段

如果 Xiaomi MiMo 支持非标准字段，可能需要 `provider_params` 传递：

- 非标准情绪/风格参数
- 非标准语速/音调映射
- 特殊音频参数

## 7. 是否需要新增 adapter_type

**初步结论：需要新增 `xiaomi_mimo_tts` adapter_type**

**理由**：
1. Xiaomi MiMo 的 API 协议与 MiniMax 不同
2. 鉴权方式（可能需要 app-id + signature）与 MiniMax（Bearer token）不同
3. 请求/响应结构可能不兼容 OpenAI-compatible 模式
4. 能力边界差异大（可能不支持流式/异步/clone/design）

**需要 Probe 验证后最终确认**。

## 8. AdapterConfig 草案

⚠️ 以下草案基于初步分析，**需要 Probe 验证后修正**。

```yaml
# config/adapters/xiaomi_mimo_tts.yaml (DRAFT - NEEDS PROBE VERIFICATION)

adapter_type: "xiaomi_mimo_tts"

display_name: "Xiaomi MiMo"

default_base_url: "https://api.mimo.ai"  # PLACEHOLDER - NEEDS VERIFICATION

default_model: "speech-synthesis-v2.5"  # PLACEHOLDER - NEEDS VERIFICATION

default_timeout_seconds: 120

endpoints:
  tts: "/v1/tts"  # PLACEHOLDER - NEEDS VERIFICATION
  # async endpoints unknown - NEEDS VERIFICATION

tts:
  supported: true
  models:
    - "speech-synthesis-v2.5"  # PLACEHOLDER - NEEDS VERIFICATION
  default_model: "speech-synthesis-v2.5"
  max_text_chars: 5000  # PLACEHOLDER - NEEDS VERIFICATION
  audio_formats:
    - "mp3"
    - "wav"
  supports_subtitle: false
  supports_streaming: false  # PLACEHOLDER - NEEDS VERIFICATION
  supports_emotion: false  # PLACEHOLDER - NEEDS VERIFICATION

batch:
  supported: false  # Xiaomi MiMo likely doesn't support batch

script:
  supported: false  # Xiaomi MiMo likely doesn't support script

voice_clone:
  supported: false

voice_design:
  supported: false

provider_voices:
  supported: false  # PLACEHOLDER - NEEDS VERIFICATION

metadata:
  version: "v2.5"
  note: "Draft - needs probe verification"
```

## 9. ProviderConfig 草案

⚠️ 以下草案基于初步分析，**需要 Probe 验证后修正**。

```yaml
# config/providers.yaml (DRAFT - NEEDS PROBE VERIFICATION)

# 不在正式 config/providers.yaml 中新增
# 仅作为 B1 实现时的草案参考
```

如果 B1 决定接入，ProviderConfig 草案：

```yaml
- name: "xiaomi_mimo"
  display_name: "Xiaomi MiMo"
  enabled: false  # 初始 disabled，需要手动启用
  adapter_type: "xiaomi_mimo_tts"
  real_cost: true  # Xiaomi MiMo 收费
  api_key_env: "XIAOMI_MIMO_API_KEY"
  # 可能还需要 app_id_env / secret_env - NEEDS VERIFICATION
  base_url: null  # 从 adapter config 获取
  endpoints: {}  # 从 adapter config 获取
  default_model: "speech-synthesis-v2.5"
  tts:
    enabled: true
  batch:
    enabled: false
  script:
    enabled: false
  voice_clone:
    enabled: false
  voice_design:
    enabled: false
  provider_voices:
    enabled: false
  metadata:
    api_type: "xiaomi_mimo"
```

## 10. 最小探测测试方案

### 10.1 Probe 目标

1. 确认鉴权是否正确
2. 确认最小文本能否生成音频
3. 确认 response 是 bytes / JSON / url / base64
4. 确认 mp3/wav 格式支持
5. 确认错误响应结构
6. 确认 unsupported model / unsupported voice 的错误格式
7. 确认最大文本长度或超长文本错误
8. 确认是否返回 request_id / usage / duration

### 10.2 Probe 用例（设计但不执行）

#### Case 1：最小成功请求

```
POST /v1/tts  # 或实际 endpoint
Headers:
  Authorization: Bearer {XIAOMI_MIMO_API_KEY}
  Content-Type: application/json
Body:
{
  "text": "你好，这是一次语音合成测试。",
  "model": "speech-synthesis-v2.5",
  "voice": "speaker_001",
  "format": "mp3"
}

预期：
- 200 OK
- JSON response with audio field
```

#### Case 2：指定 audio_format

```
Body:
{
  "text": "测试格式",
  "model": "speech-synthesis-v2.5",
  "voice": "speaker_001",
  "format": "wav"
}

预期：
- 200 OK
- 检查 Content-Type 是 audio/wav 还是 application/json
```

#### Case 3：错误鉴权

```
Headers:
  Authorization: Bearer invalid_key_12345

预期：
- 401 Unauthorized 或 403 Forbidden
- 检查错误结构
```

#### Case 4：非法模型

```
Body:
{
  "text": "测试",
  "model": "nonexistent-model",
  "voice": "speaker_001"
}

预期：
- 4xx 错误
- 检查错误码和错误信息结构
```

#### Case 5：非法 voice/speaker

```
Body:
{
  "text": "测试",
  "model": "speech-synthesis-v2.5",
  "voice": "nonexistent_voice"
}

预期：
- 4xx 错误
- 检查错误信息
```

#### Case 6：超长文本

```
Body:
{
  "text": "X" * 20000,  # 假设 max 是 5000
  "model": "speech-synthesis-v2.5",
  "voice": "speaker_001"
}

预期：
- 4xx 错误
- 检查 max_text_chars 和错误信息
```

#### Case 7：可选参数

```
Body:
{
  "text": "测试参数",
  "model": "speech-synthesis-v2.5",
  "voice": "speaker_001",
  "speed": 1.5,
  "pitch": 0.5,
  "emotion": "happy"
}

预期：
- 检查这些参数是否被接受
- 检查是否影响输出
```

### 10.3 Probe 脚本设计

建议新增 `scripts/probe_xiaomi_mimo_tts.py`：

```python
#!/usr/bin/env python3
"""
Xiaomi MiMo TTS API Probe Script

用途：手动探测 Xiaomi MiMo speech-synthesis-v2.5 API 能力边界
不进入业务链路，不进入 database / AudioAsset / history
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 默认 dry-run，不请求外部 API
DEFAULT_DRY_RUN = True

PROBE_OUTPUT_DIR = Path("tmp/probes/xiaomi_mimo")

def get_api_key():
    key = os.environ.get("XIAOMI_MIMO_API_KEY", "")
    if not key:
        print("ERROR: XIAOMI_MIMO_API_KEY not set")
        sys.exit(1)
    return key

def probe_minimal_request(api_key: str, base_url: str):
    """Case 1: 最小成功请求"""
    print("\n=== Case 1: Minimal Request ===")
    payload = {
        "text": "你好，这是一次语音合成测试。",
        "model": "speech-synthesis-v2.5",
        "voice": "speaker_001",
        "format": "mp3"
    }
    # 实现探测逻辑...
    return {"status": "pending", "payload": payload}

def probe_audio_format(api_key: str, base_url: str, fmt: str):
    """Case 2: 指定 audio_format"""
    print(f"\n=== Case 2: Format={fmt} ===")
    # ...

def probe_auth_error(api_key: str, base_url: str):
    """Case 3: 错误鉴权"""
    print("\n=== Case 3: Auth Error ===")
    # ...

def probe_invalid_model(api_key: str, base_url: str):
    """Case 4: 非法模型"""
    print("\n=== Case 4: Invalid Model ===")
    # ...

def probe_invalid_voice(api_key: str, base_url: str):
    """Case 5: 非法 voice"""
    print("\n=== Case 5: Invalid Voice ===")
    # ...

def probe_long_text(api_key: str, base_url: str):
    """Case 6: 超长文本"""
    print("\n=== Case 6: Long Text ===")
    # ...

def probe_optional_params(api_key: str, base_url: str):
    """Case 7: 可选参数"""
    print("\n=== Case 7: Optional Params ===")
    # ...

def main():
    parser = argparse.ArgumentParser(description="Xiaomi MiMo TTS Probe")
    parser.add_argument("--real-call", action="store_true", help="Enable actual API calls")
    parser.add_argument("--dry-run", action="store_true", default=DEFAULT_DRY_RUN)
    parser.add_argument("--base-url", default="https://api.mimo.ai", help="Base URL")
    args = parser.parse_args()

    dry_run = not args.real_call

    if dry_run:
        print("⚠️  DRY RUN MODE - No real API calls will be made")
        print("   Use --real-call to enable actual requests")
    else:
        print("⚠️  REAL CALL MODE - API calls will be made")
        print("   Ensure you have set XIAOMI_MIMO_API_KEY")

    api_key = get_api_key()
    base_url = args.base_url

    PROBE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 执行所有 probe cases
    results = {}
    results["case1"] = probe_minimal_request(api_key, base_url)
    results["case2a"] = probe_audio_format(api_key, base_url, "mp3")
    results["case2b"] = probe_audio_format(api_key, base_url, "wav")
    results["case3"] = probe_auth_error(api_key, base_url)
    results["case4"] = probe_invalid_model(api_key, base_url)
    results["case5"] = probe_invalid_voice(api_key, base_url)
    results["case6"] = probe_long_text(api_key, base_url)
    results["case7"] = probe_optional_params(api_key, base_url)

    # 保存结果
    output_file = PROBE_OUTPUT_DIR / f"probe_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Results saved to {output_file}")

if __name__ == "__main__":
    main()
```

## 11. P16-XIAOMI-MIMO-TTS-B1 最小实现建议

如果 Probe 测试确认需要新增 adapter，以下是 B1 最小范围：

### B1 最小支持范围

| 功能 | 是否支持 | 原因 |
|---|---|---|
| 同步 TTS | ✅ 支持 | 核心能力 |
| 单文本输入 | ✅ 支持 | 核心能力 |
| 单 voice/speaker | ✅ 支持 | 核心能力 |
| mp3 格式 | ✅ 支持 | 最常用 |
| wav 格式 | 待定 | 根据 Probe 结果 |
| 本地音频文件保存 | ✅ 支持 | 复用现有逻辑 |
| mock transport 单元测试 | ✅ 支持 | 必须 |

### B1 明确不支持

| 功能 | 原因 |
|---|---|
| 流式 TTS | Xiaomi 可能不支持 WebSocket |
| 异步任务 | Xiaomi 可能不支持 |
| 字幕 | Xiaomi 可能不支持 |
| 声音克隆 | Xiaomi 可能不支持 |
| 声音设计 | Xiaomi 可能不支持 |
| 音色删除 | Xiaomi 可能不支持 |
| 音色列表 | Xiaomi 可能不支持 |
| provider voice import | Xiaomi 可能不支持 |
| 批量长文本 | B1 范围外 |
| 剧本模式 | B1 范围外 |
| UI 改造 | B1 范围外 |

### B1 探测后需要确认

1. 鉴权方式是否正确
2. endpoint 是否正确
3. 请求体字段名是否正确
4. 响应格式是否正确
5. 音频返回方式（base64/url/hex）
6. 错误响应结构
7. max_text_chars
8. 支持的 audio_format

## 12. 当前不能判断的信息

由于文档无法访问，以下信息**无法判断**，需要通过 Probe 或用户提供文档正文：

1. **鉴权细节**：是否需要 app-id + secret + signature，还是简单 API Key
2. **endpoint 完整路径**：base_url + path
3. **请求体字段名**：text/input/model/voice/format 等
4. **响应格式**：audio 是 base64/url/hex，还是其他
5. **能力边界**：是否支持异步/流式/字幕/clone/design
6. **错误格式**：标准错误结构
7. **max_text_chars**：最大文本长度
8. **支持 audio_format**：mp3/wav/flac 等
9. **支持 model 列表**：具体 model name
10. **支持 voice/speaker 列表**：具体 voice ID

## 13. 剩余风险

| 风险 | 级别 | 说明 |
|---|---|---|
| 文档无法访问 | 🔴 高 | 无法准确判断 API 协议 |
| 初步分析可能错误 | 🟡 中 | 基于常见模式推断，可能与实际不符 |
| adapter_type 判断 | 🟡 中 | 可能不需要新增 adapter |
| 能力边界判断 | 🟡 中 | 可能 Xiaomi MiMo 能力更丰富或更少 |

## 14. 下一阶段建议

### 推荐路径

| 阶段 | 内容 | 前提 |
|---|---|---|
| **P16-XIAOMI-MIMO-TTS-A0-DOCS-BLOCKED** | 等待用户提供 Xiaomi MiMo 文档正文/截图 | 当前状态 |
| 或 **P16-XIAOMI-MIMO-TTS-PROBE** | 人工阅读文档 + 执行 probe 脚本 | 用户提供文档 |
| 或 **P16-XIAOMI-MIMO-TTS-B1** | 实现最小 Xiaomi MiMo adapter | Probe 完成 |

### 阻塞原因

官方文档无法通过工具访问，导致：
1. 无法确认鉴权方式
2. 无法确认 endpoint
3. 无法确认请求/响应格式
4. 无法确认能力边界

### 建议用户操作

1. **提供文档正文**：复制 https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5 的文档正文
2. **提供截图**：如果无法复制文字，提供关键 API 截图
3. **或直接告知**：Xiaomi MiMo 的 API 是否与 MiniMax 兼容

### 备选阶段（不阻塞）

如果 Xiaomi MiMo 文档长期无法获取，可以考虑：

| 阶段 | 内容 | 前提 |
|---|---|---|
| P16-OPENAI-COMPATIBLE-TTS-A0 | 分析 OpenAI TTS API | OpenAI 文档可访问 |
| P16-DYNAMIC-PROVIDER-CONFIG-B2 | Provider capability override 增强 | 不依赖外部文档 |

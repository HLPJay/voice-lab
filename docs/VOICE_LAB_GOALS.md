# Voice Lab 目标归档

## 一句话目标

开发一个可扩展的 Voice Lab 声音中台，将 MiniMax `speech-2.8-hd` 等语音能力封装成标准化的产品服务能力。

## 第一阶段产品形态

第一版核心形态是“旁白试音台”：

```text
输入文案
-> 选择场景 / 声音人设
-> 生成 1 个或多个旁白版本
-> 保存音频文件
-> 保存字幕时间轴
-> 记录生成任务
-> 返回可播放、可下载、可被视频模块复用的资产
```

## 业务背景

用户拥有 MiniMax Token Plan，希望探索并沉淀可复用的声音服务模块。未来可能服务于：

- 情绪 MV 生成器
- 旁白试音台
- 播客生成器
- 短剧配音工具
- 有声书生成器
- 商家广告视频旁白
- 个人 IP 内容生产工具

## 关键约束

系统不能让业务代码直接调用 MiniMax TTS，也不能让业务层直接传递 MiniMax 字段。

错误方向：

```text
产品模块 -> MiniMax voice_id / speed / emotion / subtitle_enable
```

正确方向：

```text
产品模块 -> text / scene / voice_profile / need_subtitle
Voice Lab -> RenderPlan -> Provider Adapter -> MiniMax
```

## 核心抽象

- `VoiceProfile`：声音人设，产品级资产。
- `VoiceBinding`：声音人设在某个 Provider 下的实现绑定。
- `RenderPlan`：内部标准生成计划。
- `VoiceJob`：一次生成任务。
- `AudioAsset`：本地音频资产。
- `SubtitleAsset`：字幕资产。
- `VoiceVariantGroup`：多版本试听组。
- `VoiceVariant`：单个试听版本。

## MiniMax 能力边界

P0 只实现 MiniMax T2A HTTP 同步接口：

```text
POST /v1/t2a_v2
model = speech-2.8-hd
stream = false
output_format = hex
subtitle_enable = true
subtitle_type = sentence
```

P0 只把 Voice Clone、Voice Design、Voice Management、异步 T2A 作为后续扩展方向，不在第一版强行实现。

## P0 成功标准

- 系统可启动。
- SQLite 表可自动创建。
- 默认声音人设可 seed。
- Mock Provider 可完整跑通。
- MiniMax Adapter 代码存在，但真实调用不作为自动测试前提。
- 单条生成与多版本生成流程形成标准任务记录和本地资产。
- README 和架构文档足够让其他实现模块接手。

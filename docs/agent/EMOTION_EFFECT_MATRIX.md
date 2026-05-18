# Emotion Effect Matrix — C10B

## 1. 产品情绪目标

想Ta了不是普通文案工具，而是**手机端情绪表达入口**。

目标是帮助用户把"不好说、说不顺、怕说重"的话，整理成更合适的文字和语音。

## 2. Recipient 情绪边界

| recipient | 情绪边界 |
|---|---|
| lover（恋人）| 亲密、温柔、可稍微更靠近，但不能油腻/压迫/施压 |
| family（父母）| 克制、真诚、少煽情，多体谅，不越界 |
| friend（朋友）| 自然、轻松、不过度沉重，不刻意煽情 |
| self（自己）| 独白、接纳、低评判，自我陪伴感 |

## 3. Scene 情绪目标

| scene | 目标情绪 | 应包含 | 应避免 | 适合 tone |
|---|---|---|---|---|
| miss（想念）| 轻轻表达挂念，不给对方压力 | 具体瞬间、想起对方、靠近感 | 占有欲、逼回应、太肉麻 | 温柔 / 轻声 |
| sorry（道歉）| 承担责任，表达在意 | 承认问题、理解对方感受、愿意改变 | 找借口、逼原谅、道德绑架 | 真诚 / 克制 |
| thanks（感谢）| 具体感谢，表达珍惜 | 具体细节、对方给予的支持、被记住 | 空泛客套、过度煽情 | 温柔 / 真诚 |
| comfort（安慰）| 陪伴和接住对方 | 允许对方脆弱、不急着解决、"我在" | 说教、讲大道理、否定痛苦 | 轻声 / 温柔 |
| night（晚安）| 收束一天，给安全感 | 放下压力、温柔收尾、安心休息 | 重话题、制造焦虑、展开争论 | 睡前 / 轻声 |

## 4. Style 输出要求

### restrained / 克制版

- **目标**：短、稳、少修饰、不施压
- **语言特征**：简短句式、近乎陈述、留白多
- **应避免**：感叹号、情感形容词堆砌、命令式
- **适合场景**：family、自我对话、不确定对方状态时

### gentle / 温柔版

- **目标**：更柔软、有陪伴感、有关系温度
- **语言特征**：柔软词汇、轻声语气、有互动感
- **应避免**：过度肉麻、占有欲表达、逼迫感
- **适合场景**：lover、深夜、对方需要被接住时

### sincere / 真诚版

- **目标**：更直接、承担情绪、表达重点清楚
- **语言特征**：第一人称、直接承认感受、不绕弯
- **应避免**：过度道歉、道德说教、逻辑论证
- **适合场景**：sorry、thanks、需要认真说清楚时

## 5. LLM 接入前最小测试矩阵（10 cases）

| # | recipient | scene | rawText 示例 | expectedEffect | mustAvoid | expectedStyles | suggestedTone | manualEvalNotes |
|---|---|---|---|---|---|---|---|---|
| 1 | lover | miss | "我今天突然很想你" | 轻轻挂念，有关系温度 | 占有欲、"必须回" | gentle, sincere | 温柔 | 挂念感要轻不腻 |
| 2 | lover | sorry | "那天我话说重了，后来一直后悔" | 承担责任，不找借口 | 逼原谅、"但是"句式 | sincere, restrained | 真诚 | 歉意要真不虚 |
| 3 | lover | night | "今天先到这里，晚安" | 温柔收束，放下压力 | 重话题、展开争论 | gentle, restrained | 睡前 | 收束感要自然 |
| 4 | family | thanks | "你那天一直陪着我，想认真说声谢谢" | 具体感谢，克制真诚 | 煽情、空泛客套 | sincere, restrained | 真诚 | 感激要实不要虚 |
| 5 | family | sorry | "上次那件事我处理得很不好" | 承担责任，不辩解 | 找借口、道德绑架 | restrained, sincere | 克制 | 歉意要真不绕弯 |
| 6 | friend | comfort | "听说你最近工作很累" | 陪伴感，不说教 | "你应该..."、"我懂" | gentle, sincere | 轻声 | 陪伴感要真不说教 |
| 7 | friend | thanks | "那天你帮了我大忙，一直没好好说" | 具体细节，不过度 | 过度煽情、回报压力 | sincere, gentle | 真诚 | 感激要自然不刻意 |
| 8 | self | night | "今天先到这里吧，别再想那些了" | 接纳，放下，接纳感 | 自我批判、施压 | gentle, restrained | 睡前 | 独白要接纳不评判 |
| 9 | self | comfort | "如果你累了就先休息" | 允许脆弱，不否定 | 说教、否定感受 | gentle, restrained | 轻声 | 允许感要不否定 |
| 10 | lover | comfort | "不管怎样我都在" | 陪伴感，有承担 | 占有欲、逼迫感 | gentle, sincere | 温柔 | 陪伴要不施压 |

## 6. 人工评估标准

评分 1～5，5 分最优：

| 维度 | 含义 |
|---|---|
| 自然度 | 文案读起来是否像人话，不生硬 |
| 情绪贴合度 | 是否贴近指定 scene 的目标情绪 |
| 边界感 | 是否在 recipient 合适的情绪边界内 |
| 不油腻程度 | 是否有油腻/肉麻/占有欲感（越低越油腻） |
| 不是说教程度 | 是否避免了说教/否定/大道理 |
| 可发送性 | 用户是否愿意发出这条 |
| 适合转语音程度 | 是否适合 TTS 朗读 |

**通过标准**：
- 任一 case 任一维度不得低于 3 分
- 关键 case（lover + miss/sorry，family + sorry）平均不低于 4 分
- 不得出现：逼迫、PUA、道德绑架、过度承诺、医疗/心理诊断式表达

## 7. 后续 LLM 接入阶段建议

下一步不是本任务执行，而是后续阶段：

- **P18-XIANGTA-LLM-PROMPT-CONTRACT-C10C**：制定 prompt contract、离线评估样本、效果验收标准
- **P18-XIANGTA-MINIMAX-COPYWRITING-ADAPTER-C10D**：接真实 MiniMax LLM adapter（behind flag，不影响 formal 路径）

当前状态（C10B）：
- CopywritingGateway 仍为 TemplateCopywritingGateway 或 FakeLlmCopywritingGateway
- 无真实 API 调用，无 API key 读取
- 情绪效果由 template 字符串拼接实现，与真实 LLM 效果存在差距
- 差距主要在：自然度、场景贴合力、边界感控制

## 8. 当前 RAW_EXAMPLES 情绪对应

| scene | RAW_EXAMPLES 情绪 |
|---|---|
| miss | 雨夜挂念，安静靠近感 ✓ |
| sorry | 承认情绪，不找借口 ✓ |
| thanks | 具体细节 + 在意 ✓ |
| comfort | 允许脆弱，不解决 ✓ |
| night | 放下工作，好好睡 ✓ |

## 9. 当前 GUIDANCE_PROMPTS 方向

| scene | GUIDANCE_PROMPTS 引导方向 |
|---|---|
| miss | 感受焦点、避免太重、上次互动 |
| sorry | 具体事件、责任承认、避免借口 |
| thanks | 具体细节、意义、没说出口的那句 |
| comfort | 对方经历、接住方式、不说教 |
| night | 晚安感觉、放松收尾、不说重话 |

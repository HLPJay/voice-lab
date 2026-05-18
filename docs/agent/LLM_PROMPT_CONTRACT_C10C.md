# LLM Prompt Contract — C10C

## 1. C10C 目标

建立 copywriting LLM 的 prompt contract，为后续 C10D 真实 MiniMax adapter 接入提供稳定的输入/输出规范。

本阶段**不调用真实 LLM，不读取 API key，不发起网络请求**。

## 2. 为什么本阶段不接真实 LLM

- C10B 的情绪效果矩阵明确了产品目标，但未量化到 prompt 层面
- 需要先建立 prompt contract，再让 adapter 实现者有据可依
- 离线样本 + 静态测试可验证 contract 完整性，无需真实调用
- C10D 才接入真实 provider behind flag，默认不启用

## 3. Prompt 输入字段

```python
@dataclass(frozen=True)
class PromptContractInput:
    recipient: str   # lover | family | friend | self
    scene: str      # miss | sorry | thanks | comfort | night
    raw_text: str   # 用户原始输入
    max_suggestions: int = 3
```

## 4. Prompt system message 规则

system message 必须包含：

```
- 产品定位：想Ta了 — 手机端情绪表达入口
- Recipient 边界（lover/family/friend/self 各有明确边界）
- Scene 目标情绪（5 个场景各有 goal/should_include/should_avoid/suitable_tones）
- Style 输出要求（restrained/gentle/sincere 各有目标/语言特征/应避免/适合场景）
- 全局安全禁止项（10 条）
- TTS 朗读友好要求（7 条）
- JSON 输出格式要求（纯 JSON，不得 markdown 包裹）
```

## 5. Prompt user message 规则

user message 必须包含：

```
- recipient 字段
- scene 字段（含目标情绪说明）
- recipient_boundary
- 用户原始输入（raw_text）
- 要求生成 3 条建议（restrained/gentle/sincere）
- 明确引用当前 scene 和 recipient 的规则
```

## 6. 预期 JSON 输出 schema

```json
{
  "summary": "string — 对用户输入的整体理解",
  "intent": "string — 本次表达的核心目标",
  "suggestions": [
    {
      "style": "restrained | gentle | sincere",
      "styleLabel": "克制版 | 温柔版 | 真诚版",
      "fitsFor": "string — 说明这个风格适合什么情况",
      "text": "string — 最终输出文案，建议 20-80 字"
    }
  ]
}
```

约束：
- 必须恰好 3 条 suggestions
- style 必须是 restrained/gentle/sincere
- 不得包含 markdown 代码块
- 不得包含 apiKey/coreProfileId/providerRawResponse

## 7. Recipient 边界

| recipient | 边界 |
|---|---|
| lover | 亲密温柔但不能油腻/压迫/施压，禁止占有欲表达 |
| family | 克制真诚少煽情，不越界，禁止命令式语气 |
| friend | 自然轻松不沉重，不刻意煽情，禁止回报压力 |
| self | 独白接纳低评判，禁止自我批判/施压 |

## 8. Scene 情绪规则

| scene | 目标 | 应包含 | 应避免 | tone |
|---|---|---|---|---|
| miss | 轻轻挂念不施压 | 具体瞬间、靠近感 | 占有欲、逼回应 | 温柔/轻声 |
| sorry | 承担责任表达在意 | 承认问题、愿意改变 | 找借口、逼原谅 | 真诚/克制 |
| thanks | 具体感谢表达珍惜 | 具体细节、被记住 | 空泛客套、过度煽情 | 温柔/真诚 |
| comfort | 陪伴接住对方 | 允许脆弱、"我在" | 说教、否定痛苦 | 轻声/温柔 |
| night | 收束给安全感 | 放下压力、安心休息 | 重话题、争论 | 睡前/轻声 |

## 9. Style 输出规则

| style | 目标 | 语言特征 | 应避免 |
|---|---|---|---|
| restrained | 短稳少修饰不施压 | 简短句式、留白多 | 感叹号堆砌、命令式 |
| gentle | 柔软有陪伴感 | 柔软词汇、轻声语气 | 过度肉麻、占有欲 |
| sincere | 直接承担清楚表达 | 第一人称、直接承认感受 | 过度道歉、道德说教 |

## 10. Safety 禁止项

```
1. 不得逼迫对方回应
2. 不得 PUA
3. 不得道德绑架
4. 不得威胁
5. 不得过度承诺
6. 不得医疗/心理诊断式表达
7. 不得说教
8. 不得用"你必须/你应该/你最好"压迫对方
9. 不得暴露技术字段（apiKey/coreProfileId/providerRawResponse）
10. 不得英文夹杂过多
```

## 11. TTS 友好规则

```
- 句子不宜过长（建议 ≤40 字）
- 避免复杂括号符号
- 适合自然朗读节奏
- 少用网络梗
- 少用英文单词夹杂
- 避免堆叠感叹号
- 语气自然不戏剧化
```

## 12. 后续 C10D 如何复用

C10D 实现 MiniMax Copywriting adapter 时：

1. **输入构建**：调用 `build_copywriting_prompt_contract(PromptContractInput(...))` 获取 `PromptContract`
2. **消息发送**：将 `contract.messages` 转为 MiniMax chat API 格式
3. **输出解析**：将 LLM 响应 JSON 解析为 `CopywritingResult`（与现有 `copywriting_gateway.py` 接口一致）
4. **Schema 校验**：用 `contract.expected_json_schema` 校验 LLM 输出
5. **静态验证**：用 `validate_prompt_contract_static(contract)` 验证 contract 完整性
6. **离线评估**：用 `build_offline_eval_cases()` 获取 10 个测试 case

adapter 内部不调用 `CopywritingService`，独立实现 `generate()` 方法，behind flag 控制。

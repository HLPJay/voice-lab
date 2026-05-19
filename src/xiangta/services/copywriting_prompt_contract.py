# -*- coding: utf-8 -*-
"""
Copywriting Prompt Contract — LLM input/output contract for copywriting suggestions.

C10C: defines prompt schema, output schema, safety rules, and offline eval cases.
No real API calls, no API key access, no network I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

# ── Version ────────────────────────────────────────────────────────────────────

CONTRACT_VERSION: Final[str] = "1.0"

# ── Recipient boundaries ───────────────────────────────────────────────────────

RECIPIENT_BOUNDARIES: Final[dict[str, str]] = {
    "lover": (
        "亲密、温柔、可稍微更靠近，但绝不能油腻、压迫或施压。 "
        "禁止占有欲表达、禁止逼迫对方回应。"
    ),
    "family": (
        "克制、真诚、少煽情，多体谅，不越界。 "
        "禁止过度亲密、禁止命令式语气。"
    ),
    "friend": (
        "自然、轻松、不过度沉重，不刻意煽情。 "
        "禁止回报压力、禁止过度郑重。"
    ),
    "self": (
        "独白、接纳、低评判，自我陪伴感。 "
        "禁止自我批判、禁止施压。"
    ),
}

# ── Scene emotion rules ────────────────────────────────────────────────────────

_SCENE_RULES: Final[dict[str, tuple[str, str, str, str]]] = {
    "miss": (
        "轻轻表达挂念，不给对方压力",
        "具体瞬间、想起对方、靠近感",
        "占有欲、逼回应、太肉麻",
        "温柔 / 轻声",
    ),
    "sorry": (
        "承担责任，表达在意",
        "承认问题、理解对方感受、愿意改变",
        "找借口、逼原谅、道德绑架",
        "真诚 / 克制",
    ),
    "thanks": (
        "具体感谢，表达珍惜",
        "具体细节、对方给予的支持、被记住",
        "空泛客套、过度煽情",
        "温柔 / 真诚",
    ),
    "comfort": (
        "陪伴和接住对方",
        "允许对方脆弱、不急着解决、我一直在",
        "说教、讲大道理、否定痛苦",
        "轻声 / 温柔",
    ),
    "night": (
        "收束一天，给安全感",
        "放下压力、温柔收尾、安心休息",
        "重话题、制造焦虑、展开争论",
        "睡前 / 轻声",
    ),
}

SCENE_EMOTION_RULES: Final[dict[str, dict[str, str]]] = {
    scene: {
        "goal": goal,
        "should_include": should_include,
        "should_avoid": should_avoid,
        "suitable_tones": suitable_tones,
    }
    for scene, (goal, should_include, should_avoid, suitable_tones) in _SCENE_RULES.items()
}

# ── Style output rules ─────────────────────────────────────────────────────────

STYLE_OUTPUT_RULES: Final[dict[str, dict[str, str]]] = {
    "restrained": {
        "goal": "短、稳、少修饰、不施压",
        "language": "简短句式、近乎陈述、留白多",
        "avoid": "感叹号、情感形容词堆砌、命令式",
        "scenes": "family、自我对话、不确定对方状态时",
    },
    "gentle": {
        "goal": "更柔软、有陪伴感、有关系温度",
        "language": "柔软词汇、轻声语气、有互动感",
        "avoid": "过度肉麻、占有欲表达、逼迫感",
        "scenes": "lover、深夜、对方需要被接住时",
    },
    "sincere": {
        "goal": "更直接、承担情绪、表达重点清楚",
        "language": "第一人称、直接承认感受、不绕弯",
        "avoid": "过度道歉、道德说教、逻辑论证",
        "scenes": "sorry、thanks、需要认真说清楚时",
    },
}

# ── Global safety rules ───────────────────────────────────────────────────────

GLOBAL_SAFETY_RULES: Final[str] = (
    "【安全禁止项 - 必须严格执行】\n"
    '1. 不得逼迫对方回应（禁止"你必须回""你看到没""怎么不回"）\n'
    '2. 不得 PUA（禁止否定对方感受、禁止"你就是这样的人"）\n'
    '3. 不得道德绑架（禁止"我都这样了你还..."、"你应该感恩"）\n'
    '4. 不得威胁（禁止"你要是不...我就..."、禁止制造恐惧）\n'
    '5. 不得过度承诺（禁止"我永远会...""我一定...""我保证..."）\n'
    '6. 不得医疗/心理诊断式表达（禁止"你有病""你这是抑郁症""你需要治疗"）\n'
    '7. 不得说教（禁止"你应该...""你必须...""你只要...就..."）\n'
    '8. 不得用"你必须/你应该/你最好"压迫对方\n'
    '9. 不得暴露技术字段（禁止 apiKey/provider/coreProfileId/rawResponse）\n'
    "10. 不得出现英文夹杂过多（保持中文为主、自然流畅）"
)

# ── TTS-friendly rules ────────────────────────────────────────────────────────

TTS_FRIENDLY_RULES: Final[str] = (
    "【TTS 朗读友好要求】\n"
    "1. 句子不宜过长，建议不超过 40 字\n"
    "2. 避免复杂括号和符号（如 [[]]、{{}}、<<<）\n"
    "3. 适合自然朗读的节奏和停顿\n"
    "4. 少用网络梗和流行语（时效性差）\n"
    "5. 少用英文单词夹杂（影响朗读流畅性）\n"
    "6. 避免堆叠感叹号（最多 1 个）\n"
    "7. 语气自然，不过度戏剧化"
)

# ── Output schema ───────────────────────────────────────────────────────────────

EXPECTED_JSON_SCHEMA: Final[dict] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "对用户输入的整体理解，一句话概括"},
        "intent": {"type": "string", "description": "本次表达的核心目标，一句话"},
        "suggestions": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": [
                {
                    "style": {"type": "string", "enum": ["restrained", "gentle", "sincere"]},
                    "styleLabel": {"type": "string", "enum": ["克制版", "温柔版", "真诚版"]},
                    "fitsFor": {"type": "string", "description": "说明这个风格适合什么情况"},
                    "text": {"type": "string", "description": "最终输出的文案，建议 20-80 字"},
                },
            ],
        },
    },
    "required": ["summary", "intent", "suggestions"],
    "additionalProperties": False,
}


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PromptContractInput:
    recipient: str
    scene: str
    raw_text: str
    max_suggestions: int = 3


@dataclass(frozen=True)
class PromptMessage:
    role: str
    content: str


@dataclass(frozen=True)
class PromptContract:
    version: str
    messages: list[PromptMessage]
    expected_json_schema: dict
    evaluation_notes: dict


# ── Offline eval cases ───────────────────────────────────────────────────────────

OFFLINE_EVAL_CASES: Final[list[dict]] = [
    {
        "case_id": 1,
        "recipient": "lover",
        "scene": "miss",
        "raw_text": "我今天突然很想你",
        "expected_effect": "轻轻挂念，有关系温度",
        "must_avoid": "占有欲、必须回",
        "expected_styles": ["gentle", "sincere"],
        "suggested_tone": "温柔",
        "manual_eval_notes": "挂念感要轻不腻",
    },
    {
        "case_id": 2,
        "recipient": "lover",
        "scene": "sorry",
        "raw_text": "那天我话说重了，后来一直后悔",
        "expected_effect": "承担责任，不找借口",
        "must_avoid": "逼原谅、但是句式",
        "expected_styles": ["sincere", "restrained"],
        "suggested_tone": "真诚",
        "manual_eval_notes": "歉意要真不虚",
    },
    {
        "case_id": 3,
        "recipient": "lover",
        "scene": "night",
        "raw_text": "今天先到这里，晚安",
        "expected_effect": "温柔收束，放下压力",
        "must_avoid": "重话题、展开争论",
        "expected_styles": ["gentle", "restrained"],
        "suggested_tone": "睡前",
        "manual_eval_notes": "收束感要自然",
    },
    {
        "case_id": 4,
        "recipient": "family",
        "scene": "thanks",
        "raw_text": "你那天一直陪着我，想认真说声谢谢",
        "expected_effect": "具体感谢，克制真诚",
        "must_avoid": "煽情、空泛客套",
        "expected_styles": ["sincere", "restrained"],
        "suggested_tone": "真诚",
        "manual_eval_notes": "感激要实不要虚",
    },
    {
        "case_id": 5,
        "recipient": "family",
        "scene": "sorry",
        "raw_text": "上次那件事我处理得很不好",
        "expected_effect": "承担责任，不辩解",
        "must_avoid": "找借口、道德绑架",
        "expected_styles": ["restrained", "sincere"],
        "suggested_tone": "克制",
        "manual_eval_notes": "歉意要真不绕弯",
    },
    {
        "case_id": 6,
        "recipient": "friend",
        "scene": "comfort",
        "raw_text": "听说你最近工作很累",
        "expected_effect": "陪伴感，不说教",
        "must_avoid": "你应该…、我懂",
        "expected_styles": ["gentle", "sincere"],
        "suggested_tone": "轻声",
        "manual_eval_notes": "陪伴感要真不说教",
    },
    {
        "case_id": 7,
        "recipient": "friend",
        "scene": "thanks",
        "raw_text": "那天你帮了我大忙，一直没好好说",
        "expected_effect": "具体细节，不过度",
        "must_avoid": "过度煽情、回报压力",
        "expected_styles": ["sincere", "gentle"],
        "suggested_tone": "真诚",
        "manual_eval_notes": "感激要自然不刻意",
    },
    {
        "case_id": 8,
        "recipient": "self",
        "scene": "night",
        "raw_text": "今天先到这里吧，别再想那些了",
        "expected_effect": "接纳，放下，接纳感",
        "must_avoid": "自我批判、施压",
        "expected_styles": ["gentle", "restrained"],
        "suggested_tone": "睡前",
        "manual_eval_notes": "独白要接纳不评判",
    },
    {
        "case_id": 9,
        "recipient": "self",
        "scene": "comfort",
        "raw_text": "如果你累了就先休息",
        "expected_effect": "允许脆弱，不否定",
        "must_avoid": "说教、否定感受",
        "expected_styles": ["gentle", "restrained"],
        "suggested_tone": "轻声",
        "manual_eval_notes": "允许感要不否定",
    },
    {
        "case_id": 10,
        "recipient": "lover",
        "scene": "comfort",
        "raw_text": "不管怎样我都在",
        "expected_effect": "陪伴感，有承担",
        "must_avoid": "占有欲、逼迫感",
        "expected_styles": ["gentle", "sincere"],
        "suggested_tone": "温柔",
        "manual_eval_notes": "陪伴要不施压",
    },
]


# ── Core builder ────────────────────────────────────────────────────────────────

def _build_system_message(recipient: str, scene: str) -> str:
    recipient_boundary = RECIPIENT_BOUNDARIES.get(recipient, "自然、真诚表达")
    scene_rule = SCENE_EMOTION_RULES.get(scene, {})
    scene_goal = scene_rule.get("goal", "真诚表达")
    scene_include = scene_rule.get("should_include", "")
    scene_avoid = scene_rule.get("should_avoid", "")
    scene_tones = scene_rule.get("suitable_tones", "")

    lines = [
        "【产品定位】想Ta了 — 手机端情绪表达入口。",
        '帮助用户把"不好说、说不顺、怕说重"的话，整理成更合适的文字和语音。',
        "",
        "【当前任务】根据用户输入，生成 3 条风格不同的文案建议。",
        "",
        f"【Recipient 边界】{recipient_boundary}",
        "",
        f"【Scene 目标】{scene_goal}",
        f"  应包含：{scene_include}",
        f"  应避免：{scene_avoid}",
        f"  适合 tone：{scene_tones}",
        "",
        "【Style 输出要求】",
    ]

    for style, rule in STYLE_OUTPUT_RULES.items():
        lines.append(
            f"  [{rule['goal']}] {rule['language']} "
            f"应避免：{rule['avoid']} 适合：{rule['scenes']}"
        )

    lines.extend(["", GLOBAL_SAFETY_RULES, "", TTS_FRIENDLY_RULES, "", "【JSON 输出要求】"])
    lines.append(
        "必须输出纯 JSON，不得包含 markdown 代码块标记，不得包含解释文字。\n"
        "输出结构必须严格遵循以下 schema：\n"
        f"{EXPECTED_JSON_SCHEMA}"
    )
    return "\n".join(lines)


def _build_user_message(input_data: PromptContractInput) -> str:
    scene_rule = SCENE_EMOTION_RULES.get(input_data.scene, {})
    scene_goal = scene_rule.get("goal", "")
    recipient_boundary = RECIPIENT_BOUNDARIES.get(input_data.recipient, "")

    lines = [
        f"recipient: {input_data.recipient}",
        f"scene: {input_data.scene}（{scene_goal}）",
        f"recipient_boundary: {recipient_boundary}",
        "",
        f"用户想说的话：{input_data.raw_text}",
        "",
        "请生成 3 条风格建议：restrained（克制版）、gentle（温柔版）、sincere（真诚版）。",
        "每条建议要贴合当前 scene 的目标情绪和 recipient 的边界。",
        f"输出 {input_data.max_suggestions} 条建议，严格遵循 JSON schema。",
    ]
    return "\n".join(lines)


def build_copywriting_prompt_contract(input_data: PromptContractInput) -> PromptContract:
    """
    Build a PromptContract for copywriting LLM.

    No network I/O, no API key access.
    """
    system_content = _build_system_message(input_data.recipient, input_data.scene)
    user_content = _build_user_message(input_data)

    messages = [
        PromptMessage(role="system", content=system_content),
        PromptMessage(role="user", content=user_content),
    ]

    evaluation_notes = {
        "min_cases": 10,
        "pass_threshold": {
            "any_dimension_min": 3,
            "key_cases_avg_min": 4,
            "key_cases": [1, 2, 5],  # lover+miss, lover+sorry, family+sorry
        },
        "banned_patterns": [
            "逼迫对方回应",
            "PUA",
            "道德绑架",
            "威胁",
            "过度承诺",
            "医疗诊断式",
            "说教",
            "你必须",
            "你应该",
            "apiKey",
            "coreProfileId",
        ],
    }

    return PromptContract(
        version=CONTRACT_VERSION,
        messages=messages,
        expected_json_schema=EXPECTED_JSON_SCHEMA,
        evaluation_notes=evaluation_notes,
    )


# ── Offline eval cases accessor ────────────────────────────────────────────────

def build_offline_eval_cases() -> list[dict]:
    """Return the 10 offline eval cases for LLM output assessment."""
    return list(OFFLINE_EVAL_CASES)


# ── Static validation ──────────────────────────────────────────────────────────

def validate_prompt_contract_static(contract: PromptContract) -> list[str]:
    """
    Statically validate a PromptContract without calling any LLM.

    Returns a list of error strings. Empty list means passed.
    """
    errors = []

    if not contract.messages:
        errors.append("messages must not be empty")

    has_system = any(m.role == "system" for m in contract.messages)
    has_user = any(m.role == "user" for m in contract.messages)
    if not has_system:
        errors.append("messages must contain a system message")
    if not has_user:
        errors.append("messages must contain a user message")

    # Check JSON output requirement
    json_required = False
    for msg in contract.messages:
        content_lower = msg.content.lower()
        if "json" in content_lower or "输出" in content_lower:
            if "必须输出" in content_lower or "must output" in content_lower or \
               "纯 json" in content_lower or "pure json" in content_lower or \
               "strict json" in content_lower:
                json_required = True
                break
    if not json_required:
        errors.append("prompt should explicitly require JSON output format")

    # Check style coverage
    full_content = " ".join(m.content for m in contract.messages)
    for style in ("restrained", "gentle", "sincere"):
        if style not in full_content:
            errors.append(f"prompt must mention style: {style}")

    # Check recipient in user message
    user_msg = next((m.content for m in contract.messages if m.role == "user"), "")
    if "recipient" not in user_msg.lower():
        errors.append("user message must contain recipient field")

    # Check scene in user message
    if "scene" not in user_msg.lower():
        errors.append("user message must contain scene field")

    # Check raw_text in user message
    if "raw_text" not in user_msg.lower() and "用户想说的话" not in user_msg:
        errors.append("user message must contain raw_text")

    # Check no forbidden fields used as actual values (not in safety rule context)
    # We check that the raw output schema doesn't mention them
    schema_str = str(contract.expected_json_schema).lower()
    forbidden_output_fields = ("apikey", "coreprofileid", "providerrawresponse", "rawresponse")
    for f in forbidden_output_fields:
        if f in schema_str:
            errors.append(f"output schema must not contain forbidden field: {f}")

    return errors

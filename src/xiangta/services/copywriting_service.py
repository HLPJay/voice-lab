"""
CopywritingService — 生成文案建议。

B5-1 版本：基于模板，不调用 LLM / 外部 API。
输入：recipient, scene, raw_text
输出：summary + intent + 3 条 style 建议（restrained / gentle / sincere）
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

_SCENE_SUMMARY = {
    "miss":    "表达想念与牵挂",
    "sorry":   "传递歉意与在意",
    "thanks":  "表达感谢与珍惜",
    "comfort": "传递陪伴与关怀",
    "night":   "送一声晚安，传递温柔",
}

_SCENE_INTENT = {
    "miss":    "让对方感受到你的挂念，不给压力，但传递真实情绪",
    "sorry":   "真诚道歉，让对方感受到你的在意和改变的意愿",
    "thanks":  "表达感激，让对方知道你的心意与珍惜",
    "comfort": "给对方安慰与支撑，传递陪伴感",
    "night":   "结束一天时，用温柔的方式说声晚安",
}

# (scene, style) → (opener, closer, fitsFor)
_TEMPLATES: dict[tuple[str, str], tuple[str, str, str]] = {
    ("miss",    "restrained"): ("",             "。想了你一下。",                         "少修饰，保留原意，不给对方压力"),
    ("miss",    "gentle"):     ("有些挂念你，", "，悄悄想了一会儿。",                     "更温柔，适合发给亲密对象"),
    ("miss",    "sincere"):    ("想认真告诉你：","。这是真话，说出来感觉好一些。",         "直接真诚，表达重点更清楚"),
    ("sorry",   "restrained"): ("",             "。想和你说一声，对不起。",               "少修饰，保留原意，不给对方压力"),
    ("sorry",   "gentle"):     ("一直想和你说，","，希望你能感受到我的在意。",            "更温柔，适合发给亲密对象"),
    ("sorry",   "sincere"):    ("认真地说：",   "。我真的很抱歉，希望你能接受这份心意。", "直接真诚，表达重点更清楚"),
    ("thanks",  "restrained"): ("",             "。谢谢你。",                             "少修饰，保留原意，不给对方压力"),
    ("thanks",  "gentle"):     ("一直很感谢你，","，你让我觉得很温暖。",                  "更温柔，适合发给亲密对象"),
    ("thanks",  "sincere"):    ("想认真地谢谢你：","。你的好意我都记得，真心感谢。",       "直接真诚，表达重点更清楚"),
    ("comfort", "restrained"): ("",             "。我在这里，随时找我。",                 "少修饰，保留原意，不给对方压力"),
    ("comfort", "gentle"):     ("看到你这样，我有些担心——","，不管怎样，我陪着你。",     "更温柔，适合发给亲密对象"),
    ("comfort", "sincere"):    ("想直接告诉你：","。你不是一个人，我一直在。",            "直接真诚，表达重点更清楚"),
    ("night",   "restrained"): ("",             "。晚安，好好休息。",                     "少修饰，保留原意，不给对方压力"),
    ("night",   "gentle"):     ("夜深了，想到你，","，愿你睡个好觉。",                    "更温柔，适合发给亲密对象"),
    ("night",   "sincere"):    ("今晚想和你说：","。晚安，明天又是新的一天。",            "直接真诚，表达重点更清楚"),
}

_DEFAULT_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "restrained": ("",           "。",                         "少修饰，保留原意，不给对方压力"),
    "gentle":     ("想告诉你，", "，希望你能感受到我的心意。", "更温柔，适合发给亲密对象"),
    "sincere":    ("认真说：",   "。这是我的真心话。",         "直接真诚，表达重点更清楚"),
}

_STYLE_LABELS = {
    "restrained": "克制版",
    "gentle":     "温柔版",
    "sincere":    "真诚版",
}

_STYLES_ORDER = ["restrained", "gentle", "sincere"]


class CopywritingService:

    def __init__(self, gateway: "VoiceLabGateway | None" = None) -> None:
        self._gw = gateway

    async def generate_suggestions(
        self,
        *,
        recipient: str,
        scene: str,
        raw_text: str,
    ) -> dict:
        """生成 3 条模板文案建议（restrained / gentle / sincere）。不调用 LLM。"""
        raw_text = raw_text.strip()
        if not raw_text:
            raise ValueError("raw_text 不能为空")

        summary = _SCENE_SUMMARY.get(scene, "表达你的心意")
        intent  = _SCENE_INTENT.get(scene, "把原文整理成更合适的表达方式")

        suggestions = []
        for style in _STYLES_ORDER:
            opener, closer, fits_for = _TEMPLATES.get(
                (scene, style), _DEFAULT_TEMPLATES[style]
            )
            text = f"{opener}{raw_text}{closer}"
            suggestions.append({
                "style":      style,
                "styleLabel": _STYLE_LABELS[style],
                "fitsFor":    fits_for,
                "text":       text,
                "charCount":  len(text),
            })

        return {
            "summary":     summary,
            "intent":      intent,
            "suggestions": suggestions,
        }

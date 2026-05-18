"""
Copywriting Gateway — abstract LLM provider interface for copywriting suggestions.

C8 MVP:
- TemplateCopywritingGateway: uses built-in template logic
- FakeLlmCopywritingGateway: returns predictable fake LLM-style suggestions

No real API calls, no API key access.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CopywritingRequest:
    recipient: str
    scene: str
    raw_text: str
    max_suggestions: int = 3


@dataclass(frozen=True)
class CopywritingSuggestion:
    style: str
    style_label: str
    fits_for: str
    text: str


@dataclass(frozen=True)
class CopywritingResult:
    summary: str
    intent: str
    suggestions: list[CopywritingSuggestion]
    source: str = "template"  # "template" | "fake_llm" | "minimax"
    degraded: bool = False    # True when LLM failed and template was used as fallback
    latency_ms: int | None = None  # Milliseconds for LLM call (template/fake_llm = None)


class CopywritingGateway(Protocol):
    async def generate(self, request: CopywritingRequest) -> CopywritingResult:
        ...


# ── Text normalization ─────────────────────────────────────────────────────────

def normalize_copy_text(raw_text: str | None) -> str:
    """
    Normalize Chinese emotional copy text:

    1. Clean duplicate punctuation:
       ``。。`` → ``。``，``！！`` → ``！``，``？？`` → ``？``，``，，`` → ``，``

    2. Add readable paragraph breaks:
       Split by full-width sentence-ending punctuation (。！？).
       Group 1-2 sentences per paragraph, max 3 paragraphs.
       Empty lines become single newlines.
    """
    if not raw_text:
        return raw_text or ""

    # Step 1: clean duplicate punctuation
    text = raw_text
    text = text.replace("、、", "、")   # 、、
    text = text.replace("，，", "，")   # ，， (fullwidth)
    text = text.replace("。。", "。")   # 。。
    text = text.replace("！！", "！")   # ！！ (fullwidth)
    text = text.replace("？？", "？")   # ？？ (fullwidth)
    text = text.replace("。。", "。")
    text = text.replace("！！", "！")
    text = text.replace("？？", "？")
    text = text.replace("，，", "，")

    # Step 2: paragraph splitting
    # Split into sentences by 。！？ (keeping the punctuation)
    sentences = _split_into_sentences(text)

    # Group into paragraphs: 1-2 sentences each, max 3 paragraphs
    paragraphs = []
    for i in range(0, len(sentences), 2):
        chunk = sentences[i : i + 2]
        paragraphs.append("".join(chunk))

    # Trim and limit to 3 paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    if len(paragraphs) > 3:
        paragraphs = paragraphs[:3]

    return "\n".join(paragraphs)


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences preserving the ending punctuation."""
    result: list[str] = []
    current = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "。！？":
            current += ch
            result.append(current)
            current = ""
        elif ch in "\n\r":
            if current:
                result.append(current)
                current = ""
        else:
            current += ch
        i += 1
    if current:
        result.append(current)
    return result


# ── Template implementation ───────────────────────────────────────────────────

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

_TEMPLATES: dict[tuple[str, str], tuple[str, str, str]] = {
    ("miss",    "restrained"): ("",             "\n\n想了你一下。",                       "少修饰，保留原意，不给对方压力"),
    ("miss",    "gentle"):     ("有些挂念你，", "\n\n悄悄想了一会儿。",                   "更温柔，适合发给亲密对象"),
    ("miss",    "sincere"):    ("想认真告诉你：","\n\n这是真话，说出来感觉好一些。",       "直接真诚，表达重点更清楚"),
    ("sorry",   "restrained"): ("",             "\n\n想和你说一声，对不起。",             "少修饰，保留原意，不给对方压力"),
    ("sorry",   "gentle"):     ("一直想和你说，","\n\n希望你能感受到我的在意。",          "更温柔，适合发给亲密对象"),
    ("sorry",   "sincere"):    ("认真地说：",   "\n\n我真的很抱歉，希望你能接受这份心意。", "直接真诚，表达重点更清楚"),
    ("thanks",  "restrained"): ("",             "\n\n谢谢你。",                           "少修饰，保留原意，不给对方压力"),
    ("thanks",  "gentle"):     ("一直很感谢你，","\n\n你让我觉得很温暖。",                "更温柔，适合发给亲密对象"),
    ("thanks",  "sincere"):    ("想认真地谢谢你：","\n\n你的好意我都记得，真心感谢。",     "直接真诚，表达重点更清楚"),
    ("comfort", "restrained"): ("",             "\n\n我在这里，随时找我。",               "少修饰，保留原意，不给对方压力"),
    ("comfort", "gentle"):     ("看到你这样，我有些担心——","\n\n不管怎样，我陪着你。",   "更温柔，适合发给亲密对象"),
    ("comfort", "sincere"):    ("想直接告诉你：","\n\n你不是一个人，我一直在。",          "直接真诚，表达重点更清楚"),
    ("night",   "restrained"): ("",             "\n\n晚安，好好休息。",                   "少修饰，保留原意，不给对方压力"),
    ("night",   "gentle"):     ("夜深了，想到你，","\n\n愿你睡个好觉。",                  "更温柔，适合发给亲密对象"),
    ("night",   "sincere"):    ("今晚想和你说：","\n\n晚安，明天又是新的一天。",          "直接真诚，表达重点更清楚"),
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

_TERMINAL_PUNCT = "。！？!?…"
_ANY_PUNCT = "。！？!?…，、；："


def _join_template_text(opener: str, raw_text: str, closer: str) -> str:
    body = raw_text.strip()
    if opener:
        body = f"{opener}{body}"
    if not closer:
        return body
    if closer.startswith("\n"):
        if body.endswith(tuple(_TERMINAL_PUNCT)):
            return f"{body}{closer}"
        return f"{body}。{closer}"

    leading = closer[0]
    tail = closer[1:] if leading in _ANY_PUNCT else closer

    if leading == "。":
        if body.endswith(tuple(_TERMINAL_PUNCT)):
            return f"{body}{tail}"
        return f"{body}{closer}"

    if leading == "，":
        if body.endswith(tuple(_TERMINAL_PUNCT)):
            return f"{body}{tail}"
        return f"{body}{closer}"

    return f"{body}{closer}"


class TemplateCopywritingGateway:
    async def generate(self, request: CopywritingRequest) -> CopywritingResult:
        summary = _SCENE_SUMMARY.get(request.scene, "表达你的心意")
        intent  = _SCENE_INTENT.get(request.scene, "把原文整理成更合适的表达方式")

        suggestions = []
        for style in _STYLES_ORDER:
            opener, closer, fits_for = _TEMPLATES.get(
                (request.scene, style), _DEFAULT_TEMPLATES[style]
            )
            text = _join_template_text(opener, request.raw_text, closer)
            suggestions.append(CopywritingSuggestion(
                style=style,
                style_label=_STYLE_LABELS[style],
                fits_for=fits_for,
                text=text,
            ))

        return CopywritingResult(
            summary=summary,
            intent=intent,
            suggestions=suggestions,
            source="template",
        )


# ── Fake LLM implementation ────────────────────────────────────────────────────

_FAKE_LLM_STYLE_FORMATS = {
    "restrained": "我想把这句话轻轻说给你听：{raw_text}",
    "gentle":     "有些话想慢慢告诉你：{raw_text}。愿你听见我的在意。",
    "sincere":    "认真说：{raw_text}。这是我现在最真实的心情。",
}


class FakeLlmCopywritingGateway:
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    async def generate(self, request: CopywritingRequest) -> CopywritingResult:
        if self._should_fail:
            raise RuntimeError("fake LLM unavailable")

        suggestions = []
        for style in _STYLES_ORDER:
            text_template = _FAKE_LLM_STYLE_FORMATS[style]
            text = text_template.format(raw_text=request.raw_text)
            suggestions.append(CopywritingSuggestion(
                style=style,
                style_label=_STYLE_LABELS[style],
                fits_for="AI 整理，保持原意，更适合发送",
                text=text,
            ))

        return CopywritingResult(
            summary="AI 整理你的表达",
            intent="在保留原意的基础上，生成更适合发送的情绪文案",
            suggestions=suggestions,
            source="fake_llm",
        )

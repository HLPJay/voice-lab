"""
Copywriting Service — 调用 LLM 生成文案建议。

输入：recipient, scene, raw_text
输出：SuggestionsData（summary + intent + 3 条 style 建议）

LLM 调用通过 voice_lab_gateway.generate_llm_text()，
Prompt 模板从 prompts/<scene>.md 读取。
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class CopywritingService:

    def __init__(self, gateway: "VoiceLabGateway") -> None:
        self._gw = gateway

    async def generate_suggestions(
        self,
        *,
        recipient: str,
        scene: str,
        raw_text: str,
    ) -> dict:
        """
        Returns:
            {
              "summary": str,
              "intent": str,
              "suggestions": [
                {"style": "restrained", "styleLabel": "克制版", "fitsFor": ..., "text": ..., "charCount": int},
                {"style": "gentle", ...},
                {"style": "sincere", ...},
              ]
            }
        """
        # TODO(P17-A2):
        # 1. 读取 prompts/<scene>.md 作为 system prompt 模板
        # 2. 将 recipient, raw_text 填入模板
        # 3. 调用 self._gw.generate_llm_text(prompt=..., max_tokens=600)
        # 4. 解析 LLM 输出（JSON 或结构化文本）为 SuggestionsData
        raise NotImplementedError

    def _load_prompt(self, scene: str) -> str:
        # TODO(P17-A2): 读取并缓存 prompt 模板
        path = _PROMPTS_DIR / f"{scene}.md"
        return path.read_text(encoding="utf-8")

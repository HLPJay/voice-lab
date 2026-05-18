"""
CopywritingService — 生成文案建议。

B5-1 版本：基于模板，不调用 LLM / 外部 API。
C8 版本：支持可选 CopywritingGateway（fake LLM）+ template fallback。

输入：recipient, scene, raw_text
输出：summary + intent + 3 条 style 建议（restrained / gentle / sincere）
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.xiangta.services.copywriting_gateway import CopywritingGateway


class CopywritingService:

    def __init__(
        self,
        gateway: "CopywritingGateway | None" = None,
        fallback_to_template: bool = True,
    ) -> None:
        self._gateway = gateway
        self._template_gateway = None  # lazy
        self._fallback_to_template = fallback_to_template

    def _get_template_gateway(self):
        """Lazy-load template gateway to avoid circular import at construction."""
        if self._template_gateway is None:
            from src.xiangta.services.copywriting_gateway import TemplateCopywritingGateway
            self._template_gateway = TemplateCopywritingGateway()
        return self._template_gateway

    def _to_dict(self, gateway_result) -> dict:
        """Convert CopywritingResult to API dict (camelCase)."""
        return {
            "summary": gateway_result.summary,
            "intent":  gateway_result.intent,
            "suggestions": [
                {
                    "style":      s.style,
                    "styleLabel": s.style_label,
                    "fitsFor":    s.fits_for,
                    "text":       s.text,
                    "charCount":  len(s.text),
                }
                for s in gateway_result.suggestions
            ],
        }

    async def generate_suggestions(
        self,
        *,
        recipient: str,
        scene: str,
        raw_text: str,
    ) -> dict:
        """
        Generate 3 style suggestions (restrained / gentle / sincere).

        If gateway is set, try gateway.generate() first.
        On gateway failure with fallback=True, fall back to template.
        On gateway failure with fallback=False, raise LlmFailedError.
        """
        raw_text = raw_text.strip()
        if not raw_text:
            raise ValueError("raw_text 不能为空")

        from src.xiangta.services.copywriting_gateway import CopywritingRequest
        from src.xiangta.services.error_translator import LlmFailedError

        request = CopywritingRequest(
            recipient=recipient,
            scene=scene,
            raw_text=raw_text,
        )

        if self._gateway is None:
            tg = self._get_template_gateway()
            result = await tg.generate(request)
            return self._to_dict(result)

        try:
            result = await self._gateway.generate(request)
            return self._to_dict(result)
        except Exception:
            if self._fallback_to_template:
                tg = self._get_template_gateway()
                fallback_result = await tg.generate(request)
                return self._to_dict(fallback_result)
            raise LlmFailedError()

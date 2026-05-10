import re

from app.core.errors import ValidationError


PAUSE_RE = re.compile(r"<#\d{1,2}(?:\.\d{1,2})?#>")


class TextPreprocessService:
    def preprocess(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            raise ValidationError("Text cannot be empty")
        if len(normalized) > 9500:
            raise ValidationError("Text is too long for sync render", "Use async longform TTS for text over 9500 characters")
        if PAUSE_RE.search(normalized):
            return normalized
        processed = re.sub(r"([。！？!?])", r"\1<#0.5#>", normalized)
        return re.sub(r"(<#\d+(?:\.\d+)?#>){2,}", r"\1", processed).rstrip()

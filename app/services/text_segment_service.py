import re


class TextSegmentService:
    def segment(
        self, text: str, strategy: str = "auto", max_chars: int = 2000
    ) -> list[str]:
        """将长文本拆分为多个段落，每段不超过 max_chars 字符。"""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        text = text.strip()
        if strategy == "paragraph":
            return self._segment_paragraph(text, max_chars)
        elif strategy == "sentence":
            return self._segment_sentence(text, max_chars)
        elif strategy == "auto":
            return self._segment_auto(text, max_chars)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _split_by_paragraphs(self, text: str) -> list[str]:
        """Split by double newlines."""
        parts = re.split(r'\n\n+', text)
        return [p.strip() for p in parts if p.strip()]

    def _split_sentences(self, text: str) -> list[str]:
        """Split by Chinese and English sentence endings."""
        parts = re.split(r'([。！？!?\n]+)', text)
        sentences = []
        current = ""
        for part in parts:
            if re.match(r'^[。！？!?\n]+$', part):
                current += part
            else:
                if current:
                    sentences.append(current.strip())
                current = part
        if current.strip():
            sentences.append(current.strip())
        return [s for s in sentences if s]

    def _split_by_comma(self, text: str, max_chars: int) -> list[str]:
        """Split by comma/semicolon when even sentences are too long."""
        parts = re.split(r'([，,；;]+)', text)
        segments = []
        current = ""
        for part in parts:
            if re.match(r'^[，,；;]+$', part):
                current += part
            else:
                if len(current) + len(part) > max_chars and current:
                    segments.append(current.strip())
                    current = part
                else:
                    current += part
        if current.strip():
            segments.append(current.strip())
        return [s for s in segments if s]

    def _segment_paragraph(self, text: str, max_chars: int) -> list[str]:
        paragraphs = self._split_by_paragraphs(text)
        result = []
        for para in paragraphs:
            if len(para) <= max_chars:
                result.append(para)
            else:
                sentences = self._split_sentences(para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_chars:
                        current = (current + "\n" + sent).strip()
                    else:
                        if current:
                            result.append(current)
                        if len(sent) > max_chars:
                            result.extend(self._split_by_comma(sent, max_chars))
                            current = ""
                        else:
                            current = sent
                if current:
                    result.append(current)
        return result

    def _segment_sentence(self, text: str, max_chars: int) -> list[str]:
        sentences = self._split_sentences(text)
        result = []
        current = ""
        for sent in sentences:
            if len(sent) <= max_chars:
                if len(current) + len(sent) + 1 <= max_chars:
                    current = (current + "\n" + sent).strip()
                else:
                    if current:
                        result.append(current)
                    current = sent
            else:
                if current:
                    result.append(current)
                result.extend(self._split_by_comma(sent))
                current = ""
        if current:
            result.append(current)
        return result

    def _segment_auto(self, text: str, max_chars: int) -> list[str]:
        paragraphs = self._split_by_paragraphs(text)
        result = []
        for para in paragraphs:
            if len(para) <= max_chars:
                result.append(para)
            else:
                sentences = self._split_sentences(para)
                current = ""
                for sent in sentences:
                    if len(sent) <= max_chars:
                        if len(current) + len(sent) + 1 <= max_chars:
                            current = (current + "\n" + sent).strip()
                        else:
                            if current:
                                result.append(current)
                            current = sent
                    else:
                        if current:
                            result.append(current)
                        result.extend(self._split_by_comma(sent, max_chars))
                        current = ""
                if current:
                    result.append(current)
        return result

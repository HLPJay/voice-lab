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
        elif strategy == "line":
            return self._segment_line(text, max_chars)
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

    def _hard_split(self, text: str, max_chars: int) -> list[str]:
        """Pure length-based split as last resort when no punctuation available."""
        return [text[i : i + max_chars] for i in range(0, len(text), max_chars) if text[i : i + max_chars]]

    def _append_with_hard_limit(
        self, result: list[str], segment: str, max_chars: int
    ) -> None:
        """Append segment, hard-splitting if it exceeds max_chars."""
        segment = segment.strip()
        if not segment:
            return
        if len(segment) <= max_chars:
            result.append(segment)
        else:
            result.extend(self._hard_split(segment, max_chars))

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
                    self._append_with_hard_limit(segments, current, max_chars)
                    current = part
                else:
                    current += part
        if current.strip():
            self._append_with_hard_limit(segments, current, max_chars)
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
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(sent) <= max_chars:
                result.append(sent)
            else:
                result.extend(self._split_by_comma(sent, max_chars))
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

    def _split_by_lines(self, text: str) -> list[str]:
        """Split by single newline, stripping and removing empty lines."""
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _segment_line(self, text: str, max_chars: int) -> list[str]:
        """Each non-empty line becomes an independent segment; long lines are split by sentences."""
        lines = self._split_by_lines(text)
        result = []
        for line in lines:
            if len(line) <= max_chars:
                result.append(line)
            else:
                result.extend(self._segment_sentence(line, max_chars))
        return result

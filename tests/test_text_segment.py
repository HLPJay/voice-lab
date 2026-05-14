import pytest

from app.services.text_segment_service import TextSegmentService


@pytest.fixture
def service():
    return TextSegmentService()


def test_segment_auto_short_text(service):
    text = "这是一段短文本。"
    result = service.segment(text)
    assert len(result) == 1
    assert result[0] == text


def test_segment_auto_by_paragraph(service):
    text = "第一段文字。\n\n第二段文字。"
    result = service.segment(text)
    assert len(result) == 2
    assert "第一段文字" in result[0]
    assert "第二段文字" in result[1]


def test_segment_auto_long_paragraph_splits(service):
    long_text = "这是一段测试文字。" * 300
    text = "开头段。" + long_text + "结尾段。"
    result = service.segment(text, max_chars=2000)
    assert len(result) >= 2
    for seg in result:
        assert len(seg) <= 2000


def test_segment_paragraph_strategy(service):
    text = "第一段\n\n第二段\n\n第三段"
    result = service.segment(text, strategy="paragraph")
    assert len(result) == 3


def test_segment_sentence_strategy(service):
    text = "第一句！第二句？第三句。"
    result = service.segment(text, strategy="sentence")
    assert len(result) >= 1
    joined = "".join(result)
    normalized = "".join(text.split())
    assert "".join(joined.split()) == normalized


def test_segment_preserves_order(service):
    text = "段落一的内容。\n\n段落二的内容。\n\n段落三的内容。"
    result = service.segment(text)
    full = "".join(result)
    assert "段落一的内容" in full
    assert "段落二的内容" in full
    assert "段落三的内容" in full
    first_pos = full.find("段落一的内容")
    second_pos = full.find("段落二的内容")
    third_pos = full.find("段落三的内容")
    assert first_pos < second_pos < third_pos


def test_segment_max_chars_respected(service):
    text = "句子。" * 500
    result = service.segment(text, max_chars=2000)
    for seg in result:
        assert len(seg) <= 2000


def test_segment_empty_text_raises(service):
    with pytest.raises(ValueError, match="cannot be empty"):
        service.segment("")
    with pytest.raises(ValueError, match="cannot be empty"):
        service.segment("   ")


def test_segment_sentence_long_sentence_splits_by_comma(service):
    """strategy=sentence, single sentence exceeds max_chars → split by comma."""
    text = "这是一个很长的片段，" * 200  # ~2000 chars, far exceeds max_chars=100
    result = service.segment(text, strategy="sentence", max_chars=100)

    assert len(result) > 1
    for seg in result:
        assert len(seg) <= 100


def test_segment_line_each_line_is_segment(service):
    """Each non-empty line becomes an independent segment."""
    text = "第一条\n第二条\n第三条"
    result = service.segment(text, strategy="line")
    assert len(result) == 3
    assert result == ["第一条", "第二条", "第三条"]


def test_segment_line_ignores_empty_lines(service):
    """Empty lines are stripped and do not create segments."""
    text = "第一条\n\n第二条\n\n\n第三条"
    result = service.segment(text, strategy="line")
    assert len(result) == 3
    assert result == ["第一条", "第二条", "第三条"]


def test_segment_line_does_not_merge_short_lines(service):
    """Short lines are not merged together."""
    text = "短1\n短2"
    result = service.segment(text, strategy="line", max_chars=2000)
    assert len(result) == 2
    assert result == ["短1", "短2"]


def test_segment_line_long_line_is_split(service):
    """A single line exceeding max_chars is further split by sentences."""
    text = "第一句！第二句？第三句。" * 50  # each ~600 chars, far exceeds max_chars=100
    result = service.segment(text, strategy="line", max_chars=100)
    assert len(result) > 1
    for seg in result:
        assert len(seg) <= 100


def test_segment_line_unknown_strategy_raises(service):
    """Unknown strategy raises ValueError."""
    with pytest.raises(ValueError, match="Unknown strategy: nonexistent"):
        service.segment("some text", strategy="nonexistent")


def test_segment_line_long_text_without_punctuation_is_hard_split(service):
    """Line strategy: unpunctuated long text is hard-split to respect max_chars."""
    text = "a" * 251
    result = service.segment(text, strategy="line", max_chars=100)
    assert len(result) == 3
    assert all(len(seg) <= 100 for seg in result)


def test_segment_sentence_long_text_without_punctuation_is_hard_split(service):
    """Sentence strategy: unpunctuated long text is hard-split to respect max_chars."""
    text = "a" * 251
    result = service.segment(text, strategy="sentence", max_chars=100)
    assert len(result) == 3
    assert all(len(seg) <= 100 for seg in result)


def test_segment_paragraph_long_text_without_punctuation_is_hard_split(service):
    """Paragraph strategy: unpunctuated long text is hard-split to respect max_chars."""
    text = "a" * 251
    result = service.segment(text, strategy="paragraph", max_chars=100)
    assert len(result) == 3
    assert all(len(seg) <= 100 for seg in result)


def test_segment_auto_long_text_without_punctuation_is_hard_split(service):
    """Auto strategy: unpunctuated long text is hard-split to respect max_chars."""
    text = "a" * 251
    result = service.segment(text, strategy="auto", max_chars=100)
    assert len(result) == 3
    assert all(len(seg) <= 100 for seg in result)

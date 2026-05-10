import pytest

from app.services.text_preprocess_service import TextPreprocessService


def test_preprocess_inserts_pause():
    service = TextPreprocessService()
    text = "你好，世界！这是一段测试文本。"
    result = service.preprocess(text)
    assert "<#" in result
    assert "！" in result or "！" in text


def test_preprocess_preserves_existing_pause():
    service = TextPreprocessService()
    text = "你好<#0.5#>世界"
    result = service.preprocess(text)
    assert "<#0.5#>" in result


def test_preprocess_empty_text_raises():
    service = TextPreprocessService()
    with pytest.raises(Exception):
        service.preprocess("")


def test_preprocess_too_long_raises():
    service = TextPreprocessService()
    long_text = "好" * 10000
    with pytest.raises(Exception):
        service.preprocess(long_text)

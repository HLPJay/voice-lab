import pytest
from pydantic import ValidationError

from app.domain.schemas import (
    LongtextBatchRequest,
    VoiceRenderRequest,
    VoiceVariantRenderRequest,
    VoiceCloneRequest,
    AsyncRenderRequest,
)


class TestSegmentStrategyLiteral:
    def test_longtext_batch_bad_strategy_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            LongtextBatchRequest(segment_strategy="bad_strategy")
        errors = exc_info.value.errors()
        assert any("segment_strategy" in str(e) or "Input should be" in str(e) for e in errors)

    def test_longtext_batch_valid_strategies(self):
        for strategy in ("auto", "paragraph", "sentence", "line"):
            req = LongtextBatchRequest(segment_strategy=strategy, text="hello")
            assert req.segment_strategy == strategy


class TestLongtextBatchTextMaxLength:
    def test_longtext_text_too_long_raises(self):
        with pytest.raises(ValidationError):
            LongtextBatchRequest(text="x" * 50001)

    def test_longtext_text_at_limit(self):
        req = LongtextBatchRequest(text="x" * 50000)
        assert len(req.text) == 50000


class TestVoiceRenderTextMaxLength:
    def test_voice_render_text_too_long_raises(self):
        with pytest.raises(ValidationError):
            VoiceRenderRequest(text="x" * 10001)

    def test_voice_render_text_at_limit(self):
        req = VoiceRenderRequest(text="x" * 10000)
        assert len(req.text) == 10000


class TestVoiceVariantTextMaxLength:
    def test_voice_variant_text_too_long_raises(self):
        with pytest.raises(ValidationError):
            VoiceVariantRenderRequest(text="x" * 10001)

    def test_voice_variant_text_at_limit(self):
        req = VoiceVariantRenderRequest(text="x" * 10000)
        assert len(req.text) == 10000


class TestAsyncRenderTextMaxLength:
    def test_async_render_text_too_long_raises(self):
        with pytest.raises(ValidationError):
            AsyncRenderRequest(text="x" * 50001)

    def test_async_render_text_at_limit(self):
        req = AsyncRenderRequest(text="x" * 50000)
        assert len(req.text) == 50000


class TestVoiceCloneFileIdPositive:
    def test_file_id_zero_raises(self):
        with pytest.raises(ValidationError):
            VoiceCloneRequest(voice_id="valid_voice_01", file_id=0)

    def test_file_id_negative_raises(self):
        with pytest.raises(ValidationError):
            VoiceCloneRequest(voice_id="valid_voice_01", file_id=-1)

    def test_file_id_positive_ok(self):
        req = VoiceCloneRequest(voice_id="valid_voice_01", file_id=1)
        assert req.file_id == 1

    def test_prompt_file_id_zero_raises(self):
        with pytest.raises(ValidationError):
            VoiceCloneRequest(voice_id="valid_voice_01", file_id=1, prompt_file_id=0)

    def test_prompt_file_id_negative_raises(self):
        with pytest.raises(ValidationError):
            VoiceCloneRequest(voice_id="valid_voice_01", file_id=1, prompt_file_id=-1)

    def test_prompt_file_id_none_ok(self):
        req = VoiceCloneRequest(voice_id="valid_voice_01", file_id=1, prompt_file_id=None)
        assert req.prompt_file_id is None

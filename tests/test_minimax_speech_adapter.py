import binascii
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter


def make_plan(output_format="hex"):
    return RenderPlan(
        id="plan_test",
        text="测试文本",
        processed_text="测试文本",
        profile_id="test_profile",
        provider="minimax",
        model="speech-2.8-hd",
        provider_voice_id="English_expressive_narrator",
        voice_params={"speed": 0.88, "emotion": "sad"},
        audio_params={"format": "mp3", "sample_rate": 32000, "bitrate": 128000, "channel": 1},
        subtitle=SubtitlePlan(enabled=True, type="sentence"),
        output_format=output_format,
        language_boost="auto",
    )


class FakeResponse:
    def __init__(self, json_data=None, content=b"", status_code=200):
        self._json = json_data
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class TestIsHexString:
    adapter = MiniMaxSpeechAdapter()

    def test_valid_hex_even_length(self):
        assert self.adapter._is_hex_string("48656c6c6f") is True

    def test_valid_hex_uppercase(self):
        assert self.adapter._is_hex_string("ABCD12") is True

    def test_invalid_odd_length(self):
        assert self.adapter._is_hex_string("48656c6") is False  # 7 chars, odd

    def test_invalid_non_hex_chars(self):
        assert self.adapter._is_hex_string("48656c6cxx") is False

    def test_invalid_empty_string(self):
        assert self.adapter._is_hex_string("") is False  # empty string not valid hex

    def test_invalid_not_string(self):
        assert self.adapter._is_hex_string(12345) is False
        assert self.adapter._is_hex_string(None) is False


class TestSaveAudioFromData:
    adapter = MiniMaxSpeechAdapter()

    @pytest.mark.asyncio
    async def test_audio_hex_valid(self):
        hex_data = "ffd2ff4f4e"  # even-length valid hex
        body = {"data": {"audio": hex_data}}
        data = body["data"]

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            path, fmt = await self.adapter._save_audio_from_data(
                data, "hex", {"format": "mp3"}, 30.0
            )
            assert path.exists()
            assert fmt == "mp3"
            assert path.read_bytes() == binascii.unhexlify(hex_data)
            mock_dl.assert_not_called()

    @pytest.mark.asyncio
    async def test_audio_url_downloaded(self):
        body = {"data": {"audio_url": "https://example.com/audio.mp3"}}
        data = body["data"]
        fake_content = b"fake audio bytes"

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            path, fmt = await self.adapter._save_audio_from_data(
                data, "hex", {"format": "mp3"}, 30.0
            )
            assert path.exists()
            assert path.read_bytes() == fake_content
            mock_dl.assert_called_once()

    @pytest.mark.asyncio
    async def test_audio_field_url_downloaded(self):
        data = {"audio": "https://example.com/audio.mp3"}
        fake_content = b"audio from data.audio url"

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            path, fmt = await self.adapter._save_audio_from_data(
                data, "hex", {"format": "mp3"}, 30.0
            )
            assert path.exists()
            assert path.read_bytes() == fake_content
            mock_dl.assert_called_once_with("https://example.com/audio.mp3", 30.0)

    @pytest.mark.asyncio
    async def test_output_format_url_prefers_audio_url(self):
        body = {"data": {"audio": "48656c6c6f", "audio_url": "https://example.com/audio.mp3"}}
        data = body["data"]
        fake_content = b"url audio"

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            path, fmt = await self.adapter._save_audio_from_data(
                data, "url", {"format": "mp3"}, 30.0
            )
            assert path.exists()
            assert path.read_bytes() == fake_content
            mock_dl.assert_called_once_with("https://example.com/audio.mp3", 30.0)

    @pytest.mark.asyncio
    async def test_audio_invalid_odd_length_raises(self):
        body = {"data": {"audio": "48656c6c6"}}
        data = body["data"]

        with pytest.raises(Exception) as exc_info:
            await self.adapter._save_audio_from_data(
                data, "hex", {"format": "mp3"}, 30.0
            )
        assert "No valid audio source" in str(exc_info.value) or "audio" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_no_audio_source_raises(self):
        body = {"data": {}}
        data = body["data"]

        with pytest.raises(Exception) as exc_info:
            await self.adapter._save_audio_from_data(
                data, "hex", {"format": "mp3"}, 30.0
            )
        assert "No valid audio source" in str(exc_info.value)


class TestExtractTimelineFromSubtitleFile:
    adapter = MiniMaxSpeechAdapter()

    @pytest.mark.asyncio
    async def test_subtitle_minimax_real_fields(self):
        """Real MiniMax field names: time_begin/time_end in milliseconds."""
        timeline_data = [{"text": "你好", "time_begin": 0, "time_end": 1500, "pronounce_text": "ni hao"}]
        timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
            timeline_data, 30.0
        )
        assert timeline[0]["text"] == "你好"
        assert timeline[0]["start"] == 0.0
        assert timeline[0]["end"] == 1.5
        assert "pronounce_text" not in timeline[0]
        assert "time_begin" not in timeline[0]

    @pytest.mark.asyncio
    async def test_subtitle_list(self):
        # start=0, end=1000ms → normalized to start=0.0, end=1.0 (seconds)
        timeline_data = [{"text": "hello", "start": 0, "end": 1000}]
        timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
            timeline_data, 30.0
        )
        assert timeline[0]["text"] == "hello"
        assert timeline[0]["start"] == 0.0
        assert timeline[0]["end"] == 1.0
        assert metadata == {}

    @pytest.mark.asyncio
    async def test_subtitle_url_json_list(self):
        # start=0, end=1000ms → normalized to start=0.0, end=1.0 (seconds)
        fake_timeline = [{"text": "hello", "start": 0, "end": 1000}]
        fake_content = json.dumps(fake_timeline).encode("utf-8")

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
                "https://example.com/subtitles.json", 30.0
            )
            assert timeline[0]["text"] == "hello"
            assert timeline[0]["start"] == 0.0
            assert timeline[0]["end"] == 1.0
            assert metadata.get("subtitle_file_url_downloaded") is True

    @pytest.mark.asyncio
    async def test_subtitle_url_json_dict_sentences(self):
        fake_data = {
            "sentences": [
                {"text": "hello world", "start": 0, "end": 1500},
                {"text": "goodbye", "start": 1500, "end": 2500},
            ]
        }
        fake_content = json.dumps(fake_data).encode("utf-8")

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
                "https://example.com/subtitles.json", 30.0
            )
            assert len(timeline) == 2
            assert timeline[0]["text"] == "hello world"
            assert metadata.get("subtitle_file_url_downloaded") is True

    @pytest.mark.asyncio
    async def test_subtitle_url_json_dict_items(self):
        fake_data = {
            "items": [{"text": "item1", "start": 0, "end": 500}]
        }
        fake_content = json.dumps(fake_data).encode("utf-8")

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
                "https://example.com/subtitles.json", 30.0
            )
            assert len(timeline) == 1
            assert timeline[0]["text"] == "item1"

    @pytest.mark.asyncio
    async def test_subtitle_url_not_json(self):
        fake_content = b"not json content"

        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
                "https://example.com/subtitles.txt", 30.0
            )
            assert timeline == []
            assert metadata.get("subtitle_file_url_downloaded") is True
            assert metadata.get("subtitle_file_parse_failed") is True

    @pytest.mark.asyncio
    async def test_subtitle_url_download_fails(self):
        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.side_effect = Exception("network error")
            timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
                "https://example.com/subtitles.json", 30.0
            )
            assert timeline == []
            assert metadata.get("subtitle_file_url_downloaded") is True
            assert metadata.get("subtitle_file_parse_failed") is True

    @pytest.mark.asyncio
    async def test_subtitle_none(self):
        timeline, metadata = await self.adapter._extract_timeline_from_subtitle_file(
            None, 30.0
        )
        assert timeline == []
        assert metadata == {}


class TestRenderSync:
    adapter = MiniMaxSpeechAdapter()

    @pytest.mark.asyncio
    async def test_hex_audio_saved(self):
        hex_data = "48656c6c6f"  # "Hello"
        plan = make_plan("hex")
        body = {
            "trace_id": "trace_abc123",
            "data": {"audio": hex_data},
            "extra_info": {"audio_length": 1000, "usage_characters": 4},
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = FakeResponse(body)
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            result = await self.adapter.render_sync(plan)

            assert result.trace_id == "trace_abc123"
            assert result.duration_ms == 1000
            assert result.usage_characters == 4
            assert result.response_json == body
            # audio_path should exist as a file
            from pathlib import Path
            assert Path(result.audio_path).exists()

    @pytest.mark.asyncio
    async def test_url_output_format_prefers_audio_url(self):
        plan = make_plan("url")
        fake_audio = b"fake audio from url"
        body = {
            "trace_id": "trace_url",
            "data": {
                "audio": "48656c6c6f",  # hex also present but should be ignored for url mode
                "audio_url": "https://example.com/audio.mp3",
            },
            "extra_info": {"audio_length": 500},
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = FakeResponse(body)
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
                mock_dl.return_value = fake_audio
                result = await self.adapter.render_sync(plan)

                # Should have downloaded from audio_url, not hex
                mock_dl.assert_called_once_with("https://example.com/audio.mp3", 120.0)
                from pathlib import Path
                assert Path(result.audio_path).exists()
                assert Path(result.audio_path).read_bytes() == fake_audio

    @pytest.mark.asyncio
    async def test_subtitle_file_url_downloaded_and_parsed(self):
        plan = make_plan("hex")
        fake_timeline = [{"text": "hello", "start": 0, "end": 1000}]
        body = {
            "trace_id": "trace_sub",
            "data": {
                "audio": "48656c6c6f",
                "subtitle_file": "https://example.com/subs.json",
            },
            "extra_info": {"audio_length": 1000},
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = FakeResponse(body)
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
                mock_dl.return_value = json.dumps(fake_timeline).encode("utf-8")
                result = await self.adapter.render_sync(plan)

                assert len(result.timeline) == 1
                assert result.timeline[0]["text"] == "hello"
                assert result.metadata.get("subtitle_file_url_downloaded") is True

    @pytest.mark.asyncio
    async def test_inline_subtitle_list_is_preserved(self):
        plan = make_plan("hex")
        timeline = [{"text": "inline", "start": 0, "end": 1000}]
        body = {
            "trace_id": "trace_inline_sub",
            "data": {
                "audio": "48656c6c6f",
                "subtitle": timeline,
            },
            "extra_info": {"audio_length": 1000},
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = FakeResponse(body)
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            result = await self.adapter.render_sync(plan)

            # Normalized: start/end converted from ms to seconds
            assert result.timeline[0]["text"] == "inline"
            assert result.timeline[0]["start"] == 0.0
            assert result.timeline[0]["end"] == 1.0

    @pytest.mark.asyncio
    async def test_invalid_hex_raises_provider_error(self):
        plan = make_plan("hex")
        body = {
            "trace_id": "trace_err",
            "data": {"audio": "48656c6"},  # 7 chars, odd-length -> invalid hex
            "extra_info": {},
            "base_resp": {"status_code": 0, "status_msg": "success"},
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = FakeResponse(body)
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            MockClient.return_value = mock_instance

            from app.core.errors import ProviderError
            with pytest.raises(ProviderError) as exc_info:
                await self.adapter.render_sync(plan)
            assert "MiniMax audio save failed" in str(exc_info.value.message)


class TestParseRenderResponse:
    """Tests for _save_audio_from_data covering output_format=url response combinations."""

    adapter = MiniMaxSpeechAdapter()

    @pytest.mark.asyncio
    async def test_parse_response_audio_url_only(self):
        """audio_url only (no audio hex), output_format=url: downloads from URL."""
        data = {"audio_url": "https://example.com/audio.mp3"}
        fake_content = b"audio from url only"
        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            path, fmt = await self.adapter._save_audio_from_data(
                data, "url", {"format": "mp3"}, 30.0
            )
            assert path.exists()
            assert path.read_bytes() == fake_content
            mock_dl.assert_called_once_with("https://example.com/audio.mp3", 30.0)

    @pytest.mark.asyncio
    async def test_parse_response_audio_hex_and_url(self):
        """Both audio hex and audio_url exist, output_format=url: URL takes priority over hex."""
        data = {
            "audio": "48656c6c6f",  # valid hex "Hello"
            "audio_url": "https://example.com/audio.mp3",
        }
        fake_content = b"audio from url priority"
        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = fake_content
            path, fmt = await self.adapter._save_audio_from_data(
                data, "url", {"format": "mp3"}, 30.0
            )
            assert path.exists()
            assert path.read_bytes() == fake_content
            # Verifies URL is used, not hex
            mock_dl.assert_called_once_with("https://example.com/audio.mp3", 30.0)

    @pytest.mark.asyncio
    async def test_parse_response_hex_format_prefers_hex_over_url(self):
        """Both audio hex and audio_url exist, output_format=hex: hex takes priority."""
        data = {
            "audio": "48656c6c6f",  # valid hex "Hello"
            "audio_url": "https://example.com/audio.mp3",
        }
        with patch.object(self.adapter, "_download_content", new_callable=AsyncMock) as mock_dl:
            path, fmt = await self.adapter._save_audio_from_data(
                data, "hex", {"format": "mp3"}, 30.0
            )
            assert path.exists()
            assert path.read_bytes() == b"Hello"
            mock_dl.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_response_no_audio(self):
        """Neither audio hex nor audio_url exists: raises ProviderError."""
        data = {}
        from app.core.errors import ProviderError
        with pytest.raises(ProviderError) as exc_info:
            await self.adapter._save_audio_from_data(
                data, "url", {"format": "mp3"}, 30.0
            )
        assert "No valid audio source" in str(exc_info.value) or "audio" in str(exc_info.value).lower()


class TestSrtIntegration:
    """Verify that normalized timeline produces correct SRT output."""

    def test_srt_from_normalized_timeline(self):
        from app.utils.srt import timeline_to_srt
        timeline = [
            {"text": "你好世界", "start": 0.0, "end": 1.5},
            {"text": "再见", "start": 1.5, "end": 2.5},
        ]
        srt = timeline_to_srt(timeline)
        assert "00:00:00,000 --> 00:00:01,500" in srt
        assert "00:00:01,500 --> 00:00:02,500" in srt
        assert "你好世界" in srt
        assert "再见" in srt

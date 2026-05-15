"""Tests for audio duration fallback in AssetService.save_assets()."""

import tempfile
from pathlib import Path

import pytest
from sqlmodel import Session

from app.providers.base import ProviderRenderResult
from app.services.asset_service import (
    AssetService,
    _valid_duration_ms,
    _probe_audio_duration_ms,
)


class TestValidDurationMs:
    """Unit tests for _valid_duration_ms helper."""

    @pytest.mark.parametrize("value,expected", [
        (None, None),
        (0, None),
        ("0", None),
        ("", None),
        ("abc", None),
        (1, 1),
        (1200, 1200),
        ("1200", 1200),
        (1500.0, 1500),
        (-100, None),
        ("-5", None),
    ])
    def test_valid_duration_ms(self, value, expected):
        assert _valid_duration_ms(value) == expected


class TestProbeAudioDurationMs:
    """Unit tests for _probe_audio_duration_ms helper."""

    def test_nonexistent_file(self):
        result = _probe_audio_duration_ms(Path("/nonexistent/audio/file.mp3"))
        assert result is None

    def test_valid_wav_file(self, tmp_path):
        # Create a silent 500ms WAV file using the existing test helper
        from app.utils.audio import write_silent_wav
        audio_path = tmp_path / "test.wav"
        write_silent_wav(audio_path, duration_ms=500)

        result = _probe_audio_duration_ms(audio_path)
        assert result is not None
        # pydub returns duration in ms; allow some tolerance for encoding overhead
        assert 400 <= result <= 600

    def test_invalid_audio_file(self, tmp_path):
        # Write a text file with .mp3 extension
        audio_path = tmp_path / "fake.mp3"
        audio_path.write_text("not an audio file")

        result = _probe_audio_duration_ms(audio_path)
        assert result is None


class TestSaveAssetsDurationFallback:
    """Integration tests for save_assets duration fallback behavior."""

    def _make_result(self, audio_path: Path, duration_ms) -> ProviderRenderResult:
        return ProviderRenderResult(
            audio_path=str(audio_path),
            duration_ms=duration_ms,
        )

    def test_valid_provider_duration_preserved(self, session: Session, tmp_path):
        """When result.duration_ms is a positive int, it is used directly."""
        from app.utils.audio import write_silent_wav

        audio_path = tmp_path / "audio.wav"
        write_silent_wav(audio_path, duration_ms=1000)

        result = self._make_result(audio_path, 5000)
        service = AssetService()
        audio_asset, _ = service.save_assets(
            session=session,
            job_id="job_test_valid",
            provider="mock",
            model="test",
            result=result,
            audio_params={"format": "wav"},
            subtitle_type="sentence",
        )

        # Provider value (5000) should be preserved, not overwritten by probe
        assert audio_asset.duration_ms == 5000

    def test_zero_duration_falls_back_to_probe(self, session: Session, tmp_path, monkeypatch):
        """When result.duration_ms is 0, pydub probe is called."""
        from app.utils.audio import write_silent_wav

        audio_path = tmp_path / "audio_zero.wav"
        write_silent_wav(audio_path, duration_ms=1200)

        # Track whether _probe_audio_duration_ms was called
        calls = []
        original_probe = _probe_audio_duration_ms

        def tracking_probe(path):
            calls.append(path)
            return original_probe(path)

        monkeypatch.setenv("_probe_tracker", "installed")
        # Patch in the module
        import app.services.asset_service as mod
        monkeypatch.setattr(mod, "_probe_audio_duration_ms", tracking_probe)

        result = self._make_result(audio_path, 0)
        service = AssetService()
        audio_asset, _ = service.save_assets(
            session=session,
            job_id="job_test_zero",
            provider="mock",
            model="test",
            result=result,
            audio_params={"format": "wav"},
            subtitle_type="sentence",
        )

        assert audio_asset.duration_ms == 1200
        assert len(calls) == 1

    def test_none_duration_falls_back_to_probe(self, session: Session, tmp_path, monkeypatch):
        """When result.duration_ms is None, pydub probe is called."""
        from app.utils.audio import write_silent_wav

        audio_path = tmp_path / "audio_none.wav"
        write_silent_wav(audio_path, duration_ms=800)

        import app.services.asset_service as mod
        original_probe = mod._probe_audio_duration_ms
        calls = []

        def tracking_probe(path):
            calls.append(path)
            return original_probe(path)

        monkeypatch.setattr(mod, "_probe_audio_duration_ms", tracking_probe)

        result = self._make_result(audio_path, None)
        service = AssetService()
        audio_asset, _ = service.save_assets(
            session=session,
            job_id="job_test_none",
            provider="mock",
            model="test",
            result=result,
            audio_params={"format": "wav"},
            subtitle_type="sentence",
        )

        assert audio_asset.duration_ms == 800
        assert len(calls) == 1

    def test_string_zero_falls_back(self, session: Session, tmp_path):
        """When result.duration_ms is the string '0', it is treated as invalid."""
        from app.utils.audio import write_silent_wav

        audio_path = tmp_path / "audio_str0.wav"
        write_silent_wav(audio_path, duration_ms=900)

        result = self._make_result(audio_path, "0")
        service = AssetService()
        audio_asset, _ = service.save_assets(
            session=session,
            job_id="job_test_str0",
            provider="mock",
            model="test",
            result=result,
            audio_params={"format": "wav"},
            subtitle_type="sentence",
        )

        assert audio_asset.duration_ms == 900

    def test_probe_failure_keeps_none(self, session: Session, tmp_path, monkeypatch):
        """When pydub probe fails, duration_ms stays None (does not raise)."""
        import app.services.asset_service as mod

        audio_path = tmp_path / "nonexistent.wav"

        def failing_probe(path):
            return None

        monkeypatch.setattr(mod, "_probe_audio_duration_ms", failing_probe)

        result = self._make_result(audio_path, 0)
        service = AssetService()
        audio_asset, _ = service.save_assets(
            session=session,
            job_id="job_test_probe_fail",
            provider="mock",
            model="test",
            result=result,
            audio_params={"format": "wav"},
            subtitle_type="sentence",
        )

        # Should not raise, and duration_ms should be None
        assert audio_asset.duration_ms is None

    def test_valid_string_int_preserved(self, session: Session, tmp_path):
        """String integers like '1500' are coerced to int and preserved."""
        from app.utils.audio import write_silent_wav

        audio_path = tmp_path / "audio_str.wav"
        write_silent_wav(audio_path, duration_ms=500)

        result = self._make_result(audio_path, "1500")
        service = AssetService()
        audio_asset, _ = service.save_assets(
            session=session,
            job_id="job_test_str_int",
            provider="mock",
            model="test",
            result=result,
            audio_params={"format": "wav"},
            subtitle_type="sentence",
        )

        assert audio_asset.duration_ms == 1500

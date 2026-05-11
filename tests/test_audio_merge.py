import tempfile
from pathlib import Path

import pytest
from pydub import AudioSegment

from app.services.audio_merge_service import AudioMergeService
from app.utils.audio import write_silent_wav


@pytest.fixture
def service():
    return AudioMergeService()


@pytest.fixture
def two_audio_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = Path(tmpdir) / "a.wav"
        p2 = Path(tmpdir) / "b.wav"
        write_silent_wav(p1, duration_ms=500)
        write_silent_wav(p2, duration_ms=500)
        yield [str(p1), str(p2)], tmpdir


def test_merge_two_wav_files(service, two_audio_files):
    audio_paths, tmpdir = two_audio_files
    result = service.merge(audio_paths, silence_between_ms=0, output_format="wav")
    assert Path(result).exists()
    merged = AudioSegment.from_file(result)
    assert len(merged) >= 990  # ~500ms each, no silence


def test_merge_with_silence(service, two_audio_files):
    audio_paths, tmpdir = two_audio_files
    result = service.merge(audio_paths, silence_between_ms=300, output_format="wav")
    merged = AudioSegment.from_file(result)
    # 500 + 300 + 500 = 1300ms
    assert len(merged) >= 1290


def test_merge_timelines_offset(service):
    timelines = [
        [{"text": "hello", "start": 0.0, "end": 1.0}],
        [{"text": "world", "start": 0.0, "end": 2.0}],
    ]
    durations_ms = [1000, 2000]
    result = service.merge_timelines(timelines, durations_ms, silence_between_ms=300)
    assert len(result) == 2
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 1.0
    # Second entry offset: 1000 + 300 = 1300
    assert result[1]["start"] == 1.3
    assert result[1]["end"] == 3.3


def test_merge_empty_list(service):
    with pytest.raises(ValueError, match="cannot be empty"):
        service.merge([])

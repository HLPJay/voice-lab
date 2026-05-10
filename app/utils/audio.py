import math
import wave
from pathlib import Path


def write_silent_wav(path: Path, duration_ms: int = 700, sample_rate: int = 16000) -> None:
    frames = int(sample_rate * duration_ms / 1000)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)


def estimate_duration_ms(text: str) -> int:
    return max(700, math.ceil(len(text) * 180))

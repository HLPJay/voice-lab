from pathlib import Path

from pydub import AudioSegment

from app.utils.files import storage_path
from app.utils.id_generator import new_id


class AudioMergeService:
    def merge(
        self,
        audio_paths: list[str],
        silence_between_ms: int = 300,
        output_format: str = "mp3",
    ) -> str:
        """合并多个音频文件，段间插入静音。返回合并后文件路径。"""
        if not audio_paths:
            raise ValueError("audio_paths cannot be empty")

        merged = AudioSegment.empty()
        for path_str in audio_paths:
            audio = AudioSegment.from_file(path_str)
            merged = merged + audio
            if silence_between_ms > 0:
                silence = AudioSegment.silent(duration=silence_between_ms)
                merged = merged + silence

        # Remove trailing silence
        if silence_between_ms > 0 and len(merged) >= silence_between_ms:
            merged = merged[:-silence_between_ms]

        merged_id = new_id("merged")
        output_path = storage_path("audio", f"{merged_id}.{output_format}")
        merged.export(str(output_path), format=output_format)
        return str(output_path)

    def merge_timelines(
        self,
        timelines: list[list[dict]],
        durations_ms: list[int],
        silence_between_ms: int = 300,
    ) -> list[dict]:
        """合并多段字幕时间轴，偏移量累加。返回合并后时间轴。"""
        if not timelines:
            return []

        result = []
        accumulated_ms = 0

        for i, (segment_timeline, duration_ms) in enumerate(zip(timelines, durations_ms)):
            if not segment_timeline:
                accumulated_ms += duration_ms + silence_between_ms
                continue

            for entry in segment_timeline:
                start_ms = int((entry.get("start", 0) or 0) * 1000)
                end_ms = int((entry.get("end", 0) or 0) * 1000)
                result.append({
                    "text": entry.get("text", ""),
                    "start": (accumulated_ms + start_ms) / 1000.0,
                    "end": (accumulated_ms + end_ms) / 1000.0,
                })

            segment_duration = duration_ms if duration_ms else sum(
                int((e.get("end", 0) - e.get("start", 0)) * 1000)
                for e in segment_timeline
            )
            accumulated_ms += segment_duration + silence_between_ms

        # Remove trailing silence offset from last entry
        if result and silence_between_ms > 0:
            pass  # entries already have correct offset, no need to trim

        return result

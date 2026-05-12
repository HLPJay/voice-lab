import io
import tempfile
from pathlib import Path

from app.core.errors import VoiceLabError
from app.core.logging import get_logger
from app.domain.schemas import VoiceCloneRequest, VoiceCloneResponse, VoiceCloneUploadResponse
from app.providers.registry import get_provider

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB


def _probe_audio_duration(file_data: bytes, ext: str) -> float | None:
    """Probe audio duration using pydub. Returns seconds or None if probing fails."""
    try:
        from pydub import AudioSegment
    except ImportError:
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        try:
            audio = AudioSegment.from_file(tmp_path)
            return len(audio) / 1000.0
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except Exception:
        return None


class VoiceCloneService:
    def __init__(self):
        self.logger = get_logger("voice_clone")

    async def upload_audio(
        self,
        provider: str,
        file_data: bytes,
        filename: str,
        purpose: str,
    ) -> VoiceCloneUploadResponse:
        if purpose not in ("voice_clone", "prompt_audio"):
            raise VoiceLabError("Invalid purpose", f"purpose must be 'voice_clone' or 'prompt_audio', got '{purpose}'")

        # 1a: Validate audio file extension and MIME type (official formats: mp3/m4a/wav)
        allowed_extensions = {".mp3", ".wav", ".m4a"}
        allowed_mime_prefixes = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4"}
        import mimetypes
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in allowed_extensions:
            raise VoiceLabError(
                "Unsupported audio format",
                f"file extension '{ext}' not allowed. Allowed: {', '.join(sorted(allowed_extensions))}",
            )
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and not any(mime_type.startswith(p) for p in allowed_mime_prefixes):
            raise VoiceLabError(
                "Unsupported audio MIME type",
                f"MIME type '{mime_type}' not allowed for audio upload",
            )

        # 1b: File size check
        if not file_data or len(file_data) < 10:
            raise VoiceLabError("Invalid audio data", "file is empty or too small to be a valid audio file")
        if len(file_data) > MAX_UPLOAD_SIZE:
            raise VoiceLabError("Audio file too large", f"Maximum 20MB, got {len(file_data) / 1024 / 1024:.1f}MB")

        # 1b: Duration check by purpose
        duration_sec = _probe_audio_duration(file_data, ext)
        if duration_sec is not None:
            if purpose == "voice_clone":
                if duration_sec < 10 or duration_sec > 300:
                    raise VoiceLabError(
                        "Audio duration out of range",
                        f"voice_clone requires 10-300 seconds, got {duration_sec:.1f}s",
                    )
            elif purpose == "prompt_audio":
                if duration_sec >= 8:
                    raise VoiceLabError(
                        "Audio duration out of range",
                        f"prompt_audio requires < 8 seconds, got {duration_sec:.1f}s",
                    )

        adapter = get_provider(provider)
        result = await adapter.upload_voice_file(file_data, filename, purpose)

        self.logger.info(
            "upload_audio provider=%s purpose=%s filename=%s file_id=%s",
            provider, purpose, filename, result.get("file_id"),
        )

        created_at_val = result.get("created_at")
        if isinstance(created_at_val, int):
            created_at_val = str(created_at_val)

        return VoiceCloneUploadResponse(
            file_id=result["file_id"],
            filename=result["filename"],
            purpose=result["purpose"],
            bytes=result.get("bytes"),
            created_at=created_at_val,
        )

    async def clone_voice(
        self,
        provider: str,
        request: VoiceCloneRequest,
    ) -> VoiceCloneResponse:
        adapter = get_provider(provider)

        request_dict = request.model_dump(exclude_none=False)
        result = await adapter.clone_voice(request_dict)

        self.logger.info(
            "clone_voice provider=%s voice_id=%s",
            provider, result.get("voice_id"),
        )

        return VoiceCloneResponse(
            voice_id=result["voice_id"],
            demo_audio_url=result.get("demo_audio_url"),
            duration_ms=result.get("duration_ms"),
            usage_characters=result.get("usage_characters"),
            message=result.get("message", "克隆成功"),
        )

import pytest
from unittest.mock import MagicMock
from fastapi import Request
from app.core.errors import VoiceLabError, voice_lab_error_handler


class TestVoiceLabErrorHandler:
    @pytest.mark.asyncio
    async def test_error_handler_log_includes_error_detail(self, caplog):
        """voice_lab_error_handler logs extra with error_detail."""
        exc = VoiceLabError("test error", detail="insufficient balance")
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test/path"
        mock_request.method = "POST"

        await voice_lab_error_handler(mock_request, exc)

        # Find the log record for voice_lab_error
        records = [r for r in caplog.records if r.message == "voice_lab_error"]
        assert len(records) == 1
        record = records[0]
        assert record.error_code == "VOICE_LAB_ERROR"
        assert record.error_message == "test error"
        assert record.error_detail == "insufficient balance"

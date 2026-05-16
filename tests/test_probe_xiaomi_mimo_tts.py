"""Tests for scripts/probe_xiaomi_mimo_tts.py.

P16-XIAOMI-MIMO-TTS-REAL-PROBE-B1: Tests for real API probe script.

These tests verify:
- dry-run doesn't call network
- --real-call calls network only when specified
- --env-file support
- redaction of API key and audio data
- output file structure
- error handling

All tests use fake httpx - no real network calls.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakehttpxResponse:
    """Fake httpx.Response for testing."""

    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            from httpx import HTTPStatusError
            raise HTTPStatusError(
                "server error",
                request=MagicMock(),
                response=self,
            )


@pytest.fixture
def temp_env_file():
    """Create a temporary env file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
        f.write("MIMO_API_KEY=fake_test_key\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "probes" / "xiaomi_mimo"


class TestDryRun:
    """Tests for dry-run mode."""

    def setup_method(self):
        """Clear environment before each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def teardown_method(self):
        """Clean up after each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def test_dry_run_does_not_call_http(self, temp_env_file):
        """dry-run mode does not make HTTP requests."""
        os.environ["VOICE_LAB_ENV_FILE"] = temp_env_file

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            from scripts.probe_xiaomi_mimo_tts import main

            exit_code = main(["--dry-run"])

            mock_client.post.assert_not_called()
            assert exit_code == 0

    def test_dry_run_output_contains_config(self, temp_env_file):
        """dry-run mode outputs configuration."""
        os.environ["VOICE_LAB_ENV_FILE"] = temp_env_file

        with patch("httpx.AsyncClient"):
            from scripts.probe_xiaomi_mimo_tts import main

            with patch("sys.stdout") as mock_stdout:
                mock_stdout.write = lambda x: None
                exit_code = main(["--dry-run"])

            assert exit_code == 0


class TestRealCall:
    """Tests for real-call mode."""

    def setup_method(self):
        """Clear environment before each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def teardown_method(self):
        """Clean up after each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def test_real_call_makes_http_request(self, temp_env_file, temp_output_dir):
        """--real-call makes HTTP request."""
        os.environ["VOICE_LAB_ENV_FILE"] = temp_env_file

        fake_wav = b"RIFF" + b"\x00" * 100
        encoded_audio = base64.b64encode(fake_wav).decode()

        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {"data": encoded_audio, "format": "wav"},
                    "content": ""
                }
            }],
            "usage": {"completion_tokens": 50}
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            exit_code = main([
                "--real-call",
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            assert mock_client.post.called

    def test_real_call_without_key_blocked(self, temp_output_dir):
        """--real-call without API key is blocked."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)

        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

        with patch("httpx.AsyncClient"):
            from scripts.probe_xiaomi_mimo_tts import main

            exit_code = main([
                "--real-call",
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            assert exit_code == 1


class TestEnvFile:
    """Tests for --env-file parameter."""

    def setup_method(self):
        """Clear environment before each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def teardown_method(self):
        """Clean up after each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def test_env_file_sets_voice_lab_env_file(self, temp_env_file):
        """--env-file sets VOICE_LAB_ENV_FILE."""
        fake_wav = b"RIFF" + b"\x00" * 100
        encoded_audio = base64.b64encode(fake_wav).decode()

        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {"data": encoded_audio, "format": "wav"},
                    "content": ""
                }
            }]
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            exit_code = main([
                "--real-call",
                "--env-file", temp_env_file,
            ])

            assert mock_client.post.called

            call_args = mock_client.post.call_args
            headers = call_args.kwargs.get("headers", {}) if call_args.kwargs else {}
            if "headers" in call_args[1]:
                headers = call_args[1]["headers"]
            assert headers.get("api-key") == "fake_test_key"


class TestRedaction:
    """Tests for redaction of sensitive data."""

    def setup_method(self):
        """Clear environment before each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def teardown_method(self):
        """Clean up after each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def test_request_redacted_does_not_contain_api_key(self, temp_env_file, temp_output_dir):
        """request.redacted.json does not contain real API key."""
        fake_wav = b"RIFF" + b"\x00" * 100
        encoded_audio = base64.b64encode(fake_wav).decode()

        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {"data": encoded_audio, "format": "wav"},
                    "content": ""
                }
            }]
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            main([
                "--real-call",
                "--env-file", temp_env_file,
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            probe_dirs = list((temp_output_dir.parent.parent).glob("probe_*"))
            assert len(probe_dirs) >= 1

            request_file = probe_dirs[-1] / "request.redacted.json"
            assert request_file.exists()

            with open(request_file, "r", encoding="utf-8") as f:
                request_data = json.load(f)

            assert request_data["headers"]["api-key"] == "***REDACTED***"
            request_str = json.dumps(request_data)
            assert "fake_test_key" not in request_str

    def test_response_redacted_does_not_contain_audio_data(self, temp_env_file, temp_output_dir):
        """response.redacted.json does not contain real base64 audio."""
        fake_wav = b"RIFF" + b"\x00" * 100
        encoded_audio = base64.b64encode(fake_wav).decode()

        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {"data": encoded_audio, "format": "wav"},
                    "content": ""
                }
            }]
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            main([
                "--real-call",
                "--env-file", temp_env_file,
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            probe_dirs = list((temp_output_dir.parent.parent).glob("probe_*"))
            assert len(probe_dirs) >= 1

            response_file = probe_dirs[-1] / "response.redacted.json"
            assert response_file.exists()

            with open(response_file, "r", encoding="utf-8") as f:
                response_data = json.load(f)

            audio_data = response_data["body"]["choices"][0]["message"]["audio"]["data"]
            assert audio_data == "***REDACTED_BASE64***"
            response_str = json.dumps(response_data)
            assert encoded_audio not in response_str

    def test_metadata_does_not_contain_api_key(self, temp_env_file, temp_output_dir):
        """metadata.json does not contain API key."""
        fake_wav = b"RIFF" + b"\x00" * 100
        encoded_audio = base64.b64encode(fake_wav).decode()

        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {"data": encoded_audio, "format": "wav"},
                    "content": ""
                }
            }]
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            main([
                "--real-call",
                "--env-file", temp_env_file,
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            probe_dirs = list((temp_output_dir.parent.parent).glob("probe_*"))
            assert len(probe_dirs) >= 1

            metadata_file = probe_dirs[-1] / "metadata.json"
            assert metadata_file.exists()

            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            assert metadata.get("api_key_source") == "hidden"
            metadata_str = json.dumps(metadata)
            assert "fake_test_key" not in metadata_str


class TestOutputStructure:
    """Tests for output file structure."""

    def setup_method(self):
        """Clear environment before each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def teardown_method(self):
        """Clean up after each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def test_output_creates_all_files(self, temp_env_file, temp_output_dir):
        """Successful probe creates all expected output files."""
        fake_wav = b"RIFF" + b"\x00" * 100
        encoded_audio = base64.b64encode(fake_wav).decode()

        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {"data": encoded_audio, "format": "wav"},
                    "content": ""
                }
            }],
            "usage": {"completion_tokens": 50}
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            main([
                "--real-call",
                "--env-file", temp_env_file,
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            probe_dirs = list((temp_output_dir.parent.parent).glob("probe_*"))
            assert len(probe_dirs) >= 1

            probe_dir = probe_dirs[-1]

            assert (probe_dir / "request.redacted.json").exists()
            assert (probe_dir / "response.redacted.json").exists()
            assert (probe_dir / "metadata.json").exists()
            assert (probe_dir / "output.wav").exists()

            with open(probe_dir / "metadata.json", "r", encoding="utf-8") as f:
                metadata = json.load(f)

            assert metadata["provider"] == "xiaomi_mimo"
            assert metadata["adapter_type"] == "xiaomi_mimo_chat_tts"
            assert metadata["real_call"] is True
            assert "success" in metadata


class TestErrorHandling:
    """Tests for error handling."""

    def setup_method(self):
        """Clear environment before each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def teardown_method(self):
        """Clean up after each test."""
        os.environ.pop("MIMO_API_KEY", None)
        os.environ.pop("VOICE_LAB_ENV_FILE", None)
        from app.config.env_resolver import clear_env_cache
        clear_env_cache()

    def test_http_error_401_saves_failed_metadata(self, temp_env_file, temp_output_dir):
        """HTTP 401 error saves failed metadata."""
        fake_response = FakehttpxResponse(
            {"error": "invalid API key"},
            status_code=401
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            main([
                "--real-call",
                "--env-file", temp_env_file,
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            probe_dirs = list((temp_output_dir.parent.parent).glob("probe_*"))
            assert len(probe_dirs) >= 1

            probe_dir = probe_dirs[-1]

            with open(probe_dir / "metadata.json", "r", encoding="utf-8") as f:
                metadata = json.load(f)

            assert metadata["success"] is False
            assert metadata["status_code"] == 401
            assert "error" in metadata["error_type"].lower() or "auth" in metadata["error_type"].lower()

    def test_missing_audio_data_saves_failed_metadata(self, temp_env_file, temp_output_dir):
        """Missing audio.data saves failed metadata."""
        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {},
                    "content": ""
                }
            }]
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            main([
                "--real-call",
                "--env-file", temp_env_file,
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            probe_dirs = list((temp_output_dir.parent.parent).glob("probe_*"))
            assert len(probe_dirs) >= 1

            probe_dir = probe_dirs[-1]

            with open(probe_dir / "metadata.json", "r", encoding="utf-8") as f:
                metadata = json.load(f)

            assert metadata["success"] is False
            assert "error" in metadata["error_type"].lower() or metadata["error_message"]

    def test_invalid_base64_saves_failed_metadata(self, temp_env_file, temp_output_dir):
        """Invalid base64 in response saves failed metadata."""
        fake_response = FakehttpxResponse({
            "id": "test-trace-123",
            "choices": [{
                "message": {
                    "audio": {"data": "!!!not-valid-base64!!!", "format": "wav"},
                    "content": ""
                }
            }]
        })

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = fake_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            from scripts.probe_xiaomi_mimo_tts import main

            main([
                "--real-call",
                "--env-file", temp_env_file,
                "--output-dir", str(temp_output_dir.parent.parent),
            ])

            probe_dirs = list((temp_output_dir.parent.parent).glob("probe_*"))
            assert len(probe_dirs) >= 1

            probe_dir = probe_dirs[-1]

            with open(probe_dir / "metadata.json", "r", encoding="utf-8") as f:
                metadata = json.load(f)

            assert metadata["success"] is False
            assert "audio" in metadata["error_type"].lower() or "decode" in metadata["error_message"].lower()
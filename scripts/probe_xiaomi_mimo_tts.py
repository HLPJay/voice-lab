#!/usr/bin/env python3
"""Xiaomi MiMo TTS Real API Probe Script.

P16-XIAOMI-MIMO-TTS-REAL-PROBE-B1: Execute real API probe for Xiaomi MiMo TTS.

This script probes the Xiaomi MiMo API without going through the full business
pipeline. Results are saved to tmp/probes/xiaomi_mimo/ with redacted data.

Usage:
    # Dry-run (default, no real API call)
    python scripts/probe_xiaomi_mimo_tts.py --dry-run

    # Real API call (requires --real-call flag)
    python scripts/probe_xiaomi_mimo_tts.py --real-call --env-file .env.local

Security:
    - Default dry-run mode: no network request made
    - --real-call required to enable real API calls
    - API key is never printed, logged, or saved
    - Request/response are redacted before saving
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path for imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))


DEFAULT_TEXT = "你好，这是一次小米 MiMo 语音合成探测。"
DEFAULT_VOICE = "mimo_default"
DEFAULT_MODEL = "mimo-v2.5-tts"
DEFAULT_FORMAT = "wav"
DEFAULT_OUTPUT_DIR = "tmp/probes/xiaomi_mimo/"
DEFAULT_TIMEOUT = 120

# Redacted constants
REDACTED = "***REDACTED***"
REDACTED_BASE64 = "***REDACTED_BASE64***"


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def resolve_mimo_api_key(env_file: str | None = None) -> tuple[str | None, str]:
    """Resolve MIMO_API_KEY using env_resolver.

    Args:
        env_file: Optional path to env file (sets VOICE_LAB_ENV_FILE).

    Returns:
        Tuple of (api_key, source) where source describes where the key was found.
    """
    # Set VOICE_LAB_ENV_FILE if provided
    if env_file:
        os.environ["VOICE_LAB_ENV_FILE"] = str(Path(env_file).resolve())

    # Use env_resolver to get the key
    from app.config.env_resolver import resolve_env_value

    api_key = resolve_env_value("MIMO_API_KEY")

    # Determine source for reporting (not the actual key)
    if api_key is not None:
        # Check which source provided it
        if os.environ.get("MIMO_API_KEY"):
            source = "os.environ"
        elif os.environ.get("VOICE_LAB_ENV_FILE"):
            source = "VOICE_LAB_ENV_FILE"
        else:
            source = ".env"
        return api_key, source

    # Key not found - determine which sources were checked
    sources_checked = []
    if "MIMO_API_KEY" in os.environ:
        sources_checked.append("os.environ.MIMO_API_KEY")
    else:
        sources_checked.append("os.environ.MIMO_API_KEY: NOT SET")

    if os.environ.get("VOICE_LAB_ENV_FILE"):
        sources_checked.append(f"VOICE_LAB_ENV_FILE: {os.environ['VOICE_LAB_ENV_FILE']}")
    else:
        sources_checked.append("VOICE_LAB_ENV_FILE: NOT SET")

    # Check project .env
    project_env = get_project_root() / ".env"
    if project_env.exists():
        sources_checked.append(f"Project .env: {project_env}")
    else:
        sources_checked.append(f"Project .env: NOT FOUND")

    return None, ", ".join(sources_checked)


def print_dry_run_banner(
    endpoint: str,
    model: str,
    voice: str,
    format: str,
    text: str,
    output_dir: str,
    api_key_source: str,
) -> None:
    """Print the dry-run banner."""
    print()
    print("[DRY-RUN] Xiaomi MiMo TTS Real Probe")
    print("=" * 50)
    print()
    print("Real API call: NO (use --real-call to enable)")
    print()
    print("Configuration:")
    print(f"  endpoint:    POST {endpoint}")
    print(f"  model:      {model}")
    print(f"  voice:      {voice}")
    print(f"  format:     {format}")
    print(f"  text:       {text}")
    print(f"  text_chars: {len(text)}")
    print(f"  output_dir: {output_dir}")
    print()
    print("API Key:")
    print(f"  - {api_key_source}")
    print()
    print("Ready to probe. No network call made.")
    print()


def make_request_payload(
    model: str,
    text: str,
    voice: str,
    format: str,
) -> dict[str, Any]:
    """Build the request payload for Xiaomi MiMo API."""
    return {
        "model": model,
        "messages": [
            {"role": "assistant", "content": text}
        ],
        "audio": {
            "format": format,
            "voice": voice,
        },
    }


async def execute_real_request(
    endpoint: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: int,
) -> tuple[dict[str, Any], int]:
    """Execute the real API request.

    Returns:
        Tuple of (response_json, status_code)
    """
    import httpx

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            endpoint,
            json=payload,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
        )
        return response.json(), response.status_code


def create_redacted_request(
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Create a redacted version of the request for saving."""
    return {
        "url": endpoint,
        "method": "POST",
        "headers": {
            "api-key": REDACTED,
            "Content-Type": "application/json",
        },
        "body": payload,
    }


def create_redacted_response(
    response_json: dict[str, Any],
    status_code: int,
) -> dict[str, Any]:
    """Create a redacted version of the response for saving."""
    redacted = dict(response_json)

    # Redact audio data
    if "choices" in redacted:
        for choice in redacted["choices"]:
            if "message" in choice:
                msg = choice["message"]
                if "audio" in msg and "data" in msg["audio"]:
                    msg["audio"]["data"] = REDACTED_BASE64

    return {
        "status_code": status_code,
        "headers": {
            "content-type": "application/json",
        },
        "body": redacted,
    }


def save_probe_output(
    output_dir: Path,
    request_redacted: dict[str, Any],
    response_redacted: dict[str, Any],
    metadata: dict[str, Any],
    audio_bytes: bytes | None,
) -> None:
    """Save probe output files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save redacted request
    with open(output_dir / "request.redacted.json", "w", encoding="utf-8") as f:
        json.dump(request_redacted, f, ensure_ascii=False, indent=2)

    # Save redacted response
    with open(output_dir / "response.redacted.json", "w", encoding="utf-8") as f:
        json.dump(response_redacted, f, ensure_ascii=False, indent=2)

    # Save metadata
    with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Save audio if present
    if audio_bytes:
        with open(output_dir / "output.wav", "wb") as f:
            f.write(audio_bytes)


async def run_probe(
    endpoint: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: int,
    output_dir: Path,
    started_at: str,
) -> dict[str, Any]:
    """Run the actual probe and save results.

    Returns:
        Metadata dict for the probe.
    """
    import httpx

    duration_ms = 0
    trace_id = None
    audio_bytes = None
    audio_path = None
    error_type = None
    error_message = None
    status_code = 0

    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={
                    "api-key": api_key,
                    "Content-Type": "application/json",
                },
            )
        duration_ms = int((time.time() - start_time) * 1000)
        status_code = response.status_code
        response_json = response.json()

        if response.status_code >= 400:
            # HTTP error
            error_type = "HTTPError"
            error_message = f"status={response.status_code}, detail={response.text[:200]}"

            # Still save redacted response
            response_redacted = create_redacted_response(response_json, status_code)
            metadata = {
                "provider": "xiaomi_mimo",
                "adapter_type": "xiaomi_mimo_chat_tts",
                "model": payload["model"],
                "voice": payload["audio"]["voice"],
                "format": payload["audio"]["format"],
                "text": payload["messages"][0]["content"],
                "text_chars": len(payload["messages"][0]["content"]),
                "real_call": True,
                "success": False,
                "status_code": status_code,
                "error_type": error_type,
                "error_message": error_message,
                "trace_id": None,
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "duration_ms": duration_ms,
                "api_key_source": "hidden",
            }
            save_probe_output(
                output_dir,
                create_redacted_request(endpoint, payload),
                response_redacted,
                metadata,
                None,
            )
        else:
            # Success
            trace_id = response_json.get("id")

            # Parse audio data
            choices = response_json.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                audio_data = message.get("audio", {}).get("data")

                if audio_data is None:
                    error_type = "MissingAudioData"
                    error_message = "response missing audio.data"
                else:
                    try:
                        audio_bytes = base64.b64decode(audio_data)
                    except Exception as exc:
                        error_type = "AudioDecodeError"
                        error_message = f"Failed to decode base64 audio: {exc}"

            if error_type:
                # Audio decode error
                metadata = {
                    "provider": "xiaomi_mimo",
                    "adapter_type": "xiaomi_mimo_chat_tts",
                    "model": payload["model"],
                    "voice": payload["audio"]["voice"],
                    "format": payload["audio"]["format"],
                    "text": payload["messages"][0]["content"],
                    "text_chars": len(payload["messages"][0]["content"]),
                    "real_call": True,
                    "success": False,
                    "status_code": status_code,
                    "error_type": error_type,
                    "error_message": error_message,
                    "trace_id": trace_id,
                    "started_at": started_at,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": duration_ms,
                    "api_key_source": "hidden",
                }
                save_probe_output(
                    output_dir,
                    create_redacted_request(endpoint, payload),
                    create_redacted_response(response_json, status_code),
                    metadata,
                    None,
                )
            else:
                # Full success
                audio_path_str = str(output_dir / "output.wav")
                metadata = {
                    "provider": "xiaomi_mimo",
                    "adapter_type": "xiaomi_mimo_chat_tts",
                    "model": payload["model"],
                    "voice": payload["audio"]["voice"],
                    "format": payload["audio"]["format"],
                    "text": payload["messages"][0]["content"],
                    "text_chars": len(payload["messages"][0]["content"]),
                    "real_call": True,
                    "success": True,
                    "status_code": status_code,
                    "audio_path": audio_path_str,
                    "audio_bytes": len(audio_bytes) if audio_bytes else 0,
                    "trace_id": trace_id,
                    "started_at": started_at,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": duration_ms,
                    "api_key_source": "hidden",
                }
                save_probe_output(
                    output_dir,
                    create_redacted_request(endpoint, payload),
                    create_redacted_response(response_json, status_code),
                    metadata,
                    audio_bytes,
                )

    except httpx.TimeoutException as exc:
        duration_ms = int((time.time() - start_time) * 1000) if 'start_time' in dir() else 0
        error_type = "TimeoutException"
        error_message = f"Request timeout: {exc}"

        metadata = {
            "provider": "xiaomi_mimo",
            "adapter_type": "xiaomi_mimo_chat_tts",
            "model": payload["model"],
            "voice": payload["audio"]["voice"],
            "format": payload["audio"]["format"],
            "text": payload["messages"][0]["content"],
            "text_chars": len(payload["messages"][0]["content"]),
            "real_call": True,
            "success": False,
            "status_code": 0,
            "error_type": error_type,
            "error_message": error_message,
            "trace_id": None,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "api_key_source": "hidden",
        }
        save_probe_output(
            output_dir,
            create_redacted_request(endpoint, payload),
            {"error": "timeout"},
            metadata,
            None,
        )

    except Exception as exc:
        duration_ms = int((time.time() - start_time) * 1000) if 'start_time' in dir() else 0
        error_type = type(exc).__name__
        error_message = str(exc)

        metadata = {
            "provider": "xiaomi_mimo",
            "adapter_type": "xiaomi_mimo_chat_tts",
            "model": payload["model"],
            "voice": payload["audio"]["voice"],
            "format": payload["audio"]["format"],
            "text": payload["messages"][0]["content"],
            "text_chars": len(payload["messages"][0]["content"]),
            "real_call": True,
            "success": False,
            "status_code": 0,
            "error_type": error_type,
            "error_message": error_message,
            "trace_id": None,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "api_key_source": "hidden",
        }
        save_probe_output(
            output_dir,
            create_redacted_request(endpoint, payload),
            {"error": str(exc)},
            metadata,
            None,
        )

    return metadata


def print_real_call_banner(
    api_key_source: str,
    endpoint: str,
    output_dir: Path,
    metadata: dict[str, Any],
) -> None:
    """Print the result banner after real call."""
    print()
    print("[REAL-CALL] Xiaomi MiMo TTS Real Probe")
    print("=" * 50)
    print()
    print(f"API Key: Found ({api_key_source})")
    print(f"Making real API call to {endpoint}...")
    print()

    if metadata["success"]:
        print("[SUCCESS] Audio saved to:")
        print(f"  {output_dir / 'request.redacted.json'}")
        print(f"  {output_dir / 'response.redacted.json'}")
        print(f"  {output_dir / 'metadata.json'}")
        print(f"  {output_dir / 'output.wav'}")
        print()
        print(f"  status_code: {metadata['status_code']}")
        print(f"  audio_bytes: {metadata['audio_bytes']}")
        if metadata.get("trace_id"):
            print(f"  trace_id: {metadata['trace_id']}")
        print(f"  duration_ms: {metadata['duration_ms']}")
    else:
        print("[FAILED] Probe failed:")
        print(f"  status_code: {metadata.get('status_code', 'N/A')}")
        print(f"  error_type: {metadata.get('error_type', 'Unknown')}")
        print(f"  error_message: {metadata.get('error_message', 'Unknown')}")
        print()
        print(f"Results saved to: {output_dir}")


async def async_main(args: argparse.Namespace) -> int:
    """Async main entry point."""
    # Build configuration
    endpoint = "https://api.xiaomimimo.com/v1/chat/completions"
    model = args.model or DEFAULT_MODEL
    voice = args.voice or DEFAULT_VOICE
    format = args.format or DEFAULT_FORMAT
    text = args.text or DEFAULT_TEXT
    output_base = args.output_dir or DEFAULT_OUTPUT_DIR
    timeout = args.timeout or DEFAULT_TIMEOUT

    # Resolve API key
    api_key, api_key_source = resolve_mimo_api_key(args.env_file)

    # Generate output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    probe_id = f"probe_{timestamp}"
    output_dir = Path(output_base) / probe_id

    started_at = datetime.now(timezone.utc).isoformat()

    if not args.real_call:
        # Dry-run mode
        print_dry_run_banner(
            endpoint=endpoint,
            model=model,
            voice=voice,
            format=format,
            text=text,
            output_dir=str(output_dir),
            api_key_source=api_key_source,
        )
        return 0

    # Real-call mode
    if api_key is None:
        print()
        print("[BLOCKED] MIMO_API_KEY not found.")
        print()
        print("API Key:")
        print(f"  - {api_key_source}")
        print()
        print("Cannot execute real API call without a valid MIMO_API_KEY.")
        print("Please ensure one of:")
        print("  1. Set os.environ['MIMO_API_KEY']")
        print("  2. Set VOICE_LAB_ENV_FILE to point to an env file with MIMO_API_KEY")
        print("  3. Place MIMO_API_KEY in project .env file")
        print()
        return 1

    print()
    print("[REAL-CALL] Xiaomi MiMo TTS Real Probe")
    print("=" * 50)
    print()
    print(f"API Key: Found ({api_key_source})")
    print(f"Making real API call to {endpoint}...")
    print()

    # Build payload
    payload = make_request_payload(model, text, voice, format)

    # Execute request
    metadata = await run_probe(
        endpoint=endpoint,
        api_key=api_key,
        payload=payload,
        timeout=timeout,
        output_dir=output_dir,
        started_at=started_at,
    )

    # Print result
    print_real_call_banner(api_key_source, endpoint, output_dir, metadata)

    return 0 if metadata["success"] else 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Optional argument list. If None, uses sys.argv.
    """
    parser = argparse.ArgumentParser(
        description="Xiaomi MiMo TTS Real API Probe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (default, no real API call)
  python scripts/probe_xiaomi_mimo_tts.py --dry-run

  # Real API call (requires --real-call)
  python scripts/probe_xiaomi_mimo_tts.py --real-call --env-file .env.local

  # With custom parameters
  python scripts/probe_xiaomi_mimo_tts.py --real-call \\
    --text "你好，这是一次小米 MiMo 语音合成探测。" \\
    --voice "mimo_default" \\
    --format wav
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry-run mode (default, no real API call)",
    )
    parser.add_argument(
        "--real-call",
        action="store_true",
        default=False,
        help="Enable real API call (required to make actual requests)",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to env file (sets VOICE_LAB_ENV_FILE)",
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help=f"Text to synthesize (default: {DEFAULT_TEXT!r})",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default=None,
        help=f"Voice ID (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"Model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        help=f"Audio format (default: {DEFAULT_FORMAT})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help=f"Output base directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )

    args = parser.parse_args(argv)

    # Run async main
    import asyncio
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main())

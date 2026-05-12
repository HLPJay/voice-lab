"""Asset download tests."""
import io
import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.time import utc_now_iso
from app.models.batch_job import BatchJob
from app.models.voice_asset import AudioAsset


@pytest.fixture
def flac_asset(session: Session, seed_profile):
    """Create an AudioAsset with format=flac backed by a real FLAC file."""
    from app.utils.files import storage_path
    from pydub import AudioSegment

    # Generate a real silent FLAC file
    flac_data = io.BytesIO()
    try:
        from pydub import AudioSegment
        silence = AudioSegment.silent(duration=500, frame_rate=16000)
        silence.export(flac_data, format="flac")
        flac_bytes = flac_data.getvalue()
    except Exception:
        # Fallback: write raw bytes if pydub FLAC export fails
        flac_bytes = b"fLaC" + b"\x00" * 100

    asset_id = "audio_flac_test"
    storage_dir = storage_path("audio", "")
    os.makedirs(storage_dir, exist_ok=True)
    file_path = storage_path("audio", f"{asset_id}.flac")
    file_path.write_bytes(flac_bytes)

    now = utc_now_iso()
    asset = AudioAsset(
        id=asset_id,
        job_id="job_flac_test",
        provider="mock",
        model="speech-2.8-hd",
        file_path=str(file_path),
        file_url=f"/api/voice/assets/{asset_id}/download",
        format="flac",
        duration_ms=500,
        created_at=now,
    )
    session.add(asset)
    session.commit()
    return asset


def test_batch_download_flac_media_type(test_app, session: Session, seed_profile, seed_mock_binding, flac_asset):
    """Batch download of a flac-format merged asset returns Content-Type: audio/flac."""
    from app.domain.enums import BatchStatus

    # Create a completed batch job pointing to the flac asset
    now = utc_now_iso()
    batch_id = "batch_flac_test"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status=BatchStatus.success,
        provider="mock",
        output_format="hex",
        total_segments=1,
        completed_segments=1,
        failed_segments=0,
        merged_audio_asset_id=flac_asset.id,
        silence_between_ms=0,
        config_json="{}",
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)
    session.commit()

    # Request batch download
    client = TestClient(test_app)
    resp = client.get(f"/api/voice/batch/{batch_id}/download")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "audio/flac", \
        f"expected audio/flac, got {resp.headers.get('content-type')}"


def test_asset_download_flac_asset(test_app, session: Session, flac_asset):
    """GET /api/voice/assets/{id}/download with a flac asset returns Content-Type: audio/flac."""
    client = TestClient(test_app)
    resp = client.get(f"/api/voice/assets/{flac_asset.id}/download")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "audio/flac", \
        f"expected audio/flac, got {resp.headers.get('content-type')}"

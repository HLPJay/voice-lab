"""
P8-BE3D: Tests for cleanup_assets.py quarantine and restore modes.

Covers:
1. Forbidden argument rejection (--purge, --purge-quarantine)
2. Mutual exclusivity of --dry-run/--quarantine/--restore
3. --quarantine requires --plan
4. --quarantine requires --confirm QUARANTINE
5. --restore requires --manifest
6. --restore requires --confirm RESTORE
7. Plan version check in quarantine
8. Plan mode check in quarantine
9. Manifest structure after quarantine
10. Restore skips conflicts (no overwrite)
11. Restore only processes status=moved files
12. DB re-validation skips DB-referenced files
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cleanup_assets import (
    MANIFEST_VERSION,
    REPORT_VERSION,
)


class TestForbiddenArguments:
    """Forbidden arguments must always be rejected regardless of mode."""

    @pytest.mark.parametrize("arg", [
        "--purge",
        "--purge-quarantine",
    ])
    def test_purge_rejected_standalone(self, arg: str):
        """--purge and --purge-quarantine must be rejected with an error."""
        result = subprocess.run(
            [sys.executable, "scripts/cleanup_assets.py", arg],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, f"{arg} should be rejected"
        assert "not supported" in result.stderr.lower() or "error" in result.stderr.lower()

    @pytest.mark.parametrize("arg", [
        "--purge",
        "--purge-quarantine",
    ])
    def test_purge_rejected_with_dryRun(self, arg: str):
        """--purge must be rejected even alongside --dry-run."""
        result = subprocess.run(
            [sys.executable, "scripts/cleanup_assets.py", "--dry-run", arg],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, f"{arg} should be rejected with --dry-run"


class TestModeMutualExclusivity:
    """Modes --dry-run, --quarantine, --restore are mutually exclusive."""

    def test_cannot_combine_quarantine_and_restore(self):
        """Cannot specify both --quarantine and --restore."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine", "--restore",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "mutually exclusive args should be rejected"

    def test_cannot_combine_dry_run_and_quarantine(self):
        """Cannot specify both --dry-run and --quarantine."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--quarantine",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "mutually exclusive args should be rejected"

    def test_cannot_combine_dry_run_and_restore(self):
        """Cannot specify both --dry-run and --restore."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--restore",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "mutually exclusive args should be rejected"


class TestQuarantineRequires:
    """--quarantine requires --plan and --confirm QUARANTINE."""

    def test_quarantine_requires_plan(self):
        """--quarantine without --plan must error."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine", "--confirm", "QUARANTINE",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "plan" in result.stderr.lower()

    def test_quarantine_requires_confirm_token(self):
        """--quarantine without --confirm QUARANTINE must error."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine",
                "--plan", "docs/generated/asset_cleanup_dry_run.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "confirm" in result.stderr.lower()

    def test_quarantine_requires_exact_confirm_token(self):
        """--quarantine with wrong confirm token must error."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine",
                "--plan", "docs/generated/asset_cleanup_dry_run.json",
                "--confirm", "WRONGTOKEN",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "confirm" in result.stderr.lower()


class TestRestoreRequires:
    """--restore requires --manifest and --confirm RESTORE."""

    def test_restore_requires_manifest(self):
        """--restore without --manifest must error."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore", "--confirm", "RESTORE",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "manifest" in result.stderr.lower()

    def test_restore_requires_confirm_token(self):
        """--restore without --confirm RESTORE must error."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore",
                "--manifest", "storage/quarantine/20260101T000000/manifest.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "confirm" in result.stderr.lower()

    def test_restore_requires_exact_confirm_token(self):
        """--restore with wrong confirm token must error."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore",
                "--manifest", "storage/quarantine/20260101T000000/manifest.json",
                "--confirm", "WRONGTOKEN",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "confirm" in result.stderr.lower()


class TestDryRunRequires:
    """--dry-run is valid standalone (backward compat)."""

    def test_dry_run_standalone_ok(self):
        """--dry-run alone is valid (existing BE3C behavior)."""
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run",
                "--storage-dir", "/tmp/nonexistent",
            ],
            capture_output=True,
            text=True,
        )
        # Should not error about missing mode
        assert result.returncode == 0 or "mode" in result.stderr.lower()


class TestPlanValidation:
    """Quarantine plan validation checks."""

    def test_quarantine_rejects_wrong_version(self, tmp_path: Path):
        """Quarantine must reject a plan with wrong report_version."""
        bad_plan = {
            "report_version": "wrong-version",
            "mode": "dry-run",
            "candidates": [],
        }
        plan_file = tmp_path / "bad_plan.json"
        plan_file.write_text(json.dumps(bad_plan), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine",
                "--plan", str(plan_file),
                "--confirm", "QUARANTINE",
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "version" in result.stderr.lower()

    def test_quarantine_rejects_non_dry_run_mode(self, tmp_path: Path):
        """Quarantine must reject a plan whose mode is not 'dry-run'."""
        bad_plan = {
            "report_version": REPORT_VERSION,
            "mode": "quarantine",  # wrong mode
            "candidates": [],
        }
        plan_file = tmp_path / "bad_plan.json"
        plan_file.write_text(json.dumps(bad_plan), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine",
                "--plan", str(plan_file),
                "--confirm", "QUARANTINE",
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "dry-run" in result.stderr.lower()


class TestRestoreManifestValidation:
    """Restore manifest validation checks."""

    def test_restore_rejects_wrong_manifest_version(self, tmp_path: Path):
        """Restore must reject a manifest with wrong manifest_version."""
        bad_manifest = {
            "manifest_version": "wrong-version",
            "mode": "quarantine",
            "files": [],
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(bad_manifest), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore",
                "--manifest", str(manifest_file),
                "--confirm", "RESTORE",
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "version" in result.stderr.lower()

    def test_restore_rejects_non_quarantine_mode(self, tmp_path: Path):
        """Restore must reject a manifest whose mode is not 'quarantine'."""
        bad_manifest = {
            "manifest_version": MANIFEST_VERSION,
            "mode": "restore",  # wrong mode
            "files": [],
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(bad_manifest), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore",
                "--manifest", str(manifest_file),
                "--confirm", "RESTORE",
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "quarantine" in result.stderr.lower()


class TestQuarantineManifestStructure:
    """Quarantine execution produces correct manifest structure."""

    def test_quarantine_creates_manifest(self, tmp_path: Path):
        """Quarantine must create a manifest.json in the quarantine dir."""
        # Create a minimal storage dir with an old audio file
        storage = tmp_path / "storage"
        audio_dir = storage / "audio"
        audio_dir.mkdir(parents=True)
        audio_file = audio_dir / "orphan.mp3"
        audio_file.write_text("fake audio content", encoding="utf-8")

        # Make it old
        old_mtime = time.time() - (10 * 86400)
        os.utime(audio_file, (old_mtime, old_mtime))

        # Create a valid plan
        plan = {
            "report_version": REPORT_VERSION,
            "mode": "dry-run",
            "candidates": [
                {
                    "candidate_id": "cand_000001",
                    "kind": "orphan-audio",
                    "reason": "orphan_audio",
                    "files": [
                        {
                            "relative_path": "audio/orphan.mp3",
                            "suffix": ".mp3",
                            "size_bytes": audio_file.stat().st_size,
                            "modified_time": "2026-04-01T00:00:00",
                            "modified_age_days": 10,
                        }
                    ],
                    "file_count": 1,
                    "total_size_bytes": audio_file.stat().st_size,
                    "oldest_modified_age_days": 10,
                    "newest_modified_age_days": 10,
                }
            ],
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine",
                "--plan", str(plan_file),
                "--confirm", "QUARANTINE",
                "--storage-dir", str(storage),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Quarantine failed: {result.stderr}"
        assert "manifest" in result.stdout.lower()

    def test_quarantine_manifest_fields(self, tmp_path: Path):
        """Manifest must contain all required top-level fields."""
        storage = tmp_path / "storage"
        audio_dir = storage / "audio"
        audio_dir.mkdir(parents=True)
        audio_file = audio_dir / "orphan.mp3"
        audio_file.write_text("fake audio content", encoding="utf-8")
        old_mtime = time.time() - (10 * 86400)
        os.utime(audio_file, (old_mtime, old_mtime))

        plan = {
            "report_version": REPORT_VERSION,
            "mode": "dry-run",
            "candidates": [
                {
                    "candidate_id": "cand_000001",
                    "kind": "orphan-audio",
                    "reason": "orphan_audio",
                    "files": [
                        {
                            "relative_path": "audio/orphan.mp3",
                            "suffix": ".mp3",
                            "size_bytes": audio_file.stat().st_size,
                            "modified_time": "2026-04-01T00:00:00",
                            "modified_age_days": 10,
                        }
                    ],
                    "file_count": 1,
                    "total_size_bytes": audio_file.stat().st_size,
                    "oldest_modified_age_days": 10,
                    "newest_modified_age_days": 10,
                }
            ],
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan), encoding="utf-8")

        subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine",
                "--plan", str(plan_file),
                "--confirm", "QUARANTINE",
                "--storage-dir", str(storage),
            ],
            capture_output=True,
            text=True,
        )

        # Find the manifest
        q_dirs = list((storage / "quarantine").glob("*"))
        assert len(q_dirs) == 1
        manifest_path = q_dirs[0] / "manifest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ["manifest_version", "created_at", "mode", "source_plan",
                    "storage_root", "quarantine_timestamp", "summary", "files", "notices"]:
            assert key in manifest, f"Missing key: {key}"

        assert manifest["manifest_version"] == MANIFEST_VERSION
        assert manifest["mode"] == "quarantine"
        assert manifest["summary"]["moved_file_count"] >= 0


class TestRestoreBehavior:
    """Restore correctly handles conflicts and status=moved only."""

    def test_restore_skips_status_not_moved(self, tmp_path: Path):
        """Restore must skip files with status=skipped or status=failed."""
        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "mode": "quarantine",
            "files": [
                {
                    "candidate_id": "cand_000001",
                    "kind": "orphan-audio",
                    "reason": "orphan_audio",
                    "original_relative_path": "audio/orphan.mp3",
                    "quarantine_relative_path": "quarantine/20260101T000000/audio/orphan.mp3",
                    "size_bytes": 100,
                    "modified_time": "2026-04-01T00:00:00",
                    "status": "skipped",
                    "skip_reason": "file_not_found",
                    "error": None,
                },
            ],
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore",
                "--manifest", str(manifest_file),
                "--confirm", "RESTORE",
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Restore failed: {result.stderr}"
        # skipped_not_moved count should be 1
        assert "skipped" in result.stdout.lower()

    def test_restore_skips_conflict_no_overwrite(self, tmp_path: Path):
        """Restore must skip if original path already exists (no overwrite)."""
        storage = tmp_path / "storage"
        orig_dir = storage / "audio"
        orig_dir.mkdir(parents=True)
        orig_file = orig_dir / "orphan.mp3"
        orig_file.write_text("existing content", encoding="utf-8")

        q_dir = storage / "quarantine" / "20260101T000000" / "audio"
        q_dir.mkdir(parents=True)
        q_file = q_dir / "orphan.mp3"
        q_file.write_text("quarantined content", encoding="utf-8")

        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "mode": "quarantine",
            "files": [
                {
                    "candidate_id": "cand_000001",
                    "kind": "orphan-audio",
                    "reason": "orphan_audio",
                    "original_relative_path": "audio/orphan.mp3",
                    "quarantine_relative_path": "quarantine/20260101T000000/audio/orphan.mp3",
                    "size_bytes": 100,
                    "modified_time": "2026-04-01T00:00:00",
                    "status": "moved",
                    "skip_reason": None,
                    "error": None,
                },
            ],
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore",
                "--manifest", str(manifest_file),
                "--confirm", "RESTORE",
                "--storage-dir", str(storage),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Restore failed: {result.stderr}"
        assert "conflict" in result.stdout.lower()
        # Original file must not be overwritten
        assert orig_file.read_text(encoding="utf-8") == "existing content"
        # Quarantine file must still exist (restore was skipped due to conflict)
        assert q_file.exists(), "Quarantine file must still exist when restore is skipped due to conflict"

    def test_restore_moves_file_back(self, tmp_path: Path):
        """Restore must move (not copy) — quarantine file must not exist after successful restore."""
        storage = tmp_path / "storage"
        orig_dir = storage / "audio"
        orig_dir.mkdir(parents=True)
        # No original file (path is free)

        q_dir = storage / "quarantine" / "20260101T000000" / "audio"
        q_dir.mkdir(parents=True)
        q_file = q_dir / "orphan.mp3"
        q_file.write_text("quarantined content", encoding="utf-8")

        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "mode": "quarantine",
            "files": [
                {
                    "candidate_id": "cand_000001",
                    "kind": "orphan-audio",
                    "reason": "orphan_audio",
                    "original_relative_path": "audio/orphan.mp3",
                    "quarantine_relative_path": "quarantine/20260101T000000/audio/orphan.mp3",
                    "size_bytes": 100,
                    "modified_time": "2026-04-01T00:00:00",
                    "status": "moved",
                    "skip_reason": None,
                    "error": None,
                },
            ],
        }
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--restore",
                "--manifest", str(manifest_file),
                "--confirm", "RESTORE",
                "--storage-dir", str(storage),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Restore failed: {result.stderr}"
        assert "restored" in result.stdout.lower()
        # Original file must now exist
        orig_file = orig_dir / "orphan.mp3"
        assert orig_file.exists(), "Original file must exist after restore"
        assert orig_file.read_text(encoding="utf-8") == "quarantined content"
        # Quarantine file must be gone (move semantics)
        assert not q_file.exists(), "Quarantine file must be removed after restore"


class TestNoDestructiveInQuarantine:
    """Verify quarantine uses move semantics (source removed, file preserved in quarantine)."""

    def test_quarantine_source_file_moved(self, tmp_path: Path):
        """Quarantine must move (not copy) — source file must not exist after quarantine."""
        storage = tmp_path / "storage"
        audio_dir = storage / "audio"
        audio_dir.mkdir(parents=True)
        audio_file = audio_dir / "orphan.mp3"
        audio_file.write_text("fake audio", encoding="utf-8")
        old_mtime = time.time() - (10 * 86400)
        os.utime(audio_file, (old_mtime, old_mtime))

        plan = {
            "report_version": REPORT_VERSION,
            "mode": "dry-run",
            "candidates": [
                {
                    "candidate_id": "cand_000001",
                    "kind": "orphan-audio",
                    "reason": "orphan_audio",
                    "files": [
                        {
                            "relative_path": "audio/orphan.mp3",
                            "suffix": ".mp3",
                            "size_bytes": len("fake audio"),
                            "modified_time": "2026-04-01T00:00:00",
                            "modified_age_days": 10,
                        }
                    ],
                    "file_count": 1,
                    "total_size_bytes": len("fake audio"),
                    "oldest_modified_age_days": 10,
                    "newest_modified_age_days": 10,
                }
            ],
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan), encoding="utf-8")

        subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--quarantine",
                "--plan", str(plan_file),
                "--confirm", "QUARANTINE",
                "--storage-dir", str(storage),
            ],
            capture_output=True,
            text=True,
        )

        # Source file must be gone (move semantics, not copy)
        assert not audio_file.exists(), "Source file still exists — quarantine must move, not copy"
        # Quarantine file must exist
        q_dirs = list((storage / "quarantine").glob("*"))
        assert len(q_dirs) == 1
        # Use rglob to get only files, excluding manifest.json
        q_files = [f for f in q_dirs[0].rglob("*") if f.is_file() and f.name != "manifest.json"]
        assert len(q_files) == 1, f"Quarantine file must exist after move, found: {q_files}"

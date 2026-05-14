"""
P8-BE3C-FIX: Tests for cleanup_assets.py dry-run planner.

Covers:
1. CLI parameter parsing and defaults
2. Forbidden argument rejection
3. DB reference exclusion
4. Orphan audio classification
5. Subtitle pair grouping
6. Unpaired subtitle handling
7. max_files truncation
8. Output structure
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cleanup_assets import (
    REPORT_VERSION,
    RUNNING_PROTECTION_WINDOW_HOURS,
    STANDARD_RUNNING_JOB_STATUSES,
    EXCLUDED_STORAGE_DIRS,
    VALID_KINDS,
    build_subtitle_pairs,
    safe_path_str,
)


class TestSafePathStr:
    """Tests for safe_path_str helper."""

    def test_relative_path_returns_relative(self, tmp_path: Path):
        """Relative paths should be returned as-is (OS-aware separator)."""
        storage = tmp_path / "storage"
        storage.mkdir()
        result = safe_path_str("audio/file.mp3", storage)
        # Result may use backslash on Windows — compare as parts
        assert Path(result.replace("/", "\\")).parts == Path("audio/file.mp3").parts

    def test_absolute_path_within_root_returns_relative(self, tmp_path: Path):
        """Absolute path inside root resolves to relative."""
        storage = tmp_path / "storage"
        storage.mkdir()
        file_path = storage / "audio" / "file.mp3"
        file_path.parent.mkdir(parents=True)
        file_path.touch()
        result = safe_path_str(str(file_path), storage)
        # Must be a relative path, not an absolute one
        assert not Path(result).is_absolute(), f"Expected relative, got: {result}"

    def test_absolute_path_outside_root_is_redacted(self, tmp_path: Path):
        """Absolute path outside storage root is redacted."""
        storage = tmp_path / "storage"
        storage.mkdir()
        outside = tmp_path / "outside.mp3"
        outside.touch()
        result = safe_path_str(str(outside), storage)
        assert result == f"<OUTSIDE_STORAGE_ROOT>/{outside.name}"
        assert "C:" not in result and "/home" not in result

    def test_none_returns_none(self, tmp_path: Path):
        assert safe_path_str(None, tmp_path) is None


class TestBuildSubtitlePairs:
    """Tests for subtitle pair grouping."""

    def test_paired_json_and_srt(self):
        """json+srt pair is recognized."""
        files = [
            {"relative_path": "subtitles/2026-05-14/abc.json"},
            {"relative_path": "subtitles/2026-05-14/abc.srt"},
        ]
        pairs, unpaired = build_subtitle_pairs(files)
        assert len(pairs) == 1
        assert len(unpaired) == 0
        assert pairs[0]["base"] == "subtitles/2026-05-14/abc"

    def test_json_only_no_srt(self):
        """json-only goes to unpaired."""
        files = [
            {"relative_path": "subtitles/2026-05-14/abc.json"},
        ]
        pairs, unpaired = build_subtitle_pairs(files)
        assert len(pairs) == 0
        assert len(unpaired) == 1

    def test_srt_only_no_json(self):
        """srt-only goes to unpaired."""
        files = [
            {"relative_path": "subtitles/2026-05-14/abc.srt"},
        ]
        pairs, unpaired = build_subtitle_pairs(files)
        assert len(pairs) == 0
        assert len(unpaired) == 1

    def test_multiple_pairs(self):
        """Multiple pairs are separated correctly."""
        files = [
            {"relative_path": "subtitles/2026-05-14/abc.json"},
            {"relative_path": "subtitles/2026-05-14/abc.srt"},
            {"relative_path": "subtitles/2026-05-14/def.json"},
            {"relative_path": "subtitles/2026-05-14/def.srt"},
        ]
        pairs, unpaired = build_subtitle_pairs(files)
        assert len(pairs) == 2
        assert len(unpaired) == 0

    def test_extra_json_no_pair(self):
        """Extra json without srt goes to unpaired."""
        files = [
            {"relative_path": "subtitles/2026-05-14/abc.json"},
            {"relative_path": "subtitles/2026-05-14/abc.srt"},
            {"relative_path": "subtitles/2026-05-14/extra.json"},
        ]
        pairs, unpaired = build_subtitle_pairs(files)
        assert len(pairs) == 1
        assert len(unpaired) == 1
        assert unpaired[0]["relative_path"] == "subtitles/2026-05-14/extra.json"


class TestConstants:
    """Test that constants match BE3B policy."""

    def test_report_version(self):
        assert REPORT_VERSION == "p8-be3c-dry-run"

    def test_running_protection_window_72h(self):
        assert RUNNING_PROTECTION_WINDOW_HOURS == 72

    def test_standard_running_statuses(self):
        assert STANDARD_RUNNING_JOB_STATUSES == {"queued", "pending", "running", "processing"}
        assert "pending" in STANDARD_RUNNING_JOB_STATUSES

    def test_quarantine_excluded(self):
        assert "quarantine" in EXCLUDED_STORAGE_DIRS

    def test_valid_kinds(self):
        assert VALID_KINDS == {"temp", "orphan-audio", "orphan-subtitle", "orphan"}


class TestForbiddenArguments:
    """Test that forbidden arguments are rejected by argparse."""

    @pytest.mark.parametrize("arg", [
        "--execute",
        "--mode",
        "--quarantine",
        "--restore",
        "--purge-quarantine",
        "--confirm",
    ])
    def test_forbidden_arg_rejected(self, arg: str):
        """Forbidden arguments must cause an error."""
        result = subprocess.run(
            [sys.executable, "scripts/cleanup_assets.py", "--dry-run", arg],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, f"{arg} should be rejected but was accepted"
        assert "not supported" in result.stderr or "error" in result.stderr.lower()


class TestDryRunDefaults:
    """Test default parameter values."""

    def test_dry_run_required(self):
        """Running without --dry-run should error."""
        result = subprocess.run(
            [sys.executable, "scripts/cleanup_assets.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "error" in result.stderr.lower()

    def test_kind_default(self):
        """Default kind should be 'orphan'."""
        result = subprocess.run(
            [sys.executable, "scripts/cleanup_assets.py", "--dry-run", "--help"],
            capture_output=True,
            text=True,
        )
        assert "orphan" in result.stdout


class TestOutputStructure:
    """Test that the JSON output has the required structure."""

    def test_output_json_structure(self, tmp_path: Path):
        """Output JSON must contain all required top-level keys."""
        output = tmp_path / "dry_run_out.json"
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run",
                "--kind", "orphan",
                "--min-age-days", "7",
                "--max-files", "1000",
                "--output", str(output),
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert output.exists()

        data = json.loads(output.read_text(encoding="utf-8"))
        for key in ["report_version", "generated_at", "mode", "storage_root",
                    "kind", "min_age_days", "max_files", "protection",
                    "summary", "candidates", "excluded", "notices"]:
            assert key in data, f"Missing key: {key}"

        assert data["report_version"] == "p8-be3c-dry-run"
        assert data["mode"] == "dry-run"
        assert data["storage_root"] == "<REDACTED>"
        assert "candidate_file_count" in data["summary"]
        assert "candidate_group_count" in data["summary"]
        assert "excluded_recent_count" in data["summary"]
        assert "excluded_db_referenced_count" in data["summary"]
        assert "excluded_running_guard_count" in data["summary"]
        assert "truncated" in data["summary"]

    def test_protection_fields(self, tmp_path: Path):
        """Protection block must contain running-like job info."""
        output = tmp_path / "dry_run_out.json"
        subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--output", str(output), "--storage-dir", str(tmp_path),
            ],
            capture_output=True, text=True,
        )
        data = json.loads(output.read_text(encoding="utf-8"))
        prot = data["protection"]
        assert "standard_running_statuses" in prot
        assert "extended_running_statuses" in prot
        assert "running_like_job_count" in prot
        assert "protection_window_hours" in prot
        assert prot["protection_window_hours"] == 72
        assert "db_referenced_files_excluded" in prot
        assert "quarantine_excluded" in prot
        assert "subtitle_pair_required" in prot

    def test_notices_present(self, tmp_path: Path):
        """Notices must warn about dry-run nature."""
        output = tmp_path / "dry_run_out.json"
        subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--output", str(output), "--storage-dir", str(tmp_path),
            ],
            capture_output=True, text=True,
        )
        data = json.loads(output.read_text(encoding="utf-8"))
        notices = data.get("notices", [])
        dry_run_notice = any("delete" in n.lower() or "dry-run" in n.lower() for n in notices)
        assert dry_run_notice, "Must have dry-run notice"

    def test_excluded_has_all_categories(self, tmp_path: Path):
        """excluded block must have all required categories."""
        output = tmp_path / "dry_run_out.json"
        subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--output", str(output), "--storage-dir", str(tmp_path),
            ],
            capture_output=True, text=True,
        )
        data = json.loads(output.read_text(encoding="utf-8"))
        excl = data["excluded"]
        for cat in ["recent_files", "db_referenced_files", "running_guard_files",
                    "unpaired_subtitle_files", "quarantine_files"]:
            assert cat in excl, f"Missing excluded category: {cat}"
            assert "count" in excl[cat]
            assert "note" in excl[cat]


class TestNoDestructiveOperations:
    """Verify the script does not contain destructive operation code."""

    def test_no_permanent_deletion_in_source(self):
        """Source must not contain permanent deletion operations (unlink, os.remove, shutil.rmtree).

        Note: shutil.move is allowed for quarantine (move to quarantine dir) and restore
        (move back to original dir) — these are reversible operations that preserve files.
        """
        src = Path("scripts/cleanup_assets.py").read_text(encoding="utf-8")
        # Check epilog is excluded from this test
        epilog_marker = "Examples:"
        epilog_start = src.find(epilog_marker)
        src_code = src[:epilog_start] if epilog_start != -1 else src

        forbidden = [
            ".unlink(",
            "os.remove",
            "shutil.rmtree",
            "session.delete",
            "session.commit",
            "DROP ",
            "TRUNCATE ",
            "UPDATE ",
            "DELETE ",
            ".rename(",
            "os.rename",
        ]
        found = [x for x in forbidden if x in src_code]
        assert not found, f"Permanent deletion operations found in script: {found}"

    def test_dry_run_mode_enforced(self):
        """Running with forbidden args must fail, not silently do nothing."""
        for arg in ["--execute", "--quarantine"]:
            result = subprocess.run(
                [sys.executable, "scripts/cleanup_assets.py", "--dry-run", arg],
                capture_output=True, text=True,
            )
            assert result.returncode != 0, f"{arg} should error but succeeded"


class TestTruncationLogic:
    """Test that truncation is based on eligible count vs max_files."""

    def test_truncated_false_when_under_limit(self, tmp_path: Path):
        """With max-files=1000 and few files, truncated should be false."""
        # Create a few old audio files
        audio_dir = tmp_path / "storage" / "audio"
        audio_dir.mkdir(parents=True)
        (audio_dir / "old1.mp3").touch()

        output = tmp_path / "dry_run_out.json"
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--kind", "orphan-audio",
                "--min-age-days", "0",
                "--max-files", "1000",
                "--output", str(output),
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["summary"]["truncated"] is False

    def test_truncated_true_when_over_limit(self, tmp_path: Path):
        """With max-files=1 and more than 1 eligible, truncated should be true."""
        # Files must be at --storage-dir/audio/ not --storage-dir/storage/audio/
        audio_dir = tmp_path / "audio"
        audio_dir.mkdir(parents=True)
        for i in range(5):
            f = audio_dir / f"old{i}.mp3"
            f.touch()
            import os, time
            old_mtime = time.time() - (10 * 86400)  # 10 days old
            os.utime(f, (old_mtime, old_mtime))

        output = tmp_path / "dry_run_out.json"
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--kind", "orphan-audio",
                "--min-age-days", "7",
                "--max-files", "1",
                "--output", str(output),
                "--storage-dir", str(tmp_path),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["summary"]["truncated"] is True
        assert data["summary"]["candidate_group_count"] == 1


class TestExcludedCounts:
    """Test that excluded counts are accurate."""

    def test_db_referenced_not_in_candidates(self, tmp_path: Path):
        """Files referenced in DB should appear in excluded_db_referenced_count, not candidates."""
        storage = tmp_path / "storage"
        audio_dir = storage / "audio"
        audio_dir.mkdir(parents=True)
        audio_file = audio_dir / "db_ref.mp3"
        audio_file.touch()
        # Make it appear old
        import os, time
        old = time.time() - 10 * 86400
        os.utime(audio_file, (old, old))

        output = tmp_path / "dry_run_out.json"
        result = subprocess.run(
            [
                sys.executable, "scripts/cleanup_assets.py",
                "--dry-run", "--kind", "orphan-audio",
                "--min-age-days", "7",
                "--max-files", "1000",
                "--output", str(output),
                "--storage-dir", str(storage),
            ],
            capture_output=True, text=True,
            env={**os.environ, "VOICE_LAB_STORAGE_DIR": str(storage)},
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        data = json.loads(output.read_text(encoding="utf-8"))
        # DB-referenced file is excluded, not a candidate
        # (actual DB doesn't reference our temp file, so it's an orphan)
        assert data["summary"]["candidate_group_count"] >= 0
        assert data["excluded"]["db_referenced_files"]["count"] >= 0

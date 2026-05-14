#!/usr/bin/env python3
"""
P8-BE3C: Asset cleanup dry-run planner.

This script generates a read-only cleanup plan.
It does not delete files.
It does not move files.
It does not modify database records.
It does not implement quarantine.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.database import engine
from app.models.voice_asset import AudioAsset, SubtitleAsset
from app.models.voice_job import VoiceJob

REPORT_VERSION = "p8-be3c-dry-run"
MAX_DEFAULT_FILES = 1000
DEFAULT_KIND = "orphan"
DEFAULT_MIN_AGE_DAYS = 7
RUNNING_PROTECTION_WINDOW_HOURS = 72
STANDARD_RUNNING_JOB_STATUSES = {"queued", "pending", "running", "processing"}
EXTENDED_RUNNING_JOB_STATUSES = {"protected"}
RUNNING_JOB_STATUSES = STANDARD_RUNNING_JOB_STATUSES | EXTENDED_RUNNING_JOB_STATUSES
EXCLUDED_STORAGE_DIRS = {"quarantine"}
VALID_KINDS = {"temp", "orphan-audio", "orphan-subtitle", "orphan"}


def safe_path_str(path: str | None, root: Path) -> str | None:
    """Return a safe relative path string, or redacted if outside root."""
    if not path:
        return None
    try:
        p = Path(path)
        if p.is_absolute():
            try:
                return str(p.relative_to(root.resolve()))
            except Exception:
                return f"<OUTSIDE_STORAGE_ROOT>/{p.name}"
        return str(p)
    except Exception:
        return "<INVALID_PATH>"


def safe_file_info(full_path: Path, root: Path) -> dict | None:
    """Return safe file info dict or None if file doesn't exist or is unreadable."""
    try:
        if not full_path.exists() or not full_path.is_file():
            return None
        stat = full_path.stat()
        age_days = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
        return {
            "relative_path": safe_path_str(str(full_path), root),
            "suffix": full_path.suffix,
            "size_bytes": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "modified_age_days": age_days,
        }
    except Exception:
        return None


def scan_storage_directory(root: Path, subdir: str) -> list[dict]:
    """Recursively scan a storage subdirectory and return file info list."""
    if subdir in EXCLUDED_STORAGE_DIRS:
        return []
    dir_path = root / subdir
    if not dir_path.exists():
        return []
    results = []
    try:
        for item in dir_path.rglob("*"):
            if item.is_file():
                info = safe_file_info(item, root)
                if info:
                    info["subdir"] = subdir
                    results.append(info)
    except Exception:
        pass
    return results


def age_bucket(days: int) -> str:
    if days < 1:
        return "0-1d"
    elif days < 7:
        return "1-7d"
    elif days < 30:
        return "7-30d"
    elif days < 90:
        return "30-90d"
    else:
        return "90d+"


def size_bucket(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    elif size_bytes < 10 * 1024:
        return "<10KB"
    elif size_bytes < 1024 * 1024:
        return "10KB-1MB"
    elif size_bytes < 10 * 1024 * 1024:
        return "1MB-10MB"
    else:
        return "10MB+"


def build_subtitle_pairs(subtitle_files: list[dict]) -> tuple[list[dict], list[dict]]:
    """Group subtitle files into paired (json+srt) and unpaired lists.

    Returns (paired_groups, unpaired_files).
    paired_groups: list of dicts with 'base', 'json_file', 'srt_file'
    unpaired_files: list of file dicts that have no pair
    """
    by_key: dict[str, dict[str, dict]] = {}
    for f in subtitle_files:
        rp = f.get("relative_path", "")
        p = Path(rp)
        if len(p.parts) >= 2:
            subdir = p.parts[0]
            date_part = p.parts[1] if len(p.parts) > 1 else ""
            base = p.stem
            key = f"{subdir}/{date_part}/{base}"
            ext = p.suffix.lower()
            if ext in (".json", ".srt"):
                if key not in by_key:
                    by_key[key] = {}
                by_key[key][ext] = f

    paired_groups = []
    unpaired_files = []
    for base_key, files in by_key.items():
        has_json = ".json" in files
        has_srt = ".srt" in files
        if has_json and has_srt:
            paired_groups.append({
                "base": base_key,
                "json_file": files[".json"],
                "srt_file": files[".srt"],
            })
        else:
            for ext, f in files.items():
                unpaired_files.append(f)

    return paired_groups, unpaired_files


def run_dry_run(
    kind: str,
    min_age_days: int,
    max_files: int,
    output_path: str | None,
    storage_dir: str | None,
) -> dict[str, Any]:
    root = Path(storage_dir) if storage_dir else Path(get_settings().storage_dir)
    output_path = Path(output_path) if output_path else Path("docs/generated/asset_cleanup_dry_run.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- DB scan (read-only) ---
    with Session(engine) as session:
        audio_assets = list(session.exec(select(AudioAsset)).all())
        subtitle_assets = list(session.exec(select(SubtitleAsset)).all())
        voice_jobs = list(session.exec(select(VoiceJob)).all())

    # Build DB reference sets
    audio_file_paths_db: set[str] = set()
    subtitle_file_paths_db: set[str] = set()
    subtitle_srt_paths_db: set[str] = set()

    for a in audio_assets:
        if a.file_path:
            audio_file_paths_db.add(str(Path(a.file_path).resolve()))

    for s in subtitle_assets:
        if s.file_path:
            subtitle_file_paths_db.add(str(Path(s.file_path).resolve()))
        if s.srt_path:
            subtitle_srt_paths_db.add(str(Path(s.srt_path).resolve()))

    # Running-like jobs
    running_like_jobs = [j for j in voice_jobs if j.status in STANDARD_RUNNING_JOB_STATUSES]
    running_like_status_dist = dict(Counter(j.status for j in running_like_jobs))

    # --- Storage scan ---
    audio_files = scan_storage_directory(root, "audio")
    subtitle_files = scan_storage_directory(root, "subtitles")
    temp_files = scan_storage_directory(root, "temp")

    # Build disk path sets (full resolved paths)
    audio_file_disk: set[str] = set()
    subtitle_file_disk: set[str] = set()

    for f in audio_files:
        full = root / f["relative_path"]
        audio_file_disk.add(str(full.resolve()))

    for f in subtitle_files:
        full = root / f["relative_path"]
        subtitle_file_disk.add(str(full.resolve()))

    # Running protection threshold: 72 hours = 3 days
    protection_age_days = max(1, RUNNING_PROTECTION_WINDOW_HOURS // 24)

    # --- Classify every audio file on disk into exactly one bucket ---
    # Categories: db_referenced | recent | running_guard | eligible_orphan_audio
    db_referenced_audio = []
    recent_audio = []
    running_guard_audio = []
    eligible_orphan_audio = []

    for f in audio_files:
        full = root / f["relative_path"]
        full_str = str(full.resolve())
        age = f["modified_age_days"]

        if full_str in audio_file_paths_db:
            db_referenced_audio.append(f)
        elif age < min_age_days:
            recent_audio.append(f)
        elif age < protection_age_days:
            running_guard_audio.append(f)
        else:
            eligible_orphan_audio.append(f)

    # --- Classify every subtitle file on disk into exactly one bucket ---
    # Categories: db_referenced | recent | running_guard | eligible_orphan_subtitle
    db_referenced_subtitle = []
    recent_subtitle = []
    running_guard_subtitle = []
    eligible_orphan_subtitle = []

    for f in subtitle_files:
        full = root / f["relative_path"]
        full_str = str(full.resolve())
        age = f["modified_age_days"]

        if full_str in subtitle_file_paths_db or full_str in subtitle_srt_paths_db:
            db_referenced_subtitle.append(f)
        elif age < min_age_days:
            recent_subtitle.append(f)
        elif age < protection_age_days:
            running_guard_subtitle.append(f)
        else:
            eligible_orphan_subtitle.append(f)

    # --- Classify every temp file into exactly one bucket ---
    recent_temp = []
    running_guard_temp = []
    eligible_temp = []

    for f in temp_files:
        age = f["modified_age_days"]
        if age < min_age_days:
            recent_temp.append(f)
        elif age < protection_age_days:
            running_guard_temp.append(f)
        else:
            eligible_temp.append(f)

    # --- Build subtitle pairs from eligible orphan subtitles ---
    subtitle_pairs, unpaired_subtitles = build_subtitle_pairs(eligible_orphan_subtitle)

    # --- Compute truncated ---
    # Truncated = total eligible items (in file-count terms) exceeds max_files
    total_eligible_file_count = (
        len(eligible_orphan_audio) +
        (len(subtitle_pairs) * 2) +
        len(eligible_temp)
    )
    truncated = total_eligible_file_count > max_files

    # --- Build candidate groups (respecting max_files) ---
    candidates = []
    candidate_id = 0
    total_file_count = 0

    def next_id() -> str:
        nonlocal candidate_id
        candidate_id += 1
        return f"cand_{candidate_id:06d}"

    # orphan-audio candidates
    if kind in ("orphan", "orphan-audio"):
        for f in eligible_orphan_audio:
            if total_file_count >= max_files:
                break
            age = f["modified_age_days"]
            candidates.append({
                "candidate_id": next_id(),
                "kind": "orphan-audio",
                "reason": "orphan_audio",
                "files": [{
                    "relative_path": f["relative_path"],
                    "suffix": f["suffix"],
                    "size_bytes": f["size_bytes"],
                    "modified_time": f["modified_time"],
                    "modified_age_days": age,
                }],
                "file_count": 1,
                "total_size_bytes": f["size_bytes"],
                "oldest_modified_age_days": age,
                "newest_modified_age_days": age,
            })
            total_file_count += 1

    # orphan-subtitle pair candidates
    if kind in ("orphan", "orphan-subtitle"):
        for group in subtitle_pairs:
            json_f = group["json_file"]
            srt_f = group["srt_file"]
            if total_file_count + 2 > max_files:
                break
            age = max(json_f["modified_age_days"], srt_f["modified_age_days"])
            candidates.append({
                "candidate_id": next_id(),
                "kind": "orphan-subtitle",
                "reason": "orphan_subtitle_pair",
                "files": [
                    {
                        "relative_path": json_f["relative_path"],
                        "suffix": json_f["suffix"],
                        "size_bytes": json_f["size_bytes"],
                        "modified_time": json_f["modified_time"],
                        "modified_age_days": json_f["modified_age_days"],
                    },
                    {
                        "relative_path": srt_f["relative_path"],
                        "suffix": srt_f["suffix"],
                        "size_bytes": srt_f["size_bytes"],
                        "modified_time": srt_f["modified_time"],
                        "modified_age_days": srt_f["modified_age_days"],
                    },
                ],
                "file_count": 2,
                "total_size_bytes": json_f["size_bytes"] + srt_f["size_bytes"],
                "oldest_modified_age_days": age,
                "newest_modified_age_days": age,
            })
            total_file_count += 2

    # temp candidates
    if kind == "temp":
        for f in eligible_temp:
            if total_file_count >= max_files:
                break
            age = f["modified_age_days"]
            candidates.append({
                "candidate_id": next_id(),
                "kind": "temp",
                "reason": "temp_expired",
                "files": [{
                    "relative_path": f["relative_path"],
                    "suffix": f["suffix"],
                    "size_bytes": f["size_bytes"],
                    "modified_time": f["modified_time"],
                    "modified_age_days": age,
                }],
                "file_count": 1,
                "total_size_bytes": f["size_bytes"],
                "oldest_modified_age_days": age,
                "newest_modified_age_days": age,
            })
            total_file_count += 1

    # --- Summary ---
    candidate_file_count = sum(c["file_count"] for c in candidates)
    candidate_total_bytes = sum(c["total_size_bytes"] for c in candidates)

    excluded_recent_count = (
        len(recent_audio) +
        len(recent_subtitle) +
        len(recent_temp)
    )
    excluded_running_count = (
        len(running_guard_audio) +
        len(running_guard_subtitle) +
        len(running_guard_temp)
    )
    # Direct count: files on disk not in DB references
    excluded_db_count = (
        len(db_referenced_audio) +
        len(db_referenced_subtitle)
    )
    excluded_unpaired_count = len(unpaired_subtitles)

    report = {
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now().isoformat(),
        "mode": "dry-run",
        "storage_root": "<REDACTED>",
        "kind": kind,
        "min_age_days": min_age_days,
        "max_files": max_files,
        "protection": {
            "standard_running_statuses": sorted(STANDARD_RUNNING_JOB_STATUSES),
            "extended_running_statuses": sorted(EXTENDED_RUNNING_JOB_STATUSES),
            "running_like_job_count": len(running_like_jobs),
            "running_like_status_distribution": running_like_status_dist,
            "protection_window_hours": RUNNING_PROTECTION_WINDOW_HOURS,
            "protection_age_days": protection_age_days,
            "db_referenced_files_excluded": True,
            "quarantine_excluded": True,
            "subtitle_pair_required": True,
        },
        "summary": {
            "candidate_file_count": candidate_file_count,
            "candidate_group_count": len(candidates),
            "candidate_total_bytes": candidate_total_bytes,
            "excluded_recent_count": excluded_recent_count,
            "excluded_db_referenced_count": excluded_db_count,
            "excluded_running_guard_count": excluded_running_count,
            "excluded_unpaired_subtitle_count": excluded_unpaired_count,
            "truncated": truncated,
            "truncated_reason": "max_files reached" if truncated else None,
            "total_eligible_file_count": total_eligible_file_count,
        },
        "candidates": candidates,
        "excluded": {
            "recent_files": {
                "count": excluded_recent_count,
                "note": f"Files younger than {min_age_days} days",
            },
            "db_referenced_files": {
                "count": excluded_db_count,
                "note": "Files referenced by AudioAsset or SubtitleAsset",
            },
            "running_guard_files": {
                "count": excluded_running_count,
                "note": f"Files within {protection_age_days} days (72h window) of a running-like job",
            },
            "unpaired_subtitle_files": {
                "count": excluded_unpaired_count,
                "note": "Orphan subtitle files without a json+srt pair",
            },
            "quarantine_files": {
                "count": 0,
                "note": "storage/quarantine is always excluded",
            },
        },
        "notices": [
            "Dry-run only. No files were deleted, moved, or modified.",
            "Orphan files are candidates only and may have backfill value.",
            "Subtitle candidates require both .json and .srt to be present as a pair.",
        ],
    }

    # --- Write output ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Console summary ---
    print("Asset cleanup dry-run completed.")
    print(f"  Mode: dry-run")
    print(f"  Kind: {kind}")
    print(f"  Min age days: {min_age_days}")
    print(f"  Candidates: {len(candidates)} groups / {candidate_file_count} files")
    print(f"  Candidate bytes: {candidate_total_bytes}")
    print(f"  Excluded recent: {excluded_recent_count}")
    print(f"  Excluded DB referenced: {excluded_db_count}")
    print(f"  Excluded running guard: {excluded_running_count}")
    print(f"  Excluded unpaired subtitles: {excluded_unpaired_count}")
    print(f"  Truncated: {truncated}")
    print(f"  Report: {output_path}")
    print("No files were deleted, moved, or modified.")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="P8-BE3C Asset cleanup dry-run planner (read-only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script generates a read-only cleanup plan.
It does NOT delete, move, or modify any files or database records.
Examples:
  python scripts/cleanup_assets.py --dry-run --kind orphan
  python scripts/cleanup_assets.py --dry-run --kind orphan --min-age-days 7 --max-files 1000
  python scripts/cleanup_assets.py --dry-run --kind orphan-audio --min-age-days 30
  python scripts/cleanup_assets.py --dry-run --kind temp --min-age-days 1
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Generate dry-run plan (required)",
    )
    parser.add_argument(
        "--kind",
        default=DEFAULT_KIND,
        choices=list(VALID_KINDS),
        help=f"Cleanup kind (default: {DEFAULT_KIND})",
    )
    parser.add_argument(
        "--min-age-days",
        type=int,
        default=DEFAULT_MIN_AGE_DAYS,
        help=f"Minimum file age in days (default: {DEFAULT_MIN_AGE_DAYS})",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=MAX_DEFAULT_FILES,
        help=f"Maximum candidate files to include (default: {MAX_DEFAULT_FILES})",
    )
    parser.add_argument(
        "--output",
        default="docs/generated/asset_cleanup_dry_run.json",
        help="Output JSON path (default: docs/generated/asset_cleanup_dry_run.json)",
    )
    parser.add_argument(
        "--storage-dir",
        default=None,
        help="Storage root directory (default: from app config)",
    )

    # Refuse any execute/mode/confirm arguments
    forbidden_args = [
        "--execute", "--mode", "--quarantine", "--restore",
        "--purge-quarantine", "--confirm",
    ]
    for arg in sys.argv[1:]:
        if arg in forbidden_args:
            parser.error(f"{arg} is not supported in dry-run mode")

    args = parser.parse_args()

    # Suppress noisy logs
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    run_dry_run(
        kind=args.kind,
        min_age_days=args.min_age_days,
        max_files=args.max_files,
        output_path=args.output,
        storage_dir=args.storage_dir,
    )


if __name__ == "__main__":
    main()

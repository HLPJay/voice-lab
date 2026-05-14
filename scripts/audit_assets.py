#!/usr/bin/env python3
"""
P8-BE3A2: Hardened read-only asset audit script.

Additions over P8-BE3A1:
  - pending added to running-like statuses (standard: queued/pending/running/processing)
  - protected listed separately as extended status
  - storage_dirs with per-directory file counts and bytes
  - content_file_count / all_scanned_file_count distinguish content vs all scanned
  - temp / metadata age and size distributions
  - largest_storage_files for temp and metadata
  - safe_path_str hardened: outside root paths return <OUTSIDE_STORAGE_ROOT>/<filename>
  - orphan_subtitle_pair_analysis added
  - report_privacy_check added
  - policy_readiness_check added
  - report_version: "p8-be3a2"

No deletions are performed. Output: docs/generated/asset_audit_report.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.database import engine
from app.models.voice_asset import AudioAsset, SubtitleAsset
from app.models.voice_job import VoiceJob

MAX_ITEMS = 200  # Max items per list in report to avoid bloat
MAX_LARGEST = 50  # Max entries in largest_orphan_files per category
EXCLUDED_STORAGE_DIRS = {"quarantine"}  # dirs to skip in storage scan
AGE_BUCKETS = ["0-1d", "1-7d", "7-30d", "30-90d", "90d+"]
SIZE_BUCKETS = ["0B", "<10KB", "10KB-1MB", "1MB-10MB", "10MB+"]
# Standard running-like job statuses (active / not finished)
STANDARD_RUNNING_JOB_STATUSES = {"queued", "pending", "running", "processing"}
# Extended statuses that are non-standard but still indicate active state
EXTENDED_RUNNING_JOB_STATUSES = {"protected"}
RUNNING_JOB_STATUSES = STANDARD_RUNNING_JOB_STATUSES | EXTENDED_RUNNING_JOB_STATUSES


def safe_path_str(path: str | None, root: Path) -> str | None:
    """Return a safe relative path string, or <OUTSIDE_STORAGE_ROOT>/<filename> if outside root."""
    if not path:
        return None
    try:
        p = Path(path)
        if p.is_absolute():
            try:
                return str(p.relative_to(root.resolve()))
            except Exception:
                # Do not return absolute paths outside storage root
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
        return {
            "relative_path": safe_path_str(str(full_path), root),
            "suffix": full_path.suffix,
            "size_bytes": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "modified_age_days": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days,
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
    """Return the age bucket label for a given age in days."""
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
    """Return the size bucket label for a given file size in bytes."""
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


def build_distribution(items: list[dict]) -> dict[str, int]:
    """Build a distribution dict from a list of file info dicts."""
    return dict(Counter(item.get("bucket", "unknown") for item in items))


def file_info_summary(files: list[dict]) -> dict[str, Any]:
    """Return a summary dict for a list of file info dicts."""
    return {
        "file_count": len(files),
        "total_bytes": sum(f["size_bytes"] for f in files),
    }


def build_subtitle_pair_analysis(subtitle_files: list[dict]) -> dict[str, Any]:
    """Group subtitle files by base name within the same date directory."""
    by_dir_and_base: dict[str, dict[str, str]] = {}
    for f in subtitle_files:
        rp = f["relative_path"]
        p = Path(rp)
        if len(p.parts) >= 2:
            subdir = p.parts[0]
            date_part = p.parts[1] if len(p.parts) > 1 else ""
            base = p.stem
            key = f"{subdir}/{date_part}/{base}"
            ext = p.suffix.lower()
            if key not in by_dir_and_base:
                by_dir_and_base[key] = {}
            if ext in (".json", ".srt"):
                by_dir_and_base[key][ext] = rp

    paired = []
    json_only = []
    srt_only = []
    for base, files in by_dir_and_base.items():
        has_json = ".json" in files
        has_srt = ".srt" in files
        if has_json and has_srt:
            paired.append({"base": base, "json_path": files[".json"], "srt_path": files[".srt"]})
        elif has_json:
            json_only.append({"base": base, "json_path": files[".json"]})
        elif has_srt:
            srt_only.append({"base": base, "srt_path": files[".srt"]})

    return {
        "paired_json_and_srt": len(paired),
        "json_only_no_srt": len(json_only),
        "srt_only_no_json": len(srt_only),
        "paired_samples": paired[:10],
        "json_only_samples": json_only[:10],
        "srt_only_samples": srt_only[:10],
    }


def run_audit(storage_dir: str | None, output_path: str | None) -> dict[str, Any]:
    root = Path(storage_dir) if storage_dir else Path(get_settings().storage_dir)
    output_path = Path(output_path) if output_path else Path("docs/generated/asset_audit_report.json")

    # Ensure output parent dir exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- DB scan ---
    with Session(engine) as session:
        audio_assets = list(session.exec(select(AudioAsset)).all())
        subtitle_assets = list(session.exec(select(SubtitleAsset)).all())
        voice_jobs = list(session.exec(select(VoiceJob)).all())

    # Build lookup maps
    job_by_id = {j.id: j for j in voice_jobs}
    audio_by_id = {a.id: a for a in audio_assets}
    subtitle_by_id = {s.id: s for s in subtitle_assets}

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

    all_db_file_paths = audio_file_paths_db | subtitle_file_paths_db | subtitle_srt_paths_db

    # --- Storage scan (excluding quarantine) ---
    audio_files = scan_storage_directory(root, "audio")
    subtitle_files = scan_storage_directory(root, "subtitles")
    temp_files = scan_storage_directory(root, "temp")
    metadata_files = scan_storage_directory(root, "metadata")

    audio_file_disk: set[str] = set()
    subtitle_file_disk: set[str] = set()

    for f in audio_files:
        full = root / f["relative_path"]
        audio_file_disk.add(str(full.resolve()))

    for f in subtitle_files:
        full = root / f["relative_path"]
        subtitle_file_disk.add(str(full.resolve()))

    all_disk_paths = audio_file_disk | subtitle_file_disk

    # --- Stats ---
    job_status_counts = dict(Counter(j.status for j in voice_jobs))

    audio_file_count = len(audio_files)
    subtitle_file_count = len(subtitle_files)
    temp_file_count = len(temp_files)
    metadata_file_count = len(metadata_files)

    audio_total_bytes = sum(f["size_bytes"] for f in audio_files)
    subtitle_total_bytes = sum(f["size_bytes"] for f in subtitle_files)
    temp_total_bytes = sum(f["size_bytes"] for f in temp_files)
    metadata_total_bytes = sum(f["size_bytes"] for f in metadata_files)

    # content = audio + subtitles; all_scanned = audio + subtitles + temp + metadata
    content_file_count = audio_file_count + subtitle_file_count
    content_total_bytes = audio_total_bytes + subtitle_total_bytes
    all_scanned_file_count = content_file_count + temp_file_count + metadata_file_count
    all_scanned_total_bytes = content_total_bytes + temp_total_bytes + metadata_total_bytes

    # Legacy field for backwards compatibility
    storage_file_count = content_file_count
    storage_total_bytes = content_total_bytes

    # Per-directory summary
    storage_dirs = {
        "audio": {"file_count": audio_file_count, "total_bytes": audio_total_bytes},
        "subtitles": {"file_count": subtitle_file_count, "total_bytes": subtitle_total_bytes},
        "temp": {"file_count": temp_file_count, "total_bytes": temp_total_bytes},
        "metadata": {"file_count": metadata_file_count, "total_bytes": metadata_total_bytes},
    }

    # --- Asset file existence ---
    audio_with_file = sum(1 for a in audio_assets if a.file_path and Path(a.file_path).exists())
    audio_missing_file = sum(1 for a in audio_assets if a.file_path and not Path(a.file_path).exists())
    subtitle_with_file = sum(
        1 for s in subtitle_assets
        if (s.file_path and Path(s.file_path).exists()) or (s.srt_path and Path(s.srt_path).exists())
    )
    subtitle_missing_file = sum(
        1 for s in subtitle_assets
        if s.file_path and not Path(s.file_path).exists()
    )

    # --- Orphan files (on disk, not referenced by DB) ---
    orphan_audio = []
    for f in audio_files:
        full = root / f["relative_path"]
        if str(full.resolve()) not in audio_file_paths_db:
            orphan_audio.append(f)
    orphan_audio_truncated = len(orphan_audio) > MAX_ITEMS
    orphan_audio_limited = orphan_audio[:MAX_ITEMS]

    orphan_subtitle = []
    for f in subtitle_files:
        full = root / f["relative_path"]
        if str(full.resolve()) not in subtitle_file_paths_db and str(full.resolve()) not in subtitle_srt_paths_db:
            orphan_subtitle.append(f)
    orphan_subtitle_truncated = len(orphan_subtitle) > MAX_ITEMS
    orphan_subtitle_limited = orphan_subtitle[:MAX_ITEMS]

    # --- Orphan DB records (missing job) ---
    orphan_audio_db = []
    for a in audio_assets:
        if a.job_id and a.job_id not in job_by_id:
            orphan_audio_db.append({
                "audio_asset_id": a.id,
                "job_id": a.job_id,
                "file_path": safe_path_str(a.file_path, root),
            })
    orphan_audio_db_truncated = len(orphan_audio_db) > MAX_ITEMS
    orphan_audio_db_limited = orphan_audio_db[:MAX_ITEMS]

    orphan_subtitle_db = []
    for s in subtitle_assets:
        if s.job_id and s.job_id not in job_by_id:
            orphan_subtitle_db.append({
                "subtitle_asset_id": s.id,
                "job_id": s.job_id,
                "file_path": safe_path_str(s.file_path, root),
                "srt_path": safe_path_str(s.srt_path, root),
            })
    orphan_subtitle_db_truncated = len(orphan_subtitle_db) > MAX_ITEMS
    orphan_subtitle_db_limited = orphan_subtitle_db[:MAX_ITEMS]

    # --- Deleted job assets ---
    deleted_audio = []
    deleted_subtitle = []
    for a in audio_assets:
        if a.job_id and a.job_id in job_by_id and job_by_id[a.job_id].status == "deleted":
            deleted_audio.append({
                "audio_asset_id": a.id,
                "job_id": a.job_id,
                "file_path": safe_path_str(a.file_path, root),
                "file_exists": Path(a.file_path).exists() if a.file_path else False,
            })
    deleted_audio_truncated = len(deleted_audio) > MAX_ITEMS
    deleted_audio_limited = deleted_audio[:MAX_ITEMS]

    for s in subtitle_assets:
        if s.job_id and s.job_id in job_by_id and job_by_id[s.job_id].status == "deleted":
            deleted_subtitle.append({
                "subtitle_asset_id": s.id,
                "job_id": s.job_id,
                "file_path": safe_path_str(s.file_path, root),
                "srt_path": safe_path_str(s.srt_path, root),
                "file_exists": (Path(s.file_path).exists() if s.file_path else False),
                "srt_exists": (Path(s.srt_path).exists() if s.srt_path else False),
            })
    deleted_subtitle_truncated = len(deleted_subtitle) > MAX_ITEMS
    deleted_subtitle_limited = deleted_subtitle[:MAX_ITEMS]

    # --- Missing file DB records ---
    missing_file_audio = []
    for a in audio_assets:
        if a.file_path and not Path(a.file_path).exists():
            missing_file_audio.append({
                "audio_asset_id": a.id,
                "job_id": a.job_id,
                "file_path": safe_path_str(a.file_path, root),
            })
    missing_file_audio_truncated = len(missing_file_audio) > MAX_ITEMS
    missing_file_audio_limited = missing_file_audio[:MAX_ITEMS]

    missing_file_subtitle = []
    for s in subtitle_assets:
        if s.file_path and not Path(s.file_path).exists():
            missing_file_subtitle.append({
                "subtitle_asset_id": s.id,
                "job_id": s.job_id,
                "file_path": safe_path_str(s.file_path, root),
            })
    missing_file_subtitle_truncated = len(missing_file_subtitle) > MAX_ITEMS
    missing_file_subtitle_limited = missing_file_subtitle[:MAX_ITEMS]

    # --- Age distributions ---
    def tag_age_bucket(files: list[dict]) -> list[dict]:
        for f in files:
            f["bucket"] = age_bucket(f["modified_age_days"])
        return files

    orphan_audio_age_dist = build_distribution(tag_age_bucket([f.copy() for f in orphan_audio]))
    orphan_subtitle_age_dist = build_distribution(tag_age_bucket([f.copy() for f in orphan_subtitle]))
    temp_age_dist = build_distribution(tag_age_bucket([f.copy() for f in temp_files]))
    metadata_age_dist = build_distribution(tag_age_bucket([f.copy() for f in metadata_files]))

    # --- Size distributions ---
    def tag_size_bucket(files: list[dict]) -> list[dict]:
        for f in files:
            f["bucket"] = size_bucket(f["size_bytes"])
        return files

    orphan_audio_size_dist = build_distribution(tag_size_bucket([f.copy() for f in orphan_audio]))
    orphan_subtitle_size_dist = build_distribution(tag_size_bucket([f.copy() for f in orphan_subtitle]))
    temp_size_dist = build_distribution(tag_size_bucket([f.copy() for f in temp_files]))
    metadata_size_dist = build_distribution(tag_size_bucket([f.copy() for f in metadata_files]))

    # --- Largest orphan files ---
    def largest_items(files: list[dict]) -> list[dict]:
        return [
            {
                "relative_path": f["relative_path"],
                "size_bytes": f["size_bytes"],
                "modified_time": f["modified_time"],
                "modified_age_days": f["modified_age_days"],
            }
            for f in sorted(files, key=lambda x: x["size_bytes"], reverse=True)[:MAX_LARGEST]
        ]

    largest_orphan_audio = largest_items(orphan_audio)
    largest_orphan_subtitle = largest_items(orphan_subtitle)

    # --- Largest temp / metadata files ---
    largest_temp = largest_items(temp_files)
    largest_metadata = largest_items(metadata_files)

    # --- All subtitle pair analysis (all subtitle files on disk) ---
    all_subtitle_pair_analysis = build_subtitle_pair_analysis(subtitle_files)

    # --- Orphan subtitle pair analysis (only orphan subtitle files) ---
    orphan_subtitle_pair_analysis = build_subtitle_pair_analysis(orphan_subtitle)

    # --- Running job guard ---
    running_jobs = [j for j in voice_jobs if j.status in RUNNING_JOB_STATUSES]
    running_like_jobs = [j for j in voice_jobs if j.status in STANDARD_RUNNING_JOB_STATUSES]
    running_job_ids = {j.id for j in running_jobs}
    running_like_job_ids = {j.id for j in running_like_jobs}
    running_job_status_dist = dict(Counter(j.status for j in running_jobs))
    running_like_status_dist = dict(Counter(j.status for j in running_like_jobs))

    # Assets linked to running jobs (protected from cleanup)
    protected_audio = [a for a in audio_assets if a.job_id in running_job_ids]
    protected_subtitle = [s for s in subtitle_assets if s.job_id in running_job_ids]

    # --- Policy readiness check ---
    has_recent_orphan = (
        orphan_audio_age_dist.get("0-1d", 0) > 0
        or orphan_audio_age_dist.get("1-7d", 0) > 0
        or orphan_subtitle_age_dist.get("0-1d", 0) > 0
        or orphan_subtitle_age_dist.get("1-7d", 0) > 0
    )
    has_large_orphan = len(orphan_audio) > 0 or len(orphan_subtitle) > 0
    has_deleted_job_assets = len(deleted_audio) > 0 or len(deleted_subtitle) > 0
    has_missing_db_records = len(missing_file_audio) > 0 or len(missing_file_subtitle) > 0

    policy_readiness_check = {
        "has_running_like_jobs": len(running_like_jobs) > 0,
        "has_recent_orphan_files": has_recent_orphan,
        "has_temp_files": temp_file_count > 0,
        "has_metadata_files": metadata_file_count > 0,
        "has_missing_db_records": has_missing_db_records,
        "has_deleted_job_assets": has_deleted_job_assets,
        "has_large_orphan_files": has_large_orphan,
        "orphan_should_not_be_deleted_directly": True,
        "recommended_next_stage": "P8-BE3B asset cleanup policy confirmation",
    }

    # --- Report privacy check ---
    report_privacy_check = {
        "storage_root_redacted": True,
        "absolute_path_output_allowed": False,
        "contains_audio_content": False,
        "safe_path_policy": (
            "relative paths under storage root; outside paths redacted as <OUTSIDE_STORAGE_ROOT>/<filename>; "
            "invalid paths redacted as <INVALID_PATH>"
        ),
    }

    # --- Build report ---
    report = {
        "generated_at": datetime.now().isoformat(),
        "storage_root": "<REDACTED>",
        "report_version": "p8-be3a2",
        "summary": {
            "audio_asset_count": len(audio_assets),
            "subtitle_asset_count": len(subtitle_assets),
            "voice_job_count": len(voice_jobs),
            "job_status_counts": job_status_counts,
            # Legacy aliases (content = audio + subtitles only)
            "storage_file_count": storage_file_count,
            "storage_total_bytes": storage_total_bytes,
            "audio_file_count": audio_file_count,
            "audio_total_bytes": audio_total_bytes,
            "subtitle_file_count": subtitle_file_count,
            "subtitle_total_bytes": subtitle_total_bytes,
            "temp_file_count": temp_file_count,
            "temp_total_bytes": temp_total_bytes,
            "metadata_file_count": metadata_file_count,
            "metadata_total_bytes": metadata_total_bytes,
            "excluded_storage_dirs": list(EXCLUDED_STORAGE_DIRS),
            # Explicit content vs all-scanned distinction
            "content_file_count": content_file_count,
            "content_total_bytes": content_total_bytes,
            "all_scanned_file_count": all_scanned_file_count,
            "all_scanned_total_bytes": all_scanned_total_bytes,
        },
        "storage_dirs": storage_dirs,
        "database_asset_file_existence": {
            "audio_assets_with_existing_file": audio_with_file,
            "audio_assets_missing_file": audio_missing_file,
            "subtitle_assets_with_existing_file": subtitle_with_file,
            "subtitle_assets_missing_file": subtitle_missing_file,
        },
        "orphan_files": {
            "audio_files_not_referenced_by_db": {
                "truncated": orphan_audio_truncated,
                "total": len(orphan_audio),
                "items": orphan_audio_limited,
            },
            "subtitle_files_not_referenced_by_db": {
                "truncated": orphan_subtitle_truncated,
                "total": len(orphan_subtitle),
                "items": orphan_subtitle_limited,
            },
        },
        "orphan_db_records": {
            "audio_assets_with_missing_job": {
                "truncated": orphan_audio_db_truncated,
                "total": len(orphan_audio_db),
                "items": orphan_audio_db_limited,
            },
            "subtitle_assets_with_missing_job": {
                "truncated": orphan_subtitle_db_truncated,
                "total": len(orphan_subtitle_db),
                "items": orphan_subtitle_db_limited,
            },
        },
        "deleted_job_assets": {
            "audio_assets_for_deleted_jobs": {
                "truncated": deleted_audio_truncated,
                "total": len(deleted_audio),
                "items": deleted_audio_limited,
            },
            "subtitle_assets_for_deleted_jobs": {
                "truncated": deleted_subtitle_truncated,
                "total": len(deleted_subtitle),
                "items": deleted_subtitle_limited,
            },
        },
        "age_distribution": {
            "buckets": AGE_BUCKETS,
            "orphan_audio_files": orphan_audio_age_dist,
            "orphan_subtitle_files": orphan_subtitle_age_dist,
            "temp_files": temp_age_dist,
            "metadata_files": metadata_age_dist,
        },
        "size_distribution": {
            "buckets": SIZE_BUCKETS,
            "orphan_audio_files": orphan_audio_size_dist,
            "orphan_subtitle_files": orphan_subtitle_size_dist,
            "temp_files": temp_size_dist,
            "metadata_files": metadata_size_dist,
        },
        "largest_orphan_files": {
            "audio": {
                "total": len(orphan_audio),
                "returned": len(largest_orphan_audio),
                "items": largest_orphan_audio,
            },
            "subtitle": {
                "total": len(orphan_subtitle),
                "returned": len(largest_orphan_subtitle),
                "items": largest_orphan_subtitle,
            },
        },
        "largest_storage_files": {
            "temp": {
                "total": temp_file_count,
                "returned": len(largest_temp),
                "items": largest_temp,
            },
            "metadata": {
                "total": metadata_file_count,
                "returned": len(largest_metadata),
                "items": largest_metadata,
            },
        },
        "subtitle_pair_analysis": all_subtitle_pair_analysis,
        "orphan_subtitle_pair_analysis": orphan_subtitle_pair_analysis,
        "running_job_guard": {
            "standard_running_statuses": list(STANDARD_RUNNING_JOB_STATUSES),
            "extended_running_statuses": list(EXTENDED_RUNNING_JOB_STATUSES),
            "note": (
                "Assets linked to jobs with standard running-like statuses are protected. "
                "Cleanup tools should re-check job status before execution."
            ),
            "recommended_protection_window_hours": 72,
            "running_like_job_count": len(running_like_jobs),
            "running_like_status_distribution": running_like_status_dist,
            "all_running_job_count": len(running_jobs),
            "all_running_status_distribution": running_job_status_dist,
            "protected_audio_asset_count": len(protected_audio),
            "protected_subtitle_asset_count": len(protected_subtitle),
        },
        "cleanup_candidates_readonly": {
            "note": (
                "These are candidates only. This report does not delete anything. "
                "Orphan files are NOT safe to delete directly — they may have backfill value "
                "or belong to jobs that will be referenced in the future."
            ),
            "not_deletion_recommendation": (
                "Orphan files are files on disk that are not referenced by current database records. "
                "They are NOT automatically deletable. Possible origins: early test files, "
                "provider-side files not recorded in DB, or files from jobs whose records were "
                "manually deleted. Before deleting any orphan file, verify it is not needed "
                "for record reconstruction or backfill."
            ),
            "missing_file_db_records": {
                "audio_assets": {
                    "truncated": missing_file_audio_truncated,
                    "total": len(missing_file_audio),
                    "items": missing_file_audio_limited,
                },
                "subtitle_assets": {
                    "truncated": missing_file_subtitle_truncated,
                    "total": len(missing_file_subtitle),
                    "items": missing_file_subtitle_limited,
                },
            },
            "orphan_storage_files": {
                "audio": {
                    "truncated": orphan_audio_truncated,
                    "total": len(orphan_audio),
                    "items": orphan_audio_limited,
                },
                "subtitle": {
                    "truncated": orphan_subtitle_truncated,
                    "total": len(orphan_subtitle),
                    "items": orphan_subtitle_limited,
                },
            },
            "deleted_job_assets": {
                "audio": {
                    "truncated": deleted_audio_truncated,
                    "total": len(deleted_audio),
                    "items": deleted_audio_limited,
                },
                "subtitle": {
                    "truncated": deleted_subtitle_truncated,
                    "total": len(deleted_subtitle),
                    "items": deleted_subtitle_limited,
                },
            },
        },
        "backfill_candidates_note": (
            "Orphan files discovered in this audit may be used to backfill missing DB records "
            "if the files can be matched to jobs via filename or metadata. "
            "Before deleting any orphan file, verify it is not needed for record reconstruction."
        ),
        "report_privacy_check": report_privacy_check,
        "policy_readiness_check": policy_readiness_check,
    }

    # --- Write report ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Console summary ---
    print("Asset audit (p8-be3a2) completed.")
    print(f"  AudioAsset: {len(audio_assets)}")
    print(f"  SubtitleAsset: {len(subtitle_assets)}")
    print(f"  VoiceJob: {len(voice_jobs)}")
    print(f"  Content files (audio+subtitles): {content_file_count}")
    print(f"  All scanned files: {all_scanned_file_count}")
    print(f"  Orphan audio: {len(orphan_audio)}")
    print(f"  Orphan subtitle: {len(orphan_subtitle)}")
    print(f"  Missing file DB records (audio): {len(missing_file_audio)}")
    print(f"  Missing file DB records (subtitle): {len(missing_file_subtitle)}")
    print(f"  Deleted job audio assets: {len(deleted_audio)}")
    print(f"  Deleted job subtitle assets: {len(deleted_subtitle)}")
    print(f"  Running-like jobs (standard): {len(running_like_jobs)}")
    print(f"  Running jobs (all): {len(running_jobs)}")
    print(f"  Protected audio assets: {len(protected_audio)}")
    print(f"  Protected subtitle assets: {len(protected_subtitle)}")
    print(f"  Orphan subtitle pairs: {orphan_subtitle_pair_analysis['paired_json_and_srt']}")
    print(f"  All subtitle pairs: {all_subtitle_pair_analysis['paired_json_and_srt']}")
    print(f"  Policy readiness: {policy_readiness_check}")
    print(f"  Report: {output_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="P8-BE3A2 Hardened read-only asset audit script")
    parser.add_argument(
        "--output",
        default="docs/generated/asset_audit_report.json",
        help="Output JSON report path (default: docs/generated/asset_audit_report.json)",
    )
    parser.add_argument(
        "--storage-dir",
        default=None,
        help="Storage root directory (default: from app config)",
    )
    args = parser.parse_args()

    # Suppress noisy logs from other modules
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    run_audit(storage_dir=args.storage_dir, output_path=args.output)


if __name__ == "__main__":
    main()

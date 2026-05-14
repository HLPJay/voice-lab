#!/usr/bin/env python3
"""
P8-BE3A1: Enhanced read-only asset audit script.

Additions over P8-BE3A:
  - storage_root redacted to "<REDACTED>" in JSON output
  - Excludes quarantine/ from storage scanning
  - temp and metadata subdirectory statistics
  - Age distribution buckets (0-1d, 1-7d, 7-30d, 30-90d, 90d+)
  - Size distribution buckets (0B, <10KB, 10KB-1MB, 1MB-10MB, 10MB+)
  - Largest orphan files (top 50 per category)
  - Subtitle pair analysis (json/srt pairing)
  - Running job guard (running/queued/processing/protected statuses)
  - Backfill candidates note
  - report_version: "p8-be3a1"

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
# Job statuses that indicate a running/active job — these assets are protected
RUNNING_JOB_STATUSES = {"running", "queued", "processing", "protected"}


def safe_path_str(path: str | None, root: Path) -> str | None:
    """Return a safe relative path string, or the original if not relative to root."""
    if not path:
        return None
    try:
        p = Path(path)
        if p.is_absolute():
            try:
                return str(p.relative_to(root.resolve()))
            except Exception:
                return str(p)
        return str(p)
    except Exception:
        return str(path)


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

    # Also scan temp and metadata for stats even though they may not have orphan logic
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

    storage_file_count = len(audio_files) + len(subtitle_files)
    storage_total_bytes = sum(f["size_bytes"] for f in audio_files) + sum(f["size_bytes"] for f in subtitle_files)
    audio_total_bytes = sum(f["size_bytes"] for f in audio_files)
    subtitle_total_bytes = sum(f["size_bytes"] for f in subtitle_files)
    temp_file_count = len(temp_files)
    temp_total_bytes = sum(f["size_bytes"] for f in temp_files)
    metadata_file_count = len(metadata_files)
    metadata_total_bytes = sum(f["size_bytes"] for f in metadata_files)

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
            f["bucket"] = age_bucket(f["modified_age_days"])
            orphan_audio.append(f)
    orphan_audio_truncated = len(orphan_audio) > MAX_ITEMS
    orphan_audio_limited = orphan_audio[:MAX_ITEMS]

    orphan_subtitle = []
    for f in subtitle_files:
        full = root / f["relative_path"]
        if str(full.resolve()) not in subtitle_file_paths_db and str(full.resolve()) not in subtitle_srt_paths_db:
            f["bucket"] = age_bucket(f["modified_age_days"])
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
    def age_dist_items(files: list[dict]) -> list[dict]:
        for f in files:
            f["bucket"] = age_bucket(f["modified_age_days"])
        return files

    orphan_audio_age_dist = build_distribution(age_dist_items([f.copy() for f in orphan_audio]))
    orphan_subtitle_age_dist = build_distribution(age_dist_items([f.copy() for f in orphan_subtitle]))

    # --- Size distributions ---
    def size_dist_items(files: list[dict]) -> list[dict]:
        for f in files:
            f["bucket"] = size_bucket(f["size_bytes"])
        return files

    orphan_audio_size_dist = build_distribution(size_dist_items([f.copy() for f in orphan_audio]))
    orphan_subtitle_size_dist = build_distribution(size_dist_items([f.copy() for f in orphan_subtitle]))

    # --- Largest orphan files (top 50 per category) ---
    orphan_audio_sorted = sorted(orphan_audio, key=lambda x: x["size_bytes"], reverse=True)
    orphan_subtitle_sorted = sorted(orphan_subtitle, key=lambda x: x["size_bytes"], reverse=True)

    largest_orphan_audio = [
        {
            "relative_path": f["relative_path"],
            "size_bytes": f["size_bytes"],
            "modified_time": f["modified_time"],
            "modified_age_days": f["modified_age_days"],
        }
        for f in orphan_audio_sorted[:MAX_LARGEST]
    ]
    largest_orphan_subtitle = [
        {
            "relative_path": f["relative_path"],
            "size_bytes": f["size_bytes"],
            "modified_time": f["modified_time"],
            "modified_age_days": f["modified_age_days"],
        }
        for f in orphan_subtitle_sorted[:MAX_LARGEST]
    ]

    # --- Subtitle pair analysis ---
    # Group subtitle files by base name (without extension) within the same date directory
    subtitle_by_dir_and_base: dict[str, dict[str, str]] = {}
    for f in subtitle_files:
        rp = f["relative_path"]
        p = Path(rp)
        # e.g. storage/subtitles/2025-01-15/abc123.json -> (subdir, base=abc123)
        if len(p.parts) >= 2:
            subdir = p.parts[0]  # "subtitles"
            date_part = p.parts[1] if len(p.parts) > 1 else ""  # "2025-01-15"
            base = p.stem  # "abc123"
            key = f"{subdir}/{date_part}/{base}"
            ext = p.suffix.lower()
            if key not in subtitle_by_dir_and_base:
                subtitle_by_dir_and_base[key] = {}
            if ext in (".json", ".srt"):
                subtitle_by_dir_and_base[key][ext] = rp

    subtitle_pairs = []
    subtitle_json_only = []
    subtitle_srt_only = []
    for base, files in subtitle_by_dir_and_base.items():
        has_json = ".json" in files
        has_srt = ".srt" in files
        if has_json and has_srt:
            subtitle_pairs.append({
                "base": base,
                "json_path": files[".json"],
                "srt_path": files[".srt"],
            })
        elif has_json:
            subtitle_json_only.append({"base": base, "json_path": files[".json"]})
        elif has_srt:
            subtitle_srt_only.append({"base": base, "srt_path": files[".srt"]})

    subtitle_pair_analysis = {
        "paired_json_and_srt": len(subtitle_pairs),
        "json_only_no_srt": len(subtitle_json_only),
        "srt_only_no_json": len(subtitle_srt_only),
        "paired_samples": subtitle_pairs[:10],
        "json_only_samples": subtitle_json_only[:10],
        "srt_only_samples": subtitle_srt_only[:10],
    }

    # --- Running job guard ---
    running_jobs = [j for j in voice_jobs if j.status in RUNNING_JOB_STATUSES]
    running_job_ids = {j.id for j in running_jobs}
    running_job_status_dist = dict(Counter(j.status for j in running_jobs))

    # Assets linked to running jobs (protected from cleanup)
    protected_audio = [a for a in audio_assets if a.job_id in running_job_ids]
    protected_subtitle = [s for s in subtitle_assets if s.job_id in running_job_ids]

    # --- Build report ---
    report = {
        "generated_at": datetime.now().isoformat(),
        "storage_root": "<REDACTED>",
        "report_version": "p8-be3a1",
        "summary": {
            "audio_asset_count": len(audio_assets),
            "subtitle_asset_count": len(subtitle_assets),
            "voice_job_count": len(voice_jobs),
            "job_status_counts": job_status_counts,
            "storage_file_count": storage_file_count,
            "storage_total_bytes": storage_total_bytes,
            "audio_file_count": len(audio_files),
            "audio_total_bytes": audio_total_bytes,
            "subtitle_file_count": len(subtitle_files),
            "subtitle_total_bytes": subtitle_total_bytes,
            "temp_file_count": temp_file_count,
            "temp_total_bytes": temp_total_bytes,
            "metadata_file_count": metadata_file_count,
            "metadata_total_bytes": metadata_total_bytes,
            "excluded_storage_dirs": list(EXCLUDED_STORAGE_DIRS),
        },
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
        },
        "size_distribution": {
            "buckets": SIZE_BUCKETS,
            "orphan_audio_files": orphan_audio_size_dist,
            "orphan_subtitle_files": orphan_subtitle_size_dist,
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
        "subtitle_pair_analysis": subtitle_pair_analysis,
        "running_job_guard": {
            "note": f"Assets linked to jobs with status in {RUNNING_JOB_STATUSES} are protected from cleanup",
            "running_job_count": len(running_jobs),
            "running_job_status_distribution": running_job_status_dist,
            "protected_audio_asset_count": len(protected_audio),
            "protected_subtitle_asset_count": len(protected_subtitle),
        },
        "cleanup_candidates_readonly": {
            "note": "These are candidates only. This report does not delete anything.",
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
    }

    # --- Write report ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Console summary ---
    print("Asset audit (p8-be3a1) completed.")
    print(f"  AudioAsset: {len(audio_assets)}")
    print(f"  SubtitleAsset: {len(subtitle_assets)}")
    print(f"  VoiceJob: {len(voice_jobs)}")
    print(f"  Storage files: {storage_file_count}")
    print(f"  Orphan audio files (not in DB): {len(orphan_audio)}")
    print(f"  Orphan subtitle files (not in DB): {len(orphan_subtitle)}")
    print(f"  Missing file DB records (audio): {len(missing_file_audio)}")
    print(f"  Missing file DB records (subtitle): {len(missing_file_subtitle)}")
    print(f"  Deleted job audio assets: {len(deleted_audio)}")
    print(f"  Deleted job subtitle assets: {len(deleted_subtitle)}")
    print(f"  Running job protected assets: {len(protected_audio)} audio, {len(protected_subtitle)} subtitle")
    print(f"  Subtitle pairs (json+srt): {subtitle_pair_analysis['paired_json_and_srt']}")
    print(f"  Report: {output_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="P8-BE3A1 Read-only asset audit script (enhanced)")
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

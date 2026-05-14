#!/usr/bin/env python3
"""
P8-BE3A: Asset cleanup audit script (read-only).

Scans the database and storage filesystem to produce a readonly report
containing:
  - AudioAsset / SubtitleAsset / VoiceJob counts and status distribution
  - Storage file counts and sizes
  - Orphan files (on disk, not referenced by DB)
  - Missing file records (DB records pointing to non-existent files)
  - Deleted-job assets (assets linked to status="deleted" jobs)

No deletions are performed. Output: docs/generated/asset_audit_report.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
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
        }
    except Exception:
        return None


def scan_storage_directory(root: Path, subdir: str) -> list[dict]:
    """Recursively scan a storage subdirectory and return file info list."""
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

    # --- Storage scan ---
    audio_files = scan_storage_directory(root, "audio")
    subtitle_files = scan_storage_directory(root, "subtitles")

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

    # --- Build report ---
    report = {
        "generated_at": datetime.now().isoformat(),
        "storage_root": str(root.resolve()),
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
    }

    # --- Write report ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Console summary ---
    print("Asset audit completed.")
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
    print(f"  Report: {output_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="P8-BE3A Read-only asset audit script")
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

#!/usr/bin/env python3
"""
P8-BE3D: Asset quarantine and restore tool.

Supports three modes:
  --dry-run   : Read-only plan generation (BE3C)
  --quarantine: Move plan candidates to storage/quarantine/<timestamp>/
  --restore   : Restore quarantined files to original locations

No permanent deletion. No database modification.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
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
MANIFEST_VERSION = "p8-be3d-quarantine"
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


# ---------------------------------------------------------------------------
# Shared DB helpers
# ---------------------------------------------------------------------------

def build_db_reference_sets() -> tuple[set[str], set[str], set[str]]:
    """Return (audio_paths, subtitle_paths, srt_paths) from current DB state."""
    with Session(engine) as session:
        audio_assets = list(session.exec(select(AudioAsset)).all())
        subtitle_assets = list(session.exec(select(SubtitleAsset)).all())

    audio_paths: set[str] = set()
    subtitle_paths: set[str] = set()
    srt_paths: set[str] = set()

    for a in audio_assets:
        if a.file_path:
            audio_paths.add(str(Path(a.file_path).resolve()))
    for s in subtitle_assets:
        if s.file_path:
            subtitle_paths.add(str(Path(s.file_path).resolve()))
        if s.srt_path:
            srt_paths.add(str(Path(s.srt_path).resolve()))

    return audio_paths, subtitle_paths, srt_paths


def is_db_referenced(path: str, audio_paths: set[str], subtitle_paths: set[str], srt_paths: set[str]) -> bool:
    """Return True if path is referenced by any DB asset."""
    return path in audio_paths or path in subtitle_paths or path in srt_paths


# ---------------------------------------------------------------------------
# Dry-run (BE3C logic — unchanged)
# ---------------------------------------------------------------------------

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
        voice_jobs = list(session.exec(select(VoiceJob)).all())

    audio_file_paths_db, subtitle_file_paths_db, subtitle_srt_paths_db = build_db_reference_sets()

    running_like_jobs = [j for j in voice_jobs if j.status in STANDARD_RUNNING_JOB_STATUSES]
    running_like_status_dist = dict(Counter(j.status for j in running_like_jobs))

    # --- Storage scan ---
    audio_files = scan_storage_directory(root, "audio")
    subtitle_files = scan_storage_directory(root, "subtitles")
    temp_files = scan_storage_directory(root, "temp")

    # Running protection threshold: 72 hours = 3 days
    protection_age_days = max(1, RUNNING_PROTECTION_WINDOW_HOURS // 24)

    # --- Classify every audio file on disk into exactly one bucket ---
    db_referenced_audio = []
    recent_audio = []
    running_guard_audio = []
    eligible_orphan_audio = []

    for f in audio_files:
        full_str = str((root / f["relative_path"]).resolve())
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
    db_referenced_subtitle = []
    recent_subtitle = []
    running_guard_subtitle = []
    eligible_orphan_subtitle = []

    for f in subtitle_files:
        full_str = str((root / f["relative_path"]).resolve())
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
        len(recent_audio) + len(recent_subtitle) + len(recent_temp)
    )
    excluded_running_count = (
        len(running_guard_audio) + len(running_guard_subtitle) + len(running_guard_temp)
    )
    excluded_db_count = len(db_referenced_audio) + len(db_referenced_subtitle)
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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

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


# ---------------------------------------------------------------------------
# Quarantine (BE3D)
# ---------------------------------------------------------------------------

def run_quarantine(
    plan_path: str,
    storage_dir: str | None,
) -> dict[str, Any]:
    """Execute quarantine based on a dry-run plan."""
    root = Path(storage_dir) if storage_dir else Path(get_settings().storage_dir)

    # --- Load and validate plan ---
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))

    if plan.get("report_version") != REPORT_VERSION:
        raise SystemExit(f"Unsupported plan version: {plan.get('report_version')}. Expected {REPORT_VERSION}.")
    if plan.get("mode") != "dry-run":
        raise SystemExit(f"Plan mode must be 'dry-run', got: {plan.get('mode')}")
    if "candidates" not in plan:
        raise SystemExit("Plan has no candidates field.")

    candidates = plan["candidates"]
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    q_dir = root / "quarantine" / timestamp

    # Build DB reference sets for re-validation
    audio_db, subtitle_db, srt_db = build_db_reference_sets()

    manifest_files: list[dict] = []
    moved_count = 0
    skipped_count = 0
    failed_count = 0
    moved_bytes = 0

    # --- Create quarantine subdirectories ---
    (q_dir / "audio").mkdir(parents=True, exist_ok=True)
    (q_dir / "subtitles").mkdir(parents=True, exist_ok=True)
    (q_dir / "temp").mkdir(parents=True, exist_ok=True)

    for cand in candidates:
        kind = cand.get("kind")
        cand_id = cand.get("candidate_id", "?")
        files = cand.get("files", [])

        for file_entry in files:
            rel_path = file_entry.get("relative_path", "")
            size_bytes = file_entry.get("size_bytes", 0)
            modified_time = file_entry.get("modified_time", "")

            # --- Path safety checks ---
            if Path(rel_path).is_absolute():
                manifest_files.append({
                    "candidate_id": cand_id,
                    "kind": kind,
                    "reason": cand.get("reason"),
                    "original_relative_path": rel_path,
                    "quarantine_relative_path": None,
                    "size_bytes": size_bytes,
                    "modified_time": modified_time,
                    "status": "failed",
                    "skip_reason": "absolute_path_not_allowed",
                    "error": "Absolute paths are not allowed",
                })
                failed_count += 1
                continue

            if ".." in rel_path or Path(rel_path).name != rel_path.split("/")[-1] and ".." in str(Path(rel_path).parts):
                manifest_files.append({
                    "candidate_id": cand_id,
                    "kind": kind,
                    "reason": cand.get("reason"),
                    "original_relative_path": rel_path,
                    "quarantine_relative_path": None,
                    "size_bytes": size_bytes,
                    "modified_time": modified_time,
                    "status": "failed",
                    "skip_reason": "path_traversal_not_allowed",
                    "error": "Path traversal (..) is not allowed",
                })
                failed_count += 1
                continue

            # --- Determine quarantine subdirectory ---
            first_part = rel_path.split("/")[0] if "/" in rel_path else ""
            if first_part == "audio":
                q_subdir = q_dir / "audio"
            elif first_part == "subtitles":
                q_subdir = q_dir / "subtitles"
            elif first_part == "temp":
                q_subdir = q_dir / "temp"
            else:
                q_subdir = q_dir / "audio"

            q_rel = str(q_subdir.relative_to(root)) + "/" + Path(rel_path).name
            q_full = q_dir / Path(rel_path).name

            # --- Avoid name collision ---
            if q_full.exists():
                base = Path(rel_path).stem
                ext = Path(rel_path).suffix
                q_full = q_subdir / f"{base}_{timestamp}{ext}"
                q_rel = str(q_full.relative_to(root))

            src_full = root / rel_path

            # --- File existence re-check ---
            if not src_full.exists():
                manifest_files.append({
                    "candidate_id": cand_id,
                    "kind": kind,
                    "reason": cand.get("reason"),
                    "original_relative_path": rel_path,
                    "quarantine_relative_path": q_rel,
                    "size_bytes": size_bytes,
                    "modified_time": modified_time,
                    "status": "skipped",
                    "skip_reason": "file_not_found",
                    "error": None,
                })
                skipped_count += 1
                continue

            # --- DB reference re-check ---
            src_str = str(src_full.resolve())
            if is_db_referenced(src_str, audio_db, subtitle_db, srt_db):
                manifest_files.append({
                    "candidate_id": cand_id,
                    "kind": kind,
                    "reason": cand.get("reason"),
                    "original_relative_path": rel_path,
                    "quarantine_relative_path": q_rel,
                    "size_bytes": size_bytes,
                    "modified_time": modified_time,
                    "status": "skipped",
                    "skip_reason": "db_referenced",
                    "error": "File became DB-referenced since plan was generated",
                })
                skipped_count += 1
                continue

            # --- Move file (copy, don't delete) ---
            try:
                shutil.copy2(src_full, q_full)
                manifest_files.append({
                    "candidate_id": cand_id,
                    "kind": kind,
                    "reason": cand.get("reason"),
                    "original_relative_path": rel_path,
                    "quarantine_relative_path": q_rel,
                    "size_bytes": size_bytes,
                    "modified_time": modified_time,
                    "status": "moved",
                    "skip_reason": None,
                    "error": None,
                })
                moved_count += 1
                moved_bytes += size_bytes
            except Exception as ex:
                manifest_files.append({
                    "candidate_id": cand_id,
                    "kind": kind,
                    "reason": cand.get("reason"),
                    "original_relative_path": rel_path,
                    "quarantine_relative_path": q_rel,
                    "size_bytes": size_bytes,
                    "modified_time": modified_time,
                    "status": "failed",
                    "skip_reason": None,
                    "error": str(ex),
                })
                failed_count += 1

    # --- Write manifest ---
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "created_at": datetime.now().isoformat(),
        "mode": "quarantine",
        "source_plan": str(Path(plan_path).resolve()),
        "storage_root": "<REDACTED>",
        "quarantine_timestamp": timestamp,
        "summary": {
            "requested_file_count": sum(len(c.get("files", [])) for c in candidates),
            "moved_file_count": moved_count,
            "skipped_file_count": skipped_count,
            "failed_file_count": failed_count,
            "moved_total_bytes": moved_bytes,
        },
        "files": manifest_files,
        "notices": [
            "Quarantine only. No files were permanently deleted.",
            "No database records were modified.",
            "Restore is available via --restore --manifest storage/quarantine/<timestamp>/manifest.json --confirm RESTORE.",
        ],
    }

    manifest_path = q_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Console summary ---
    print("Asset quarantine completed.")
    print(f"  Quarantine dir: {q_dir}")
    print(f"  Moved: {moved_count} files ({moved_bytes} bytes)")
    print(f"  Skipped: {skipped_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Manifest: {manifest_path}")
    print("No files were permanently deleted.")

    return manifest


# ---------------------------------------------------------------------------
# Restore (BE3D)
# ---------------------------------------------------------------------------

def run_restore(
    manifest_path: str,
    storage_dir: str | None,
) -> dict[str, Any]:
    """Restore quarantined files to their original locations."""
    root = Path(storage_dir) if storage_dir else Path(get_settings().storage_dir)

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    if manifest.get("manifest_version") != MANIFEST_VERSION:
        raise SystemExit(f"Unsupported manifest version: {manifest.get('manifest_version')}. Expected {MANIFEST_VERSION}.")
    if manifest.get("mode") != "quarantine":
        raise SystemExit(f"Manifest mode must be 'quarantine', got: {manifest.get('mode')}")

    files = manifest.get("files", [])
    restore_timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    restored_count = 0
    skipped_count = 0
    conflict_count = 0
    failed_count = 0
    restore_files: list[dict] = []

    for entry in files:
        if entry.get("status") != "moved":
            restore_files.append({
                **entry,
                "restore_status": "skipped_not_moved",
                "note": "Only status=moved files are restored",
            })
            skipped_count += 1
            continue

        q_rel = entry.get("quarantine_relative_path")
        orig_rel = entry.get("original_relative_path")
        if not q_rel or not orig_rel:
            restore_files.append({
                **entry,
                "restore_status": "failed",
                "note": "Missing quarantine or original path",
            })
            failed_count += 1
            continue

        q_full = root / q_rel
        orig_full = root / orig_rel

        # Check quarantine file exists
        if not q_full.exists():
            restore_files.append({
                **entry,
                "restore_status": "skipped",
                "note": "Quarantined file not found",
            })
            skipped_count += 1
            continue

        # Check original path already exists (no overwrite)
        if orig_full.exists():
            restore_files.append({
                **entry,
                "restore_status": "conflict",
                "note": "Original path already exists, skipping",
            })
            conflict_count += 1
            skipped_count += 1
            continue

        # Restore: copy back to original location
        try:
            orig_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(q_full, orig_full)
            restore_files.append({
                **entry,
                "restore_status": "restored",
                "note": None,
            })
            restored_count += 1
        except Exception as ex:
            restore_files.append({
                **entry,
                "restore_status": "failed",
                "note": str(ex),
            })
            failed_count += 1

    # --- Console summary ---
    print("Asset restore completed.")
    print(f"  Restored: {restored_count}")
    print(f"  Skipped (not moved): {skipped_count - conflict_count}")
    print(f"  Conflicts (already exists): {conflict_count}")
    print(f"  Failed: {failed_count}")
    print("No files were permanently deleted.")

    return {
        "restored_count": restored_count,
        "skipped_count": skipped_count,
        "conflict_count": conflict_count,
        "failed_count": failed_count,
        "restore_files": restore_files,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class ModeAction(argparse.Action):
    """Ensure only one of --dry-run / --quarantine / --restore is given."""
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is not None:
            raise argparse.ArgumentError(self, f"Cannot specify both {option_string} and existing mode")
        setattr(namespace, self.dest, values)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="P8-BE3D Asset quarantine/restore tool (BE3C dry-run also supported)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes (mutually exclusive):
  --dry-run     Generate read-only cleanup plan (BE3C)
  --quarantine  Move plan candidates to storage/quarantine/<timestamp>/
  --restore     Restore quarantined files to original locations

Examples:
  # Generate dry-run plan
  python scripts/cleanup_assets.py --dry-run --kind orphan --min-age-days 7

  # Execute quarantine (requires --plan and --confirm QUARANTINE)
  python scripts/cleanup_assets.py --quarantine --plan docs/generated/asset_cleanup_dry_run.json --confirm QUARANTINE

  # Restore files (requires --manifest and --confirm RESTORE)
  python scripts/cleanup_assets.py --restore --manifest storage/quarantine/<timestamp>/manifest.json --confirm RESTORE

Security:
  No permanent deletion. No database modification. Restore available for all quarantined files.
        """,
    )

    # Mutually exclusive mode flags
    parser.add_argument(
        "--dry-run",
        nargs="?",
        const="dry-run",
        default=None,
        dest="mode",
        action=ModeAction,
        metavar="MODE",
        help="Generate dry-run plan (MODE value is ignored, kept for compatibility)",
    )
    parser.add_argument(
        "--quarantine",
        nargs="?",
        const="quarantine",
        default=None,
        dest="mode",
        action=ModeAction,
        metavar="MODE",
        help="Execute quarantine move (requires --plan and --confirm QUARANTINE)",
    )
    parser.add_argument(
        "--restore",
        nargs="?",
        const="restore",
        default=None,
        dest="mode",
        action=ModeAction,
        metavar="MODE",
        help="Restore quarantined files (requires --manifest and --confirm RESTORE)",
    )

    # Dry-run parameters
    parser.add_argument(
        "--kind",
        default=DEFAULT_KIND,
        choices=list(VALID_KINDS),
        help=f"Cleanup kind for dry-run (default: {DEFAULT_KIND})",
    )
    parser.add_argument(
        "--min-age-days",
        type=int,
        default=DEFAULT_MIN_AGE_DAYS,
        help=f"Minimum file age in days for dry-run (default: {DEFAULT_MIN_AGE_DAYS})",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=MAX_DEFAULT_FILES,
        help=f"Maximum candidate files for dry-run (default: {MAX_DEFAULT_FILES})",
    )
    parser.add_argument(
        "--output",
        default="docs/generated/asset_cleanup_dry_run.json",
        help="Output JSON path for dry-run (default: docs/generated/asset_cleanup_dry_run.json)",
    )

    # Quarantine parameters
    parser.add_argument(
        "--plan",
        help="Path to dry-run JSON plan for quarantine execution",
    )
    parser.add_argument(
        "--confirm",
        help="Confirmation token (must be QUARANTINE for quarantine, RESTORE for restore)",
    )

    # Restore parameters
    parser.add_argument(
        "--manifest",
        help="Path to quarantine manifest.json for restore",
    )

    # Common
    parser.add_argument(
        "--storage-dir",
        default=None,
        help="Storage root directory (default: from app config)",
    )

    # Refuse purge arguments at all times
    for arg in sys.argv[1:]:
        if arg in ("--purge", "--purge-quarantine"):
            parser.error(f"{arg} is not supported in this version")

    args = parser.parse_args()

    # --- Validate mode ---
    if args.mode is None:
        parser.error("One of --dry-run, --quarantine, or --restore is required")
    if args.mode == "dry-run":
        if args.plan is not None or args.manifest is not None:
            parser.error("--plan and --manifest are only for --quarantine and --restore")
    if args.mode == "quarantine":
        if args.plan is None:
            parser.error("--quarantine requires --plan")
        if args.confirm != "QUARANTINE":
            parser.error("--quarantine requires --confirm QUARANTINE")
    if args.mode == "restore":
        if args.manifest is None:
            parser.error("--restore requires --manifest")
        if args.confirm != "RESTORE":
            parser.error("--restore requires --confirm RESTORE")

    # Suppress noisy logs
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    if args.mode == "dry-run":
        run_dry_run(
            kind=args.kind,
            min_age_days=args.min_age_days,
            max_files=args.max_files,
            output_path=args.output,
            storage_dir=args.storage_dir,
        )
    elif args.mode == "quarantine":
        run_quarantine(
            plan_path=args.plan,
            storage_dir=args.storage_dir,
        )
    elif args.mode == "restore":
        run_restore(
            manifest_path=args.manifest,
            storage_dir=args.storage_dir,
        )


if __name__ == "__main__":
    main()

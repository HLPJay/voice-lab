"""Dry-run audit for voice binding provider/model/voice consistency.

This script is read-only. It reports bindings whose provider, model, and
provider_voice_id no longer belong to the same provider capability domain.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sqlmodel import Session, create_engine, select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config.provider_config_loader import list_provider_configs
from app.core.config import get_settings
from app.models.provider_voice import ProviderVoice
from app.models.voice_binding import VoiceBinding
from app.providers.capability_registry import _build_capability_from_config


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _provider_capabilities_by_name() -> dict[str, Any]:
    return {cfg.name: _build_capability_from_config(cfg) for cfg in list_provider_configs()}


def _voice_index(session: Session) -> dict[tuple[str, str], ProviderVoice]:
    voices = session.exec(select(ProviderVoice)).all()
    return {(voice.provider, voice.provider_voice_id): voice for voice in voices}


def _other_provider_matches(
    voices: dict[tuple[str, str], ProviderVoice],
    provider: str,
    provider_voice_id: str,
) -> list[str]:
    return sorted(
        other_provider
        for (other_provider, other_voice_id), _voice in voices.items()
        if other_voice_id == provider_voice_id and other_provider != provider
    )


def _add_problem(item: dict[str, Any], problem_type: str, message: str, suggested_action: str) -> None:
    item["problems"].append(
        {
            "problem_type": problem_type,
            "message": message,
            "suggested_action": suggested_action,
        }
    )


def audit_bindings(database_url: str, provider_filter: str | None = None) -> dict[str, Any]:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    caps = _provider_capabilities_by_name()

    with Session(engine) as session:
        bindings = session.exec(select(VoiceBinding)).all()
        if provider_filter:
            bindings = [b for b in bindings if b.provider == provider_filter]
        voices = _voice_index(session)

        issues: list[dict[str, Any]] = []
        for binding in bindings:
            item: dict[str, Any] = {
                "binding_id": binding.id,
                "profile_id": binding.profile_id,
                "provider": binding.provider,
                "model": binding.model,
                "provider_voice_id": binding.provider_voice_id,
                "status": binding.status,
                "problems": [],
            }

            cap = caps.get(binding.provider)
            if cap is None:
                _add_problem(
                    item,
                    "UNKNOWN_PROVIDER",
                    f"provider {binding.provider!r} is not present in config/providers.yaml",
                    "Delete and recreate the binding with a configured provider.",
                )
            else:
                if not cap.enabled:
                    _add_problem(
                        item,
                        "PROVIDER_DISABLED",
                        f"provider {binding.provider!r} is disabled",
                        "Do not render with this binding; delete/recreate it after the provider is intentionally enabled.",
                    )

                supported_models = cap.tts.models if cap.tts and cap.tts.models else []
                if binding.model not in supported_models:
                    _add_problem(
                        item,
                        "MODEL_NOT_IN_PROVIDER_TTS_MODELS",
                        f"model {binding.model!r} is not in provider {binding.provider!r} TTS models",
                        "Delete and recreate the binding through the provider-aware UI; do not blindly rewrite the model.",
                    )

            voice = voices.get((binding.provider, binding.provider_voice_id))
            if voice is None:
                other_providers = _other_provider_matches(voices, binding.provider, binding.provider_voice_id)
                _add_problem(
                    item,
                    "VOICE_NOT_IN_PROVIDER",
                    f"voice_id {binding.provider_voice_id!r} is not registered under provider {binding.provider!r}",
                    (
                        "Delete and recreate the binding with a voice from the same provider."
                        if not other_providers
                        else f"Voice id exists under provider(s): {', '.join(other_providers)}; recreate under the correct provider."
                    ),
                )
            elif voice.status != "available":
                _add_problem(
                    item,
                    "VOICE_DEPRECATED" if voice.status == "deprecated" else "VOICE_NOT_AVAILABLE",
                    f"voice status is {voice.status!r}",
                    "Do not render with this binding; choose an available provider voice and recreate the binding.",
                )

            if item["problems"]:
                issues.append(item)

        counts = Counter(problem["problem_type"] for item in issues for problem in item["problems"])
        return {
            "dry_run": True,
            "commit": _git_commit(),
            "database_url": database_url,
            "provider_filter": provider_filter,
            "summary": {
                "bindings_scanned": len(bindings),
                "bindings_with_issues": len(issues),
                "problem_counts": dict(sorted(counts.items())),
            },
            "issues": issues,
        }


def delete_deprecated_issue_bindings(database_url: str, issue_binding_ids: list[str]) -> dict[str, Any]:
    """Delete bindings that are both in the issue list AND have status=deprecated.

    Safety invariants (enforced, not caller-trusted):
    - Only bindings whose status column == 'deprecated' are deleted.
    - Only binding_ids that appeared in the audit issues list are deleted.
    - available/active bindings are never touched.
    """
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    deleted: list[str] = []
    skipped: list[dict[str, str]] = []

    with Session(engine) as session:
        for bid in issue_binding_ids:
            binding = session.get(VoiceBinding, bid)
            if binding is None:
                skipped.append({"binding_id": bid, "reason": "not_found"})
                continue
            if binding.status != "deprecated":
                skipped.append({"binding_id": bid, "reason": f"status={binding.status!r}, only deprecated allowed"})
                continue
            session.delete(binding)
            deleted.append(bid)
        session.commit()

    return {
        "deleted_count": len(deleted),
        "deleted": deleted,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run audit for voice binding consistency.")
    parser.add_argument("--db-url", default=get_settings().database_url, help="SQLAlchemy database URL")
    parser.add_argument("--provider", default=None, help="Filter to a specific provider name")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Read-only mode (always true; flag for explicitness)")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--delete-deprecated-issues", action="store_true", default=False,
                        help="Delete bindings that are in issues AND have status=deprecated. Requires --confirm-delete.")
    parser.add_argument("--confirm-delete", action="store_true", default=False,
                        help="Confirm destructive delete. Must be combined with --delete-deprecated-issues.")
    args = parser.parse_args()

    # --- Apply delete path ---
    if args.delete_deprecated_issues:
        if not args.confirm_delete:
            print("ERROR: --delete-deprecated-issues requires --confirm-delete to prevent accidental deletion.", file=sys.stderr)
            return 1

        # Run full audit first to get current issue binding ids
        report = audit_bindings(args.db_url, provider_filter=args.provider)
        issue_ids = [item["binding_id"] for item in report["issues"]]

        if not issue_ids:
            print("No issue bindings found. Nothing to delete.")
            return 0

        print(f"About to delete {len(issue_ids)} deprecated issue binding(s):")
        for item in report["issues"]:
            print(f"  {item['binding_id']}  provider={item['provider']}  status={item['status']}")

        result = delete_deprecated_issue_bindings(args.db_url, issue_ids)
        print(f"Deleted: {result['deleted_count']}")
        for bid in result["deleted"]:
            print(f"  deleted: {bid}")
        for s in result["skipped"]:
            print(f"  skipped: {s['binding_id']} ({s['reason']})")
        return 0

    # --- Dry-run path (default) ---
    report = audit_bindings(args.db_url, provider_filter=args.provider)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        summary = report["summary"]
        print("Voice binding audit dry-run")
        print(f"  Commit:   {report['commit']}")
        print(f"  Database: {report['database_url']}")
        if report["provider_filter"]:
            print(f"  Provider filter: {report['provider_filter']}")
        print(f"  Bindings scanned:      {summary['bindings_scanned']}")
        print(f"  Bindings with issues:  {summary['bindings_with_issues']}")
        print(f"  Problem counts: {summary['problem_counts']}")
        for item in report["issues"]:
            problem_types = ", ".join(p["problem_type"] for p in item["problems"])
            print(
                f"  - {item['binding_id']} profile={item['profile_id']} "
                f"provider={item['provider']} model={item['model']} "
                f"voice={item['provider_voice_id']} problems={problem_types}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

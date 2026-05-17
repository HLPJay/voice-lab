"""Tests for scripts/audit_voice_bindings.py.

Verifies read-only guarantees and delete safety invariants.
Tests use a file-based SQLite tmp DB so audit_bindings() can open its own
engine connection to the same DB (in-memory SQLite doesn't share across connections).
No real API calls. No production DB writes.
"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.provider_voice import ProviderVoice
from app.models.voice_binding import VoiceBinding


_TS = "2026-01-01T00:00:00Z"


@pytest.fixture()
def db(tmp_path):
    """Return (db_url, engine) backed by a temp file so audit_bindings() can open its own connection."""
    db_file = tmp_path / "test_audit.db"
    url = f"sqlite:///{db_file}"
    eng = create_engine(url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return url, eng


def _add_voice(session: Session, provider: str, voice_id: str, status: str = "available") -> ProviderVoice:
    pv = ProviderVoice(
        id=f"pv_{provider}_{voice_id}",
        provider=provider,
        provider_voice_id=voice_id,
        name=voice_id,
        voice_type="voice_cloning",
        status=status,
        created_at=_TS,
        updated_at=_TS,
    )
    session.add(pv)
    return pv


def _add_binding(session: Session, bid: str, profile: str, provider: str, model: str, voice_id: str, status: str = "available") -> VoiceBinding:
    b = VoiceBinding(
        id=bid,
        profile_id=profile,
        provider=provider,
        model=model,
        provider_voice_id=voice_id,
        status=status,
        created_at=_TS,
        updated_at=_TS,
    )
    session.add(b)
    return b


class TestAuditDryRun:
    def test_dry_run_returns_true(self, db):
        """audit_bindings always returns dry_run=True."""
        from scripts.audit_voice_bindings import audit_bindings
        db_url, _ = db
        result = audit_bindings(db_url)
        assert result["dry_run"] is True

    def test_dry_run_does_not_write_db(self, db):
        """audit_bindings does not modify the database (binding count unchanged)."""
        from scripts.audit_voice_bindings import audit_bindings
        db_url, engine = db

        with Session(engine) as session:
            _add_binding(session, "b1", "p1", "mock", "mock-tts", "mock_v1", status="deprecated")
            session.commit()

        audit_bindings(db_url)

        with Session(engine) as session:
            count = len(session.exec(select(VoiceBinding)).all())
        assert count == 1  # unchanged

    def test_model_not_in_provider_detected(self, db):
        """MODEL_NOT_IN_PROVIDER_TTS_MODELS is detected when model not in capability."""
        from scripts.audit_voice_bindings import audit_bindings
        db_url, engine = db

        with Session(engine) as session:
            _add_voice(session, "mock", "mock_v1")
            _add_binding(session, "b1", "p1", "mock", "wrong-model", "mock_v1", status="deprecated")
            session.commit()

        result = audit_bindings(db_url)
        types = [p["problem_type"] for item in result["issues"] for p in item["problems"]]
        assert "MODEL_NOT_IN_PROVIDER_TTS_MODELS" in types

    def test_voice_not_in_provider_detected(self, db):
        """VOICE_NOT_IN_PROVIDER is detected when voice_id missing from provider_voices."""
        from scripts.audit_voice_bindings import audit_bindings
        db_url, engine = db

        with Session(engine) as session:
            _add_binding(session, "b1", "p1", "mock", "mock-tts", "ghost_voice", status="deprecated")
            session.commit()

        result = audit_bindings(db_url)
        types = [p["problem_type"] for item in result["issues"] for p in item["problems"]]
        assert "VOICE_NOT_IN_PROVIDER" in types

    def test_provider_filter(self, db):
        """--provider filter limits bindings scanned."""
        from scripts.audit_voice_bindings import audit_bindings
        db_url, engine = db

        with Session(engine) as session:
            _add_binding(session, "b_mock", "p1", "mock", "mock-tts", "ghost", status="deprecated")
            _add_binding(session, "b_mm", "p2", "minimax", "speech-2.8-hd", "ghost2", status="deprecated")
            session.commit()

        result = audit_bindings(db_url, provider_filter="mock")
        assert result["summary"]["bindings_scanned"] == 1
        assert all(item["provider"] == "mock" for item in result["issues"])


class TestDeleteDeprecatedIssues:
    def test_delete_requires_explicit_call(self, db):
        """Passing empty list to delete_deprecated_issue_bindings deletes nothing."""
        from scripts.audit_voice_bindings import delete_deprecated_issue_bindings
        db_url, engine = db

        with Session(engine) as session:
            _add_binding(session, "b1", "p1", "mock", "mock-tts", "v1", status="deprecated")
            session.commit()

        result = delete_deprecated_issue_bindings(db_url, [])
        assert result["deleted_count"] == 0

        with Session(engine) as session:
            still_there = session.get(VoiceBinding, "b1")
        assert still_there is not None

    def test_delete_only_deprecated(self, db):
        """delete_deprecated_issue_bindings skips bindings with status != deprecated."""
        from scripts.audit_voice_bindings import delete_deprecated_issue_bindings
        db_url, engine = db

        with Session(engine) as session:
            _add_binding(session, "b_avail", "p1", "mock", "mock-tts", "v1", status="available")
            _add_binding(session, "b_dep", "p2", "mock", "mock-tts", "v2", status="deprecated")
            session.commit()

        result = delete_deprecated_issue_bindings(db_url, ["b_avail", "b_dep"])
        assert "b_dep" in result["deleted"]
        assert "b_avail" not in result["deleted"]
        skipped_ids = [s["binding_id"] for s in result["skipped"]]
        assert "b_avail" in skipped_ids

        with Session(engine) as session:
            still_there = session.get(VoiceBinding, "b_avail")
        assert still_there is not None

    def test_delete_removes_deprecated_binding(self, db):
        """delete_deprecated_issue_bindings removes a deprecated binding from DB."""
        from scripts.audit_voice_bindings import delete_deprecated_issue_bindings
        db_url, engine = db

        with Session(engine) as session:
            _add_binding(session, "b_dep", "p1", "mock", "mock-tts", "v1", status="deprecated")
            session.commit()

        result = delete_deprecated_issue_bindings(db_url, ["b_dep"])
        assert result["deleted_count"] == 1
        assert "b_dep" in result["deleted"]

        with Session(engine) as session:
            gone = session.get(VoiceBinding, "b_dep")
        assert gone is None

    def test_delete_skips_not_found(self, db):
        """delete_deprecated_issue_bindings skips binding_ids not in DB."""
        from scripts.audit_voice_bindings import delete_deprecated_issue_bindings
        db_url, _ = db

        result = delete_deprecated_issue_bindings(db_url, ["nonexistent_id"])
        assert result["deleted_count"] == 0
        assert result["skipped"][0]["reason"] == "not_found"

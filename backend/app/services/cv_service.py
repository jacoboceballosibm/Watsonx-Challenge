"""CV repository service backed by the local SQLite database."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Optional
from uuid import uuid4

from app.models.cv import (
    CVCreateRequest,
    CVDuplicateRequest,
    CVAgentRun,
    CVDocument,
    CVUpdateRequest,
)
from app.services.database import get_connection
from app.services.profile_service import get_profile


def _loads_json(value: str | None, fallback):
    if not value:
        return fallback
    return json.loads(value)


def _cv_from_row(row) -> CVDocument:
    return CVDocument(
        cv_id=row["cv_id"],
        professional_id=row["professional_id"],
        name=row["name"],
        target_role=row["target_role"],
        source_type=row["source_type"],
        tags=_loads_json(row["tags_json"], []),
        cv_contact=_loads_json(row["cv_contact_json"], {}),
        cv_overview=row["cv_overview"],
        skills=_loads_json(row["skills_json"], []),
        cv_sections=_loads_json(row["cv_sections_json"], {}),
        is_default=bool(row["is_default"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def list_cvs(professional_id: str) -> list[CVDocument]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM cvs
            WHERE professional_id = ?
            ORDER BY is_default DESC, updated_at DESC, name ASC
            """,
            (professional_id,),
        ).fetchall()
    return [_cv_from_row(row) for row in rows]


def get_cv(cv_id: str) -> Optional[CVDocument]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM cvs WHERE cv_id = ?", (cv_id,)).fetchone()
    return _cv_from_row(row) if row else None


def _clear_default_cv(professional_id: str, conn) -> None:
    conn.execute(
        "UPDATE cvs SET is_default = 0, updated_at = CURRENT_TIMESTAMP WHERE professional_id = ?",
        (professional_id,),
    )


def create_cv(request: CVCreateRequest) -> Optional[CVDocument]:
    if not get_profile(request.professional_id):
        return None

    cv_id = f"cv_{uuid4().hex}"
    with get_connection() as conn:
        if request.is_default:
            _clear_default_cv(request.professional_id, conn)

        conn.execute(
            """
            INSERT INTO cvs (
                cv_id,
                professional_id,
                name,
                target_role,
                source_type,
                tags_json,
                cv_contact_json,
                cv_overview,
                skills_json,
                cv_sections_json,
                is_default
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cv_id,
                request.professional_id,
                request.name,
                request.target_role,
                request.source_type,
                json.dumps(request.tags),
                json.dumps(request.cv_contact),
                request.cv_overview,
                json.dumps(request.skills),
                json.dumps(request.cv_sections),
                1 if request.is_default else 0,
            ),
        )
    return get_cv(cv_id)


def update_cv(cv_id: str, updates: CVUpdateRequest) -> Optional[CVDocument]:
    current = get_cv(cv_id)
    if not current:
        return None

    data = current.model_dump()
    data.update(updates.model_dump(exclude_none=True))
    updated = CVDocument(**data)

    with get_connection() as conn:
        if updated.is_default:
            _clear_default_cv(updated.professional_id, conn)

        conn.execute(
            """
            UPDATE cvs
            SET name = ?,
                target_role = ?,
                source_type = ?,
                tags_json = ?,
                cv_contact_json = ?,
                cv_overview = ?,
                skills_json = ?,
                cv_sections_json = ?,
                is_default = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE cv_id = ?
            """,
            (
                updated.name,
                updated.target_role,
                updated.source_type,
                json.dumps(updated.tags),
                json.dumps(updated.cv_contact),
                updated.cv_overview,
                json.dumps(updated.skills),
                json.dumps(updated.cv_sections),
                1 if updated.is_default else 0,
                cv_id,
            ),
        )
    return get_cv(cv_id)


def delete_cv(cv_id: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM cvs WHERE cv_id = ?", (cv_id,))
    return cursor.rowcount > 0


def duplicate_cv(cv_id: str, request: CVDuplicateRequest) -> Optional[CVDocument]:
    source = get_cv(cv_id)
    if not source:
        return None

    return create_cv(
        CVCreateRequest(
            professional_id=source.professional_id,
            name=request.name or f"{source.name} Copy",
            target_role=request.target_role if request.target_role is not None else source.target_role,
            source_type="duplicate",
            tags=source.tags,
            cv_contact=source.cv_contact,
            cv_overview=source.cv_overview,
            skills=source.skills,
            cv_sections=source.cv_sections,
            is_default=False,
        )
    )


def record_cv_agent_run(
    *,
    professional_id: str,
    tailored_cv_text: str,
    cv_id: str | None = None,
    role_description: str | None = None,
    source_cv_text: str | None = None,
    changes: list[str] | None = None,
    warnings: list[str] | None = None,
    model: str | None = None,
) -> CVAgentRun:
    run_id = f"cvrun_{uuid4().hex}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO cv_agent_runs (
                run_id,
                cv_id,
                professional_id,
                role_description,
                source_cv_text,
                tailored_cv_text,
                changes_json,
                warnings_json,
                model
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                cv_id,
                professional_id,
                role_description,
                source_cv_text,
                tailored_cv_text,
                json.dumps(changes or []),
                json.dumps(warnings or []),
                model,
            ),
        )
        row = conn.execute(
            "SELECT * FROM cv_agent_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

    return CVAgentRun(
        run_id=row["run_id"],
        cv_id=row["cv_id"],
        professional_id=row["professional_id"],
        role_description=row["role_description"],
        source_cv_text=row["source_cv_text"],
        tailored_cv_text=row["tailored_cv_text"],
        changes=_loads_json(row["changes_json"], []),
        warnings=_loads_json(row["warnings_json"], []),
        model=row["model"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def seed_cvs_from_profiles() -> None:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM profiles ORDER BY professional_id").fetchall()

    for row in rows:
        professional_id = row["professional_id"]
        if list_cvs(professional_id):
            continue

        profile = get_profile(professional_id)
        if not profile:
            continue

        create_cv(
            CVCreateRequest(
                professional_id=profile.professional_id,
                name="Base CV",
                target_role=None,
                source_type="profile",
                tags=["base"],
                cv_contact=profile.cv_contact,
                cv_overview=profile.cv_overview,
                skills=profile.skills,
                cv_sections=profile.cv_sections,
                is_default=True,
            )
        )

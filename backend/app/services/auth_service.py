"""Demo authentication backed by SQLite sessions and users."""
from __future__ import annotations

import os
import secrets
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.auth import LoginResponse, User, UserRole
from app.services.database import get_connection

DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "password")
bearer_scheme = HTTPBearer(auto_error=False)

_SEED_USERS: dict[str, User] = {
    "anguyen": User(
        username="anguyen",
        password=DEMO_PASSWORD,
        professional_id="A5XCVSPCNN2O",
        user_id="A5XCVSPCNN2O",
        role=UserRole.CANDIDATE,
    ),
    "jsmith": User(
        username="jsmith",
        password=DEMO_PASSWORD,
        professional_id="JS7BQM3PXWK1",
        user_id="JS7BQM3PXWK1",
        role=UserRole.CANDIDATE,
    ),
    "mchen": User(
        username="mchen",
        password=DEMO_PASSWORD,
        professional_id="MC2NVD9RTPW5",
        user_id="MC2NVD9RTPW5",
        role=UserRole.OWNER,
    ),
    "swilliams": User(
        username="swilliams",
        password=DEMO_PASSWORD,
        professional_id="SW8FHK4TQNX7",
        user_id="SW8FHK4TQNX7",
        role=UserRole.OWNER,
    ),
    "drodriguez": User(
        username="drodriguez",
        password=DEMO_PASSWORD,
        professional_id="DR3KGP6LMZY8",
        user_id="DR3KGP6LMZY8",
        role=UserRole.OWNER,
    ),
}


def _user_from_row(row) -> User:
    return User(
        username=row["username"],
        password=row["password"],
        professional_id=row["professional_id"],
        user_id=row["user_id"],
        role=UserRole(row["role"]),
    )


def get_user_by_username(username: str) -> Optional[User]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return _user_from_row(row) if row else None


def get_user_by_token(token: str) -> Optional[User]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT users.*
            FROM sessions
            JOIN users ON users.username = sessions.username
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    return _user_from_row(row) if row else None


def list_users() -> list[User]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY username").fetchall()
    return [_user_from_row(row) for row in rows]


def authenticate(username: str, password: str) -> Optional[LoginResponse]:
    user = get_user_by_username(username)
    if not user or user.password != password:
        return None

    token = secrets.token_urlsafe(32)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (token, username, professional_id)
            VALUES (?, ?, ?)
            """,
            (token, user.username, user.professional_id),
        )

    from app.services.profile_service import get_profile

    profile = get_profile(user.professional_id)
    name = profile.name if profile else username

    return LoginResponse(
        professional_id=user.professional_id,
        user_id=user.user_id,
        name=name,
        token=token,
        role=user.role,
    )


def verify_token(token: str) -> Optional[str]:
    user = get_user_by_token(token)
    return user.professional_id if user else None


def logout(token: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return cursor.rowcount > 0


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    user = get_user_by_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return user


def seed_users() -> None:
    with get_connection() as conn:
        for user in _SEED_USERS.values():
            conn.execute(
                """
                INSERT OR IGNORE INTO users (
                    username,
                    password,
                    professional_id,
                    user_id,
                    role
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user.username,
                    user.password,
                    user.professional_id,
                    user.user_id,
                    user.role.value,
                ),
            )

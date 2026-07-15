"""
Authentication service — stub implementation.
In production, use proper password hashing (bcrypt), JWT tokens, and secure session management.
"""
from typing import Optional
import secrets
import os
from app.models.auth import User, LoginResponse

# Demo password from environment or default for development only
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "password")

# ── Fake user accounts ────────────────────────────────────────────────────────
_USERS: dict[str, User] = {
    "anguyen": User(
        username="anguyen",
        password=DEMO_PASSWORD,
        professional_id="A5XCVSPCNN2O"
    ),
    "jsmith": User(
        username="jsmith",
        password=DEMO_PASSWORD,
        professional_id="JS7BQM3PXWK1"
    ),
    "mchen": User(
        username="mchen",
        password=DEMO_PASSWORD,
        professional_id="MC2NVD9RTPW5"
    ),
    "swilliams": User(
        username="swilliams",
        password=DEMO_PASSWORD,
        professional_id="SW8FHK4TQNX7"
    ),
    "drodriguez": User(
        username="drodriguez",
        password=DEMO_PASSWORD,
        professional_id="DR3KGP6LMZY8"
    ),
}

# Simple in-memory session store
_SESSIONS: dict[str, str] = {}  # token -> professional_id


def authenticate(username: str, password: str) -> Optional[LoginResponse]:
    """
    Authenticate user and return session token.
    In production: use bcrypt.checkpw() for password verification.
    """
    user = _USERS.get(username)
    if not user or user.password != password:
        return None

    # Generate session token
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = user.professional_id

    # Get user's name from profile service
    from app.services.profile_service import get_profile
    profile = get_profile(user.professional_id)
    name = profile.name if profile else username

    return LoginResponse(
        professional_id=user.professional_id,
        name=name,
        token=token
    )


def verify_token(token: str) -> Optional[str]:
    """Verify token and return professional_id if valid."""
    return _SESSIONS.get(token)


def logout(token: str) -> bool:
    """Remove session token."""
    if token in _SESSIONS:
        del _SESSIONS[token]
        return True
    return False

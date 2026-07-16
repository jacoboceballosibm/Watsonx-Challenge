import os

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from app.models.auth import LoginRequest, LoginResponse
from app.services.auth_service import authenticate, bearer_scheme, list_users, logout
from app.services.profile_service import get_profile

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Authenticate user and return session token."""
    result = authenticate(request.username, request.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return result


@router.post("/logout")
def logout_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    """Logout user by invalidating token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    success = logout(credentials.credentials)
    if not success:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {"message": "Logged out successfully"}


@router.get("/users")
def list_demo_users():
    """
    List available demo users for the sign-in page.
    In production, this endpoint would not exist!
    """
    users = list_users()
    demo_users = []
    for user in users:
        profile = get_profile(user.professional_id)
        demo_users.append(
            {
                "username": user.username,
                "name": profile.name if profile else user.username,
                "band": profile.band if profile else "",
                "location": profile.location if profile else "",
                "role": user.role.value,
            }
        )

    return {
        "users": demo_users,
        "default_password": os.getenv("DEMO_PASSWORD", "password")
    }

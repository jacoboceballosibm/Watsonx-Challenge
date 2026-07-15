from fastapi import APIRouter, HTTPException
from app.models.auth import LoginRequest, LoginResponse
from app.services.auth_service import authenticate, logout

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Authenticate user and return session token."""
    result = authenticate(request.username, request.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return result


@router.post("/logout")
def logout_user(token: str):
    """Logout user by invalidating token."""
    success = logout(token)
    if not success:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {"message": "Logged out successfully"}


@router.get("/users")
def list_demo_users():
    """
    List available demo users for the sign-in page.
    In production, this endpoint would not exist!
    """
    import os
    return {
        "users": [
            {"username": "anguyen", "name": "Alysa Nguyen", "band": "7", "location": "US"},
            {"username": "jsmith", "name": "John Smith", "band": "6", "location": "UK"},
            {"username": "mchen", "name": "Marcus Chen", "band": "8", "location": "SG"},
            {"username": "swilliams", "name": "Sarah Williams", "band": "7", "location": "CA"},
            {"username": "drodriguez", "name": "David Rodriguez", "band": "9", "location": "MX"},
        ],
        "default_password": os.getenv("DEMO_PASSWORD", "password")
    }

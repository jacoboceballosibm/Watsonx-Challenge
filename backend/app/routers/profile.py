from fastapi import APIRouter, HTTPException
from app.models.profile import Profile, ProfileUpdateRequest
from app.services.profile_service import get_profile, update_profile

router = APIRouter()


@router.get("/{professional_id}", response_model=Profile)
def read_profile(professional_id: str):
    profile = get_profile(professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    return profile


@router.patch("/{professional_id}", response_model=Profile)
def patch_profile(professional_id: str, updates: ProfileUpdateRequest):
    profile = update_profile(professional_id, updates)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    return profile

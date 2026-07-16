from fastapi import APIRouter, HTTPException, Query

from app.models.cv import (
    CVCreateRequest,
    CVDuplicateRequest,
    CVDocument,
    CVListResponse,
    CVUpdateRequest,
)
from app.services.cv_service import (
    create_cv,
    delete_cv,
    duplicate_cv,
    get_cv,
    list_cvs,
    update_cv,
)

router = APIRouter()


@router.get("", response_model=CVListResponse)
def read_cvs(professional_id: str = Query(...)):
    return CVListResponse(
        professional_id=professional_id,
        cvs=list_cvs(professional_id),
    )


@router.post("", response_model=CVDocument)
def create_cv_document(request: CVCreateRequest):
    cv = create_cv(request)
    if not cv:
        raise HTTPException(status_code=404, detail="Professional not found")
    return cv


@router.get("/{cv_id}", response_model=CVDocument)
def read_cv(cv_id: str):
    cv = get_cv(cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.patch("/{cv_id}", response_model=CVDocument)
def patch_cv(cv_id: str, updates: CVUpdateRequest):
    cv = update_cv(cv_id, updates)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


@router.delete("/{cv_id}")
def remove_cv(cv_id: str):
    if not delete_cv(cv_id):
        raise HTTPException(status_code=404, detail="CV not found")
    return {"status": "deleted", "cv_id": cv_id}


@router.post("/{cv_id}/duplicate", response_model=CVDocument)
def duplicate_cv_document(cv_id: str, request: CVDuplicateRequest):
    cv = duplicate_cv(cv_id, request)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv

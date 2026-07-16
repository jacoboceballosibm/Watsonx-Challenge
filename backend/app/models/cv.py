from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CVDocument(BaseModel):
    cv_id: str
    professional_id: str
    name: str
    target_role: Optional[str] = None
    source_type: str = "profile"
    tags: list[str] = Field(default_factory=list)
    cv_contact: dict[str, str] = Field(default_factory=dict)
    cv_overview: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    cv_sections: dict[str, str] = Field(default_factory=dict)
    is_default: bool = False
    created_at: datetime
    updated_at: datetime


class CVCreateRequest(BaseModel):
    professional_id: str
    name: str
    target_role: Optional[str] = None
    source_type: str = "manual"
    tags: list[str] = Field(default_factory=list)
    cv_contact: dict[str, str] = Field(default_factory=dict)
    cv_overview: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    cv_sections: dict[str, str] = Field(default_factory=dict)
    is_default: bool = False


class CVUpdateRequest(BaseModel):
    name: Optional[str] = None
    target_role: Optional[str] = None
    source_type: Optional[str] = None
    tags: Optional[list[str]] = None
    cv_contact: Optional[dict[str, str]] = None
    cv_overview: Optional[str] = None
    skills: Optional[list[str]] = None
    cv_sections: Optional[dict[str, str]] = None
    is_default: Optional[bool] = None


class CVDuplicateRequest(BaseModel):
    name: Optional[str] = None
    target_role: Optional[str] = None


class CVListResponse(BaseModel):
    professional_id: str
    cvs: list[CVDocument]


class CVAgentRun(BaseModel):
    run_id: str
    cv_id: Optional[str] = None
    professional_id: str
    role_description: Optional[str] = None
    source_cv_text: Optional[str] = None
    tailored_cv_text: str
    changes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model: Optional[str] = None
    created_at: datetime

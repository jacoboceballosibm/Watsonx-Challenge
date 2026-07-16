from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Agent #1: Stale listing reconfirmation ────────────────────────────────────
class StaleCheckRequest(BaseModel):
    seat_id: str
    days_threshold: int = 30


class StaleCheckResult(BaseModel):
    seat_id: str
    days_since_update: int
    is_stale: bool
    nudge_draft: Optional[str] = None  # drafted message to owner


# ── Agent #2: Internally-filled mismatch detector ────────────────────────────
class MismatchCheckRequest(BaseModel):
    seat_id: str


class MismatchCheckResult(BaseModel):
    seat_id: str
    mismatch_detected: bool
    reason: Optional[str] = None
    ai_recommendation_note: Optional[str] = None


# ── Agent #5: AI outreach email drafter ──────────────────────────────────────
class OutreachDraftRequest(BaseModel):
    seat_id: str
    candidate_professional_id: str


class OutreachDraftResult(BaseModel):
    seat_id: str
    candidate_professional_id: str
    to_email: Optional[str] = None
    to_display_name: Optional[str] = None
    subject: str
    body: str
    # Frontend presents this for user edit before sending via Outlook


class OutreachSendRequest(BaseModel):
    seat_id: str
    candidate_professional_id: str
    to_email: str
    subject: str
    body: str


class OutreachSendResult(BaseModel):
    status: str
    provider: str = "outlook"
    message_id: Optional[str] = None
    detail: Optional[str] = None


# ── Agent #7: AI project recommendations ─────────────────────────────────────
class RecommendationRequest(BaseModel):
    professional_id: str
    mode: str = "candidate"  # "candidate" or "owner"


class RecommendationResult(BaseModel):
    professional_id: str
    mode: str
    recommendations: list[dict]
    reasoning: Optional[str] = None


# ── Agent #8: AI CV tailor ────────────────────────────────────────────────────
class CVTailorRequest(BaseModel):
    professional_id: str
    seat_id: Optional[str] = None
    cv_id: Optional[str] = None
    role_description: Optional[str] = None
    source_cv_text: Optional[str] = None
    output_mode: str = "preview"


class CVTailorResult(BaseModel):
    seat_id: Optional[str] = None
    cv_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    tailored_cv_text: str
    tailored_cv_contact: dict[str, str] = Field(default_factory=dict)
    tailored_cv_overview: Optional[str] = None
    tailored_skills: list[str] = Field(default_factory=list)
    tailored_cv_sections: dict[str, str] = Field(default_factory=dict)
    changes_summary: list[str]
    role_alignment: list[str] = Field(default_factory=list)
    missing_experience: list[str] = Field(default_factory=list)
    suggested_keywords: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ── Agent #9: Expiration check agent ──────────────────────────────────────────
class AgentResponse(BaseModel):
    agent_name: str
    summary: str
    data: dict
    success: bool

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel


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
    subject: str
    body: str
    # Frontend presents this for user edit before sending via Outlook


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
    seat_id: str
    professional_id: str


class CVTailorResult(BaseModel):
    seat_id: str
    tailored_cv_text: str
    changes_summary: list[str]

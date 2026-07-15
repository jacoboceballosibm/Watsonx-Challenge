from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.agent import (
    StaleCheckRequest, StaleCheckResult,
    MismatchCheckRequest, MismatchCheckResult,
    OutreachDraftRequest, OutreachDraftResult,
    OutreachSendRequest, OutreachSendResult,
    RecommendationRequest, RecommendationResult,
    CVTailorRequest, CVTailorResult,
    AgentResponse,
)
from app.models.seat import Seat
from app.agents.stale_agent import run_stale_check
from app.agents.mismatch_agent import run_mismatch_check
from app.agents.outreach_agent import run_outreach_draft, run_outreach_send
from app.agents.recommendation_agent import run_recommendations
from app.agents.cv_tailor_agent import run_cv_tailor
from app.agents.expiration_agent import check_listing_expiration
from app.models.auth import User
from app.services.auth_service import get_current_user

router = APIRouter()


# ── Agent #1 ──────────────────────────────────────────────────────────────────
@router.post("/stale-check", response_model=StaleCheckResult)
async def stale_check(request: StaleCheckRequest):
    return await run_stale_check(request)


# ── Agent #2 ──────────────────────────────────────────────────────────────────
@router.post("/mismatch-check", response_model=MismatchCheckResult)
async def mismatch_check(request: MismatchCheckRequest):
    return await run_mismatch_check(request)


# ── Agent #5 ──────────────────────────────────────────────────────────────────
@router.post("/outreach-draft", response_model=OutreachDraftResult)
async def outreach_draft(request: OutreachDraftRequest):
    return await run_outreach_draft(request)

@router.post("/outreach-send", response_model=OutreachSendResult)
async def outreach_send(request: OutreachSendRequest):
    return await run_outreach_send(request)


# ── Agent #7 ──────────────────────────────────────────────────────────────────
@router.post("/recommendations", response_model=RecommendationResult)
async def recommendations(request: RecommendationRequest):
    return await run_recommendations(request)


# ── Agent #8 ──────────────────────────────────────────────────────────────────
@router.post("/cv-tailor", response_model=CVTailorResult)
async def cv_tailor(request: CVTailorRequest):
    return await run_cv_tailor(request)


# ── Agent #9: Expiration Check ─────────────────────────────────────────────────
@router.post("/expiration-check", response_model=AgentResponse)
def expiration_check(
    seats: List[Seat],
    threshold_days: int = 7
):
    """
    Check which listings are approaching expiration
    """
    return check_listing_expiration(seats, threshold_days)

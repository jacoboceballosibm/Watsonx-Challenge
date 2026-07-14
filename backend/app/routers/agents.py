from fastapi import APIRouter, HTTPException
from app.models.agent import (
    StaleCheckRequest, StaleCheckResult,
    MismatchCheckRequest, MismatchCheckResult,
    OutreachDraftRequest, OutreachDraftResult,
    RecommendationRequest, RecommendationResult,
    CVTailorRequest, CVTailorResult,
)
from app.agents.stale_agent import run_stale_check
from app.agents.mismatch_agent import run_mismatch_check
from app.agents.outreach_agent import run_outreach_draft
from app.agents.recommendation_agent import run_recommendations
from app.agents.cv_tailor_agent import run_cv_tailor

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


# ── Agent #7 ──────────────────────────────────────────────────────────────────
@router.post("/recommendations", response_model=RecommendationResult)
async def recommendations(request: RecommendationRequest):
    return await run_recommendations(request)


# ── Agent #8 ──────────────────────────────────────────────────────────────────
@router.post("/cv-tailor", response_model=CVTailorResult)
async def cv_tailor(request: CVTailorRequest):
    return await run_cv_tailor(request)

"""
Agent #7 — AI project recommendations
Candidate mode:  given a professional_id, return recommended open seats.
Owner mode:      given a seat owner's professional_id, return recommended candidates.
Wire WATSONX_API_KEY + WATSONX_URL and replace stub logic below.
"""
from __future__ import annotations
import logging
from app.models.agent import RecommendationRequest, RecommendationResult
from app.services.profile_service import get_profile
from app.services.seat_service import search_seats
from app.models.seat import SeatSearchParams

logger = logging.getLogger(__name__)


async def run_recommendations(request: RecommendationRequest) -> RecommendationResult:
    profile = get_profile(request.professional_id)

    if request.mode == "candidate":
        # TODO: replace stub with watsonx.ai semantic matching call
        all_seats = search_seats(SeatSearchParams(per_page=10))
        recs = [
            {
                "seat_id": s.seat_id,
                "title": s.title,
                "client_name": s.client_name,
                "match_score": 0.85,  # placeholder — LLM will compute this
                "reason": "Skills and band align with listing requirements.",
            }
            for s in all_seats.seats[:3]
        ]
        reasoning = "Recommendations based on your skills, band, and availability."
    else:
        # Owner mode: return candidate suggestions (stub)
        recs = [
            {
                "professional_id": "STUB-001",
                "name": "Sample Candidate A",
                "match_score": 0.90,
                "reason": "Strong match on required band and location.",
            }
        ]
        reasoning = "Candidate recommendations based on seat requirements."

    logger.info(
        '{"agent": "recommendations", "professional_id": "%s", "mode": "%s"}',
        request.professional_id,
        request.mode,
    )

    return RecommendationResult(
        professional_id=request.professional_id,
        mode=request.mode,
        recommendations=recs,
        reasoning=reasoning,
    )

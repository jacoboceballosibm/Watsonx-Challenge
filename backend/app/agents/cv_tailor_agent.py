"""
Agent #8 — AI CV tailor
Given a seat and a professional, produces a tailored version of the CV
that highlights relevant experience for that specific listing.
Wire WATSONX_API_KEY + WATSONX_URL and replace stub logic below.
CV repository integration: pull the base CV from profile.cv_repository_url.
"""
from __future__ import annotations
import logging
from app.models.agent import CVTailorRequest, CVTailorResult
from app.services.seat_service import get_seat_by_id
from app.services.profile_service import get_profile

logger = logging.getLogger(__name__)


async def run_cv_tailor(request: CVTailorRequest) -> CVTailorResult:
    seat = get_seat_by_id(request.seat_id)
    profile = get_profile(request.professional_id)

    seat_title = seat.title if seat else "the role"
    client = seat.client_name if seat else "the client"
    skills = ", ".join(profile.skills) if profile and profile.skills else "your skills"

    # TODO: replace stub with watsonx.ai call that:
    #   1. Fetches base CV from profile.cv_repository_url
    #   2. Rewrites summary + highlights to match seat requirements
    #   3. Returns the tailored text + a diff summary

    tailored_cv_text = (
        f"TAILORED CV — {seat_title} at {client}\n"
        f"{'=' * 60}\n\n"
        f"Professional Summary:\n"
        f"Experienced IBM professional with expertise in {skills}, "
        f"with a strong track record delivering results in {seat.sector if seat else 'public sector'} "
        f"environments. Seeking to contribute to {client} as a {seat_title}.\n\n"
        f"[Full CV content would be populated here by watsonx.ai]\n"
    )

    changes_summary = [
        f"Rewrote professional summary to highlight {seat_title} relevance.",
        f"Promoted {skills} to top of skills section.",
        f"Added {client}-specific terminology throughout.",
    ]

    logger.info(
        '{"agent": "cv_tailor", "seat_id": "%s", "professional_id": "%s"}',
        request.seat_id,
        request.professional_id,
    )

    return CVTailorResult(
        seat_id=request.seat_id,
        tailored_cv_text=tailored_cv_text,
        changes_summary=changes_summary,
    )

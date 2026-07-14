"""
Agent #2 — Internally-filled mismatch detector
Cross-checks listing status against internal signals (e.g., candidates
already Selected/Confirmed) and flags the mismatch with an AI note.
Wire WATSONX_API_KEY + WATSONX_URL and replace stub logic below.
"""
from __future__ import annotations
import logging
from app.models.agent import MismatchCheckRequest, MismatchCheckResult
from app.models.seat import CandidateStatus
from app.services.seat_service import get_seat_by_id

logger = logging.getLogger(__name__)


async def run_mismatch_check(request: MismatchCheckRequest) -> MismatchCheckResult:
    seat = get_seat_by_id(request.seat_id)
    if not seat:
        return MismatchCheckResult(seat_id=request.seat_id, mismatch_detected=False)

    mismatch = seat.candidate_status in (CandidateStatus.SELECTED,)
    reason = None
    ai_note = None

    if mismatch:
        reason = (
            f"Seat '{seat.title}' has a candidate in status "
            f"'{seat.candidate_status.value}' but the listing is still open."
        )
        # TODO: replace stub with watsonx.ai LLM call for richer recommendation
        ai_note = (
            f"This seat appears to be internally filled. "
            f"Consider closing it to keep ProM data accurate."
        )
        logger.info(
            '{"agent": "mismatch_check", "seat_id": "%s", "mismatch": true}',
            request.seat_id,
        )

    return MismatchCheckResult(
        seat_id=request.seat_id,
        mismatch_detected=mismatch,
        reason=reason,
        ai_recommendation_note=ai_note,
    )

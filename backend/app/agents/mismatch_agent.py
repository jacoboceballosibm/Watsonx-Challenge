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

    # Check multiple mismatch conditions
    mismatch = False
    reason = None
    ai_note = None

    # Condition 1: Candidate status is SELECTED
    if seat.candidate_status in (CandidateStatus.SELECTED,):
        mismatch = True
        reason = (
            f"Seat '{seat.title}' has a candidate in status "
            f"'{seat.candidate_status.value}' but the listing is still open."
        )

    # Condition 2: Check status breakdown - if selected count >= positions needed
    if seat.status_breakdown and seat.positions_still_needed is not None:
        selected_count = seat.status_breakdown.selected
        if selected_count >= seat.positions_still_needed and seat.positions_still_needed > 0:
            mismatch = True
            reason = (
                f"Seat '{seat.title}' has {selected_count} candidates already Selected, "
                f"but only {seat.positions_still_needed} position(s) needed. "
                f"The listing should be closed or marked as formality."
            )

    if mismatch:
        # TODO: replace stub with watsonx.ai LLM call for richer recommendation
        ai_note = (
            f"This seat appears to be internally filled. "
            f"Recommended actions: (1) Close the listing if no longer hiring, or "
            f"(2) Mark as 'Formality/compliance posting' if keeping it open for compliance."
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

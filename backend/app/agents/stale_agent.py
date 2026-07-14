"""
Agent #1 — Stale listing reconfirmation
Reviews days-since-update; drafts a nudge message to the seat owner.
Wire WATSONX_API_KEY + WATSONX_URL into the environment and replace
the stub logic below with a real LLM call.
"""
from __future__ import annotations
import logging
import os
from app.models.agent import StaleCheckRequest, StaleCheckResult
from app.services.seat_service import get_seat_by_id

logger = logging.getLogger(__name__)

STALE_DAYS_THRESHOLD = int(os.getenv("STALE_DAYS_THRESHOLD", "30"))


async def run_stale_check(request: StaleCheckRequest) -> StaleCheckResult:
    seat = get_seat_by_id(request.seat_id)
    if not seat:
        return StaleCheckResult(seat_id=request.seat_id, days_since_update=0, is_stale=False)

    threshold = request.days_threshold or STALE_DAYS_THRESHOLD
    is_stale = seat.days_since_update >= threshold

    nudge_draft = None
    if is_stale:
        # TODO: replace stub with watsonx.ai LLM call
        nudge_draft = (
            f"Hi,\n\n"
            f"The open seat '{seat.title}' for {seat.client_name} has not been updated "
            f"in {seat.days_since_update} days. Could you confirm it is still active "
            f"or close it if it has been filled?\n\n"
            f"Thanks,\nProM Agent"
        )
        logger.info(
            '{"agent": "stale_check", "seat_id": "%s", "days": %d, "stale": true}',
            request.seat_id,
            seat.days_since_update,
        )

    return StaleCheckResult(
        seat_id=request.seat_id,
        days_since_update=seat.days_since_update,
        is_stale=is_stale,
        nudge_draft=nudge_draft,
    )

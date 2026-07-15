from __future__ import annotations

import logging
import os
from uuid import uuid4

from app.models.agent import OutreachSendRequest, OutreachSendResult

logger = logging.getLogger(__name__)


async def send_outlook_email(request: OutreachSendRequest) -> OutreachSendResult:
    mode = os.getenv("OUTLOOK_SEND_MODE", "dry_run")

    if not request.to_email.strip():
        return OutreachSendResult(
            status="error",
            detail="Recipient email is required.",
        )

    if not request.subject.strip():
        return OutreachSendResult(
            status="error",
            detail="Subject is required.",
        )

    if not request.body.strip():
        return OutreachSendResult(
            status="error",
            detail="Email body is required.",
        )

    if mode == "dry_run":
        logger.info(
            '{"service": "outlook", "mode": "dry_run", "seat_id": "%s", "candidate_id": "%s"}',
            request.seat_id,
            request.candidate_professional_id,
        )
        return OutreachSendResult(
            status="drafted",
            provider="outlook",
            message_id=f"dry-run-{uuid4()}",
            detail="Dry run only. No email was sent.",
        )

    return OutreachSendResult(
        status="error",
        provider="outlook",
        detail="Real Outlook sending is not configured yet.",
    )
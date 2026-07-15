"""
Agent #5 — AI outreach email drafter
Drafts a personalised inquiry to the project contact based on the
listing and the candidate's background.
Wire WATSONX_API_KEY + WATSONX_URL and replace stub logic below.
The drafted email is returned to the frontend for user editing;
the user then sends it via their Outlook integration.
"""
from __future__ import annotations
import logging
from app.models.agent import (
    OutreachDraftRequest,
    OutreachDraftResult,
    OutreachSendRequest,
    OutreachSendResult,
)
from app.services.outlook_service import send_outlook_email
from app.services.seat_service import get_seat_by_id
from app.services.profile_service import get_profile

logger = logging.getLogger(__name__)


async def run_outreach_draft(request: OutreachDraftRequest) -> OutreachDraftResult:
    seat = get_seat_by_id(request.seat_id)
    candidate = get_profile(request.candidate_professional_id)

    seat_title = seat.title if seat else "the open seat"
    client = seat.client_name if seat else "the client"
    candidate_name = candidate.name if candidate else "Candidate"
    skills = ", ".join(candidate.skills) if candidate and candidate.skills else "relevant skills"

    # TODO: replace stub with watsonx.ai LLM call
    subject = f"Interest in {seat_title} – {client}"
    body = (
        f"Dear Hiring Manager,\n\n"
        f"I am reaching out regarding the open {seat_title} position at {client}.\n\n"
        f"My name is {candidate_name} and I bring expertise in {skills}. "
        f"I believe my background aligns closely with the requirements of this role "
        f"and I would welcome the opportunity to discuss how I can contribute to your team.\n\n"
        f"I have attached my tailored CV for your review. Please do not hesitate to reach out "
        f"at your earliest convenience.\n\n"
        f"Best regards,\n{candidate_name}"
    )

    logger.info(
        '{"agent": "outreach_draft", "seat_id": "%s", "candidate_id": "%s"}',
        request.seat_id,
        request.candidate_professional_id,
    )

    return OutreachDraftResult(
        seat_id=request.seat_id,
        candidate_professional_id=request.candidate_professional_id,
        to_email=None,
        to_display_name=seat.owner_notes_id if seat else None,
        subject=subject,
        body=body,
    )


async def run_outreach_send(request: OutreachSendRequest) -> OutreachSendResult:
    logger.info(
        '{"agent": "outreach_send", "seat_id": "%s", "candidate_id": "%s"}',
        request.seat_id,
        request.candidate_professional_id,
    )
    return await send_outlook_email(request)

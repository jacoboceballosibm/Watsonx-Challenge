"""
Agent #8 - AI CV tailor.

Given a seat and a professional, produces a tailored version of the CV that
highlights relevant experience for that specific listing.
"""
from __future__ import annotations

import logging
import os
from textwrap import dedent

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.models.agent import CVTailorRequest, CVTailorResult
from app.models.cv import CVDocument
from app.models.profile import Profile
from app.models.seat import Seat
from app.services.cv_service import get_cv, list_cvs, record_cv_agent_run
from app.services.profile_service import get_profile
from app.services.seat_service import get_seat_by_id

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4.1-mini"
MAX_CV_CHARS = 16_000


class TailoredCVContact(BaseModel):
    name: str = Field(description="Candidate display name.")
    title: str = Field(description="Role or professional title.")
    phone: str = Field(description="Phone number, or empty string when unavailable.")
    email: str = Field(description="Email address, or empty string when unavailable.")


class TailoredCVSections(BaseModel):
    work_experience: str = Field(description="Role-tailored work experience section.")
    ibm_assignment_history: str = Field(description="Role-tailored IBM assignment history section.")
    additional_client_history: str = Field(description="Additional client history, or empty string.")
    industry_experience: str = Field(description="Industry experience, or empty string.")
    education: str = Field(description="Education section, or empty string.")
    languages: str = Field(description="Languages section, or empty string.")
    publications: str = Field(description="Publications section, or empty string.")
    memberships: str = Field(description="Memberships section, or empty string.")
    additional_information: str = Field(description="Additional information section, or empty string.")


class CVTailorAgentOutput(BaseModel):
    tailored_cv_text: str = Field(
        min_length=1,
        description="Full tailored CV text ready for user review and editing.",
    )
    tailored_cv_contact: TailoredCVContact = Field(
        description="Contact fields keyed as name, title, phone, and email.",
    )
    tailored_cv_overview: str = Field(
        min_length=1,
        description="Role-tailored overview/professional summary.",
    )
    tailored_skills: list[str] = Field(
        min_length=1,
        description="Role-tailored key skills as short strings.",
    )
    tailored_cv_sections: TailoredCVSections = Field(
        description=(
            "CV Builder sections keyed by work_experience, ibm_assignment_history, "
            "additional_client_history, industry_experience, education, languages, "
            "publications, memberships, and additional_information."
        ),
    )
    changes_summary: list[str] = Field(
        min_length=1,
        description="Concise bullets describing what changed and why.",
    )
    role_alignment: list[str] = Field(
        min_length=1,
        description="Bullets explaining how the tailored CV aligns to the role.",
    )
    missing_experience: list[str] = Field(
        min_length=0,
        description="Relevant gaps or weak evidence the candidate should review.",
    )
    suggested_keywords: list[str] = Field(
        min_length=0,
        description="Role-relevant keywords worth including if factually accurate.",
    )
    warnings: list[str] = Field(
        min_length=0,
        description="Cautions about uncertain, missing, or potentially invented details.",
    )


def _cv_tailor_model() -> str:
    return os.getenv("OPENAI_CV_TAILOR_MODEL", DEFAULT_MODEL)


def _ensure_openai_configured() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your_openai_api_key_here":
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set a real key in backend/.env and restart the backend."
        )


def _cv_tailor_instructions() -> str:
    _ensure_openai_configured()
    return dedent(
        """
        You tailor CVs for IBM professionals applying to internal ProM roles.

        Your job:
        - Rewrite the CV so the most relevant experience, skills, and language
          are prominent for the target seat.
        - Preserve the candidate's factual background. Do not invent employers,
          certifications, dates, project outcomes, clearance, tools, degrees,
          metrics, or client names.
        - If the source CV is thin, create a polished draft from the supplied
          profile data and mark uncertain areas with bracketed placeholders.
        - Keep the tone professional, specific, and scannable.
        - Return a complete CV draft, not just notes.
        - Return structured fields that map directly to the ProM CV Builder:
          tailored_cv_contact, tailored_cv_overview, tailored_skills, and
          tailored_cv_sections.
        - Use these exact tailored_cv_sections keys when content exists:
          work_experience, ibm_assignment_history, additional_client_history,
          industry_experience, education, languages, publications,
          memberships, additional_information.
        - Keep unknown or unavailable optional sections as empty strings.
        - Include a changes summary focused on role alignment decisions.
        - Also return role alignment bullets, gaps, suggested keywords, and warnings.
        """
    ).strip()


def _profile_seed_cv(profile: Profile) -> str:
    skills = ", ".join(profile.skills) if profile.skills else "[Add key skills]"
    return dedent(
        f"""
        {profile.name}

        Professional Summary
        IBM professional with experience across {skills}. Available from
        {profile.availability_date}. Based in {profile.location or "[Add location]"}.

        Skills
        {skills}

        Experience
        [Add recent projects, responsibilities, outcomes, technologies, and client
        context from the source CV or profile repository.]

        Education and Certifications
        [Add relevant education and certifications.]
        """
    ).strip()


def _cv_document_text(cv: CVDocument) -> str:
    contact_lines = [
        cv.cv_contact.get("name"),
        cv.cv_contact.get("title"),
        cv.cv_contact.get("phone"),
        cv.cv_contact.get("email"),
    ]
    contact = "\n".join(line for line in contact_lines if line)
    skills = ", ".join(cv.skills) if cv.skills else "[Add key skills]"
    sections = "\n\n".join(
        f"{key.replace('_', ' ').title()}\n{value}"
        for key, value in cv.cv_sections.items()
        if value
    )

    return dedent(
        f"""
        {contact}

        Professional Summary
        {cv.cv_overview or "[Add professional summary]"}

        Skills
        {skills}

        {sections or "Experience\n[Add relevant experience.]"}
        """
    ).strip()


def _default_cv_for_profile(profile: Profile) -> CVDocument | None:
    cvs = list_cvs(profile.professional_id)
    default = next((cv for cv in cvs if cv.is_default), None)
    return default or (cvs[0] if cvs else None)


async def _fetch_base_cv(profile: Profile) -> str:
    if not profile.cv_repository_url:
        return _profile_seed_cv(profile)

    url = profile.cv_repository_url
    if not url.startswith(("http://", "https://")):
        logger.warning(
            '{"agent": "cv_tailor", "event": "unsupported_cv_repository_url", "professional_id": "%s"}',
            profile.professional_id,
        )
        return _profile_seed_cv(profile)

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text[:MAX_CV_CHARS]


def _seat_context(seat: Seat) -> str:
    return dedent(
        f"""
        Seat ID: {seat.seat_id}
        Title: {seat.title}
        Client: {seat.client_name}
        Service: {seat.service}
        Sector: {seat.sector}
        Industry: {seat.industry}
        Requested band: {seat.requested_band_low} - {seat.requested_band_high}
        Work location: {seat.work_location}
        Remote eligible: {"yes" if seat.work_remotely else "no"}
        Contract country: {seat.contract_owning_country}
        Owner notes ID: {seat.owner_notes_id}
        """
    ).strip()


def _role_context(seat: Seat | None, role_description: str | None) -> str:
    parts = []
    if seat:
        parts.append(_seat_context(seat))
    if role_description:
        parts.append(f"Pasted role description:\n{role_description.strip()}")
    return "\n\n".join(parts).strip()


def _profile_context(profile: Profile) -> str:
    return dedent(
        f"""
        Professional ID: {profile.professional_id}
        Name: {profile.name}
        Band: {profile.band or "[Not provided]"}
        Location: {profile.location or "[Not provided]"}
        Availability: {profile.availability_date}
        Skills: {", ".join(profile.skills) if profile.skills else "[Not provided]"}
        W3 link: {profile.w3_link or "[Not provided]"}
        CV repository URL: {profile.cv_repository_url or "[Not provided]"}
        """
    ).strip()


def _build_prompt(target_role: str, profile: Profile, base_cv: str) -> str:
    return dedent(
        f"""
        Tailor the candidate's CV for this target role.

        Target role:
        {target_role}

        Candidate profile:
        {_profile_context(profile)}

        Source CV:
        {base_cv}
        """
    ).strip()


async def run_cv_tailor(request: CVTailorRequest) -> CVTailorResult:
    profile = get_profile(request.professional_id)
    if not profile:
        raise ValueError(f"Professional profile not found: {request.professional_id}")

    seat = None
    if request.seat_id:
        seat = get_seat_by_id(request.seat_id)
        if not seat:
            raise ValueError(f"Seat not found: {request.seat_id}")

    target_role = _role_context(seat, request.role_description)
    if not target_role:
        raise ValueError("Provide either seat_id or role_description for CV tailoring")

    selected_cv_id = request.cv_id
    if request.source_cv_text:
        base_cv = request.source_cv_text[:MAX_CV_CHARS]
    elif request.cv_id:
        cv = get_cv(request.cv_id)
        if not cv:
            raise ValueError(f"CV not found: {request.cv_id}")
        if cv.professional_id != request.professional_id:
            raise ValueError(f"CV does not belong to professional: {request.cv_id}")
        base_cv = _cv_document_text(cv)[:MAX_CV_CHARS]
    else:
        default_cv = _default_cv_for_profile(profile)
        if default_cv:
            selected_cv_id = default_cv.cv_id
            base_cv = _cv_document_text(default_cv)[:MAX_CV_CHARS]
        else:
            base_cv = await _fetch_base_cv(profile)

    prompt = _build_prompt(target_role, profile, base_cv)
    client = AsyncOpenAI()
    result = await client.chat.completions.parse(
        model=_cv_tailor_model(),
        messages=[
            {"role": "system", "content": _cv_tailor_instructions()},
            {"role": "user", "content": prompt},
        ],
        response_format=CVTailorAgentOutput,
    )
    output = result.choices[0].message.parsed
    if output is None:
        raise RuntimeError("CV tailor returned an empty structured response")

    run = record_cv_agent_run(
        professional_id=request.professional_id,
        cv_id=selected_cv_id,
        role_description=target_role,
        source_cv_text=base_cv,
        tailored_cv_text=output.tailored_cv_text,
        changes=output.changes_summary,
        warnings=output.warnings,
        model=_cv_tailor_model(),
    )

    logger.info(
        '{"agent": "cv_tailor", "seat_id": "%s", "professional_id": "%s", "model": "%s"}',
        request.seat_id,
        request.professional_id,
        _cv_tailor_model(),
    )

    return CVTailorResult(
        seat_id=request.seat_id,
        cv_id=selected_cv_id,
        agent_run_id=run.run_id,
        tailored_cv_text=output.tailored_cv_text,
        tailored_cv_contact=output.tailored_cv_contact.model_dump(),
        tailored_cv_overview=output.tailored_cv_overview,
        tailored_skills=output.tailored_skills,
        tailored_cv_sections=output.tailored_cv_sections.model_dump(),
        changes_summary=output.changes_summary,
        role_alignment=output.role_alignment,
        missing_experience=output.missing_experience,
        suggested_keywords=output.suggested_keywords,
        warnings=output.warnings,
    )

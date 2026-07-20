"""
Agent #7 — AI project recommendations.

Candidate mode: rank open seats for a professional using their CV/skills.
Owner mode: rank applicants already in play for a specific seat.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import date
import re
from textwrap import dedent

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.models.agent import (
    CandidateSeatRecommendation,
    OwnerApplicantRecommendation,
    RecommendationMode,
    RecommendationRequest,
    RecommendationResult,
)
from app.models.cv import CVDocument
from app.models.profile import Profile
from app.models.seat import Seat
from app.services.application_service import list_applicants_for_seat
from app.services.cv_service import get_cv, list_cvs
from app.services.profile_service import get_profile
from app.services.seat_service import get_all_seats, get_seat_by_id

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4.1-mini"
MAX_CV_CHARS = 8_000
MAX_SEATS_FOR_LLM = 20


class _SeatRecLLM(BaseModel):
    seat_id: str
    match_score: float = Field(ge=0.0, le=1.0)
    reason: str
    aligned_skills: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class _CandidateRecsLLM(BaseModel):
    recommendations: list[_SeatRecLLM]
    reasoning: str


class _ApplicantRecLLM(BaseModel):
    professional_id: str
    match_score: float = Field(ge=0.0, le=1.0)
    reason: str
    aligned_skills: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class _OwnerRecsLLM(BaseModel):
    recommendations: list[_ApplicantRecLLM]
    reasoning: str


def _recommendations_model() -> str:
    return os.getenv("OPENAI_RECOMMENDATIONS_MODEL", os.getenv("OPENAI_CV_TAILOR_MODEL", DEFAULT_MODEL))


def _openai_configured() -> bool:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(api_key) and api_key != "your_openai_api_key_here"


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9+#/.]+", text.lower()) if len(token) > 1}


_FRONTEND_SEAT_TOKENS = frozenset({"frontend", "front", "ui", "web", "react", "fullstack", "full", "stack"})
_FRONTEND_SKILL_TOKENS = frozenset(
    {"react", "typescript", "javascript", "vue", "angular", "node", "js", "html", "css"}
)


def _profile_for_applicant(applicant) -> Profile:
    return Profile(
        professional_id=applicant.professional_id,
        name=applicant.name,
        availability_date=date.today(),
        skills=list(applicant.skills or []),
        band=applicant.band,
        location=applicant.location,
    )


def _resolve_applicant_profile(applicant) -> Profile:
    try:
        profile = get_profile(applicant.professional_id)
    except sqlite3.OperationalError:
        profile = None
    if profile:
        return profile
    return _profile_for_applicant(applicant)


def _default_cv_for_profile(profile: Profile, cv_id: str | None = None) -> CVDocument | None:
    if cv_id:
        cv = get_cv(cv_id)
        if cv and cv.professional_id == profile.professional_id:
            return cv
        return None
    cvs = list_cvs(profile.professional_id)
    default = next((cv for cv in cvs if cv.is_default), None)
    return default or (cvs[0] if cvs else None)


def _cv_document_text(cv: CVDocument) -> str:
    skills = ", ".join(cv.skills) if cv.skills else ""
    sections = "\n\n".join(
        f"{key.replace('_', ' ').title()}\n{value}"
        for key, value in cv.cv_sections.items()
        if value
    )
    return dedent(
        f"""
        {cv.cv_contact.get('name') or ''}
        {cv.cv_overview or ''}
        Skills: {skills}
        {sections}
        """
    ).strip()


def _candidate_context(profile: Profile, cv: CVDocument | None) -> tuple[str, list[str]]:
    if cv:
        skills = list(cv.skills) or list(profile.skills)
        text = _cv_document_text(cv)[:MAX_CV_CHARS]
        return text, skills
    skills = list(profile.skills)
    text = dedent(
        f"""
        {profile.name}
        Band: {profile.band or 'unknown'}
        Location: {profile.location or 'unknown'}
        Overview: {profile.cv_overview or ''}
        Skills: {', '.join(skills)}
        """
    ).strip()
    return text, skills


def _seat_context(seat: Seat) -> str:
    return (
        f"{seat.title} | {seat.client_name} | {seat.service} | "
        f"band {seat.requested_band_low}-{seat.requested_band_high} | "
        f"{seat.work_location} | remote={seat.work_remotely} | "
        f"{seat.sector}/{seat.industry} | type={seat.seat_type.value}"
    )


def _available_seats() -> list[Seat]:
    return [
        seat
        for seat in get_all_seats()
        if seat.is_available and not seat.is_expired and seat.seat_type.value == "real"
    ]


def _heuristic_seat_score(skills: list[str], profile: Profile, seat: Seat) -> tuple[float, list[str], list[str]]:
    skill_tokens = _tokenize(" ".join(skills))
    seat_tokens = _tokenize(
        f"{seat.title} {seat.service} {seat.sector} {seat.industry} {seat.client_name}"
    )
    overlap = sorted(skill_tokens & seat_tokens)
    # Also match multi-word skills as substrings against title/service
    aligned = list(overlap)
    haystack = f"{seat.title} {seat.service} {seat.sector} {seat.industry}".lower()
    for skill in skills:
        lowered = skill.lower()
        if lowered in haystack or any(part in seat_tokens for part in _tokenize(skill)):
            if skill not in aligned:
                aligned.append(skill)

    seat_suggests_frontend = bool(seat_tokens & _FRONTEND_SEAT_TOKENS) or "frontend" in haystack
    if seat_suggests_frontend:
        for skill in skills:
            if _tokenize(skill) & _FRONTEND_SKILL_TOKENS and skill not in aligned:
                aligned.append(skill)

    base = min(0.95, 0.35 + 0.12 * len(aligned))
    if profile.band and profile.band in {seat.requested_band_low, seat.requested_band_high}:
        base = min(1.0, base + 0.1)
    if profile.location and profile.location.lower() in seat.work_location.lower():
        base = min(1.0, base + 0.05)
    if seat.work_remotely:
        base = min(1.0, base + 0.03)

    gaps: list[str] = []
    title_tokens = _tokenize(seat.title)
    missing = sorted(title_tokens - skill_tokens)
    gaps = missing[:3]
    return round(base, 2), aligned[:8], gaps


def _heuristic_candidate_recs(
    profile: Profile,
    skills: list[str],
    seats: list[Seat],
    limit: int,
) -> tuple[list[CandidateSeatRecommendation], str]:
    scored: list[CandidateSeatRecommendation] = []
    for seat in seats:
        score, aligned, gaps = _heuristic_seat_score(skills, profile, seat)
        reason = (
            f"Skills and background align with '{seat.title}' "
            f"({', '.join(aligned[:3]) or 'general fit'})."
        )
        scored.append(
            CandidateSeatRecommendation(
                seat_id=seat.seat_id,
                title=seat.title,
                client_name=seat.client_name,
                match_score=score,
                reason=reason,
                aligned_skills=aligned,
                gaps=gaps,
            )
        )
    scored.sort(key=lambda item: item.match_score, reverse=True)
    top = scored[:limit]
    reasoning = (
        f"Ranked {len(top)} open seats for {profile.name} using CV/skills overlap "
        f"(heuristic fallback)."
    )
    return top, reasoning


def _heuristic_owner_recs(
    seat: Seat,
    applicants: list,
    limit: int,
) -> tuple[list[OwnerApplicantRecommendation], str]:
    scored: list[OwnerApplicantRecommendation] = []
    for applicant in applicants:
        profile = _resolve_applicant_profile(applicant)
        score, aligned, gaps = _heuristic_seat_score(applicant.skills or profile.skills, profile, seat)
        scored.append(
            OwnerApplicantRecommendation(
                professional_id=applicant.professional_id,
                name=applicant.name,
                application_id=applicant.application_id,
                status=applicant.status.value if hasattr(applicant.status, "value") else str(applicant.status),
                match_score=score,
                reason=(
                    f"{applicant.name.split('/')[0]} matches '{seat.title}' based on "
                    f"{', '.join(aligned[:3]) or 'profile signals'}."
                ),
                aligned_skills=aligned,
                gaps=gaps,
                band=applicant.band,
                location=applicant.location,
            )
        )
    scored.sort(key=lambda item: item.match_score, reverse=True)
    top = scored[:limit]
    reasoning = (
        f"Ranked {len(top)} in-play applicants for '{seat.title}' using skills overlap "
        f"(heuristic fallback)."
    )
    return top, reasoning


async def _llm_candidate_recs(
    profile: Profile,
    cv_text: str,
    skills: list[str],
    seats: list[Seat],
    limit: int,
) -> tuple[list[CandidateSeatRecommendation], str]:
    seat_map = {seat.seat_id: seat for seat in seats}
    seat_block = "\n".join(f"- {seat.seat_id}: {_seat_context(seat)}" for seat in seats[:MAX_SEATS_FOR_LLM])
    instructions = dedent(
        """
        You recommend IBM Professional Marketplace open seats for a candidate.
        Rank only from the provided seat list. Do not invent seats or employers.
        Prefer stronger evidence from skills and experience. Scores must be 0-1.
        Keep reasons concise and grounded in the CV.
        """
    ).strip()
    prompt = dedent(
        f"""
        Candidate profile:
        Name: {profile.name}
        Band: {profile.band}
        Location: {profile.location}
        Skills: {', '.join(skills)}

        CV:
        {cv_text}

        Open seats:
        {seat_block}

        Return the top {limit} seats only, best match first.
        """
    ).strip()

    client = AsyncOpenAI()
    result = await client.chat.completions.parse(
        model=_recommendations_model(),
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
        response_format=_CandidateRecsLLM,
    )
    parsed = result.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("Recommendations model returned an empty response")

    recommendations: list[CandidateSeatRecommendation] = []
    for item in parsed.recommendations:
        seat = seat_map.get(item.seat_id)
        if not seat:
            continue
        recommendations.append(
            CandidateSeatRecommendation(
                seat_id=seat.seat_id,
                title=seat.title,
                client_name=seat.client_name,
                match_score=item.match_score,
                reason=item.reason,
                aligned_skills=item.aligned_skills,
                gaps=item.gaps,
            )
        )
    recommendations.sort(key=lambda item: item.match_score, reverse=True)
    return recommendations[:limit], parsed.reasoning


async def _llm_owner_recs(
    seat: Seat,
    applicants: list,
    limit: int,
) -> tuple[list[OwnerApplicantRecommendation], str]:
    applicant_map = {a.professional_id: a for a in applicants}
    blocks = []
    for applicant in applicants:
        profile = get_profile(applicant.professional_id)
        cv = _default_cv_for_profile(profile) if profile else None
        cv_text, skills = _candidate_context(profile, cv) if profile else ("", [])
        blocks.append(
            dedent(
                f"""
                Applicant {applicant.professional_id}:
                Name: {applicant.name}
                Status: {applicant.status}
                Band: {applicant.band}
                Location: {applicant.location}
                Skills: {', '.join(skills or applicant.skills)}
                CV excerpt:
                {cv_text[:2500]}
                """
            ).strip()
        )

    instructions = dedent(
        """
        You rank applicants already in play for one IBM ProM seat.
        Only rank people from the provided applicant list. Do not invent applicants.
        Scores must be 0-1 and reasons must cite skills/experience evidence.
        """
    ).strip()
    prompt = dedent(
        f"""
        Seat:
        {_seat_context(seat)}

        Applicants in play:
        {chr(10).join(blocks)}

        Return up to {limit} applicants, best match first.
        """
    ).strip()

    client = AsyncOpenAI()
    result = await client.chat.completions.parse(
        model=_recommendations_model(),
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
        response_format=_OwnerRecsLLM,
    )
    parsed = result.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("Owner recommendations model returned an empty response")

    recommendations: list[OwnerApplicantRecommendation] = []
    for item in parsed.recommendations:
        applicant = applicant_map.get(item.professional_id)
        if not applicant:
            continue
        recommendations.append(
            OwnerApplicantRecommendation(
                professional_id=applicant.professional_id,
                name=applicant.name,
                application_id=applicant.application_id,
                status=applicant.status.value if hasattr(applicant.status, "value") else str(applicant.status),
                match_score=item.match_score,
                reason=item.reason,
                aligned_skills=item.aligned_skills,
                gaps=item.gaps,
                band=applicant.band,
                location=applicant.location,
            )
        )
    recommendations.sort(key=lambda item: item.match_score, reverse=True)
    return recommendations[:limit], parsed.reasoning


async def run_recommendations(request: RecommendationRequest) -> RecommendationResult:
    profile = get_profile(request.professional_id)
    if not profile:
        raise LookupError(f"Professional profile not found: {request.professional_id}")

    warnings: list[str] = []
    source = "heuristic"

    if request.mode == RecommendationMode.CANDIDATE:
        if request.cv_id:
            cv = _default_cv_for_profile(profile, request.cv_id)
            if not cv:
                raise LookupError(f"CV not found for professional: {request.cv_id}")
        else:
            cv = _default_cv_for_profile(profile)
            if not cv:
                warnings.append("No CV in repository; using profile skills and overview.")

        cv_text, skills = _candidate_context(profile, cv)
        seats = _available_seats()
        if not seats:
            return RecommendationResult(
                professional_id=request.professional_id,
                mode=request.mode,
                recommendations=[],
                reasoning="No available open seats to recommend.",
                source="heuristic",
                warnings=warnings,
            )

        if _openai_configured():
            try:
                recs, reasoning = await _llm_candidate_recs(
                    profile, cv_text, skills, seats, request.limit
                )
                source = "openai"
            except Exception as exc:  # noqa: BLE001 — fall back for demo resilience
                logger.warning('{"agent":"recommendations","fallback":"heuristic","error":"%s"}', exc)
                warnings.append(f"OpenAI ranking unavailable; used heuristic fallback ({exc}).")
                recs, reasoning = _heuristic_candidate_recs(profile, skills, seats, request.limit)
        else:
            warnings.append("OPENAI_API_KEY not configured; used heuristic skill matching.")
            recs, reasoning = _heuristic_candidate_recs(profile, skills, seats, request.limit)

        logger.info(
            '{"agent":"recommendations","mode":"candidate","professional_id":"%s","count":%d,"source":"%s"}',
            request.professional_id,
            len(recs),
            source,
        )
        return RecommendationResult(
            professional_id=request.professional_id,
            mode=request.mode,
            recommendations=recs,
            reasoning=reasoning,
            source=source,
            warnings=warnings,
        )

    # Owner mode
    if not request.seat_id:
        raise ValueError("seat_id is required for owner mode recommendations")

    seat = get_seat_by_id(request.seat_id)
    if not seat:
        raise LookupError(f"Seat not found: {request.seat_id}")

    if seat.owner_professional_id and seat.owner_professional_id != request.professional_id:
        raise PermissionError("Not authorized to rank applicants for this listing")

    applicants = list_applicants_for_seat(request.seat_id)
    if not applicants:
        return RecommendationResult(
            professional_id=request.professional_id,
            mode=request.mode,
            seat_id=request.seat_id,
            recommendations=[],
            reasoning=f"No applicants currently in play for '{seat.title}'.",
            source="heuristic",
            warnings=warnings,
        )

    if _openai_configured():
        try:
            recs, reasoning = await _llm_owner_recs(seat, applicants, request.limit)
            source = "openai"
        except Exception as exc:  # noqa: BLE001
            logger.warning('{"agent":"recommendations","fallback":"heuristic","error":"%s"}', exc)
            warnings.append(f"OpenAI ranking unavailable; used heuristic fallback ({exc}).")
            recs, reasoning = _heuristic_owner_recs(seat, applicants, request.limit)
    else:
        warnings.append("OPENAI_API_KEY not configured; used heuristic skill matching.")
        recs, reasoning = _heuristic_owner_recs(seat, applicants, request.limit)

    logger.info(
        '{"agent":"recommendations","mode":"owner","seat_id":"%s","count":%d,"source":"%s"}',
        request.seat_id,
        len(recs),
        source,
    )
    return RecommendationResult(
        professional_id=request.professional_id,
        mode=request.mode,
        seat_id=request.seat_id,
        recommendations=recs,
        reasoning=reasoning,
        source=source,
        warnings=warnings,
    )

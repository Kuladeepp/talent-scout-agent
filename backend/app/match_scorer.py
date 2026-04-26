"""Stage 3: per-candidate match scoring (parallel Gemini 2.5 Pro calls)."""
from __future__ import annotations

import asyncio
import json

from app.cache import disk_cache
from app.config import settings
from app.gemini_client import generate_json
from app.models import Candidate, JDStruct, MatchResult

MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "match_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "reasoning": {"type": "string"},
        "matched_skills": {"type": "array", "items": {"type": "string"}},
        "missing_skills": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["match_score", "reasoning", "matched_skills", "missing_skills"],
}

MATCH_SYSTEM = (
    "You score how well a candidate matches a job description on a 0-100 scale. "
    "Be honest and calibrated: 90+ is exceptional fit; 70-89 is strong; 50-69 is plausible "
    "with gaps; below 50 means real misalignment. Cite specific skill matches and gaps. "
    "Reasoning must be 1-2 sentences, recruiter-readable."
)


def _prompt(jd: JDStruct, c: Candidate) -> str:
    return (
        f"JOB DESCRIPTION:\n"
        f"  Role: {jd.role}\n"
        f"  Required skills: {', '.join(jd.skills_required) or 'none'}\n"
        f"  Nice-to-have: {', '.join(jd.skills_nice) or 'none'}\n"
        f"  Experience: {jd.experience_min}-{jd.experience_max} years\n"
        f"  Location: {jd.location}\n"
        f"  Must-haves: {', '.join(jd.must_haves) or 'none'}\n"
        f"  Soft skills: {', '.join(jd.soft_skills) or 'none'}\n\n"
        f"CANDIDATE:\n"
        f"  Title: {c.title}\n"
        f"  Skills: {', '.join(c.skills)}\n"
        f"  Experience: {c.experience_years} years\n"
        f"  Location: {c.location}\n"
        f"  Summary: {c.summary}\n\n"
        f"Score this match."
    )


async def score_one(jd: JDStruct, candidate: Candidate) -> MatchResult:
    cache_key = disk_cache.key(
        f"{jd.model_dump_json()}|{candidate.id}", "match_score",
    )
    cached = disk_cache.get(cache_key)
    if cached:
        return MatchResult.model_validate(cached)

    try:
        raw = await generate_json(
            model=settings.model_pro,
            prompt=_prompt(jd, candidate),
            schema=MATCH_SCHEMA,
            system=MATCH_SYSTEM,
            temperature=0.3,
        )
        result = MatchResult(candidate_id=candidate.id, **raw)
    except Exception as e:
        # Fail soft: assign neutral score so candidate still appears
        result = MatchResult(
            candidate_id=candidate.id,
            match_score=0,
            reasoning=f"Scoring error: {e!s}",
            matched_skills=[],
            missing_skills=[],
        )

    disk_cache.put(cache_key, result.model_dump())
    return result


async def score_many(jd: JDStruct, candidates: list[Candidate]) -> list[MatchResult]:
    return await asyncio.gather(*[score_one(jd, c) for c in candidates])

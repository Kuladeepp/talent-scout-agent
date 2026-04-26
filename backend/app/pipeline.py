"""Orchestrates the full 5-stage pipeline."""
from __future__ import annotations

import asyncio

from app.candidate_pool import pool
from app.config import settings
from app.gemini_client import embed
from app.jd_ingest import ingest
from app.match_scorer import score_many
from app.models import (
    Candidate, JDStruct, MatchResult, ScoutRequest, ScoutResponse,
)
from app.outreach_sim import outreach_many
from app.ranker import combine


def _jd_query_text(jd: JDStruct) -> str:
    return (
        f"Role: {jd.role}. "
        f"Required skills: {', '.join(jd.skills_required)}. "
        f"Nice to have: {', '.join(jd.skills_nice)}. "
        f"Location: {jd.location}. "
        f"Experience: {jd.experience_min}-{jd.experience_max} years."
    )


async def _retrieve(jd: JDStruct) -> list[Candidate]:
    qvec = await embed(_jd_query_text(jd))
    hits = pool.top_k(qvec, k=settings.top_k_retrieve, floor=settings.similarity_floor)
    return [pool.get(cid) for cid, _ in hits]


async def run(req: ScoutRequest) -> ScoutResponse:
    jd = await ingest(jd_text=req.jd_text, jd_url=req.jd_url)
    candidates = await _retrieve(jd)
    if not candidates:
        return ScoutResponse(
            jd=jd, ranked=[], conversations={}, match_details={},
            interest_details={}, weights=req.weights,
        )

    matches = await score_many(jd, candidates)
    cand_lookup = {c.id: c for c in candidates}

    # Stage 4: top N by match score -> simulated outreach
    top_for_outreach = sorted(matches, key=lambda m: m.match_score, reverse=True)[: settings.top_k_outreach]
    outreach_pairs = [(cand_lookup[m.candidate_id], m) for m in top_for_outreach]
    interests = await outreach_many(jd, outreach_pairs)

    ranked = combine(cand_lookup, matches, interests, req.weights)

    return ScoutResponse(
        jd=jd,
        ranked=ranked,
        conversations={i.candidate_id: i.conversation for i in interests},
        match_details={m.candidate_id: m for m in matches},
        interest_details={i.candidate_id: i for i in interests},
        weights=req.weights,
    )

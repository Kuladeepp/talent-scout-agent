"""Stage 5: combine match and interest scores with tunable weights."""
from __future__ import annotations

from app.models import Candidate, InterestResult, MatchResult, RankedRow


def combine(
    candidates: dict[str, Candidate],
    matches: list[MatchResult],
    interests: list[InterestResult],
    weights: dict[str, float],
) -> list[RankedRow]:
    """Produce a ranked list. Candidates without an interest result get final_score = match_score."""
    interest_by_id: dict[str, InterestResult] = {i.candidate_id: i for i in interests}
    w_match = float(weights.get("match", 0.6))
    w_interest = float(weights.get("interest", 0.4))

    rows: list[RankedRow] = []
    for m in matches:
        c = candidates[m.candidate_id]
        ir = interest_by_id.get(m.candidate_id)
        if ir is None:
            interest_score: int | None = None
            interest_summary: str | None = None
            final = float(m.match_score)
        else:
            interest_score = ir.interest_score
            interest_summary = ir.summary
            final = w_match * m.match_score + w_interest * ir.interest_score
        rows.append(RankedRow(
            candidate_id=c.id, name=c.name, title=c.title,
            match_score=m.match_score,
            interest_score=interest_score,
            final_score=round(final, 2),
            match_reasoning=m.reasoning,
            interest_summary=interest_summary,
        ))
    rows.sort(key=lambda r: r.final_score, reverse=True)
    return rows

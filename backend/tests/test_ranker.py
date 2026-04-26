from app.models import (
    Candidate, MatchResult, InterestResult, Conversation,
)
from app.ranker import combine


def _candidate(cid: str = "c001") -> Candidate:
    return Candidate(
        id=cid, name="Alex", title="Backend",
        skills=["Python"], experience_years=5, location="Remote",
        summary="x", hidden_interest_profile="passive",
    )


def _match(cid: str, score: int) -> MatchResult:
    return MatchResult(candidate_id=cid, match_score=score, reasoning="r",
                       matched_skills=[], missing_skills=[])


def _interest(cid: str, score: int | None) -> InterestResult:
    return InterestResult(
        candidate_id=cid,
        interest_score=score if score is not None else 0,
        signals=[], summary="s" if score is not None else "missing",
        conversation=Conversation(turns=[]),
    )


def test_combine_basic_weights():
    cands = {"c001": _candidate("c001")}
    matches = [_match("c001", 80)]
    interests = [_interest("c001", 60)]
    rows = combine(cands, matches, interests, {"match": 0.5, "interest": 0.5})
    assert rows[0].final_score == 70.0
    assert rows[0].interest_score == 60


def test_combine_default_weights():
    cands = {"c001": _candidate("c001")}
    matches = [_match("c001", 80)]
    interests = [_interest("c001", 50)]
    rows = combine(cands, matches, interests, {"match": 0.6, "interest": 0.4})
    # 0.6*80 + 0.4*50 = 48 + 20 = 68
    assert rows[0].final_score == 68.0


def test_combine_missing_interest_falls_back_to_match_only():
    cands = {"c001": _candidate("c001")}
    matches = [_match("c001", 80)]
    interests: list = []  # Stage 4 didn't run for this candidate
    rows = combine(cands, matches, interests, {"match": 0.6, "interest": 0.4})
    assert rows[0].interest_score is None
    assert rows[0].final_score == 80.0


def test_combine_sorts_descending():
    cands = {"c001": _candidate("c001"), "c002": _candidate("c002")}
    matches = [_match("c001", 60), _match("c002", 90)]
    interests = [_interest("c001", 90), _interest("c002", 50)]
    rows = combine(cands, matches, interests, {"match": 0.5, "interest": 0.5})
    # c001: 0.5*60 + 0.5*90 = 75
    # c002: 0.5*90 + 0.5*50 = 70
    assert rows[0].candidate_id == "c001"
    assert rows[0].final_score == 75.0

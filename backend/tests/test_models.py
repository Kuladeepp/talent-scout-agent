from app.models import (
    JDStruct, Candidate, MatchResult, Conversation,
    ConversationTurn, InterestResult, RankedRow, ScoutResponse,
)


def test_jdstruct_minimal():
    jd = JDStruct(
        role="Backend Engineer",
        skills_required=["Python"],
        skills_nice=[],
        experience_min=2,
        experience_max=5,
        location="Remote",
        must_haves=[],
        soft_skills=[],
    )
    assert jd.role == "Backend Engineer"


def test_candidate_minimal():
    c = Candidate(
        id="c001",
        name="Alex Doe",
        title="Backend Engineer",
        skills=["Python", "Django"],
        experience_years=4,
        location="Bengaluru",
        summary="4 years building APIs.",
        hidden_interest_profile="passive",
    )
    assert c.hidden_interest_profile in {"actively_looking", "passive", "not_looking"}


def test_match_result_bounds():
    mr = MatchResult(
        candidate_id="c001",
        match_score=87,
        reasoning="Solid backend fit.",
        matched_skills=["Python"],
        missing_skills=["AWS"],
    )
    assert 0 <= mr.match_score <= 100


def test_interest_result():
    ir = InterestResult(
        candidate_id="c001",
        interest_score=72,
        signals=["asked about salary"],
        summary="Passively interested.",
        conversation=Conversation(turns=[
            ConversationTurn(speaker="recruiter", text="Hi"),
            ConversationTurn(speaker="candidate", text="Hello"),
        ]),
    )
    assert ir.conversation.turns[0].speaker == "recruiter"


def test_ranked_row_and_response():
    row = RankedRow(
        candidate_id="c001",
        name="Alex",
        title="Backend Engineer",
        match_score=80,
        interest_score=70,
        final_score=76,
        match_reasoning="x",
        interest_summary="y",
    )
    resp = ScoutResponse(
        jd=JDStruct(
            role="r", skills_required=[], skills_nice=[],
            experience_min=0, experience_max=10, location="",
            must_haves=[], soft_skills=[],
        ),
        ranked=[row],
        conversations={"c001": Conversation(turns=[])},
        match_details={"c001": MatchResult(
            candidate_id="c001", match_score=80, reasoning="",
            matched_skills=[], missing_skills=[],
        )},
        interest_details={"c001": InterestResult(
            candidate_id="c001", interest_score=70, signals=[], summary="",
            conversation=Conversation(turns=[]),
        )},
        weights={"match": 0.6, "interest": 0.4},
    )
    assert resp.ranked[0].final_score == 76

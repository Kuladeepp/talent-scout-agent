from typing import Literal
from pydantic import BaseModel, Field, conint, confloat


InterestProfile = Literal["actively_looking", "passive", "not_looking"]


class JDStruct(BaseModel):
    role: str
    skills_required: list[str]
    skills_nice: list[str]
    experience_min: int
    experience_max: int
    location: str
    must_haves: list[str]
    soft_skills: list[str]


class Candidate(BaseModel):
    id: str
    name: str
    title: str
    skills: list[str]
    experience_years: int
    location: str
    summary: str
    hidden_interest_profile: InterestProfile


class MatchResult(BaseModel):
    candidate_id: str
    match_score: conint(ge=0, le=100)
    reasoning: str
    matched_skills: list[str]
    missing_skills: list[str]


class ConversationTurn(BaseModel):
    speaker: Literal["recruiter", "candidate"]
    text: str


class Conversation(BaseModel):
    turns: list[ConversationTurn] = Field(default_factory=list)


class InterestResult(BaseModel):
    candidate_id: str
    interest_score: conint(ge=0, le=100)
    signals: list[str]
    summary: str
    conversation: Conversation


class RankedRow(BaseModel):
    candidate_id: str
    name: str
    title: str
    match_score: conint(ge=0, le=100)
    interest_score: int | None  # null if Stage 4 failed
    final_score: confloat(ge=0, le=100)
    match_reasoning: str
    interest_summary: str | None


class ScoutRequest(BaseModel):
    jd_text: str | None = None
    jd_url: str | None = None
    weights: dict[str, float] = Field(default_factory=lambda: {"match": 0.6, "interest": 0.4})


class ScoutResponse(BaseModel):
    jd: JDStruct
    ranked: list[RankedRow]
    conversations: dict[str, Conversation]
    match_details: dict[str, MatchResult]
    interest_details: dict[str, InterestResult]
    weights: dict[str, float]

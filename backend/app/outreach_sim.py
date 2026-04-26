"""Stage 4: simulate a 4-turn recruiter<->candidate conversation, then score interest.

Conversation structure:
  Turn 1 (recruiter): personalized opener referencing match reasoning
  Turn 2 (candidate): persona-driven response (open / lukewarm / declining)
  Turn 3 (recruiter): respond to candidate, surface compensation/role specifics
  Turn 4 (candidate): final position -- concrete signals (availability, blockers)
Then a separate Gemini 2.5 Pro call scores the transcript on 0-100 interest.
"""
from __future__ import annotations

import asyncio
import json

from app.cache import disk_cache
from app.config import settings
from app.gemini_client import generate_json, generate_text
from app.models import (
    Candidate, Conversation, ConversationTurn, InterestResult, JDStruct, MatchResult,
)

INTEREST_SCHEMA = {
    "type": "object",
    "properties": {
        "interest_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "signals": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["interest_score", "signals", "summary"],
}

RECRUITER_SYSTEM = (
    "You are a senior technical recruiter reaching out to a passive candidate. "
    "Be warm, specific, and concise -- never spammy. Reference concrete reasons this role fits the candidate. "
    "Each message must be 2-4 sentences, max ~80 words. Do not use bullet points. "
    "If the candidate asks about compensation, location, or growth, answer plausibly."
)

CANDIDATE_SYSTEM_TEMPLATE = (
    "You are roleplaying as a candidate named {name}, currently a {title} with {years} years of experience, "
    "based in {location}. Your hidden interest level is: {profile}. "
    "- actively_looking: respond enthusiastically, ask specific questions about role/comp/team. "
    "- passive: respond politely but cautiously, raise 1-2 concerns (e.g. timing, location, comp), open to learning more. "
    "- not_looking: politely decline; only continue if the recruiter surfaces something exceptional. "
    "Stay in character. Each message must be 1-3 sentences. Never break character or mention you are an AI."
)


def _opener_prompt(jd: JDStruct, c: Candidate, m: MatchResult) -> str:
    return (
        f"Write the opening message to {c.name}. They are a {c.title} based in {c.location}.\n\n"
        f"Job: {jd.role} ({jd.location}, {jd.experience_min}-{jd.experience_max} yrs).\n"
        f"Why they fit (use this, do not repeat verbatim): {m.reasoning}\n\n"
        f"Write the message now (no greeting label, just the message body)."
    )


def _candidate_prompt(history: list[ConversationTurn]) -> str:
    transcript = "\n".join(f"{t.speaker.upper()}: {t.text}" for t in history)
    return f"Conversation so far:\n{transcript}\n\nWrite your next reply as the candidate."


def _recruiter_followup_prompt(jd: JDStruct, c: Candidate, history: list[ConversationTurn]) -> str:
    transcript = "\n".join(f"{t.speaker.upper()}: {t.text}" for t in history)
    return (
        f"Conversation so far:\n{transcript}\n\n"
        f"Continue as the recruiter. The role is {jd.role} at a growing team. "
        f"If asked about compensation, give a plausible band (e.g., 'INR 40-55L total comp' for India, "
        f"'$160k-200k base' for US). If asked about location, the role is {jd.location}. "
        f"Acknowledge the candidate's previous concerns. Write the next message."
    )


def _interest_prompt(jd: JDStruct, c: Candidate, conv: Conversation) -> str:
    transcript = "\n".join(f"{t.speaker.upper()}: {t.text}" for t in conv.turns)
    return (
        f"JOB: {jd.role}\n"
        f"CANDIDATE: {c.name} ({c.title})\n\n"
        f"TRANSCRIPT:\n{transcript}\n\n"
        f"Score this candidate's genuine interest (0-100). 80+ = clearly engaged and likely to advance; "
        f"50-79 = open with concrete blockers; 20-49 = polite but uninterested; under 20 = clear no. "
        f"List the specific signals (quotes or paraphrases) you used. Write a 1-sentence summary."
    )


async def converse(jd: JDStruct, c: Candidate, m: MatchResult) -> Conversation:
    """Run the 4-turn back-and-forth."""
    candidate_system = CANDIDATE_SYSTEM_TEMPLATE.format(
        name=c.name, title=c.title, years=c.experience_years,
        location=c.location, profile=c.hidden_interest_profile,
    )

    turns: list[ConversationTurn] = []
    # Turn 1: recruiter opener
    opener = await generate_text(
        settings.model_flash, _opener_prompt(jd, c, m),
        system=RECRUITER_SYSTEM, temperature=0.7,
    )
    turns.append(ConversationTurn(speaker="recruiter", text=opener.strip()))

    # Turn 2: candidate
    reply2 = await generate_text(
        settings.model_flash, _candidate_prompt(turns),
        system=candidate_system, temperature=0.8,
    )
    turns.append(ConversationTurn(speaker="candidate", text=reply2.strip()))

    # Turn 3: recruiter follow-up
    reply3 = await generate_text(
        settings.model_flash, _recruiter_followup_prompt(jd, c, turns),
        system=RECRUITER_SYSTEM, temperature=0.7,
    )
    turns.append(ConversationTurn(speaker="recruiter", text=reply3.strip()))

    # Turn 4: candidate close
    reply4 = await generate_text(
        settings.model_flash, _candidate_prompt(turns),
        system=candidate_system, temperature=0.8,
    )
    turns.append(ConversationTurn(speaker="candidate", text=reply4.strip()))

    return Conversation(turns=turns)


async def score_interest(jd: JDStruct, c: Candidate, conv: Conversation) -> InterestResult:
    raw = await generate_json(
        model=settings.model_pro,
        prompt=_interest_prompt(jd, c, conv),
        schema=INTEREST_SCHEMA,
        thinking_level="MEDIUM",
        temperature=0.2,
    )
    return InterestResult(
        candidate_id=c.id,
        interest_score=raw["interest_score"],
        signals=raw["signals"],
        summary=raw["summary"],
        conversation=conv,
    )


async def outreach_one(jd: JDStruct, c: Candidate, m: MatchResult) -> InterestResult:
    cache_key = disk_cache.key(
        f"{jd.model_dump_json()}|{c.id}|{m.match_score}", "outreach",
    )
    cached = disk_cache.get(cache_key)
    if cached:
        return InterestResult.model_validate(cached)

    try:
        conv = await converse(jd, c, m)
        result = await score_interest(jd, c, conv)
    except Exception as e:
        result = InterestResult(
            candidate_id=c.id,
            interest_score=0,
            signals=[],
            summary=f"Outreach error: {e!s}",
            conversation=Conversation(turns=[]),
        )

    disk_cache.put(cache_key, result.model_dump())
    return result


async def outreach_many(
    jd: JDStruct, items: list[tuple[Candidate, MatchResult]],
) -> list[InterestResult]:
    return await asyncio.gather(*[outreach_one(jd, c, m) for c, m in items])


async def explain_conversation(jd: JDStruct, c: Candidate, conv: Conversation, score: int) -> str:
    transcript = "\n".join(f"{t.speaker.upper()}: {t.text}" for t in conv.turns)
    prompt = (
        f"This candidate received an interest score of {score}/100 for the role: {jd.role}.\n\n"
        f"TRANSCRIPT:\n{transcript}\n\n"
        f"In 3-4 sentences, explain WHY this score was assigned. Quote specific phrases from the transcript. "
        f"Note any blockers, positive signals, or open questions a recruiter should follow up on."
    )
    return await generate_text(settings.model_pro, prompt, temperature=0.3)

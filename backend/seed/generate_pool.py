"""One-shot script: generate 200 synthetic candidates with Claude Opus.

Usage:
    cd backend && python -m seed.generate_pool

Writes:
    data/candidates.db   (SQLite)
    data/raw_pool.json   (raw model output, for audit)
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import anthropic

from app.config import settings
from app.models import Candidate

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "candidates.db"
RAW_PATH = DATA_DIR / "raw_pool.json"

# Generate in 4 batches of 50 to stay within output token limits and get variety
BATCH_SIZE = 50
NUM_BATCHES = 4

ROLE_FAMILIES = [
    "Backend Engineer (Python/Django/FastAPI)",
    "Backend Engineer (Java/Spring or Go)",
    "Frontend Engineer (React/TypeScript)",
    "Full-stack Engineer",
    "Mobile Engineer (iOS/Swift or Android/Kotlin)",
    "ML Engineer (LLMs, training, inference)",
    "Data Engineer (Spark, Airflow, dbt)",
    "Data Scientist",
    "DevOps / SRE",
    "Security Engineer",
    "Product Designer",
    "UX Researcher",
    "Product Manager",
    "Engineering Manager",
    "QA / SDET",
]

INTEREST_PROFILES = ["actively_looking", "passive", "not_looking"]

PROMPT_TEMPLATE = """You are generating realistic synthetic candidate profiles for a recruiting product demo.

Generate exactly {n} candidates as a JSON array. Each candidate object must match this schema:

{{
  "id": "c{batch_prefix}NNN",        // c001..c050 for batch 1, c051..c100 for batch 2, etc.
  "name": "First Last",
  "title": "Specific job title",
  "skills": ["..."],                  // 5-12 specific skills, mix of technical and tool names
  "experience_years": 0-25,
  "location": "City, Country",        // mix of remote/hybrid/onsite cities globally; bias toward India + US + EU
  "summary": "2-4 sentence career summary written in third person, specific about projects and outcomes.",
  "hidden_interest_profile": "actively_looking" | "passive" | "not_looking"
}}

Rules to make this pool realistic and useful for a matching demo:
1. Spread across these role families: {roles}
2. Vary experience: ~20% junior (0-2 yrs), ~50% mid (3-7 yrs), ~25% senior (8-15 yrs), ~5% staff/principal (15+ yrs)
3. Inject deliberate gaps: some candidates strong in core skills but missing common adjacent ones (e.g. backend dev with no AWS); some with mismatched titles vs actual skill stack
4. Mix interest profiles roughly 30% actively_looking, 50% passive, 20% not_looking
5. Use varied summary writing styles -- some terse, some detailed
6. Include realistic-sounding names from diverse backgrounds (Indian, Western, East Asian, European, African)
7. Locations: include Bengaluru, Hyderabad, Pune, Mumbai, Delhi NCR, Remote (India), San Francisco, NYC, Austin, Berlin, London, Singapore, Toronto, Remote (EU)
8. Skills should be specific tool/framework names, not generic ("LangChain" not "AI"; "PostgreSQL" not "databases")

This batch covers IDs c{id_lo:03d} through c{id_hi:03d}.

Output ONLY the JSON array. No prose, no markdown fences."""


def call_opus(client: anthropic.Anthropic, batch_idx: int) -> list[dict]:
    id_lo = batch_idx * BATCH_SIZE + 1
    id_hi = (batch_idx + 1) * BATCH_SIZE
    prompt = PROMPT_TEMPLATE.format(
        n=BATCH_SIZE,
        batch_prefix="",
        roles=", ".join(ROLE_FAMILIES),
        id_lo=id_lo,
        id_hi=id_hi,
    )
    msg = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # Strip accidental fences just in case
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0]
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"Batch {batch_idx}: expected JSON array, got {type(data)}")
    return data


def main() -> int:
    if not settings.anthropic_api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    all_candidates: list[dict] = []

    for batch_idx in range(NUM_BATCHES):
        print(f"Generating batch {batch_idx + 1}/{NUM_BATCHES}...")
        batch = call_opus(client, batch_idx)
        # Renumber IDs to be globally unique and zero-padded
        for i, c in enumerate(batch):
            c["id"] = f"c{batch_idx * BATCH_SIZE + i + 1:03d}"
        all_candidates.extend(batch)
        print(f"  got {len(batch)} candidates")

    # Validate every candidate against pydantic model
    validated: list[Candidate] = []
    for c in all_candidates:
        try:
            validated.append(Candidate.model_validate(c))
        except Exception as e:
            print(f"  WARN: dropped invalid candidate {c.get('id')}: {e}", file=sys.stderr)

    print(f"Validated {len(validated)} / {len(all_candidates)} candidates")

    # Save raw for audit
    RAW_PATH.write_text(json.dumps(all_candidates, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write SQLite
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE candidates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            skills_json TEXT NOT NULL,
            experience_years INTEGER NOT NULL,
            location TEXT NOT NULL,
            summary TEXT NOT NULL,
            hidden_interest_profile TEXT NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO candidates VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                c.id, c.name, c.title, json.dumps(c.skills),
                c.experience_years, c.location, c.summary,
                c.hidden_interest_profile,
            )
            for c in validated
        ],
    )
    conn.commit()
    conn.close()

    print(f"Wrote {DB_PATH} and {RAW_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

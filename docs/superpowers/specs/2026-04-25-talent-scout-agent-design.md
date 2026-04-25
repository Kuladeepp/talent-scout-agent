# AI-Powered Talent Scouting & Engagement Agent — Design Spec

**Project:** Catalyst Hackathon Submission
**Deadline:** 2026-04-27, 01:00 IST
**Author:** sravyap2219@gmail.com
**Date:** 2026-04-25

---

## 1. Problem Statement

Recruiters spend hours sifting through profiles and chasing candidate interest. Build an AI agent that:

1. Takes a Job Description as input (text or URL)
2. Discovers matching candidates from a pool
3. Engages them conversationally to assess genuine interest
4. Outputs a ranked shortlist scored on **Match Score** and **Interest Score**

Submission requirements: working prototype (deployed), public repo + README, 3–5 min demo video, architecture diagram, sample inputs/outputs.

---

## 2. Scope Decision

**Candidate source: synthetic pool of 200 pre-generated profiles.**

Rationale: judges score the *agent's intelligence*, not the data source. The synthetic pool is framed honestly as the "recruiter's existing ATS database" (the same data layer Greenhouse/Lever operate on). The candidate-source layer is pluggable; LinkedIn/GitHub/ATS swap-in is a one-line README note. Avoids scraping legality, rate-limit fights, and split pipelines that would consume the bandwidth needed for the actual differentiator (Stage 4).

**Out of scope:** real candidate scraping, authentication, multi-tenancy, persistence beyond the demo session, email/SMS delivery (outreach is *simulated*), recruiter accounts, billing.

---

## 3. End-to-End Workflow

### Stage 1 — JD Ingestion
- **Input:** raw JD text *or* a job posting URL
- **If URL:** Firecrawl scrapes the page → markdown
- **Parse:** Gemini (via Vertex AI) returns structured JSON:
  ```
  {
    role: string,
    skills_required: string[],
    skills_nice: string[],
    experience_years: { min: number, max: number },
    location: string,
    must_haves: string[],
    soft_skills: string[]
  }
  ```

### Stage 2 — Candidate Discovery
- Pool of **200 synthetic candidates** stored in SQLite (`candidates.db`)
- Each candidate: `{id, name, title, skills[], experience_years, location, summary, hidden_interest_profile}`
- **Embeddings pre-computed at startup** on candidate `summary` using Vertex AI `text-embedding-005` (or `gemini-embedding-001`); stored in-memory as a NumPy matrix (200 × dim) — no separate vector DB needed at this scale
- **Query:** embed the parsed JD (concatenated role + skills + summary) → cosine similarity → **top 20** candidates

### Stage 3 — Match Scoring + Explainability
- For each of the top 20: **Gemini 3.1 Pro** call (`thinking_level="MEDIUM"`) with `(JD, candidate_profile)` → returns:
  ```
  {
    match_score: 0-100,
    reasoning: "Matched on Python, Django, 4yr exp. Missing: AWS. Strong fit on backend.",
    matched_skills: string[],
    missing_skills: string[]
  }
  ```
- Run all 20 **in parallel** (`asyncio.gather`)
- Sort by `match_score`, take **top 10** for Stage 4

### Stage 4 — Conversational Outreach (the differentiator)
For top 10, simulate a recruiter↔candidate conversation:

1. **Opening message:** Recruiter agent (Gemini 3 Flash) generates personalized opener using Stage 3 reasoning
2. **Candidate persona:** Gemini 3 Flash call with the candidate's `hidden_interest_profile` (one of: `actively_looking | passive | not_looking`) plus role-specific objections (salary, remote, location, growth)
3. **Conversation:** 3–4 turn back-and-forth (recruiter agent ↔ candidate persona, both Flash)
4. **Interest scoring:** Final **Gemini 3.1 Pro** call scores the transcript:
   ```
   {
     interest_score: 0-100,
     signals: ["asked about salary", "available in 2 weeks", "raised remote concerns"],
     summary: "Candidate is passively open; primary blocker is on-site requirement."
   }
   ```

**All 10 conversations run in parallel** (asyncio.gather). Each is ~4 Gemini calls, so wall-clock ≈ 15s instead of 2+ minutes.

### Stage 5 — Combined Ranking + Output
- `final_score = w_match * match_score + w_interest * interest_score`
- Defaults: `w_match = 0.6`, `w_interest = 0.4`
- **Sliders in UI** let the recruiter retune weights live (re-sorts without re-running pipeline)
- Output: ranked table with both scores + reasoning; click row to expand conversation transcript and the "Explain this conversation" summary

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Next.js Frontend (Vercel)                                   │
│  - JD input (text/URL)                                      │
│  - Ranked results table + sliders                           │
│  - Conversation drawer / explainability panel               │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP (Next.js API routes)
┌─────────────────────▼───────────────────────────────────────┐
│ FastAPI Backend (Render / Cloud Run)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Stage 1      │  │ Stage 2      │  │ Stage 3          │   │
│  │ JD Parser    │─▶│ Discovery    │─▶│ Match Scorer     │   │
│  │ (Firecrawl + │  │ (cosine vs   │  │ (Gemini, parallel│   │
│  │ Gemini)      │  │ embeddings)  │  │  over top 20)    │   │
│  └──────────────┘  └──────────────┘  └────────┬─────────┘   │
│                                               │             │
│  ┌──────────────────────────────┐  ┌──────────▼─────────┐   │
│  │ Stage 5                      │◀─│ Stage 4            │   │
│  │ Combined Ranking             │  │ Simulated Outreach │   │
│  │ (weighted score, no LLM)     │  │ (Gemini, parallel  │   │
│  └──────────────────────────────┘  │  over top 10)      │   │
│                                    └────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Disk cache (JD-hash keyed) — Stages 1, 3, 4          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ Data Layer                                                  │
│  - candidates.db (SQLite, 200 synthetic profiles)           │
│  - embeddings.npy (200 × 768 float32, loaded at startup)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Component Breakdown

| Module | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `jd_ingest.py` | Scrape (if URL) + parse JD to structured JSON | text or URL | `JDStruct` |
| `candidate_pool.py` | Load SQLite + embeddings at startup, expose `top_k(jd_embedding, k)` | JD embedding | top-k candidate rows |
| `match_scorer.py` | For each candidate, call Gemini with (JD, profile) | JDStruct, Candidate[] | `MatchResult[]` |
| `outreach_sim.py` | Run 4-turn recruiter↔candidate conversation, score it | JDStruct, Candidate, MatchResult | `InterestResult` |
| `ranker.py` | Combine match + interest with weights | MatchResult[], InterestResult[], weights | ranked list |
| `cache.py` | Disk cache keyed on `sha256(JD text + stage)` | stage, key, value | cached value or miss |
| `gemini_client.py` | Vertex AI wrapper, retries, structured-output schema enforcement | prompt, schema | parsed JSON |
| `seed/generate_pool.py` | One-shot script: generate 200 candidates with Opus, write to SQLite | — | `candidates.db` |

Each module is a single file with one clear public interface. No module knows about another's internals beyond its return type.

---

## 6. Tech Stack

- **Frontend:** Next.js 14 (App Router) + Tailwind + shadcn/ui — deployed to Vercel
- **Backend:** FastAPI (Python 3.11) — deployed to Render or Cloud Run
- **LLM:** **Gemini 3 Flash** (Stage 1 parsing, Stage 4 conversations + persona) + **Gemini 3.1 Pro** (Stage 3 match scoring + Stage 4 final interest scoring) via **Vertex AI** (`google-genai` SDK, `vertexai=True`, region `us-central1`)
  - Pro uses `thinking_level="MEDIUM"` for match scoring (better reasoning, controlled cost)
  - Flash-Lite (`gemini-3.1-flash-lite`) reserved as cost fallback if quota tightens
- **Embeddings:** Vertex AI `text-embedding-005` (text-embedding-004 retired; gemini-embedding-001 also acceptable)
- **Scraping:** Firecrawl (`/scrape` endpoint, markdown output)
- **Storage:** SQLite (candidates), NumPy `.npy` (embeddings), local filesystem (cache)
- **Synthetic pool generation:** Claude Opus 4.7, one-shot via Anthropic API

---

## 7. Data Flow Example

```
User pastes JD URL
  ↓
Firecrawl → markdown
  ↓
Gemini 3 Flash → JDStruct (role: "Senior Backend Engineer", skills: [Python, Django, AWS]…)
  ↓
embed(JDStruct) → query vector
  ↓
cosine vs candidates.npy → top 20 candidate IDs
  ↓
parallel: Gemini 3.1 Pro × 20 → MatchResult[] with reasoning
  ↓
take top 10 by match_score
  ↓
parallel: 10 conversations × 4 turns × Gemini 3 Flash → InterestResult[] (final score by 3.1 Pro)
  ↓
ranker (0.6 × match + 0.4 × interest) → ranked table
  ↓
return to UI with full transcripts + reasoning
```

---

## 8. Error Handling

- **Firecrawl failure:** fall back to "paste JD text" with explicit error toast
- **Gemini structured-output validation failure:** retry once with stricter schema reminder; if still fails, skip that candidate (don't fail the whole pipeline) and log
- **Empty JD parse result:** show validation error in UI before running pipeline
- **No candidates above similarity threshold (0.3):** show "no strong matches in pool" rather than returning noise
- **Stage 4 partial failure:** if a conversation errors out, that candidate gets `interest_score = null` and is shown in the table with an "interest assessment unavailable" badge — don't drop them

---

## 9. Testing Strategy

Time-boxed for 36-hour build — pragmatic, not exhaustive:

- **Manual end-to-end test** with 3 canned JDs (backend engineer, ML engineer, product designer) before deploy
- **Unit test** the ranker (pure function — easiest to test, easiest to break)
- **Schema validation test** for `JDStruct`, `MatchResult`, `InterestResult` — Pydantic models with one example each
- **Smoke test script** (`scripts/smoke.py`) that runs the full pipeline against one canned JD; runs in CI / pre-deploy
- No frontend tests — manual click-through before deploy

---

## 10. Demo & Submission Plan

- **Sample JDs** (committed to repo): 3 realistic JDs (backend, ML, designer) with expected top-5 results captured for the README
- **Demo video script:**
  1. Paste a JD URL → show Firecrawl + parse (5s)
  2. Watch 20 candidates get matched with reasoning (10s)
  3. Watch 10 simulated conversations stream in (15s)
  4. Show ranked table; expand a conversation transcript (15s)
  5. Move the weight slider live; watch ranking re-sort (10s)
  6. Hit "Explain this conversation" on a passive candidate (15s)
  7. One-line architecture recap + close (10s)
  Total: ~80s of substance, pad with framing → fits 3 min comfortably
- **README:** problem → architecture diagram → how scoring works → quickstart → sample I/O → "swap in real candidate sources" note
- **Deploy:** Vercel (frontend) + Render free tier (backend). Both behind a single demo URL.

---

## 11. Build Schedule (36 Hours)

| Slot | Task | Output |
|---|---|---|
| Day 1 morning (post-Round 3) | Generate 200 synthetic candidates via Opus, build SQLite + embeddings | `candidates.db`, `embeddings.npy` |
| Day 1 afternoon | Stages 1–3 + FastAPI scaffold + Next.js scaffold | Working JD → ranked-by-match results |
| Day 1 evening | Stage 4 (the hard part — prompt engineering for personas + scoring) | Working conversations + interest scores |
| Day 2 morning | Stage 5 + UI polish (sliders, conversation drawer, explain button) + Vercel/Render deploy | Live URL |
| Day 2 afternoon | Architecture diagram + README + demo script | Submission-ready repo |
| Day 2 evening | Record demo, submit | Submitted before 01:00 IST Apr 27 |

**Ironclad rule:** Stages 1–3 must be working and deployed before touching Stage 4. A working JD → matched-with-explainability submission is still valid; Stage 4 is the differentiator but not the foundation.

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Vertex AI quota / region issues mid-build | Pre-test `gemini-3-flash`, `gemini-3-1-pro-preview`, and `text-embedding-005` in `us-central1` before Day 1 afternoon; cost-fallback to `gemini-3-1-flash-lite` wired in `gemini_client.py` |
| Gemini 3.1 Pro still in preview — schema or rate-limit changes mid-build | Pin SDK version, capture model ID + version in env vars (`MODEL_PRO`, `MODEL_FLASH`) so swap is one-line |
| Stage 4 prompt engineering takes longer than evening | Cap at 3 hours; if not converging, ship with simpler 2-turn conversations |
| Render free tier cold-start kills demo | Pre-warm with a cron ping every 10 min during demo window; or deploy backend to Cloud Run |
| Synthetic pool feels "too clean" | Inject deliberate skill gaps, location mismatches, and mixed-quality summaries so match scores have real spread |
| Demo runs slow on first JD | Pre-cache 3 sample JDs so the demo video shows instant results |

---

## 13. Success Criteria

- Recruiter pastes a JD URL, gets a ranked shortlist with match + interest scores within 30 seconds
- Each row has a clickable reasoning + full conversation transcript
- Weight sliders re-sort live without re-running the pipeline
- Deployed at a public URL that survives the demo
- README + architecture diagram + sample I/O committed
- Demo video submitted before 01:00 IST 2026-04-27

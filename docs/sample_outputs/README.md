# Sample inputs and outputs

Concrete example of what the agent produces end-to-end.

## Input

Three sample job descriptions live in [`backend/tests/fixtures/sample_jds.json`](../../backend/tests/fixtures/sample_jds.json). The one used for the captured response below:

> Senior Backend Engineer at a fintech startup. 5+ years of Python, deep Django experience, comfortable with PostgreSQL and Redis. AWS or GCP required. Bonus: event-driven architectures, Kafka. Bengaluru hybrid (3 days in office).

## Output

[`backend_engineer_response.json`](backend_engineer_response.json) — the actual `/scout` response from the deployed Cloud Run backend. Contains:

- **`jd`** — the parsed JD struct (role, required/nice skills, experience range, location, must-haves)
- **`ranked`** — 20 candidates sorted by `final_score`, each with `match_score`, `interest_score`, `final_score`, and human-readable reasoning
- **`match_details`** — per-candidate scoring with matched and missing skills
- **`interest_details`** — per-candidate interest score, signal quotes from the conversation, and 1-sentence summary
- **`conversations`** — full 4-turn recruiter↔candidate transcripts for the top 10 candidates
- **`weights`** — the score weighting used (default 0.6 match, 0.4 interest)

## Top result from the captured run

| Field | Value |
|---|---|
| Candidate | Aarav Sharma — Senior Backend Engineer |
| Match score | 93 |
| Interest score | 68 |
| Final score | 83.0 |
| Reasoning excerpt | Cited Python + Django + PostgreSQL + Redis match; flagged skill gaps and assessed Bengaluru fit |
| Conversation length | 4 turns (recruiter opener → candidate reply → recruiter follow-up → candidate close) |

## Reproducing this output

```bash
curl -X POST https://scout-backend-agah7k3aja-uc.a.run.app/scout \
  -H "content-type: application/json" \
  -d @- <<'EOF'
{
  "jd_text": "Senior Backend Engineer at a fintech startup. 5+ years of Python, deep Django experience, comfortable with PostgreSQL and Redis. AWS or GCP required. Bonus: event-driven architectures, Kafka. Bengaluru hybrid (3 days in office).",
  "weights": {"match": 0.6, "interest": 0.4}
}
EOF
```

Cached responses return in ~1s. Fresh JDs go through the full pipeline (~30-90s on warm backend; longer on cold start).

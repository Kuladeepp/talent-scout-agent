"""End-to-end smoke test against running server.

Usage:
    uvicorn app.main:app --port 8000 &
    python scripts/smoke.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "sample_jds.json"


def main() -> int:
    samples = json.loads(FIXTURES.read_text(encoding="utf-8"))
    base = "http://localhost:8000"
    with httpx.Client(timeout=300) as http:
        h = http.get(f"{base}/healthz").json()
        print("healthz:", h)
        for s in samples:
            print(f"\n== {s['name']} ==")
            r = http.post(f"{base}/scout", json={"jd_text": s["text"]})
            r.raise_for_status()
            data = r.json()
            print(f"role parsed: {data['jd']['role']}")
            print(f"ranked count: {len(data['ranked'])}")
            for row in data["ranked"][:3]:
                print(
                    f"  {row['candidate_id']} {row['name']:<25} "
                    f"match={row['match_score']:>3} interest={row['interest_score']} -- {row['match_reasoning'][:60]}"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Embed every candidate's summary into a NumPy matrix saved to data/embeddings.npy.

Usage:
    cd backend && python -m seed.embed_pool

Reads:  data/candidates.db
Writes: data/embeddings.npy        (float32, shape [N, dim])
        data/embedding_ids.json    (list[str] aligned with rows)
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

from app.gemini_client import embed_batch

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "candidates.db"
EMB_PATH = DATA_DIR / "embeddings.npy"
IDS_PATH = DATA_DIR / "embedding_ids.json"

BATCH = 16


def candidate_text(row: tuple) -> str:
    """Concatenate fields used for retrieval: title + skills + summary."""
    cid, name, title, skills_json, exp, loc, summary, _ = row
    skills = ", ".join(json.loads(skills_json))
    return f"Title: {title}. Skills: {skills}. Experience: {exp} years. Location: {loc}. Summary: {summary}"


async def main() -> int:
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found. Run seed.generate_pool first.", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, name, title, skills_json, experience_years, location, summary, hidden_interest_profile FROM candidates ORDER BY id"
    ).fetchall()
    conn.close()

    ids = [r[0] for r in rows]
    texts = [candidate_text(r) for r in rows]

    vectors: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        print(f"Embedding {i + len(chunk)}/{len(texts)}...")
        vectors.extend(await embed_batch(chunk))

    arr = np.array(vectors, dtype=np.float32)
    # L2-normalize so cosine similarity == dot product
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    arr = arr / np.clip(norms, 1e-9, None)

    np.save(EMB_PATH, arr)
    IDS_PATH.write_text(json.dumps(ids), encoding="utf-8")
    print(f"Wrote {EMB_PATH} (shape {arr.shape}) and {IDS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

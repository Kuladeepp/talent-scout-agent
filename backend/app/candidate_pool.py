"""Loads candidates + embeddings at startup, provides top-k retrieval."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np

from app.models import Candidate

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class CandidatePool:
    def __init__(self) -> None:
        self.candidates: dict[str, Candidate] = {}
        self.ids: list[str] = []
        self.embeddings: np.ndarray | None = None  # shape (N, dim), L2-normalized

    def load(self) -> None:
        db_path = DATA_DIR / "candidates.db"
        emb_path = DATA_DIR / "embeddings.npy"
        ids_path = DATA_DIR / "embedding_ids.json"

        if not db_path.exists():
            raise FileNotFoundError(f"{db_path} missing — run seed.generate_pool first")
        if not emb_path.exists():
            raise FileNotFoundError(f"{emb_path} missing — run seed.embed_pool first")

        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT id, name, title, skills_json, experience_years, location, summary, hidden_interest_profile FROM candidates"
        ).fetchall()
        conn.close()

        for r in rows:
            c = Candidate(
                id=r[0], name=r[1], title=r[2],
                skills=json.loads(r[3]),
                experience_years=r[4], location=r[5],
                summary=r[6], hidden_interest_profile=r[7],
            )
            self.candidates[c.id] = c

        self.ids = json.loads(ids_path.read_text(encoding="utf-8"))
        self.embeddings = np.load(emb_path)
        if self.embeddings.shape[0] != len(self.ids):
            raise RuntimeError("embedding rows != id list length")

    def top_k(self, query_embedding: list[float], k: int, floor: float = 0.0) -> list[tuple[str, float]]:
        if self.embeddings is None:
            raise RuntimeError("CandidatePool not loaded")
        q = np.array(query_embedding, dtype=np.float32)
        q = q / max(float(np.linalg.norm(q)), 1e-9)
        scores = self.embeddings @ q  # cosine since both sides are L2-normalized
        order = np.argsort(-scores)
        out: list[tuple[str, float]] = []
        for idx in order[: k * 2]:
            s = float(scores[idx])
            if s < floor:
                break
            out.append((self.ids[idx], s))
            if len(out) == k:
                break
        return out

    def get(self, candidate_id: str) -> Candidate:
        return self.candidates[candidate_id]


pool = CandidatePool()

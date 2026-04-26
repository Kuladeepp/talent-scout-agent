"""Trivial JSON disk cache keyed by sha256(input + stage)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.config import settings

CACHE_DIR: Path = settings.cache_path


class _DiskCache:
    @staticmethod
    def key(payload: str, stage: str) -> str:
        h = hashlib.sha256(f"{stage}::{payload}".encode("utf-8")).hexdigest()
        return f"{stage}_{h[:16]}"

    @staticmethod
    def _path(key: str) -> Path:
        return CACHE_DIR / f"{key}.json"

    def get(self, key: str) -> Any | None:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def put(self, key: str, value: Any) -> None:
        self._path(key).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


disk_cache = _DiskCache()

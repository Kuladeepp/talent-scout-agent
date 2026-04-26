import json
from pathlib import Path

from app.cache import disk_cache


def test_cache_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr("app.cache.CACHE_DIR", tmp_path)
    key = disk_cache.key("hello", "stage1")
    assert disk_cache.get(key) is None
    disk_cache.put(key, {"a": 1})
    assert disk_cache.get(key) == {"a": 1}


def test_cache_key_stable():
    k1 = disk_cache.key("same input", "stage1")
    k2 = disk_cache.key("same input", "stage1")
    assert k1 == k2
    k3 = disk_cache.key("same input", "stage2")
    assert k1 != k3

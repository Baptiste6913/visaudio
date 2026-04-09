"""SHA-256 disk cache for Mesa simulation run results.

Cache key = sha256(scenario_id + sorted_json(params)).
Storage: one JSON file per key in the cache directory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path("data/processed/mesa_runs")


def cache_key(scenario_id: str, params: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hex key for a scenario + params."""
    payload = scenario_id + json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_path(key: str, cache_dir: Path) -> Path:
    return cache_dir / f"{key}.json"


def read_cache(key: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> dict | None:
    """Read a cached result by key. Returns None on miss."""
    path = _cache_path(key, cache_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_cache(key: str, data: dict, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    """Write a result dict to cache. Returns the file path."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key, cache_dir)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return path

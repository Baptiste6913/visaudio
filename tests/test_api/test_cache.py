"""Tests for Mesa run disk cache — P4 Task 2."""
from __future__ import annotations

import pytest

from src.api.cache import cache_key, read_cache, write_cache


def test_cache_key_deterministic():
    k1 = cache_key("SC-BASE", {})
    k2 = cache_key("SC-BASE", {})
    assert k1 == k2
    assert len(k1) == 64  # SHA-256 hex


def test_cache_key_differs_by_scenario():
    k1 = cache_key("SC-BASE", {})
    k2 = cache_key("SC-L2a", {})
    assert k1 != k2


def test_cache_key_differs_by_params():
    k1 = cache_key("SC-L2a", {"effort": 1.3})
    k2 = cache_key("SC-L2a", {"effort": 1.5})
    assert k1 != k2


def test_write_then_read(tmp_path):
    data = {"scenario_id": "SC-BASE", "ca_mean": [100.0, 200.0]}
    key = cache_key("SC-BASE", {})
    write_cache(key, data, cache_dir=tmp_path)
    result = read_cache(key, cache_dir=tmp_path)
    assert result is not None
    assert result["ca_mean"] == [100.0, 200.0]


def test_read_cache_miss(tmp_path):
    result = read_cache("nonexistent_hash", cache_dir=tmp_path)
    assert result is None

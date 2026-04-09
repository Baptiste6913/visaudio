"""Tests for archetype loader — P3 Task 1."""
from __future__ import annotations

import pytest

from src.simulation.archetypes import (
    ArchetypeParams,
    load_archetypes_from_payload,
)


def test_load_returns_dict_of_archetype_params(archetypes_payload):
    params = load_archetypes_from_payload(archetypes_payload)
    assert isinstance(params, dict)
    assert len(params) == archetypes_payload["n_archetypes"]
    for k, v in params.items():
        assert isinstance(k, int)
        assert isinstance(v, ArchetypeParams)


def test_gamme_distribution_sums_to_one(archetypes_payload):
    params = load_archetypes_from_payload(archetypes_payload)
    for ap in params.values():
        total = sum(ap.gamme_distribution.values())
        assert total == pytest.approx(1.0, abs=0.01)


def test_purchase_interval_positive(archetypes_payload):
    params = load_archetypes_from_payload(archetypes_payload)
    for ap in params.values():
        assert ap.purchase_interval_months > 0


def test_switch_prob_in_zero_one(archetypes_payload):
    params = load_archetypes_from_payload(archetypes_payload)
    for ap in params.values():
        assert 0.0 <= ap.switch_prob <= 1.0


def test_high_premium_archetype_has_higher_premium_prob(archetypes_payload):
    """Archetype 0 (part_premium_plus=0.65) should have more PREMIUM than archetype 2 (0.05)."""
    params = load_archetypes_from_payload(archetypes_payload)
    assert params[0].gamme_distribution["PREMIUM"] > params[2].gamme_distribution["PREMIUM"]


def test_mean_ticket_matches_centroid(archetypes_payload):
    params = load_archetypes_from_payload(archetypes_payload)
    assert params[0].mean_ticket == pytest.approx(225.0)
    assert params[1].mean_ticket == pytest.approx(160.0)

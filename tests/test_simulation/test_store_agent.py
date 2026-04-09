"""Tests for StoreAgent — P3 Task 3."""
from __future__ import annotations

import mesa
import pytest

from src.simulation.agents.store import StoreAgent


def test_store_agent_has_required_attributes():
    model = mesa.Model(rng=42)
    store = StoreAgent(model, store_name="Avranches")
    assert store.store_name == "Avranches"
    assert isinstance(store.effort_commercial_level, dict)
    assert isinstance(store.price_multipliers, dict)
    assert isinstance(store.active_campaigns, list)


def test_default_effort_is_neutral():
    model = mesa.Model(rng=42)
    store = StoreAgent(model, store_name="Rampan")
    assert store.get_effort(archetype_id=0) == 1.0
    assert store.get_effort(archetype_id=99) == 1.0


def test_price_multiplier_default_is_neutral():
    model = mesa.Model(rng=42)
    store = StoreAgent(model, store_name="Yquelon")
    assert store.get_price_multiplier("PREMIUM") == 1.0


def test_custom_effort_and_price():
    model = mesa.Model(rng=42)
    store = StoreAgent(
        model,
        store_name="Avranches",
        effort_commercial_level={0: 1.3},
        price_multipliers={"PREMIUM": 0.9},
    )
    assert store.get_effort(0) == 1.3
    assert store.get_effort(1) == 1.0
    assert store.get_price_multiplier("PREMIUM") == 0.9
    assert store.get_price_multiplier("ESSENTIEL") == 1.0

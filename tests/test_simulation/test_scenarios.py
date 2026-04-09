"""Tests for scenario definitions -- P3 Task 6."""
from __future__ import annotations

import pytest

from src.simulation.scenarios import SCENARIOS, get_scenario, ScenarioDef


def test_six_scenarios_defined():
    assert len(SCENARIOS) == 6


def test_base_has_no_overrides():
    base = get_scenario("SC-BASE")
    assert base.store_overrides == {}


def test_l2a_has_effort_boost():
    hero = get_scenario("SC-L2a")
    assert hero.store_overrides is not None
    has_boost = False
    for store_kw in hero.store_overrides.values():
        for v in store_kw.get("effort_commercial_level", {}).values():
            if v > 1.0:
                has_boost = True
    assert has_boost


def test_get_scenario_unknown_raises():
    with pytest.raises(KeyError):
        get_scenario("SC-UNKNOWN")


def test_scenario_def_has_required_fields():
    for sc in SCENARIOS.values():
        assert isinstance(sc, ScenarioDef)
        assert sc.scenario_id
        assert sc.name
        assert sc.description


def test_all_stores_have_overrides_in_l2a():
    hero = get_scenario("SC-L2a")
    expected_stores = {"Avranches", "Carentan-les-Marais", "Cherbourg-en-Cotentin",
                       "Coutances", "Rampan", "Yquelon"}
    assert set(hero.store_overrides.keys()) == expected_stores

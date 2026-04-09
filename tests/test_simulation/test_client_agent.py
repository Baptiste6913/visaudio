"""Tests for ClientAgent — P3 Task 4."""
from __future__ import annotations

import mesa
import pytest

from src.simulation.agents.client import ClientAgent
from src.simulation.agents.store import StoreAgent
from src.simulation.archetypes import ArchetypeParams


@pytest.fixture
def simple_archetype():
    return ArchetypeParams(
        archetype_id=0,
        label="test",
        n_clients=100,
        purchase_interval_months=12.0,
        hazard_base=0.083,
        gamme_distribution={
            "ESSENTIEL": 0.6, "CONFORT": 0.3,
            "PREMIUM": 0.08, "PRESTIGE": 0.02,
        },
        switch_prob=0.05,
        mean_ticket=200.0,
    )


def _make_model_with_store(store_name="Avranches", **store_kw):
    """Helper: create a Model with one store and the attributes ClientAgent expects."""
    model = mesa.Model(rng=42)
    model.current_step = 0
    model.seasonality = {m: 1.0 for m in range(1, 13)}
    model.sales_log = []
    store = StoreAgent(model, store_name=store_name, **store_kw)
    model.stores = {store_name: store}
    return model


def test_client_agent_creation(simple_archetype):
    model = _make_model_with_store()
    client = ClientAgent(
        model,
        archetype=simple_archetype,
        home_store_name="Avranches",
        conventionnement="LIBRE",
        age=55,
        last_purchase_step=-12,
    )
    assert client.archetype.archetype_id == 0
    assert client.home_store_name == "Avranches"
    assert client.age == 55


def test_client_does_not_buy_before_interval(simple_archetype):
    model = _make_model_with_store()
    model.current_step = 1
    client = ClientAgent(
        model, archetype=simple_archetype,
        home_store_name="Avranches", conventionnement="LIBRE",
        age=55, last_purchase_step=0,
    )
    client.step()
    assert len(model.sales_log) == 0


def test_client_buys_deterministically_with_high_hazard():
    always_buy = ArchetypeParams(
        archetype_id=0, label="always", n_clients=1,
        purchase_interval_months=1.0, hazard_base=1.0,
        gamme_distribution={"ESSENTIEL": 1.0, "CONFORT": 0.0, "PREMIUM": 0.0, "PRESTIGE": 0.0},
        switch_prob=0.0, mean_ticket=100.0,
    )
    model = _make_model_with_store()
    model.current_step = 2
    client = ClientAgent(
        model, archetype=always_buy,
        home_store_name="Avranches", conventionnement="LIBRE",
        age=50, last_purchase_step=0,
    )
    client.step()
    assert len(model.sales_log) == 1
    sale = model.sales_log[0]
    assert sale["store"] == "Avranches"
    assert sale["gamme"] == "ESSENTIEL"
    assert sale["ticket"] > 0


def test_effort_boost_shifts_gamme_distribution():
    """With effort=1.3 on archetype 0, PREMIUM prob should increase."""
    arch = ArchetypeParams(
        archetype_id=0, label="test", n_clients=1,
        purchase_interval_months=1.0, hazard_base=1.0,
        gamme_distribution={"ESSENTIEL": 0.5, "CONFORT": 0.3, "PREMIUM": 0.15, "PRESTIGE": 0.05},
        switch_prob=0.0, mean_ticket=200.0,
    )
    model = _make_model_with_store(effort_commercial_level={0: 1.3})
    model.current_step = 2
    client = ClientAgent(
        model, archetype=arch,
        home_store_name="Avranches", conventionnement="LIBRE",
        age=50, last_purchase_step=0,
    )
    probs = client._compute_gamme_probs(model.stores["Avranches"])
    # PREMIUM should be higher than base 0.15
    assert probs["PREMIUM"] > 0.15

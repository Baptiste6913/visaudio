"""Tests for src.simulation.model — VisaudioModel orchestration."""
from __future__ import annotations

import pytest

from src.simulation.model import VisaudioModel


def test_model_creation(archetypes_payload, mini_sales):
    model = VisaudioModel(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        n_steps=12,
        seed=42,
    )
    assert model.current_step == 0
    assert len(model.stores) > 0


def test_model_step_advances(archetypes_payload, mini_sales):
    model = VisaudioModel(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        n_steps=12,
        seed=42,
    )
    model.step()
    assert model.current_step == 1


def test_model_runs_full_horizon(archetypes_payload, mini_sales):
    model = VisaudioModel(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        n_steps=6,
        seed=42,
    )
    for _ in range(6):
        model.step()
    assert model.current_step == 6
    assert isinstance(model.sales_log, list)


def test_model_is_reproducible(archetypes_payload, mini_sales):
    def run():
        m = VisaudioModel(
            sales_df=mini_sales,
            archetypes_payload=archetypes_payload,
            n_steps=12,
            seed=42,
        )
        for _ in range(12):
            m.step()
        return m.sales_log
    log1 = run()
    log2 = run()
    assert len(log1) == len(log2)
    for s1, s2 in zip(log1, log2):
        assert s1 == s2


# -- Word-of-mouth integration tests --


def test_model_wom_enabled_builds_contacts(archetypes_payload, mini_sales):
    model = VisaudioModel(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        n_steps=6,
        seed=42,
        enable_word_of_mouth=True,
    )
    from src.simulation.agents.client import ClientAgent
    clients = list(model.agents_by_type[ClientAgent])
    # At least some clients should have contacts
    has_contacts = any(len(c.contacts) > 0 for c in clients)
    assert has_contacts
    # Contacts should be capped at 5
    for c in clients:
        assert len(c.contacts) <= 5


def test_model_wom_disabled_no_contacts(archetypes_payload, mini_sales):
    model = VisaudioModel(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        n_steps=6,
        seed=42,
        enable_word_of_mouth=False,
    )
    from src.simulation.agents.client import ClientAgent
    clients = list(model.agents_by_type[ClientAgent])
    for c in clients:
        assert len(c.contacts) == 0


def test_model_wom_default_is_true(archetypes_payload, mini_sales):
    model = VisaudioModel(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        n_steps=6,
        seed=42,
    )
    assert model.enable_word_of_mouth is True

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

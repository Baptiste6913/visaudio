"""Tests for the batch runner — P3 Task 7."""
from __future__ import annotations

import pytest

from src.simulation.runner import run_scenario, RunResult


def test_run_returns_run_result(archetypes_payload, mini_sales):
    result = run_scenario(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        scenario_id="SC-BASE",
        n_steps=6,
        n_replications=3,
        seed=42,
    )
    assert isinstance(result, RunResult)
    assert result.scenario_id == "SC-BASE"
    assert result.n_replications == 3
    assert len(result.ca_mean) == 6
    assert len(result.ca_lower) == 6
    assert len(result.ca_upper) == 6


def test_ci_bounds_sensible(archetypes_payload, mini_sales):
    result = run_scenario(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        scenario_id="SC-BASE",
        n_steps=6,
        n_replications=5,
        seed=42,
    )
    for i in range(6):
        assert result.ca_lower[i] <= result.ca_mean[i] <= result.ca_upper[i]


def test_reproducible(archetypes_payload, mini_sales):
    r1 = run_scenario(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        scenario_id="SC-BASE",
        n_steps=6,
        n_replications=3,
        seed=42,
    )
    r2 = run_scenario(
        sales_df=mini_sales,
        archetypes_payload=archetypes_payload,
        scenario_id="SC-BASE",
        n_steps=6,
        n_replications=3,
        seed=42,
    )
    assert r1.ca_mean == r2.ca_mean

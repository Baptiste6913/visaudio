"""Tests for API pydantic schemas — P4 Task 1."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    SimulateRequest,
    SimulateResponse,
    Trajectory,
    ScenarioInfo,
)


def test_simulate_request_default_params():
    req = SimulateRequest(scenario_id="SC-BASE")
    assert req.scenario_id == "SC-BASE"
    assert req.params == {}
    assert req.n_steps == 36
    assert req.n_replications == 20


def test_simulate_request_custom_params():
    req = SimulateRequest(
        scenario_id="SC-L2a",
        params={"effort": 1.3},
        n_steps=12,
        n_replications=5,
    )
    assert req.n_steps == 12


def test_simulate_request_rejects_unknown_scenario():
    with pytest.raises(ValidationError):
        SimulateRequest(scenario_id="SC-NOPE")


def test_trajectory_validation():
    t = Trajectory(
        months=[1, 2, 3], ca_mean=[100.0, 110.0, 120.0],
        ca_lower=[90.0, 100.0, 110.0], ca_upper=[110.0, 120.0, 130.0],
    )
    assert len(t.months) == 3


def test_simulate_response_construction():
    traj = Trajectory(months=[1], ca_mean=[100.0], ca_lower=[90.0], ca_upper=[110.0])
    resp = SimulateResponse(
        scenario_id="SC-BASE", params={},
        baseline=traj, intervention=traj,
        delta_ca_cumul_36m=0.0, delta_ca_ci_low=0.0, delta_ca_ci_high=0.0,
        n_replications=20, from_cache=True,
    )
    assert resp.from_cache is True


def test_scenario_info_construction():
    info = ScenarioInfo(
        scenario_id="SC-BASE", name="Baseline", levier="—",
        description="No intervention",
    )
    assert info.scenario_id == "SC-BASE"

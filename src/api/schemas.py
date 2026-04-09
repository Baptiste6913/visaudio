"""Pydantic models for FastAPI request/response — spec §9.3."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

VALID_SCENARIOS = Literal[
    "SC-BASE", "SC-L2a", "SC-L2b", "SC-L1a", "SC-L4a", "SC-L5a"
]


class SimulateRequest(BaseModel):
    """POST /simulate request body."""

    scenario_id: VALID_SCENARIOS
    params: dict[str, Any] = {}
    n_steps: int = 36
    n_replications: int = 20


class Trajectory(BaseModel):
    """Time-series trajectory with confidence interval."""

    months: list[int]
    ca_mean: list[float]
    ca_lower: list[float]
    ca_upper: list[float]


class SimulateResponse(BaseModel):
    """POST /simulate response body."""

    scenario_id: str
    params: dict[str, Any]
    baseline: Trajectory
    intervention: Trajectory
    delta_ca_cumul_36m: float
    delta_ca_ci_low: float
    delta_ca_ci_high: float
    n_replications: int
    from_cache: bool


class ScenarioInfo(BaseModel):
    """GET /scenarios list item."""

    scenario_id: str
    name: str
    levier: str
    description: str

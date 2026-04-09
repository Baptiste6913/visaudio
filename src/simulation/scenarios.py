"""Scenario definitions for P3 Mesa simulation.

Each scenario is a frozen dataclass ``ScenarioDef`` describing the levers
applied to the 6 Normandy stores.  The registry ``SCENARIOS`` maps
*scenario_id* -> ``ScenarioDef`` and ``get_scenario()`` provides safe lookup.

Reference: architecture-spec.md S8.6
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---- constants ---------------------------------------------------------------

STORE_NAMES: list[str] = [
    "Avranches",
    "Carentan-les-Marais",
    "Cherbourg-en-Cotentin",
    "Coutances",
    "Rampan",
    "Yquelon",
]

# ---- dataclass ---------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioDef:
    """Immutable definition of a simulation scenario."""

    scenario_id: str
    name: str
    levier: str
    description: str
    store_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    n_replications: int = 20


# ---- helpers -----------------------------------------------------------------


def _all_stores_override(**kwargs: Any) -> dict[str, dict[str, Any]]:
    """Return the same override dict for every store."""
    return {store: dict(kwargs) for store in STORE_NAMES}


# ---- scenario registry ------------------------------------------------------

SCENARIOS: dict[str, ScenarioDef] = {}


def _register(sc: ScenarioDef) -> None:
    SCENARIOS[sc.scenario_id] = sc


_register(ScenarioDef(
    scenario_id="SC-BASE",
    name="Baseline calibre",
    levier="",
    description="No intervention",
))

_register(ScenarioDef(
    scenario_id="SC-L2a",
    name="Effort commercial cible (HERO)",
    levier="L2",
    description="+30% effort on archetype 0 across all 6 stores",
    store_overrides=_all_stores_override(
        effort_commercial_level={0: 1.3},
    ),
))

_register(ScenarioDef(
    scenario_id="SC-L2b",
    name="Best-in-class effort",
    levier="L2",
    description="Max effort all archetypes",
    store_overrides=_all_stores_override(
        effort_commercial_level={i: 1.5 for i in range(10)},
    ),
))

_register(ScenarioDef(
    scenario_id="SC-L1a",
    name="Baisse PREMIUM -10%",
    levier="L1",
    description="Price reduction on PREMIUM",
    store_overrides=_all_stores_override(
        price_multipliers={"PREMIUM": 0.9},
    ),
))

_register(ScenarioDef(
    scenario_id="SC-L4a",
    name="Campagne dormants",
    levier="L4",
    description="Reactivation campaign",
    store_overrides=_all_stores_override(
        active_campaigns=[{
            "target_archetype": "dormants",
            "reactivation_boost": 0.3,
            "window_months": 6,
        }],
    ),
))

_register(ScenarioDef(
    scenario_id="SC-L5a",
    name="Santeclair -10% remboursement",
    levier="L5",
    description="Defensive scenario",
    store_overrides=_all_stores_override(
        price_multipliers={
            "ESSENTIEL": 1.05,
            "CONFORT": 1.05,
            "PREMIUM": 1.08,
            "PRESTIGE": 1.08,
        },
    ),
))


# ---- public API --------------------------------------------------------------


def get_scenario(scenario_id: str) -> ScenarioDef:
    """Return a scenario by id; raises ``KeyError`` if not found."""
    try:
        return SCENARIOS[scenario_id]
    except KeyError:
        raise KeyError(
            f"Unknown scenario '{scenario_id}'. "
            f"Available: {sorted(SCENARIOS)}"
        ) from None

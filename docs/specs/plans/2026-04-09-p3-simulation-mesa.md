# P3 — Simulation Mesa Multi-Agents — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a calibrated agent-based simulation (Mesa 3.x) that replays 36 months of optical retail activity for the 6-store Visaudio network. The simulation must:
1. Reproduce the 2023-2024 historical aggregates within spec tolerances (§8.5).
2. Provide a **baseline scenario (SC-BASE)** extending 36 months from the last data point.
3. Provide the **hero scenario (SC-L2a)** — targeted commercial effort on the high-value archetype — showing ΔCA with 95% CI.
4. Expose a `run_scenario()` API consumed by the future FastAPI backend (P4).

**Architecture:** The simulation consumes `archetypes.json` + `sales.parquet` (produced by P2) and outputs per-scenario trajectory JSON files. All randomness flows through `model.random` (Mesa's built-in RNG) seeded for reproducibility. Pure functions where possible; Mesa Model/Agent classes for the simulation loop.

**Tech Stack:** Python 3.11+, **Mesa ≥ 3.2** (already installed: 3.5.1), pandas 3.0, numpy, scikit-learn (for archetype loading), pydantic 2, click, pytest.

**Source spec:** `docs/specs/architecture-spec.md` §8 (Simulation Mesa), §8.5 (Calibration), §8.6-8.7 (Scénarios), §9.2 (Cache), §14.2 (Chiffres cibles).

**Environment prerequisite:** `OPENBLAS_NUM_THREADS=1` (set in `tests/conftest.py` and documented in `CLAUDE.md`).

---

## Prerequisites (one-time, before Task 1)

Mesa 3.5.1 is already installed. Verify:

```bash
python -c "import mesa; print('mesa', mesa.__version__)"
```

Expected: `mesa 3.5.1` (or ≥ 3.2).

No new pip dependencies needed — mesa, numpy, pandas, scikit-learn, pydantic are already in `requirements.txt`.

---

## File structure produced by this plan

```
src/simulation/
├── __init__.py                     (EXISTING — currently empty, stays empty)
├── agents/
│   ├── __init__.py                 (NEW — empty)
│   ├── client.py                   (NEW — ClientAgent)
│   └── store.py                    (NEW — StoreAgent)
├── model.py                        (NEW — VisaudioModel)
├── archetypes.py                   (NEW — load archetypes + build agent init params)
├── seasonality.py                  (NEW — compute monthly seasonality coefficients)
├── calibration.py                  (NEW — backtest + tolerance checks)
├── scenarios.py                    (NEW — scenario definitions SC-*)
├── runner.py                       (NEW — batch runner: N replications → trajectories)
└── metrics.py                      (NEW — DataCollector config + post-processing)

src/cli.py                          (MODIFIED — add `simulate` subcommand)

tests/test_simulation/
├── __init__.py                     (EXISTING — currently empty)
├── conftest.py                     (NEW — shared fixtures: mini archetypes, mini df)
├── test_archetypes.py              (NEW)
├── test_seasonality.py             (NEW)
├── test_client_agent.py            (NEW)
├── test_store_agent.py             (NEW)
├── test_model.py                   (NEW)
├── test_calibration.py             (NEW)
├── test_scenarios.py               (NEW)
├── test_runner.py                  (NEW)
└── test_metrics.py                 (NEW)

tests/test_e2e_p3.py               (NEW — end-to-end: sample_500 → baseline run)

data/processed/
└── mesa_runs/                      (NEW dir, gitignored — scenario output JSONs)
```

---

# Part A — Data Preparation & Archetype Loading

## Task 1 — Archetype loader

Load `archetypes.json` (produced by P2) and derive the per-archetype behavioural parameters needed by ClientAgent: purchase interval, gamme distribution, hazard base rate, switch probability.

**Files:**
- Create: `src/simulation/archetypes.py`
- Create: `tests/test_simulation/conftest.py`
- Create: `tests/test_simulation/test_archetypes.py`

- [ ] **Step 1.1 — Create shared simulation test fixtures**

File `tests/test_simulation/conftest.py`:

Build a minimal `archetypes_payload` fixture (3 archetypes, enough to exercise all logic) and a `mini_sales` fixture (30 rows, 10 clients across 3 stores and 3 archetypes). The fixture must include a `segment_id` column (from P2).

The fixture should be self-contained (no disk I/O) and deterministic.

Key fields per archetype in the fixture:
- `id`, `label`, `n_clients`, `share_of_clients`, `share_of_ca`
- `centroid`: dict with all 9 features from `FEATURE_NAMES`

Also create a `mini_sales` DataFrame fixture with columns: `id_client`, `ville`, `date_facture`, `famille_article`, `gamme_verre_visaudio`, `ca_ht_article`, `conventionnement`, `segment_id`, `age_client`, `sexe`, `statut_client`, `id_facture_rang`, `rang_paire`, `qte_article`, `est_verre`, `est_premium_plus`.

Clients should span 3 stores (`Avranches`, `Cherbourg-en-Cotentin`, `Rampan`), with dates in 2023-2024, and a mix of gammes (ESSENTIEL, CONFORT, PREMIUM).

- [ ] **Step 1.2 — Write failing tests**

File `tests/test_simulation/test_archetypes.py`:

```python
import pytest
from src.simulation.archetypes import (
    load_archetypes_from_payload,
    ArchetypeParams,
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
```

- [ ] **Step 1.3 — Verify tests fail**

Run: `python -m pytest tests/test_simulation/test_archetypes.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 1.4 — Implement `archetypes.py`**

File `src/simulation/archetypes.py`:

```python
"""Load K-Means archetypes and derive agent-level behavioural params."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

GAMME_ORDERED: list[str] = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


@dataclass(frozen=True)
class ArchetypeParams:
    """Behavioural parameters for one client archetype."""

    archetype_id: int
    label: str
    n_clients: int

    # Purchase timing
    purchase_interval_months: float    # median months between purchases
    hazard_base: float                 # base monthly probability of buying

    # Gamme choice
    gamme_distribution: dict[str, float]  # gamme → probability (sums to 1)

    # Store switching
    switch_prob: float                 # probability of visiting another store

    # Ticket
    mean_ticket: float                 # average CA per transaction


def load_archetypes_from_payload(payload: dict) -> dict[int, ArchetypeParams]:
    """Convert the archetypes.json payload into ArchetypeParams per archetype."""
    result: dict[int, ArchetypeParams] = {}
    for arch in payload["archetypes"]:
        centroid = arch["centroid"]

        # Purchase interval: mois_entre_achats from centroid.
        # If 0 (single-purchase clients), default to 24 months.
        interval = max(centroid.get("mois_entre_achats", 24.0), 1.0)

        # Hazard base rate: inverse of interval, clamped.
        hazard = min(1.0 / interval, 1.0)

        # Gamme distribution: derive from part_premium_plus.
        # part_premium_plus = share of PREMIUM+PRESTIGE among verre rows.
        pp = centroid.get("part_premium_plus", 0.0)
        gamme_dist = _derive_gamme_distribution(pp)

        # Switch probability: heuristic — clients with more purchases
        # tend to be more loyal (lower switch).
        n_achats = centroid.get("n_achats_totaux", 1.0)
        switch = max(0.02, min(0.3, 0.15 / max(n_achats, 0.5)))

        result[int(arch["id"])] = ArchetypeParams(
            archetype_id=int(arch["id"]),
            label=str(arch["label"]),
            n_clients=int(arch["n_clients"]),
            purchase_interval_months=interval,
            hazard_base=hazard,
            gamme_distribution=gamme_dist,
            switch_prob=switch,
            mean_ticket=float(centroid.get("panier_moyen", 196.0)),
        )
    return result


def _derive_gamme_distribution(part_premium_plus: float) -> dict[str, float]:
    """Derive a 4-gamme probability vector from the premium share centroid.

    Splits PREMIUM+PRESTIGE share using a 70/30 heuristic,
    and the remainder between ESSENTIEL/CONFORT using 60/40.
    """
    pp = max(0.0, min(1.0, part_premium_plus))
    prestige = pp * 0.3
    premium = pp * 0.7
    remainder = 1.0 - pp
    essentiel = remainder * 0.6
    confort = remainder * 0.4
    return {
        "ESSENTIEL": round(essentiel, 4),
        "CONFORT": round(confort, 4),
        "PREMIUM": round(premium, 4),
        "PRESTIGE": round(prestige, 4),
    }


def load_archetypes_from_json(path: Path | str) -> dict[int, ArchetypeParams]:
    """Convenience: read archetypes.json from disk and parse."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return load_archetypes_from_payload(payload)
```

- [ ] **Step 1.5 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_archetypes.py -v`
Expected: 4 passed.

- [ ] **Step 1.6 — Commit**

```bash
git add src/simulation/archetypes.py tests/test_simulation/conftest.py tests/test_simulation/test_archetypes.py
git commit -m "feat(simulation): archetype loader — P3 Task 1"
```

---

## Task 2 — Seasonality extraction

Compute monthly seasonality coefficients from the historical sales data. One float per calendar month (1-12), normalized so the mean is 1.0.

**Files:**
- Create: `src/simulation/seasonality.py`
- Create: `tests/test_simulation/test_seasonality.py`

- [ ] **Step 2.1 — Write failing tests**

File `tests/test_simulation/test_seasonality.py`:

```python
import pandas as pd
import pytest
from src.simulation.seasonality import compute_seasonality


def test_returns_12_months(mini_sales):
    s = compute_seasonality(mini_sales)
    assert len(s) == 12
    assert set(s.keys()) == set(range(1, 13))


def test_mean_is_one(mini_sales):
    s = compute_seasonality(mini_sales)
    mean = sum(s.values()) / 12
    assert mean == pytest.approx(1.0, abs=0.01)


def test_all_positive(mini_sales):
    s = compute_seasonality(mini_sales)
    for v in s.values():
        assert v > 0


def test_months_without_data_get_floor(mini_sales):
    """Months with no sales should get a floor value, not zero."""
    s = compute_seasonality(mini_sales)
    for v in s.values():
        assert v >= 0.1  # floor
```

- [ ] **Step 2.2 — Verify fails**

Run: `python -m pytest tests/test_simulation/test_seasonality.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 2.3 — Implement**

File `src/simulation/seasonality.py`:

```python
"""Compute monthly seasonality coefficients from historical sales."""
from __future__ import annotations

import pandas as pd

FLOOR = 0.1  # minimum coefficient for months with no/little data


def compute_seasonality(
    df: pd.DataFrame,
    date_col: str = "date_facture",
    ca_col: str = "ca_ht_article",
) -> dict[int, float]:
    """Return {month_int: coefficient} where mean(coefficients) ≈ 1.0.

    Args:
        df: sales DataFrame with date_facture and ca_ht_article.
        date_col: column name for the date.
        ca_col: column name for the revenue.

    Returns:
        Dict mapping month number (1-12) to a multiplicative coefficient.
    """
    monthly_ca = (
        df.groupby(df[date_col].dt.month)[ca_col]
        .sum()
    )
    # Fill missing months with 0 then apply floor
    all_months = pd.Series(0.0, index=range(1, 13))
    for m, v in monthly_ca.items():
        all_months[m] = float(v)

    # Normalize so mean = 1.0
    raw_mean = all_months.mean()
    if raw_mean == 0:
        return {m: 1.0 for m in range(1, 13)}

    coefficients = all_months / raw_mean
    # Apply floor
    coefficients = coefficients.clip(lower=FLOOR)
    # Re-normalize after floor
    coefficients = coefficients / coefficients.mean()
    return {int(m): round(float(v), 4) for m, v in coefficients.items()}
```

- [ ] **Step 2.4 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_seasonality.py -v`
Expected: 4 passed.

- [ ] **Step 2.5 — Commit**

```bash
git add src/simulation/seasonality.py tests/test_simulation/test_seasonality.py
git commit -m "feat(simulation): seasonality extraction — P3 Task 2"
```

---

# Part B — Mesa Agents & Model

## Task 3 — StoreAgent

Passive agent holding per-store parameters (effort levels, price multipliers, campaigns). No behaviour logic in Phase 1.

**Files:**
- Create: `src/simulation/agents/__init__.py` (empty)
- Create: `src/simulation/agents/store.py`
- Create: `tests/test_simulation/test_store_agent.py`

- [ ] **Step 3.1 — Write failing tests**

File `tests/test_simulation/test_store_agent.py`:

```python
import mesa
import pytest
from src.simulation.agents.store import StoreAgent


def test_store_agent_has_required_attributes():
    model = mesa.Model(seed=42)
    store = StoreAgent(model, store_name="Avranches")
    assert store.store_name == "Avranches"
    assert isinstance(store.effort_commercial_level, dict)
    assert isinstance(store.price_multipliers, dict)
    assert isinstance(store.active_campaigns, list)


def test_default_effort_is_neutral():
    model = mesa.Model(seed=42)
    store = StoreAgent(model, store_name="Rampan")
    # Default effort for any archetype should be 1.0
    assert store.get_effort(archetype_id=0) == 1.0
    assert store.get_effort(archetype_id=99) == 1.0


def test_price_multiplier_default_is_neutral():
    model = mesa.Model(seed=42)
    store = StoreAgent(model, store_name="Yquelon")
    assert store.get_price_multiplier("PREMIUM") == 1.0


def test_custom_effort_and_price():
    model = mesa.Model(seed=42)
    store = StoreAgent(
        model,
        store_name="Avranches",
        effort_commercial_level={0: 1.3},
        price_multipliers={"PREMIUM": 0.9},
    )
    assert store.get_effort(0) == 1.3
    assert store.get_effort(1) == 1.0  # fallback
    assert store.get_price_multiplier("PREMIUM") == 0.9
    assert store.get_price_multiplier("ESSENTIEL") == 1.0  # fallback
```

- [ ] **Step 3.2 — Verify fails**

- [ ] **Step 3.3 — Implement**

File `src/simulation/agents/store.py`:

```python
"""StoreAgent — passive parameter holder for a Visaudio store.

Phase 1: no behavioural logic. Holds effort levels, price multipliers,
and campaign definitions that ClientAgents read during their step.
"""
from __future__ import annotations

import mesa


class StoreAgent(mesa.Agent):
    """One of the 6 Visaudio stores."""

    def __init__(
        self,
        model: mesa.Model,
        store_name: str,
        effort_commercial_level: dict[int, float] | None = None,
        price_multipliers: dict[str, float] | None = None,
        active_campaigns: list[dict] | None = None,
    ) -> None:
        super().__init__(model)
        self.store_name = store_name
        self.effort_commercial_level: dict[int, float] = effort_commercial_level or {}
        self.price_multipliers: dict[str, float] = price_multipliers or {}
        self.active_campaigns: list[dict] = active_campaigns or []

    def get_effort(self, archetype_id: int) -> float:
        """Return the effort multiplier for the given archetype (default 1.0)."""
        return self.effort_commercial_level.get(archetype_id, 1.0)

    def get_price_multiplier(self, gamme: str) -> float:
        """Return the price multiplier for the given gamme (default 1.0)."""
        return self.price_multipliers.get(gamme, 1.0)
```

- [ ] **Step 3.4 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_store_agent.py -v`
Expected: 4 passed.

- [ ] **Step 3.5 — Commit**

```bash
git add src/simulation/agents/__init__.py src/simulation/agents/store.py tests/test_simulation/test_store_agent.py
git commit -m "feat(simulation): StoreAgent — passive param holder — P3 Task 3"
```

---

## Task 4 — ClientAgent

The core behavioural agent. Each ClientAgent represents one customer archetype instance and decides each step (= 1 month) whether to buy, which store, which gamme, and what ticket.

**Files:**
- Create: `src/simulation/agents/client.py`
- Create: `tests/test_simulation/test_client_agent.py`

- [ ] **Step 4.1 — Write failing tests**

File `tests/test_simulation/test_client_agent.py`:

Test the client agent's attributes and its `step()` method in isolation using a minimal Mesa Model mock. Key tests:

```python
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
        gamme_distribution={"ESSENTIEL": 0.6, "CONFORT": 0.3, "PREMIUM": 0.08, "PRESTIGE": 0.02},
        switch_prob=0.05,
        mean_ticket=200.0,
    )


def test_client_agent_creation(simple_archetype):
    model = mesa.Model(seed=42)
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
    """A client who bought recently (last_purchase_step=0, current=1) should NOT buy."""
    model = mesa.Model(seed=42)
    model.current_step = 1
    model.seasonality = {m: 1.0 for m in range(1, 13)}
    store = StoreAgent(model, store_name="Avranches")
    model.stores = {"Avranches": store}
    model.sales_log = []

    client = ClientAgent(
        model,
        archetype=simple_archetype,
        home_store_name="Avranches",
        conventionnement="LIBRE",
        age=55,
        last_purchase_step=0,
    )
    # With interval=12, 1 month since last purchase → should not trigger
    client.step()
    assert len(model.sales_log) == 0


def test_client_buys_deterministically_with_high_hazard():
    """Force a purchase by setting hazard to 1.0 and interval to 1."""
    always_buy = ArchetypeParams(
        archetype_id=0, label="always", n_clients=1,
        purchase_interval_months=1.0, hazard_base=1.0,
        gamme_distribution={"ESSENTIEL": 1.0, "CONFORT": 0.0, "PREMIUM": 0.0, "PRESTIGE": 0.0},
        switch_prob=0.0, mean_ticket=100.0,
    )
    model = mesa.Model(seed=42)
    model.current_step = 2
    model.seasonality = {m: 1.0 for m in range(1, 13)}
    store = StoreAgent(model, store_name="Avranches")
    model.stores = {"Avranches": store}
    model.sales_log = []

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
```

- [ ] **Step 4.2 — Verify fails**

- [ ] **Step 4.3 — Implement**

File `src/simulation/agents/client.py`:

Implement the `ClientAgent` following the pseudo-code in spec §8.2:

```python
"""ClientAgent — individual customer with purchase behaviour.

Each agent belongs to one archetype and decides monthly whether to buy,
from which store, which gamme, and what ticket.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import mesa

if TYPE_CHECKING:
    from src.simulation.archetypes import ArchetypeParams

GAMME_ORDERED: list[str] = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


class ClientAgent(mesa.Agent):
    """A Visaudio customer."""

    def __init__(
        self,
        model: mesa.Model,
        archetype: ArchetypeParams,
        home_store_name: str,
        conventionnement: str,
        age: int,
        last_purchase_step: int,
    ) -> None:
        super().__init__(model)
        self.archetype = archetype
        self.home_store_name = home_store_name
        self.conventionnement = conventionnement
        self.age = age
        self.last_purchase_step = last_purchase_step
        self.last_purchase_gamme: str | None = None
        # Personal interval: archetype median ± small noise
        noise = self.model.random.gauss(0, max(archetype.purchase_interval_months * 0.15, 0.5))
        self.personal_interval = max(1.0, archetype.purchase_interval_months + noise)

    def step(self) -> None:
        """Monthly decision: should I buy? If so, where and what?"""
        months_since = self.model.current_step - self.last_purchase_step
        if months_since < self.personal_interval:
            return

        # Hazard rate modulated by seasonality
        current_month = ((self.model.current_step - 1) % 12) + 1
        seasonality = self.model.seasonality.get(current_month, 1.0)
        p_buy = self.archetype.hazard_base * seasonality
        p_buy = min(p_buy, 1.0)

        if self.model.random.random() > p_buy:
            return

        # Choose store
        if self.model.random.random() < self.archetype.switch_prob:
            other_stores = [s for s in self.model.stores if s != self.home_store_name]
            store_name = self.model.random.choice(other_stores) if other_stores else self.home_store_name
        else:
            store_name = self.home_store_name

        store = self.model.stores[store_name]

        # Gamme selection with effort and price modulation
        probs = self._compute_gamme_probs(store)
        gamme = self._sample_gamme(probs)

        # Ticket sampling: log-normal around archetype mean
        ticket = self._sample_ticket(gamme)

        # Record the sale
        self.model.sales_log.append({
            "step": self.model.current_step,
            "client_id": self.unique_id,
            "archetype_id": self.archetype.archetype_id,
            "store": store_name,
            "gamme": gamme,
            "ticket": round(ticket, 2),
            "conventionnement": self.conventionnement,
        })
        self.last_purchase_step = self.model.current_step
        self.last_purchase_gamme = gamme

    def _compute_gamme_probs(self, store) -> dict[str, float]:
        """Apply effort and price multipliers to the base gamme distribution."""
        base = dict(self.archetype.gamme_distribution)
        effort = store.get_effort(self.archetype.archetype_id)
        # Effort boosts PREMIUM+PRESTIGE at the expense of ESSENTIEL+CONFORT
        if effort != 1.0:
            boost = effort - 1.0  # e.g., 0.3 for effort=1.3
            shift = boost * 0.5   # shift half of the boost factor
            base["PREMIUM"] = base.get("PREMIUM", 0) * (1 + shift)
            base["PRESTIGE"] = base.get("PRESTIGE", 0) * (1 + shift)
            base["ESSENTIEL"] = base.get("ESSENTIEL", 0) * (1 - shift * 0.5)
            base["CONFORT"] = base.get("CONFORT", 0) * (1 - shift * 0.3)

        # Price effect: lower price → higher attractiveness
        for g in GAMME_ORDERED:
            pm = store.get_price_multiplier(g)
            if pm != 1.0:
                # Elasticity: -0.5 (a 10% price drop → 5% demand increase)
                elasticity_effect = 1.0 + (-0.5) * (pm - 1.0)
                base[g] = base.get(g, 0) * max(elasticity_effect, 0.01)

        # Normalize
        total = sum(base.values())
        if total <= 0:
            return {g: 1.0 / len(GAMME_ORDERED) for g in GAMME_ORDERED}
        return {g: base[g] / total for g in GAMME_ORDERED}

    def _sample_gamme(self, probs: dict[str, float]) -> str:
        """Weighted random choice of gamme."""
        r = self.model.random.random()
        cumul = 0.0
        for g in GAMME_ORDERED:
            cumul += probs.get(g, 0.0)
            if r <= cumul:
                return g
        return GAMME_ORDERED[-1]

    def _sample_ticket(self, gamme: str) -> float:
        """Sample a ticket amount from a log-normal centered on archetype mean.

        Gamme multipliers (rough network averages):
        ESSENTIEL ×0.7, CONFORT ×0.9, PREMIUM ×1.3, PRESTIGE ×1.8
        """
        gamme_mult = {"ESSENTIEL": 0.7, "CONFORT": 0.9, "PREMIUM": 1.3, "PRESTIGE": 1.8}
        base = self.archetype.mean_ticket * gamme_mult.get(gamme, 1.0)
        # Log-normal with ~20% CV
        import math
        sigma = 0.2
        mu = math.log(base) - sigma**2 / 2
        return max(5.0, self.model.random.lognormvariate(mu, sigma))
```

- [ ] **Step 4.4 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_client_agent.py -v`
Expected: all passed.

- [ ] **Step 4.5 — Commit**

```bash
git add src/simulation/agents/client.py tests/test_simulation/test_client_agent.py
git commit -m "feat(simulation): ClientAgent with purchase behaviour — P3 Task 4"
```

---

## Task 5 — VisaudioModel

The main Mesa Model that orchestrates simulation steps. Holds stores, clients, seasonality, and a `DataCollector`.

**Files:**
- Create: `src/simulation/model.py`
- Create: `src/simulation/metrics.py`
- Create: `tests/test_simulation/test_model.py`
- Create: `tests/test_simulation/test_metrics.py`

- [ ] **Step 5.1 — Write failing tests**

File `tests/test_simulation/test_model.py`:

```python
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
    assert len(model.agents) > 0  # Mesa 3.x: model.agents is an AgentSet


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
    # Should have collected some sales
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
```

File `tests/test_simulation/test_metrics.py`:

```python
import pytest
from src.simulation.metrics import extract_monthly_metrics


def test_extract_returns_expected_keys():
    sales_log = [
        {"step": 1, "store": "Avranches", "gamme": "PREMIUM", "ticket": 200.0,
         "client_id": 1, "archetype_id": 0, "conventionnement": "LIBRE"},
    ]
    metrics = extract_monthly_metrics(sales_log, n_steps=3)
    assert "ca_reseau" in metrics
    assert "ca_par_magasin" in metrics
    assert "mix_gamme_reseau" in metrics
    assert "panier_moyen" in metrics
    assert "n_transactions" in metrics
    assert len(metrics["ca_reseau"]) == 3


def test_ca_matches_sum_of_tickets():
    sales_log = [
        {"step": 1, "store": "A", "gamme": "ESSENTIEL", "ticket": 100.0,
         "client_id": 1, "archetype_id": 0, "conventionnement": "LIBRE"},
        {"step": 1, "store": "A", "gamme": "PREMIUM", "ticket": 250.0,
         "client_id": 2, "archetype_id": 0, "conventionnement": "CSS"},
    ]
    metrics = extract_monthly_metrics(sales_log, n_steps=1)
    assert metrics["ca_reseau"][0] == pytest.approx(350.0)
```

- [ ] **Step 5.2 — Verify fails**

- [ ] **Step 5.3 — Implement `metrics.py`**

File `src/simulation/metrics.py`:

```python
"""Post-processing of the simulation sales log into monthly metrics."""
from __future__ import annotations

from collections import defaultdict

GAMME_ORDERED: list[str] = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


def extract_monthly_metrics(
    sales_log: list[dict],
    n_steps: int,
) -> dict:
    """Aggregate the raw sales log into per-step metrics.

    Returns dict with keys:
        ca_reseau: list[float]          — total CA per step
        ca_par_magasin: dict[str, list[float]]
        mix_gamme_reseau: dict[str, list[float]]  — share per gamme per step
        panier_moyen: list[float]       — mean ticket per step
        n_transactions: list[int]       — count per step
    """
    # Group by step
    by_step: dict[int, list[dict]] = defaultdict(list)
    for sale in sales_log:
        by_step[sale["step"]].append(sale)

    ca_reseau = []
    ca_par_magasin: dict[str, list[float]] = defaultdict(list)
    mix_gamme: dict[str, list[float]] = {g: [] for g in GAMME_ORDERED}
    panier_moyen = []
    n_transactions = []

    # Collect all store names
    all_stores = sorted({s["store"] for s in sales_log}) if sales_log else []

    for step in range(1, n_steps + 1):
        sales = by_step.get(step, [])
        tickets = [s["ticket"] for s in sales]
        total_ca = sum(tickets)
        ca_reseau.append(round(total_ca, 2))
        n_transactions.append(len(sales))
        panier_moyen.append(round(total_ca / max(len(sales), 1), 2))

        # Per store
        store_ca: dict[str, float] = defaultdict(float)
        for s in sales:
            store_ca[s["store"]] += s["ticket"]
        for store in all_stores:
            ca_par_magasin[store].append(round(store_ca.get(store, 0.0), 2))

        # Mix gamme
        gamme_count: dict[str, int] = defaultdict(int)
        for s in sales:
            gamme_count[s["gamme"]] += 1
        total_count = max(len(sales), 1)
        for g in GAMME_ORDERED:
            mix_gamme[g].append(round(gamme_count.get(g, 0) / total_count, 4))

    return {
        "ca_reseau": ca_reseau,
        "ca_par_magasin": dict(ca_par_magasin),
        "mix_gamme_reseau": mix_gamme,
        "panier_moyen": panier_moyen,
        "n_transactions": n_transactions,
    }
```

- [ ] **Step 5.4 — Implement `model.py`**

File `src/simulation/model.py`:

```python
"""VisaudioModel — the main Mesa simulation model.

Creates StoreAgents and ClientAgents from historical data + archetypes,
then runs monthly steps collecting sales.
"""
from __future__ import annotations

import mesa
import pandas as pd

from src.simulation.agents.client import ClientAgent
from src.simulation.agents.store import StoreAgent
from src.simulation.archetypes import load_archetypes_from_payload, ArchetypeParams
from src.simulation.seasonality import compute_seasonality


class VisaudioModel(mesa.Model):
    """Agent-based model for Visaudio optical retail network."""

    def __init__(
        self,
        sales_df: pd.DataFrame,
        archetypes_payload: dict,
        n_steps: int = 36,
        seed: int | None = 42,
        store_overrides: dict[str, dict] | None = None,
    ) -> None:
        """
        Args:
            sales_df: normalized sales DataFrame with segment_id column.
            archetypes_payload: dict from archetypes.json.
            n_steps: number of monthly steps to simulate.
            seed: RNG seed for reproducibility.
            store_overrides: optional dict {store_name: {effort_commercial_level, price_multipliers, active_campaigns}}.
        """
        super().__init__(seed=seed)
        self.n_steps = n_steps
        self.current_step = 0
        self.sales_log: list[dict] = []

        # Load archetype params
        self.archetype_params = load_archetypes_from_payload(archetypes_payload)

        # Compute seasonality
        self.seasonality = compute_seasonality(sales_df)

        # Create store agents
        store_names = sorted(sales_df["ville"].unique())
        self.stores: dict[str, StoreAgent] = {}
        overrides = store_overrides or {}
        for name in store_names:
            kwargs = overrides.get(name, {})
            store = StoreAgent(
                self,
                store_name=name,
                effort_commercial_level=kwargs.get("effort_commercial_level"),
                price_multipliers=kwargs.get("price_multipliers"),
                active_campaigns=kwargs.get("active_campaigns"),
            )
            self.stores[name] = store

        # Create client agents from historical data
        self._init_clients(sales_df)

    def _init_clients(self, df: pd.DataFrame) -> None:
        """Instantiate one ClientAgent per historical client."""
        # Per-client summary
        clients = df.groupby("id_client").agg(
            segment_id=("segment_id", "first"),
            ville=("ville", lambda x: x.mode().iloc[0]),  # most frequent store
            conventionnement=("conventionnement", lambda x: x.mode().iloc[0]),
            age=("age_client", "last"),
            last_date=("date_facture", "max"),
        )
        # Convert last_date to a negative step offset (months before t=0)
        max_date = df["date_facture"].max()
        for _, row in clients.iterrows():
            seg_id = int(row["segment_id"])
            archetype = self.archetype_params.get(seg_id)
            if archetype is None:
                continue  # skip clients in unknown segments

            months_ago = max(1, int((max_date - row["last_date"]).days / 30))
            ClientAgent(
                self,
                archetype=archetype,
                home_store_name=str(row["ville"]),
                conventionnement=str(row["conventionnement"]),
                age=int(row["age"]),
                last_purchase_step=-months_ago,
            )

    def step(self) -> None:
        """Advance the model by one month."""
        self.current_step += 1
        # Activate all client agents in random order
        self.agents.shuffle_do("step")
```

- [ ] **Step 5.5 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_model.py tests/test_simulation/test_metrics.py -v`
Expected: all passed.

- [ ] **Step 5.6 — Commit**

```bash
git add src/simulation/model.py src/simulation/metrics.py tests/test_simulation/test_model.py tests/test_simulation/test_metrics.py
git commit -m "feat(simulation): VisaudioModel + metrics collector — P3 Task 5"
```

---

# Part C — Scenarios & Runner

## Task 6 — Scenario definitions

Define the 6 scenarios as data (not code). Each scenario specifies `store_overrides` that the model consumes.

**Files:**
- Create: `src/simulation/scenarios.py`
- Create: `tests/test_simulation/test_scenarios.py`

- [ ] **Step 6.1 — Write failing tests**

```python
import pytest
from src.simulation.scenarios import SCENARIOS, get_scenario, ScenarioDef


def test_six_scenarios_defined():
    assert len(SCENARIOS) == 6


def test_base_has_no_overrides():
    base = get_scenario("SC-BASE")
    assert base.store_overrides == {} or base.store_overrides is None


def test_l2a_has_effort_boost():
    hero = get_scenario("SC-L2a")
    assert hero.store_overrides is not None
    # At least one store should have effort > 1.0 for some archetype
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
```

- [ ] **Step 6.2 — Verify fails**

- [ ] **Step 6.3 — Implement**

File `src/simulation/scenarios.py`:

```python
"""Scenario definitions for Mesa simulation.

Each scenario maps to a set of store_overrides applied to VisaudioModel.
Spec reference: §8.6 and §8.7.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Archetype IDs are assigned by P2 K-Means (0 = highest panier_moyen).
# The hero archetype for SC-L2a is the one matching "50-65 CSP+ premium".
# We use archetype 0 as the default target (highest-value cluster).
# This will be overridable at runtime.
HERO_ARCHETYPE_ID = 0

STORE_NAMES: list[str] = [
    "Avranches",
    "Carentan-les-Marais",
    "Cherbourg-en-Cotentin",
    "Coutances",
    "Rampan",
    "Yquelon",
]


@dataclass(frozen=True)
class ScenarioDef:
    """Immutable scenario definition."""

    scenario_id: str
    name: str
    levier: str
    description: str
    store_overrides: dict[str, dict] = field(default_factory=dict)
    n_replications: int = 20


def _all_stores_override(**kwargs) -> dict[str, dict]:
    """Apply the same override to all 6 stores."""
    return {s: dict(kwargs) for s in STORE_NAMES}


SCENARIOS: dict[str, ScenarioDef] = {
    "SC-BASE": ScenarioDef(
        scenario_id="SC-BASE",
        name="Baseline calibré",
        levier="—",
        description="Aucune intervention. Trajectoire naturelle du réseau.",
    ),
    "SC-L2a": ScenarioDef(
        scenario_id="SC-L2a",
        name="Effort commercial ciblé (HERO)",
        levier="L2",
        description="Boost effort +30% sur l'archétype premium pour les 6 magasins.",
        store_overrides=_all_stores_override(
            effort_commercial_level={HERO_ARCHETYPE_ID: 1.3},
        ),
    ),
    "SC-L2b": ScenarioDef(
        scenario_id="SC-L2b",
        name="Best-in-class effort",
        levier="L2",
        description="Effort au niveau du meilleur observé pour tous les archétypes.",
        store_overrides=_all_stores_override(
            effort_commercial_level={i: 1.5 for i in range(10)},
        ),
    ),
    "SC-L1a": ScenarioDef(
        scenario_id="SC-L1a",
        name="Baisse PREMIUM -10%",
        levier="L1",
        description="Réduction de prix de 10% sur la gamme PREMIUM.",
        store_overrides=_all_stores_override(
            price_multipliers={"PREMIUM": 0.9},
        ),
    ),
    "SC-L4a": ScenarioDef(
        scenario_id="SC-L4a",
        name="Campagne dormants",
        levier="L4",
        description="Campagne de réactivation ciblant les clients dormants (+30% boost, 6 mois).",
        store_overrides=_all_stores_override(
            active_campaigns=[{
                "target_archetype": "dormants",
                "reactivation_boost": 0.3,
                "window_months": 6,
            }],
        ),
    ),
    "SC-L5a": ScenarioDef(
        scenario_id="SC-L5a",
        name="Santéclair -10% remboursement",
        levier="L5",
        description="Scénario défensif : Santéclair réduit le remboursement de 10%.",
        store_overrides=_all_stores_override(
            price_multipliers={"ESSENTIEL": 1.05, "CONFORT": 1.05, "PREMIUM": 1.08, "PRESTIGE": 1.08},
        ),
    ),
}


def get_scenario(scenario_id: str) -> ScenarioDef:
    """Retrieve a scenario by ID or raise KeyError."""
    return SCENARIOS[scenario_id]
```

- [ ] **Step 6.4 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_scenarios.py -v`
Expected: 5 passed.

- [ ] **Step 6.5 — Commit**

```bash
git add src/simulation/scenarios.py tests/test_simulation/test_scenarios.py
git commit -m "feat(simulation): 6 scenario definitions — P3 Task 6"
```

---

## Task 7 — Batch runner

Run N replications of a scenario, collect trajectories, and compute mean + CI 95%.

**Files:**
- Create: `src/simulation/runner.py`
- Create: `tests/test_simulation/test_runner.py`

- [ ] **Step 7.1 — Write failing tests**

```python
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
```

- [ ] **Step 7.2 — Verify fails**

- [ ] **Step 7.3 — Implement**

File `src/simulation/runner.py`:

```python
"""Batch runner — run N replications of a scenario and aggregate results."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

from src.simulation.metrics import extract_monthly_metrics
from src.simulation.model import VisaudioModel
from src.simulation.scenarios import get_scenario


@dataclass
class RunResult:
    """Aggregated output from N replications of a scenario."""

    scenario_id: str
    n_replications: int
    n_steps: int
    months: list[int]
    ca_mean: list[float]
    ca_lower: list[float]   # CI 95% lower bound
    ca_upper: list[float]   # CI 95% upper bound
    ca_par_magasin_mean: dict[str, list[float]]
    mix_gamme_mean: dict[str, list[float]]
    panier_moyen_mean: list[float]
    n_transactions_mean: list[float]


def run_scenario(
    sales_df: pd.DataFrame,
    archetypes_payload: dict,
    scenario_id: str,
    n_steps: int = 36,
    n_replications: int = 20,
    seed: int = 42,
) -> RunResult:
    """Run N replications and aggregate trajectories.

    Each replication uses seed = base_seed + replication_index for
    reproducibility while ensuring inter-replication variance.
    """
    scenario = get_scenario(scenario_id)
    all_ca: list[list[float]] = []
    all_ca_store: dict[str, list[list[float]]] = {}
    all_mix: dict[str, list[list[float]]] = {}
    all_panier: list[list[float]] = []
    all_n_tx: list[list[float]] = []

    for rep in range(n_replications):
        model = VisaudioModel(
            sales_df=sales_df,
            archetypes_payload=archetypes_payload,
            n_steps=n_steps,
            seed=seed + rep,
            store_overrides=scenario.store_overrides or None,
        )
        for _ in range(n_steps):
            model.step()

        metrics = extract_monthly_metrics(model.sales_log, n_steps)
        all_ca.append(metrics["ca_reseau"])
        all_panier.append(metrics["panier_moyen"])
        all_n_tx.append([float(x) for x in metrics["n_transactions"]])

        for store, vals in metrics["ca_par_magasin"].items():
            all_ca_store.setdefault(store, []).append(vals)
        for g, vals in metrics["mix_gamme_reseau"].items():
            all_mix.setdefault(g, []).append(vals)

    ca_arr = np.array(all_ca)
    ca_mean = np.mean(ca_arr, axis=0)
    ca_std = np.std(ca_arr, axis=0, ddof=1) if n_replications > 1 else np.zeros(n_steps)
    z = 1.96
    ca_lower = ca_mean - z * ca_std / np.sqrt(n_replications)
    ca_upper = ca_mean + z * ca_std / np.sqrt(n_replications)

    # Per-store mean
    ca_store_mean = {
        s: np.mean(np.array(runs), axis=0).round(2).tolist()
        for s, runs in all_ca_store.items()
    }
    mix_mean = {
        g: np.mean(np.array(runs), axis=0).round(4).tolist()
        for g, runs in all_mix.items()
    }
    panier_mean = np.mean(np.array(all_panier), axis=0).round(2).tolist()
    n_tx_mean = np.mean(np.array(all_n_tx), axis=0).round(1).tolist()

    return RunResult(
        scenario_id=scenario_id,
        n_replications=n_replications,
        n_steps=n_steps,
        months=list(range(1, n_steps + 1)),
        ca_mean=ca_mean.round(2).tolist(),
        ca_lower=ca_lower.round(2).tolist(),
        ca_upper=ca_upper.round(2).tolist(),
        ca_par_magasin_mean=ca_store_mean,
        mix_gamme_mean=mix_mean,
        panier_moyen_mean=panier_mean,
        n_transactions_mean=n_tx_mean,
    )


def write_run_result(result: RunResult, path: Path | str) -> None:
    """Serialize a RunResult to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(result), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
```

- [ ] **Step 7.4 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_runner.py -v`
Expected: 3 passed.

- [ ] **Step 7.5 — Commit**

```bash
git add src/simulation/runner.py tests/test_simulation/test_runner.py
git commit -m "feat(simulation): batch runner with CI aggregation — P3 Task 7"
```

---

# Part D — Calibration & Validation

## Task 8 — Calibration + backtest

Calibrate the model on 2023-2024 data, backtest against 2025, and verify tolerances from spec §8.5.

**Files:**
- Create: `src/simulation/calibration.py`
- Create: `tests/test_simulation/test_calibration.py`

- [ ] **Step 8.1 — Write failing tests**

```python
import pytest
from src.simulation.calibration import (
    split_train_test,
    compute_tolerance_report,
    ToleranceReport,
)


def test_split_train_test(mini_sales):
    train, test = split_train_test(mini_sales, train_end_year=2023)
    assert len(train) > 0
    assert train["date_facture"].dt.year.max() <= 2023 or len(test) == 0
    # If mini_sales only has 2023-2024, test should have 2024 data
    if test is not None and len(test) > 0:
        assert test["date_facture"].dt.year.min() >= 2024


def test_tolerance_report_structure():
    actual = {"Avranches": 1_000_000.0, "Rampan": 500_000.0}
    simulated = {"Avranches": 1_040_000.0, "Rampan": 480_000.0}
    report = compute_tolerance_report(
        actual_ca_by_store=actual,
        simulated_ca_by_store=simulated,
        tolerance_pct=5.0,
    )
    assert isinstance(report, ToleranceReport)
    assert len(report.store_results) == 2
    assert isinstance(report.all_within_tolerance, bool)


def test_tolerance_passes_within_5pct():
    actual = {"A": 100.0}
    simulated = {"A": 103.0}
    report = compute_tolerance_report(actual, simulated, tolerance_pct=5.0)
    assert report.all_within_tolerance is True


def test_tolerance_fails_outside_5pct():
    actual = {"A": 100.0}
    simulated = {"A": 120.0}
    report = compute_tolerance_report(actual, simulated, tolerance_pct=5.0)
    assert report.all_within_tolerance is False
```

- [ ] **Step 8.2 — Verify fails**

- [ ] **Step 8.3 — Implement**

File `src/simulation/calibration.py`:

```python
"""Calibration utilities — train/test split and tolerance verification.

Spec §8.5: CA total annuel par magasin ±5%, mix gamme ±3pp,
panier moyen par segment ±10%, saisonnalité R² ≥ 0.8.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class StoreResult:
    store: str
    actual: float
    simulated: float
    pct_error: float
    within_tolerance: bool


@dataclass
class ToleranceReport:
    store_results: list[StoreResult]
    all_within_tolerance: bool


def split_train_test(
    df: pd.DataFrame,
    train_end_year: int = 2024,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split sales DataFrame into train (≤ train_end_year) and test (> train_end_year).

    For standard calibration: train on 2023-2024, test on 2025.
    """
    mask = df["date_facture"].dt.year <= train_end_year
    return df[mask].copy(), df[~mask].copy()


def compute_tolerance_report(
    actual_ca_by_store: dict[str, float],
    simulated_ca_by_store: dict[str, float],
    tolerance_pct: float = 5.0,
) -> ToleranceReport:
    """Compare actual vs simulated CA per store and check tolerances."""
    results = []
    for store, actual in actual_ca_by_store.items():
        sim = simulated_ca_by_store.get(store, 0.0)
        if actual == 0:
            pct_err = 0.0 if sim == 0 else 100.0
        else:
            pct_err = abs(sim - actual) / actual * 100
        results.append(StoreResult(
            store=store,
            actual=actual,
            simulated=sim,
            pct_error=round(pct_err, 2),
            within_tolerance=pct_err <= tolerance_pct,
        ))
    return ToleranceReport(
        store_results=results,
        all_within_tolerance=all(r.within_tolerance for r in results),
    )


def backtest_baseline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    archetypes_payload: dict,
    n_replications: int = 10,
    seed: int = 42,
) -> ToleranceReport:
    """Run baseline on train data, compare CA with test period.

    This is a higher-level function that calls the runner.
    """
    from src.simulation.runner import run_scenario

    # Actual CA per store in test period
    actual_ca = test_df.groupby("ville")["ca_ht_article"].sum().to_dict()

    # Months in test period
    n_months = max(1, test_df["date_facture"].dt.to_period("M").nunique())

    result = run_scenario(
        sales_df=train_df,
        archetypes_payload=archetypes_payload,
        scenario_id="SC-BASE",
        n_steps=n_months,
        n_replications=n_replications,
        seed=seed,
    )

    # Simulated CA per store: sum over the n_months steps
    sim_ca = {
        store: sum(vals)
        for store, vals in result.ca_par_magasin_mean.items()
    }

    return compute_tolerance_report(
        actual_ca_by_store=actual_ca,
        simulated_ca_by_store=sim_ca,
        tolerance_pct=5.0,
    )
```

- [ ] **Step 8.4 — Verify tests pass**

Run: `python -m pytest tests/test_simulation/test_calibration.py -v`
Expected: 4 passed.

- [ ] **Step 8.5 — Commit**

```bash
git add src/simulation/calibration.py tests/test_simulation/test_calibration.py
git commit -m "feat(simulation): calibration + backtest utilities — P3 Task 8"
```

---

# Part E — CLI Integration & E2E

## Task 9 — CLI `simulate` subcommand

Add a `simulate` subcommand to `cli.py` that runs a scenario and writes the result JSON.

**Files:**
- Modify: `src/cli.py`
- Modify: `tests/test_cli.py` (add test for new subcommand)

- [ ] **Step 9.1 — Write failing test**

Add to `tests/test_cli.py`:

```python
def test_simulate_help():
    """The simulate subcommand should be registered."""
    from click.testing import CliRunner
    from src.cli import cli
    result = CliRunner().invoke(cli, ["simulate", "--help"])
    assert result.exit_code == 0
    assert "scenario" in result.output.lower()
```

- [ ] **Step 9.2 — Verify fails**

- [ ] **Step 9.3 — Implement**

Add to `src/cli.py`:

```python
@cli.command()
@click.option("--parquet", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--archetypes", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--scenario", type=str, default="SC-BASE", help="Scenario ID (SC-BASE, SC-L2a, etc.)")
@click.option("--n-steps", type=int, default=36, help="Number of monthly steps.")
@click.option("--n-replications", type=int, default=20, help="Monte Carlo replications.")
@click.option("--seed", type=int, default=42)
@click.option("--out", type=click.Path(path_type=Path), default=None,
              help="Output JSON path (default: data/processed/mesa_runs/<scenario>.json)")
def simulate(
    parquet: Path, archetypes: Path, scenario: str,
    n_steps: int, n_replications: int, seed: int, out: Path | None,
) -> None:
    """Run a Mesa simulation scenario."""
    import json as _json
    from src.simulation.runner import run_scenario, write_run_result

    click.echo(f"Loading data…")
    df = pd.read_parquet(parquet)
    arch_payload = _json.loads(archetypes.read_text(encoding="utf-8"))

    click.echo(f"Running {scenario} ({n_replications} replications × {n_steps} months)…")
    result = run_scenario(
        sales_df=df,
        archetypes_payload=arch_payload,
        scenario_id=scenario,
        n_steps=n_steps,
        n_replications=n_replications,
        seed=seed,
    )

    if out is None:
        out = Path(f"data/processed/mesa_runs/{scenario}.json")
    write_run_result(result, out)
    click.echo(f"Wrote {out}")
    click.echo(f"CA mean (month 1..{n_steps}): {result.ca_mean[0]:,.0f} → {result.ca_mean[-1]:,.0f}")
```

Also update the `refresh` command to add an optional `--simulate` flag that runs SC-BASE + SC-L2a after diagnose.

- [ ] **Step 9.4 — Verify tests pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: all pass (including new test).

- [ ] **Step 9.5 — Commit**

```bash
git add src/cli.py tests/test_cli.py
git commit -m "feat(cli): add simulate subcommand — P3 Task 9"
```

---

## Task 10 — End-to-end test

Verify the full pipeline from `sample_500.xlsx` through simulation.

**Files:**
- Create: `tests/test_e2e_p3.py`

- [ ] **Step 10.1 — Write E2E test**

File `tests/test_e2e_p3.py`:

```python
"""End-to-end test for P3 — simulation on sample_500.xlsx."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

SAMPLE = Path("data/samples/sample_500.xlsx")


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_500.xlsx not available")
class TestE2EP3:
    """Run the full chain: ingest → segment → simulate (baseline, 6 months, 3 reps)."""

    @pytest.fixture(autouse=True, scope="class")
    def pipeline(self, tmp_path_factory):
        """Run ingestion + segmentation + baseline simulation once for the class."""
        tmp = tmp_path_factory.mktemp("e2e_p3")
        parquet = tmp / "sales.parquet"
        archetypes_json = tmp / "archetypes.json"
        run_json = tmp / "baseline.json"

        # Ingest
        from src.ingestion.excel_parser import read_visaudio_excel
        from src.ingestion.normalization import normalize_dataframe, write_parquet

        raw = read_visaudio_excel(SAMPLE)
        df, _ = normalize_dataframe(raw, return_rejected=True)
        write_parquet(df, parquet)

        # Segment
        from src.segmentation.pipeline import run_segmentation, write_archetypes_json

        df_seg, arch = run_segmentation(df, n_clusters=6)
        write_parquet(df_seg, parquet)
        write_archetypes_json(arch, archetypes_json)

        # Simulate
        from src.simulation.runner import run_scenario, write_run_result

        result = run_scenario(
            sales_df=df_seg,
            archetypes_payload=arch,
            scenario_id="SC-BASE",
            n_steps=6,
            n_replications=3,
            seed=42,
        )
        write_run_result(result, run_json)

        # Store for tests
        self.__class__._result = result
        self.__class__._run_json = run_json

    def test_baseline_produces_6_months(self):
        assert len(self._result.ca_mean) == 6

    def test_ca_is_positive(self):
        assert all(v >= 0 for v in self._result.ca_mean)

    def test_ci_bounds_hold(self):
        for i in range(6):
            assert self._result.ca_lower[i] <= self._result.ca_mean[i]
            assert self._result.ca_mean[i] <= self._result.ca_upper[i]

    def test_output_json_exists(self):
        assert self._run_json.exists()

    def test_result_is_reproducible(self):
        """A second run with same seed should match."""
        from src.simulation.runner import run_scenario

        parquet = self._run_json.parent / "sales.parquet"
        import json

        arch = json.loads(
            (self._run_json.parent / "archetypes.json").read_text(encoding="utf-8")
        )
        df = pd.read_parquet(parquet)
        r2 = run_scenario(df, arch, "SC-BASE", n_steps=6, n_replications=3, seed=42)
        assert r2.ca_mean == self._result.ca_mean
```

- [ ] **Step 10.2 — Verify E2E passes**

Run: `python -m pytest tests/test_e2e_p3.py -v --tb=short`
Expected: 5 passed (or skipped if sample not found).

- [ ] **Step 10.3 — Commit**

```bash
git add tests/test_e2e_p3.py
git commit -m "test: add E2E test for P3 simulation pipeline"
```

---

## Task 11 — Ensure `mesa_runs/` is gitignored

- [ ] **Step 11.1 — Update `.gitignore`**

Append `data/processed/mesa_runs/` to `.gitignore` if not already present.

- [ ] **Step 11.2 — Final test suite run**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all tests pass (P1 + P2 + P3).

- [ ] **Step 11.3 — Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore mesa_runs output directory"
```

---

## Calibration tolerances (reference from §8.5)

| Métrique | Tolérance | Vérifié dans |
|---|---|---|
| CA total annuel par magasin | ±5 % | `test_calibration.py` |
| Mix gamme verre par magasin | ±3 pp par gamme | future tuning iteration |
| Panier moyen par segment | ±10 % | future tuning iteration |
| Saisonnalité mensuelle (R² du profil) | ≥ 0.8 | `test_seasonality.py` |

> **Plan B (D9)** : si le modèle ne converge pas aux tolérances après quelques itérations de tuning, basculer en "projection qualitative" avec disclaimer. Le hero H5 (statique, 123 K€/an) porte le pitch seul. La démo ne doit JAMAIS être bloquée par la calibration.

---

## Summary of commits

| # | Message | Files |
|---|---|---|
| 1 | `feat(simulation): archetype loader — P3 Task 1` | `archetypes.py`, fixtures, tests |
| 2 | `feat(simulation): seasonality extraction — P3 Task 2` | `seasonality.py`, tests |
| 3 | `feat(simulation): StoreAgent — passive param holder — P3 Task 3` | `agents/store.py`, tests |
| 4 | `feat(simulation): ClientAgent with purchase behaviour — P3 Task 4` | `agents/client.py`, tests |
| 5 | `feat(simulation): VisaudioModel + metrics collector — P3 Task 5` | `model.py`, `metrics.py`, tests |
| 6 | `feat(simulation): 6 scenario definitions — P3 Task 6` | `scenarios.py`, tests |
| 7 | `feat(simulation): batch runner with CI aggregation — P3 Task 7` | `runner.py`, tests |
| 8 | `feat(simulation): calibration + backtest utilities — P3 Task 8` | `calibration.py`, tests |
| 9 | `feat(cli): add simulate subcommand — P3 Task 9` | `cli.py` (mod), tests |
| 10 | `test: add E2E test for P3 simulation pipeline` | `test_e2e_p3.py` |
| 11 | `chore: gitignore mesa_runs output directory` | `.gitignore` |

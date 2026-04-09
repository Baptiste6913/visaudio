# P4 — Backend FastAPI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the Visaudio analytics pipeline (KPIs, archetypes, diagnostics, Mesa simulation) through a FastAPI backend with cache-first simulation, pré-chauffage at startup, and pydantic request/response models — ready for the React dashboard (P5) to consume.

**Architecture:** Thin FastAPI app reading pre-computed JSON files for static endpoints (`/kpis`, `/archetypes`, `/diagnostics`, `/scenarios`) and delegating simulation to the P3 runner with a disk-based SHA-256 cache. At startup, a background task pre-warms the 6 standard scenarios. All responses use pydantic models. CORS enabled for `localhost:5173` (Vite dev server).

**Tech Stack:** Python 3.11+, **FastAPI 0.135+** (already installed), **uvicorn 0.42+** (already installed), pydantic 2, pandas 3.0, P3 simulation modules.

**Source spec:** `docs/specs/architecture-spec.md` §9 (Backend API), §9.1 (Endpoints), §9.2 (Cache Mesa), §9.3 (Modèles pydantic).

---

## Prerequisites (one-time, before Task 1)

FastAPI and uvicorn are already installed. Verify:

```bash
python -c "import fastapi, uvicorn; print('fastapi', fastapi.__version__, 'uvicorn', uvicorn.__version__)"
```

Expected: `fastapi 0.135.2 uvicorn 0.42.0` (or ≥ those versions).

Also install httpx for async test client:

```bash
pip install httpx
python -c "import httpx; print('httpx', httpx.__version__)"
```

Append to `requirements.txt`:

```
httpx>=0.27
```

Commit:

```bash
git add requirements.txt
git commit -m "chore: add httpx for FastAPI test client (P4)"
```

---

## File structure produced by this plan

```
src/api/
├── __init__.py                     (EXISTING — currently empty, stays empty)
├── main.py                         (NEW — FastAPI app, lifespan, CORS)
├── schemas.py                      (NEW — pydantic request/response models)
├── endpoints.py                    (NEW — all route handlers)
├── cache.py                        (NEW — SHA-256 disk cache for Mesa runs)
└── prewarm.py                      (NEW — background pre-warming of 6 scenarios)

tests/
├── test_api/
│   ├── __init__.py                 (NEW — empty)
│   ├── conftest.py                 (NEW — shared fixtures: test client, tmp data dir)
│   ├── test_schemas.py             (NEW)
│   ├── test_cache.py               (NEW)
│   ├── test_endpoints.py           (NEW)
│   └── test_prewarm.py             (NEW)
└── test_e2e_p4.py                  (NEW — full startup + request cycle)
```

---

# Part A — Schemas & Cache

## Task 1 — Pydantic request/response models

Define the API schemas matching spec §9.3.

**Files:**
- Create: `src/api/schemas.py`
- Create: `tests/test_api/__init__.py` (empty)
- Create: `tests/test_api/test_schemas.py`

- [ ] **Step 1.1 — Write failing tests**

File `tests/test_api/__init__.py`: empty.

File `tests/test_api/test_schemas.py`:

```python
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
    t = Trajectory(months=[1, 2, 3], ca_mean=[100.0, 110.0, 120.0],
                   ca_lower=[90.0, 100.0, 110.0], ca_upper=[110.0, 120.0, 130.0])
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
```

- [ ] **Step 1.2 — Verify fails**

Run: `python -m pytest tests/test_api/test_schemas.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 1.3 — Implement**

File `src/api/schemas.py`:

```python
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
```

- [ ] **Step 1.4 — Verify tests pass**

Run: `python -m pytest tests/test_api/test_schemas.py -v`
Expected: 6 passed.

- [ ] **Step 1.5 — Commit**

```bash
git add src/api/schemas.py tests/test_api/__init__.py tests/test_api/test_schemas.py
git commit -m "feat(api): pydantic request/response schemas — P4 Task 1"
```

---

## Task 2 — Disk cache for Mesa runs

SHA-256 keyed disk cache: `data/processed/mesa_runs/<hash>.json`. Reads/writes `RunResult` dicts.

**Files:**
- Create: `src/api/cache.py`
- Create: `tests/test_api/test_cache.py`

- [ ] **Step 2.1 — Write failing tests**

File `tests/test_api/test_cache.py`:

```python
"""Tests for Mesa run disk cache — P4 Task 2."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.api.cache import cache_key, read_cache, write_cache


def test_cache_key_deterministic():
    k1 = cache_key("SC-BASE", {})
    k2 = cache_key("SC-BASE", {})
    assert k1 == k2
    assert len(k1) == 64  # SHA-256 hex


def test_cache_key_differs_by_scenario():
    k1 = cache_key("SC-BASE", {})
    k2 = cache_key("SC-L2a", {})
    assert k1 != k2


def test_cache_key_differs_by_params():
    k1 = cache_key("SC-L2a", {"effort": 1.3})
    k2 = cache_key("SC-L2a", {"effort": 1.5})
    assert k1 != k2


def test_write_then_read(tmp_path):
    data = {"scenario_id": "SC-BASE", "ca_mean": [100.0, 200.0]}
    key = cache_key("SC-BASE", {})
    write_cache(key, data, cache_dir=tmp_path)
    result = read_cache(key, cache_dir=tmp_path)
    assert result is not None
    assert result["ca_mean"] == [100.0, 200.0]


def test_read_cache_miss(tmp_path):
    result = read_cache("nonexistent_hash", cache_dir=tmp_path)
    assert result is None
```

- [ ] **Step 2.2 — Verify fails**

- [ ] **Step 2.3 — Implement**

File `src/api/cache.py`:

```python
"""SHA-256 disk cache for Mesa simulation run results.

Cache key = sha256(scenario_id + sorted_json(params)).
Storage: one JSON file per key in the cache directory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path("data/processed/mesa_runs")


def cache_key(scenario_id: str, params: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hex key for a scenario + params."""
    payload = scenario_id + json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_path(key: str, cache_dir: Path) -> Path:
    return cache_dir / f"{key}.json"


def read_cache(
    key: str, cache_dir: Path = DEFAULT_CACHE_DIR
) -> dict | None:
    """Read a cached result by key. Returns None on miss."""
    path = _cache_path(key, cache_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_cache(
    key: str, data: dict, cache_dir: Path = DEFAULT_CACHE_DIR
) -> Path:
    """Write a result dict to cache. Returns the file path."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key, cache_dir)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return path
```

- [ ] **Step 2.4 — Verify tests pass**

Run: `python -m pytest tests/test_api/test_cache.py -v`
Expected: 5 passed.

- [ ] **Step 2.5 — Commit**

```bash
git add src/api/cache.py tests/test_api/test_cache.py
git commit -m "feat(api): SHA-256 disk cache for Mesa runs — P4 Task 2"
```

---

# Part B — FastAPI App & Endpoints

## Task 3 — FastAPI app + static endpoints

Create the FastAPI app with lifespan, CORS, and the 5 static GET endpoints (`/health`, `/kpis`, `/archetypes`, `/diagnostics`, `/scenarios`).

**Files:**
- Create: `src/api/main.py`
- Create: `src/api/endpoints.py`
- Create: `tests/test_api/conftest.py`
- Create: `tests/test_api/test_endpoints.py`

- [ ] **Step 3.1 — Create shared test fixtures**

File `tests/test_api/conftest.py`:

```python
"""Shared fixtures for API tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app


@pytest.fixture
def data_dir(tmp_path) -> Path:
    """Create a temporary data directory with minimal JSON files."""
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "mesa_runs").mkdir()

    # Minimal kpis.json
    (processed / "kpis.json").write_text(json.dumps({
        "meta": {"generated_at": "2026-04-09"},
        "cadrage": {"ca_total": 9_100_000},
    }), encoding="utf-8")

    # Minimal archetypes.json
    (processed / "archetypes.json").write_text(json.dumps({
        "generated_at": "2026-04-09",
        "n_archetypes": 2,
        "archetypes": [
            {"id": 0, "label": "test0", "n_clients": 100,
             "share_of_clients": 0.5, "share_of_ca": 0.6,
             "centroid": {"panier_moyen": 200.0, "mois_entre_achats": 12.0,
                          "n_achats_totaux": 2.0, "part_premium_plus": 0.3,
                          "age_dernier_achat": 50.0, "ratio_monture_verre": 0.5,
                          "conventionnement_libre": 0.4, "sexe_Femme": 0.5,
                          "sexe_Homme": 0.5}},
            {"id": 1, "label": "test1", "n_clients": 100,
             "share_of_clients": 0.5, "share_of_ca": 0.4,
             "centroid": {"panier_moyen": 150.0, "mois_entre_achats": 10.0,
                          "n_achats_totaux": 1.5, "part_premium_plus": 0.1,
                          "age_dernier_achat": 45.0, "ratio_monture_verre": 0.4,
                          "conventionnement_libre": 0.3, "sexe_Femme": 0.8,
                          "sexe_Homme": 0.2}},
        ],
    }), encoding="utf-8")

    # Minimal diagnostics.json
    (processed / "diagnostics.json").write_text(json.dumps({
        "generated_at": "2026-04-09",
        "Avranches": {"findings": []},
    }), encoding="utf-8")

    return tmp_path


@pytest.fixture
def app(data_dir):
    """Create a FastAPI app pointed at the temp data directory."""
    return create_app(data_dir=data_dir / "processed", enable_prewarm=False)


@pytest.fixture
async def client(app):
    """Async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

- [ ] **Step 3.2 — Write failing tests**

File `tests/test_api/test_endpoints.py`:

```python
"""Tests for FastAPI endpoints — P4 Task 3."""
from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_get_kpis(client):
    resp = await client.get("/kpis")
    assert resp.status_code == 200
    body = resp.json()
    assert "cadrage" in body


@pytest.mark.anyio
async def test_get_archetypes(client):
    resp = await client.get("/archetypes")
    assert resp.status_code == 200
    body = resp.json()
    assert "archetypes" in body
    assert body["n_archetypes"] == 2


@pytest.mark.anyio
async def test_get_diagnostics(client):
    resp = await client.get("/diagnostics")
    assert resp.status_code == 200
    body = resp.json()
    assert "Avranches" in body


@pytest.mark.anyio
async def test_get_scenarios(client):
    resp = await client.get("/scenarios")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 6
    ids = {s["scenario_id"] for s in body}
    assert "SC-BASE" in ids
    assert "SC-L2a" in ids
```

- [ ] **Step 3.3 — Verify fails**

- [ ] **Step 3.4 — Implement `endpoints.py`**

File `src/api/endpoints.py`:

```python
"""FastAPI route handlers — spec §9.1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.schemas import ScenarioInfo, SimulateRequest, SimulateResponse, Trajectory
from src.simulation.scenarios import SCENARIOS

router = APIRouter()

# The data_dir is injected via app.state at startup
_data_dir: Path | None = None


def set_data_dir(path: Path) -> None:
    global _data_dir
    _data_dir = path


def _read_json(filename: str) -> dict:
    """Read a JSON file from the data directory."""
    if _data_dir is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    path = _data_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/kpis")
async def get_kpis() -> dict[str, Any]:
    return _read_json("kpis.json")


@router.get("/archetypes")
async def get_archetypes() -> dict[str, Any]:
    return _read_json("archetypes.json")


@router.get("/diagnostics")
async def get_diagnostics() -> dict[str, Any]:
    return _read_json("diagnostics.json")


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def get_scenarios() -> list[dict]:
    return [
        {
            "scenario_id": sc.scenario_id,
            "name": sc.name,
            "levier": sc.levier,
            "description": sc.description,
        }
        for sc in SCENARIOS.values()
    ]
```

- [ ] **Step 3.5 — Implement `main.py`**

File `src/api/main.py`:

```python
"""FastAPI application factory — spec §9."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import endpoints

DEFAULT_DATA_DIR = Path("data/processed")


def create_app(
    data_dir: Path = DEFAULT_DATA_DIR,
    enable_prewarm: bool = True,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        data_dir: Path to the processed data directory.
        enable_prewarm: Whether to pre-warm Mesa scenarios at startup.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        endpoints.set_data_dir(data_dir)
        if enable_prewarm:
            from src.api.prewarm import prewarm_scenarios
            prewarm_scenarios(data_dir)
        yield
        # Shutdown — nothing to clean up

    app = FastAPI(
        title="Visaudio Optique Analytics",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(endpoints.router)

    return app
```

- [ ] **Step 3.6 — Verify tests pass**

Run: `python -m pytest tests/test_api/test_endpoints.py -v`
Expected: 5 passed.

- [ ] **Step 3.7 — Commit**

```bash
git add src/api/main.py src/api/endpoints.py tests/test_api/conftest.py tests/test_api/test_endpoints.py
git commit -m "feat(api): FastAPI app + static endpoints — P4 Task 3"
```

---

## Task 4 — POST /simulate endpoint

The simulation endpoint: cache-first lookup, Mesa run on miss, baseline + intervention comparison, ΔCA calculation.

**Files:**
- Modify: `src/api/endpoints.py` (add `/simulate` route)
- Modify: `tests/test_api/test_endpoints.py` (add simulation tests)

- [ ] **Step 4.1 — Write failing tests**

Append to `tests/test_api/test_endpoints.py`:

```python
@pytest.mark.anyio
async def test_simulate_base_returns_200(client, data_dir):
    """POST /simulate with SC-BASE should work (mini data, few reps)."""
    # We need a parquet + archetypes for the runner
    # The conftest already created archetypes.json; we need a sales parquet too.
    # Create a minimal one from the test fixtures.
    import pandas as pd
    from tests.test_simulation.conftest import _row, GAMME_ORDER
    from pandas.api.types import CategoricalDtype

    rows = []
    for cid in range(1, 6):
        rows.append(_row(
            id_client=cid, ville="Avranches",
            id_facture_rang=f"F{cid}A|1",
            date_facture=pd.Timestamp("2024-03-15"),
            famille_article="OPT_VERRE", gamme_verre_visaudio="CONFORT",
            ca_ht_article=150.0, conventionnement="LIBRE",
            age_client=50, sexe="Femme", segment_id=0,
        ))
    df = pd.DataFrame(rows)
    df["date_facture"] = pd.to_datetime(df["date_facture"])
    df["segment_id"] = df["segment_id"].astype("int64")
    df["famille_article"] = df["famille_article"].astype("category")
    df["ville"] = df["ville"].astype("category")
    df["conventionnement"] = df["conventionnement"].astype("category")
    df["gamme_verre_visaudio"] = df["gamme_verre_visaudio"].astype(
        CategoricalDtype(categories=GAMME_ORDER, ordered=True)
    )
    df["sexe"] = df["sexe"].astype("category")
    df["est_verre"] = df["famille_article"] == "OPT_VERRE"
    df["est_premium_plus"] = df["gamme_verre_visaudio"].isin(["PREMIUM", "PRESTIGE"])

    parquet_path = data_dir / "processed" / "sales.parquet"
    df.to_parquet(parquet_path, engine="pyarrow")

    resp = await client.post("/simulate", json={
        "scenario_id": "SC-BASE",
        "n_steps": 3,
        "n_replications": 2,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["scenario_id"] == "SC-BASE"
    assert "baseline" in body
    assert len(body["baseline"]["ca_mean"]) == 3
    assert body["n_replications"] == 2


@pytest.mark.anyio
async def test_simulate_invalid_scenario(client):
    resp = await client.post("/simulate", json={"scenario_id": "SC-NOPE"})
    assert resp.status_code == 422  # pydantic validation error


@pytest.mark.anyio
async def test_simulate_uses_cache(client, data_dir):
    """A second call with the same params should hit cache."""
    import pandas as pd
    from tests.test_simulation.conftest import _row, GAMME_ORDER
    from pandas.api.types import CategoricalDtype

    rows = [_row(
        id_client=1, ville="Avranches", id_facture_rang="F1A|1",
        date_facture=pd.Timestamp("2024-03-15"),
        famille_article="OPT_VERRE", gamme_verre_visaudio="CONFORT",
        ca_ht_article=150.0, conventionnement="LIBRE",
        age_client=50, sexe="Femme", segment_id=0,
    )]
    df = pd.DataFrame(rows)
    df["date_facture"] = pd.to_datetime(df["date_facture"])
    df["segment_id"] = df["segment_id"].astype("int64")
    df["famille_article"] = df["famille_article"].astype("category")
    df["ville"] = df["ville"].astype("category")
    df["conventionnement"] = df["conventionnement"].astype("category")
    df["gamme_verre_visaudio"] = df["gamme_verre_visaudio"].astype(
        CategoricalDtype(categories=GAMME_ORDER, ordered=True)
    )
    df["sexe"] = df["sexe"].astype("category")
    df["est_verre"] = df["famille_article"] == "OPT_VERRE"
    df["est_premium_plus"] = df["gamme_verre_visaudio"].isin(["PREMIUM", "PRESTIGE"])

    parquet_path = data_dir / "processed" / "sales.parquet"
    if not parquet_path.exists():
        df.to_parquet(parquet_path, engine="pyarrow")

    body1 = {"scenario_id": "SC-BASE", "n_steps": 3, "n_replications": 2}
    resp1 = await client.post("/simulate", json=body1)
    assert resp1.status_code == 200
    assert resp1.json()["from_cache"] is False

    resp2 = await client.post("/simulate", json=body1)
    assert resp2.status_code == 200
    assert resp2.json()["from_cache"] is True
```

- [ ] **Step 4.2 — Verify fails**

- [ ] **Step 4.3 — Implement**

Add to `src/api/endpoints.py`:

```python
@router.post("/simulate", response_model=SimulateResponse)
async def simulate(req: SimulateRequest) -> dict[str, Any]:
    """Run a simulation scenario (cache-first)."""
    from dataclasses import asdict

    from src.api.cache import cache_key, read_cache, write_cache
    from src.simulation.runner import run_scenario

    import pandas as pd

    # Check cache
    cache_dir = _data_dir / "mesa_runs" if _data_dir else Path("data/processed/mesa_runs")
    key = cache_key(req.scenario_id, {
        "params": req.params,
        "n_steps": req.n_steps,
        "n_replications": req.n_replications,
    })
    cached = read_cache(key, cache_dir=cache_dir)
    if cached is not None:
        cached["from_cache"] = True
        return _build_simulate_response(cached, req)

    # Cache miss — run simulation
    parquet_path = _data_dir / "sales.parquet" if _data_dir else Path("data/processed/sales.parquet")
    archetypes_path = _data_dir / "archetypes.json" if _data_dir else Path("data/processed/archetypes.json")

    if not parquet_path.exists():
        raise HTTPException(status_code=503, detail="sales.parquet not found — run the pipeline first")
    if not archetypes_path.exists():
        raise HTTPException(status_code=503, detail="archetypes.json not found — run the pipeline first")

    df = pd.read_parquet(parquet_path)
    arch = json.loads(archetypes_path.read_text(encoding="utf-8"))

    result = run_scenario(
        sales_df=df,
        archetypes_payload=arch,
        scenario_id=req.scenario_id,
        n_steps=req.n_steps,
        n_replications=req.n_replications,
    )

    # Also run baseline for comparison if this isn't already the baseline
    if req.scenario_id != "SC-BASE":
        baseline = run_scenario(
            sales_df=df,
            archetypes_payload=arch,
            scenario_id="SC-BASE",
            n_steps=req.n_steps,
            n_replications=req.n_replications,
        )
    else:
        baseline = result

    result_dict = asdict(result)
    baseline_dict = asdict(baseline)

    # Compute delta
    delta_cumul = sum(result_dict["ca_mean"]) - sum(baseline_dict["ca_mean"])
    delta_low = sum(result_dict["ca_lower"]) - sum(baseline_dict["ca_upper"])
    delta_high = sum(result_dict["ca_upper"]) - sum(baseline_dict["ca_lower"])

    result_dict["_baseline"] = baseline_dict
    result_dict["_delta_cumul"] = delta_cumul
    result_dict["_delta_low"] = delta_low
    result_dict["_delta_high"] = delta_high

    # Cache
    write_cache(key, result_dict, cache_dir=cache_dir)

    return _build_simulate_response(result_dict, req, from_cache=False)


def _build_simulate_response(
    data: dict, req: SimulateRequest, from_cache: bool | None = None
) -> dict:
    """Build a SimulateResponse dict from cached or fresh run data."""
    baseline_data = data.get("_baseline", data)
    intervention_data = data

    baseline_traj = {
        "months": baseline_data["months"],
        "ca_mean": baseline_data["ca_mean"],
        "ca_lower": baseline_data.get("ca_lower", baseline_data["ca_mean"]),
        "ca_upper": baseline_data.get("ca_upper", baseline_data["ca_mean"]),
    }
    intervention_traj = {
        "months": intervention_data["months"],
        "ca_mean": intervention_data["ca_mean"],
        "ca_lower": intervention_data.get("ca_lower", intervention_data["ca_mean"]),
        "ca_upper": intervention_data.get("ca_upper", intervention_data["ca_mean"]),
    }

    return {
        "scenario_id": data.get("scenario_id", req.scenario_id),
        "params": req.params,
        "baseline": baseline_traj,
        "intervention": intervention_traj,
        "delta_ca_cumul_36m": data.get("_delta_cumul", 0.0),
        "delta_ca_ci_low": data.get("_delta_low", 0.0),
        "delta_ca_ci_high": data.get("_delta_high", 0.0),
        "n_replications": data.get("n_replications", req.n_replications),
        "from_cache": from_cache if from_cache is not None else data.get("from_cache", False),
    }
```

- [ ] **Step 4.4 — Verify tests pass**

Run: `python -m pytest tests/test_api/test_endpoints.py -v`
Expected: 8 passed.

- [ ] **Step 4.5 — Commit**

```bash
git add src/api/endpoints.py tests/test_api/test_endpoints.py
git commit -m "feat(api): POST /simulate with cache — P4 Task 4"
```

---

# Part C — Pre-warming & Integration

## Task 5 — Pre-warm scenarios at startup

Run the 6 standard scenarios at startup and cache them.

**Files:**
- Create: `src/api/prewarm.py`
- Create: `tests/test_api/test_prewarm.py`

- [ ] **Step 5.1 — Write failing tests**

File `tests/test_api/test_prewarm.py`:

```python
"""Tests for scenario pre-warming — P4 Task 5."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.api.prewarm import prewarm_scenarios, PREWARM_SCENARIOS


def test_prewarm_scenarios_list():
    """All 6 standard scenarios should be in the prewarm list."""
    assert len(PREWARM_SCENARIOS) == 6
    assert "SC-BASE" in PREWARM_SCENARIOS
    assert "SC-L2a" in PREWARM_SCENARIOS


def test_prewarm_writes_cache_files(tmp_path):
    """Prewarm should write one JSON per scenario to the cache dir."""
    cache_dir = tmp_path / "mesa_runs"
    cache_dir.mkdir()

    # Mock run_scenario to avoid actual Mesa computation
    mock_result = MagicMock()
    mock_result_dict = {
        "scenario_id": "SC-BASE", "n_replications": 2, "n_steps": 3,
        "months": [1, 2, 3], "ca_mean": [100.0, 100.0, 100.0],
        "ca_lower": [90.0, 90.0, 90.0], "ca_upper": [110.0, 110.0, 110.0],
        "ca_par_magasin_mean": {}, "mix_gamme_mean": {},
        "panier_moyen_mean": [100.0, 100.0, 100.0],
        "n_transactions_mean": [10.0, 10.0, 10.0],
    }

    with patch("src.api.prewarm.run_scenario") as mock_run, \
         patch("src.api.prewarm.asdict", return_value=mock_result_dict):
        mock_run.return_value = mock_result
        prewarm_scenarios(
            data_dir=tmp_path,
            n_steps=3,
            n_replications=2,
        )

    # Should have written files
    json_files = list(cache_dir.glob("*.json"))
    assert len(json_files) == 6
```

- [ ] **Step 5.2 — Verify fails**

- [ ] **Step 5.3 — Implement**

File `src/api/prewarm.py`:

```python
"""Pre-warm the 6 standard Mesa scenarios at backend startup.

Runs each scenario and writes the result to the disk cache so that
the first dashboard request is instantaneous.
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from src.api.cache import cache_key, read_cache, write_cache
from src.simulation.runner import run_scenario
from src.simulation.scenarios import SCENARIOS

logger = logging.getLogger(__name__)

PREWARM_SCENARIOS: list[str] = list(SCENARIOS.keys())


def prewarm_scenarios(
    data_dir: Path,
    n_steps: int = 36,
    n_replications: int = 20,
) -> None:
    """Pre-compute and cache all standard scenarios.

    Args:
        data_dir: Path to processed data (must contain sales.parquet + archetypes.json).
        n_steps: Simulation horizon in months.
        n_replications: Monte Carlo replications per scenario.
    """
    parquet_path = data_dir / "sales.parquet"
    archetypes_path = data_dir / "archetypes.json"
    cache_dir = data_dir / "mesa_runs"

    if not parquet_path.exists() or not archetypes_path.exists():
        logger.warning("Skipping prewarm: sales.parquet or archetypes.json missing")
        return

    import json
    df = pd.read_parquet(parquet_path)
    arch = json.loads(archetypes_path.read_text(encoding="utf-8"))

    for sc_id in PREWARM_SCENARIOS:
        key = cache_key(sc_id, {
            "params": {},
            "n_steps": n_steps,
            "n_replications": n_replications,
        })
        if read_cache(key, cache_dir=cache_dir) is not None:
            logger.info("Cache hit for %s — skipping", sc_id)
            continue

        logger.info("Pre-warming %s (%d reps × %d months)…", sc_id, n_replications, n_steps)
        result = run_scenario(
            sales_df=df,
            archetypes_payload=arch,
            scenario_id=sc_id,
            n_steps=n_steps,
            n_replications=n_replications,
        )
        result_dict = asdict(result)
        write_cache(key, result_dict, cache_dir=cache_dir)
        logger.info("Cached %s", sc_id)
```

- [ ] **Step 5.4 — Verify tests pass**

Run: `python -m pytest tests/test_api/test_prewarm.py -v`
Expected: 2 passed.

- [ ] **Step 5.5 — Commit**

```bash
git add src/api/prewarm.py tests/test_api/test_prewarm.py
git commit -m "feat(api): pre-warm 6 scenarios at startup — P4 Task 5"
```

---

## Task 6 — CLI `serve` subcommand

Add a `serve` command to `src/cli.py` that starts the uvicorn server.

**Files:**
- Modify: `src/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 6.1 — Write failing test**

Append to `tests/test_cli.py`:

```python
def test_serve_help():
    """The serve subcommand should be registered."""
    from click.testing import CliRunner
    from src.cli import cli
    result = CliRunner().invoke(cli, ["serve", "--help"])
    assert result.exit_code == 0
    assert "port" in result.output.lower()
```

- [ ] **Step 6.2 — Verify fails**

- [ ] **Step 6.3 — Implement**

Add to `src/cli.py` (before `if __name__`):

```python
@cli.command()
@click.option("--host", type=str, default="127.0.0.1", help="Bind host.")
@click.option("--port", type=int, default=8000, help="Bind port.")
@click.option("--data-dir", type=click.Path(exists=True, path_type=Path),
              default=Path("data/processed"), help="Path to processed data.")
@click.option("--no-prewarm", is_flag=True, default=False,
              help="Skip pre-warming of scenarios at startup.")
def serve(host: str, port: int, data_dir: Path, no_prewarm: bool) -> None:
    """Start the FastAPI backend server."""
    import uvicorn
    from src.api.main import create_app

    app = create_app(data_dir=data_dir, enable_prewarm=not no_prewarm)
    click.echo(f"Starting Visaudio API on {host}:{port} (data: {data_dir})")
    uvicorn.run(app, host=host, port=port)
```

- [ ] **Step 6.4 — Verify tests pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: all pass (including new test).

- [ ] **Step 6.5 — Commit**

```bash
git add src/cli.py tests/test_cli.py
git commit -m "feat(cli): add serve subcommand for FastAPI — P4 Task 6"
```

---

## Task 7 — E2E test + pyproject.toml anyio config

End-to-end test verifying the app starts and serves correct data. Also configure pytest for async tests.

**Files:**
- Modify: `pyproject.toml` (add anyio pytest marker config)
- Create: `tests/test_e2e_p4.py`

- [ ] **Step 7.1 — Configure pytest for anyio**

Read `pyproject.toml`, find the `[tool.pytest.ini_options]` section, and ensure it includes:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Or if using anyio (already installed as a dep), add the marker config so `@pytest.mark.anyio` works without warnings.

- [ ] **Step 7.2 — Write E2E test**

File `tests/test_e2e_p4.py`:

```python
"""End-to-end test for P4 — FastAPI on sample_500.xlsx pipeline output."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

SAMPLE = Path("data/samples/sample_500.xlsx")


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_500.xlsx not available")
class TestE2EP4:
    """Start the API on real pipeline output and verify endpoints."""

    @pytest.fixture(autouse=True, scope="class")
    def pipeline_and_app(self, tmp_path_factory):
        """Run the full pipeline, then create the app."""
        tmp = tmp_path_factory.mktemp("e2e_p4")
        processed = tmp / "processed"
        processed.mkdir()
        (processed / "mesa_runs").mkdir()

        from src.ingestion.excel_parser import read_visaudio_excel
        from src.ingestion.normalization import normalize_dataframe, write_parquet
        from src.segmentation.pipeline import run_segmentation, write_archetypes_json
        from src.kpi.pipeline import write_kpis_json
        from src.rules.diagnostics import build_diagnostics_payload, write_diagnostics_json

        raw = read_visaudio_excel(SAMPLE)
        df, _ = normalize_dataframe(raw, return_rejected=True)
        parquet = processed / "sales.parquet"
        write_parquet(df, parquet)

        df_seg, arch = run_segmentation(df, n_clusters=6)
        write_parquet(df_seg, parquet)
        write_archetypes_json(arch, processed / "archetypes.json")
        write_kpis_json(df_seg, processed / "kpis.json")

        kpis = json.loads((processed / "kpis.json").read_text(encoding="utf-8"))
        diag = build_diagnostics_payload(kpis)
        write_diagnostics_json(diag, processed / "diagnostics.json")

        from src.api.main import create_app
        self.__class__._app = create_app(data_dir=processed, enable_prewarm=False)
        self.__class__._processed = processed

    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=self._app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    @pytest.mark.anyio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_kpis_has_cadrage(self, client):
        resp = await client.get("/kpis")
        assert resp.status_code == 200
        assert "cadrage" in resp.json()

    @pytest.mark.anyio
    async def test_archetypes_has_6(self, client):
        resp = await client.get("/archetypes")
        assert resp.status_code == 200
        assert resp.json()["n_archetypes"] == 6

    @pytest.mark.anyio
    async def test_scenarios_returns_6(self, client):
        resp = await client.get("/scenarios")
        assert resp.status_code == 200
        assert len(resp.json()) == 6

    @pytest.mark.anyio
    async def test_simulate_baseline(self, client):
        resp = await client.post("/simulate", json={
            "scenario_id": "SC-BASE", "n_steps": 3, "n_replications": 2,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["scenario_id"] == "SC-BASE"
        assert len(body["baseline"]["ca_mean"]) == 3
```

- [ ] **Step 7.3 — Verify E2E passes**

Run: `python -m pytest tests/test_e2e_p4.py -v --tb=short`
Expected: 5 passed (or skipped).

- [ ] **Step 7.4 — Final full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: all tests pass (P1 + P2 + P3 + P4).

- [ ] **Step 7.5 — Commit**

```bash
git add pyproject.toml tests/test_e2e_p4.py
git commit -m "test: add E2E test for P4 FastAPI backend"
```

---

## Summary of commits

| # | Message | Files |
|---|---|---|
| 0 | `chore: add httpx for FastAPI test client (P4)` | `requirements.txt` |
| 1 | `feat(api): pydantic request/response schemas — P4 Task 1` | `schemas.py`, tests |
| 2 | `feat(api): SHA-256 disk cache for Mesa runs — P4 Task 2` | `cache.py`, tests |
| 3 | `feat(api): FastAPI app + static endpoints — P4 Task 3` | `main.py`, `endpoints.py`, fixtures, tests |
| 4 | `feat(api): POST /simulate with cache — P4 Task 4` | `endpoints.py` (mod), tests |
| 5 | `feat(api): pre-warm 6 scenarios at startup — P4 Task 5` | `prewarm.py`, tests |
| 6 | `feat(cli): add serve subcommand for FastAPI — P4 Task 6` | `cli.py` (mod), tests |
| 7 | `test: add E2E test for P4 FastAPI backend` | `pyproject.toml`, `test_e2e_p4.py` |

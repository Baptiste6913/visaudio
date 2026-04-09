"""FastAPI route handlers — spec S9.1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.schemas import ScenarioInfo, SimulateRequest, SimulateResponse, Trajectory
from src.simulation.scenarios import SCENARIOS

router = APIRouter()
_data_dir: Path | None = None


def set_data_dir(path: Path) -> None:
    global _data_dir
    _data_dir = path


def _read_json(filename: str) -> dict:
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
        {"scenario_id": sc.scenario_id, "name": sc.name,
         "levier": sc.levier, "description": sc.description}
        for sc in SCENARIOS.values()
    ]


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(req: SimulateRequest) -> dict[str, Any]:
    """Run a simulation scenario (cache-first)."""
    from dataclasses import asdict

    import pandas as pd

    from src.api.cache import cache_key, read_cache, write_cache
    from src.simulation.runner import run_scenario

    cache_dir = _data_dir / "mesa_runs" if _data_dir else Path("data/processed/mesa_runs")
    key = cache_key(req.scenario_id, {
        "params": req.params, "n_steps": req.n_steps,
        "n_replications": req.n_replications,
    })

    cached = read_cache(key, cache_dir=cache_dir)
    if cached is not None:
        cached["from_cache"] = True
        return _build_response(cached, req)

    parquet_path = (
        _data_dir / "sales.parquet" if _data_dir
        else Path("data/processed/sales.parquet")
    )
    archetypes_path = (
        _data_dir / "archetypes.json" if _data_dir
        else Path("data/processed/archetypes.json")
    )

    if not parquet_path.exists():
        raise HTTPException(status_code=503, detail="sales.parquet not found")
    if not archetypes_path.exists():
        raise HTTPException(status_code=503, detail="archetypes.json not found")

    df = pd.read_parquet(parquet_path)
    arch = json.loads(archetypes_path.read_text(encoding="utf-8"))

    result = run_scenario(df, arch, req.scenario_id, req.n_steps, req.n_replications)
    baseline = (
        result if req.scenario_id == "SC-BASE"
        else run_scenario(df, arch, "SC-BASE", req.n_steps, req.n_replications)
    )

    result_dict = asdict(result)
    baseline_dict = asdict(baseline)
    delta_cumul = sum(result_dict["ca_mean"]) - sum(baseline_dict["ca_mean"])
    delta_low = sum(result_dict["ca_lower"]) - sum(baseline_dict["ca_upper"])
    delta_high = sum(result_dict["ca_upper"]) - sum(baseline_dict["ca_lower"])

    result_dict["_baseline"] = baseline_dict
    result_dict["_delta_cumul"] = delta_cumul
    result_dict["_delta_low"] = delta_low
    result_dict["_delta_high"] = delta_high

    write_cache(key, result_dict, cache_dir=cache_dir)
    return _build_response(result_dict, req, from_cache=False)


def _build_response(
    data: dict, req: SimulateRequest, from_cache: bool | None = None,
) -> dict:
    """Shape a raw result dict into the SimulateResponse schema."""
    baseline_data = data.get("_baseline", data)
    return {
        "scenario_id": data.get("scenario_id", req.scenario_id),
        "params": req.params,
        "baseline": {
            "months": baseline_data["months"],
            "ca_mean": baseline_data["ca_mean"],
            "ca_lower": baseline_data.get("ca_lower", baseline_data["ca_mean"]),
            "ca_upper": baseline_data.get("ca_upper", baseline_data["ca_mean"]),
        },
        "intervention": {
            "months": data["months"],
            "ca_mean": data["ca_mean"],
            "ca_lower": data.get("ca_lower", data["ca_mean"]),
            "ca_upper": data.get("ca_upper", data["ca_mean"]),
        },
        "delta_ca_cumul_36m": data.get("_delta_cumul", 0.0),
        "delta_ca_ci_low": data.get("_delta_low", 0.0),
        "delta_ca_ci_high": data.get("_delta_high", 0.0),
        "n_replications": data.get("n_replications", req.n_replications),
        "from_cache": (
            from_cache if from_cache is not None
            else data.get("from_cache", False)
        ),
    }

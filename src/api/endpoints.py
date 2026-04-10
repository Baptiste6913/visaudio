"""FastAPI route handlers — spec S9.1."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse

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

    # For SC-CUSTOM, build store_overrides from params
    if req.scenario_id == "SC-CUSTOM" and req.params:
        from src.simulation.scenarios import STORE_NAMES, ScenarioDef
        effort_val = float(req.params.get("effort", 1.0))
        price_val = float(req.params.get("price_mult", 1.0))
        target_archetypes = req.params.get("archetypes", list(range(10)))
        target_stores = req.params.get("stores", STORE_NAMES)

        effort_map = {int(a): effort_val for a in target_archetypes}
        price_map = {}
        if price_val != 1.0:
            for g in ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]:
                price_map[g] = price_val

        overrides = {
            s: {"effort_commercial_level": effort_map, "price_multipliers": price_map}
            for s in target_stores
        }
        from src.simulation.model import VisaudioModel
        from src.simulation.metrics import extract_monthly_metrics
        import numpy as np

        all_ca: list[list[float]] = []
        for rep in range(req.n_replications):
            model = VisaudioModel(df, arch, req.n_steps, seed=42 + rep, store_overrides=overrides)
            for _ in range(req.n_steps):
                model.step()
            metrics = extract_monthly_metrics(model.sales_log, req.n_steps)
            all_ca.append(metrics["ca_reseau"])
        ca_arr = np.array(all_ca)
        from dataclasses import asdict as _asdict
        from src.simulation.runner import RunResult
        result = RunResult(
            scenario_id="SC-CUSTOM", n_replications=req.n_replications,
            n_steps=req.n_steps, months=list(range(1, req.n_steps + 1)),
            ca_mean=np.mean(ca_arr, axis=0).round(2).tolist(),
            ca_lower=(np.mean(ca_arr, axis=0) - 1.96 * np.std(ca_arr, axis=0, ddof=1) / np.sqrt(req.n_replications)).round(2).tolist() if req.n_replications > 1 else np.mean(ca_arr, axis=0).round(2).tolist(),
            ca_upper=(np.mean(ca_arr, axis=0) + 1.96 * np.std(ca_arr, axis=0, ddof=1) / np.sqrt(req.n_replications)).round(2).tolist() if req.n_replications > 1 else np.mean(ca_arr, axis=0).round(2).tolist(),
            ca_par_magasin_mean={}, mix_gamme_mean={},
            panier_moyen_mean=[], n_transactions_mean=[],
        )
    else:
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


@router.post("/upload")
async def upload_excel(file: UploadFile) -> JSONResponse:
    """Accept an Excel file, run the full pipeline, return summary."""
    if _data_dir is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Le fichier doit être un .xlsx ou .xls")

    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        from src.ingestion.excel_parser import read_visaudio_excel
        from src.ingestion.normalization import normalize_dataframe, write_parquet
        from src.segmentation.pipeline import run_segmentation, write_archetypes_json
        from src.kpi.pipeline import write_kpis_json
        from src.rules.diagnostics import build_diagnostics_payload, write_diagnostics_json

        # 1. Ingest
        raw = read_visaudio_excel(tmp_path)
        df, rejected = normalize_dataframe(raw, return_rejected=True)
        parquet_path = _data_dir / "sales.parquet"
        write_parquet(df, parquet_path)

        # 2. Segment
        df_seg, arch_payload = run_segmentation(df, n_clusters=6)
        write_parquet(df_seg, parquet_path)
        write_archetypes_json(arch_payload, _data_dir / "archetypes.json")

        # 3. KPIs
        write_kpis_json(df_seg, _data_dir / "kpis.json")

        # 4. Diagnostics
        kpis = json.loads((_data_dir / "kpis.json").read_text(encoding="utf-8"))
        diag_payload = build_diagnostics_payload(kpis)
        write_diagnostics_json(diag_payload, _data_dir / "diagnostics.json")

        return JSONResponse(content={
            "status": "ok",
            "rows_imported": len(df),
            "rows_rejected": len(rejected),
            "clients": int(df["id_client"].nunique()),
            "archetypes": arch_payload["n_archetypes"],
            "message": f"Pipeline complet : {len(df)} lignes importées, "
                       f"{int(df['id_client'].nunique())} clients, "
                       f"{arch_payload['n_archetypes']} archétypes.",
        })
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erreur pipeline : {e}") from e
    finally:
        tmp_path.unlink(missing_ok=True)


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

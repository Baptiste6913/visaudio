"""Pre-warm standard Mesa scenarios at backend startup — P4 Task 5.

Reads sales.parquet and archetypes.json, then runs each of the 6 standard
scenarios (unless already cached) and writes results to the mesa_runs/ cache
directory.
"""
from __future__ import annotations

import json
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

    Reads sales.parquet and archetypes.json from *data_dir*.
    For each scenario, checks cache first (skip if hit).
    On miss: runs simulation, writes to data_dir/mesa_runs/.
    If parquet or archetypes missing, logs warning and returns.

    Args:
        data_dir: Directory containing sales.parquet and archetypes.json.
        n_steps: Number of simulation steps (months).
        n_replications: Number of independent replications per scenario.
    """
    parquet_path = data_dir / "sales.parquet"
    archetypes_path = data_dir / "archetypes.json"

    if not parquet_path.exists():
        logger.warning("sales.parquet not found in %s — skipping pre-warm", data_dir)
        return
    if not archetypes_path.exists():
        logger.warning("archetypes.json not found in %s — skipping pre-warm", data_dir)
        return

    sales_df = pd.read_parquet(parquet_path)
    archetypes_payload = json.loads(archetypes_path.read_text(encoding="utf-8"))

    cache_dir = data_dir / "mesa_runs"
    cache_dir.mkdir(parents=True, exist_ok=True)

    params = {"n_steps": n_steps, "n_replications": n_replications}

    for scenario_id in PREWARM_SCENARIOS:
        key = cache_key(scenario_id, params)

        if read_cache(key, cache_dir) is not None:
            logger.info("Cache hit for %s — skipping", scenario_id)
            continue

        logger.info("Running scenario %s (%d steps, %d reps)…", scenario_id, n_steps, n_replications)
        result = run_scenario(
            sales_df=sales_df,
            archetypes_payload=archetypes_payload,
            scenario_id=scenario_id,
            n_steps=n_steps,
            n_replications=n_replications,
        )
        write_cache(key, asdict(result), cache_dir)
        logger.info("Cached %s → %s", scenario_id, key[:12])

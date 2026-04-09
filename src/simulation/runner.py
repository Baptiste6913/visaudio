"""Batch runner — runs N replications of a scenario and aggregates results.

Each replication uses a different seed (base_seed + rep_index) for
stochastic independence.  Results include per-step means and 95% CI
for the network CA.

P3 Task 7.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.simulation.metrics import extract_monthly_metrics
from src.simulation.model import VisaudioModel
from src.simulation.scenarios import get_scenario

Z_95 = 1.96


@dataclass
class RunResult:
    """Aggregated output of N replications for a single scenario."""

    scenario_id: str
    n_replications: int
    n_steps: int
    months: list[int]
    ca_mean: list[float]
    ca_lower: list[float]
    ca_upper: list[float]
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
    """Run N replications of a scenario and aggregate metrics.

    Each replication uses ``seed = base_seed + rep_index`` to ensure
    stochastic independence while remaining fully reproducible.

    Args:
        sales_df: Historical sales DataFrame.
        archetypes_payload: Archetypes dict (as loaded from JSON).
        scenario_id: Registered scenario identifier (e.g. ``"SC-BASE"``).
        n_steps: Number of simulation steps (months).
        n_replications: Number of independent replications.
        seed: Base random seed.

    Returns:
        RunResult with aggregated metrics across replications.
    """
    scenario = get_scenario(scenario_id)
    store_overrides = scenario.store_overrides or None

    # Collect per-replication metrics
    all_ca: list[list[float]] = []
    all_ca_par_magasin: list[dict[str, list[float]]] = []
    all_mix_gamme: list[dict[str, list[float]]] = []
    all_panier: list[list[float]] = []
    all_n_tx: list[list[float]] = []

    for rep in range(n_replications):
        model = VisaudioModel(
            sales_df=sales_df,
            archetypes_payload=archetypes_payload,
            n_steps=n_steps,
            seed=seed + rep,
            store_overrides=store_overrides,
        )
        for _ in range(n_steps):
            model.step()

        metrics = extract_monthly_metrics(model.sales_log, n_steps)
        all_ca.append(metrics["ca_reseau"])
        all_ca_par_magasin.append(metrics["ca_par_magasin"])
        all_mix_gamme.append(metrics["mix_gamme_reseau"])
        all_panier.append(metrics["panier_moyen"])
        all_n_tx.append([float(x) for x in metrics["n_transactions"]])

    # --- Aggregate CA with confidence interval ---
    ca_array = np.array(all_ca, dtype=np.float64)  # (n_reps, n_steps)
    ca_mean = np.mean(ca_array, axis=0)

    if n_replications > 1:
        ca_std = np.std(ca_array, axis=0, ddof=1)
    else:
        ca_std = np.zeros(n_steps, dtype=np.float64)

    margin = Z_95 * ca_std / math.sqrt(n_replications)
    ca_lower = ca_mean - margin
    ca_upper = ca_mean + margin

    # --- Aggregate per-store CA (means only) ---
    all_stores: set[str] = set()
    for d in all_ca_par_magasin:
        all_stores.update(d.keys())

    ca_par_magasin_mean: dict[str, list[float]] = {}
    for store in sorted(all_stores):
        store_arrays = []
        for d in all_ca_par_magasin:
            if store in d:
                store_arrays.append(d[store])
            else:
                store_arrays.append([0.0] * n_steps)
        arr = np.array(store_arrays, dtype=np.float64)
        ca_par_magasin_mean[store] = np.mean(arr, axis=0).tolist()

    # --- Aggregate mix gamme (means only) ---
    all_gammes: set[str] = set()
    for d in all_mix_gamme:
        all_gammes.update(d.keys())

    mix_gamme_mean: dict[str, list[float]] = {}
    for gamme in sorted(all_gammes):
        gamme_arrays = []
        for d in all_mix_gamme:
            if gamme in d:
                gamme_arrays.append(d[gamme])
            else:
                gamme_arrays.append([0.0] * n_steps)
        arr = np.array(gamme_arrays, dtype=np.float64)
        mix_gamme_mean[gamme] = np.mean(arr, axis=0).tolist()

    # --- Aggregate panier moyen and n_transactions (means only) ---
    panier_array = np.array(all_panier, dtype=np.float64)
    panier_moyen_mean = np.mean(panier_array, axis=0).tolist()

    n_tx_array = np.array(all_n_tx, dtype=np.float64)
    n_transactions_mean = np.mean(n_tx_array, axis=0).tolist()

    return RunResult(
        scenario_id=scenario_id,
        n_replications=n_replications,
        n_steps=n_steps,
        months=list(range(1, n_steps + 1)),
        ca_mean=ca_mean.tolist(),
        ca_lower=ca_lower.tolist(),
        ca_upper=ca_upper.tolist(),
        ca_par_magasin_mean=ca_par_magasin_mean,
        mix_gamme_mean=mix_gamme_mean,
        panier_moyen_mean=panier_moyen_mean,
        n_transactions_mean=n_transactions_mean,
    )


def write_run_result(result: RunResult, path: Path) -> None:
    """Serialize a RunResult to JSON.

    Args:
        result: The aggregated run result to persist.
        path: Destination file path (parent dirs created if needed).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(result)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

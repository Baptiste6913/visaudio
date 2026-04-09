"""Calibration utilities for simulation back-testing.

Provides pure comparison functions (split_train_test, compute_tolerance_report)
and a backtest_baseline() wrapper that lazily imports the simulation runner.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class StoreResult:
    """Comparison result for a single store."""

    store: str
    actual: float
    simulated: float
    pct_error: float
    within_tolerance: bool


@dataclass
class ToleranceReport:
    """Aggregated comparison across all stores."""

    store_results: list[StoreResult]
    all_within_tolerance: bool


# ---------------------------------------------------------------------------
# Pure comparison helpers
# ---------------------------------------------------------------------------

def split_train_test(
    df: pd.DataFrame,
    train_end_year: int = 2024,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by year: train = years <= *train_end_year*, test = years > it."""
    years = df["date_facture"].dt.year
    train_mask = years <= train_end_year
    return df.loc[train_mask].copy(), df.loc[~train_mask].copy()


def compute_tolerance_report(
    actual_ca_by_store: dict[str, float],
    simulated_ca_by_store: dict[str, float],
    tolerance_pct: float = 5.0,
) -> ToleranceReport:
    """Compare actual vs simulated CA per store.

    For each store present in *actual_ca_by_store*, compute the percentage
    error and check whether ``|error| <= tolerance_pct``.

    When actual is zero, a simulated value of zero is considered within
    tolerance (0 % error); any non-zero simulated value yields 100 % error.
    """
    results: list[StoreResult] = []

    for store, actual in actual_ca_by_store.items():
        simulated = simulated_ca_by_store.get(store, 0.0)

        if actual == 0.0:
            pct_error = 0.0 if simulated == 0.0 else 100.0
        else:
            pct_error = abs(simulated - actual) / abs(actual) * 100.0

        within = pct_error <= tolerance_pct

        results.append(
            StoreResult(
                store=store,
                actual=actual,
                simulated=simulated,
                pct_error=round(pct_error, 2),
                within_tolerance=within,
            )
        )

    all_ok = all(r.within_tolerance for r in results)
    return ToleranceReport(store_results=results, all_within_tolerance=all_ok)


# ---------------------------------------------------------------------------
# Back-test wrapper (depends on runner — lazy import)
# ---------------------------------------------------------------------------

def backtest_baseline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    archetypes_payload: dict,
    n_replications: int = 10,
    seed: int = 42,
) -> ToleranceReport:
    """Run baseline scenario on *train_df*, compare with *test_df* actual CA.

    The runner is imported lazily so that the pure comparison functions above
    remain usable even when the full simulation stack is not available.
    """
    from src.simulation.runner import run_scenario  # noqa: WPS433

    # Actual CA from the test period, grouped by store (ville).
    actual_ca: dict[str, float] = (
        test_df.groupby("ville", observed=True)["ca_ht_article"]
        .sum()
        .to_dict()
    )

    # Run the baseline scenario on training data.
    result = run_scenario(
        sales_df=train_df,
        archetypes_payload=archetypes_payload,
        scenario_id="baseline",
        n_steps=12,
        n_replications=n_replications,
        seed=seed,
    )

    # Extract mean simulated CA per store (sum of monthly means).
    simulated_ca: dict[str, float] = {
        store: sum(monthly_values)
        for store, monthly_values in result.ca_par_magasin_mean.items()
    }

    return compute_tolerance_report(actual_ca, simulated_ca)

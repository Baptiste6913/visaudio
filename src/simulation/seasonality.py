"""Compute monthly seasonality coefficients from historical sales."""
from __future__ import annotations

import pandas as pd

FLOOR = 0.1


def compute_seasonality(
    df: pd.DataFrame,
    date_col: str = "date_facture",
    ca_col: str = "ca_ht_article",
) -> dict[int, float]:
    """Return {month_int: coefficient} where mean(coefficients) ~ 1.0.

    Args:
        df: sales DataFrame with date_facture and ca_ht_article.
        date_col: column name for the date.
        ca_col: column name for the revenue.

    Returns:
        Dict mapping month number (1-12) to a multiplicative coefficient.
    """
    monthly_ca = df.groupby(df[date_col].dt.month)[ca_col].sum()

    all_months = pd.Series(0.0, index=range(1, 13))
    for m, v in monthly_ca.items():
        all_months[m] = float(v)

    raw_mean = all_months.mean()
    if raw_mean == 0:
        return {m: 1.0 for m in range(1, 13)}

    coefficients = all_months / raw_mean
    # Iterate clip + normalize until floor holds after normalization
    for _ in range(5):
        coefficients = coefficients.clip(lower=FLOOR)
        coefficients = coefficients / coefficients.mean()
    return {int(m): round(float(v), 4) for m, v in coefficients.items()}

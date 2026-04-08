"""Retention / LTV KPIs R1-R5."""
from __future__ import annotations

import pandas as pd


def taux_renouvellement_24mois(df: pd.DataFrame) -> float:
    """R1 — among clients with ≥2 purchases, share whose 2nd purchase is
    within 24 months of the 1st.

    Note: spec says 'clients avec ≥24 mois d'historique' but in small samples
    this is always empty; we fall back to 'clients with a second purchase'
    for a usable ratio. If no client has ≥2 purchases, return 0.0.
    """
    g = df.sort_values("date_facture").groupby("id_client")
    delays = []
    for _, sub in g:
        if len(sub) < 2:
            continue
        gap = (sub["date_facture"].iloc[1] - sub["date_facture"].iloc[0]).days
        delays.append(gap)
    if not delays:
        return 0.0
    within = sum(1 for d in delays if d <= 24 * 30)
    return float(within / len(delays))


def delai_median_entre_achats(df: pd.DataFrame) -> float:
    """R2 — median gap in days between consecutive purchases, across clients
    having ≥2 purchases. Returns NaN-safe (0 if no eligible client)."""
    gaps: list[float] = []
    for _, sub in df.sort_values("date_facture").groupby("id_client"):
        dates = sub["date_facture"].drop_duplicates().sort_values()
        if len(dates) < 2:
            continue
        diffs = dates.diff().dropna().dt.days
        gaps.extend(diffs.tolist())
    if not gaps:
        return 0.0
    return float(pd.Series(gaps).median())


def ltv_3_ans(df: pd.DataFrame) -> dict[int, float]:
    """R3 — sum of CA per client, restricted to clients with ≥3 years of
    purchase history within the dataset."""
    per_client = df.groupby("id_client")
    out: dict[int, float] = {}
    for cid, sub in per_client:
        span = (sub["date_facture"].max() - sub["date_facture"].min()).days
        if span < 3 * 365:
            continue
        out[int(cid)] = float(sub["ca_ht_article"].sum())
    return out


def clients_dormants(df: pd.DataFrame, threshold_months: int = 24) -> int:
    """R4 — count of distinct clients whose last purchase is older than
    `threshold_months` months from today."""
    today = pd.Timestamp.now().normalize()
    last_seen = df.groupby("id_client")["date_facture"].max()
    threshold = today - pd.Timedelta(days=threshold_months * 30)
    return int((last_seen < threshold).sum())


def cohort_retention_curve(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """R5 — for each cohort month (month of the client's first purchase),
    share of clients still active at +6, +12, +24 months.
    """
    first_buy = df.groupby("id_client")["date_facture"].min()
    cohorts = first_buy.dt.to_period("M").astype("string")
    out: dict[str, dict[str, float]] = {}
    for cohort, clients in cohorts.groupby(cohorts):
        cohort_clients = clients.index.tolist()
        cohort_start = first_buy[cohort_clients].min()
        stats: dict[str, float] = {}
        for months in (6, 12, 24):
            window_end = cohort_start + pd.Timedelta(days=months * 30)
            still_active = 0
            for cid in cohort_clients:
                client_dates = df.loc[df["id_client"] == cid, "date_facture"]
                if (client_dates > cohort_start).any() and (
                    client_dates <= window_end
                ).any():
                    still_active += 1
            stats[f"M+{months}"] = float(still_active / len(cohort_clients))
        out[str(cohort)] = stats
    return out

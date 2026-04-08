"""Diagnostic signal KPIs X1-X5. Consumed by the rules engine in P2."""
from __future__ import annotations

import pandas as pd


def index_saisonnalite_par_magasin(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """X1 — per ville, per month, CA index relative to the ville's yearly mean.
    Output: {ville: {month(YYYY-MM): index}}.
    """
    df = df.copy()
    df["month_ym"] = df["date_facture"].dt.to_period("M").astype("string")
    per = df.groupby(["ville", "month_ym"], observed=True)["ca_ht_article"].sum()
    out: dict[str, dict[str, float]] = {}
    for ville, sub in per.groupby(level=0, observed=True):
        mean = sub.mean()
        if mean == 0:
            continue
        out[str(ville)] = {str(k[1]): float(v / mean) for k, v in sub.items()}
    return out


def part_clients_60_plus(df: pd.DataFrame) -> float:
    """X2 — share of distinct clients aged ≥ 60 at their latest purchase."""
    per_client = df.sort_values("date_facture").drop_duplicates(
        "id_client", keep="last"
    )
    if len(per_client) == 0:
        return 0.0
    return float((per_client["age_client"] >= 60).mean())


def ratio_monture_verre_eur(df: pd.DataFrame) -> dict[str, float]:
    """X3 — CA monture / CA verre per ville (0.0 if verre is missing)."""
    monture = df[df["famille_article"] == "OPT_MONTURE"].groupby(
        "ville", observed=True
    )["ca_ht_article"].sum()
    verre = df[df["famille_article"] == "OPT_VERRE"].groupby(
        "ville", observed=True
    )["ca_ht_article"].sum()
    out: dict[str, float] = {}
    for ville in verre.index:
        m = float(monture.get(ville, 0.0))
        v = float(verre.loc[ville])
        out[str(ville)] = m / v if v > 0 else 0.0
    return out


def ecart_type_mix_intra_magasin(df: pd.DataFrame) -> dict[str, float]:
    """X4 — for each ville, std dev of the verre-CA shares across the 4 gammes.
    A lower stdev means more uniform distribution; higher means concentration.
    """
    verres = df[df["est_verre"]]
    if verres.empty:
        return {}
    shares = verres.groupby(["ville", "gamme_verre_visaudio"], observed=True)[
        "ca_ht_article"
    ].sum()
    totals = verres.groupby("ville", observed=True)["ca_ht_article"].sum()
    out: dict[str, float] = {}
    for ville in totals.index:
        s = shares.xs(ville, level=0) / totals.loc[ville]
        out[str(ville)] = float(s.std(ddof=0))
    return out


def part_factures_une_paire(df: pd.DataFrame) -> float:
    """X5 — share of factures with only 1 distinct rang_paire value."""
    paires = df.groupby("id_facture_rang")["rang_paire"].nunique()
    if len(paires) == 0:
        return 0.0
    return float((paires == 1).mean())

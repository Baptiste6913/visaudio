"""Benchmark inter-stores KPIs B1-B4."""
from __future__ import annotations

import pandas as pd

from src.kpi.cadrage import ca_par_magasin, panier_moyen_par_magasin


def classement_magasins(df: pd.DataFrame) -> dict[str, int]:
    """B1 — rank villes by total CA (1 = best)."""
    ca = pd.Series(ca_par_magasin(df))
    ranks = ca.rank(ascending=False, method="min").astype(int)
    return {k: int(v) for k, v in ranks.items()}


def decomposition_ca(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """B2 — CA = n_factures × panier_moyen per ville."""
    ca = ca_par_magasin(df)
    panier = panier_moyen_par_magasin(df)
    n = (
        df.groupby("ville", observed=True)["id_facture_rang"]
        .nunique()
        .to_dict()
    )
    return {
        v: {
            "ca_total": float(ca[v]),
            "n_factures": int(n[v]),
            "panier_moyen": float(panier[v]),
        }
        for v in ca
    }


def ecart_mediane_reseau(
    df: pd.DataFrame, metric: str = "ca_par_magasin"
) -> dict[str, float]:
    """B3 — relative gap to the network median for a given metric.

    Only `ca_par_magasin` is supported in P1; other metrics in later plans.
    """
    if metric != "ca_par_magasin":
        raise NotImplementedError(f"metric={metric!r} not supported in P1")
    ca = pd.Series(ca_par_magasin(df))
    if ca.empty:
        return {}
    median = ca.median()
    if median == 0 or pd.isna(median):
        return {k: 0.0 for k in ca.index}
    return {k: float((v - median) / median) for k, v in ca.items()}


def contrefactuel_best_practice(
    df: pd.DataFrame,
    source_ville: str,
    target_ville: str,
) -> dict[str, float]:
    """B4 — what would target_ville's verre CA be if it had source_ville's
    mean verre ticket, keeping the same number of verre sales?
    """
    verres = df[df["est_verre"]]
    mean_source = verres[verres["ville"] == source_ville]["ca_ht_article"].mean()
    target = verres[verres["ville"] == target_ville]
    current_ca = float(target["ca_ht_article"].sum())
    n_sales = len(target)
    projected_ca = float(mean_source * n_sales)
    return {
        "current_ca_verre": current_ca,
        "projected_ca_verre": projected_ca,
        "delta_ca_verre": projected_ca - current_ca,
    }

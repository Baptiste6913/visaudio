"""Cadrage (top-line) KPIs C1-C8.

Each function takes a DataFrame and returns a primitive or a dict.
Pure — no I/O.
"""
from __future__ import annotations

import pandas as pd


def ca_total(df: pd.DataFrame) -> float:
    """C1 — total CA HT across all rows."""
    return float(df["ca_ht_article"].sum())


def ca_par_famille(df: pd.DataFrame) -> dict[str, float]:
    """C2 — CA HT grouped by famille_article."""
    s = df.groupby("famille_article", observed=True)["ca_ht_article"].sum()
    return {str(k): float(v) for k, v in s.items()}


def ca_par_magasin(df: pd.DataFrame) -> dict[str, float]:
    """C3 — CA HT grouped by ville."""
    s = df.groupby("ville", observed=True)["ca_ht_article"].sum()
    return {str(k): float(v) for k, v in s.items()}


def panier_moyen_reseau(df: pd.DataFrame) -> float:
    """C4 — mean of invoice totals (sum of ca per id_facture_rang)."""
    per_facture = df.groupby("id_facture_rang")["ca_ht_article"].sum()
    return float(per_facture.mean())


def panier_moyen_par_magasin(df: pd.DataFrame) -> dict[str, float]:
    """C5 — mean invoice total per ville."""
    per = (
        df.groupby(["ville", "id_facture_rang"], observed=True)["ca_ht_article"]
        .sum()
        .groupby("ville", observed=True)
        .mean()
    )
    return {str(k): float(v) for k, v in per.items()}


def clients_uniques(df: pd.DataFrame) -> int:
    """C6 — number of distinct clients."""
    return int(df["id_client"].nunique())


def taux_nouveaux_vs_renouv(df: pd.DataFrame) -> dict[str, float]:
    """C7 — share of nouveaux vs renouvellement, counted on distinct clients.

    A client's status is taken from its first row (arbitrary but consistent).
    """
    first_rows = df.drop_duplicates("id_client")
    counts = first_rows["statut_client"].value_counts(normalize=True, dropna=True)
    return {str(k): float(v) for k, v in counts.items()}


def ca_par_mois(df: pd.DataFrame) -> dict[str, float]:
    """C8 — CA HT grouped by month (YYYY-MM)."""
    idx = df["date_facture"].dt.to_period("M").astype("string")
    s = df.groupby(idx)["ca_ht_article"].sum().sort_index()
    return {str(k): float(v) for k, v in s.items()}

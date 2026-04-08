"""Conventionnement dependency KPIs D1-D4."""
from __future__ import annotations

import pandas as pd


def part_ca_par_conv(df: pd.DataFrame) -> dict[str, float]:
    """D1 — share of total CA per conventionnement."""
    total = df["ca_ht_article"].sum()
    if total == 0:
        return {}
    s = df.groupby("conventionnement", observed=True)["ca_ht_article"].sum() / total
    return {str(k): float(v) for k, v in s.items()}


def panier_moyen_par_conv(df: pd.DataFrame) -> dict[str, float]:
    """D2 — mean invoice total per conventionnement."""
    per = (
        df.groupby(["conventionnement", "id_facture_rang"], observed=True)[
            "ca_ht_article"
        ]
        .sum()
        .groupby("conventionnement", observed=True)
        .mean()
    )
    return {str(k): float(v) for k, v in per.items()}


def hhi_conventionnement(df: pd.DataFrame) -> float:
    """D3 — Herfindahl-Hirschman Index on conventionnement shares (×10000)."""
    shares = pd.Series(part_ca_par_conv(df))
    return float((shares ** 2).sum() * 10000)


def exposition_top3(df: pd.DataFrame) -> float:
    """D4 — share of CA from the top 3 conventionnements."""
    shares = pd.Series(part_ca_par_conv(df)).sort_values(ascending=False)
    return float(shares.head(3).sum())

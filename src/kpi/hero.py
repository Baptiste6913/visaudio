"""Hero KPIs H1-H10 for the upsell growth narrative.

H5 (opportunite_upsell_annuelle) is the star — see Task 7 for its detailed
implementation and tests.
"""
from __future__ import annotations

import pandas as pd


# ------------- H1 -------------
def mix_gamme_par_magasin(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """H1 — share of verre CA by gamme, per ville."""
    verres = df[df["est_verre"]]
    out: dict[str, dict[str, float]] = {}
    for ville, group in verres.groupby("ville", observed=True):
        total = group["ca_ht_article"].sum()
        if total == 0:
            continue
        by_gamme = group.groupby("gamme_verre_visaudio", observed=True)[
            "ca_ht_article"
        ].sum()
        out[str(ville)] = {str(g): float(ca / total) for g, ca in by_gamme.items()}
    return out


# ------------- H2 -------------
def mix_gamme_par_segment(
    df: pd.DataFrame, segment_col: str
) -> dict[str, dict[str, float]]:
    """H2 — share of verre CA by gamme, per segment."""
    verres = df[df["est_verre"]]
    ca_par_gamme = verres.groupby(
        [segment_col, "gamme_verre_visaudio"], observed=True
    )["ca_ht_article"].sum()
    ca_total_seg = verres.groupby(segment_col, observed=True)["ca_ht_article"].sum()
    out: dict[str, dict[str, float]] = {}
    for (seg, gamme), ca in ca_par_gamme.items():
        if ca_total_seg.loc[seg] == 0:
            continue
        out.setdefault(str(seg), {})[str(gamme)] = float(ca / ca_total_seg.loc[seg])
    return out


# ------------- H3 -------------
def panier_moyen_verre_par_segment(
    df: pd.DataFrame, segment_col: str
) -> dict[str, float]:
    """H3 — mean ticket on verre rows, per segment."""
    verres = df[df["est_verre"]]
    s = verres.groupby(segment_col, observed=True)["ca_ht_article"].mean()
    return {str(k): float(v) for k, v in s.items()}


# ------------- H4 -------------
def panier_moyen_verre_par_segment_top_q75(
    df: pd.DataFrame, segment_col: str
) -> dict[str, float]:
    """H4 — Q75 across villes of the mean verre ticket per (segment, ville)."""
    verres = df[df["est_verre"]]
    per = verres.groupby([segment_col, "ville"], observed=True)["ca_ht_article"].mean()
    q75 = per.groupby(level=0, observed=True).quantile(0.75)
    return {str(k): float(v) for k, v in q75.items()}


# ------------- H7 -------------
def taux_cross_sell_verre_monture(df: pd.DataFrame) -> float:
    """H7 — share of factures containing both a verre and a monture."""
    fam = df["famille_article"].astype(str)
    per_facture = fam.groupby(df["id_facture_rang"]).agg(set)
    both = per_facture.apply(
        lambda s: "OPT_VERRE" in s and "OPT_MONTURE" in s
    )
    has_verre = per_facture.apply(lambda s: "OPT_VERRE" in s)
    if not has_verre.any():
        return 0.0
    return float(both.sum() / has_verre.sum())


# ------------- H8 -------------
def taux_upgrade_renouvellement(df: pd.DataFrame) -> float:
    """H8 — among clients in renouvellement with ≥2 verre invoices, share whose
    latest-purchase gamme is strictly higher than the previous one (ordered
    categorical).
    """
    verre = df[df["est_verre"] & (df["statut_client"] == "Renouvellement")]
    # Keep one row per (client, facture) = the first verre row of that facture
    per_facture = verre.sort_values("date_facture").drop_duplicates(
        ["id_client", "id_facture_rang"]
    )
    upgrades = 0
    eligible = 0
    for client_id, group in per_facture.groupby("id_client", observed=True):
        if len(group) < 2:
            continue
        eligible += 1
        sorted_g = group.sort_values("date_facture")
        first_gamme = sorted_g["gamme_verre_visaudio"].iloc[-2]
        second_gamme = sorted_g["gamme_verre_visaudio"].iloc[-1]
        if pd.isna(first_gamme) or pd.isna(second_gamme):
            continue
        if second_gamme > first_gamme:  # ordered categorical
            upgrades += 1
    if eligible == 0:
        return 0.0
    return float(upgrades / eligible)


# ------------- H9 -------------
def part_premium_plus_par_magasin(df: pd.DataFrame) -> dict[str, float]:
    """H9 — share of (PREMIUM + PRESTIGE) in verre CA per ville."""
    verres = df[df["est_verre"]]
    num = verres[verres["est_premium_plus"]].groupby("ville", observed=True)[
        "ca_ht_article"
    ].sum()
    den = verres.groupby("ville", observed=True)["ca_ht_article"].sum()
    out = (num / den).fillna(0.0)
    return {str(k): float(v) for k, v in out.items()}


# ------------- H10 -------------
def ecart_au_top_du_reseau(df: pd.DataFrame) -> dict[str, float]:
    """H10 — H9(ville) - max(H9 over all villes). Always ≤ 0."""
    shares = part_premium_plus_par_magasin(df)
    if not shares:
        return {}
    top = max(shares.values())
    return {k: float(v - top) for k, v in shares.items()}

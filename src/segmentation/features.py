"""Per-client feature vector construction for K-Means segmentation.

Takes a normalized sales DataFrame (one row per article line) and returns
a client-level DataFrame (one row per id_client) with the 9 features
listed in spec §6.1 plus one-hot encoding of sex.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


FEATURE_NAMES: tuple[str, ...] = (
    "age_dernier_achat",
    "panier_moyen",
    "n_achats_totaux",
    "mois_entre_achats",
    "part_premium_plus",
    "ratio_monture_verre",
    "conventionnement_libre",
    "sexe_Femme",
    "sexe_Homme",
)


def build_client_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the sales DataFrame to a per-client feature matrix.

    Args:
        df: normalized sales DataFrame with columns from P1 schema plus
            derived columns (est_verre, est_premium_plus, age_client).

    Returns:
        A DataFrame indexed by id_client with the columns in FEATURE_NAMES.
        All values are numeric (float64 or int).
    """
    groups = df.groupby("id_client", sort=True)

    # age_dernier_achat: age at the latest purchase of each client
    age = groups.apply(
        lambda g: g.sort_values("date_facture")["age_client"].iloc[-1],
        include_groups=False,
    ).astype("float64")

    # panier_moyen: mean CA per row across all the client's rows
    panier = groups["ca_ht_article"].mean().astype("float64")

    # n_achats_totaux: number of distinct invoices (id_facture_rang)
    n_achats = groups["id_facture_rang"].nunique().astype("float64")

    # mois_entre_achats: median gap in months between consecutive distinct
    # purchase dates. Single-purchase clients get 0.
    def _gap_months(g: pd.DataFrame) -> float:
        dates = g["date_facture"].drop_duplicates().sort_values()
        if len(dates) < 2:
            return 0.0
        diffs_days = dates.diff().dropna().dt.days
        return float(diffs_days.median() / 30.0)

    mois = groups.apply(_gap_months, include_groups=False).astype("float64")

    # part_premium_plus: share of verre rows that are PREMIUM or PRESTIGE
    def _part_premium(g: pd.DataFrame) -> float:
        verres = g[g["est_verre"]]
        if len(verres) == 0:
            return 0.0
        return float(verres["est_premium_plus"].mean())

    part_premium = groups.apply(_part_premium, include_groups=False).astype("float64")

    # ratio_monture_verre: €CA monture / €CA verre
    def _ratio(g: pd.DataFrame) -> float:
        monture = g.loc[g["famille_article"] == "OPT_MONTURE", "ca_ht_article"].sum()
        verre = g.loc[g["famille_article"] == "OPT_VERRE", "ca_ht_article"].sum()
        if verre == 0:
            return 0.0
        return float(monture / verre)

    ratio = groups.apply(_ratio, include_groups=False).astype("float64")

    # conventionnement_libre: share of the client's rows that are LIBRE
    def _conv_libre(g: pd.DataFrame) -> float:
        return float((g["conventionnement"] == "LIBRE").mean())

    conv_libre = groups.apply(_conv_libre, include_groups=False).astype("float64")

    # sexe_Femme / sexe_Homme: one-hot of the client's (constant) sex
    def _first_sex(g: pd.DataFrame) -> str:
        return str(g["sexe"].iloc[0])

    sex = groups.apply(_first_sex, include_groups=False)
    sex_femme = (sex == "Femme").astype("float64")
    sex_homme = (sex == "Homme").astype("float64")

    feats = pd.DataFrame(
        {
            "age_dernier_achat": age,
            "panier_moyen": panier,
            "n_achats_totaux": n_achats,
            "mois_entre_achats": mois,
            "part_premium_plus": part_premium,
            "ratio_monture_verre": ratio,
            "conventionnement_libre": conv_libre,
            "sexe_Femme": sex_femme,
            "sexe_Homme": sex_homme,
        }
    )
    feats.index.name = "id_client"
    return feats

"""Shared fixtures for segmentation tests.

synthetic_sales: a 30-row dataset with 5 clients, each with 3-8 rows,
enough to exercise feature aggregation and K-Means.
"""
from __future__ import annotations

import pandas as pd
import pytest
from pandas.api.types import CategoricalDtype


GAMME_ORDER = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


def _row(**k):
    base = dict(
        implantation="CENTRE-VILLE",
        secteur_economique="Tertiaire",
        gamme_verre_fournisseur=None,
        libelle_produit="x",
        nom_marque="ESS",
        categorie_geom_verre=None,
        rang_paire=1,
        qte_article=1,
        mois_facture="2024-01",
        annee_facture=2024,
    )
    base.update(k)
    return base


@pytest.fixture
def synthetic_sales() -> pd.DataFrame:
    """5 clients × varied histories spanning multiple families and gammes."""
    rows = []
    # Client 1 — 60+, premium buyer, LIBRE, 3 factures, strong cross-sell
    for i, (fid, gamme, ca, fam) in enumerate([
        ("F1|1", "PREMIUM", 220.0, "OPT_VERRE"),
        ("F1|1", None,      110.0, "OPT_MONTURE"),
        ("F2|1", "PRESTIGE", 300.0, "OPT_VERRE"),
        ("F2|1", None,       130.0, "OPT_MONTURE"),
        ("F3|1", "PRESTIGE", 320.0, "OPT_VERRE"),
    ]):
        rows.append(_row(
            id_client=1, ville="Avranches", id_facture_rang=fid,
            date_facture=pd.Timestamp("2024-01-10") + pd.Timedelta(days=100 * i),
            famille_article=fam, gamme_verre_visaudio=gamme, ca_ht_article=ca,
            conventionnement="LIBRE", age_client=62, tranche_age="60-75",
            sexe="Femme", statut_client="Renouvellement",
        ))
    # Client 2 — 30s, ESSENTIEL, CSS, 1 facture, no cross-sell
    rows.append(_row(
        id_client=2, ville="Cherbourg-en-Cotentin", id_facture_rang="F4|1",
        date_facture=pd.Timestamp("2024-03-15"),
        famille_article="OPT_VERRE", gamme_verre_visaudio="ESSENTIEL",
        ca_ht_article=95.0, conventionnement="CSS",
        age_client=34, tranche_age="30-45", sexe="Homme", statut_client="Nouveau client",
    ))
    # Client 3 — 50s, CONFORT, LIBRE, 2 factures, with cross-sell
    for i, (fid, gamme, ca, fam) in enumerate([
        ("F5|1", "CONFORT", 170.0, "OPT_VERRE"),
        ("F5|1", None,       90.0, "OPT_MONTURE"),
        ("F6|1", "CONFORT", 180.0, "OPT_VERRE"),
        ("F6|1", None,       95.0, "OPT_MONTURE"),
    ]):
        rows.append(_row(
            id_client=3, ville="Rampan", id_facture_rang=fid,
            date_facture=pd.Timestamp("2024-02-05") + pd.Timedelta(days=200 * (i // 2)),
            famille_article=fam, gamme_verre_visaudio=gamme, ca_ht_article=ca,
            conventionnement="LIBRE", age_client=54, tranche_age="45-60",
            sexe="Femme", statut_client="Renouvellement",
        ))
    # Client 4 — 70+, PREMIUM, KALIXIA, 1 facture
    rows.append(_row(
        id_client=4, ville="Yquelon", id_facture_rang="F7|1",
        date_facture=pd.Timestamp("2024-05-10"),
        famille_article="OPT_VERRE", gamme_verre_visaudio="PREMIUM",
        ca_ht_article=250.0, conventionnement="KALIXIA",
        age_client=73, tranche_age="60-75", sexe="Homme", statut_client="Nouveau client",
    ))
    # Client 5 — 20s, solaire only, LIBRE, 1 facture
    rows.append(_row(
        id_client=5, ville="Avranches", id_facture_rang="F8|1",
        date_facture=pd.Timestamp("2024-07-01"),
        famille_article="OPT_SOLAIRE", gamme_verre_visaudio=None,
        ca_ht_article=80.0, conventionnement="LIBRE",
        age_client=25, tranche_age="<30", sexe="Femme", statut_client="Nouveau client",
    ))
    df = pd.DataFrame(rows)
    df["famille_article"] = df["famille_article"].astype("category")
    df["ville"] = df["ville"].astype("category")
    df["conventionnement"] = df["conventionnement"].astype("category")
    df["gamme_verre_visaudio"] = df["gamme_verre_visaudio"].astype(
        CategoricalDtype(categories=GAMME_ORDER, ordered=True)
    )
    df["tranche_age"] = df["tranche_age"].astype("category")
    df["sexe"] = df["sexe"].astype("category")
    df["statut_client"] = df["statut_client"].astype("category")
    df["est_verre"] = df["famille_article"] == "OPT_VERRE"
    df["est_premium_plus"] = df["gamme_verre_visaudio"].isin(["PREMIUM", "PRESTIGE"])
    return df

"""Shared fixtures for simulation tests.

Provides a minimal archetypes_payload (3 archetypes) and a mini_sales
DataFrame (30 rows, 10 clients, 3 stores) with segment_id column.
"""
from __future__ import annotations

import pandas as pd
import pytest
from pandas.api.types import CategoricalDtype

GAMME_ORDER = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]
STORES = ["Avranches", "Cherbourg-en-Cotentin", "Rampan"]


@pytest.fixture
def archetypes_payload() -> dict:
    """3 archetypes with realistic centroids."""
    return {
        "generated_at": "2026-04-09T00:00:00+00:00",
        "n_archetypes": 3,
        "archetypes": [
            {
                "id": 0,
                "label": "45-60 premium mixte NON-LIBRE",
                "n_clients": 200,
                "share_of_clients": 0.20,
                "share_of_ca": 0.35,
                "centroid": {
                    "age_dernier_achat": 52.0,
                    "panier_moyen": 225.0,
                    "n_achats_totaux": 2.5,
                    "mois_entre_achats": 14.0,
                    "part_premium_plus": 0.65,
                    "ratio_monture_verre": 0.55,
                    "conventionnement_libre": 0.3,
                    "sexe_Femme": 0.5,
                    "sexe_Homme": 0.5,
                },
            },
            {
                "id": 1,
                "label": "45-60 mid femmes NON-LIBRE",
                "n_clients": 500,
                "share_of_clients": 0.50,
                "share_of_ca": 0.45,
                "centroid": {
                    "age_dernier_achat": 48.0,
                    "panier_moyen": 160.0,
                    "n_achats_totaux": 1.8,
                    "mois_entre_achats": 10.0,
                    "part_premium_plus": 0.20,
                    "ratio_monture_verre": 0.50,
                    "conventionnement_libre": 0.2,
                    "sexe_Femme": 0.85,
                    "sexe_Homme": 0.15,
                },
            },
            {
                "id": 2,
                "label": "60-75 bas hommes LIBRE",
                "n_clients": 300,
                "share_of_clients": 0.30,
                "share_of_ca": 0.20,
                "centroid": {
                    "age_dernier_achat": 67.0,
                    "panier_moyen": 120.0,
                    "n_achats_totaux": 1.2,
                    "mois_entre_achats": 0.0,
                    "part_premium_plus": 0.05,
                    "ratio_monture_verre": 0.40,
                    "conventionnement_libre": 0.7,
                    "sexe_Femme": 0.15,
                    "sexe_Homme": 0.85,
                },
            },
        ],
    }


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
        tranche_age="45-60",
        statut_client="Renouvellement",
    )
    base.update(k)
    return base


@pytest.fixture
def mini_sales() -> pd.DataFrame:
    """10 clients across 3 stores, dates in 2023-2024, with segment_id."""
    rows = []
    # -- Segment 0 (premium): clients 1-3, Avranches --
    for cid, conv, age in [(1, "LIBRE", 55), (2, "CSS", 50), (3, "KALIXIA", 58)]:
        for fid_suffix, dt, gamme, ca, fam in [
            ("A", "2023-03-10", "PREMIUM", 240.0, "OPT_VERRE"),
            ("A", "2023-03-10", None, 110.0, "OPT_MONTURE"),
            ("B", "2024-05-15", "PRESTIGE", 310.0, "OPT_VERRE"),
        ]:
            rows.append(_row(
                id_client=cid, ville="Avranches",
                id_facture_rang=f"F{cid}{fid_suffix}|1",
                date_facture=pd.Timestamp(dt),
                famille_article=fam, gamme_verre_visaudio=gamme,
                ca_ht_article=ca, conventionnement=conv,
                age_client=age, sexe="Femme" if cid % 2 else "Homme",
                segment_id=0,
            ))
    # -- Segment 1 (mid): clients 4-7, Cherbourg --
    for cid, conv, age in [(4, "CSS", 45), (5, "SANTECLAIR", 49),
                           (6, "CSS", 47), (7, "ITELIS", 51)]:
        for fid_suffix, dt, gamme, ca in [
            ("A", "2023-06-20", "CONFORT", 170.0),
            ("B", "2024-01-10", "ESSENTIEL", 130.0),
        ]:
            rows.append(_row(
                id_client=cid, ville="Cherbourg-en-Cotentin",
                id_facture_rang=f"F{cid}{fid_suffix}|1",
                date_facture=pd.Timestamp(dt),
                famille_article="OPT_VERRE", gamme_verre_visaudio=gamme,
                ca_ht_article=ca, conventionnement=conv,
                age_client=age, sexe="Femme",
                segment_id=1,
            ))
    # -- Segment 2 (bas): clients 8-10, Rampan --
    for cid, conv, age in [(8, "LIBRE", 65), (9, "LIBRE", 70), (10, "CSS", 68)]:
        rows.append(_row(
            id_client=cid, ville="Rampan",
            id_facture_rang=f"F{cid}A|1",
            date_facture=pd.Timestamp("2024-02-15"),
            famille_article="OPT_VERRE", gamme_verre_visaudio="ESSENTIEL",
            ca_ht_article=95.0, conventionnement=conv,
            age_client=age, sexe="Homme",
            segment_id=2,
        ))

    df = pd.DataFrame(rows)
    df["date_facture"] = pd.to_datetime(df["date_facture"])
    df["famille_article"] = df["famille_article"].astype("category")
    df["ville"] = df["ville"].astype("category")
    df["conventionnement"] = df["conventionnement"].astype("category")
    df["gamme_verre_visaudio"] = df["gamme_verre_visaudio"].astype(
        CategoricalDtype(categories=GAMME_ORDER, ordered=True)
    )
    df["sexe"] = df["sexe"].astype("category")
    df["statut_client"] = df["statut_client"].astype("category")
    df["tranche_age"] = df["tranche_age"].astype("category")
    df["est_verre"] = df["famille_article"] == "OPT_VERRE"
    df["est_premium_plus"] = df["gamme_verre_visaudio"].isin(["PREMIUM", "PRESTIGE"])
    df["segment_id"] = df["segment_id"].astype("int64")
    return df

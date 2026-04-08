"""Shared DataFrame fixtures for KPI unit tests.

The tiny_sales fixture is a hand-crafted 16-row dataset covering:
  - 3 villes (Avranches, Cherbourg, Carentan)
  - 2 segments (via tranche_age: '45-60' and '60-75')
  - 3 familles (verre, monture, solaire)
  - 4 gammes (all including PRESTIGE)
  - 2 conventionnements (LIBRE, CSS)
  - 3 distinct clients, with repeats (client 1 renews, client 2 cross-sells)

KPI expected values are documented in each test file.
"""
from __future__ import annotations

import pandas as pd
import pytest
from pandas.api.types import CategoricalDtype


GAMME_ORDER = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


@pytest.fixture
def tiny_sales() -> pd.DataFrame:
    # client 1 (Avranches, age 55 → 45-60): 2 factures (renouvellement)
    #   facture F1: 1 verre PREMIUM 200€ + 1 monture 100€
    #   facture F2 (10 mois plus tard): 1 verre PRESTIGE 300€ + 1 monture 120€
    # client 2 (Cherbourg, age 65 → 60-75): 1 facture F3, 1 verre CONFORT 150€ + 1 monture 80€ + 1 solaire 60€
    # client 3 (Carentan, age 50 → 45-60): 1 facture F4, 1 verre ESSENTIEL 90€ + 1 monture 70€
    # client 4 (Avranches, age 70 → 60-75): 1 facture F5 (nouveau), 1 verre PREMIUM 220€
    # client 5 (Cherbourg, age 58 → 45-60): 1 facture F6, 1 verre PRESTIGE 310€ + 1 monture 130€
    rows = [
        # --- client 1, facture F1 (Avranches, verre PREMIUM + monture)
        dict(id_client=1, ville="Avranches", id_facture_rang="F1|1", rang_paire=1,
             date_facture="2024-02-10", famille_article="OPT_VERRE",
             gamme_verre_visaudio="PREMIUM", ca_ht_article=200.0,
             conventionnement="LIBRE", age_client=55, tranche_age="45-60",
             sexe="Femme", statut_client="Renouvellement", qte_article=1),
        dict(id_client=1, ville="Avranches", id_facture_rang="F1|1", rang_paire=1,
             date_facture="2024-02-10", famille_article="OPT_MONTURE",
             gamme_verre_visaudio=None, ca_ht_article=100.0,
             conventionnement="LIBRE", age_client=55, tranche_age="45-60",
             sexe="Femme", statut_client="Renouvellement", qte_article=1),
        # --- client 1, facture F2 (upgrade to PRESTIGE)
        dict(id_client=1, ville="Avranches", id_facture_rang="F2|1", rang_paire=1,
             date_facture="2024-12-15", famille_article="OPT_VERRE",
             gamme_verre_visaudio="PRESTIGE", ca_ht_article=300.0,
             conventionnement="LIBRE", age_client=55, tranche_age="45-60",
             sexe="Femme", statut_client="Renouvellement", qte_article=1),
        dict(id_client=1, ville="Avranches", id_facture_rang="F2|1", rang_paire=1,
             date_facture="2024-12-15", famille_article="OPT_MONTURE",
             gamme_verre_visaudio=None, ca_ht_article=120.0,
             conventionnement="LIBRE", age_client=55, tranche_age="45-60",
             sexe="Femme", statut_client="Renouvellement", qte_article=1),
        # --- client 2 (Cherbourg)
        dict(id_client=2, ville="Cherbourg", id_facture_rang="F3|1", rang_paire=1,
             date_facture="2024-05-20", famille_article="OPT_VERRE",
             gamme_verre_visaudio="CONFORT", ca_ht_article=150.0,
             conventionnement="CSS", age_client=65, tranche_age="60-75",
             sexe="Homme", statut_client="Renouvellement", qte_article=1),
        dict(id_client=2, ville="Cherbourg", id_facture_rang="F3|1", rang_paire=1,
             date_facture="2024-05-20", famille_article="OPT_MONTURE",
             gamme_verre_visaudio=None, ca_ht_article=80.0,
             conventionnement="CSS", age_client=65, tranche_age="60-75",
             sexe="Homme", statut_client="Renouvellement", qte_article=1),
        dict(id_client=2, ville="Cherbourg", id_facture_rang="F3|1", rang_paire=1,
             date_facture="2024-05-20", famille_article="OPT_SOLAIRE",
             gamme_verre_visaudio=None, ca_ht_article=60.0,
             conventionnement="CSS", age_client=65, tranche_age="60-75",
             sexe="Homme", statut_client="Renouvellement", qte_article=1),
        # --- client 3 (Carentan)
        dict(id_client=3, ville="Carentan", id_facture_rang="F4|1", rang_paire=1,
             date_facture="2024-08-10", famille_article="OPT_VERRE",
             gamme_verre_visaudio="ESSENTIEL", ca_ht_article=90.0,
             conventionnement="LIBRE", age_client=50, tranche_age="45-60",
             sexe="Femme", statut_client="Nouveau client", qte_article=1),
        dict(id_client=3, ville="Carentan", id_facture_rang="F4|1", rang_paire=1,
             date_facture="2024-08-10", famille_article="OPT_MONTURE",
             gamme_verre_visaudio=None, ca_ht_article=70.0,
             conventionnement="LIBRE", age_client=50, tranche_age="45-60",
             sexe="Femme", statut_client="Nouveau client", qte_article=1),
        # --- client 4 (Avranches, new, 60-75, PREMIUM)
        dict(id_client=4, ville="Avranches", id_facture_rang="F5|1", rang_paire=1,
             date_facture="2024-09-18", famille_article="OPT_VERRE",
             gamme_verre_visaudio="PREMIUM", ca_ht_article=220.0,
             conventionnement="LIBRE", age_client=70, tranche_age="60-75",
             sexe="Homme", statut_client="Nouveau client", qte_article=1),
        # --- client 5 (Cherbourg, 45-60, PRESTIGE)
        dict(id_client=5, ville="Cherbourg", id_facture_rang="F6|1", rang_paire=1,
             date_facture="2024-10-22", famille_article="OPT_VERRE",
             gamme_verre_visaudio="PRESTIGE", ca_ht_article=310.0,
             conventionnement="LIBRE", age_client=58, tranche_age="45-60",
             sexe="Homme", statut_client="Renouvellement", qte_article=1),
        dict(id_client=5, ville="Cherbourg", id_facture_rang="F6|1", rang_paire=1,
             date_facture="2024-10-22", famille_article="OPT_MONTURE",
             gamme_verre_visaudio=None, ca_ht_article=130.0,
             conventionnement="LIBRE", age_client=58, tranche_age="45-60",
             sexe="Homme", statut_client="Renouvellement", qte_article=1),
    ]
    df = pd.DataFrame(rows)
    df["date_facture"] = pd.to_datetime(df["date_facture"])
    df["ville"] = df["ville"].astype("category")
    df["famille_article"] = df["famille_article"].astype("category")
    df["conventionnement"] = df["conventionnement"].astype("category")
    df["gamme_verre_visaudio"] = df["gamme_verre_visaudio"].astype(
        CategoricalDtype(categories=GAMME_ORDER, ordered=True)
    )
    df["tranche_age"] = df["tranche_age"].astype("category")
    df["est_verre"] = (df["famille_article"] == "OPT_VERRE")
    df["est_premium_plus"] = df["gamme_verre_visaudio"].isin(["PREMIUM", "PRESTIGE"])
    return df

import pandas as pd
import pytest

from src.kpi.cadrage import (
    ca_total,
    ca_par_famille,
    ca_par_magasin,
    panier_moyen_reseau,
    panier_moyen_par_magasin,
    clients_uniques,
    taux_nouveaux_vs_renouv,
    ca_par_mois,
)


def test_ca_total(tiny_sales):
    # Sum of all ca_ht_article: 200+100+300+120+150+80+60+90+70+220+310+130 = 1830
    assert ca_total(tiny_sales) == 1830.0


def test_ca_par_famille(tiny_sales):
    res = ca_par_famille(tiny_sales)
    # verre: 200+300+150+90+220+310 = 1270
    # monture: 100+120+80+70+130 = 500
    # solaire: 60
    assert res["OPT_VERRE"] == 1270.0
    assert res["OPT_MONTURE"] == 500.0
    assert res["OPT_SOLAIRE"] == 60.0


def test_ca_par_magasin(tiny_sales):
    res = ca_par_magasin(tiny_sales)
    # Avranches: 200+100+300+120+220 = 940
    # Cherbourg: 150+80+60+310+130 = 730
    # Carentan: 90+70 = 160
    assert res["Avranches"] == 940.0
    assert res["Cherbourg"] == 730.0
    assert res["Carentan"] == 160.0


def test_panier_moyen_reseau(tiny_sales):
    # 6 distinct factures: F1(300), F2(420), F3(290), F4(160), F5(220), F6(440) → mean = 305
    assert panier_moyen_reseau(tiny_sales) == 305.0


def test_panier_moyen_par_magasin(tiny_sales):
    res = panier_moyen_par_magasin(tiny_sales)
    # Avranches factures: F1=300, F2=420, F5=220 → mean = 313.333...
    assert res["Avranches"] == pytest.approx(940 / 3)
    # Cherbourg: F3=290, F6=440 → 365
    assert res["Cherbourg"] == 365.0
    # Carentan: F4=160
    assert res["Carentan"] == 160.0


def test_clients_uniques(tiny_sales):
    assert clients_uniques(tiny_sales) == 5


def test_taux_nouveaux_vs_renouv(tiny_sales):
    res = taux_nouveaux_vs_renouv(tiny_sales)
    # clients 3 & 4 are "Nouveau client" → 2 out of 5
    assert res["Nouveau client"] == pytest.approx(2 / 5)
    assert res["Renouvellement"] == pytest.approx(3 / 5)


def test_ca_par_mois(tiny_sales):
    res = ca_par_mois(tiny_sales)
    # Feb 2024: 200+100 = 300 ; May: 290 ; Aug: 160 ; Sep: 220 ; Oct: 440 ; Dec: 420
    assert res["2024-02"] == 300.0
    assert res["2024-12"] == 420.0
    # 6 distinct months
    assert len(res) == 6

import pytest

from src.kpi.benchmark import (
    classement_magasins,
    decomposition_ca,
    ecart_mediane_reseau,
    contrefactuel_best_practice,
)


def test_classement_magasins(tiny_sales):
    rank = classement_magasins(tiny_sales)
    # CA: Avranches 940, Cherbourg 730, Carentan 160
    assert rank["Avranches"] == 1
    assert rank["Cherbourg"] == 2
    assert rank["Carentan"] == 3


def test_decomposition_ca(tiny_sales):
    decomp = decomposition_ca(tiny_sales)
    # Avranches: n_factures = 3 (F1,F2,F5), panier moyen = 940/3 = 313.33
    assert decomp["Avranches"]["n_factures"] == 3
    assert decomp["Avranches"]["panier_moyen"] == pytest.approx(940 / 3)
    assert decomp["Avranches"]["ca_total"] == 940.0


def test_ecart_mediane_reseau(tiny_sales):
    # Median of (940, 730, 160) = 730
    # Avranches: (940-730)/730 ≈ +0.288
    ec = ecart_mediane_reseau(tiny_sales, metric="ca_par_magasin")
    assert ec["Avranches"] == pytest.approx((940 - 730) / 730)
    assert ec["Cherbourg"] == pytest.approx(0.0)


def test_contrefactuel_best_practice(tiny_sales):
    # If Carentan adopted Avranches's mix, what would its CA verre be?
    # Carentan has 1 verre sale; Avranches mean verre ticket is ~240.
    res = contrefactuel_best_practice(
        tiny_sales, source_ville="Avranches", target_ville="Carentan"
    )
    assert res["delta_ca_verre"] > 0  # Carentan is lower, so uplift is positive

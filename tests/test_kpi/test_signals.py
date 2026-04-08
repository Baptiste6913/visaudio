import pytest

from src.kpi.signals import (
    index_saisonnalite_par_magasin,
    part_clients_60_plus,
    ratio_monture_verre_eur,
    ecart_type_mix_intra_magasin,
    part_factures_une_paire,
)


def test_index_saisonnalite_is_dict(tiny_sales):
    res = index_saisonnalite_par_magasin(tiny_sales)
    assert isinstance(res, dict)
    assert "Avranches" in res
    # Each value is a dict of month → index
    assert isinstance(res["Avranches"], dict)


def test_part_clients_60_plus(tiny_sales):
    # Clients 2 (65) and 4 (70) are 60+ → 2 out of 5 = 0.4
    assert part_clients_60_plus(tiny_sales) == pytest.approx(2 / 5)


def test_ratio_monture_verre_eur(tiny_sales):
    res = ratio_monture_verre_eur(tiny_sales)
    # Avranches: monture 220, verre 720 → 220/720
    assert res["Avranches"] == pytest.approx(220 / 720)


def test_ecart_type_mix_intra_magasin(tiny_sales):
    res = ecart_type_mix_intra_magasin(tiny_sales)
    assert "Avranches" in res
    # Just check structure, exact number depends on gamme distribution
    assert res["Avranches"] >= 0


def test_part_factures_une_paire(tiny_sales):
    # All 6 factures in tiny fixture have rang_paire=1 only → 100% = 1.0
    assert part_factures_une_paire(tiny_sales) == pytest.approx(1.0)

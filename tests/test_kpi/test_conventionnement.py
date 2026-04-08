import pytest

from src.kpi.conventionnement import (
    part_ca_par_conv,
    panier_moyen_par_conv,
    hhi_conventionnement,
    exposition_top3,
)


def test_part_ca_par_conv(tiny_sales):
    res = part_ca_par_conv(tiny_sales)
    # LIBRE: F1(300)+F2(420)+F4(160)+F5(220)+F6(440) = 1540
    # CSS: F3(290) = 290
    # Total 1830
    assert res["LIBRE"] == pytest.approx(1540 / 1830)
    assert res["CSS"] == pytest.approx(290 / 1830)


def test_panier_moyen_par_conv(tiny_sales):
    res = panier_moyen_par_conv(tiny_sales)
    # LIBRE factures: F1=300, F2=420, F4=160, F5=220, F6=440 → mean = 308
    assert res["LIBRE"] == pytest.approx(308.0)
    assert res["CSS"] == pytest.approx(290.0)


def test_hhi(tiny_sales):
    res = hhi_conventionnement(tiny_sales)
    # HHI = sum of squared shares × 10000
    # LIBRE = 0.8415..., CSS = 0.1584...
    # HHI ≈ (0.8415^2 + 0.1584^2) × 10000 ≈ 7332
    assert 7000 < res < 8000


def test_exposition_top3(tiny_sales):
    # Only 2 conventionnements → exposition top3 = 100%
    assert exposition_top3(tiny_sales) == pytest.approx(1.0)

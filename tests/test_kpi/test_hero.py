import pytest

from src.kpi.hero import (
    mix_gamme_par_magasin,
    mix_gamme_par_segment,
    panier_moyen_verre_par_segment,
    panier_moyen_verre_par_segment_top_q75,
    taux_cross_sell_verre_monture,
    taux_upgrade_renouvellement,
    part_premium_plus_par_magasin,
    ecart_au_top_du_reseau,
)


# ---------- H1 ----------
def test_mix_gamme_par_magasin_avranches(tiny_sales):
    mix = mix_gamme_par_magasin(tiny_sales)
    # Avranches verre CA: PREMIUM(200+220=420) + PRESTIGE(300) = 720
    # share PREMIUM = 420/720, PRESTIGE = 300/720
    assert mix["Avranches"]["PREMIUM"] == pytest.approx(420 / 720)
    assert mix["Avranches"]["PRESTIGE"] == pytest.approx(300 / 720)


# ---------- H2 ----------
def test_mix_gamme_par_segment(tiny_sales):
    mix = mix_gamme_par_segment(tiny_sales, segment_col="tranche_age")
    # 45-60 verre CA: PREMIUM(200)+PRESTIGE(300)+ESSENTIEL(90)+PRESTIGE(310) = 900
    # CONFORT in 60-75 only
    assert "PREMIUM" in mix["45-60"]
    assert mix["45-60"]["PREMIUM"] == pytest.approx(200 / 900)


# ---------- H3 ----------
def test_panier_moyen_verre_par_segment(tiny_sales):
    pm = panier_moyen_verre_par_segment(tiny_sales, segment_col="tranche_age")
    # 45-60 verre rows: 200, 300, 90, 310 → mean = 225
    assert pm["45-60"] == pytest.approx(225.0)
    # 60-75 verre rows: 150, 220 → mean = 185
    assert pm["60-75"] == pytest.approx(185.0)


# ---------- H4 ----------
def test_panier_moyen_verre_par_segment_top_q75(tiny_sales):
    pm_q75 = panier_moyen_verre_par_segment_top_q75(
        tiny_sales, segment_col="tranche_age"
    )
    # 45-60, per ville mean verre ticket:
    #   Avranches: mean(200, 300) = 250  [client4 age=70 is in 60-75, not 45-60]
    #   Cherbourg: mean(310) = 310
    #   Carentan: mean(90) = 90
    # Q75 across [90, 250, 310]: index = 0.75*2 = 1.5 → 250 + 0.5*(310-250) = 280
    assert pm_q75["45-60"] == pytest.approx(280.0)


# ---------- H7 ----------
def test_taux_cross_sell_verre_monture(tiny_sales):
    # 6 factures total, factures containing both verre and monture:
    #   F1 ✓, F2 ✓, F3 ✓, F4 ✓, F5 ✗ (only verre), F6 ✓ → 5/6
    assert taux_cross_sell_verre_monture(tiny_sales) == pytest.approx(5 / 6)


# ---------- H8 ----------
def test_taux_upgrade_renouvellement(tiny_sales):
    # Client 1 had 2 invoices: PREMIUM → PRESTIGE = upgrade
    # Only 1 client in renouvellement has 2+ invoices (client 1)
    # → 1/1 = 1.0
    rate = taux_upgrade_renouvellement(tiny_sales)
    assert rate == pytest.approx(1.0)


# ---------- H9 ----------
def test_part_premium_plus_par_magasin(tiny_sales):
    share = part_premium_plus_par_magasin(tiny_sales)
    # Avranches verre CA: 720 total, PREMIUM+PRESTIGE = 720 → 100%
    assert share["Avranches"] == pytest.approx(1.0)
    # Cherbourg verre CA: 150 CONFORT + 310 PRESTIGE = 460, premium+ = 310 → 310/460
    assert share["Cherbourg"] == pytest.approx(310 / 460)
    # Carentan: 90 ESSENTIEL → 0%
    assert share["Carentan"] == pytest.approx(0.0)


# ---------- H10 ----------
def test_ecart_au_top_du_reseau(tiny_sales):
    ecart = ecart_au_top_du_reseau(tiny_sales)
    # top = Avranches (1.0)
    assert ecart["Avranches"] == pytest.approx(0.0)
    assert ecart["Carentan"] == pytest.approx(-1.0)
    assert ecart["Cherbourg"] == pytest.approx(310 / 460 - 1.0)


# ========== H5 (HERO) ==========
from src.kpi.hero import compute_opportunite_upsell


def test_h5_on_tiny_fixture(tiny_sales):
    """Walkthrough of the H5 formula on the tiny fixture.

    Per-(segment, ville) verre ticket mean:
      45-60: Avranches=250 (2 rows), Cherbourg=310 (1), Carentan=90 (1)
      60-75: Avranches=220 (1), Cherbourg=150 (1)

    Q75 per segment:
      45-60: Q75 of [90, 250, 310] = 280
      60-75: Q75 of [150, 220] = 202.5

    Gap × count per cell (years_divisor=1):
      (45-60, Avranches): 30 × 2 = 60
      (45-60, Cherbourg): 0
      (45-60, Carentan):  190 × 1 = 190
      (60-75, Avranches): 0
      (60-75, Cherbourg): 52.5 × 1 = 52.5

    Grand total = 302.5
    """
    res = compute_opportunite_upsell(
        tiny_sales, segment_col="tranche_age", years_divisor=1.0
    )
    assert res["total_eur_per_year"] == pytest.approx(302.5, abs=0.5)


def test_h5_by_store_decomposition(tiny_sales):
    res = compute_opportunite_upsell(
        tiny_sales, segment_col="tranche_age", years_divisor=1.0
    )
    assert res["by_store"]["Carentan"] == pytest.approx(190.0, abs=0.5)
    assert res["by_store"]["Avranches"] == pytest.approx(60.0, abs=0.5)
    assert res["by_store"]["Cherbourg"] == pytest.approx(52.5, abs=0.5)


def test_h5_by_segment_sum_matches_total(tiny_sales):
    res = compute_opportunite_upsell(
        tiny_sales, segment_col="tranche_age", years_divisor=1.0
    )
    assert sum(res["by_segment"].values()) == pytest.approx(
        res["total_eur_per_year"], rel=1e-6
    )


def test_h5_handles_empty_df():
    import pandas as pd
    empty = pd.DataFrame(
        columns=["ville", "tranche_age", "est_verre", "ca_ht_article"]
    )
    res = compute_opportunite_upsell(empty, segment_col="tranche_age", years_divisor=1.0)
    assert res["total_eur_per_year"] == 0.0
    assert res["by_segment"] == {}
    assert res["by_store"] == {}


def test_h5_divides_by_annees_data_when_none(tiny_sales):
    res = compute_opportunite_upsell(tiny_sales, segment_col="tranche_age")
    # The tiny fixture spans 2024-02-10 to 2024-12-15 → ~0.84 years
    # So total_eur_per_year is LARGER than when years_divisor=1
    res1 = compute_opportunite_upsell(
        tiny_sales, segment_col="tranche_age", years_divisor=1.0
    )
    assert res["total_eur_per_year"] > res1["total_eur_per_year"]


def test_h5_never_goes_negative(tiny_sales):
    res = compute_opportunite_upsell(
        tiny_sales, segment_col="tranche_age", years_divisor=1.0
    )
    assert res["total_eur_per_year"] >= 0
    for v in res["by_segment"].values():
        assert v >= 0
    for v in res["by_store"].values():
        assert v >= 0

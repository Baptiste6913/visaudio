import numpy as np
import pandas as pd
import pytest

from src.segmentation.features import build_client_features, FEATURE_NAMES


def test_one_row_per_client(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    assert len(feats) == synthetic_sales["id_client"].nunique()
    assert feats.index.name == "id_client"


def test_has_expected_feature_columns(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    for col in FEATURE_NAMES:
        assert col in feats.columns, f"missing feature {col}"


def test_panier_moyen_client1(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    # Client 1: 5 rows, total CA = 220+110+300+130+320 = 1080
    # Mean ca per row = 1080 / 5 = 216
    assert feats.loc[1, "panier_moyen"] == pytest.approx(216.0)


def test_part_premium_plus_client1(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    # Client 1 verre rows: PREMIUM, PRESTIGE, PRESTIGE → 3/3 premium+
    assert feats.loc[1, "part_premium_plus"] == pytest.approx(1.0)


def test_ratio_monture_verre_client3(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    # Client 3: monture CA = 90+95 = 185, verre CA = 170+180 = 350
    assert feats.loc[3, "ratio_monture_verre"] == pytest.approx(185 / 350)


def test_conventionnement_libre_binary(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    # Client 1 all LIBRE → 1.0 ; Client 2 all CSS → 0.0
    assert feats.loc[1, "conventionnement_libre"] == pytest.approx(1.0)
    assert feats.loc[2, "conventionnement_libre"] == pytest.approx(0.0)


def test_sex_is_one_hot(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    assert "sexe_Femme" in feats.columns
    assert "sexe_Homme" in feats.columns
    assert feats.loc[1, "sexe_Femme"] == 1.0
    assert feats.loc[4, "sexe_Homme"] == 1.0


def test_no_nans(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    assert not feats.isna().any().any(), "client features must not contain NaN"

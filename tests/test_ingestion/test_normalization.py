from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.normalization import (
    normalize_dataframe,
    write_parquet,
)


def _raw_fixture() -> pd.DataFrame:
    """Simulates what read_visaudio_excel returns (post column rename, pre normalization)."""
    return pd.DataFrame(
        {
            "ville": ["Avranches", "Cherbourg", "Avranches"],
            "implantation": ["CENTRE-VILLE", "PERIPHERIE", "CENTRE-VILLE"],
            "secteur_economique": ["Tertiaire"] * 3,
            "date_facture": pd.to_datetime(
                ["2024-03-15", "2024-03-16", "2024-03-17"]
            ),
            "id_facture_rang": ["F1|1", "F2|1", "F3|1"],
            "rang_paire": [1, 1, 1],
            "famille_article": ["OPT_VERRE", "OPT_MONTURE", "OPT_VERRE"],
            "categorie_geom_verre": ["UNIFOCAL", None, "MULTIFOCAL"],
            "gamme_verre_fournisseur": ["Varilux", None, "Hoya ID"],
            "gamme_verre_visaudio": ["PREMIUM", None, "PRESTIGE"],
            "nom_marque": ["ESS", "RAY-BAN", "HOY"],
            "libelle_produit": ["Varilux Comfort", "RB5154", "Hoya ID"],
            "qte_article": [2, 1, 2],
            "ca_ht_article": [180.50, 95.0, 320.0],
            "id_client": [42, 42, 101],
            "conventionnement": ["LIBRE", "LIBRE", "CSS"],
            "date_naissance_client": pd.to_datetime(
                ["1970-05-12", "1970-05-12", "1988-11-02"]
            ),
            "sexe": ["Femme", "Femme", "Homme"],
            "statut_client": ["Renouvellement", "Renouvellement", "Nouveau client"],
        }
    )


def test_returns_expected_dtypes():
    df = normalize_dataframe(_raw_fixture())
    assert df["ville"].dtype.name == "category"
    assert df["date_facture"].dtype.name == "datetime64[ns]"
    assert df["qte_article"].dtype.name == "int16"
    assert df["ca_ht_article"].dtype.name == "float64"
    assert df["id_client"].dtype.name == "int64"


def test_adds_derived_columns():
    df = normalize_dataframe(_raw_fixture())
    assert "age_client" in df.columns
    assert "tranche_age" in df.columns
    assert "mois_facture" in df.columns
    assert "annee_facture" in df.columns
    assert "est_verre" in df.columns
    assert "est_premium_plus" in df.columns


def test_age_client_is_correct():
    df = normalize_dataframe(_raw_fixture())
    # First row: born 1970-05-12, invoiced 2024-03-15 → age 53
    assert df.loc[0, "age_client"] == 53


def test_est_verre_flag():
    df = normalize_dataframe(_raw_fixture())
    assert bool(df.loc[0, "est_verre"]) is True
    assert bool(df.loc[1, "est_verre"]) is False


def test_est_premium_plus_flag():
    df = normalize_dataframe(_raw_fixture())
    assert bool(df.loc[0, "est_premium_plus"]) is True   # PREMIUM
    assert bool(df.loc[1, "est_premium_plus"]) is False  # None (monture)
    assert bool(df.loc[2, "est_premium_plus"]) is True   # PRESTIGE


def test_gamme_visaudio_is_ordered_category():
    df = normalize_dataframe(_raw_fixture())
    cat = df["gamme_verre_visaudio"].dtype
    assert cat.ordered is True
    assert list(cat.categories) == ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


def test_rejects_rows_violating_business_rules():
    raw = _raw_fixture()
    # Inject a row where gamme Visaudio is set on a monture (should be rejected)
    raw.loc[1, "gamme_verre_visaudio"] = "CONFORT"
    df, rejected = normalize_dataframe(raw, return_rejected=True)
    assert len(df) == 2
    assert len(rejected) == 1
    assert rejected.iloc[0]["reason"].startswith("gamme_verre_visaudio")


def test_write_parquet_roundtrip(tmp_path: Path):
    df = normalize_dataframe(_raw_fixture())
    out = tmp_path / "sales.parquet"
    write_parquet(df, out)
    assert out.exists()
    loaded = pd.read_parquet(out)
    assert len(loaded) == len(df)
    assert list(loaded.columns) == list(df.columns)

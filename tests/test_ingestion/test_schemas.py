from datetime import datetime

import pytest
from pydantic import ValidationError

from src.ingestion.schemas import NormalizedSaleRow


VALID_ROW = {
    "ville": "Avranches",
    "implantation": "CENTRE-VILLE",
    "secteur_economique": "Tertiaire",
    "date_facture": datetime(2024, 3, 15),
    "id_facture_rang": "12345678|1",
    "rang_paire": 1,
    "famille_article": "OPT_VERRE",
    "categorie_geom_verre": "UNIFOCAL",
    "gamme_verre_fournisseur": "Varilux",
    "gamme_verre_visaudio": "PREMIUM",
    "nom_marque": "ESS",
    "libelle_produit": "Varilux Comfort",
    "qte_article": 2,
    "ca_ht_article": 180.50,
    "id_client": 42,
    "conventionnement": "LIBRE",
    "date_naissance_client": datetime(1970, 5, 12),
    "sexe": "Femme",
    "statut_client": "Renouvellement",
}


def test_accepts_valid_row():
    row = NormalizedSaleRow.model_validate(VALID_ROW)
    assert row.ville == "Avranches"
    assert row.gamme_verre_visaudio == "PREMIUM"


def test_rejects_gamme_visaudio_on_non_verre():
    bad = dict(VALID_ROW, famille_article="OPT_MONTURE", gamme_verre_visaudio="PREMIUM")
    with pytest.raises(ValidationError, match="gamme_verre_visaudio"):
        NormalizedSaleRow.model_validate(bad)


def test_accepts_null_gamme_on_monture():
    ok = dict(
        VALID_ROW,
        famille_article="OPT_MONTURE",
        gamme_verre_visaudio=None,
        categorie_geom_verre=None,
        gamme_verre_fournisseur=None,
    )
    row = NormalizedSaleRow.model_validate(ok)
    assert row.gamme_verre_visaudio is None


def test_rejects_negative_ca():
    bad = dict(VALID_ROW, ca_ht_article=-10.0)
    with pytest.raises(ValidationError):
        NormalizedSaleRow.model_validate(bad)


def test_rejects_zero_qte():
    bad = dict(VALID_ROW, qte_article=0)
    with pytest.raises(ValidationError):
        NormalizedSaleRow.model_validate(bad)


def test_accepts_null_optional_fields():
    ok = dict(VALID_ROW, date_naissance_client=None, statut_client=None)
    row = NormalizedSaleRow.model_validate(ok)
    assert row.statut_client is None

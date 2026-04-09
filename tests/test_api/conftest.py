"""Shared fixtures for API tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import create_app


@pytest.fixture
def data_dir(tmp_path) -> Path:
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "mesa_runs").mkdir()

    (processed / "kpis.json").write_text(json.dumps({
        "meta": {"generated_at": "2026-04-09"},
        "cadrage": {"ca_total": 9_100_000},
    }), encoding="utf-8")

    (processed / "archetypes.json").write_text(json.dumps({
        "generated_at": "2026-04-09",
        "n_archetypes": 2,
        "archetypes": [
            {"id": 0, "label": "test0", "n_clients": 100,
             "share_of_clients": 0.5, "share_of_ca": 0.6,
             "centroid": {"panier_moyen": 200.0, "mois_entre_achats": 12.0,
                          "n_achats_totaux": 2.0, "part_premium_plus": 0.3,
                          "age_dernier_achat": 50.0, "ratio_monture_verre": 0.5,
                          "conventionnement_libre": 0.4, "sexe_Femme": 0.5,
                          "sexe_Homme": 0.5}},
            {"id": 1, "label": "test1", "n_clients": 100,
             "share_of_clients": 0.5, "share_of_ca": 0.4,
             "centroid": {"panier_moyen": 150.0, "mois_entre_achats": 10.0,
                          "n_achats_totaux": 1.5, "part_premium_plus": 0.1,
                          "age_dernier_achat": 45.0, "ratio_monture_verre": 0.4,
                          "conventionnement_libre": 0.3, "sexe_Femme": 0.8,
                          "sexe_Homme": 0.2}},
        ],
    }), encoding="utf-8")

    (processed / "diagnostics.json").write_text(json.dumps({
        "generated_at": "2026-04-09",
        "Avranches": {"findings": []},
    }), encoding="utf-8")

    return tmp_path


@pytest.fixture
def app(data_dir):
    return create_app(data_dir=data_dir / "processed", enable_prewarm=False)


@pytest.fixture
async def client(app, data_dir):
    from src.api import endpoints
    # ASGITransport does not trigger ASGI lifespan events,
    # so we manually initialise the module-level data_dir.
    endpoints.set_data_dir(data_dir / "processed")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

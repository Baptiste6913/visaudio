"""Tests for FastAPI endpoints — P4 Tasks 3 & 4."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.anyio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_get_kpis(client):
    resp = await client.get("/kpis")
    assert resp.status_code == 200
    assert "cadrage" in resp.json()


@pytest.mark.anyio
async def test_get_archetypes(client):
    resp = await client.get("/archetypes")
    assert resp.status_code == 200
    assert resp.json()["n_archetypes"] == 2


@pytest.mark.anyio
async def test_get_diagnostics(client):
    resp = await client.get("/diagnostics")
    assert resp.status_code == 200
    assert "Avranches" in resp.json()


@pytest.mark.anyio
async def test_get_scenarios(client):
    resp = await client.get("/scenarios")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 6
    ids = {s["scenario_id"] for s in body}
    assert "SC-BASE" in ids
    assert "SC-L2a" in ids


# ---------- Task 4: POST /simulate tests ----------


def _create_mini_parquet(data_dir: Path) -> None:
    """Helper to create a minimal sales parquet for simulation tests."""
    import pandas as pd
    from pandas.api.types import CategoricalDtype

    GAMME_ORDER = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]
    rows = []
    for cid in range(1, 6):
        rows.append({
            "id_client": cid, "ville": "Avranches",
            "id_facture_rang": f"F{cid}A|1", "rang_paire": 1, "qte_article": 1,
            "date_facture": pd.Timestamp("2024-03-15"),
            "famille_article": "OPT_VERRE", "gamme_verre_visaudio": "CONFORT",
            "ca_ht_article": 150.0, "conventionnement": "LIBRE",
            "age_client": 50, "sexe": "Femme", "segment_id": 0,
            "tranche_age": "45-60", "statut_client": "Renouvellement",
            "est_verre": True, "est_premium_plus": False,
            "implantation": "CENTRE-VILLE", "secteur_economique": "Tertiaire",
            "gamme_verre_fournisseur": None, "libelle_produit": "x",
            "nom_marque": "ESS", "categorie_geom_verre": None,
            "mois_facture": "2024-03", "annee_facture": 2024,
        })
    df = pd.DataFrame(rows)
    df["date_facture"] = pd.to_datetime(df["date_facture"])
    df["segment_id"] = df["segment_id"].astype("int64")
    for col in ["famille_article", "ville", "conventionnement", "sexe",
                "statut_client", "tranche_age"]:
        df[col] = df[col].astype("category")
    df["gamme_verre_visaudio"] = df["gamme_verre_visaudio"].astype(
        CategoricalDtype(categories=GAMME_ORDER, ordered=True)
    )
    parquet_path = data_dir / "processed" / "sales.parquet"
    df.to_parquet(parquet_path, engine="pyarrow")


@pytest.mark.anyio
async def test_simulate_base_returns_200(client, data_dir):
    _create_mini_parquet(data_dir)
    resp = await client.post("/simulate", json={
        "scenario_id": "SC-BASE", "n_steps": 3, "n_replications": 2,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["scenario_id"] == "SC-BASE"
    assert "baseline" in body
    assert len(body["baseline"]["ca_mean"]) == 3
    assert body["from_cache"] is False


@pytest.mark.anyio
async def test_simulate_invalid_scenario(client):
    resp = await client.post("/simulate", json={"scenario_id": "SC-NOPE"})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_simulate_uses_cache(client, data_dir):
    _create_mini_parquet(data_dir)
    body = {"scenario_id": "SC-BASE", "n_steps": 3, "n_replications": 2}
    resp1 = await client.post("/simulate", json=body)
    assert resp1.status_code == 200
    assert resp1.json()["from_cache"] is False

    resp2 = await client.post("/simulate", json=body)
    assert resp2.status_code == 200
    assert resp2.json()["from_cache"] is True

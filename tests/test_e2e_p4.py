"""End-to-end test for P4 — FastAPI on sample_500.xlsx pipeline output."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

SAMPLE = Path("data/samples/sample_500.xlsx")


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_500.xlsx not available")
class TestE2EP4:
    """Start the API on real pipeline output and verify endpoints."""

    @pytest.fixture(autouse=True, scope="class")
    def pipeline_and_app(self, tmp_path_factory):
        """Run the full pipeline, then create the app."""
        tmp = tmp_path_factory.mktemp("e2e_p4")
        processed = tmp / "processed"
        processed.mkdir()
        (processed / "mesa_runs").mkdir()

        from src.ingestion.excel_parser import read_visaudio_excel
        from src.ingestion.normalization import normalize_dataframe, write_parquet
        from src.segmentation.pipeline import run_segmentation, write_archetypes_json
        from src.kpi.pipeline import write_kpis_json
        from src.rules.diagnostics import build_diagnostics_payload, write_diagnostics_json

        raw = read_visaudio_excel(SAMPLE)
        df, _ = normalize_dataframe(raw, return_rejected=True)
        parquet = processed / "sales.parquet"
        write_parquet(df, parquet)

        df_seg, arch = run_segmentation(df, n_clusters=6)
        write_parquet(df_seg, parquet)
        write_archetypes_json(arch, processed / "archetypes.json")
        write_kpis_json(df_seg, processed / "kpis.json")

        kpis = json.loads((processed / "kpis.json").read_text(encoding="utf-8"))
        diag = build_diagnostics_payload(kpis)
        write_diagnostics_json(diag, processed / "diagnostics.json")

        from src.api.main import create_app
        self.__class__._app = create_app(data_dir=processed, enable_prewarm=False)
        self.__class__._processed = processed

    @pytest.fixture
    async def client(self):
        from src.api import endpoints
        endpoints.set_data_dir(self._processed)
        transport = ASGITransport(app=self._app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    @pytest.mark.anyio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_kpis_has_cadrage(self, client):
        resp = await client.get("/kpis")
        assert resp.status_code == 200
        assert "cadrage" in resp.json()

    @pytest.mark.anyio
    async def test_archetypes_has_6(self, client):
        resp = await client.get("/archetypes")
        assert resp.status_code == 200
        assert resp.json()["n_archetypes"] == 6

    @pytest.mark.anyio
    async def test_scenarios_returns_7(self, client):
        resp = await client.get("/scenarios")
        assert resp.status_code == 200
        assert len(resp.json()) == 7

    @pytest.mark.anyio
    async def test_simulate_baseline(self, client):
        resp = await client.post("/simulate", json={
            "scenario_id": "SC-BASE", "n_steps": 3, "n_replications": 2,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["scenario_id"] == "SC-BASE"
        assert len(body["baseline"]["ca_mean"]) == 3

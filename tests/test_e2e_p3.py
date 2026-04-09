"""End-to-end test for P3 — simulation on sample_500.xlsx."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

SAMPLE = Path("data/samples/sample_500.xlsx")


@pytest.mark.skipif(not SAMPLE.exists(), reason="sample_500.xlsx not available")
class TestE2EP3:
    """Full chain: ingest → segment → simulate baseline (6 months, 3 reps)."""

    @pytest.fixture(autouse=True, scope="class")
    def pipeline(self, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("e2e_p3")
        parquet = tmp / "sales.parquet"
        archetypes_json = tmp / "archetypes.json"
        run_json = tmp / "baseline.json"

        from src.ingestion.excel_parser import read_visaudio_excel
        from src.ingestion.normalization import normalize_dataframe, write_parquet

        raw = read_visaudio_excel(SAMPLE)
        df, _ = normalize_dataframe(raw, return_rejected=True)
        write_parquet(df, parquet)

        from src.segmentation.pipeline import run_segmentation, write_archetypes_json

        df_seg, arch = run_segmentation(df, n_clusters=6)
        write_parquet(df_seg, parquet)
        write_archetypes_json(arch, archetypes_json)

        from src.simulation.runner import run_scenario, write_run_result

        result = run_scenario(
            sales_df=df_seg, archetypes_payload=arch,
            scenario_id="SC-BASE", n_steps=6, n_replications=3, seed=42,
        )
        write_run_result(result, run_json)

        self.__class__._result = result
        self.__class__._run_json = run_json
        self.__class__._parquet = parquet
        self.__class__._archetypes_json = archetypes_json

    def test_baseline_produces_6_months(self):
        assert len(self._result.ca_mean) == 6

    def test_ca_is_positive(self):
        assert all(v >= 0 for v in self._result.ca_mean)

    def test_ci_bounds_hold(self):
        for i in range(6):
            assert self._result.ca_lower[i] <= self._result.ca_mean[i]
            assert self._result.ca_mean[i] <= self._result.ca_upper[i]

    def test_output_json_exists(self):
        assert self._run_json.exists()

    def test_result_is_reproducible(self):
        import json
        from src.simulation.runner import run_scenario

        arch = json.loads(self._archetypes_json.read_text(encoding="utf-8"))
        df = pd.read_parquet(self._parquet)
        r2 = run_scenario(df, arch, "SC-BASE", n_steps=6, n_replications=3, seed=42)
        assert r2.ca_mean == self._result.ca_mean

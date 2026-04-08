"""End-to-end P2 pipeline test on sample_500.xlsx.

Runs ingest → segment → kpi → diagnose and asserts the complete chain
produces valid artefacts.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from src.cli import cli


SAMPLE = Path("data/samples/sample_500.xlsx")


def test_e2e_p2_full_refresh(tmp_path: Path):
    runner = CliRunner()
    res = runner.invoke(
        cli,
        [
            "refresh",
            "--source", str(SAMPLE),
            "--parquet", str(tmp_path / "sales.parquet"),
            "--archetypes", str(tmp_path / "archetypes.json"),
            "--kpis", str(tmp_path / "kpis.json"),
            "--diagnostics", str(tmp_path / "diagnostics.json"),
            "--n-clusters", "6",
        ],
    )
    assert res.exit_code == 0, res.output

    # Verify all four artefacts exist
    assert (tmp_path / "sales.parquet").exists()
    assert (tmp_path / "archetypes.json").exists()
    assert (tmp_path / "kpis.json").exists()
    assert (tmp_path / "diagnostics.json").exists()

    # Verify segmented Parquet has the segment_id column
    df = pd.read_parquet(tmp_path / "sales.parquet")
    assert "segment_id" in df.columns

    # Verify archetypes has 6 entries
    arch = json.loads((tmp_path / "archetypes.json").read_text(encoding="utf-8"))
    assert arch["n_archetypes"] == 6
    assert len(arch["archetypes"]) == 6

    # Verify kpis uses segment_id
    kpis = json.loads((tmp_path / "kpis.json").read_text(encoding="utf-8"))
    assert kpis["hero"]["segment_column_used"] == "segment_id"

    # Verify diagnostics has a _network entry
    diag = json.loads((tmp_path / "diagnostics.json").read_text(encoding="utf-8"))
    assert "_network" in diag

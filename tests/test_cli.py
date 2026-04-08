import json
from pathlib import Path

import pandas as pd
from click.testing import CliRunner

from src.cli import cli


SAMPLE = Path("data/samples/sample_500.xlsx")


def test_cli_ingest_writes_parquet(tmp_path: Path):
    runner = CliRunner()
    dst = tmp_path / "sales.parquet"
    res = runner.invoke(
        cli, ["ingest", "--source", str(SAMPLE), "--out", str(dst)]
    )
    assert res.exit_code == 0, res.output
    assert dst.exists()
    df = pd.read_parquet(dst)
    assert len(df) > 0
    assert "ville" in df.columns


def test_cli_kpi_writes_json(tmp_path: Path):
    runner = CliRunner()
    # First run ingest into a temp parquet
    parquet = tmp_path / "sales.parquet"
    runner.invoke(cli, ["ingest", "--source", str(SAMPLE), "--out", str(parquet)])
    # Then run kpi
    kpis = tmp_path / "kpis.json"
    res = runner.invoke(
        cli, ["kpi", "--parquet", str(parquet), "--out", str(kpis)]
    )
    assert res.exit_code == 0, res.output
    assert kpis.exists()
    payload = json.loads(kpis.read_text(encoding="utf-8"))
    assert "hero" in payload
    assert "opportunite_upsell_annuelle" in payload["hero"]


def test_cli_diagnose_writes_diagnostics(tmp_path: Path):
    runner = CliRunner()
    parquet = tmp_path / "sales.parquet"
    kpis = tmp_path / "kpis.json"
    diag = tmp_path / "diagnostics.json"
    runner.invoke(cli, ["ingest", "--source", str(SAMPLE), "--out", str(parquet)])
    runner.invoke(cli, ["kpi", "--parquet", str(parquet), "--out", str(kpis)])
    res = runner.invoke(
        cli,
        ["diagnose", "--kpis", str(kpis), "--out", str(diag)],
    )
    assert res.exit_code == 0, res.output
    assert diag.exists()
    payload = json.loads(diag.read_text(encoding="utf-8"))
    assert "_network" in payload


def test_cli_segment_produces_archetypes_and_segmented_parquet(tmp_path: Path):
    runner = CliRunner()
    parquet = tmp_path / "sales.parquet"
    runner.invoke(cli, ["ingest", "--source", str(SAMPLE), "--out", str(parquet)])
    out_parq = tmp_path / "sales_segmented.parquet"
    out_arch = tmp_path / "archetypes.json"
    res = runner.invoke(
        cli,
        [
            "segment",
            "--parquet", str(parquet),
            "--out-parquet", str(out_parq),
            "--out-archetypes", str(out_arch),
            "--n-clusters", "3",
        ],
    )
    assert res.exit_code == 0, res.output
    assert out_parq.exists()
    assert out_arch.exists()
    df = pd.read_parquet(out_parq)
    assert "segment_id" in df.columns
    payload = json.loads(out_arch.read_text(encoding="utf-8"))
    assert payload["n_archetypes"] == 3


def test_cli_refresh_runs_full_chain(tmp_path: Path):
    runner = CliRunner()
    parquet = tmp_path / "sales.parquet"
    archetypes = tmp_path / "archetypes.json"
    kpis = tmp_path / "kpis.json"
    diag = tmp_path / "diagnostics.json"
    res = runner.invoke(
        cli,
        [
            "refresh",
            "--source", str(SAMPLE),
            "--parquet", str(parquet),
            "--archetypes", str(archetypes),
            "--kpis", str(kpis),
            "--diagnostics", str(diag),
            "--n-clusters", "3",
        ],
    )
    assert res.exit_code == 0, res.output
    assert parquet.exists()
    assert archetypes.exists()
    assert kpis.exists()
    assert diag.exists()

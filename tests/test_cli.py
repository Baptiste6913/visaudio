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

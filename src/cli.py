"""Visaudio CLI — ingest and compute KPIs.

Usage:
    python -m src.cli ingest --source data/raw/modele_donnees_optique.xlsx \\
                             --out data/processed/sales.parquet
    python -m src.cli kpi --parquet data/processed/sales.parquet \\
                          --out data/processed/kpis.json
"""
from __future__ import annotations

from pathlib import Path

import click
import pandas as pd

from src.ingestion.excel_parser import read_visaudio_excel
from src.ingestion.normalization import normalize_dataframe, write_parquet
from src.kpi.pipeline import write_kpis_json


@click.group()
def cli() -> None:
    """Visaudio command-line interface."""


@cli.command()
@click.option(
    "--source",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the raw Excel file.",
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("data/processed/sales.parquet"),
    help="Path to the output Parquet.",
)
def ingest(source: Path, out: Path) -> None:
    """Read the raw Excel, normalize it, and write Parquet."""
    click.echo(f"Reading {source}…")
    raw = read_visaudio_excel(source)
    click.echo(f"Read {len(raw)} rows, {len(raw.columns)} columns.")
    normalized, rejected = normalize_dataframe(raw, return_rejected=True)
    click.echo(f"Validated {len(normalized)} rows. Rejected {len(rejected)}.")
    write_parquet(normalized, out)
    click.echo(f"Wrote Parquet: {out}")
    if len(rejected):
        rej_path = out.parent / "rejected_rows.json"
        rejected.to_json(rej_path, orient="records", date_format="iso")
        click.echo(f"Wrote rejected rows: {rej_path}")


@cli.command()
@click.option(
    "--parquet",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the normalized Parquet.",
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("data/processed/kpis.json"),
    help="Path to the output kpis.json.",
)
def kpi(parquet: Path, out: Path) -> None:
    """Load the Parquet and write kpis.json."""
    click.echo(f"Loading {parquet}…")
    df = pd.read_parquet(parquet)
    click.echo(f"Loaded {len(df)} rows.")
    write_kpis_json(df, out)
    click.echo(f"Wrote {out}")


if __name__ == "__main__":
    cli()

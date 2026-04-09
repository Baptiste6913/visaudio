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
from src.segmentation.pipeline import run_segmentation, write_archetypes_json
from src.rules.diagnostics import build_diagnostics_payload, write_diagnostics_json


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


@cli.command()
@click.option(
    "--parquet",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the normalized Parquet (from `ingest`).",
)
@click.option(
    "--out-parquet",
    type=click.Path(path_type=Path),
    default=Path("data/processed/sales.parquet"),
    help="Path to the output segmented Parquet (overwrites the input by default).",
)
@click.option(
    "--out-archetypes",
    type=click.Path(path_type=Path),
    default=Path("data/processed/archetypes.json"),
    help="Path to the output archetypes.json.",
)
@click.option(
    "--n-clusters",
    type=int,
    default=None,
    help="Number of clusters (default: auto by silhouette in [6, 10]).",
)
def segment(
    parquet: Path,
    out_parquet: Path,
    out_archetypes: Path,
    n_clusters: int | None,
) -> None:
    """Run K-Means segmentation and add `segment_id` to the Parquet."""
    click.echo(f"Loading {parquet}…")
    df = pd.read_parquet(parquet)
    click.echo(f"Loaded {len(df)} rows, {df['id_client'].nunique()} clients.")

    click.echo("Running segmentation…")
    df_seg, archetypes = run_segmentation(df, n_clusters=n_clusters)
    click.echo(
        f"Found {archetypes['n_archetypes']} archetypes. "
        f"Writing {out_parquet} and {out_archetypes}…"
    )

    from src.ingestion.normalization import write_parquet
    write_parquet(df_seg, out_parquet)
    write_archetypes_json(archetypes, out_archetypes)
    click.echo("Done.")


@cli.command()
@click.option(
    "--kpis",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to kpis.json (from `kpi`).",
)
@click.option(
    "--rules",
    type=click.Path(exists=True, path_type=Path),
    default=Path("src/rules/rules.yaml"),
    help="Path to rules.yaml.",
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("data/processed/diagnostics.json"),
    help="Path to the output diagnostics.json.",
)
def diagnose(kpis: Path, rules: Path, out: Path) -> None:
    """Evaluate rules against kpis.json and write diagnostics.json."""
    import json as _json

    click.echo(f"Loading {kpis}…")
    kpis_payload = _json.loads(kpis.read_text(encoding="utf-8"))
    payload = build_diagnostics_payload(kpis_payload, rules_path=rules)
    write_diagnostics_json(payload, out)
    # Report one-line summary
    stores = [k for k in payload if not k.startswith("_") and k != "generated_at"]
    total_findings = sum(len(payload[k]["findings"]) for k in stores)
    total_findings += len(payload.get("_network", {}).get("findings", []))
    click.echo(
        f"Wrote {out} — {len(stores)} stores, {total_findings} total findings."
    )


@cli.command()
@click.option("--parquet", type=click.Path(exists=True, path_type=Path), required=True,
              help="Path to the segmented Parquet (with segment_id).")
@click.option("--archetypes", type=click.Path(exists=True, path_type=Path), required=True,
              help="Path to archetypes.json.")
@click.option("--scenario", type=str, default="SC-BASE",
              help="Scenario ID (SC-BASE, SC-L2a, etc.).")
@click.option("--n-steps", type=int, default=36, help="Number of monthly steps.")
@click.option("--n-replications", type=int, default=20, help="Monte Carlo replications.")
@click.option("--seed", type=int, default=42)
@click.option("--out", type=click.Path(path_type=Path), default=None,
              help="Output JSON (default: data/processed/mesa_runs/<scenario>.json)")
def simulate(parquet, archetypes, scenario, n_steps, n_replications, seed, out):
    """Run a Mesa simulation scenario."""
    import json as _json
    from src.simulation.runner import run_scenario, write_run_result

    click.echo(f"Loading data\u2026")
    df = pd.read_parquet(parquet)
    arch_payload = _json.loads(archetypes.read_text(encoding="utf-8"))

    click.echo(f"Running {scenario} ({n_replications} reps \u00d7 {n_steps} months)\u2026")
    result = run_scenario(
        sales_df=df, archetypes_payload=arch_payload,
        scenario_id=scenario, n_steps=n_steps,
        n_replications=n_replications, seed=seed,
    )
    if out is None:
        out = Path(f"data/processed/mesa_runs/{scenario}.json")
    write_run_result(result, out)
    click.echo(f"Wrote {out}")
    click.echo(f"CA mean (month 1..{n_steps}): {result.ca_mean[0]:,.0f} \u2192 {result.ca_mean[-1]:,.0f}")


@cli.command()
@click.option(
    "--source",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the raw Excel file.",
)
@click.option(
    "--parquet",
    type=click.Path(path_type=Path),
    default=Path("data/processed/sales.parquet"),
)
@click.option(
    "--archetypes",
    type=click.Path(path_type=Path),
    default=Path("data/processed/archetypes.json"),
)
@click.option(
    "--kpis",
    type=click.Path(path_type=Path),
    default=Path("data/processed/kpis.json"),
)
@click.option(
    "--diagnostics",
    type=click.Path(path_type=Path),
    default=Path("data/processed/diagnostics.json"),
)
@click.option(
    "--n-clusters",
    type=int,
    default=None,
    help="Number of K-Means clusters (default: auto).",
)
@click.pass_context
def refresh(
    ctx: click.Context,
    source: Path,
    parquet: Path,
    archetypes: Path,
    kpis: Path,
    diagnostics: Path,
    n_clusters: int | None,
) -> None:
    """Run ingest → segment → kpi → diagnose in sequence."""
    ctx.invoke(ingest, source=source, out=parquet)
    ctx.invoke(
        segment,
        parquet=parquet,
        out_parquet=parquet,
        out_archetypes=archetypes,
        n_clusters=n_clusters,
    )
    ctx.invoke(kpi, parquet=parquet, out=kpis)
    ctx.invoke(
        diagnose,
        kpis=kpis,
        rules=Path("src/rules/rules.yaml"),
        out=diagnostics,
    )
    click.echo("Refresh complete.")


if __name__ == "__main__":
    cli()

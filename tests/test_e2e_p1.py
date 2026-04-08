"""End-to-end P1 pipeline test on data/samples/sample_500.xlsx.

Verifies the full chain: Excel → Parquet → kpis.json, with sanity
assertions on the magnitudes of key outputs.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.excel_parser import read_visaudio_excel
from src.ingestion.normalization import normalize_dataframe, write_parquet
from src.kpi.pipeline import build_kpis_payload, write_kpis_json


SAMPLE = Path("data/samples/sample_500.xlsx")


def test_e2e_ingestion(tmp_path: Path):
    raw = read_visaudio_excel(SAMPLE)
    assert len(raw) == 500
    df, rejected = normalize_dataframe(raw, return_rejected=True)
    # Accept a small rejection rate but not a catastrophe
    assert len(df) >= 450, f"Too many rejected rows: {len(rejected)}"
    assert df["ca_ht_article"].sum() > 0


def test_e2e_parquet_roundtrip(tmp_path: Path):
    raw = read_visaudio_excel(SAMPLE)
    df = normalize_dataframe(raw)
    out = tmp_path / "sales.parquet"
    write_parquet(df, out)
    loaded = pd.read_parquet(out)
    assert len(loaded) == len(df)
    assert loaded["ca_ht_article"].sum() == pytest.approx(
        df["ca_ht_article"].sum()
    )


def test_e2e_kpi_payload_sanity(tmp_path: Path):
    raw = read_visaudio_excel(SAMPLE)
    df = normalize_dataframe(raw)
    payload = build_kpis_payload(df)

    # meta
    assert payload["meta"]["n_rows"] == len(df)

    # cadrage (keys per spec §5.4)
    assert payload["cadrage"]["ca_total"] > 0
    assert len(payload["cadrage"]["par_magasin"]) >= 1
    assert isinstance(payload["cadrage"]["par_mois"], list)

    # hero
    assert payload["hero"]["opportunite_upsell_annuelle"] >= 0
    assert isinstance(payload["hero"]["opportunite_par_magasin"], dict)
    assert isinstance(payload["hero"]["opportunite_par_segment"], list)


def test_e2e_json_writable(tmp_path: Path):
    raw = read_visaudio_excel(SAMPLE)
    df = normalize_dataframe(raw)
    out = tmp_path / "kpis.json"
    write_kpis_json(df, out)
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["cadrage"]["ca_total"] > 0

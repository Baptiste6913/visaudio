import json
from pathlib import Path

import pandas as pd
import pytest

from src.kpi.pipeline import build_kpis_payload, write_kpis_json


def test_build_kpis_payload_has_required_sections(tiny_sales):
    payload = build_kpis_payload(tiny_sales)
    assert set(payload.keys()) >= {
        "meta",
        "cadrage",
        "hero",
        "retention",
        "benchmark",
        "conventionnement",
        "diagnostic_signals",
    }


def test_meta_is_populated(tiny_sales):
    payload = build_kpis_payload(tiny_sales)
    assert payload["meta"]["n_rows"] == len(tiny_sales)
    assert payload["meta"]["n_clients"] == tiny_sales["id_client"].nunique()
    assert payload["meta"]["data_period"]["start"].startswith("2024")
    assert payload["meta"]["data_period"]["end"].startswith("2024")


def test_hero_opportunite_is_present_and_non_negative(tiny_sales):
    payload = build_kpis_payload(tiny_sales)
    hero = payload["hero"]
    assert "opportunite_upsell_annuelle" in hero
    assert hero["opportunite_upsell_annuelle"] >= 0
    assert "opportunite_par_magasin" in hero
    assert "opportunite_par_segment" in hero


def test_write_kpis_json_roundtrip(tiny_sales, tmp_path: Path):
    out = tmp_path / "kpis.json"
    write_kpis_json(tiny_sales, out)
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert "cadrage" in loaded
    assert "hero" in loaded


def test_pipeline_uses_segment_id_when_present(tiny_sales):
    df = tiny_sales.copy()
    # Simulate a segmented Parquet: assign segment_id 0/1 per client_id parity
    df["segment_id"] = df["id_client"] % 2
    payload = build_kpis_payload(df)
    assert payload["hero"]["segment_column_used"] == "segment_id"


def test_pipeline_falls_back_to_tranche_age(tiny_sales):
    # tiny_sales fixture has no segment_id column
    payload = build_kpis_payload(tiny_sales)
    assert payload["hero"]["segment_column_used"] == "tranche_age"

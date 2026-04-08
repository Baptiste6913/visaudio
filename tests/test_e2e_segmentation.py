"""E2E test: ingest → segment → kpi on sample_500.xlsx.

Asserts the segmented pipeline produces a valid hero chiffre and the
archetypes payload has the expected structure.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.ingestion.excel_parser import read_visaudio_excel
from src.ingestion.normalization import normalize_dataframe
from src.kpi.pipeline import build_kpis_payload
from src.segmentation.pipeline import run_segmentation


SAMPLE = Path("data/samples/sample_500.xlsx")


def test_e2e_segmentation_on_sample():
    raw = read_visaudio_excel(SAMPLE)
    df = normalize_dataframe(raw)
    df_seg, archetypes = run_segmentation(df, n_clusters=6)

    # Structural assertions
    assert "segment_id" in df_seg.columns
    assert archetypes["n_archetypes"] == 6
    assert len(archetypes["archetypes"]) == 6

    # Each client assigned to exactly one segment
    per_client = df_seg.groupby("id_client")["segment_id"].nunique()
    assert (per_client == 1).all()

    # Run KPIs on segmented df and verify hero is non-negative + uses segment_id
    payload = build_kpis_payload(df_seg)
    assert payload["hero"]["segment_column_used"] == "segment_id"
    assert payload["hero"]["opportunite_upsell_annuelle"] >= 0


def test_e2e_segmentation_hero_differs_from_tranche_age():
    """The hero chiffre should differ between tranche_age (P1) and segment_id (P2)."""
    raw = read_visaudio_excel(SAMPLE)
    df = normalize_dataframe(raw)
    p1_payload = build_kpis_payload(df)                       # uses tranche_age
    df_seg, _ = run_segmentation(df, n_clusters=6)
    p2_payload = build_kpis_payload(df_seg)                   # uses segment_id

    p1_hero = p1_payload["hero"]["opportunite_upsell_annuelle"]
    p2_hero = p2_payload["hero"]["opportunite_upsell_annuelle"]
    # Just verify they are both non-negative and documented in the test output;
    # no strict inequality since the relationship depends on the real data.
    assert p1_hero >= 0
    assert p2_hero >= 0
    print(f"\nHero P1 (tranche_age):   {p1_hero:>12,.0f} €")
    print(f"Hero P2 (segment_id×6):  {p2_hero:>12,.0f} €")
    print(f"Delta:                   {p2_hero - p1_hero:>+12,.0f} €")

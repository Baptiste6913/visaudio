import json
from pathlib import Path

import pandas as pd
import pytest

from src.segmentation.pipeline import (
    build_archetypes_payload,
    run_segmentation,
    write_archetypes_json,
)


def test_build_archetypes_payload_shape(synthetic_sales):
    payload = build_archetypes_payload(synthetic_sales, n_clusters=3)
    assert payload["n_archetypes"] == 3
    assert len(payload["archetypes"]) == 3
    for arch in payload["archetypes"]:
        assert set(arch.keys()) >= {
            "id",
            "label",
            "n_clients",
            "share_of_clients",
            "share_of_ca",
            "centroid",
        }
        assert isinstance(arch["centroid"], dict)


def test_archetype_ids_are_sequential(synthetic_sales):
    payload = build_archetypes_payload(synthetic_sales, n_clusters=3)
    ids = [a["id"] for a in payload["archetypes"]]
    assert ids == list(range(3))


def test_shares_sum_to_one(synthetic_sales):
    payload = build_archetypes_payload(synthetic_sales, n_clusters=3)
    total_clients = sum(a["share_of_clients"] for a in payload["archetypes"])
    total_ca = sum(a["share_of_ca"] for a in payload["archetypes"])
    assert total_clients == pytest.approx(1.0)
    assert total_ca == pytest.approx(1.0)


def test_run_segmentation_adds_segment_id_column(synthetic_sales):
    df_with_segment, archetypes = run_segmentation(
        synthetic_sales, n_clusters=3
    )
    assert "segment_id" in df_with_segment.columns
    # Every original row has a segment_id
    assert df_with_segment["segment_id"].notna().all()
    # Each client has exactly one segment_id
    per_client = df_with_segment.groupby("id_client")["segment_id"].nunique()
    assert (per_client == 1).all()
    assert isinstance(archetypes, dict)


def test_write_archetypes_json_roundtrip(synthetic_sales, tmp_path: Path):
    _, archetypes = run_segmentation(synthetic_sales, n_clusters=3)
    out = tmp_path / "archetypes.json"
    write_archetypes_json(archetypes, out)
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["n_archetypes"] == 3

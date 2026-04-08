"""Segmentation pipeline — Parquet → archetypes.json + segmented Parquet."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.segmentation.features import build_client_features
from src.segmentation.kmeans import fit_kmeans, pick_k_by_silhouette
from src.segmentation.labels import sort_and_label_archetypes


def run_segmentation(
    df: pd.DataFrame,
    n_clusters: int | None = None,
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict]:
    """Run the full segmentation on a sales DataFrame.

    Args:
        df: normalized sales DataFrame (from P1).
        n_clusters: if None, auto-pick in [6, 10] by silhouette.
        random_state: for reproducibility.

    Returns:
        (df_with_segment_id, archetypes_payload)
        - df_with_segment_id: copy of df with a `segment_id` int column joined
          on id_client
        - archetypes_payload: the JSON-ready archetypes dict (see spec §6.3)
    """
    feats = build_client_features(df)

    if n_clusters is None:
        # Cap upper bound at min(10, n_clients // 20) for real-world safety;
        # ensure at least k_min is used.
        k_max = max(6, min(10, len(feats) // 20))
        n_clusters = pick_k_by_silhouette(
            feats, k_min=6, k_max=k_max, random_state=random_state
        )

    result = fit_kmeans(feats, n_clusters=n_clusters, random_state=random_state)
    labels_original = result["labels"]        # indexed by id_client, values 0..k-1 (original sklearn)
    centroids_original = result["centroids"]  # rows indexed 0..k-1

    # Sort clusters by panier_moyen descending; new ids 0..k-1
    sorted_labelled = sort_and_label_archetypes(centroids_original)

    # Build the remapping original_cluster_id → new segment_id
    remap = {
        int(row["original_cluster_id"]): int(new_id)
        for new_id, row in sorted_labelled.iterrows()
    }
    segment_id_per_client = labels_original.map(remap).astype("int64")
    segment_id_per_client.name = "segment_id"

    # Join the per-client segment_id back onto the row-level df
    df_out = df.copy()
    df_out["segment_id"] = df_out["id_client"].map(segment_id_per_client).astype("int64")

    archetypes_payload = build_archetypes_payload_from_artifacts(
        df=df,
        segment_id_per_client=segment_id_per_client,
        sorted_centroids=sorted_labelled,
        n_clusters=n_clusters,
    )
    return df_out, archetypes_payload


def build_archetypes_payload_from_artifacts(
    df: pd.DataFrame,
    segment_id_per_client: pd.Series,
    sorted_centroids: pd.DataFrame,
    n_clusters: int,
) -> dict:
    """Assemble the archetypes JSON payload (spec §6.3)."""
    # Client counts per new segment
    counts = segment_id_per_client.value_counts().sort_index()
    total_clients = int(counts.sum())

    # Share of CA per segment
    client_to_segment = segment_id_per_client.to_dict()
    df_seg = df.assign(
        segment_id=df["id_client"].map(client_to_segment).astype("int64")
    )
    ca_per_seg = df_seg.groupby("segment_id")["ca_ht_article"].sum()
    total_ca = float(ca_per_seg.sum())

    archetypes = []
    for seg_id, row in sorted_centroids.iterrows():
        centroid_dict = {
            col: float(row[col])
            for col in row.index
            if col not in ("label", "original_cluster_id")
        }
        archetypes.append(
            {
                "id": int(seg_id),
                "label": str(row["label"]),
                "n_clients": int(counts.get(seg_id, 0)),
                "share_of_clients": float(counts.get(seg_id, 0)) / max(total_clients, 1),
                "share_of_ca": float(ca_per_seg.get(seg_id, 0.0)) / max(total_ca, 1e-9),
                "centroid": centroid_dict,
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_archetypes": int(n_clusters),
        "archetypes": archetypes,
    }


def build_archetypes_payload(
    df: pd.DataFrame, n_clusters: int | None = None, random_state: int = 42
) -> dict:
    """Convenience wrapper: run segmentation and return the archetypes payload only."""
    _, payload = run_segmentation(df, n_clusters=n_clusters, random_state=random_state)
    return payload


def write_archetypes_json(payload: dict, path: Path | str) -> None:
    """Serialize the archetypes payload to a JSON file.

    Args:
        payload: the archetypes dict produced by build_archetypes_payload.
        path: destination file path (created with parents if needed).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

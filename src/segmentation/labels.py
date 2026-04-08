"""Convert K-Means centroids into human-readable archetype labels."""
from __future__ import annotations

import pandas as pd


AGE_BUCKETS = [
    (0, 30, "<30"),
    (30, 45, "30-45"),
    (45, 60, "45-60"),
    (60, 75, "60-75"),
    (75, 200, "75+"),
]


def _age_bucket(age: float) -> str:
    for lo, hi, label in AGE_BUCKETS:
        if lo <= age < hi:
            return label
    return "75+"


def _conv_flag(conv_libre_share: float) -> str:
    return "LIBRE" if conv_libre_share >= 0.5 else "NON-LIBRE"


def _premium_flag(part_premium: float) -> str:
    if part_premium >= 0.5:
        return "premium"
    if part_premium >= 0.2:
        return "mixte"
    return "essentiel"


def label_archetype_from_centroid(centroid: pd.Series) -> str:
    """Produce a short human label from one centroid vector.

    Format: '<age_bucket> <LIBRE|NON-LIBRE> <premium|mixte|essentiel>'
    """
    age = _age_bucket(float(centroid["age_dernier_achat"]))
    conv = _conv_flag(float(centroid["conventionnement_libre"]))
    prem = _premium_flag(float(centroid["part_premium_plus"]))
    return f"{age} {conv} {prem}"


def sort_and_label_archetypes(centroids: pd.DataFrame) -> pd.DataFrame:
    """Sort centroids by panier_moyen descending and attach a label.

    Returns a new DataFrame with:
      - the original centroid columns
      - `original_cluster_id`: the sklearn cluster index before sorting
      - `label`: the human-readable label
      - index = new cluster id (0..k-1)
    """
    sorted_idx = centroids["panier_moyen"].sort_values(ascending=False).index
    out = centroids.loc[sorted_idx].copy()
    out["original_cluster_id"] = out.index
    out = out.reset_index(drop=True)
    out.index.name = "segment_id"
    out["label"] = out.apply(label_archetype_from_centroid, axis=1)
    return out

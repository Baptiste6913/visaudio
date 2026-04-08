"""Convert K-Means centroids into human-readable archetype labels.

The label combines five axes observed to be the real distinguishers
K-Means produces on the Visaudio dataset:

  - age bucket
  - panier tier (premium if mean ticket ≥ 200 € OR part_premium_plus ≥ 50 %)
  - sex split (femmes ≥ 80 %, hommes ≤ 20 %, mixte otherwise)
  - conv flag (LIBRE when cluster is majority LIBRE, else NON-LIBRE)
  - loyalty flag ("fidèle" when n_achats ≥ 2.5 AND mois_entre ≥ 10)

Rationale: the heuristic used in P1 (age × conv × part_premium_plus) gave
5 out of 6 clusters the same label on real data because the age and
premium axes are nearly constant network-wide. Sex and loyalty turned out
to be the axes along which K-Means actually splits clients.
"""
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


def _panier_tier(panier: float, part_premium_plus: float) -> str:
    if part_premium_plus >= 0.5 or panier >= 200:
        return "premium"
    if panier >= 80:
        return "mid"
    return "bas"


def _sex_flag(sex_femme: float) -> str:
    if sex_femme >= 0.8:
        return "femmes"
    if sex_femme <= 0.2:
        return "hommes"
    return "mixte"


def _conv_flag(conv_libre_share: float) -> str:
    return "LIBRE" if conv_libre_share >= 0.5 else "NON-LIBRE"


def _loyalty_flag(n_achats_totaux: float, mois_entre_achats: float) -> str:
    """Return 'fidèle' when the cluster shows a clear repeat-purchase pattern."""
    if n_achats_totaux >= 2.5 and mois_entre_achats >= 10.0:
        return "fidèle"
    return ""


def label_archetype_from_centroid(centroid: pd.Series) -> str:
    """Produce a short human label from one centroid vector.

    Format: '<age> <panier_tier> <sex> <conv> [fidèle]'
    Example: '60-75 premium mixte LIBRE', '45-60 mid femmes NON-LIBRE fidèle'
    """
    age = _age_bucket(float(centroid["age_dernier_achat"]))
    panier = _panier_tier(
        float(centroid["panier_moyen"]),
        float(centroid["part_premium_plus"]),
    )
    sex = _sex_flag(float(centroid["sexe_Femme"]))
    conv = _conv_flag(float(centroid["conventionnement_libre"]))
    loyalty = _loyalty_flag(
        float(centroid["n_achats_totaux"]),
        float(centroid["mois_entre_achats"]),
    )
    parts = [age, panier, sex, conv]
    if loyalty:
        parts.append(loyalty)
    return " ".join(parts)


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

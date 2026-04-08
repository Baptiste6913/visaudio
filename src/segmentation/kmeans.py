"""K-Means clustering on client features with silhouette-based k selection.

Uses sklearn KMeans with StandardScaler preprocessing. Centroids are
returned in the original (unscaled) feature space for interpretability.
Deterministic when random_state is set.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def fit_kmeans(
    feats: pd.DataFrame,
    n_clusters: int,
    random_state: int = 42,
) -> dict[str, Any]:
    """Fit K-Means on standardized features.

    Args:
        feats: client-level feature DataFrame (one row per client).
        n_clusters: number of clusters to fit.
        random_state: for reproducibility.

    Returns:
        {
          "labels":      pd.Series of cluster labels, indexed by id_client,
          "centroids":   pd.DataFrame of centroids in original feature space,
          "n_clusters":  int,
          "inertia":     float (within-cluster sum of squares),
          "silhouette":  float or None (None when n_clusters >= n_samples),
        }
    """
    X = feats.to_numpy(dtype=float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels_arr = km.fit_predict(Xs)

    # Un-scale centroids back to original feature space
    centroids_unscaled = scaler.inverse_transform(km.cluster_centers_)
    centroids_df = pd.DataFrame(centroids_unscaled, columns=feats.columns)

    labels = pd.Series(labels_arr, index=feats.index, name="segment_id")

    sil: float | None
    if n_clusters >= len(feats) or len(set(labels_arr)) < 2:
        sil = None
    else:
        # Subsample on large datasets: silhouette_score allocates an
        # O(n^2) distance matrix otherwise — ~3 GiB at 20K clients.
        sample_size = min(2000, len(feats))
        sil = float(
            silhouette_score(
                Xs, labels_arr, sample_size=sample_size, random_state=random_state
            )
        )

    return {
        "labels": labels,
        "centroids": centroids_df,
        "n_clusters": int(n_clusters),
        "inertia": float(km.inertia_),
        "silhouette": sil,
    }


def pick_k_by_silhouette(
    feats: pd.DataFrame,
    k_min: int = 6,
    k_max: int = 10,
    random_state: int = 42,
) -> int:
    """Pick the best k in [k_min, k_max] by silhouette score.

    Caps k_max at (n_clients - 1) to avoid degenerate fits on tiny datasets.
    Returns k_min if no valid silhouette can be computed.
    """
    n = len(feats)
    k_max_eff = min(k_max, max(k_min, n - 1))
    best_k = k_min
    best_score = -1.0
    for k in range(k_min, k_max_eff + 1):
        if k >= n:
            break
        res = fit_kmeans(feats, n_clusters=k, random_state=random_state)
        if res["silhouette"] is None:
            continue
        if res["silhouette"] > best_score:
            best_score = res["silhouette"]
            best_k = k
    return int(best_k)

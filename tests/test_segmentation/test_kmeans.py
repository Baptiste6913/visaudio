import numpy as np
import pandas as pd
import pytest

from src.segmentation.features import FEATURE_NAMES, build_client_features
from src.segmentation.kmeans import fit_kmeans, pick_k_by_silhouette


def test_fit_returns_labels_matching_input_length(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    res = fit_kmeans(feats, n_clusters=3, random_state=42)
    assert len(res["labels"]) == len(feats)
    assert res["n_clusters"] == 3
    assert set(res["labels"].unique()) <= {0, 1, 2}


def test_fit_is_deterministic(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    r1 = fit_kmeans(feats, n_clusters=3, random_state=42)
    r2 = fit_kmeans(feats, n_clusters=3, random_state=42)
    assert (r1["labels"] == r2["labels"]).all()


def test_fit_exposes_centroids_in_feature_space(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    res = fit_kmeans(feats, n_clusters=3, random_state=42)
    # Centroids are in the ORIGINAL (unscaled) feature space for interpretability
    assert set(res["centroids"].columns) == set(feats.columns)
    assert len(res["centroids"]) == 3


def test_pick_k_returns_integer_in_valid_range(synthetic_sales):
    feats = build_client_features(synthetic_sales)
    # With only 5 clients, range should be capped
    k = pick_k_by_silhouette(feats, k_min=2, k_max=4, random_state=42)
    assert isinstance(k, int)
    assert 2 <= k <= 4

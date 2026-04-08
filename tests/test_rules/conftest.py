"""Shared fixtures for rules engine tests."""
from __future__ import annotations

import pytest


@pytest.fixture
def store_context_avranches() -> dict:
    """Context dict simulating per-store KPI values for Avranches."""
    return {
        "ville": "Avranches",
        "ca_total": 1_300_000.0,
        "panier_moyen": 188.0,
        "mix_essentiel": 0.50,
        "mix_premium_plus": 0.18,
        "ratio_monture_verre": 0.21,
        "part_clients_60_plus": 0.45,
        "network_mix_essentiel": 0.32,
        "network_ratio_monture_verre": 0.32,
    }


@pytest.fixture
def network_context() -> dict:
    return {
        "ca_total": 9_100_000.0,
        "hhi_conventionnement": 3_200.0,
        "exposition_top3": 0.62,
        "n_clients": 21_000,
    }

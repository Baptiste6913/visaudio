"""Tests for src.simulation.metrics — post-processing of sales_log."""
from __future__ import annotations

import pytest

from src.simulation.metrics import extract_monthly_metrics


def test_extract_returns_expected_keys():
    sales_log = [
        {"step": 1, "store": "Avranches", "gamme": "PREMIUM", "ticket": 200.0,
         "client_id": 1, "archetype_id": 0, "conventionnement": "LIBRE", "age": 50},
    ]
    metrics = extract_monthly_metrics(sales_log, n_steps=3)
    assert "ca_reseau" in metrics
    assert "ca_par_magasin" in metrics
    assert "mix_gamme_reseau" in metrics
    assert "panier_moyen" in metrics
    assert "n_transactions" in metrics
    assert len(metrics["ca_reseau"]) == 3


def test_ca_matches_sum_of_tickets():
    sales_log = [
        {"step": 1, "store": "A", "gamme": "ESSENTIEL", "ticket": 100.0,
         "client_id": 1, "archetype_id": 0, "conventionnement": "LIBRE", "age": 50},
        {"step": 1, "store": "A", "gamme": "PREMIUM", "ticket": 250.0,
         "client_id": 2, "archetype_id": 0, "conventionnement": "CSS", "age": 45},
    ]
    metrics = extract_monthly_metrics(sales_log, n_steps=1)
    assert metrics["ca_reseau"][0] == pytest.approx(350.0)


def test_empty_log():
    metrics = extract_monthly_metrics([], n_steps=3)
    assert metrics["ca_reseau"] == [0.0, 0.0, 0.0]
    assert metrics["n_transactions"] == [0, 0, 0]

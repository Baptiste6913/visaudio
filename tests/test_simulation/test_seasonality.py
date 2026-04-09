"""Tests for seasonality extraction — P3 Task 2."""
from __future__ import annotations

import pytest

from src.simulation.seasonality import compute_seasonality


def test_returns_12_months(mini_sales):
    s = compute_seasonality(mini_sales)
    assert len(s) == 12
    assert set(s.keys()) == set(range(1, 13))


def test_mean_is_one(mini_sales):
    s = compute_seasonality(mini_sales)
    mean = sum(s.values()) / 12
    assert mean == pytest.approx(1.0, abs=0.01)


def test_all_positive(mini_sales):
    s = compute_seasonality(mini_sales)
    for v in s.values():
        assert v > 0


def test_months_without_data_get_floor(mini_sales):
    """Months with no sales should get a floor value, not zero."""
    s = compute_seasonality(mini_sales)
    for v in s.values():
        assert v >= 0.1


def test_months_with_sales_are_higher(mini_sales):
    """Months that have actual sales should have coefficient > floor."""
    s = compute_seasonality(mini_sales)
    # mini_sales has data in months 1, 2, 3, 5, 6 — at least some > floor
    active_months = mini_sales["date_facture"].dt.month.unique()
    max_coeff = max(s[m] for m in active_months)
    assert max_coeff > 0.5

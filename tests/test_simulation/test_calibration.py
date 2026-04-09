"""Tests for calibration utilities (pure functions only)."""
from __future__ import annotations

import pandas as pd
import pytest
from src.simulation.calibration import (
    split_train_test,
    compute_tolerance_report,
    ToleranceReport,
)


def test_split_train_test(mini_sales):
    train, test = split_train_test(mini_sales, train_end_year=2023)
    assert len(train) > 0
    # mini_sales has dates in 2023-2024
    if len(test) > 0:
        assert test["date_facture"].dt.year.min() >= 2024


def test_split_all_train_if_cutoff_high(mini_sales):
    train, test = split_train_test(mini_sales, train_end_year=2025)
    assert len(train) == len(mini_sales)
    assert len(test) == 0


def test_tolerance_report_structure():
    actual = {"Avranches": 1_000_000.0, "Rampan": 500_000.0}
    simulated = {"Avranches": 1_040_000.0, "Rampan": 480_000.0}
    report = compute_tolerance_report(actual, simulated, tolerance_pct=5.0)
    assert isinstance(report, ToleranceReport)
    assert len(report.store_results) == 2
    assert isinstance(report.all_within_tolerance, bool)


def test_tolerance_passes_within_5pct():
    actual = {"A": 100.0}
    simulated = {"A": 103.0}
    report = compute_tolerance_report(actual, simulated, tolerance_pct=5.0)
    assert report.all_within_tolerance is True


def test_tolerance_fails_outside_5pct():
    actual = {"A": 100.0}
    simulated = {"A": 120.0}
    report = compute_tolerance_report(actual, simulated, tolerance_pct=5.0)
    assert report.all_within_tolerance is False


def test_zero_actual_handled():
    actual = {"A": 0.0}
    simulated = {"A": 0.0}
    report = compute_tolerance_report(actual, simulated, tolerance_pct=5.0)
    assert report.all_within_tolerance is True

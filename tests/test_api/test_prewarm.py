"""Tests for scenario pre-warming — P4 Task 5."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.api.prewarm import prewarm_scenarios, PREWARM_SCENARIOS


def test_prewarm_scenarios_list():
    assert len(PREWARM_SCENARIOS) == 7
    assert "SC-BASE" in PREWARM_SCENARIOS
    assert "SC-L2a" in PREWARM_SCENARIOS


def test_prewarm_skips_when_files_missing(tmp_path):
    """Should not crash when parquet/archetypes are missing."""
    prewarm_scenarios(data_dir=tmp_path)
    # No crash = pass


def test_prewarm_writes_cache_files(tmp_path):
    cache_dir = tmp_path / "mesa_runs"
    cache_dir.mkdir()

    mock_result_dict = {
        "scenario_id": "SC-BASE", "n_replications": 2, "n_steps": 3,
        "months": [1, 2, 3], "ca_mean": [100.0, 100.0, 100.0],
        "ca_lower": [90.0, 90.0, 90.0], "ca_upper": [110.0, 110.0, 110.0],
        "ca_par_magasin_mean": {}, "mix_gamme_mean": {},
        "panier_moyen_mean": [100.0, 100.0, 100.0],
        "n_transactions_mean": [10.0, 10.0, 10.0],
    }

    with patch("src.api.prewarm.run_scenario") as mock_run, \
         patch("src.api.prewarm.asdict", return_value=mock_result_dict), \
         patch("src.api.prewarm.pd") as mock_pd, \
         patch("src.api.prewarm.json") as mock_json:
        # Make file checks pass
        (tmp_path / "sales.parquet").touch()
        (tmp_path / "archetypes.json").write_text("{}", encoding="utf-8")
        mock_pd.read_parquet.return_value = MagicMock()
        mock_json.loads.return_value = {}

        mock_run.return_value = MagicMock()
        prewarm_scenarios(data_dir=tmp_path, n_steps=3, n_replications=2)

    json_files = list(cache_dir.glob("*.json"))
    assert len(json_files) == 7

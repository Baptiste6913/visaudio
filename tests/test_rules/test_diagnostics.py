import json
from pathlib import Path

import pytest

from src.rules.diagnostics import (
    build_diagnostics_payload,
    build_store_context,
    write_diagnostics_json,
)


# Minimal synthetic kpis dict with two villes
KPIS = {
    "meta": {"n_rows": 1000, "n_clients": 200},
    "cadrage": {
        "ca_total": 1_800_000.0,
        "par_magasin": {"Avranches": 1_300_000.0, "Cherbourg-en-Cotentin": 500_000.0},
        "panier_moyen_par_magasin": {"Avranches": 188.0, "Cherbourg-en-Cotentin": 225.0},
    },
    "hero": {
        "mix_gamme_par_magasin": {
            "Avranches": {"ESSENTIEL": 0.50, "CONFORT": 0.22, "PREMIUM": 0.18, "PRESTIGE": 0.10},
            "Cherbourg-en-Cotentin": {"ESSENTIEL": 0.25, "CONFORT": 0.35, "PREMIUM": 0.25, "PRESTIGE": 0.15},
        },
        "mix_premium_plus_par_magasin": {"Avranches": 0.28, "Cherbourg-en-Cotentin": 0.40},
    },
    "diagnostic_signals": {
        "ratio_monture_verre_eur": {"Avranches": 0.21, "Cherbourg-en-Cotentin": 0.35},
        "part_clients_60_plus": 0.45,
    },
    "conventionnement": {
        "hhi": 3_200.0,
        "exposition_top3": 0.62,
    },
}


def test_build_store_context_for_avranches():
    ctx = build_store_context("Avranches", KPIS)
    assert ctx["ville"] == "Avranches"
    assert ctx["mix_essentiel"] == 0.50
    assert ctx["ratio_monture_verre"] == 0.21
    # Network reference values should be present
    assert "network_mix_essentiel" in ctx
    assert ctx["network_mix_essentiel"] == pytest.approx((0.50 + 0.25) / 2)


def test_build_diagnostics_payload_has_all_stores():
    from pathlib import Path
    payload = build_diagnostics_payload(KPIS, rules_path=Path("src/rules/rules.yaml"))
    # Should have per-store findings plus a network section
    assert "Avranches" in payload
    assert "Cherbourg-en-Cotentin" in payload
    assert "_network" in payload


def test_avranches_triggers_expected_rules():
    payload = build_diagnostics_payload(KPIS, rules_path=Path("src/rules/rules.yaml"))
    finding_ids = {f["id"] for f in payload["Avranches"]["findings"]}
    # mix_essentiel 0.50 > 0.45 and > 1.3 * 0.375 → fires
    assert "MIX_ESSENTIEL_EXCESS" in finding_ids
    # ratio_monture_verre 0.21 < 0.25 → fires
    assert "CROSS_SELL_MONTURE_LOW" in finding_ids


def test_cherbourg_triggers_nothing_store_level():
    payload = build_diagnostics_payload(KPIS, rules_path=Path("src/rules/rules.yaml"))
    assert payload["Cherbourg-en-Cotentin"]["findings"] == []


def test_network_findings_fire():
    payload = build_diagnostics_payload(KPIS, rules_path=Path("src/rules/rules.yaml"))
    ids = {f["id"] for f in payload["_network"]["findings"]}
    assert "CONVENTIONNEMENT_CONCENTRATION" in ids  # HHI 3200 > 2500
    assert "EXPOSITION_TOP3_EXCESS" in ids          # 0.62 > 0.60
    assert "PORTEFEUILLE_VIEILLISSANT" in ids        # 0.45 > 0.40 (network scalar)


def test_write_diagnostics_json(tmp_path: Path):
    payload = build_diagnostics_payload(KPIS, rules_path=Path("src/rules/rules.yaml"))
    out = tmp_path / "diagnostics.json"
    write_diagnostics_json(payload, out)
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert "Avranches" in loaded

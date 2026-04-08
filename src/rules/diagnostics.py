"""Diagnostics builder — evaluates all rules against a kpis payload.

Produces the diagnostics.json structure consumed by the dashboard Page 2
drill-down panel. Per-store findings are keyed by ville name; a special
`_network` key holds findings with scope="network".
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.rules.engine import evaluate_rule, load_rules_from_yaml
from src.rules.schema import Rule


def _mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def build_store_context(ville: str, kpis: dict) -> dict[str, Any]:
    """Assemble the context dict for one store from a kpis payload.

    This is the bridge between the flat KPI JSON and the flat namespace
    expected by the YAML rule conditions.
    """
    mix_matrix = kpis.get("hero", {}).get("mix_gamme_par_magasin", {})
    mix_ville = mix_matrix.get(ville, {})

    # Network averages across the per-store dicts we can observe
    all_mix_essentiel = [m.get("ESSENTIEL", 0.0) for m in mix_matrix.values()]

    signals = kpis.get("diagnostic_signals", {})
    ratio_per_ville = signals.get("ratio_monture_verre_eur", {})
    all_ratios = list(ratio_per_ville.values())

    return {
        "ville": ville,
        "ca_total": kpis.get("cadrage", {}).get("par_magasin", {}).get(ville, 0.0),
        "panier_moyen": kpis.get("cadrage", {}).get("panier_moyen_par_magasin", {}).get(ville, 0.0),
        "mix_essentiel": mix_ville.get("ESSENTIEL", 0.0),
        "mix_confort": mix_ville.get("CONFORT", 0.0),
        "mix_premium": mix_ville.get("PREMIUM", 0.0),
        "mix_prestige": mix_ville.get("PRESTIGE", 0.0),
        "mix_premium_plus": kpis.get("hero", {}).get("mix_premium_plus_par_magasin", {}).get(ville, 0.0),
        "ratio_monture_verre": ratio_per_ville.get(ville, 0.0),
        "part_clients_60_plus": signals.get("part_clients_60_plus", 0.0),
        "network_mix_essentiel": _mean(all_mix_essentiel),
        "network_ratio_monture_verre": _mean(all_ratios),
    }


def build_network_context(kpis: dict) -> dict[str, Any]:
    """Context for network-scope rules."""
    return {
        "ca_total": kpis.get("cadrage", {}).get("ca_total", 0.0),
        "n_clients": kpis.get("meta", {}).get("n_clients", 0),
        "hhi_conventionnement": kpis.get("conventionnement", {}).get("hhi", 0.0),
        "exposition_top3": kpis.get("conventionnement", {}).get("exposition_top3", 0.0),
        "part_clients_60_plus": kpis.get("diagnostic_signals", {}).get("part_clients_60_plus", 0.0),
    }


def _sort_by_severity(findings: list[dict]) -> list[dict]:
    """Order: critical, warning, info."""
    order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(findings, key=lambda f: order.get(f.get("severity", "info"), 3))


def build_diagnostics_payload(
    kpis: dict, rules_path: Path | str = Path("src/rules/rules.yaml")
) -> dict:
    """Build the full diagnostics payload from a kpis dict."""
    rules: list[Rule] = load_rules_from_yaml(rules_path)

    store_rules = [r for r in rules if r.scope == "store"]
    network_rules = [r for r in rules if r.scope == "network"]

    mix_matrix = kpis.get("hero", {}).get("mix_gamme_par_magasin", {})
    villes = sorted(mix_matrix.keys())

    out: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    for ville in villes:
        ctx = build_store_context(ville, kpis)
        findings: list[dict] = []
        for r in store_rules:
            f = evaluate_rule(r, ctx)
            if f is not None:
                findings.append(f)
        out[ville] = {"findings": _sort_by_severity(findings)}

    # Network section
    net_ctx = build_network_context(kpis)
    net_findings: list[dict] = []
    for r in network_rules:
        f = evaluate_rule(r, net_ctx)
        if f is not None:
            net_findings.append(f)
    out["_network"] = {"findings": _sort_by_severity(net_findings)}
    return out


def write_diagnostics_json(payload: dict, path: Path | str) -> None:
    """Serialize the diagnostics payload to a UTF-8 JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

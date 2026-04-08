from pathlib import Path

import pytest

from src.rules.engine import evaluate_rule, load_rules_from_yaml
from src.rules.schema import Rule, Severity


RULES_PATH = Path("src/rules/rules.yaml")


def test_load_rules_returns_non_empty_list():
    rules = load_rules_from_yaml(RULES_PATH)
    assert isinstance(rules, list)
    assert len(rules) >= 5
    assert all(isinstance(r, Rule) for r in rules)


def test_load_raises_on_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_rules_from_yaml(tmp_path / "does_not_exist.yaml")


def test_evaluate_triggers_mix_essentiel_excess(store_context_avranches):
    rule = Rule(
        id="MIX_ESSENTIEL_EXCESS",
        scope="store",
        severity=Severity.WARNING,
        condition="mix_essentiel > 0.45 and mix_essentiel > 1.3 * network_mix_essentiel",
        finding="Mix ESSENTIEL surreprésenté ({mix_essentiel:.0%} vs {network_mix_essentiel:.0%} réseau)",
        recommendation="Formation upsell",
    )
    finding = evaluate_rule(rule, store_context_avranches)
    assert finding is not None
    assert finding["id"] == "MIX_ESSENTIEL_EXCESS"
    assert finding["severity"] == "warning"
    assert "50%" in finding["message"]
    assert "32%" in finding["message"]


def test_evaluate_does_not_trigger_when_condition_false(store_context_avranches):
    rule = Rule(
        id="CROSS_SELL_MONTURE_LOW",
        scope="store",
        severity=Severity.CRITICAL,
        condition="ratio_monture_verre < 0.10",  # stricter than reality (0.21)
        finding="should not trigger",
    )
    finding = evaluate_rule(rule, store_context_avranches)
    assert finding is None


def test_evaluate_handles_missing_context_key():
    rule = Rule(
        id="BOOM",
        scope="store",
        severity=Severity.INFO,
        condition="inexistant > 0",
        finding="x",
    )
    finding = evaluate_rule(rule, {"ville": "X"})
    # Missing key → rule does not fire, does not crash
    assert finding is None

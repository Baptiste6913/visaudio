"""Rules engine — loads YAML rules and evaluates them against a context.

Condition evaluation uses Python's `eval()` with a restricted globals dict
to keep the rule expressions simple while preventing accidental access to
the host environment. Users authoring rules are trusted (rules.yaml is
part of the repo).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.rules.schema import Rule, Severity


def load_rules_from_yaml(path: Path | str) -> list[Rule]:
    """Load a list of rules from a YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"Expected a list of rules in {path}, got {type(raw).__name__}")
    return [Rule.model_validate(r) for r in raw]


def _safe_eval(expression: str, context: dict[str, Any]) -> bool | None:
    """Evaluate a condition expression in a restricted namespace.

    Returns True/False on success. Returns None if the context is missing
    a key referenced by the expression (interpreted as "rule does not fire").
    """
    # Restrict builtins: no __import__, no open, etc.
    safe_globals: dict[str, Any] = {"__builtins__": {}}
    try:
        return bool(eval(expression, safe_globals, context))
    except (NameError, KeyError):
        return None
    except (TypeError, ValueError):
        return None


def evaluate_rule(rule: Rule, context: dict[str, Any]) -> dict[str, Any] | None:
    """Evaluate one rule against a context.

    Returns:
        A finding dict if the rule fires, else None.
    """
    result = _safe_eval(rule.condition, context)
    if not result:
        return None
    try:
        message = rule.finding.format(**context)
    except (KeyError, IndexError, ValueError):
        message = rule.finding
    recommendation = None
    if rule.recommendation is not None:
        try:
            recommendation = rule.recommendation.format(**context)
        except (KeyError, IndexError, ValueError):
            recommendation = rule.recommendation
    return {
        "id": rule.id,
        "severity": rule.severity.value,
        "message": message,
        "recommendation": recommendation,
    }

import pytest
from pydantic import ValidationError

from src.rules.schema import Rule, Severity


VALID_RULE = {
    "id": "MIX_ESSENTIEL_EXCESS",
    "scope": "store",
    "severity": "warning",
    "condition": "mix_essentiel > 0.45",
    "finding": "Mix ESSENTIEL surreprésenté",
    "recommendation": "Formation upsell prioritaire",
}


def test_accepts_valid_rule():
    r = Rule.model_validate(VALID_RULE)
    assert r.id == "MIX_ESSENTIEL_EXCESS"
    assert r.severity == Severity.WARNING


def test_rejects_unknown_scope():
    bad = dict(VALID_RULE, scope="universe")
    with pytest.raises(ValidationError):
        Rule.model_validate(bad)


def test_rejects_unknown_severity():
    bad = dict(VALID_RULE, severity="nuclear")
    with pytest.raises(ValidationError):
        Rule.model_validate(bad)


def test_recommendation_is_optional():
    ok = {k: v for k, v in VALID_RULE.items() if k != "recommendation"}
    r = Rule.model_validate(ok)
    assert r.recommendation is None

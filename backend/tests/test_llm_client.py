"""Unit tests for LLM client (F21) — LLM_MODE=mock only, no network calls."""

import pytest

from app.models.graph import FraudType, RiskLevel
from app.services.llm_client import (
    Verdict,
    VerdictValidationError,
    _mock_classify,
    _rules_only_classify,
    classify,
    validate_verdict,
)

# ── Validation tests ─────────────────────────────────────────────────────────


def test_validate_confidence_out_of_range() -> None:
    v = Verdict(FraudType.other, RiskLevel.unknown, confidence=1.5, evidence=[])
    with pytest.raises(VerdictValidationError, match="confidence"):
        validate_verdict(v, "any text")


def test_validate_confidence_negative() -> None:
    v = Verdict(FraudType.other, RiskLevel.unknown, confidence=-0.1, evidence=[])
    with pytest.raises(VerdictValidationError, match="confidence"):
        validate_verdict(v, "any text")


def test_validate_evidence_not_in_text() -> None:
    v = Verdict(FraudType.other, RiskLevel.unknown, confidence=0.8, evidence=["not_here"])
    with pytest.raises(VerdictValidationError, match="evidence"):
        validate_verdict(v, "some other text")


def test_validate_passes_with_valid_verdict() -> None:
    text = "please send money for customs clearance"
    v = Verdict(FraudType.digital_arrest, RiskLevel.danger, confidence=0.9, evidence=["customs"])
    validate_verdict(v, text)  # should not raise


# ── Rules classifier tests ───────────────────────────────────────────────────


def test_rules_only_digital_arrest() -> None:
    v = _rules_only_classify("the CBI officer called and said you are under arrest")
    assert v.fraud_type == FraudType.digital_arrest
    assert v.risk == RiskLevel.danger
    assert v.degraded is True


def test_rules_only_investment_fraud() -> None:
    v = _rules_only_classify("guaranteed 40% ROI in crypto trading")
    assert v.fraud_type == FraudType.investment_fraud


def test_rules_only_job_fraud() -> None:
    v = _rules_only_classify("work from home earn 50000 per month vacancy")
    assert v.fraud_type == FraudType.job_fraud


def test_rules_only_other() -> None:
    v = _rules_only_classify("hello how are you")
    assert v.fraud_type == FraudType.other
    assert v.confidence == pytest.approx(0.3)


# ── Mock classify (mock mode, no network) ────────────────────────────────────


def test_mock_classify_returns_verdict() -> None:
    v = _mock_classify("you have been arrested for money laundering please pay")
    assert isinstance(v, Verdict)
    assert v.degraded is False  # mock pretends to be a real LLM


def test_classify_in_mock_mode(monkeypatch) -> None:
    monkeypatch.setattr("app.services.llm_client.settings.LLM_MODE", "mock")
    v = classify("invest now 200% profit guaranteed crypto")
    assert v.fraud_type == FraudType.investment_fraud
    assert 0.0 <= v.confidence <= 1.0


def test_classify_deterministic(monkeypatch) -> None:
    """Same input → same output (no randomness)."""
    monkeypatch.setattr("app.services.llm_client.settings.LLM_MODE", "mock")
    text = "customs officer arrested you send money"
    v1 = classify(text)
    v2 = classify(text)
    assert v1.fraud_type == v2.fraud_type
    assert v1.confidence == v2.confidence

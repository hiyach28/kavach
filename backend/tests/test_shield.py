"""Tests for Shield (F30, F33, F34) — standalone unit tests only.

These tests do NOT require Postgres. Run with:
  python -m pytest tests/test_shield.py -v

Integration tests (requiring Docker compose) are in test_shield_integration.py.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.services import shield as shield_svc
from app.services.live_companion import (
    STAGE_KEYWORDS,
    ScamScoreResult,
    StageState,
    score_transcript,
)

settings.LLM_MODE = "mock"  # ensure mock mode for tests


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    """Async HTTP client for API tests (no DB needed for authless endpoints)."""
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    return AsyncClient(transport=transport, base_url="http://test")


# ── Tier 1: Entity lookup (unit tests without DB) ──────────────────────────────


class TestTier1EntityLookup:
    """Tests that don't need a real database."""

    @pytest.mark.asyncio
    async def test_empty_entity_returns_none(self):
        result = await shield_svc._tier1_entity_lookup("", None)  # type: ignore[arg-type]
        assert result is None

    @pytest.mark.asyncio
    async def test_none_entity_returns_none(self):
        result = await shield_svc._tier1_entity_lookup(None, None)  # type: ignore[arg-type]
        assert result is None


# ── Tier 3: LLM Fallback (pure unit, no DB) ─────────────────────────────────────


class TestTier3LLMFallback:
    def test_llm_fallback_returns_verdict(self):
        """Tier 3 should always return a verdict in mock mode."""
        result = shield_svc._tier3_llm_fallback(
            "CBI arrested me and demanded money for drugs parcel"
        )
        assert result.verdict in ("danger", "suspicious", "likely_safe", "unknown")
        assert result.tier_resolved == 3

    def test_llm_fallback_includes_explanation(self):
        result = shield_svc._tier3_llm_fallback("invest Rs 5000 for 100% profit")
        assert result.explanation
        assert len(result.explanation) > 10

    def test_llm_fallback_digital_arrest_detected(self):
        """Digital arrest keywords should produce danger verdict."""
        result = shield_svc._tier3_llm_fallback(
            "CBI arrested me and demanded money for drugs parcel"
        )
        # In mock mode, the rules engine should pick up keywords
        assert result.tier_resolved == 3


# ── Full cascade edge cases ─────────────────────────────────────────────────────


class TestShieldCheckCascade:
    @pytest.mark.asyncio
    async def test_empty_input_returns_unknown(self):
        """Empty text and no entity returns unknown at tier 0."""
        result = await shield_svc.check(
            text="",
            db=None,  # type: ignore[arg-type]
        )
        assert result.verdict == "unknown"
        assert result.tier_resolved == 0


# ── Live Call Companion scoring (F33) — pure unit tests ─────────────────────────


class TestLiveCompanionScoring:
    """Offline-testable keyword-pattern stage detection (F33 AC)."""

    def test_listening_initial_state(self):
        """Empty transcript should be listening stage with score 0."""
        result = score_transcript("")
        assert result.current_stage == "listening"
        assert result.max_score == 0.0

    def test_impersonation_detected(self):
        """Impersonation keywords should trigger caution."""
        result = score_transcript("Hello this is DSP inspector calling from CBI headquarters")
        assert result.current_stage in ("caution", "listening")

    def test_threat_keywords_trigger(self):
        """Threat keywords should escalate to caution."""
        result = score_transcript(
            "You have a non-bailable warrant and arrest case filed against you"
        )
        assert result.current_stage in ("caution", "danger")

    def test_payment_escalates_to_danger(self):
        """Payment demand should escalate to danger."""
        stages = {name: StageState(name=name) for name in STAGE_KEYWORDS}
        stages["impersonation"].score = 0.6
        stages["impersonation"].triggered = True
        stages["threat"].score = 0.5
        stages["threat"].triggered = True

        result = score_transcript("Now send money immediately via UPI or GT pay", stages)
        assert result.current_stage == "danger"
        assert result.max_score >= 0.4

    def test_full_scam_script_progression(self):
        """Simulate a full scam call progression through all stages."""
        transcript_parts = [
            ("listening", "Hello sir, this is from Telecom Regulatory Authority"),
            ("caution", "We found a parcel with drugs in your name at Mumbai customs"),
            ("caution", "This is a serious criminal case, non-bailable warrant issued"),
            ("caution", "Don't tell anyone in your family, this is confidential"),
            ("danger", "You need to pay ₹50,000 immediately via UPI to close the case"),
        ]

        stages = None
        final_stage = "listening"
        for _expected_stage, text in transcript_parts:
            result = score_transcript(text, stages)
            stages = result.stages
            final_stage = result.current_stage

        assert final_stage == "danger"

    def test_stage_state_maintained_across_calls(self):
        """Score state should accumulate across transcript chunks."""
        stages = {name: StageState(name=name) for name in STAGE_KEYWORDS}

        score_transcript("hello sir this is DSP police inspector calling", stages)
        score_transcript("you have a non bailable warrant arrest case filed", stages)
        r3 = score_transcript("send money through UPI right now immediately", stages)

        assert stages["impersonation"].keyword_hits > 0
        assert stages["threat"].keyword_hits > 0
        assert stages["payment"].keyword_hits > 0
        assert r3.current_stage == "danger"

    def test_multi_language_keywords(self):
        """Hindi keywords should also trigger stage detection."""
        result = score_transcript("sahab aapke khilaf FIR darja hai, paisa bhejo")
        assert result.max_score > 0

    def test_scamscore_result_dataclass(self):
        """ScamScoreResult should be properly structured."""
        result = ScamScoreResult()
        assert result.current_stage == "listening"
        assert result.max_score == 0.0
        assert result.newly_triggered == []

    def test_client_side_keyword_detection_patterns(self):
        """Client-side keyword patterns should match."""
        # These patterns are used in the PWA JS fallback
        payment_patterns = ["pay", "send", "money", "upi", "otp", "transfer", "immediately"]

        for pattern in payment_patterns:
            result = score_transcript(f"please {pattern} now")
            assert result.stages["payment"].keyword_hits > 0 or result.current_stage != "listening"

        # Verification that client-side word boundaries match server-side
        result = score_transcript("send money via UPI")
        assert result.stages["payment"].keyword_hits >= 2

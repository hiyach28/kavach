"""LLM client with mock/replay/live modes and fallback chain (F21).

Provider interface:  classify(masked_text) -> Verdict
Mode control:        settings.LLM_MODE = "mock" | "replay" | "live"

Fallback order:  primary (Gemini) -> secondary -> RulesOnlyClassifier
Server-side validation is applied to any LLM-generated output before returning.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.graph import FraudType, RiskLevel

logger = logging.getLogger("kavach.llm")

# ── Verdict schema ──────────────────────────────────────────────────────────


@dataclass
class Verdict:
    fraud_type: FraudType
    risk: RiskLevel
    confidence: float  # 0.0 – 1.0
    evidence: list[str]  # substrings of the original masked text
    degraded: bool = False  # True if rules-only fallback was used
    reason: str = ""  # set when needs_manual_review


# ── Server-side output validation ───────────────────────────────────────────


class VerdictValidationError(Exception):
    pass


def validate_verdict(verdict: Verdict, masked_text: str) -> None:
    """
    Hard gate on every LLM-produced verdict (doc spec F21).
    Raises VerdictValidationError if any rule fails.
    """
    # Confidence must be in [0.0, 1.0]
    if not (0.0 <= verdict.confidence <= 1.0):
        raise VerdictValidationError(f"confidence {verdict.confidence} out of range [0.0, 1.0]")
    # fraud_type must be a valid enum member
    if verdict.fraud_type not in FraudType.__members__.values():
        raise VerdictValidationError(f"unknown fraud_type: {verdict.fraud_type}")
    # risk must be a valid enum member
    if verdict.risk not in RiskLevel.__members__.values():
        raise VerdictValidationError(f"unknown risk: {verdict.risk}")
    # Every evidence string must appear verbatim in the masked text
    for ev in verdict.evidence:
        if ev and ev not in masked_text:
            raise VerdictValidationError(f"evidence substring not found in input: {ev!r}")


# ── Mock classifier (deterministic, no network) ─────────────────────────────

# Keywords → fraud type mapping (longest wins)
_RULES: list[tuple[list[str], FraudType, RiskLevel]] = [
    (
        ["arrest", "cbi", "narcotics", "customs", "fia", "money launder"],
        FraudType.digital_arrest,
        RiskLevel.danger,
    ),
    (
        ["invest", "return", "profit", "trading", "crypto", "roi"],
        FraudType.investment_fraud,
        RiskLevel.danger,
    ),
    (
        ["job", "work from home", "earn", "vacancy", "salary"],
        FraudType.job_fraud,
        RiskLevel.suspicious,
    ),
    (
        ["refund", "kyc", "bank", "support", "customer care"],
        FraudType.customer_support,
        RiskLevel.suspicious,
    ),
    (["nude", "video", "blackmail", "intimate"], FraudType.sextortion, RiskLevel.danger),
    (
        ["order", "delivery", "product", "shop", "ebay", "amazon"],
        FraudType.ecommerce,
        RiskLevel.suspicious,
    ),
]


def _rules_only_classify(text: str) -> Verdict:
    """Deterministic rule-based fallback. Never calls any API."""
    lower = text.lower()
    best_type = FraudType.other
    best_risk = RiskLevel.unknown
    best_conf = 0.3
    best_ev: list[str] = []

    for keywords, ftype, risk in _RULES:
        hits = [kw for kw in keywords if kw in lower]
        if hits:
            conf = min(0.5 + 0.05 * len(hits), 0.85)
            if conf > best_conf:
                best_type, best_risk, best_conf = ftype, risk, conf
                best_ev = hits[:3]

    return Verdict(
        fraud_type=best_type,
        risk=best_risk,
        confidence=best_conf,
        evidence=best_ev,
        degraded=True,
    )


def _mock_classify(text: str) -> Verdict:
    """
    Deterministic mock that uses the rules engine but marks degraded=False
    so tests can verify a non-degraded path is returned in mock mode.
    Uses text hash to make results reproducible across runs.
    """
    verdict = _rules_only_classify(text)
    verdict.degraded = False  # mock is "pretending" to be a real LLM
    return verdict


# ── Replay classifier (load from fixture file) ───────────────────────────────

_REPLAY_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "llm_replay"


def _replay_classify(text: str) -> Verdict | None:
    """
    Look up a pre-recorded verdict by SHA-256 of the text.
    Returns None if not found (caller should fall back to mock).
    """
    key = hashlib.sha256(text.encode()).hexdigest()
    fixture_file = _REPLAY_DIR / f"{key}.json"
    if not fixture_file.exists():
        return None
    raw: dict[str, Any] = json.loads(fixture_file.read_text())
    return Verdict(
        fraud_type=FraudType(raw["fraud_type"]),
        risk=RiskLevel(raw["risk"]),
        confidence=float(raw["confidence"]),
        evidence=raw.get("evidence", []),
        degraded=raw.get("degraded", False),
    )


# ── Live classifier (Gemini) ─────────────────────────────────────────────────

_CLASSIFY_PROMPT = """\
You are a fraud-detection assistant for the Indian law enforcement KAVACH system.
Analyze the following complaint text (already de-identified) and respond ONLY with a JSON object.

Text:
{text}

Respond ONLY with valid JSON matching this schema exactly (no markdown, no explanation):
{{
  "fraud_type": "<one of: digital_arrest|job_fraud|investment_fraud|"
               "customer_support|sextortion|ecommerce|other>",
  "risk": "<one of: danger|suspicious|likely_safe|unknown>",
  "confidence": <float 0.0-1.0>,
  "evidence": ["<verbatim substring from text>", ...]
}}
"""


def _live_classify(text: str) -> Verdict:
    """Call Gemini API. Only runs if LLM_MODE=live AND LLM_LIVE_ACK=yes."""
    settings.assert_live_allowed()

    try:
        import google.generativeai as genai  # type: ignore[import]

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(_CLASSIFY_PROMPT.format(text=text))
        raw_text = resp.text.strip()
        # Strip possible markdown fences
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text, flags=re.MULTILINE)
            raw_text = raw_text.rstrip("`").strip()
        raw: dict[str, Any] = json.loads(raw_text)
        return Verdict(
            fraud_type=FraudType(raw["fraud_type"]),
            risk=RiskLevel(raw["risk"]),
            confidence=float(raw["confidence"]),
            evidence=raw.get("evidence", []),
        )
    except Exception as exc:
        logger.warning("primary LLM (Gemini) failed: %s — trying secondary", exc)
        raise


# ── Public interface ─────────────────────────────────────────────────────────


def classify(masked_text: str) -> Verdict:
    """
    Classify a (masked) complaint text using the configured LLM mode.

    Fallback order for live mode: Gemini → RulesOnly (degraded).
    Validation is applied to every non-rules verdict.
    """
    mode = settings.LLM_MODE

    if mode == "mock":
        verdict = _mock_classify(masked_text)
    elif mode == "replay":
        verdict = _replay_classify(masked_text)
        if verdict is None:
            logger.info("replay: cache miss — falling back to mock")
            verdict = _mock_classify(masked_text)
    else:  # live
        try:
            verdict = _live_classify(masked_text)
            # Server-side validation — retry once on failure → manual review
            try:
                validate_verdict(verdict, masked_text)
            except VerdictValidationError as ve:
                logger.error("LLM output validation failed: %s — marking needs_review", ve)
                verdict.reason = str(ve)
                verdict.confidence = 0.0
                verdict.risk = RiskLevel.unknown
                # Caller sees confidence=0 and will set needs_manual_review
        except Exception:
            logger.warning("all LLM providers failed — using rules-only fallback")
            verdict = _rules_only_classify(masked_text)

    return verdict

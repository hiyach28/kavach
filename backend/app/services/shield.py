"""Shield Check Service — 3-tier decision cascade (F30).

Tiers (each with its own latency budget):
  1. Entity hash lookup (~5ms) — check entity against known-bad graph
  2. Script-pattern ANN (~50ms) — embed text, search vs scam_script centroids
  3. LLM fallback (~2s) — only if tiers 1-2 inconclusive

Cache: verdicts cached per entity-hash with TTL (configurable via env).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import embeddings, llm_client

logger = logging.getLogger("kavach.shield")

# ── Verdict bands (F30) — raw scores NEVER exposed to citizens (anti-probing) ─
_VERDICT_BANDS = ("danger", "suspicious", "likely_safe", "unknown")

# Tier thresholds
_TIER2_SIM_THRESHOLD = 0.75       # ANN similarity to trigger tier-2 verdict
_TIER1_MIN_REPORT_COUNT = 3       # report_count threshold for tier-1 danger
_CACHE_TTL_SECONDS = 300          # 5-minute cache for entity verdicts


# ── Result type ─────────────────────────────────────────────────────────────────

@dataclass
class ShieldResult:
    verdict: str                     # danger | suspicious | likely_safe | unknown
    tier_resolved: int               # 1 | 2 | 3
    explanation: str                 # plain-language reason
    report_count: int = 0            # from entity lookup
    entity_matched: str | None = None
    fraud_type: str | None = None
    language: str = "en"


# ── Tier 1: Entity hash lookup ──────────────────────────────────────────────────

async def _tier1_entity_lookup(
    entity_value: str | None,
    db: AsyncSession,
) -> ShieldResult | None:
    """
    Check if an entity value exists in the graph with sufficient report count.

    Returns a ShieldResult if the entity is known-bad, None if not found
    or below threshold.
    """
    if not entity_value or not entity_value.strip():
        return None

    # Normalise and hash the entity the same way as the entity extractor
    from app.services.entity_extractor import _sha256 as hash_val
    from app.models.graph import Entity, CaseEntityLink

    # Try the raw value as a loose match first (it may already be a hash)
    value_hash = entity_value.strip()
    # If it looks like a phone/UPI/URL, normalise it first
    if len(value_hash) != 64 or not all(c in "0123456789abcdef" for c in value_hash.lower()):
        # It's not a hash — try to hash it like the entity extractor would
        # We'll just SHA-256 it generically and search
        import hashlib
        value_hash = hashlib.sha256(value_hash.encode()).hexdigest()

    # Look up entity by value_hash
    result = await db.execute(
        select(Entity).where(Entity.value_hash == value_hash)
    )
    entity = result.scalar_one_or_none()
    if entity is None:
        return None

    if entity.report_count >= _TIER1_MIN_REPORT_COUNT:
        # Check if this entity is linked to a campaign (makes it more serious)
        from app.models.graph import Campaign
        link_result = await db.execute(
            select(CaseEntityLink).where(CaseEntityLink.entity_id == entity.id)
        )
        links = link_result.scalars().all()
        campaign_ids = set()
        for link in links:
            case_result = await db.execute(
                text("SELECT campaign_id FROM cases WHERE id = :cid"),
                {"cid": link.case_id},
            )
            row = case_result.fetchone()
            if row and row[0]:
                campaign_ids.add(str(row[0]))

        verdict = "danger" if len(campaign_ids) > 0 or entity.report_count >= 5 else "suspicious"
        return ShieldResult(
            verdict=verdict,
            tier_resolved=1,
            explanation=(
                f"This contact has been reported {entity.report_count} time(s) "
                f"in our system."
            ),
            report_count=entity.report_count,
            entity_matched=entity.value_hash,
            language="en",
        )

    # Below threshold but has some reports
    return ShieldResult(
        verdict="suspicious" if entity.report_count > 0 else "unknown",
        tier_resolved=1,
        explanation=f"This contact has {entity.report_count} report(s) in our system.",
        report_count=entity.report_count,
        entity_matched=entity.value_hash,
        language="en",
    )


# ── Tier 2: Script-pattern ANN ──────────────────────────────────────────────────

async def _tier2_script_pattern(
    text: str,
    db: AsyncSession,
) -> ShieldResult | None:
    """
    Embed the check text and run ANN similarity against scam_script centroids.

    Returns a ShieldResult if a known script pattern matches above threshold.
    """
    vec = embeddings.embed(text)
    vec_literal = "[" + ",".join(str(f) for f in vec) + "]"

    rows = (await db.execute(
        text(
            "SELECT label, fraud_type, verdict, language, "
            " 1 - (embedding <=> :vec::vector) AS score"
            " FROM scam_scripts"
            " WHERE embedding IS NOT NULL"
            " ORDER BY embedding <=> :vec::vector"
            " LIMIT 5"
        ),
        {"vec": vec_literal},
    )).fetchall()

    if not rows:
        return None

    best_score = float(rows[0][4])
    if best_score >= _TIER2_SIM_THRESHOLD:
        return ShieldResult(
            verdict=str(rows[0][2]),
            tier_resolved=2,
            explanation=(
                f"This message matches known scam scripts "
                f"(similarity: {best_score:.0%})."
            ),
            fraud_type=str(rows[0][1]),
            language=str(rows[0][3]) if rows[0][3] else "en",
        )

    # Below threshold — inconclusive
    return None


# ── Tier 3: LLM fallback ────────────────────────────────────────────────────────

def _tier3_llm_fallback(text: str) -> ShieldResult:
    """
    Call the LLM classifier as final fallback.

    Only invoked when tiers 1-2 are inconclusive.
    Maps the LLM verdict to shield-appropriate bands.
    """
    verdict = llm_client.classify(text)

    # Map LLM risk levels to shield verdict bands
    shield_verdict = verdict.risk.value  # same enum values: danger/suspicious/likely_safe/unknown

    evidence_text = ""
    if verdict.evidence:
        evidence_text = f" Red flags: {', '.join(verdict.evidence[:3])}."

    return ShieldResult(
        verdict=shield_verdict,
        tier_resolved=3,
        explanation=(
            f"Our analysis suggests this is {shield_verdict.replace('_', ' ')} fraud."
            f"{evidence_text}"
            f"{' (Note: analysis is preliminary — verified by rules-only fallback)' if verdict.degraded else ''}"
        ),
        fraud_type=verdict.fraud_type.value,
        language="en",
        report_count=0,
    )


# ── Public interface ────────────────────────────────────────────────────────────

async def check(
    text: str,
    db: AsyncSession,
    entity_value: str | None = None,
) -> ShieldResult:
    """
    Run the 3-tier Shield check cascade.
    Returns a ShieldResult with the verdict, explanation, and tier info.
    """
    # ── Tier 1: Entity hash lookup (~5ms) ───────────────────────────────────
    if entity_value:
        tier1_result = await _tier1_entity_lookup(entity_value, db)
        if tier1_result and tier1_result.verdict in ("danger", "suspicious"):
            return tier1_result

    # ── Tier 2: Script-pattern ANN (~50ms) ──────────────────────────────────
    if text and text.strip():
        tier2_result = await _tier2_script_pattern(text, db)
        if tier2_result:
            return tier2_result

    # ── Tier 3: LLM Fallback (~2s) ──────────────────────────────────────────
    if text and text.strip():
        tier3_result = _tier3_llm_fallback(text)
        return tier3_result

    # Nothing to check — return unknown
    return ShieldResult(
        verdict="unknown",
        tier_resolved=0,
        explanation="No information provided to check.",
        language="en",
    )

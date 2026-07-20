"""Takedown Brief Engine (F25).

Computes a structured takedown brief per campaign, aggregating case data,
entity intelligence, and evidence summaries. Result is cached in the
campaigns.takedown_brief JSONB column.

Caching policy:
  - Computed on first read and stored in the DB column.
  - Caller can force-refresh (e.g. after new cases land in the campaign).
  - No automatic expiry — brief is a point-in-time snapshot; the nightly
    recluster job can recompute it.
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import (
    Campaign,
    Case,
    CaseEntityLink,
    Entity,
    FraudType,
    RiskLevel,
)

logger = logging.getLogger("kavach.takedown")


# ── Data structures ────────────────────────────────────────────────────────────


@dataclass
class EntitySummary:
    type: str
    value_hash: str
    report_count: int
    first_seen: str  # ISO-8601

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FraudTypeDistribution:
    type: str
    count: int
    avg_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TakedownBrief:
    """Complete intelligence brief for one campaign."""

    campaign_id: str
    total_cases: int
    fraud_type_distribution: list[FraudTypeDistribution]
    overall_risk: str
    avg_confidence: float
    top_entities: list[EntitySummary]
    total_unique_entities: int
    entity_type_breakdown: dict[str, int]
    languages: list[str]
    districts: list[str]
    case_ids: list[str]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "total_cases": self.total_cases,
            "fraud_type_distribution": [f.to_dict() for f in self.fraud_type_distribution],
            "overall_risk": self.overall_risk,
            "avg_confidence": self.avg_confidence,
            "top_entities": [e.to_dict() for e in self.top_entities],
            "total_unique_entities": self.total_unique_entities,
            "entity_type_breakdown": self.entity_type_breakdown,
            "languages": self.languages,
            "districts": self.districts,
            "case_ids": self.case_ids,
            "generated_at": self.generated_at,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────


def _compute_overall_risk(fraud_types: list[FraudType], risks: list[RiskLevel]) -> str:
    """Derive an overall risk label for the campaign.

    - If any case is `danger` → campaign is `danger`
    - If most cases are `unknown` or `likely_safe` and there are few → `likely_safe`
    - Otherwise → `suspicious`
    """
    if any(r == RiskLevel.danger for r in risks):
        return "danger"

    # Count how many cases have meaningful risk signals
    meaningful = sum(1 for r in risks if r in (RiskLevel.suspicious, RiskLevel.danger))
    total = len(risks)
    if total == 0:
        return "unknown"

    if meaningful / total > 0.3:
        return "suspicious"

    return "likely_safe"


def _get_top_entities(
    entities: list[Entity],
    max_items: int = 20,
) -> list[EntitySummary]:
    """Return the most-reported entities, sorted descending by report_count."""
    sorted_entities = sorted(entities, key=lambda e: e.report_count, reverse=True)
    return [
        EntitySummary(
            type=e.type.value,
            value_hash=e.value_hash[:12] + "…",  # truncated for readability
            report_count=e.report_count,
            first_seen=e.first_seen.isoformat() if e.first_seen else "",
        )
        for e in sorted_entities[:max_items]
    ]


def _entity_type_breakdown(entities: list[Entity]) -> dict[str, int]:
    """Count entities by type."""
    counter: Counter[str] = Counter()
    for e in entities:
        counter[e.type.value] += 1
    return dict(counter)


# ── Public interface ───────────────────────────────────────────────────────────


async def compute_takedown_brief(
    campaign_id: uuid.UUID,
    db: AsyncSession,
    *,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Compute (or retrieve cached) takedown brief for a campaign.

    If a cached brief exists and ``force_refresh`` is False, returns the
    cached version. Otherwise recomputes from current data and stores it.
    """
    # 1. Fetch the campaign row
    campaign_result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = campaign_result.scalar_one_or_none()
    if campaign is None:
        raise ValueError(f"Campaign {campaign_id} not found")

    # 2. Check cache
    if campaign.takedown_brief and not force_refresh:
        return dict(campaign.takedown_brief)  # type: ignore[arg-type]

    # 3. Fetch linked cases
    case_rows = (
        (await db.execute(select(Case).where(Case.campaign_id == campaign_id))).scalars().all()
    )

    if not case_rows:
        empty_brief = TakedownBrief(
            campaign_id=str(campaign_id),
            total_cases=0,
            fraud_type_distribution=[],
            overall_risk="unknown",
            avg_confidence=0.0,
            top_entities=[],
            total_unique_entities=0,
            entity_type_breakdown={},
            languages=[],
            districts=[],
            case_ids=[],
            generated_at=datetime.now(UTC).isoformat(),
        )
        return _store_and_return(campaign, empty_brief, db)

    # 4. Aggregate case data
    case_ids = [c.id for c in case_rows]
    fraud_types: list[FraudType] = []
    risks: list[RiskLevel] = []
    confidences: list[float] = []
    languages: set[str] = set()
    districts: set[str] = set()

    for c in case_rows:
        if c.fraud_type:
            fraud_types.append(c.fraud_type)
        if c.risk:
            risks.append(c.risk)
        if c.confidence is not None:
            confidences.append(c.confidence)
        if c.language:
            languages.add(c.language)
        if c.district:
            districts.add(c.district)

    # Fraud type distribution
    ft_counter: Counter[FraudType] = Counter(fraud_types)
    len(fraud_types) or 1
    ft_distribution = [
        FraudTypeDistribution(
            type=ft.value,
            count=cnt,
            avg_confidence=round(
                sum(
                    c.confidence or 0.0
                    for case in case_rows
                    if case.fraud_type == ft and case.confidence is not None
                )
                / max(
                    sum(
                        1
                        for case in case_rows
                        if case.fraud_type == ft and case.confidence is not None
                    ),
                    1,
                ),
                2,
            ),
        )
        for ft, cnt in ft_counter.most_common()
    ]

    avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    overall_risk = _compute_overall_risk(fraud_types, risks)

    # 5. Fetch linked entities through case_entity_links
    if case_ids:
        entity_rows = (
            (
                await db.execute(
                    select(Entity)
                    .join(CaseEntityLink, CaseEntityLink.entity_id == Entity.id)
                    .where(CaseEntityLink.case_id.in_(case_ids))
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
    else:
        entity_rows = []

    top_entities = _get_top_entities(list(entity_rows))
    type_breakdown = _entity_type_breakdown(list(entity_rows))

    brief = TakedownBrief(
        campaign_id=str(campaign_id),
        total_cases=len(case_rows),
        fraud_type_distribution=ft_distribution,
        overall_risk=overall_risk,
        avg_confidence=avg_confidence,
        top_entities=top_entities,
        total_unique_entities=len(entity_rows),
        entity_type_breakdown=type_breakdown,
        languages=sorted(languages),
        districts=sorted(districts),
        case_ids=[str(cid) for cid in case_ids],
        generated_at=datetime.now(UTC).isoformat(),
    )

    return _store_and_return(campaign, brief, db)


async def _store_and_return(
    campaign: Campaign,
    brief: TakedownBrief,
    db: AsyncSession,
) -> dict[str, Any]:
    """Store brief in DB and return as dict."""
    brief_dict = brief.to_dict()
    await db.execute(
        update(Campaign).where(Campaign.id == campaign.id).values(takedown_brief=brief_dict)
    )
    await db.flush()
    logger.info("stored takedown brief for campaign %s", campaign.id)
    return brief_dict


async def list_campaigns(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    min_cases: int = 0,
) -> list[dict[str, Any]]:
    """List known campaigns with summary stats.

    Args:
        db: Database session.
        limit: Max rows.
        offset: Pagination offset.
        min_cases: Only include campaigns with at least this many cases.

    Returns:
        List of campaign summary dicts.
    """
    query = select(Campaign).order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(query)).scalars().all()

    results: list[dict[str, Any]] = []
    for camp in rows:
        # Count cases for this campaign
        case_count = (
            (await db.execute(select(Case.id).where(Case.campaign_id == camp.id))).scalars().all()
        )
        case_ids = list(case_count)

        if len(case_ids) < min_cases:
            continue

        # Get risk summary from takedown_brief if cached
        overall_risk = "unknown"
        if camp.takedown_brief:
            overall_risk = camp.takedown_brief.get("overall_risk", "unknown")

        results.append(
            {
                "id": str(camp.id),
                "label": camp.label,
                "total_cases": len(case_ids),
                "velocity": camp.velocity or 0.0,
                "projected_victims": camp.projected_victims or 0,
                "overall_risk": overall_risk,
                "has_brief": camp.takedown_brief is not None,
                "created_at": camp.created_at.isoformat() if camp.created_at else "",
            }
        )

    return results

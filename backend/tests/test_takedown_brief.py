"""Unit tests for Takedown Brief Engine (F25) — pure unit, no DB."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.graph import Case, Campaign, Entity, EntityType, FraudType, RiskLevel
from app.services.takedown_brief import (
    _compute_overall_risk,
    _entity_type_breakdown,
    _get_top_entities,
    compute_takedown_brief,
    list_campaigns,
)


# ── Helper to make a fake case row ─────────────────────────────────────────────

def _make_case(
    *,
    fraud_type: FraudType | None = FraudType.other,
    risk: RiskLevel | None = RiskLevel.unknown,
    confidence: float | None = 0.5,
    language: str | None = "hi",
    district: str | None = "mumbai",
    campaign_id: uuid.UUID | None = None,
) -> MagicMock:
    case = MagicMock(spec=Case)
    case.id = uuid.uuid4()
    case.fraud_type = fraud_type
    case.risk = risk
    case.confidence = confidence
    case.language = language
    case.district = district
    case.campaign_id = campaign_id
    return case


def _make_entity(
    *,
    etype: EntityType = EntityType.PHONE,
    value_hash: str = "abc123",
    report_count: int = 1,
) -> MagicMock:
    ent = MagicMock(spec=Entity)
    ent.type = etype
    ent.value_hash = value_hash
    ent.report_count = report_count
    ent.first_seen = datetime.now(UTC)
    return ent


# ── _compute_overall_risk ──────────────────────────────────────────────────────

class TestComputeOverallRisk:
    def test_danger_if_any_danger(self) -> None:
        risks = [RiskLevel.suspicious, RiskLevel.danger, RiskLevel.likely_safe]
        assert _compute_overall_risk([], risks) == "danger"

    def test_suspicious_if_many_suspicious(self) -> None:
        risks = [RiskLevel.suspicious, RiskLevel.suspicious, RiskLevel.likely_safe]
        assert _compute_overall_risk([], risks) == "suspicious"

    def test_likely_safe_if_few_suspicious(self) -> None:
        risks = [RiskLevel.likely_safe, RiskLevel.likely_safe, RiskLevel.unknown]
        assert _compute_overall_risk([], risks) == "likely_safe"

    def test_unknown_if_empty(self) -> None:
        assert _compute_overall_risk([], []) == "unknown"


# ── _get_top_entities ──────────────────────────────────────────────────────────

class TestGetTopEntities:
    def test_sorts_by_report_count(self) -> None:
        e1 = _make_entity(value_hash="aaa", report_count=1)
        e2 = _make_entity(value_hash="bbb", report_count=10)
        e3 = _make_entity(value_hash="ccc", report_count=5)
        top = _get_top_entities([e1, e2, e3], max_items=5)
        assert top[0].value_hash.startswith("bbb")
        assert top[1].value_hash.startswith("ccc")
        assert top[2].value_hash.startswith("aaa")

    def test_respects_max_items(self) -> None:
        entities = [_make_entity(value_hash=f"e{i}", report_count=i) for i in range(10)]
        top = _get_top_entities(entities, max_items=3)
        assert len(top) == 3

    def test_handles_empty(self) -> None:
        assert _get_top_entities([]) == []

    def test_truncates_hash(self) -> None:
        e = _make_entity(value_hash="x" * 64, report_count=5)
        top = _get_top_entities([e])
        assert len(top[0].value_hash) < 64
        assert top[0].value_hash.endswith("…")


# ── _entity_type_breakdown ─────────────────────────────────────────────────────

class TestEntityTypeBreakdown:
    def test_counts_by_type(self) -> None:
        ents = [
            _make_entity(etype=EntityType.PHONE, value_hash="a"),
            _make_entity(etype=EntityType.PHONE, value_hash="b"),
            _make_entity(etype=EntityType.UPI, value_hash="c"),
        ]
        breakdown = _entity_type_breakdown(ents)
        assert breakdown["PHONE"] == 2
        assert breakdown["UPI"] == 1

    def test_empty(self) -> None:
        assert _entity_type_breakdown([]) == {}


# ── compute_takedown_brief ─────────────────────────────────────────────────────

class TestComputeTakedownBrief:
    @pytest.mark.asyncio
    async def test_raises_on_missing_campaign(self) -> None:
        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await compute_takedown_brief(uuid.uuid4(), db)

    @pytest.mark.asyncio
    async def test_returns_cached_brief(self) -> None:
        campaign = MagicMock(spec=Campaign)
        campaign.id = uuid.uuid4()
        campaign.takedown_brief = {"cached": True, "total_cases": 5}

        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none.return_value = campaign

        result = await compute_takedown_brief(campaign.id, db, force_refresh=False)
        assert result["cached"] is True
        # No DB flush should happen on cache hit
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_brief_for_no_cases(self) -> None:
        campaign = MagicMock(spec=Campaign)
        campaign.id = uuid.uuid4()
        campaign.takedown_brief = None

        db = AsyncMock()
        # First call: fetch campaign
        db.execute.return_value.scalar_one_or_none.return_value = campaign
        # Second call: fetch cases → empty
        db.execute.return_value.scalars.return_value.all.return_value = []

        result = await compute_takedown_brief(campaign.id, db, force_refresh=True)
        assert result["total_cases"] == 0
        assert result["overall_risk"] == "unknown"

    @pytest.mark.asyncio
    async def test_computes_brief_with_cases(self) -> None:
        campaign = MagicMock(spec=Campaign)
        campaign.id = uuid.uuid4()
        campaign.takedown_brief = None

        case1 = _make_case(
            fraud_type=FraudType.digital_arrest,
            risk=RiskLevel.danger,
            confidence=0.85,
            language="hi",
            district="mumbai",
        )
        case2 = _make_case(
            fraud_type=FraudType.digital_arrest,
            risk=RiskLevel.danger,
            confidence=0.72,
            language="en",
            district="mumbai",
        )

        phone_entity = _make_entity(etype=EntityType.PHONE, value_hash="phone123", report_count=3)
        upi_entity = _make_entity(etype=EntityType.UPI, value_hash="upi456", report_count=1)

        db = AsyncMock()
        # Configure sequential execute calls
        db.execute.side_effect = [
            # Call 1: fetch campaign
            MagicMock(scalar_one_or_none=MagicMock(return_value=campaign)),
            # Call 2: fetch cases
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[case1, case2])))),
            # Call 3: fetch entities
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[phone_entity, upi_entity])))),
        ]

        with patch("app.services.takedown_brief.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 19, 12, 0, 0)
            result = await compute_takedown_brief(campaign.id, db, force_refresh=True)

        assert result["total_cases"] == 2
        assert result["overall_risk"] == "danger"
        assert result["avg_confidence"] == 0.78  # (0.85 + 0.72) / 2 ≈ 0.78
        assert len(result["fraud_type_distribution"]) == 1
        assert result["fraud_type_distribution"][0]["type"] == "digital_arrest"
        assert result["total_unique_entities"] == 2
        assert result["entity_type_breakdown"]["PHONE"] == 1
        assert result["entity_type_breakdown"]["UPI"] == 1


# ── list_campaigns ─────────────────────────────────────────────────────────────

class TestListCampaigns:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_campaigns(self) -> None:
        db = AsyncMock()
        db.execute.return_value.scalars.return_value.all.return_value = []
        results = await list_campaigns(db)
        assert results == []

    @pytest.mark.asyncio
    async def test_lists_campaigns_with_case_counts(self) -> None:
        camp1 = MagicMock(spec=Campaign)
        camp1.id = uuid.uuid4()
        camp1.label = "Campaign Alpha"
        camp1.velocity = 3.0
        camp1.projected_victims = 100
        camp1.takedown_brief = {"overall_risk": "danger"}
        camp1.created_at = datetime.now(UTC)
        camp1.updated_at = datetime.now(UTC)

        camp2 = MagicMock(spec=Campaign)
        camp2.id = uuid.uuid4()
        camp2.label = None
        camp2.velocity = 0.0
        camp2.projected_victims = None
        camp2.takedown_brief = None
        camp2.created_at = datetime.now(UTC)
        camp2.updated_at = datetime.now(UTC)

        db = AsyncMock()
        # Return campaigns list
        db.execute.return_value.scalars.return_value.all.return_value = [camp1, camp2]

        # Configure the case count query (sequential calls)
        def side_effect(*args, **kwargs):
            # Return 3 cases for camp1, 0 for camp2
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = (
                [uuid.uuid4()] * 3 if "camp1" not in str(args) else []
            )
            return mock_result

        # For the two campaigns, we need two execute calls for case counts
        # Actually the side_effect will be called once for each campaign
        db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[uuid.uuid4() for _ in range(3)])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]

        results = await list_campaigns(db, min_cases=0)
        assert len(results) == 1  # camp2 has 0 cases, gets filtered by min_cases=0? No, min_cases=0 means no filter
        # Since min_cases=0, both should be returned
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_filters_by_min_cases(self) -> None:
        camp = MagicMock(spec=Campaign)
        camp.id = uuid.uuid4()
        camp.label = None
        camp.velocity = 0.0
        camp.projected_victims = None
        camp.takedown_brief = None
        camp.created_at = datetime.now(UTC)
        camp.updated_at = datetime.now(UTC)

        db = AsyncMock()
        db.execute.return_value.scalars.return_value.all.return_value = [camp]
        # Return 1 case
        db.execute.return_value.scalars.return_value.all.return_value = [uuid.uuid4()]

        # Actually let me just set side_effect for the two calls
        # The first call is for campaigns, second for case counts
        db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[camp])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[uuid.uuid4()])))),
        ]

        results = await list_campaigns(db, min_cases=2)
        assert len(results) == 0  # 1 case < min_cases=2

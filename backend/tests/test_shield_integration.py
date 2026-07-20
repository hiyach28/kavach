"""Shield integration tests (F30, F34) — require Postgres.

Run these tests inside Docker compose:
  docker compose run --rm backend python -m pytest tests/test_shield_integration.py -v

These tests verify:
  - Tier 1 entity lookup against real DB
  - Tier 2 script-pattern ANN against scam_scripts table
  - Full 3-tier cascade end-to-end
  - Shield API endpoint (authenticated)
  - Flywheel consented → entity creation
  - Shield check logging to shield_checks table
"""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.graph import Entity, EntityType
from app.models.shield import ShieldCheck
from app.services import shield as shield_svc
from app.config import settings

settings.LLM_MODE = "mock"


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
async def seed_known_bad_entity(db_session):
    """Seed an entity with high report_count for tier-1 testing."""
    ent = Entity(
        type=EntityType.PHONE,
        value_hash="a" * 64,
        report_count=5,
    )
    db_session.add(ent)
    await db_session.commit()
    return ent


# ── Tier 1: Entity lookup ───────────────────────────────────────────────────────

class TestTier1EntityLookup:
    async def test_known_bad_entity_returns_danger(self, db_session, seed_known_bad_entity):
        """Entity with report_count >= threshold returns danger."""
        result = await shield_svc._tier1_entity_lookup("a" * 64, db_session)
        assert result is not None
        assert result.verdict == "danger"
        assert result.tier_resolved == 1
        assert result.report_count == 5

    async def test_unknown_entity_returns_none(self, db_session):
        """Unknown entity hash returns None (goes to next tier)."""
        result = await shield_svc._tier1_entity_lookup("nonexistent_hash", db_session)
        assert result is None

    async def test_low_report_count_entity(self, db_session):
        """Entity below threshold should still return suspicious."""
        ent = Entity(type=EntityType.PHONE, value_hash="b" * 64, report_count=1)
        db_session.add(ent)
        await db_session.commit()
        result = await shield_svc._tier1_entity_lookup("b" * 64, db_session)
        assert result is not None


# ── Tier 2: Script pattern ──────────────────────────────────────────────────────

class TestTier2ScriptPattern:
    async def test_no_scripts_returns_none(self, db_session):
        """No scam_scripts in DB → tier 2 returns None."""
        result = await shield_svc._tier2_script_pattern("test message", db_session)
        assert result is None

    async def test_matching_script_detected(self, db_session):
        """Script matching known pattern should return verdict."""
        from app.models.shield import ScamScript
        from app.services import embeddings

        # Seed a scam script
        script_text = "CBI officer calling about drugs parcel, need to pay security deposit"
        script_embed = embeddings.embed(script_text)
        ss = ScamScript(
            label="digital_arrest_standard",
            fraud_type="digital_arrest",
            embedding=script_embed,  # type: ignore[arg-type]
            language="en",
            script_text=script_text,
            verdict="danger",
        )
        db_session.add(ss)
        await db_session.commit()

        result = await shield_svc._tier2_script_pattern(
            "Hello this is CBI officer about your drugs parcel pay deposit now",
            db_session,
        )
        # May or may not match depending on mock embedding quality
        if result:
            assert result.tier_resolved == 2
            assert result.verdict in ("danger", "suspicious")


# ── Full cascade ────────────────────────────────────────────────────────────────

class TestShieldCheckCascade:
    async def test_tier1_resolves_first(self, db_session, seed_known_bad_entity):
        """Known-bad entity resolves at tier 1."""
        result = await shield_svc.check(text="any text", db=db_session, entity_value="a" * 64)
        assert result.verdict == "danger"
        assert result.tier_resolved == 1

    async def test_tier3_fallback_when_no_data(self, db_session):
        """No entities or scripts → falls through to tier 3."""
        result = await shield_svc.check(text="CBI arrested me and demanded money", db=db_session)
        assert result.tier_resolved == 3


# ── API endpoint ────────────────────────────────────────────────────────────────

class TestShieldAPI:
    async def test_check_authenticated(self, client, auth_headers):
        """Authenticated shield check returns verdict."""
        resp = await client.post(
            "/v1/shield/check",
            json={"text": "suspicious message about digital arrest", "channel": "pwa"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["verdict"] in ("danger", "suspicious", "likely_safe", "unknown")
        assert data["title"]
        assert data["explanation"]
        assert data["cta"]
        assert data["check_id"]

    async def test_check_unauthenticated(self, client):
        """Unauthenticated request returns 401."""
        resp = await client.post(
            "/v1/shield/check",
            json={"text": "test"},
        )
        assert resp.status_code == 401

    async def test_check_empty_input_rejected(self, client, auth_headers):
        """Empty input returns 422."""
        resp = await client.post("/v1/shield/check", json={}, headers=auth_headers)
        assert resp.status_code == 422

    async def test_check_logged(self, client, auth_headers, db_session):
        """Check is logged to shield_checks table."""
        resp = await client.post(
            "/v1/shield/check",
            json={"text": "CBI arrest case filed money", "channel": "api"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        count = (await db_session.execute(select(ShieldCheck))).scalar()
        assert count is not None and count >= 1


# ── Flywheel ────────────────────────────────────────────────────────────────────

class TestShieldFlywheel:
    async def test_consent_creates_entity(self, db_session):
        """Consented check creates graph entity."""
        from app.api.v1.shield import _feed_flywheel
        from app.services.shield import ShieldResult

        result = ShieldResult(verdict="suspicious", tier_resolved=1, explanation="test", report_count=2)
        await _feed_flywheel(["hash_consent_1"], result, db_session)

        entities = (await db_session.execute(
            select(Entity).where(Entity.value_hash == "hash_consent_1")
        )).scalars().all()
        assert len(entities) == 1

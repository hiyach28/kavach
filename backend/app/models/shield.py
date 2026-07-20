"""SQLAlchemy models for Shield (Phase 3).

Tables:
  - shield_checks:  telemetry/log for every check (F30, F34)
  - scam_scripts:   known scam-script centroids for ANN pattern matching (F30 tier 2)
"""
import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ShieldCheck(Base, TimestampMixin):
    """Every Shield check logged here (F30 §AC, F34 telemetry)."""

    __tablename__ = "shield_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    # What was checked — raw text is NOT stored; entity hash(es) only
    entity_hashes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    # Verdict bands (anti-probing: raw scores never exposed to citizens)
    verdict: Mapped[str] = mapped_column(sa.String, nullable=False)  # danger|suspicious|l likely_safe|unknown
    tier_resolved: Mapped[int] = mapped_column(sa.Integer, nullable=False)  # 1|2|3
    latency_ms: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    # Channel (pwa, whatsapp, api)
    channel: Mapped[str] = mapped_column(sa.String, nullable=False, default="api")
    # Geo-district (consented only)
    geo: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    # Explanation fragment (plain language, no raw scores)
    explanation: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Language detected
    language: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    # User consent for flywheel (F34)
    consent_for_intel: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    # If consent given, link to created entity rows
    entity_link_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)


class ScamScript(Base, TimestampMixin):
    """Known scam-script centroid for ANN pattern matching (F30 tier 2)."""

    __tablename__ = "scam_scripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    label: Mapped[str] = mapped_column(sa.String, nullable=False)
    fraud_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    language: Mapped[str] = mapped_column(sa.String, default="en")
    # The raw script text (for reference / LLM fallback)
    script_text: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Verdict band if matched
    verdict: Mapped[str] = mapped_column(sa.String, nullable=False)

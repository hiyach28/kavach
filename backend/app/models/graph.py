"""SQLAlchemy models for cases, entities, campaigns, and the graph."""
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CaseStatus(StrEnum):
    queued = "queued"
    classifying = "classifying"
    extracting = "extracting"
    linking = "linking"
    clustered = "clustered"
    needs_manual_review = "needs_manual_review"
    failed = "failed"


class FraudType(StrEnum):
    digital_arrest = "digital_arrest"
    job_fraud = "job_fraud"
    investment_fraud = "investment_fraud"
    customer_support = "customer_support"
    sextortion = "sextortion"
    ecommerce = "ecommerce"
    other = "other"


class RiskLevel(StrEnum):
    danger = "danger"
    suspicious = "suspicious"
    likely_safe = "likely_safe"
    unknown = "unknown"


class EntityType(StrEnum):
    PHONE = "PHONE"
    UPI = "UPI"
    EMAIL = "EMAIL"
    URL = "URL"
    HANDLE = "HANDLE"
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    IFSC = "IFSC"
    ACCOUNT = "ACCOUNT"
    NAME = "NAME"


class Campaign(Base, TimestampMixin):
    """A cluster of related cases (a fraud ring)."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    velocity: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    projected_victims: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    takedown_brief: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class Case(Base, TimestampMixin):
    """An individual fraud complaint or intelligence report."""

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[CaseStatus] = mapped_column(
        sa.Enum(CaseStatus, native_enum=False), default=CaseStatus.queued
    )
    fraud_type: Mapped[FraudType | None] = mapped_column(
        sa.Enum(FraudType, native_enum=False), nullable=True
    )
    risk: Mapped[RiskLevel | None] = mapped_column(
        sa.Enum(RiskLevel, native_enum=False), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    # pgvector embedding
    embedding: Mapped[Any | None] = mapped_column(Vector(768), nullable=True)

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    district: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    language: Mapped[str | None] = mapped_column(sa.String, nullable=True)


class Entity(Base, TimestampMixin):
    """A de-identified node in the graph (e.g. a phone number or UPI ID hash)."""

    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[EntityType] = mapped_column(sa.Enum(EntityType, native_enum=False))
    value_hash: Mapped[str] = mapped_column(sa.String, index=True)
    first_seen: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    report_count: Mapped[int] = mapped_column(sa.Integer, default=1)


class CaseEntityLink(Base):
    """Edge connecting a case to an entity it contains."""

    __tablename__ = "case_entity_links"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class SemanticLink(Base):
    """Edge connecting two cases based on vector similarity."""

    __tablename__ = "semantic_links"

    a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score: Mapped[float] = mapped_column(sa.Float)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

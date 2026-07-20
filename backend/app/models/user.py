"""User model (Phase 1)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import ARRAY, DateTime, Enum, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("citizen", "analyst", "officer", "admin", name="user_role"),
        nullable=False,
        default="analyst",
    )
    district_scope: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

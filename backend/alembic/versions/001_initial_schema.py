"""001 initial schema — Phase 1 tables.

Creates: users, pii_vault, audit_chain, cases (stub).
Enables pgvector extension (ready for Phase 2 embeddings).
Audit_chain: REVOKE UPDATE/DELETE so the chain is append-only at DB level.
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── pgvector extension (Phase 2 uses it for embeddings) ────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── users ───────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column(
            "role",
            sa.Enum("citizen", "analyst", "officer", "admin", name="user_role"),
            nullable=False,
            server_default="analyst",
        ),
        sa.Column("district_scope", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("failed_attempts", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── cases (stub — Phase 2 adds columns) ────────────────────────────────
    op.create_table(
        "cases",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "classifying",
                "extracting",
                "linking",
                "clustered",
                "needs_manual_review",
                "failed",
                name="case_status",
            ),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── pii_vault ───────────────────────────────────────────────────────────
    op.create_table(
        "pii_vault",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("case_id", sa.UUID(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=True),
        sa.Column("token", sa.String(64), nullable=False),        # SHA-256 hex of original
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),  # AES-GCM encrypted
        sa.Column("dek_wrapped", sa.LargeBinary(), nullable=False),  # AES-KW wrapped DEK
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("token", name="uq_pii_vault_token"),
    )
    op.create_index("ix_pii_vault_token", "pii_vault", ["token"])
    op.create_index("ix_pii_vault_case_id", "pii_vault", ["case_id"])

    # ── audit_chain ─────────────────────────────────────────────────────────
    op.create_table(
        "audit_chain",
        sa.Column("seq", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=True),          # null for system events
        sa.Column("case_id", sa.UUID(), nullable=True),
        sa.Column("payload_hash", sa.String(64), nullable=False),  # SHA-256 of event payload
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("this_hash", sa.String(64), nullable=False),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_chain_ts", "audit_chain", ["ts"])
    op.create_index("ix_audit_chain_case_id", "audit_chain", ["case_id"])

    # Revoke UPDATE and DELETE on audit_chain so chain is append-only.
    # The kavach DB user keeps INSERT + SELECT.
    op.execute("REVOKE UPDATE, DELETE ON audit_chain FROM kavach")


def downgrade() -> None:
    op.execute("GRANT UPDATE, DELETE ON audit_chain TO kavach")
    op.drop_table("audit_chain")
    op.drop_table("pii_vault")
    op.drop_table("cases")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS case_status")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP EXTENSION IF EXISTS vector")

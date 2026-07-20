"""Add shield tables: shield_checks, scam_scripts

Revision ID: 003
Revises: 5dc51aa46843
Create Date: 2026-07-20 10:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '5dc51aa46843'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # shield_checks — telemetry/log for every check (F30, F34)
    op.create_table('shield_checks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('entity_hashes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('verdict', sa.String(), nullable=False),
        sa.Column('tier_resolved', sa.Integer(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False, server_default='api'),
        sa.Column('geo', sa.String(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('consent_for_intel', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('entity_link_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shield_checks_verdict'), 'shield_checks', ['verdict'], unique=False)
    op.create_index(op.f('ix_shield_checks_created_at'), 'shield_checks', ['created_at'], unique=False)

    # scam_scripts — known scam-script centroids for ANN matching (F30 tier 2)
    op.create_table('scam_scripts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('fraud_type', sa.String(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=True),
        sa.Column('language', sa.String(), nullable=False, server_default='en'),
        sa.Column('script_text', sa.Text(), nullable=True),
        sa.Column('verdict', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scam_scripts_fraud_type'), 'scam_scripts', ['fraud_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scam_scripts_fraud_type'), table_name='scam_scripts')
    op.drop_table('scam_scripts')
    op.drop_index(op.f('ix_shield_checks_created_at'), table_name='shield_checks')
    op.drop_index(op.f('ix_shield_checks_verdict'), table_name='shield_checks')
    op.drop_table('shield_checks')

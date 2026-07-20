"""Audit chain service (Phase 1) — F14."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import sha256_hex
from app.models.audit import AuditChain


async def append_event(
    event_type: str,
    actor_id: uuid.UUID | None,
    payload: dict[str, Any],
    db: AsyncSession,
    case_id: uuid.UUID | None = None,
) -> AuditChain:
    """
    Append an event to the cryptographically linked audit chain.
    """
    payload_str = json.dumps(payload, sort_keys=True)
    payload_hash = sha256_hex(payload_str)
    ts = datetime.now(UTC)

    # Get prev_hash (latest row in chain)
    # Since we are async and might have concurrency, we ideally lock or serialize this.
    # For Phase 1, we do a simple select. The verify script handles forks by seq order.
    stmt = select(AuditChain).order_by(AuditChain.seq.desc()).limit(1)
    result = await db.execute(stmt)
    last_row = result.scalar_one_or_none()

    prev_hash = last_row.this_hash if last_row else "GENESIS"

    # Compute this_hash = SHA256(prev_hash + payload_hash + isoformat)
    this_hash_input = f"{prev_hash}{payload_hash}{ts.isoformat()}"
    this_hash = sha256_hex(this_hash_input)

    new_event = AuditChain(
        event_type=event_type,
        actor_id=actor_id,
        case_id=case_id,
        payload_hash=payload_hash,
        prev_hash=prev_hash,
        this_hash=this_hash,
        ts=ts,
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    return new_event


async def log_pii_access(
    case_id: uuid.UUID | None,
    actor_id: uuid.UUID,
    justification: str,
    db: AsyncSession,
) -> AuditChain:
    """Convenience wrapper for logging PII decryptions."""
    return await append_event(
        event_type="PII_DECRYPT",
        actor_id=actor_id,
        payload={"justification": justification},
        db=db,
        case_id=case_id,
    )

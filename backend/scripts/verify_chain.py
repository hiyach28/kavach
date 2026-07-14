#!/usr/bin/env python3
"""
Verify Audit Chain Script (Phase 1, F14).
Checks the integrity of the audit_chain table sequentially.
Exits with 0 if intact, 1 if tampered.
"""
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.core.security import sha256_hex
from app.models.audit import AuditChain


async def main() -> None:
    # Use sync-like loop to fetch all rows ordered by seq
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(select(AuditChain).order_by(AuditChain.seq.asc()))
        rows = result.fetchall()

    if not rows:
        print("Chain is empty.")
        sys.exit(0)

    expected_prev = "GENESIS"
    
    for row in rows:
        # Check link
        if row.prev_hash != expected_prev:
            print(f"❌ LINK BROKEN at seq {row.seq}: expected prev_hash {expected_prev}, got {row.prev_hash}")
            sys.exit(1)

        # Check payload tamper
        this_hash_input = f"{row.prev_hash}{row.payload_hash}{row.ts.isoformat()}"
        recomputed_this = sha256_hex(this_hash_input)
        
        if row.this_hash != recomputed_this:
            print(f"❌ TAMPER DETECTED at seq {row.seq}: expected this_hash {row.this_hash}, recomputed {recomputed_this}")
            sys.exit(1)

        expected_prev = row.this_hash

    print(f"✓ Chain intact ({len(rows)} events)")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

"""Embedding service (F23).

EMBED_MODE (follows settings.LLM_MODE unless overridden):
  mock   — deterministic hash-based pseudo-embedding (dim=768, no network)
  replay — load from fixture file by text hash
  live   — call text-embedding-004 via google-generativeai

top_k_similar() performs ANN search using pgvector <=> cosine distance.
"""
from __future__ import annotations

import hashlib
import json
import logging
import struct
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger("kavach.embed")

_DIM = 768
_REPLAY_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "embed_replay"


# ── Mock embedding ───────────────────────────────────────────────────────────

def _mock_embed(text_: str) -> list[float]:
    """
    Deterministic hash-based pseudo-embedding.
    Uses multiple SHA-256 seeds to fill 768 floats in [-1, 1].
    Suitable for clustering correctness tests offline.
    """
    floats: list[float] = []
    seed = text_.encode("utf-8")
    i = 0
    while len(floats) < _DIM:
        digest = hashlib.sha256(seed + i.to_bytes(4, "little")).digest()
        # Each digest gives 8 floats (4 bytes each, reinterpreted as signed int32 → [-1,1])
        chunk = struct.unpack(">8i", digest[:32])
        floats.extend(v / 2_147_483_648.0 for v in chunk)
        i += 1
    return floats[:_DIM]


# ── Replay embedding ─────────────────────────────────────────────────────────

def _replay_embed(text_: str) -> list[float] | None:
    key = hashlib.sha256(text_.encode()).hexdigest()
    fixture_file = _REPLAY_DIR / f"{key}.json"
    if not fixture_file.exists():
        return None
    raw: list[float] = json.loads(fixture_file.read_text())
    if len(raw) != _DIM:
        logger.warning("replay embedding has wrong dim %d, expected %d", len(raw), _DIM)
        return None
    return raw


# ── Live embedding ───────────────────────────────────────────────────────────

def _live_embed(text_: str) -> list[float]:
    settings.assert_live_allowed()
    try:
        import google.generativeai as genai  # type: ignore[import]
        genai.configure(api_key=settings.GEMINI_API_KEY)
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text_,
            task_type="RETRIEVAL_DOCUMENT",
        )
        embedding: list[float] = result["embedding"]
        if len(embedding) != _DIM:
            raise ValueError(f"unexpected embedding dim: {len(embedding)}")
        return embedding
    except Exception as exc:
        logger.error("live embedding failed: %s — falling back to mock", exc)
        return _mock_embed(text_)


# ── Public interface ─────────────────────────────────────────────────────────

def embed(text_: str) -> list[float]:
    """Return a 768-dim embedding vector for the given text."""
    mode = settings.effective_embed_mode

    if mode == "mock":
        return _mock_embed(text_)
    elif mode == "replay":
        result = _replay_embed(text_)
        if result is None:
            logger.info("embed replay: cache miss — falling back to mock")
            return _mock_embed(text_)
        return result
    else:  # live
        return _live_embed(text_)


async def top_k_similar(
    embedding: list[float],
    db: AsyncSession,
    k: int = 10,
    exclude_case_id: uuid.UUID | None = None,
) -> list[tuple[uuid.UUID, float]]:
    """
    Return top-k most similar case IDs by cosine distance using pgvector.
    Returns list of (case_id, score) sorted by similarity descending.
    """
    vec_literal = "[" + ",".join(str(f) for f in embedding) + "]"
    params: dict[str, Any] = {"vec": vec_literal, "k": k}

    if exclude_case_id:
        params["excl"] = str(exclude_case_id)
        sql = text(
            "SELECT id, 1 - (embedding <=> :vec::vector) AS score"
            " FROM cases"
            " WHERE embedding IS NOT NULL AND id != :excl"
            " ORDER BY embedding <=> :vec::vector"
            " LIMIT :k"
        )
    else:
        sql = text(
            "SELECT id, 1 - (embedding <=> :vec::vector) AS score"
            " FROM cases"
            " WHERE embedding IS NOT NULL"
            " ORDER BY embedding <=> :vec::vector"
            " LIMIT :k"
        )

    rows = (await db.execute(sql, params)).fetchall()
    return [(uuid.UUID(str(r[0])), float(r[1])) for r in rows]

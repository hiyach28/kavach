"""PII Vault service (AES-GCM encryption) — Phase 1 (F12)."""

from __future__ import annotations

import os
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.keywrap import aes_key_unwrap, aes_key_wrap
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import sha256_hex
from app.models.pii import PIIVault


class CryptoHelper:
    """AES-256-GCM and AES-KW helper."""

    @staticmethod
    def encrypt_gcm(plaintext: bytes, key: bytes) -> bytes:
        """Encrypt with AES-GCM. Returns nonce + ciphertext."""
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ct

    @staticmethod
    def decrypt_gcm(ciphertext: bytes, key: bytes) -> bytes:
        """Decrypt AES-GCM. Expects nonce + ciphertext."""
        aesgcm = AESGCM(key)
        nonce = ciphertext[:12]
        ct = ciphertext[12:]
        return aesgcm.decrypt(nonce, ct, None)

    @staticmethod
    def wrap_key(key_to_wrap: bytes, master_key: bytes) -> bytes:
        """Wrap DEK with KEK (master key) using AES Key Wrap."""
        return aes_key_wrap(master_key, key_to_wrap)

    @staticmethod
    def unwrap_key(wrapped_key: bytes, master_key: bytes) -> bytes:
        """Unwrap DEK with KEK."""
        return aes_key_unwrap(master_key, wrapped_key)


async def store_and_tokenize(
    values: list[str],
    case_id: uuid.UUID | None,
    db: AsyncSession,
    master_key: bytes,
) -> dict[str, str]:
    """
    Encrypt and store a list of plaintext strings in the PII vault.
    Returns a dict mapping {original_plaintext: token_hash}.
    """
    if not values:
        return {}

    # Dedup
    unique_values = list(set(values))
    token_map: dict[str, str] = {}
    vault_entries: list[PIIVault] = []

    for val in unique_values:
        token = sha256_hex(val)
        token_map[val] = token

        # Check if exists (tokens are deterministic)
        existing = await db.execute(select(PIIVault).where(PIIVault.token == token))
        if existing.scalar_one_or_none():
            continue  # Already in vault

        # Generate a random 32-byte Data Encryption Key (DEK) for this row
        dek = os.urandom(32)

        # Encrypt value with DEK
        val_bytes = val.encode("utf-8")
        ciphertext = CryptoHelper.encrypt_gcm(val_bytes, dek)

        # Wrap DEK with master key
        dek_wrapped = CryptoHelper.wrap_key(dek, master_key)

        vault_entries.append(
            PIIVault(
                case_id=case_id,
                token=token,
                ciphertext=ciphertext,
                dek_wrapped=dek_wrapped,
            )
        )

    if vault_entries:
        db.add_all(vault_entries)
        await db.commit()

    return token_map


async def decrypt_token(
    token: str,
    db: AsyncSession,
    master_key: bytes,
) -> str | None:
    """Decrypt a specific token back to plaintext."""
    result = await db.execute(select(PIIVault).where(PIIVault.token == token))
    vault_row = result.scalar_one_or_none()

    if not vault_row:
        return None

    # Unwrap DEK
    try:
        dek = CryptoHelper.unwrap_key(vault_row.dek_wrapped, master_key)
        # Decrypt payload
        plaintext_bytes = CryptoHelper.decrypt_gcm(vault_row.ciphertext, dek)
        return plaintext_bytes.decode("utf-8")
    except Exception:
        return None  # Bad key or corrupted data

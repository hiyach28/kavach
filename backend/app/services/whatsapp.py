"""WhatsApp channel stub — webhook-ready interface (Phase 3).

Per roadmap: "stub behind an interface (webhook-ready); demo via PWA — don't burn days on Meta business verification."

In production, a concrete implementation would:
  1. Verify webhook callback from Meta
  2. Parse incoming WhatsApp messages
  3. Call shield_svc.check() on the message content
  4. Send back the localised verdict via WhatsApp Business API

The stub logs incoming webhook payloads and returns the expected
handshake response so the integration point is validated.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass

logger = logging.getLogger("kavach.whatsapp")


@dataclass
class WhatsAppMessage:
    """Normalised incoming WhatsApp message."""
    from_number: str
    body: str
    message_id: str
    timestamp: int


def verify_webhook(mode: str, token: str, challenge: str, verify_token: str) -> str | None:
    """
    Webhook verification handshake (Meta requirement).
    Returns the challenge string if verification succeeds.

    In production, verify_token would come from env settings.
    """
    if mode == "subscribe" and token == verify_token:
        logger.info("whatsapp webhook verified")
        return challenge
    logger.warning("whatsapp webhook verification failed")
    return None


def validate_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Validate the SHA-256 signature of the webhook payload.
    Meta signs every webhook with the app secret.
    """
    if not signature_header:
        return False
    expected = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    # Meta sends signature as "sha256=..."
    received = signature_header.replace("sha256=", "").strip()
    return hmac.compare_digest(expected, received)


def parse_message(raw: dict) -> WhatsAppMessage | None:
    """
    Parse a WhatsApp Business API incoming message payload.
    Returns a WhatsAppMessage or None if the payload isn't a message.

    Stub implementation — logs the raw payload for debugging.
    """
    try:
        entry = raw.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            logger.debug("whatsapp: no messages in payload: %s", raw)
            return None

        msg = messages[0]
        parsed = WhatsAppMessage(
            from_number=msg.get("from", ""),
            body=msg.get("text", {}).get("body", ""),
            message_id=msg.get("id", ""),
            timestamp=msg.get("timestamp", 0),
        )
        logger.info("whatsapp: message from %s: %s", parsed.from_number, parsed.body[:100])
        return parsed
    except Exception as exc:
        logger.error("whatsapp: failed to parse message: %s", exc)
        return None


def build_reply(verdict_band: str, body: str, message_id: str) -> dict:
    """
    Build a reply payload for WhatsApp Business API.

    Stub — returns the data structure; actual API call would use
    `requests.post` to the Meta Graph API endpoint.
    """
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "",  # filled in by calling code with the original from_number
        "type": "text",
        "text": {"body": body},
        "context": {"message_id": message_id},
    }

"""Live Call Companion — scam-script stage detection engine (F33).

Provides offline-testable keyword-pattern scoring for scam call stages
(impersonation → threat → isolation → payment demand) across 5 languages.

The WebSocket endpoint in `api.v1.shield` uses this engine to drive the
Live Call Companion demo. Stage keyword sets are maintained here so
they can be unit-tested independently of the WebSocket transport.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ── Stage definitions ───────────────────────────────────────────────────────────

@dataclass
class StageState:
    name: str
    score: float = 0.0
    triggered: bool = False
    keyword_hits: int = 0


@dataclass
class ScamScoreResult:
    stages: dict[str, StageState] = field(default_factory=dict)
    max_score: float = 0.0
    newly_triggered: list[str] = field(default_factory=list)
    current_stage: str = "listening"   # listening | caution | danger


# Multi-language keyword sets for each scam stage
STAGE_KEYWORDS: dict[str, list[str]] = {
    "impersonation": [
        "police", "cbi", "narcotics", "customs", "fbi", "interpol",
        "court", "judge", "lawyer", "government officer", "commissioner",
        "dsp", "inspector", "constable", "sub inspector",
        "sahab", "thana", "daroga", "sir ji",
        "authority", "official", "department", "head office", "headquarters",
        "senior", "sir", "madam", "officer", "ips", "ias",
    ],
    "threat": [
        "arrest", "warrant", "case filed", "notice", "summons",
        "legal action", "criminal case", "supreme court", "high court",
        "imprisonment", "jail", "non-bailable", "fir", "court case",
        "prosecution", "punishment", "drugs found", "parcel", "courier",
        "ndps", "money laundering",
        "girfatar", "jael", "danda", "kasur", "vakil", "kanoon", "faisla",
    ],
    "isolation": [
        "don't tell anyone", "confidential", "secret", "private matter",
        "stay on line", "don't hang up", "don't discuss", "not a word",
        "nobody else", "family", "alone", "separate room", "home",
        "nobody should know", "don't share", "between us", "your family",
        "kisi ko mat batana", "rahasya", "chup", "tanha", "akela",
        "ghar", "parivar", "apne tak", "mein batata hun",
        "this is between us", "keep this to yourself",
    ],
    "payment": [
        "upi", "payment", "transfer", "bank account", "otp",
        "send money", "digital arrest", "online payment", "scan code",
        "qr code", "net banking", "google pay", "phone pe", "paytm",
        "bank detail", "deposit", "fine", "penalty",
        "account number", "ifsc", "verify your account",
        "paisa", "rupay", "bhugtan", "khata", "transaction",
        "payment abhi karo", "account verify", "otp bhejo",
        "skype", "nodal officer", "demand draft", "processing fee",
        "security deposit", "now", "immediately", "urgent",
    ],
}


def score_transcript(text: str, stages: dict[str, StageState] | None = None) -> ScamScoreResult:
    """
    Score a transcript chunk against all scam stages.

    Maintains state across calls if `stages` dict is reused.
    Returns current scores, newly triggered stages, and overall stage.
    """
    if stages is None:
        stages = {
            name: StageState(name=name)
            for name in STAGE_KEYWORDS
        }

    text_lower = text.lower()
    newly_triggered: list[str] = []
    max_score = 0.0

    for name, keywords in STAGE_KEYWORDS.items():
        state = stages[name]
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            state.keyword_hits += hits
            # Incremental scoring: each hit adds to the stage score, diminishing returns
            increment = min(hits * 0.15, 0.8)
            state.score = min(state.score + increment, 1.0)
            if state.score >= 0.4 and not state.triggered:
                state.triggered = True
                newly_triggered.append(name)
        max_score = max(max_score, state.score)

    # Determine overall stage
    payment_triggered = stages["payment"].triggered
    threat_triggered = stages["threat"].triggered

    if payment_triggered:
        current_stage = "danger"
    elif threat_triggered:
        current_stage = "danger"
    elif any(s.triggered for s in stages.values()):
        current_stage = "caution"
    else:
        current_stage = "listening"

    return ScamScoreResult(
        stages=stages,
        max_score=max_score,
        newly_triggered=newly_triggered,
        current_stage=current_stage,
    )

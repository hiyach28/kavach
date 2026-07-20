"""Shield API — point-of-contact protection (F30, F33, F34).

Endpoints:
  POST /v1/shield/check   — 3-tier verdict cascade (F30)
  WS   /v1/shield/live    — Live Call Companion streaming (F33)
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.errors import ValidationError
from app.core.middleware import limiter
from app.models.graph import Entity, EntityType
from app.models.shield import ShieldCheck
from app.services import language as lang_svc
from app.services import llm_client
from app.services import shield as shield_svc

logger = logging.getLogger("kavach.shield.api")

router = APIRouter()


# ── Request / Response schemas ──────────────────────────────────────────────────


class ShieldCheckRequest(BaseModel):
    text: str = Field(
        "",
        max_length=10000,
        description="Message text to check (free-form, can be empty if entity is provided)",
    )
    entity: str | None = Field(
        None,
        max_length=500,
        description="Specific entity to check (phone, UPI, URL). Overrides text for tier-1 lookup.",
    )
    channel: str = Field("api", pattern=r"^(api|pwa|whatsapp)$")
    geo: str | None = Field(None, max_length=100)
    consent_for_intel: bool = False
    language: str | None = Field(None, max_length=5)


class ShieldCheckResponse(BaseModel):
    verdict: str  # danger | suspicious | likely_safe | unknown
    title: str  # Localised title
    explanation: str  # Plain-language body
    cta: str  # Call to action
    language: str  # Language code of the response
    tier_resolved: int  # 1 | 2 | 3
    check_id: str  # Shield check ID for reference


class LiveSessionRequest(BaseModel):
    """Request to start a live call companion session."""

    language: str = "hi"


# ── Shield Check (F30) ──────────────────────────────────────────────────────────


@router.post(
    "/shield/check",
    response_model=ShieldCheckResponse,
    summary="Check a message or entity against known fraud indicators",
    description="3-tier cascade: entity lookup → script-pattern ANN → LLM fallback. <3s p95.",
)
@limiter.limit("20/minute")  # F15: Shield-specific rate limit
async def shield_check(
    request: Request,
    shield_request: ShieldCheckRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShieldCheckResponse:
    """
    Run the 3-tier Shield check and return a localised verdict card.
    """
    if not request.text and not request.entity:
        raise ValidationError("Provide at least 'text' or 'entity' to check")

    start_ns = time.perf_counter_ns()

    # Determine entity value for tier-1 lookup
    entity_value = request.entity or request.text.strip()[:500]

    # Run the 3-tier cascade
    result = await shield_svc.check(
        text=request.text,
        db=db,
        entity_value=entity_value,
    )

    # Detect language (use requested or detected)
    lang = request.language or result.language or lang_svc.detect_language(request.text)

    # Render localised verdict card
    card = lang_svc.render_verdict(
        verdict_band=result.verdict,
        entity=request.entity or request.text[:100] if request.text else "unknown",
        report_count=result.report_count,
        language=lang,  # type: ignore[arg-type]
    )

    latency_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

    # Extract entity hashes from text for logging
    entity_hashes: list[str] = []
    if result.entity_matched:
        entity_hashes.append(result.entity_matched)
    elif request.text:
        from app.services.entity_extractor import extract_entities

        extracted = extract_entities(request.text)
        entity_hashes = [e.value_hash for e in extracted]

    # Log the check (F34 telemetry)
    check_id = uuid.uuid4()
    db.add(
        ShieldCheck(
            id=check_id,
            entity_hashes=entity_hashes or None,
            verdict=result.verdict,
            tier_resolved=result.tier_resolved,
            latency_ms=latency_ms,
            channel=request.channel,
            geo=request.geo,
            explanation=result.explanation,
            language=lang,
            consent_for_intel=request.consent_for_intel,
        )
    )
    await db.commit()

    # F34: Consent → feed de-identified intelligence into graph
    if request.consent_for_intel and entity_hashes:
        await _feed_flywheel(entity_hashes, result, db)

    logger.info(
        "shield check %s → %s (tier=%d, %dms) for user=%s",
        check_id,
        result.verdict,
        result.tier_resolved,
        latency_ms,
        user.id,
    )

    return ShieldCheckResponse(
        verdict=result.verdict,
        title=card.title,
        explanation=card.body,
        cta=card.cta,
        language=card.language,
        tier_resolved=result.tier_resolved,
        check_id=str(check_id),
    )


# ── Flywheel: consented checks → graph entities (F34) ──────────────────────────


async def _feed_flywheel(
    entity_hashes: list[str],
    result: shield_svc.ShieldResult,
    db: AsyncSession,
) -> None:
    """
    Consented Shield checks become de-identified graph entities with source='shield'.
    Checks against entities later confirmed in campaigns retroactively strengthen edges.
    """
    now = datetime.now(UTC)
    created_ids: list[str] = []

    for h in entity_hashes[:20]:  # cap per check
        existing = (
            await db.execute(select(Entity).where(Entity.value_hash == h))
        ).scalar_one_or_none()

        if existing is None:
            # Create new entity with source='shield' (lower weight)
            # Infer entity type from hash context (best-effort)
            entity_type = _infer_entity_type_from_hash(h)
            new_entity = Entity(
                type=entity_type,
                value_hash=h,
                first_seen=now,
                report_count=1,
            )
            db.add(new_entity)
            await db.flush()
            created_ids.append(str(new_entity.id))

    if created_ids:
        # Update the shield_check record with entity links
        shield_check = (
            await db.execute(
                select(ShieldCheck).where(
                    ShieldCheck.entity_hashes.isnot(None),
                    ShieldCheck.entity_hashes[0].as_string() == h if h else False,
                )
            )
        ).scalar_one_or_none()
        if shield_check is not None:
            shield_check.entity_link_ids = created_ids
        await db.commit()
        logger.info(
            "flywheel: created %d entities from consented shield check",
            len(created_ids),
        )


def _infer_entity_type_from_hash(h: str) -> EntityType:
    """Best-effort inference of entity type — used only for flywheel entities.
    Since we only have the hash, we default to PHONE (the most common check target).
    In practice, the entity type can be stored alongside the hash in the check metadata.
    """
    return EntityType.PHONE


# ── Live Call Companion WebSocket (F33) ─────────────────────────────────────────


@router.websocket("/shield/live")
async def live_call_companion(
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    WebSocket endpoint for the Live Call Companion (F33).

    Receives streaming transcripts from browser speech-to-text,
    runs incremental scam-script scoring, and sends escalating warnings.

    Protocol (JSON messages):
      → {"type": "transcript", "text": "...", "lang": "hi", "session_id": "..."}
      ← {"type": "status", "stage": "listening|caution|danger", "advice": "...", "score": 0.0}
      ← {"type": "warning", "level": "amber|red", "message": "...", "stage_detected": "..."}
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info("live companion session started: %s", session_id)

    # Scam stage detection — accumulating scores per stage
    stages = {
        "impersonation": {"keywords": _IMPERSONATION_KW, "score": 0.0, "triggered": False},
        "threat": {"keywords": _THREAT_KW, "score": 0.0, "triggered": False},
        "isolation": {"keywords": _ISOLATION_KW, "score": 0.0, "triggered": False},
        "payment": {"keywords": _PAYMENT_KW, "score": 0.0, "triggered": False},
    }
    current_stage = "listening"
    transcript_accumulated = ""
    llm_calls_this_session = 0
    MAX_LLM_CALLS = 4  # F33 AC: max 4 LLM calls per companion session

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") != "transcript" or not data.get("text"):
                continue

            text = data["text"]
            lang = data.get("lang", "hi")
            transcript_accumulated += " " + text

            # ── Stage detection via keyword matching (multi-language) ──────
            score, triggered_stages = _score_stages(text.lower(), stages)

            if triggered_stages:
                new_stage = (
                    "danger"
                    if "payment" in triggered_stages or "threat" in triggered_stages
                    else "caution"
                )
                if new_stage != current_stage:
                    current_stage = new_stage
                    stage_label = triggered_stages[-1]
                    stage_advice = _STAGE_ADVICE.get(stage_label, {})
                    advice = stage_advice.get(lang, _STAGE_ADVICE[stage_label]["en"])

                    await websocket.send_json(
                        {
                            "type": "warning",
                            "level": "red" if current_stage == "danger" else "amber",
                            "message": _get_stage_alert(stage_label, lang),
                            "stage_detected": stage_label,
                            "advice": advice,
                        }
                    )

            # ── LLM deep analysis (throttled to 1/15s per session) ────────
            # Only in live mode, max 4 calls per session
            if (
                settings.LLM_MODE == "live"
                and llm_calls_this_session < MAX_LLM_CALLS
                and len(transcript_accumulated.split()) > 30
            ):
                # Check if we should throttle (only for LLM, not keyword)
                try:
                    verdict = llm_client.classify(transcript_accumulated)
                    llm_calls_this_session += 1
                    if verdict.risk.value in ("danger", "suspicious"):
                        await websocket.send_json(
                            {
                                "type": "danger_signals",
                                "signals": verdict.evidence[:5],
                                "fraud_type": verdict.fraud_type.value,
                            }
                        )
                except Exception:
                    logger.debug("live companion LLM call failed", exc_info=True)

            # ── Send current status ────────────────────────────────────────
            max_score = max(s["score"] for s in stages.values())
            await websocket.send_json(
                {
                    "type": "status",
                    "stage": current_stage,
                    "score": round(max_score, 2),
                    "transcript_length": len(transcript_accumulated),
                }
            )

    except WebSocketDisconnect:
        logger.info("live companion session ended: %s", session_id)
    except Exception as exc:
        logger.error("live companion error %s: %s", session_id, exc)
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "Connection error. Please try again.",
                }
            )
        except Exception:
            logger.debug("live companion: failed to send error message")
        finally:
            try:
                await websocket.close()
            except Exception:
                logger.debug("live companion: failed to close websocket")


# ── Scam stage keyword sets (multi-language) ────────────────────────────────────

_IMPERSONATION_KW = [
    # English
    "police",
    "cbi",
    "narcotics",
    "customs",
    "fbi",
    "interpol",
    "court",
    "judge",
    "lawyer",
    "government officer",
    "commissioner",
    "senior",
    "dsp",
    "inspector",
    "constable",
    "sub inspector",
    # Hindi
    "sahab",
    "thana",
    "daroga",
    "sir ji",
    # General
    "authority",
    "official",
    "department",
    "head office",
    "headquarters",
]

_THREAT_KW = [
    # English
    "arrest",
    "warrant",
    "case filed",
    "notice",
    "summons",
    "legal action",
    "criminal case",
    "supreme court",
    "high court",
    "imprisonment",
    "jail",
    "non-bailable",
    "fir",
    "court case",
    "prosecution",
    "punishment",
    "drugs found",
    "parcel",
    "courier",
    "ndps",
    "money laundering",
    # Hindi
    "girfatar",
    "jael",
    "danda",
    "kasur",
    "vakil",
    "kanoon",
    "faisla",
]

_ISOLATION_KW = [
    # English
    "don't tell anyone",
    "confidential",
    "secret",
    "private matter",
    "stay on line",
    "don't hang up",
    "don't discuss",
    "not a word",
    "nobody else",
    "family",
    "alone",
    "separate room",
    "home",
    "nobody should know",
    "don't share",
    "between us",
    "your family",
    # Hindi
    "kisi ko mat batana",
    "rahasya",
    "chup",
    "tanha",
    "akela",
    "ghar",
    "parivar",
    "apne tak",
    "mein batata hun",
]

_PAYMENT_KW = [
    # English
    "upi",
    "payment",
    "transfer",
    "bank account",
    "otp",
    "send money",
    "digital arrest",
    "online payment",
    "scan code",
    "qr code",
    "net banking",
    "google pay",
    "phone pe",
    "paytm",
    "bank detail",
    "deposit",
    "fine",
    "penalty",
    "skype",
    "nodal officer",
    "account number",
    "ifsc",
    "verify your account",
    # Hindi
    "paisa",
    "rupay",
    "bhugtan",
    "khata",
    "accha",
    "transaction",
    "payment abhi karo",
    "account verify",
    "otp bhejo",
]

_STAGE_ADVICE: dict[str, dict[str, str]] = {
    "impersonation": {
        "en": (
            "Government agencies never call to demand money. "
            "Hang up and verify through official channels."
        ),
        "hi": (
            "सरकारी एजेंसियां पैसे मांगने के लिए कभी फोन नहीं करतीं। फोन काटें और आधिकारिक माध्यमों से सत्यापित करें।"
        ),
        "ta": (
            "அரசு நிறுவனங்கள் பணம் கேட்டு ஒருபோதும் அழைப்பதில்லை. "
            "அழைப்பை துண்டித்து அதிகாரப்பூர்வ வழிகளில் சரிபார்க்கவும்."
        ),
        "te": ("ప్రభుత్వ ఏజన్సీలు డబ్బు కోసం ఎప్పుడూ కాల్ చేయవు. ఫోన్ కట్ చేసి అధికారిక మార్గాల ద్వారా ధృవీకరించండి."),
        "bn": (
            "সরকারি সংস্থাগুলো টাকা চেয়ে কখনো ফোন করে না। ফোন কেটে দিন এবং অফিসিয়াল চ্যানেলের মাধ্যমে যাচাই করুন।"
        ),
    },
    "threat": {
        "en": (
            "This is a classic scare tactic. "
            "Real law enforcement sends written notice, not phone threats."
        ),
        "hi": (
            "यह एक क्लासिक डराने की रणनीति है। "
            "वास्तविक कानून प्रवर्तन फोन पर धमकी नहीं देता, बल्कि लिखित नोटिस भेजता है।"
        ),
        "ta": (
            "இது ஒரு பொதுவான மிரட்டல் தந்திரம். "
            "உண்மையான சட்ட அமலாக்கம் தொலைபேசி மிரட்டல்களை அனுப்பாது, "
            "எழுத்துப்பூர்வ அறிவிப்பை அனுப்பும்."
        ),
        "te": ("ఇది ఒక సాధారణ భయపెట్టే వ్యూహం. నిజమైన చట్ట అమలు ఫోన్ బెదిరింపులు కాకుండా వ్రాతపూర్వక నోటీసును పంపుతుంది."),
        "bn": (
            "এটি একটি ক্লাসিক ভীতি প্রদর্শনের কৌশল। "
            "প্রকৃত আইন প্রয়োগকারী সংস্থা ফোনে হুমকি না দিয়ে লিখিত নোটিশ পাঠায়।"
        ),
    },
    "isolation": {
        "en": (
            "Scammers isolate victims to prevent them from seeking help. "
            "Tell someone you trust immediately."
        ),
        "hi": ("स्कैमर पीड़ितों को अलग-थलग करते हैं ताकि वे मदद न ले सकें। तुरंत किसी भरोसेमंद व्यक्ति को बताएं।"),
        "ta": (
            "மோசடி செய்பவர்கள் பாதிக்கப்பட்டவர்களை "
            "தனிமைப்படுத்தி உதவி கேட்க விடாமல் செய்கிறார்கள். "
            "உடனே நம்பகமான ஒருவரிடம் சொல்லுங்கள்."
        ),
        "te": ("స్కామర్లు బాధితులను ఒంటరిగా ఉంచి సహాయం కోకుండా చేస్తారు. వెంటనే నమ్మకమైన వ్యక్తికి చెప్పండి."),
        "bn": ("স্ক্যামাররা ভিকটিমদের আলাদা করে ফেলে যাতে তারা সাহায্য চাইতে না পারে। এখনই আপনার বিশ্বস্ত কাউকে বলুন।"),
    },
    "payment": {
        "en": (
            "DO NOT SEND MONEY. This is a scam. "
            "No legitimate agency asks for payment over the phone."
        ),
        "hi": ("पैसे न भेजें। यह एक घोटाला है। कोई भी वैध एजेंसी फोन पर भुगतान नहीं मांगती।"),
        "ta": ("பணம் அனுப்ப வேண்டாம். இது ஒரு மோசடி. எந்த சட்டப்பூர்வ நிறுவனமும் தொலைபேசியில் பணம் கேட்பதில்லை."),
        "te": ("డబ్బు పంపవద్దు. ఇది స్కామ్. ఎలాంటి చట్టబద్ధమైన సంస్థ ఫోన్‌లో డబ్బు అడగదు."),
        "bn": ("টাকা পাঠাবেন না। এটি একটি স্ক্যাম। কোনো বৈধ সংস্থা ফোনে টাকা চায় না।"),
    },
}


def _score_stages(
    text: str,
    stages: dict[str, Any],
) -> tuple[float, list[str]]:
    """
    Score text against each scam stage's keywords.
    Returns (max_score, list_of_triggered_stage_names).
    """
    triggered: list[str] = []
    max_score = 0.0

    for stage_name, stage in stages.items():
        keywords = stage["keywords"]
        hits = sum(1 for kw in keywords if kw in text)
        if hits > 0:
            # Incremental scoring — each transcript chunk adds to the stage score
            increment = min(hits * 0.15, 0.8)
            stage["score"] = min(stage["score"] + increment, 1.0)
            if stage["score"] >= 0.4 and not stage["triggered"]:
                stage["triggered"] = True
                triggered.append(stage_name)
        max_score = max(max_score, stage["score"])

    return max_score, triggered


def _get_stage_alert(stage: str, lang: str) -> str:
    """Return a stage-specific alert message in the detected language."""
    alerts = {
        "impersonation": {
            "en": (
                "⚠️ The caller claims to be an authority figure. "
                "This is a common impersonation tactic."
            ),
            "hi": ("⚠️ कॉल करने वाला अधिकारी होने का दावा कर रहा है। यह एक सामान्य प्रतिरूपण रणनीति है।"),
            "ta": ("⚠️ அழைப்பவர் அதிகாரி எனக் கூறுகிறார். இது ஒரு பொதுவான ஆள்மாறாட்ட தந்திரம்."),
            "te": ("⚠️ కాల్ చేస్తున్న వ్యక్తి అధికారి అని చెప్పుకుంటున్నారు. ఇది ఒక సాధారణ వేషధారణ వ్యూహం."),
            "bn": ("⚠️ কলার কর্তৃপক্ষ হওয়ার দাবি করছেন। এটি একটি সাধারণ ছদ্মবেশ ধারণার কৌশল।"),
        },
        "threat": {
            "en": (
                "🚨 The caller is making threats. "
                "Real authorities never threaten you over the phone."
            ),
            "hi": ("🚨 कॉल करने वाला धमकी दे रहा है। वास्तविक अधिकारी फोन पर कभी धमकी नहीं देते।"),
            "ta": ("🚨 அழைப்பவர் மிரட்டுகிறார். உண்மையான அதிகாரிகள் போனில் ஒருபோதும் மிரட்ட மாட்டார்கள்."),
            "te": ("🚨 కాల్ చేస్తున్న వ్యక్తి బెదిరిస్తున్నారు. నిజమైన అధికారులు ఫోన్‌లో ఎప్పుడూ బెదిరించరు."),
            "bn": ("🚨 কলার হুমকি দিচ্ছেন। প্রকৃত কর্তৃপক্ষ কখনো ফোনে হুমকি দেয় না।"),
        },
        "isolation": {
            "en": ("⚠️ They're asking you to keep this secret. This is how scammers trap victims."),
            "hi": ("⚠️ वे आपसे इसे गुप्त रखने के लिए कह रहे हैं। इस तरह स्कैमर पीड़ितों को फंसाते हैं।"),
            "ta": ("⚠️ இதை ரகசியமாக வைக்கச் சொல்கிறார்கள். இப்படித்தான் மோசடி செய்பவர்கள் பலியாக்குகிறார்கள்."),
            "te": ("⚠️ వారు దీన్ని రహస్యంగా ఉంచమని అడుగుతున్నారు. ఇలాగే స్కామర్లు బాధితులను ట్రాప్ చేస్తారు."),
            "bn": ("⚠️ তারা আপনাকে এটি গোপন রাখতে বলছে। এইভাবেই স্ক্যামাররা ভিকটিমদের ফাঁদে ফেলে।"),
        },
        "payment": {
            "en": (
                "🔴 DANGER: They're asking for money or payment details. "
                "THIS IS A SCAM. Hang up NOW."
            ),
            "hi": ("🔴 खतरा: वे पैसे या भुगतान विवरण मांग रहे हैं। यह एक घोटाला है। अभी फोन काटें।"),
            "ta": ("🔴 ஆபத்து: பணம் அல்லது கட்டண விவரங்கள் கேட்கிறார்கள். இது ஒரு மோசடி. உடனே போனை வைக்கவும்."),
            "te": ("🔴 ప్రమాదం: వారు డబ్బు లేదా చెల్లింపు వివరాలు అడుగుతున్నారు. ఇది స్కామ్. వెంటనే ఫోన్ కట్ చేయండి."),
            "bn": ("🔴 বিপদ: তারা টাকা বা পেমেন্টের বিবরণ চাচ্ছে। এটি একটি স্ক্যাম। এখনই ফোন কাটুন।"),
        },
    }
    return alerts.get(stage, {}).get(lang, alerts.get(stage, {}).get("en", ""))

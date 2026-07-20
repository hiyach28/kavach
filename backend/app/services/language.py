"""Language detection and verdict templates (F31).

Detect script/language via Unicode-range heuristics, then render a
plain-language verdict card using reviewed templates with slot-filling.
Never uses free LLM generation for citizen-facing text (consistency + safety).

Launch languages: hi (Hindi), en (English), ta (Tamil), te (Telugu), bn (Bengali).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# ── Supported languages ───────────────────────────────────────────────────────
LangCode = Literal["hi", "en", "ta", "te", "bn"]
SUPPORTED_LANGUAGES: list[LangCode] = ["hi", "en", "ta", "te", "bn"]

# ── Language detection via Unicode ranges ──────────────────────────────────────
# Priority-ordered: more specific scripts checked first.
_LANG_SIGNATURES: list[tuple[LangCode, list[tuple[int, int]]]] = [
    ("hi", [(0x0900, 0x097F)]),  # Devanagari
    ("bn", [(0x0980, 0x09FF)]),  # Bengali
    ("ta", [(0x0B80, 0x0BFF)]),  # Tamil
    ("te", [(0x0C00, 0x0C7F)]),  # Telugu
]

# Latin-based → check keywords to distinguish Hindi-Urdu romanized vs English
_HINDI_KEYWORDS = {
    "kya",
    "hai",
    "aap",
    "apka",
    "apko",
    "karo",
    "kare",
    "nahi",
    "raha",
    "rahi",
    "sir",
    "ji",
    "bahut",
    "mera",
    "meri",
    "mujhe",
    "tum",
    "tumhara",
    "yeh",
    "vo",
    "aur",
    "kaise",
    "kahan",
    "kab",
    "kitna",
    "thoda",
    "police",
    "cbi",
    "arrest",
    "drugs",
    "narcotics",
    "customs",
    "number",
    "account",
    "upi",
    "transaction",
    "otp",
    "bank",
    "panic",
    "mummy",
    "papa",
    "beta",
    "beti",
}


def detect_language(text: str) -> LangCode:
    """
    Detect language/script of the given text.

    Strategy:
      1. Check for non-Latin Unicode script ranges (Devanagari → hi, etc.)
      2. If Latin-only, check Hindi-Urdu romanized keywords.
      3. Default to English.
    """
    if not text or not text.strip():
        return "en"

    seen_scripts: set[LangCode] = set()

    for lang_code, ranges in _LANG_SIGNATURES:
        for cp in text:
            code_point = ord(cp)
            for lo, hi in ranges:
                if lo <= code_point <= hi:
                    seen_scripts.add(lang_code)
                    break
            if seen_scripts:
                break

    # If exactly one non-Latin script found, return it
    if len(seen_scripts) == 1:
        return seen_scripts.pop()
    if len(seen_scripts) > 1:
        # Mixed scripts — return the dominant one by char count
        counts: dict[LangCode, int] = {}
        for lang_code, ranges in _LANG_SIGNATURES:
            count = 0
            for cp in text:
                code_point = ord(cp)
                for lo, hi in ranges:
                    if lo <= code_point <= hi:
                        count += 1
                        break
            counts[lang_code] = count
        if counts:
            return max(counts, key=counts.get)  # type: ignore[return-value]

    # Latin-only: check Hindi keywords
    words = set(re.sub(r"[^a-zA-Z]", " ", text.lower()).split())
    hindi_overlap = len(words & _HINDI_KEYWORDS)

    if hindi_overlap >= 2 or (hindi_overlap >= 1 and len(words) <= 10):
        return "hi"  # Romanized Hindi / Hinglish

    return "en"


# ── Verdict templates (F31) — reviewed, never LLM-generated ───────────────────
# Slot: {entity} = the checked phone/UPI/URL, {cta} = call to action

_VERDICT_TEMPLATES: dict[LangCode, dict[str, dict[str, str]]] = {
    "en": {
        "danger": {
            "title": "🚨 This is a known fraud contact",
            "body": (
                "The information you provided — **{entity}** — is linked to "
                "**{report_count} confirmed fraud report(s)** in our system. "
                "Do NOT send money, share OTPs, or follow any instructions."
            ),
            "cta": "Block this contact immediately and report to cybercrime.gov.in or 1930.",
        },
        "suspicious": {
            "title": "⚠️ This looks suspicious",
            "body": (
                "We found activity patterns similar to known scams. "
                "**{entity}** has been reported **{report_count} time(s)**. "
                "Be extremely cautious."
            ),
            "cta": "Do not share personal information. Verify independently before acting.",
        },
        "likely_safe": {
            "title": "✅ Looks safe — but stay alert",
            "body": (
                "We found **{report_count} report(s)** linked to {entity}, "
                "but nothing that clearly indicates a scam. "
                "Always stay cautious with unknown contacts."
            ),
            "cta": "If something feels off, trust your instinct and report via 1930.",
        },
        "unknown": {
            "title": "ℹ️ No records found",
            "body": (
                "We have no records linking **{entity}** to fraud in our system. "
                "This doesn't guarantee it's safe — scammers constantly change tactics."
            ),
            "cta": "Stay cautious. Report suspicious contacts to 1930.",
        },
    },
    "hi": {
        "danger": {
            "title": "🚨 यह एक ज्ञात धोखाधड़ी संपर्क है",
            "body": (
                "आपके द्वारा दी गई जानकारी — **{entity}** — हमारे सिस्टम में "
                "**{report_count} पुष्ट धोखाधड़ी रिपोर्ट(ों)** से जुड़ी है। "
                "पैसे न भेजें, OTP साझा न करें, या किसी भी निर्देश का पालन न करें।"
            ),
            "cta": "इस संपर्क को तुरंत ब्लॉक करें और cybercrime.gov.in या 1930 पर रिपोर्ट करें।",
        },
        "suspicious": {
            "title": "⚠️ यह संदिग्ध लग रहा है",
            "body": (
                "हमें ज्ञात घोटालों के समान गतिविधि पैटर्न मिले। "
                "**{entity}** के खिलाफ **{report_count} रिपोर्ट(ें)** दर्ज हैं। "
                "अत्यधिक सावधानी बरतें।"
            ),
            "cta": "व्यक्तिगत जानकारी साझा न करें। कार्रवाई करने से पहले स्वतंत्र रूप से सत्यापित करें।",
        },
        "likely_safe": {
            "title": "✅ सुरक्षित लगता है — लेकिन सावधान रहें",
            "body": (
                "हमें {entity} से जुड़ी **{report_count} रिपोर्ट(ें)** मिलीं, "
                "लेकिन स्पष्ट रूप से धोखाधड़ी का कोई संकेत नहीं है। "
                "अज्ञात संपर्कों से हमेशा सावधान रहें।"
            ),
            "cta": "अगर कुछ गलत लगे, तो अपनी प्रवृत्ति पर भरोसा करें और 1930 पर रिपोर्ट करें।",
        },
        "unknown": {
            "title": "ℹ️ कोई रिकॉर्ड नहीं मिला",
            "body": (
                "हमारे सिस्टम में **{entity}** को धोखाधड़ी से जोड़ने वाला कोई रिकॉर्ड नहीं है। "
                "यह गारंटी नहीं है कि यह सुरक्षित है — स्कैमर्स लगातार अपनी रणनीति बदलते हैं।"
            ),
            "cta": "सावधान रहें। संदिग्ध संपर्कों की 1930 पर रिपोर्ट करें।",
        },
    },
    "ta": {
        "danger": {
            "title": "🚨 இது அறியப்பட்ட மோசடி தொடர்பு",
            "body": (
                "நீங்கள் வழங்கிய தகவல் — **{entity}** — எங்கள் அமைப்பில் "
                "**{report_count} உறுதிப்படுத்தப்பட்ட மோசடி புகார்(களுடன்)** இணைக்கப்பட்டுள்ளது. "
                "பணம் அனுப்ப வேண்டாம், OTP-களைப் பகிர வேண்டாம், அல்லது எந்த அறிவுறுத்தல்களையும் பின்பற்ற வேண்டாம்."
            ),
            "cta": (
                "இந்த தொடர்பை உடனடியாகத் தடுக்கவும் மற்றும் cybercrime.gov.in அல்லது 1930 இல் புகாரளிக்கவும்."
            ),
        },
        "suspicious": {
            "title": "⚠️ இது சந்தேகத்திற்குரியதாகத் தெரிகிறது",
            "body": (
                "அறியப்பட்ட மோசடிகளை ஒத்த செயல்பாட்டு வடிவங்களைக் கண்டோம். "
                "**{entity}** எதிராக **{report_count} புகார்(கள்)** பதிவு செய்யப்பட்டுள்ளன. "
                "மிகுந்த எச்சரிக்கையுடன் இருங்கள்."
            ),
            "cta": "தனிப்பட்ட தகவல்களைப் பகிர வேண்டாம். செயல்படுவதற்கு முன் சுயாதீனமாக சரிபார்க்கவும்.",
        },
        "likely_safe": {
            "title": "✅ பாதுகாப்பாகத் தெரிகிறது — ஆனால் விழிப்புடன் இருங்கள்",
            "body": (
                "{entity} உடன் இணைக்கப்பட்ட **{report_count} புகார்(கள்)** எங்களுக்குக் கிடைத்தன, "
                "ஆனால் தெளிவான மோசடி எதுவும் இல்லை. "
                "அறிமுகமில்லாத தொடர்புகளுடன் எப்போதும் விழிப்புடன் இருங்கள்."
            ),
            "cta": "ஏதேனும் சந்தேகம் இருந்தால், உங்கள் உள்ளுணர்வை நம்பி 1930 இல் புகாரளிக்கவும்.",
        },
        "unknown": {
            "title": "ℹ️ எந்த பதிவும் இல்லை",
            "body": (
                "எங்கள் அமைப்பில் **{entity}** ஐ மோசடியுடன் இணைக்கும் எந்த பதிவும் எங்களிடம் இல்லை. "
                "இது பாதுகாப்பானது என்று இது உத்தரவாதம் அளிக்கவில்லை"
                " — மோசடி செய்பவர்கள் தொடர்ந்து தந்திரங்களை மாற்றுகிறார்கள்."
            ),
            "cta": "விழிப்புடன் இருங்கள். சந்தேகத்திற்குரிய தொடர்புகளை 1930 இல் புகாரளிக்கவும்.",
        },
    },
    "te": {
        "danger": {
            "title": "🚨 ఇది తెలిసిన స్కామ్ కాంటాక్ట్",
            "body": (
                "మీరు అందించిన సమాచారం — **{entity}** — మా సిస్టమ్లో "
                "**{report_count} ధృవీకరించబడిన మోసపూరిత నివేదిక(ల)తో** ముడిపడి ఉంది. "
                "డబ్బు పంపవద్దు, OTPలను షేర్ చేయవద్దు, లేదా ఎలాంటి సూచనలను అనుసరించవద్దు."
            ),
            "cta": "ఈ కాంటాక్ట్‌ను వెంటనే బ్లాక్ చేయండి మరియు cybercrime.gov.in లేదా 1930కి రిపోర్ట్ చేయండి.",
        },
        "suspicious": {
            "title": "⚠️ ఇది అనుమానాస్పదంగా ఉంది",
            "body": (
                "తెలిసిన స్కామ్‌లను పోలిన కార్యాచరణ నమూనాలను కనుగొన్నాము. "
                "**{entity}** పై **{report_count} నివేదిక(లు)** నమోదు అయ్యాయి. "
                "చాలా జాగ్రత్తగా ఉండండి."
            ),
            "cta": "వ్యక్తిగత సమాచారాన్ని షేర్ చేయవద్దు. చర్య తీసుకునే ముందు స్వతంత్రంగా ధృవీకరించండి.",
        },
        "likely_safe": {
            "title": "✅ సురక్షితంగా ఉంది — కానీ అప్రమత్తంగా ఉండండి",
            "body": (
                "{entity}తో ముడిపడిన **{report_count} నివేదిక(లు)** మాకు లభించాయి, "
                "కానీ స్పష్టమైన మోసం ఏమీ లేదు. "
                "తెలియని కాంటాక్ట్‌లతో ఎల్లప్పుడూ అప్రమత్తంగా ఉండండి."
            ),
            "cta": "ఏదైనా సరిగ్గా లేదనిపిస్తే, మీ అంతర్ దృష్టిని నమ్మి 1930కి రిపోర్ట్ చేయండి.",
        },
        "unknown": {
            "title": "ℹ️ రికార్డులు ఏవీ కనుగొనబడలేదు",
            "body": (
                "మా సిస్టమ్‌లో **{entity}** ను మోసంతో ముడిపెట్టే రికార్డు మాకు లేదు. "
                "ఇది సురక్షితమని హామీ ఇవ్వదు — స్కామర్లు నిరంతరం వ్యూహాలు మారుస్తుంటారు."
            ),
            "cta": "అప్రమత్తంగా ఉండండి. అనుమానాస్పద కాంటాక్ట్‌లను 1930కి రిపోర్ట్ చేయండి.",
        },
    },
    "bn": {
        "danger": {
            "title": "🚨 এটি একটি পরিচিত জালিয়াতি যোগাযোগ",
            "body": (
                "আপনার দেওয়া তথ্য — **{entity}** — আমাদের সিস্টেমে "
                "**{report_count} টি নিশ্চিত জালিয়াতি রিপোর্টের** সাথে যুক্ত। "
                "টাকা পাঠাবেন না, OTP শেয়ার করবেন না, বা কোনো নির্দেশ অনুসরণ করবেন না।"
            ),
            "cta": "এই যোগাযোগটি অবিলম্বে ব্লক করুন এবং cybercrime.gov.in বা 1930-এ রিপোর্ট করুন।",
        },
        "suspicious": {
            "title": "⚠️ এটি সন্দেহজনক মনে হচ্ছে",
            "body": (
                "আমরা পরিচিত স্ক্যামের মতো কার্যকলাপের ধরণ পেয়েছি। "
                "**{entity}** এর বিরুদ্ধে **{report_count} টি রিপোর্ট** নথিভুক্ত রয়েছে। "
                "অত্যন্ত সতর্ক থাকুন।"
            ),
            "cta": "ব্যক্তিগত তথ্য শেয়ার করবেন না। কাজ করার আগে স্বাধীনভাবে যাচাই করুন।",
        },
        "likely_safe": {
            "title": "✅ নিরাপদ মনে হচ্ছে — কিন্তু সতর্ক থাকুন",
            "body": (
                "আমরা {entity} এর সাথে যুক্ত **{report_count} টি রিপোর্ট** পেয়েছি, "
                "কিন্তু স্পষ্টভাবে কোনো জালিয়াতি নয়। "
                "অপরিচিত যোগাযোগের ক্ষেত্রে সর্বদা সতর্ক থাকুন।"
            ),
            "cta": "যদি কিছু ঠিক না মনে হয়, আপনার প্রবৃত্তিকে বিশ্বাস করুন এবং 1930-এ রিপোর্ট করুন।",
        },
        "unknown": {
            "title": "ℹ️ কোনো রেকর্ড পাওয়া যায়নি",
            "body": (
                "আমাদের সিস্টেমে **{entity}** কে জালিয়াতির সাথে যুক্ত করার কোনো রেকর্ড নেই। "
                "এটি নিরাপদ বলে গ্যারান্টি দেয় না — স্ক্যামাররা ক্রমাগত কৌশল পরিবর্তন করে।"
            ),
            "cta": "সতর্ক থাকুন। সন্দেহজনক যোগাযোগ 1930-এ রিপোর্ট করুন।",
        },
    },
}


@dataclass(frozen=True)
class VerdictCard:
    """A rendered verdict card in the detected language."""

    language: LangCode
    title: str
    body: str
    cta: str


def render_verdict(
    verdict_band: str,  # danger | suspicious | likely_safe | unknown
    entity: str,  # the checked phone/UPI/URL
    report_count: int,
    language: LangCode = "en",
) -> VerdictCard:
    """
    Render a plain-language verdict card using reviewed templates.

    Never calls an LLM — templates are hand-written and slot-filled.
    Falls back to English if the requested language or band has no template.
    """
    # Fallback to English if requested language not supported
    if language not in _VERDICT_TEMPLATES:
        language = "en"
    lang_templates = _VERDICT_TEMPLATES[language]

    # Fallback to 'unknown' band if the requested band doesn't exist
    if verdict_band not in lang_templates:
        # First try English, then fall back to the first available band
        en_templates = _VERDICT_TEMPLATES["en"]
        band_templates = en_templates.get(verdict_band, en_templates["unknown"])
    else:
        band_templates = lang_templates[verdict_band]

    return VerdictCard(
        language=language,
        title=band_templates["title"],
        body=band_templates["body"].format(entity=entity, report_count=report_count),
        cta=band_templates["cta"].format(entity=entity),
    )

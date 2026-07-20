"""De-identification v2 (Regex + spaCy NER) — Phase 1 (F13)."""

import re
from typing import TypedDict

import spacy

# Load spaCy model globally (loaded once at startup)
try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if not downloaded (e.g. in tests without the docker image)
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
    _nlp = spacy.load("en_core_web_sm")


class DeidResult(TypedDict):
    masked_text: str
    token_map: dict[str, str]  # {original: token}
    # Note: tokens are generated via sha256_hex in the PII service later.
    # Here we just map to the mask label for debugging, or we can just return
    # the list of found entities to be tokenized. Let's return the extracted strings.
    extracted: list[str]


# ── Regex Patterns ──────────────────────────────────────────────────────────
# Longest-match-first principle implies we process in a specific order if there's overlap.
_PATTERNS = {
    # 1. URL (http/https/t.me/wa.me)
    "URL": re.compile(
        r"https?://(?:[-\w./]|(?:%[\da-fA-F]{2}))+|t\.me/[a-zA-Z0-9_]+|wa\.me/[0-9]+"
    ),
    # 2. Email
    "EMAIL": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    # 3. Aadhaar (12 digits, optional spaces/hyphens)
    "AADHAAR": re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"),
    # 4. PAN (ABCDE1234F)
    "PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    # 5. UPI ID
    "UPI": re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b"),
    # 6. Phone numbers (India focus)
    "PHONE": re.compile(r"(?:\+91[\-\s]?)?\b[6789]\d{9}\b"),
    # 7. IFSC
    "IFSC": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    # 8. Social Handles (@username)
    "HANDLE": re.compile(r"@[a-zA-Z0-9_]{3,32}\b"),
}


def deidentify(text: str) -> DeidResult:
    """
    Mask PII in text using regexes and spaCy NER.
    Returns the masked text and the list of extracted PII strings.
    """
    if not text:
        return {"masked_text": "", "token_map": {}, "extracted": []}

    extracted_set: set[str] = set()
    masked = text

    # 1. Apply regexes in order
    for label, pattern in _PATTERNS.items():
        # Find all matches
        matches = pattern.findall(masked)
        for match in matches:
            extracted_set.add(match)
        # Replace in text
        masked = pattern.sub(f"[{label}]", masked)

    # 2. Apply spaCy NER for PERSON
    doc = _nlp(masked)

    # We must replace from end to start to avoid shifting indices
    # We only care about PERSON entities that aren't already masked (e.g. didn't match a regex)
    # Also ignore generic entities that are just "[EMAIL]" from our regex step
    ents_to_mask = []
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not (ent.text.startswith("[") and ent.text.endswith("]")):
            ents_to_mask.append(ent)
            extracted_set.add(ent.text)

    # Sort descending by start index
    ents_to_mask.sort(key=lambda e: e.start_char, reverse=True)

    for ent in ents_to_mask:
        masked = masked[: ent.start_char] + "[NAME]" + masked[ent.end_char :]

    # The token_map will be populated by the caller (PII service)
    # We just return the extracted strings
    return {
        "masked_text": masked,
        "token_map": {},  # Placeholder
        "extracted": list(extracted_set),
    }

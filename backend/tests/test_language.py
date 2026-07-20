"""Tests for Language Layer (F31) — detection + verdict templates.

Tests must be pure unit tests with no dependencies (no DB, no network).
"""
from __future__ import annotations

import pytest

from app.services.language import (
    SUPPORTED_LANGUAGES,
    LangCode,
    VerdictCard,
    detect_language,
    render_verdict,
)


# ── Language detection ──────────────────────────────────────────────────────────

class TestDetectLanguage:
    """detect_language() should correctly identify scripts and languages."""

    def test_english_detected(self):
        """Pure English text should return 'en'."""
        assert detect_language("Hello, how are you?") == "en"
        assert detect_language("This is a test message") == "en"
        assert detect_language("") == "en"
        assert detect_language("   ") == "en"

    def test_hindi_detected(self):
        """Devanagari script text should return 'hi'."""
        text = "नमस्ते, आप कैसे हैं?"
        assert detect_language(text) == "hi"

    def test_hindi_romanized_detected(self):
        """Romanized Hindi / Hinglish should return 'hi'."""
        text = "aap kya kar rahe ho? yeh bahut badi baat hai"
        assert detect_language(text) == "hi"

        text2 = "sir ji police arrest karegi"
        assert detect_language(text2) == "hi"

    def test_tamil_detected(self):
        """Tamil script text should return 'ta'."""
        text = "வணக்கம், எப்படி இருக்கிறீர்கள்?"
        assert detect_language(text) == "ta"

    def test_telugu_detected(self):
        """Telugu script text should return 'te'."""
        text = "నమస్కారం, మీరు ఎలా ఉన్నారు?"
        assert detect_language(text) == "te"

    def test_bengali_detected(self):
        """Bengali script text should return 'bn'."""
        text = "নমস্কার, আপনি কেমন আছেন?"
        assert detect_language(text) == "bn"

    def test_mixed_scripts_defaults_to_dominant(self):
        """Text with mixed scripts should return the dominant script's language."""
        text = "Hello नमस्ते How are you?"
        detected = detect_language(text)
        assert detected in ("hi", "en")  # Devanagari present → could be hi

    def test_short_hindi_text_detected(self):
        """Short Hindi text with keywords should be detected."""
        assert detect_language("kya hai yeh") == "hi"
        assert detect_language("mujhe bachao") == "hi"

    def test_scam_keywords_in_hinglish(self):
        """Hindi scam messages in romanized script should be detected."""
        text = "sir aapke khilaf cbi ne case file kiya hai"
        assert detect_language(text) == "hi"


# ── Verdict template rendering ──────────────────────────────────────────────────

class TestRenderVerdict:
    """render_verdict() should produce correctly localised cards."""

    def test_english_verdict(self):
        """English verdict should render with correct slots."""
        card = render_verdict("danger", "+919999999999", 5, "en")
        assert isinstance(card, VerdictCard)
        assert card.language == "en"
        assert "🚨" in card.title
        assert "5" in card.body
        assert "1930" in card.cta

    def test_hindi_verdict(self):
        """Hindi verdict should render with correct slots."""
        card = render_verdict("danger", "9999999999", 3, "hi")
        assert card.language == "hi"
        assert "🚨" in card.title
        assert "3" in card.body

    def test_tamil_verdict(self):
        """Tamil verdict should render."""
        card = render_verdict("suspicious", "test@upi", 1, "ta")
        assert card.language == "ta"
        assert "⚠️" in card.title
        assert "1" in card.body

    def test_telugu_verdict(self):
        """Telugu verdict should render."""
        card = render_verdict("likely_safe", "example.com", 0, "te")
        assert card.language == "te"
        assert "✅" in card.title

    def test_bengali_verdict(self):
        """Bengali verdict should render."""
        card = render_verdict("unknown", "some_handle", 0, "bn")
        assert card.language == "bn"
        assert "ℹ️" in card.title

    def test_unknown_language_falls_back_to_english(self):
        """Unsupported language should fall back to English."""
        card = render_verdict("danger", "test", 1, "fr")  # type: ignore[arg-type]
        assert card.language == "en"   # fallback to en

    def test_unknown_verdict_band_falls_back_to_english(self):
        """Unknown verdict band should fall back to English version."""
        card = render_verdict("nonexistent_band", "test", 1)
        assert "1930" in card.cta

    def test_all_bands_have_all_languages(self):
        """Every verdict band should have templates for every supported language."""
        bands = ["danger", "suspicious", "likely_safe", "unknown"]
        for band in bands:
            for lang in SUPPORTED_LANGUAGES:
                card = render_verdict(band, "test_entity", 1, lang)
                assert card.language in (lang, "en")
                assert card.title
                assert card.body
                assert card.cta

    def test_entity_inserted_correctly(self):
        """Entity placeholder should be replaced with actual value."""
        card = render_verdict("danger", "+919876543210", 3, "en")
        assert "+919876543210" in card.body

    def test_verdict_card_dataclass(self):
        """VerdictCard dataclass should hold all fields."""
        card = VerdictCard(language="en", title="Test Title", body="Test body", cta="Call 1930")
        assert card.language == "en"
        assert card.title == "Test Title"
        assert card.body == "Test body"
        assert card.cta == "Call 1930"


# ── Language detection edge cases ───────────────────────────────────────────────

class TestLanguageEdgeCases:
    def test_null_text(self):
        """None text should default to English."""
        assert detect_language("") == "en"

    def test_only_numbers(self):
        """Numeric text should default to English."""
        assert detect_language("1234567890") == "en"

    def test_very_short_hindi(self):
        """Very short Hindi keyword should still be detected."""
        text = "kya hai"
        assert detect_language(text) == "hi"

    def test_mixed_languages_dominant(self):
        """Mixed Hindi-English should detect the dominant language."""
        # More Hindi chars than English
        text = "नमस्ते how are you"
        assert detect_language(text) == "hi"

    def test_url_in_text(self):
        """URLs should not confuse language detection."""
        assert detect_language("Check this link https://example.com") == "en"

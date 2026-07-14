"""Test de-identification (F13)."""
from app.services.deidentify import deidentify
from tests.fixtures.pii_fixture import CLEAN_SAMPLES, PII_SAMPLES


def test_deidentify_pii_recall() -> None:
    for text, expected_piis in PII_SAMPLES:
        result = deidentify(text)
        for expected in expected_piis:
            assert expected in result["extracted"], f"Failed to extract {expected} from {text}"

def test_deidentify_clean() -> None:
    for text in CLEAN_SAMPLES:
        result = deidentify(text)
        assert len(result["extracted"]) == 0, f"False positive in {text}"

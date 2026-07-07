import re
import json
from typing import Tuple, Dict

def deidentify_text(raw_text: str) -> Tuple[str, str]:
    """
    Masks PII from raw_text.
    Returns:
        masked_text: The string with PII replaced by tokens (e.g., [PHONE_1]).
        pii_token_map: JSON string mapping tokens to original values.
    """
    token_map: Dict[str, str] = {}
    
    # 1. Indian Phone Numbers (10 digits, optionally starting with +91 or 0)
    phone_pattern = r'(?:(?:\+|00)91[\s-]?)?[6789]\d{9}'
    
    def phone_replacer(match):
        token = f"[PHONE_{len(token_map) + 1}]"
        token_map[token] = match.group(0)
        return token
        
    masked_text = re.sub(phone_pattern, phone_replacer, raw_text)
    
    # 2. Aadhaar / 12-digit numeric patterns
    aadhaar_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    
    def aadhaar_replacer(match):
        token = f"[AADHAAR_{len(token_map) + 1}]"
        token_map[token] = match.group(0)
        return token
        
    masked_text = re.sub(aadhaar_pattern, aadhaar_replacer, masked_text)
    
    # 3. Bank Account Fragments (9 to 18 digits)
    bank_pattern = r'\b\d{9,18}\b'
    
    def bank_replacer(match):
        token = f"[BANK_ACC_{len(token_map) + 1}]"
        token_map[token] = match.group(0)
        return token
        
    masked_text = re.sub(bank_pattern, bank_replacer, masked_text)
    
    return masked_text, json.dumps(token_map)

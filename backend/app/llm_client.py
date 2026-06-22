import os
from google import genai
from google.genai import types
from app.config import settings
from pydantic import BaseModel, Field
from typing import List, Optional

class LLMRedFlag(BaseModel):
    flag_id: str
    category: str = Field(description="critical, high, or medium")
    evidence: str
    explanation: str

class LLMFraudVerdict(BaseModel):
    fraud_type: str = Field(description="digital_arrest, upi_spoofing, otp_sim_swap, investment_fraud, job_loan_scam, courier_parcel, legitimate, needs_manual_review")
    risk_score: int = Field(description="0-100")
    confidence: float = Field(description="0.0-1.0")
    verdict: str = Field(description="plain-language one-liner")
    reporting_portal: str = Field(description="URL to report, e.g. https://cybercrime.gov.in")
    red_flags: List[LLMRedFlag]

def classify_text_gemini(deidentified_text: str) -> Optional[LLMFraudVerdict]:
    """
    Calls Gemini API to classify the deidentified text.
    Enforces structured JSON output via Pydantic schema.
    Returns parsed LLMFraudVerdict on success, or None on failure (triggering needs_manual_review).
    """
    try:
        # We initialize client inside the function to ensure settings are loaded correctly.
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
        You are an expert fraud analysis system for Indian cybercrime.
        Analyze the following de-identified text and classify the fraud type, extracting key evidence.
        IMPORTANT: The text has had PII replaced with tokens like [PHONE_1]. You MUST include these tokens directly in your 'evidence' string exactly as they appear if they are part of a red flag.
        
        Text:
        {deidentified_text}
        """
        
        # First attempt
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LLMFraudVerdict,
                temperature=0.1,
            ),
        )
        
        if response.parsed:
            return response.parsed
            
        try:
            return LLMFraudVerdict.model_validate_json(response.text)
        except Exception:
            print("Gemini API Error: Invalid JSON on first attempt. Retrying...")
            retry_prompt = prompt + "\n\nYour last response was invalid JSON. Return ONLY the JSON object matching the schema."
            retry_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=retry_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LLMFraudVerdict,
                    temperature=0.1,
                ),
            )
            if retry_response.parsed:
                return retry_response.parsed
            return LLMFraudVerdict.model_validate_json(retry_response.text)
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Requirements mandate degrading gracefully to 'needs_manual_review'
        return None

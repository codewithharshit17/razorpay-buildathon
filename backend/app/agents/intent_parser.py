import json
from typing import Tuple
from app.config import config

def parse_call_intent(transcript: str, question: str = "") -> Tuple[str, float, str, str]:
    """
    Parses participant's speech transcript into intent:
    - 'confirms_duplicate': participant confirmed they registered twice / extra payment
    - 'denies_duplicate': participant says it's a different person or they only registered once
    - 'unclear': ambiguous, noisy, or nonsensical response
    Returns: (intent, confidence, explanation, actor)
    """
    if not transcript or not transcript.strip():
        return ("unclear", 0.0, "No speech detected or empty transcript.", "fallback_intent_parser")

    clean_tx = transcript.strip().lower()

    # Try LLM first if API key present
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            prompt = f"""You are an AI Voice Call Intent Parser for a college workshop duplicate verification system.
Question Asked to Participant: "{question}"
Spoken Transcript from Participant: "{transcript}"

Classify the intent into one of:
1. "confirms_duplicate" -> Participant admits or confirms they registered twice / made duplicate payments.
2. "denies_duplicate" -> Participant states it is a different person, a friend/sibling, or denied registering twice.
3. "unclear" -> Response is ambiguous, cut off, or off-topic.

Respond ONLY with valid JSON:
{{
  "intent": "confirms_duplicate" | "denies_duplicate" | "unclear",
  "confidence": 0.95,
  "explanation": "Brief reasoning for classification"
}}"""
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt
            )
            txt = response.text.strip()
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0].strip()
            res = json.loads(txt)
            return (
                res.get("intent", "unclear"),
                float(res.get("confidence", 0.9)),
                res.get("explanation", "LLM parsed transcript intent."),
                "ai_intent_parser"
            )
        except Exception as e:
            print(f"[IntentParser] LLM call failed, using rule engine fallback: {e}")

    # Fallback Rule-Based Engine
    confirm_keywords = ["yes", "yeah", "yep", "twice", "registered twice", "duplicate", "two times", "my mistake", "cancel one", "refund one", "i did", "double"]
    deny_keywords = ["no", "nope", "different person", "brother", "friend", "sister", "another person", "not twice", "single", "only one", "someone else", "wrong number"]

    confirm_score = sum(1 for kw in confirm_keywords if kw in clean_tx)
    deny_score = sum(1 for kw in deny_keywords if kw in clean_tx)

    if confirm_score > deny_score and confirm_score >= 1:
        return (
            "confirms_duplicate",
            0.92,
            f"Rule parser detected confirmation keywords in: '{transcript}'",
            "fallback_intent_parser"
        )
    elif deny_score > confirm_score and deny_score >= 1:
        return (
            "denies_duplicate",
            0.92,
            f"Rule parser detected denial keywords in: '{transcript}'",
            "fallback_intent_parser"
        )
    else:
        return (
            "unclear",
            0.50,
            f"Rule parser could not confidently classify transcript: '{transcript}'",
            "fallback_intent_parser"
        )

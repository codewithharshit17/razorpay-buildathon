import json
import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from app.config import config
from app.models import Registration, Payment

def normalize_phone(phone: str) -> str:
    return re.sub(r'\D', '', phone)[-10:] if phone else ""

def normalize_name(name: str) -> str:
    return " ".join(name.lower().strip().split())

def string_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def detect_duplicates(
    db: Session,
    new_reg: Registration,
    new_payment: Optional[Payment] = None
) -> Tuple[bool, Optional[str], List[str], str, str]:
    """
    Evaluates new registration against existing active registrations for duplicate flags.
    Returns: (is_flag, flag_type, matched_fields, explanation, actor)
    """
    # Fetch existing active registrations in the same event
    existing_regs = db.query(Registration).filter(
        Registration.event_id == new_reg.event_id,
        Registration.id != new_reg.id,
        Registration.status.in_(["registered", "flagged", "verified", "pending_payment"])
    ).all()

    norm_new_phone = normalize_phone(new_reg.phone)
    norm_new_name = normalize_name(new_reg.name)
    norm_new_email = new_reg.email.lower().strip()

    candidate_matches = []
    for ex in existing_regs:
        matched_fields = []
        norm_ex_phone = normalize_phone(ex.phone)
        norm_ex_name = normalize_name(ex.name)
        norm_ex_email = ex.email.lower().strip()

        # Check phone match
        phone_match = False
        if norm_new_phone and norm_ex_phone and norm_new_phone == norm_ex_phone:
            matched_fields.append("phone")
            phone_match = True

        # Check email match
        email_match = False
        if norm_new_email and norm_ex_email:
            if norm_new_email == norm_ex_email:
                matched_fields.append("email")
                email_match = True
            elif norm_new_email.split("@")[0] == norm_ex_email.split("@")[0]:
                matched_fields.append("email_username")

        # Check fuzzy name similarity
        name_sim = string_similarity(norm_new_name, norm_ex_name)
        name_match = False
        if name_sim >= 0.80:
            matched_fields.append("name")
            name_match = True

        if phone_match or email_match or (name_match and (phone_match or email_match or name_sim > 0.88)):
            candidate_matches.append({
                "existing_id": ex.id,
                "existing_name": ex.name,
                "existing_phone": ex.phone,
                "existing_email": ex.email,
                "matched_fields": matched_fields,
                "name_similarity": round(name_sim, 2)
            })

    # If candidate matches found, attempt LLM call first if API key present
    if candidate_matches:
        llm_result = None
        actor = "fallback_duplicate_detector"

        if config.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                prompt = f"""You are an AI Duplicate Detector for a college workshop event registration system.
Analyze this new registration against potential existing duplicate records.

New Registration:
- Name: {new_reg.name}
- Email: {new_reg.email}
- Phone: {new_reg.phone}

Potential Matching Records:
{json.dumps(candidate_matches, indent=2)}

Determine if this is a likely duplicate registration or duplicate payment.
Respond ONLY with valid JSON:
{{
  "is_flag": true,
  "flag_type": "duplicate_registration",
  "matched_fields": ["name", "phone"],
  "explanation": "Detailed concise explanation of match..."
}}"""
                response = client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=prompt
                )
                txt = response.text.strip()
                if "```json" in txt:
                    txt = txt.split("```json")[1].split("```")[0].strip()
                res = json.loads(txt)
                llm_result = (
                    res.get("is_flag", True),
                    res.get("flag_type", "duplicate_registration"),
                    res.get("matched_fields", candidate_matches[0]["matched_fields"]),
                    res.get("explanation", f"Matched record {candidate_matches[0]['existing_name']}"),
                    "ai_duplicate_detector"
                )
            except Exception as e:
                print(f"[DuplicateDetector] LLM call failed, falling back to rule engine: {e}")

        if llm_result:
            return llm_result

        # Fallback heuristic duplicate detector
        top = candidate_matches[0]
        flag_type = "duplicate_payment" if "phone" in top["matched_fields"] and "name" in top["matched_fields"] else "duplicate_registration"
        explanation = (
            f"Flagged by heuristic detector: Match found with registration '{top['existing_name']}' ({top['existing_id']}). "
            f"Matched fields: {', '.join(top['matched_fields'])} (Name similarity: {int(top['name_similarity']*100)}%)."
        )
        return (True, flag_type, top["matched_fields"], explanation, "fallback_duplicate_detector")

    return (False, None, [], "No duplicate records detected.", "fallback_duplicate_detector")

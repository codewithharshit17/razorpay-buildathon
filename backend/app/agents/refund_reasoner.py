import json
from typing import Tuple, Dict, Any
from app.config import config

FIXED_REFUND_POLICY = """
Hardcoded Fixed Workshop Refund Policy:
1. Cancellation requested >72 hours before event start -> Full refund (100% of payment amount).
2. Cancellation requested <72 hours before event start -> Partial refund (50% of payment amount).
3. Participant No-Show on event day -> No refund (0%).
4. Duplicate payment / duplicate registration -> Refund the extra payment only (100% of duplicate payment).
"""

def evaluate_refund_request(
    hours_before_event: float,
    is_no_show: bool,
    is_duplicate_payment: bool,
    payment_amount: float,
    user_reason: str = ""
) -> Tuple[str, str, float, str, str]:
    """
    Evaluates refund request against the hardcoded fixed refund policy.
    Returns: (recommendation, policy_clause, calculated_amount, explanation, actor)
    - recommendation: 'full_refund', 'partial_50_percent', 'no_refund', 'refund_extra_only'
    - actor: 'ai_refund_reasoner' (LLM path) vs 'fallback_rule_engine' (Rule engine path)
    """

    # First evaluate exact deterministic rule logic as ground truth reference
    if is_duplicate_payment:
        rule_recommendation = "refund_extra_only"
        rule_clause = "Clause 4: Duplicate payment / duplicate registration -> Refund the extra payment only (100%)."
        rule_amount = payment_amount
        rule_explanation = f"Payment of ₹{payment_amount:.2f} is an extra duplicate payment. Full refund of extra payment issued."
    elif is_no_show:
        rule_recommendation = "no_refund"
        rule_clause = "Clause 3: Participant No-Show on event day -> No refund (0%)."
        rule_amount = 0.0
        rule_explanation = "Participant was marked as No-Show on event day. Per Clause 3, no refund is granted."
    elif hours_before_event >= 72.0:
        rule_recommendation = "full_refund"
        rule_clause = "Clause 1: Cancellation requested >72 hours before event start -> Full refund (100%)."
        rule_amount = payment_amount
        rule_explanation = f"Cancellation requested {hours_before_event:.1f} hours prior to event (>72h threshold). Full refund of ₹{payment_amount:.2f} granted per Clause 1."
    else:
        rule_recommendation = "partial_50_percent"
        rule_clause = "Clause 2: Cancellation requested <72 hours before event start -> Partial refund (50%)."
        rule_amount = round(payment_amount * 0.5, 2)
        rule_explanation = f"Cancellation requested {hours_before_event:.1f} hours prior to event (<72h threshold). 50% refund of ₹{rule_amount:.2f} granted per Clause 2."

    # Try LLM Reasoning if Gemini API key present
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            prompt = f"""You are an AI Refund Reasoner enforcing a strict financial refund policy for college workshop event payments.

{FIXED_REFUND_POLICY}

Refund Request Context:
- Hours before event start: {hours_before_event:.1f} hours
- Is No-Show: {is_no_show}
- Is Duplicate Payment: {is_duplicate_payment}
- Payment Amount: ₹{payment_amount:.2f}
- User Reason Given: "{user_reason}"

Enforce the policy strictly without altering rules.
Respond ONLY with valid JSON:
{{
  "recommendation": "{rule_recommendation}",
  "policy_clause": "{rule_clause}",
  "calculated_amount": {rule_amount},
  "explanation": "Professional audit justification referencing the exact policy clause..."
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
                res.get("recommendation", rule_recommendation),
                res.get("policy_clause", rule_clause),
                float(res.get("calculated_amount", rule_amount)),
                res.get("explanation", rule_explanation),
                "ai_refund_reasoner"
            )
        except Exception as e:
            print(f"[RefundReasoner] LLM call failed, using rule engine: {e}")

    # Fallback to rule engine
    return (
        rule_recommendation,
        rule_clause,
        rule_amount,
        rule_explanation,
        "fallback_rule_engine"
    )

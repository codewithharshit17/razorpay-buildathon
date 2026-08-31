import uuid
import os
from typing import Dict, Any, Tuple
from app.config import config

def get_base_url() -> str:
    """
    Dynamically read BASE_URL from environment or config.
    """
    return os.getenv("BASE_URL", config.BASE_URL).rstrip("/")

def initiate_outbound_call(
    flag_id: str,
    to_phone: str,
    registrant_name: str,
    event_name: str = "College Workshop"
) -> Tuple[bool, str, str, str]:
    """
    Triggers Twilio outbound call pointing to the voice-prompt webhook URL.
    Returns: (success, call_sid, question_asked, actor)
    """
    base_url = get_base_url()
    webhook_url = f"{base_url}/webhooks/twilio/voice-prompt?flag_id={flag_id}"
    question_asked = (
        f"We noticed a possible duplicate registration and payment under your phone number for {event_name}. "
        f"Did you register and pay twice, or is this a different person? Please say yes or no."
    )

    print(f"\n[TwilioService] ========================================================")
    print(f"[TwilioService] Outbound Call Triggered:")
    print(f"[TwilioService]   Flag ID:        {flag_id}")
    print(f"[TwilioService]   To Phone:       {to_phone}")
    print(f"[TwilioService]   From Phone:     {config.TWILIO_PHONE_NUMBER}")
    print(f"[TwilioService]   BASE_URL:       {base_url}")
    print(f"[TwilioService]   Resolved URL:   {webhook_url}")
    print(f"[TwilioService] ========================================================\n")

    if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_PHONE_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            
            call = client.calls.create(
                to=to_phone,
                from_=config.TWILIO_PHONE_NUMBER,
                url=webhook_url,
                method="POST"
            )
            print(f"[TwilioService] Twilio Call Created Successfully! SID: {call.sid}")
            return (True, call.sid, question_asked, "twilio_voice")
        except Exception as e:
            print(f"[TwilioService] Real Twilio call failed: {e}")

    # Fallback / Simulated call SID
    simulated_sid = f"CA_SIM_{uuid.uuid4().hex[:16]}"
    print(f"[TwilioService] Using fallback/simulated call SID: {simulated_sid}")
    return (True, simulated_sid, question_asked, "simulated_call")

def generate_twiml_gather_prompt(flag_id: str, question: str) -> str:
    """
    Generates well-formed standard TwiML XML with single turn <Gather input="speech">
    """
    base_url = get_base_url()
    gather_action_url = f"{base_url}/webhooks/twilio/gather?flag_id={flag_id}"
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Response>\n'
        f'  <Gather input="speech" action="{gather_action_url}" method="POST" speechTimeout="auto">\n'
        f'    <Say voice="Polly.Kajal-Neural" language="en-IN">{question}</Say>\n'
        '  </Gather>\n'
        '  <Say voice="Polly.Kajal-Neural" language="en-IN">We didn\'t catch a response. Please contact the event organizer. Goodbye.</Say>\n'
        '</Response>'
    )
    return twiml

def generate_twiml_final_response(message: str) -> str:
    """
    Generates well-formed standard TwiML XML to speak final response and hang up.
    """
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Response>\n'
        f'  <Say voice="Polly.Kajal-Neural" language="en-IN">{message}</Say>\n'
        '  <Hangup/>\n'
        '</Response>'
    )
    return twiml


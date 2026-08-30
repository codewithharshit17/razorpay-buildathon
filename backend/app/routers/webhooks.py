import uuid
import json
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Flag, VerificationCall, Payment, Registration
from app.services.audit_service import log_audit
from app.services.twilio_service import generate_twiml_gather_prompt, generate_twiml_final_response
from app.agents.intent_parser import parse_call_intent

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Voice"])

@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        event_name = body.get("event", "payment.captured")
        payload = body.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payload.get("order_id")
        payment_id = payload.get("id")
        amount = payload.get("amount", 0) / 100.0

        payment = db.query(Payment).filter(Payment.razorpay_order_id == order_id).first()
        if payment:
            payment.razorpay_payment_id = payment_id
            payment.status = "captured" if "captured" in event_name else "failed"
            db.commit()

            log_audit(
                db=db,
                actor="razorpay_webhook",
                action="PAYMENT_CAPTURED" if payment.status == "captured" else "PAYMENT_FAILED",
                entity_id=payment.id,
                payload={"razorpay_payment_id": payment_id, "amount": amount, "event": event_name}
            )
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.api_route("/twilio/voice-prompt", methods=["GET", "POST"])
async def twilio_voice_prompt(request: Request, db: Session = Depends(get_db)):
    flag_id = request.query_params.get("flag_id")
    if not flag_id and request.method == "POST":
        try:
            form = await request.form()
            flag_id = form.get("flag_id")
        except Exception:
            pass

    print(f"\n[Webhook: Voice-Prompt] ================================================")
    print(f"[Webhook: Voice-Prompt] Incoming Request: {request.method} {request.url}")
    print(f"[Webhook: Voice-Prompt] Query Params:     {dict(request.query_params)}")
    print(f"[Webhook: Voice-Prompt] Extracted Flag ID: {flag_id}")

    flag = db.query(Flag).filter(Flag.id == flag_id).first() if flag_id else None
    if not flag:
        twiml = generate_twiml_final_response("Registration flag record not found. Goodbye.")
        print(f"[Webhook: Voice-Prompt] Flag not found for flag_id={flag_id}. Returning TwiML:\n{twiml}")
        print(f"[Webhook: Voice-Prompt] ================================================\n")
        return Response(content=twiml, media_type="text/xml", headers={"Content-Type": "text/xml; charset=utf-8"})

    question = (
        f"We noticed a possible duplicate registration and payment under your phone number for our workshop. "
        f"Did you register and pay twice, or is this a different person? Please say yes or no."
    )
    twiml = generate_twiml_gather_prompt(flag.id, question)
    print(f"[Webhook: Voice-Prompt] Generated TwiML Response:\n{twiml}")
    print(f"[Webhook: Voice-Prompt] ================================================\n")
    return Response(content=twiml, media_type="text/xml", headers={"Content-Type": "text/xml; charset=utf-8"})

@router.api_route("/twilio/gather", methods=["GET", "POST"])
async def twilio_gather_webhook(request: Request, db: Session = Depends(get_db)):
    flag_id = request.query_params.get("flag_id")
    speech_result = ""
    call_sid = ""

    if request.method == "POST":
        try:
            form_data = await request.form()
            speech_result = form_data.get("SpeechResult", "").strip()
            call_sid = form_data.get("CallSid", "")
            if not flag_id:
                flag_id = form_data.get("flag_id")
        except Exception as e:
            print(f"[Webhook: Gather] Form parse exception: {e}")

    print(f"\n[Webhook: Gather] ======================================================")
    print(f"[Webhook: Gather] Incoming Request: {request.method} {request.url}")
    print(f"[Webhook: Gather] Query Params:     {dict(request.query_params)}")
    print(f"[Webhook: Gather] Extracted Flag ID: {flag_id}")
    print(f"[Webhook: Gather] Call SID:          {call_sid}")
    print(f"[Webhook: Gather] Speech Result:     '{speech_result}'")

    flag = db.query(Flag).filter(Flag.id == flag_id).first() if flag_id else None
    if not flag:
        twiml = generate_twiml_final_response("Flag not found. Goodbye.")
        print(f"[Webhook: Gather] Flag not found. Returning TwiML:\n{twiml}")
        print(f"[Webhook: Gather] ======================================================\n")
        return Response(content=twiml, media_type="text/xml", headers={"Content-Type": "text/xml; charset=utf-8"})

    question_asked = (
        f"We noticed a possible duplicate registration and payment under your phone number for our workshop. "
        f"Did you register and pay twice, or is this a different person? Please say yes or no."
    )

    # Call Intent Parser Agent
    intent, confidence, explanation, intent_actor = parse_call_intent(speech_result, question_asked)
    print(f"[Webhook: Gather] Intent Parsed: {intent} (Confidence: {confidence:.2f}, Actor: {intent_actor})")
    print(f"[Webhook: Gather] Explanation:   {explanation}")

    # Determine outcome & update flag
    outcome = "pending"
    say_message = ""

    if intent == "confirms_duplicate":
        flag.status = "call_verified"
        outcome = "auto_resolved_refund_extra"
        say_message = "Thank you for confirming. We have verified your duplicate response and automatically initiated a refund for the extra payment. Goodbye!"
        if flag.payment:
            flag.payment.status = "refunded"
        flag.registration.status = "partially_refunded"
    elif intent == "denies_duplicate":
        flag.status = "call_verified"
        outcome = "auto_resolved_kept"
        say_message = "Thank you for confirming. Your registration has been verified and marked active. Goodbye!"
        flag.registration.status = "verified"
    else:
        flag.status = "call_unclear"
        outcome = "escalated_to_organizer"
        say_message = "Thank you. We could not clearly understand your response. An organizer will follow up with you. Goodbye!"

    call_id = f"CALL-{uuid.uuid4().hex[:6].upper()}"
    v_call = VerificationCall(
        id=call_id,
        flag_id=flag.id,
        twilio_call_sid=call_sid or f"CA_{uuid.uuid4().hex[:12]}",
        question_asked=question_asked,
        transcript=speech_result,
        parsed_intent=intent,
        outcome=outcome
    )
    db.add(v_call)
    db.commit()

    # Log audit entry with explicit intent actor
    log_audit(
        db=db,
        actor=intent_actor,
        action="SPEECH_INTENT_PARSED",
        entity_id=v_call.id,
        payload={
            "flag_id": flag.id,
            "twilio_call_sid": call_sid,
            "transcript": speech_result,
            "parsed_intent": intent,
            "confidence": confidence,
            "outcome": outcome,
            "explanation": explanation
        }
    )

    twiml = generate_twiml_final_response(say_message)
    print(f"[Webhook: Gather] Final TwiML Response:\n{twiml}")
    print(f"[Webhook: Gather] Flag Status Updated to: {flag.status} (Outcome: {outcome})")
    print(f"[Webhook: Gather] ======================================================\n")
    return Response(content=twiml, media_type="text/xml", headers={"Content-Type": "text/xml; charset=utf-8"})


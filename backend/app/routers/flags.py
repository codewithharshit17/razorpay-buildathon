import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Flag, Registration, Payment, VerificationCall
from app.schemas import FlagResponse, CallVerifyRequest, CallSimulateRequest, FlagResolveRequest
from app.services.twilio_service import initiate_outbound_call
from app.services.audit_service import log_audit
from app.agents.intent_parser import parse_call_intent

router = APIRouter(prefix="/flags", tags=["Duplicate Flags"])

@router.get("", response_model=List[FlagResponse])
def list_flags(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(Flag)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Flag.status == status_filter.lower())
    
    flags = query.order_by(Flag.created_at.desc()).all()
    res = []
    for f in flags:
        reg = f.registration
        res.append(FlagResponse(
            id=f.id,
            registration_id=f.registration_id,
            payment_id=f.payment_id,
            razorpay_order_id=f.payment.razorpay_order_id if f.payment else None,
            razorpay_payment_id=f.payment.razorpay_payment_id if f.payment else None,
            flag_type=f.flag_type,
            ai_explanation=f.ai_explanation,
            matched_fields=json.loads(f.matched_fields) if f.matched_fields else [],
            status=f.status,
            registrant_name=reg.name if reg else "Unknown",
            registrant_email=reg.email if reg else "Unknown",
            registrant_phone=reg.phone if reg else "Unknown",
            created_at=f.created_at
        ))
    return res

@router.post("/{flag_id}/call-verify")
def trigger_call_verify(
    flag_id: str,
    payload: CallVerifyRequest = CallVerifyRequest(),
    db: Session = Depends(get_db)
):
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag record not found")

    reg = flag.registration
    success, call_sid, question, call_actor = initiate_outbound_call(
        flag_id=flag.id,
        to_phone=reg.phone,
        registrant_name=reg.name
    )

    flag.status = "resolving_via_call"
    db.commit()

    log_audit(
        db=db,
        actor=call_actor, # 'twilio_voice' or 'simulated_call'
        action="CALL_INITIATED",
        entity_id=flag.id,
        payload={"call_sid": call_sid, "phone": reg.phone, "question": question}
    )

    return {
        "status": "call_initiated",
        "flag_id": flag.id,
        "twilio_call_sid": call_sid,
        "question_asked": question,
        "actor": call_actor
    }

@router.post("/{flag_id}/simulate-call")
def simulate_call_response(
    flag_id: str,
    payload: CallSimulateRequest,
    db: Session = Depends(get_db)
):
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag record not found")

    reg = flag.registration
    question_asked = f"Hello {reg.name}! We noticed two registrations under your phone number. Did you register twice?"
    
    intent, confidence, explanation, intent_actor = parse_call_intent(payload.spoken_transcript, question_asked)

    outcome = "pending"
    if intent == "confirms_duplicate":
        flag.status = "call_verified"
        outcome = "auto_resolved_refund_extra"
        if flag.payment:
            flag.payment.status = "refunded"
        flag.registration.status = "partially_refunded"
    elif intent == "denies_duplicate":
        flag.status = "call_verified"
        outcome = "auto_resolved_kept"
        flag.registration.status = "verified"
    else:
        flag.status = "call_unclear"
        outcome = "escalated_to_organizer"

    call_id = f"CALL-{uuid.uuid4().hex[:6].upper()}"
    simulated_sid = f"CA_SIM_{uuid.uuid4().hex[:12]}"
    v_call = VerificationCall(
        id=call_id,
        flag_id=flag.id,
        twilio_call_sid=simulated_sid,
        question_asked=question_asked,
        transcript=payload.spoken_transcript,
        parsed_intent=intent,
        outcome=outcome
    )
    db.add(v_call)
    db.commit()

    log_audit(
        db=db,
        actor=intent_actor, # 'ai_intent_parser' or 'fallback_intent_parser'
        action="SIMULATED_CALL_INTENT_PARSED",
        entity_id=v_call.id,
        payload={
            "flag_id": flag.id,
            "simulated_call_sid": simulated_sid,
            "transcript": payload.spoken_transcript,
            "parsed_intent": intent,
            "confidence": confidence,
            "outcome": outcome,
            "explanation": explanation
        }
    )

    return {
        "status": "call_simulated",
        "flag_id": flag.id,
        "call_id": v_call.id,
        "transcript": payload.spoken_transcript,
        "parsed_intent": intent,
        "confidence": confidence,
        "outcome": outcome,
        "explanation": explanation,
        "actor": intent_actor
    }

@router.post("/{flag_id}/resolve")
def resolve_flag_manually(
    flag_id: str,
    payload: FlagResolveRequest,
    db: Session = Depends(get_db)
):
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag record not found")

    if payload.decision == "approve_refund_extra":
        flag.status = "manually_approved"
        if flag.payment:
            flag.payment.status = "refunded"
        flag.registration.status = "refunded"
    elif payload.decision == "approve_keep":
        flag.status = "manually_approved"
        flag.registration.status = "verified"
    else:
        flag.status = "manually_rejected"
        flag.registration.status = "rejected"

    db.commit()

    log_audit(
        db=db,
        actor="organizer",
        action="FLAG_MANUALLY_RESOLVED",
        entity_id=flag.id,
        payload={
            "decision": payload.decision,
            "reason": payload.reason,
            "new_flag_status": flag.status
        }
    )

    return {"status": "resolved", "flag_id": flag.id, "new_status": flag.status}

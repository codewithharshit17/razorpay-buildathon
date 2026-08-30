import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Payment, RefundDecision
from app.schemas import RefundRequest, RefundResolveRequest
from app.agents.refund_reasoner import evaluate_refund_request
from app.services.audit_service import log_audit

router = APIRouter(prefix="/payments", tags=["Payments & Refunds"])

@router.post("/{payment_id}/refund-request")
def request_payment_refund(
    payment_id: str,
    payload: RefundRequest,
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    rec, policy_clause, calc_amount, explanation, reasoner_actor = evaluate_refund_request(
        hours_before_event=payload.hours_before_event,
        is_no_show=payload.is_no_show,
        is_duplicate_payment=payload.is_duplicate_payment,
        payment_amount=payment.amount,
        user_reason=payload.reason
    )

    rfd_id = f"RFD-{uuid.uuid4().hex[:6].upper()}"
    refund_decision = RefundDecision(
        id=rfd_id,
        payment_id=payment.id,
        ai_recommendation=rec,
        policy_clause=policy_clause,
        reason=explanation
    )
    db.add(refund_decision)
    db.commit()

    log_audit(
        db=db,
        actor=reasoner_actor, # 'ai_refund_reasoner' or 'fallback_rule_engine'
        action="REFUND_EVALUATED",
        entity_id=refund_decision.id,
        payload={
            "payment_id": payment.id,
            "recommendation": rec,
            "policy_clause": policy_clause,
            "calculated_amount": calc_amount,
            "hours_before_event": payload.hours_before_event,
            "is_no_show": payload.is_no_show,
            "is_duplicate_payment": payload.is_duplicate_payment,
            "explanation": explanation
        }
    )

    return {
        "refund_decision_id": rfd_id,
        "payment_id": payment.id,
        "ai_recommendation": rec,
        "policy_clause": policy_clause,
        "calculated_amount": calc_amount,
        "explanation": explanation,
        "actor": reasoner_actor
    }

@router.post("/{payment_id}/resolve-refund")
def resolve_refund_manually(
    payment_id: str,
    payload: RefundResolveRequest,
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    rfd_decision = db.query(RefundDecision).filter(RefundDecision.payment_id == payment.id).order_by(RefundDecision.created_at.desc()).first()
    
    if rfd_decision:
        rfd_decision.human_decision = payload.decision
        db.commit()

    if payload.decision == "approved" or payload.decision == "overridden":
        payment.status = "refunded"
        if payment.registration:
            payment.registration.status = "refunded"
    else:
        payment.status = "captured"

    db.commit()

    log_audit(
        db=db,
        actor="organizer",
        action="REFUND_HUMAN_DECISION",
        entity_id=payment.id,
        payload={
            "human_decision": payload.decision,
            "reason": payload.reason,
            "new_payment_status": payment.status
        }
    )

    return {"status": "refund_resolved", "payment_id": payment.id, "human_decision": payload.decision}

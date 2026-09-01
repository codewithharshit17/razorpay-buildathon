import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Payment, RefundDecision
from app.schemas import RefundRequest, RefundResolveRequest
from app.agents.refund_reasoner import evaluate_refund_request
from app.services.audit_service import log_audit
from app.services.razorpay_service import execute_razorpay_refund, verify_razorpay_payment_signature

router = APIRouter(prefix="/payments", tags=["Payments & Refunds"])

@router.post("/verify")
def verify_payment(
    payload: dict,
    db: Session = Depends(get_db)
):
    razorpay_order_id = (payload or {}).get("razorpay_order_id")
    razorpay_payment_id = (payload or {}).get("razorpay_payment_id")
    razorpay_signature = (payload or {}).get("razorpay_signature")

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay payment verification payload")

    payment = db.query(Payment).filter(Payment.razorpay_order_id == razorpay_order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found for order")

    if not verify_razorpay_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        payment.status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail="Razorpay payment signature verification failed")

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = "captured"
    if payment.registration:
        payment.registration.status = "registered"
    db.commit()

    log_audit(
        db=db,
        actor="razorpay_checkout",
        action="PAYMENT_VERIFIED",
        entity_id=payment.id,
        payload={
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "amount": payment.amount,
        }
    )

    return {
        "status": "captured",
        "payment_id": payment.id,
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "razorpay_signature": payment.razorpay_signature,
    }

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
        calculated_amount=calc_amount,
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
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
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
    
    if not rfd_decision:
        raise HTTPException(status_code=409, detail="Refund decision must be evaluated before it can be resolved")

    rfd_decision.human_decision = payload.decision

    if payload.decision in {"approved", "overridden"}:
        refund_amount = payload.override_amount if payload.decision == "overridden" and payload.override_amount is not None else rfd_decision.calculated_amount
        refund_id, execution_error = execute_razorpay_refund(payment.razorpay_payment_id, refund_amount)

        if execution_error:
            payment.status = "pending_manual_refund"
            db.commit()
            message = f"refund not executed via Razorpay: {execution_error}"
            log_audit(
                db=db,
                actor="organizer",
                action="REFUND_NOT_EXECUTED_VIA_RAZORPAY",
                entity_id=payment.id,
                payload={
                    "message": message,
                    "human_decision": payload.decision,
                    "refund_amount": refund_amount,
                    "razorpay_payment_id": payment.razorpay_payment_id,
                }
            )
            return {
                "status": "pending_manual_refund",
                "payment_id": payment.id,
                "razorpay_order_id": payment.razorpay_order_id,
                "razorpay_payment_id": payment.razorpay_payment_id,
                "razorpay_refund_id": None,
                "message": message,
            }

        rfd_decision.razorpay_refund_id = refund_id
        payment.status = "refunded" if refund_amount >= payment.amount else "partially_refunded"
        if payment.registration:
            payment.registration.status = "refunded" if payment.status == "refunded" else "partially_refunded"
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

    return {
        "status": "refund_resolved",
        "payment_id": payment.id,
        "human_decision": payload.decision,
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "razorpay_refund_id": rfd_decision.razorpay_refund_id,
    }

import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Registration, Payment, Flag
from app.schemas import RegistrationCreate, RegistrationResponse
from app.services.razorpay_service import create_razorpay_order
from app.services.audit_service import log_audit
from app.agents.duplicate_detector import detect_duplicates

router = APIRouter(prefix="/events", tags=["Events & Registration"])

@router.post("/{event_id}/register", response_model=RegistrationResponse)
def register_for_event(event_id: str, payload: RegistrationCreate, db: Session = Depends(get_db)):
    reg_id = f"REG-{uuid.uuid4().hex[:6].upper()}"
    pay_id = f"PAY-{uuid.uuid4().hex[:6].upper()}"
    flg_id = f"FLG-{uuid.uuid4().hex[:6].upper()}"

    # 1. Create Razorpay order
    order_id, amount, pay_actor = create_razorpay_order(payload.amount, receipt=f"receipt_{reg_id}")

    # 2. Create Registration record
    new_reg = Registration(
        id=reg_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        event_id=event_id,
        status="pending_payment"
    )
    db.add(new_reg)

    # 3. Create Payment record
    new_pay = Payment(
        id=pay_id,
        registration_id=reg_id,
        razorpay_order_id=order_id,
        amount=amount,
        status="created"
    )
    db.add(new_pay)
    db.commit()

    log_audit(
        db=db,
        actor="system",
        action="REGISTRATION_CREATED",
        entity_id=reg_id,
        payload={"name": payload.name, "email": payload.email, "phone": payload.phone, "order_id": order_id, "amount": amount}
    )

    # 4. Run Duplicate Detector Agent
    is_flag, flag_type, matched_fields, explanation, dup_actor = detect_duplicates(db, new_reg, new_pay)

    flag_id_res = None
    if is_flag:
        new_reg.status = "flagged"
        new_flag = Flag(
            id=flg_id,
            registration_id=reg_id,
            payment_id=pay_id,
            flag_type=flag_type,
            ai_explanation=explanation,
            matched_fields=json.dumps(matched_fields),
            status="open"
        )
        db.add(new_flag)
        db.commit()
        flag_id_res = flg_id

        log_audit(
            db=db,
            actor=dup_actor, # 'ai_duplicate_detector' or 'fallback_duplicate_detector'
            action="FLAG_RAISED",
            entity_id=flg_id,
            payload={
                "registration_id": reg_id,
                "flag_type": flag_type,
                "matched_fields": matched_fields,
                "explanation": explanation
            }
        )
    else:
        new_reg.status = "registered"
        db.commit()

    return RegistrationResponse(
        id=new_reg.id,
        name=new_reg.name,
        email=new_reg.email,
        phone=new_reg.phone,
        event_id=new_reg.event_id,
        status=new_reg.status,
        razorpay_order_id=order_id,
        amount=amount,
        is_flagged=is_flag,
        flag_id=flag_id_res,
        created_at=new_reg.created_at
    )

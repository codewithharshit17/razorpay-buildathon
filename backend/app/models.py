import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(String, primary_key=True, index=True) # e.g. REG-1001
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, default="EVT-2026-WORKSHOP", index=True)
    status = Column(String, nullable=False, default="pending_payment") 
    # Statuses: pending_payment, registered, flagged, verified, rejected, refunded, partially_refunded
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    payments = relationship("Payment", back_populates="registration")
    flags = relationship("Flag", back_populates="registration")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True) # e.g. PAY-1001
    registration_id = Column(String, ForeignKey("registrations.id"), nullable=False)
    razorpay_payment_id = Column(String, nullable=True, index=True)
    razorpay_order_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False) # In INR
    status = Column(String, nullable=False, default="created")
    # Statuses: created, captured, failed, refunded, partially_refunded
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    registration = relationship("Registration", back_populates="payments")
    flags = relationship("Flag", back_populates="payment")
    refund_decisions = relationship("RefundDecision", back_populates="payment")

class Flag(Base):
    __tablename__ = "flags"

    id = Column(String, primary_key=True, index=True) # e.g. FLG-1001
    registration_id = Column(String, ForeignKey("registrations.id"), nullable=False)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True)
    flag_type = Column(String, nullable=False) # duplicate_registration, duplicate_payment
    ai_explanation = Column(Text, nullable=False)
    matched_fields = Column(Text, nullable=False) # JSON array string, e.g. '["phone", "name"]'
    status = Column(String, nullable=False, default="open")
    # Statuses: open, resolving_via_call, call_verified, call_denied, call_unclear, manually_approved, manually_rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    registration = relationship("Registration", back_populates="flags")
    payment = relationship("Payment", back_populates="flags")
    calls = relationship("VerificationCall", back_populates="flag")

class VerificationCall(Base):
    __tablename__ = "verification_calls"

    id = Column(String, primary_key=True, index=True) # e.g. CALL-1001
    flag_id = Column(String, ForeignKey("flags.id"), nullable=False)
    twilio_call_sid = Column(String, nullable=True, index=True)
    question_asked = Column(Text, nullable=False)
    transcript = Column(Text, nullable=True)
    parsed_intent = Column(String, nullable=True) # confirms_duplicate, denies_duplicate, unclear
    outcome = Column(String, nullable=False, default="pending")
    # Outcomes: pending, auto_resolved_refund_extra, auto_resolved_kept, escalated_to_organizer, call_failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    flag = relationship("Flag", back_populates="calls")

class RefundDecision(Base):
    __tablename__ = "refund_decisions"

    id = Column(String, primary_key=True, index=True) # e.g. RFD-1001
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    ai_recommendation = Column(String, nullable=False) # full_refund, partial_50_percent, no_refund, refund_extra_only
    policy_clause = Column(Text, nullable=False)
    human_decision = Column(String, nullable=True) # approved, overridden, rejected
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    payment = relationship("Payment", back_populates="refund_decisions")

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, index=True) # Monospace hash format e.g. aud_9f8a32b
    actor = Column(String, nullable=False, index=True) 
    # Actors: system, ai_duplicate_detector, fallback_duplicate_detector, ai_intent_parser, fallback_intent_parser, ai_refund_reasoner, fallback_rule_engine, twilio_voice, simulated_call, organizer
    action = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    payload = Column(Text, nullable=False) # JSON formatted string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

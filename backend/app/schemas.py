from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import datetime

class RegistrationCreate(BaseModel):
    name: str = Field(..., example="Rahul Sharma")
    email: str = Field(..., example="rahul.sharma@example.com")
    phone: str = Field(..., example="+919876543210")
    event_id: str = Field(default="EVT-2026-WORKSHOP")
    amount: float = Field(default=500.0)

class RegistrationResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    event_id: str
    status: str
    razorpay_order_id: str
    amount: float
    is_flagged: bool = False
    flag_id: Optional[str] = None
    payment_actor: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class FlagResponse(BaseModel):
    id: str
    registration_id: str
    payment_id: Optional[str]
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    flag_type: str
    ai_explanation: str
    matched_fields: List[str]
    status: str
    registrant_name: str
    registrant_email: str
    registrant_phone: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class CallVerifyRequest(BaseModel):
    mode: str = Field(default="auto", description="'live' (Twilio) or 'simulated' or 'auto'")

class CallSimulateRequest(BaseModel):
    spoken_transcript: str = Field(..., example="Yeah, I registered twice by mistake. Please refund the extra payment.")

class FlagResolveRequest(BaseModel):
    decision: str = Field(..., description="'approve_keep', 'approve_refund_extra', 'reject'")
    reason: str = Field(default="Organizer manual decision")

class RefundRequest(BaseModel):
    hours_before_event: float = Field(default=80.0)
    is_no_show: bool = Field(default=False)
    is_duplicate_payment: bool = Field(default=False)
    reason: str = Field(default="Cannot attend due to schedule conflict")

class RefundResolveRequest(BaseModel):
    decision: str = Field(..., description="'approved' or 'overridden' or 'rejected'")
    override_amount: Optional[float] = None
    reason: str = Field(default="Organizer decision")

class DashboardSummary(BaseModel):
    total_registrations: int
    total_collected: float
    total_refunded: float
    open_flags_count: int
    resolved_flags_count: int
    call_outcomes: dict
    demo_metrics: dict

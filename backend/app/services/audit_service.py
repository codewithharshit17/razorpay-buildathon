import uuid
import json
from sqlalchemy.orm import Session
from app.models import AuditLog

def generate_audit_id() -> str:
    return f"aud_{uuid.uuid4().hex[:8]}"

def log_audit(db: Session, actor: str, action: str, entity_id: str, payload: dict) -> AuditLog:
    """
    Logs an action to the audit trail with a monospace hash-like ID.
    `actor` explicitly indicates the execution engine source:
    - 'ai_duplicate_detector' vs 'fallback_duplicate_detector'
    - 'ai_intent_parser' vs 'fallback_intent_parser'
    - 'ai_refund_reasoner' vs 'fallback_rule_engine'
    - 'twilio_voice' vs 'simulated_call'
    - 'organizer' / 'system'
    """
    payload_str = json.dumps(payload, default=str)
    audit_entry = AuditLog(
        id=generate_audit_id(),
        actor=actor,
        action=action,
        entity_id=entity_id,
        payload=payload_str
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

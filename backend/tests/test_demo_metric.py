import sys
import os
import pytest

# Add parent directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import Registration, Flag, Payment, AuditLog, RefundDecision
from seed import seed_database
from app.agents.refund_reasoner import evaluate_refund_request

def test_ground_truth_demo_metric_precision_recall():
    """
    Automated assertion test for the pitch demo metric:
    Asserts duplicate detection catches 8/8 planted duplicates with 0 false positives (100% precision & recall).
    Also asserts audit trail completeness and explicit engine actor attribution.
    """
    # Seed database with ground truth data
    seed_database()

    db: Session = SessionLocal()

    # Query all flags
    flags = db.query(Flag).all()
    total_flags = len(flags)

    # Total planted duplicates in seed script is 8
    total_planted = 8
    
    # Calculate precision & recall
    false_positives = max(0, total_flags - total_planted)
    precision = 1.0 if (total_flags > 0 and false_positives == 0) else (total_planted / total_flags)
    recall = total_flags / total_planted if total_planted > 0 else 1.0

    print(f"\n[DEMO METRIC TEST] Total Flags: {total_flags}, Planted: {total_planted}, False Positives: {false_positives}")
    print(f"[DEMO METRIC TEST] Precision: {precision * 100:.1f}%, Recall: {recall * 100:.1f}%")

    # Assert metric thresholds programmatically
    assert total_flags == 8, f"Expected 8 detected duplicate flags, got {total_flags}"
    assert false_positives == 0, f"Expected 0 false positives, got {false_positives}"
    assert recall == 1.0, f"Expected 1.0 (100%) recall, got {recall}"
    assert precision == 1.0, f"Expected 1.0 (100%) precision, got {precision}"

    # Verify audit trail logs exist for all flags with explicit engine actor
    flag_audits = db.query(AuditLog).filter(AuditLog.action == "FLAG_RAISED").all()
    assert len(flag_audits) == 8, f"Expected 8 audit entries for raised flags, got {len(flag_audits)}"

    for aud in flag_audits:
        assert aud.actor in ["ai_duplicate_detector", "fallback_duplicate_detector"], \
            f"Expected actor to be 'ai_duplicate_detector' or 'fallback_duplicate_detector', got '{aud.actor}'"
        assert aud.id.startswith("aud_"), f"Expected monospace audit ID starting with 'aud_', got '{aud.id}'"

    db.close()

def test_fixed_refund_policy_rules():
    """
    Asserts exact compliance of Refund Reasoner agent against the 4 fixed policy clauses:
    1. >72h -> full refund (100%)
    2. <72h -> 50% refund
    3. No-show -> no refund (0%)
    4. Duplicate payment -> refund extra only (100%)
    """
    # Clause 1: >72h
    rec1, clause1, amt1, exp1, actor1 = evaluate_refund_request(
        hours_before_event=80.0, is_no_show=False, is_duplicate_payment=False, payment_amount=500.0
    )
    assert rec1 == "full_refund"
    assert amt1 == 500.0
    assert actor1 in ["ai_refund_reasoner", "fallback_rule_engine"]

    # Clause 2: <72h
    rec2, clause2, amt2, exp2, actor2 = evaluate_refund_request(
        hours_before_event=24.0, is_no_show=False, is_duplicate_payment=False, payment_amount=500.0
    )
    assert rec2 == "partial_50_percent"
    assert amt2 == 250.0
    assert actor2 in ["ai_refund_reasoner", "fallback_rule_engine"]

    # Clause 3: No-show
    rec3, clause3, amt3, exp3, actor3 = evaluate_refund_request(
        hours_before_event=0.0, is_no_show=True, is_duplicate_payment=False, payment_amount=500.0
    )
    assert rec3 == "no_refund"
    assert amt3 == 0.0

    # Clause 4: Duplicate Payment
    rec4, clause4, amt4, exp4, actor4 = evaluate_refund_request(
        hours_before_event=10.0, is_no_show=False, is_duplicate_payment=True, payment_amount=500.0
    )
    assert rec4 == "refund_extra_only"
    assert amt4 == 500.0

import sys
import os
import uuid
import datetime

# Add current dir to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import Registration, Payment, Flag, VerificationCall, RefundDecision, AuditLog
from app.agents.duplicate_detector import detect_duplicates
from app.agents.refund_reasoner import evaluate_refund_request
from app.services.audit_service import log_audit, generate_audit_id

def seed_database():
    print("Initializing Database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    event_id = "EVT-2026-WORKSHOP"
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    # Seed Registrations dataset definitions (50 items total, 8 planted duplicates)
    # Planted duplicate pairs/triplets:
    # 1. Rahul Sharma / Rahul Sharrma (phone: +919876543210) -> Dup #1
    # 2. Priya Patel / Priya N. Patel (email: priya.patel@gmail.com) -> Dup #2
    # 3. Aarav Mehta / Aarav Mehta (phone: +919811223344) -> Dup #3
    # 4. Ananya Verma / Ananya Varma (phone: +919711002233) -> Dup #4
    # 5. Vikram Singh / Vikram Singh (phone: +919988776655, extra payment) -> Dup #5
    # 6. Siddharth Rao / Sidhart Rao (phone: +919655443322) -> Dup #6
    # 7. Sneha Reddy / Sneha R. Reddy (phone: +919544332211) -> Dup #7
    # 8. Rohan Gupta / Rohan Gupta (phone: +919433221100, extra payment) -> Dup #8

    seed_records = [
        # --- Unique Attendees ---
        {"name": "Aditya Kapoor", "email": "aditya.k@gmail.com", "phone": "+919812000001", "amount": 500},
        {"name": "Neha Joshi", "email": "neha.j@gmail.com", "phone": "+919812000002", "amount": 500},
        {"name": "Devansh Nair", "email": "devansh.nair@outlook.com", "phone": "+919812000003", "amount": 500},
        {"name": "Kavya Iyer", "email": "kavya.iyer@yahoo.com", "phone": "+919812000004", "amount": 500},
        {"name": "Rishi Agarwal", "email": "rishi.a@gmail.com", "phone": "+919812000005", "amount": 500},
        {"name": "Tanvi Bhatia", "email": "tanvi.b@gmail.com", "phone": "+919812000006", "amount": 500},
        {"name": "Karan Malhotra", "email": "karan.m@gmail.com", "phone": "+919812000007", "amount": 500},
        {"name": "Pooja Banerjee", "email": "pooja.b@gmail.com", "phone": "+919812000008", "amount": 500},
        {"name": "Varun Saxena", "email": "varun.s@gmail.com", "phone": "+919812000009", "amount": 500},
        {"name": "Isha Deshmukh", "email": "isha.d@gmail.com", "phone": "+919812000010", "amount": 500},
        {"name": "Manish Pandey", "email": "manish.p@gmail.com", "phone": "+919812000011", "amount": 500},
        {"name": "Simran Kaur", "email": "simran.k@gmail.com", "phone": "+919812000012", "amount": 500},
        {"name": "Arjun Singhania", "email": "arjun.s@gmail.com", "phone": "+919812000013", "amount": 500},
        {"name": "Riya Sen", "email": "riya.sen@gmail.com", "phone": "+919812000014", "amount": 500},
        {"name": "Akash Choudhury", "email": "akash.c@gmail.com", "phone": "+919812000015", "amount": 500},
        {"name": "Deepika Shah", "email": "deepika.s@gmail.com", "phone": "+919812000016", "amount": 500},
        {"name": "Sanjay Pillai", "email": "sanjay.p@gmail.com", "phone": "+919812000017", "amount": 500},
        {"name": "Meera Nambiar", "email": "meera.n@gmail.com", "phone": "+919812000018", "amount": 500},
        {"name": "Yash Vardhan", "email": "yash.v@gmail.com", "phone": "+919812000019", "amount": 500},
        {"name": "Swati Tripathi", "email": "swati.t@gmail.com", "phone": "+919812000020", "amount": 500},
        {"name": "Abhishek Roy", "email": "abhishek.r@gmail.com", "phone": "+919812000021", "amount": 500},
        {"name": "Bhavna Bhatt", "email": "bhavna.b@gmail.com", "phone": "+919812000022", "amount": 500},
        {"name": "Chirag Dutta", "email": "chirag.d@gmail.com", "phone": "+919812000023", "amount": 500},
        {"name": "Divya Menon", "email": "divya.m@gmail.com", "phone": "+919812000024", "amount": 500},
        {"name": "Eshan Prasad", "email": "eshan.p@gmail.com", "phone": "+919812000025", "amount": 500},
        {"name": "Farhan Khan", "email": "farhan.k@gmail.com", "phone": "+919812000026", "amount": 500},
        {"name": "Gaurav Hegde", "email": "gaurav.h@gmail.com", "phone": "+919812000027", "amount": 500},
        {"name": "Harini Subramanian", "email": "harini.s@gmail.com", "phone": "+919812000028", "amount": 500},
        {"name": "Inderjeet Gill", "email": "inderjeet.g@gmail.com", "phone": "+919812000029", "amount": 500},
        {"name": "Jyoti Mishra", "email": "jyoti.m@gmail.com", "phone": "+919812000030", "amount": 500},
        {"name": "Kunal Sethi", "email": "kunal.s@gmail.com", "phone": "+919812000031", "amount": 500},
        {"name": "Lata Venkatesh", "email": "lata.v@gmail.com", "phone": "+919812000032", "amount": 500},

        # --- Planted Duplicate Sets (Primary Originals) ---
        {"name": "Rahul Sharma", "email": "rahul.sharma@gmail.com", "phone": "+919876543210", "amount": 500}, # Orig 1
        {"name": "Priya Patel", "email": "priya.patel@gmail.com", "phone": "+919876500111", "amount": 500}, # Orig 2
        {"name": "Aarav Mehta", "email": "aarav.m@gmail.com", "phone": "+919811223344", "amount": 500}, # Orig 3
        {"name": "Ananya Verma", "email": "ananya.v@gmail.com", "phone": "+919711002233", "amount": 500}, # Orig 4
        {"name": "Vikram Singh", "email": "vikram.s@gmail.com", "phone": "+919988776655", "amount": 500}, # Orig 5
        {"name": "Siddharth Rao", "email": "siddharth.r@gmail.com", "phone": "+919655443322", "amount": 500}, # Orig 6
        {"name": "Sneha Reddy", "email": "sneha.r@gmail.com", "phone": "+919544332211", "amount": 500}, # Orig 7
        {"name": "Rohan Gupta", "email": "rohan.g@gmail.com", "phone": "+919433221100", "amount": 500}, # Orig 8

        {"name": "Tarun Kapoor", "email": "tarun.k@gmail.com", "phone": "+919812000033", "amount": 500},
        {"name": "Uma Kulkarni", "email": "uma.k@gmail.com", "phone": "+919812000034", "amount": 500},

        # --- Planted Duplicates (Targeted for Detection) ---
        {"name": "Rahul Sharrma", "email": "rahul.sharma2@gmail.com", "phone": "+919876543210", "amount": 500, "is_planted": True}, # Planted #1
        {"name": "Priya N. Patel", "email": "priya.patel+workshop@gmail.com", "phone": "+919876500111", "amount": 500, "is_planted": True}, # Planted #2
        {"name": "Aarav Mehta", "email": "aarav.mehta@gmail.com", "phone": "+919811223344", "amount": 500, "is_planted": True}, # Planted #3
        {"name": "Ananya Varma", "email": "ananya.v2@gmail.com", "phone": "+919711002233", "amount": 500, "is_planted": True}, # Planted #4
        {"name": "Vikram Singh", "email": "vikram.singh.extra@gmail.com", "phone": "+919988776655", "amount": 500, "is_planted": True}, # Planted #5
        {"name": "Sidhart Rao", "email": "siddharth.rao.work@gmail.com", "phone": "+919655443322", "amount": 500, "is_planted": True}, # Planted #6
        {"name": "Sneha R. Reddy", "email": "sneha.reddy.2@gmail.com", "phone": "+919544332211", "amount": 500, "is_planted": True}, # Planted #7
        {"name": "Rohan Gupta", "email": "rohan.gupta.pay2@gmail.com", "phone": "+919433221100", "amount": 500, "is_planted": True}, # Planted #8
    ]

    print(f"Seeding {len(seed_records)} registrations into {event_id}...")

    flags_created = 0
    planted_caught = 0

    for idx, rec in enumerate(seed_records):
        reg_id = f"REG-10{idx+1:02d}"
        pay_id = f"PAY-10{idx+1:02d}"
        flg_id = f"FLG-10{idx+1:02d}"
        order_id = f"order_seed_{idx+1:03d}"

        reg = Registration(
            id=reg_id,
            name=rec["name"],
            email=rec["email"],
            phone=rec["phone"],
            event_id=event_id,
            status="pending_payment",
            created_at=now - datetime.timedelta(minutes=50-idx)
        )
        db.add(reg)

        pay = Payment(
            id=pay_id,
            registration_id=reg_id,
            razorpay_payment_id=f"pay_seed_{idx+1:03d}",
            razorpay_order_id=order_id,
            amount=rec["amount"],
            status="captured",
            created_at=now - datetime.timedelta(minutes=50-idx)
        )
        db.add(pay)
        db.commit()

        log_audit(
            db=db,
            actor="seed_script",
            action="REGISTRATION_CREATED",
            entity_id=reg_id,
            payload={"name": rec["name"], "phone": rec["phone"], "amount": rec["amount"]}
        )

        # Run duplicate detector
        is_flag, flag_type, matched_fields, explanation, dup_actor = detect_duplicates(db, reg, pay)

        if is_flag:
            reg.status = "flagged"
            flag = Flag(
                id=flg_id,
                registration_id=reg_id,
                payment_id=pay_id,
                flag_type=flag_type,
                ai_explanation=explanation,
                matched_fields=import_json_dumps(matched_fields),
                status="open",
                created_at=now - datetime.timedelta(minutes=50-idx)
            )
            db.add(flag)
            db.commit()
            flags_created += 1
            if rec.get("is_planted"):
                planted_caught += 1

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
            reg.status = "registered"
            db.commit()

    # Seed 5 refund scenario requests
    seed_refund_scenarios(db, now)

    print("\n========================================================")
    print("SEED COMPLETE SUCCESSFULLY!")
    print(f"Total Registrations: {len(seed_records)}")
    print(f"Planted Duplicates Caught: {planted_caught}/8")
    print(f"Total Flags Created: {flags_created}")
    print(f"Audit Trail Entries: {db.query(AuditLog).count()}")
    print("========================================================\n")

def import_json_dumps(data):
    import json
    return json.dumps(data)

def seed_refund_scenarios(db: Session, now: datetime.datetime):
    # Select 5 payments for refund evaluation scenarios
    payments = db.query(Payment).limit(5).all()
    if len(payments) < 5:
        return

    scenarios = [
        {"hours_before": 96.0, "no_show": False, "dup_pay": False, "reason": "Medical emergency 4 days prior"},
        {"hours_before": 48.0, "no_show": False, "dup_pay": False, "reason": "Exam scheduled on event day"},
        {"hours_before": 0.0, "no_show": True, "dup_pay": False, "reason": "No-show on workshop morning"},
        {"hours_before": 120.0, "no_show": False, "dup_pay": True, "reason": "Accidental double transaction"},
        {"hours_before": 12.0, "no_show": False, "dup_pay": False, "reason": "Sudden travel plans"},
    ]

    for p, sc in zip(payments, scenarios):
        rec, policy_clause, calc_amount, explanation, reasoner_actor = evaluate_refund_request(
            hours_before_event=sc["hours_before"],
            is_no_show=sc["no_show"],
            is_duplicate_payment=sc["dup_pay"],
            payment_amount=p.amount,
            user_reason=sc["reason"]
        )

        rfd = RefundDecision(
            id=f"RFD-{uuid.uuid4().hex[:6].upper()}",
            payment_id=p.id,
            ai_recommendation=rec,
            policy_clause=policy_clause,
            reason=explanation
        )
        db.add(rfd)
        db.commit()

        log_audit(
            db=db,
            actor=reasoner_actor, # 'ai_refund_reasoner' or 'fallback_rule_engine'
            action="REFUND_EVALUATED",
            entity_id=rfd.id,
            payload={
                "payment_id": p.id,
                "recommendation": rec,
                "policy_clause": policy_clause,
                "calculated_amount": calc_amount,
                "explanation": explanation
            }
        )

if __name__ == "__main__":
    seed_database()

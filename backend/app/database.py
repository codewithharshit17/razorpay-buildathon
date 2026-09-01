from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def ensure_schema_columns():
    """Apply the small additive migrations needed by existing local databases."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "payments" in tables:
        payment_columns = {column["name"] for column in inspector.get_columns("payments")}
        for name, definition in {"razorpay_signature": "VARCHAR"}.items():
            if name not in payment_columns:
                with engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE payments ADD COLUMN {name} {definition}"))

    if "refund_decisions" in tables:
        refund_columns = {column["name"] for column in inspector.get_columns("refund_decisions")}
        additions = {
            "calculated_amount": "FLOAT NOT NULL DEFAULT 0.0",
            "razorpay_refund_id": "VARCHAR",
        }
        with engine.begin() as connection:
            for name, definition in additions.items():
                if name not in refund_columns:
                    connection.execute(text(f"ALTER TABLE refund_decisions ADD COLUMN {name} {definition}"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

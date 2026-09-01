import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    PORT: int = int(os.getenv("PORT", "8000"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trust_layer.db")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_USE_MOCK: bool = os.getenv("RAZORPAY_USE_MOCK", "false").strip().lower() in {"1", "true", "yes", "on"}

    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

config = Config()


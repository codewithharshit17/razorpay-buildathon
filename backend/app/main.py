from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import events, webhooks, flags, payments, dashboard

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="College Workshops Event Payments Trust Layer",
    description="Razorpay AI Buildathon — Open Track Trust & Audit Layer for College Event Payments",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(events.router)
app.include_router(webhooks.router)
app.include_router(flags.router)
app.include_router(payments.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "app": "College Workshops Event Payments Trust Layer",
        "version": "1.0.0",
        "endpoints": [
            "/events/{id}/register",
            "/flags",
            "/flags/{id}/call-verify",
            "/flags/{id}/simulate-call",
            "/webhooks/razorpay",
            "/webhooks/twilio/gather",
            "/payments/{id}/refund-request",
            "/dashboard",
            "/dashboard/audit-logs"
        ]
    }

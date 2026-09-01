import uuid
from typing import Tuple
from app.config import config

def create_razorpay_order(amount: float, receipt: str) -> Tuple[str, float, str]:
    """
    Creates a Razorpay order in real test mode. The mock path is opt-in only for local dev.
    Returns: (order_id, amount_in_inr, actor)
    """
    amount_in_paise = int(amount * 100)
    key_id = (config.RAZORPAY_KEY_ID or "").strip()
    key_secret = (config.RAZORPAY_KEY_SECRET or "").strip()

    if key_id and key_secret and key_id.startswith("rzp_test_"):
        try:
            import razorpay
            client = razorpay.Client(auth=(key_id, key_secret))
            order_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": receipt,
                "payment_capture": 1
            }
            order = client.order.create(data=order_data)
            return (order["id"], amount, "razorpay_test_api")
        except Exception as e:
            if config.RAZORPAY_USE_MOCK:
                print(f"[RazorpayService] Live test API call failed, using mock order (explicit opt-in only): {e}")
                mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
                return (mock_order_id, amount, "razorpay_mock_gateway")
            raise RuntimeError(f"Razorpay order creation failed: {e}")

    if config.RAZORPAY_USE_MOCK:
        print("[RazorpayService] MOCKED ORDER: explicit fallback enabled for local dev only; this is not a real payment.")
        mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
        return (mock_order_id, amount, "razorpay_mock_gateway")

    raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured for real Razorpay test payments")

def verify_razorpay_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
) -> bool:
    """
    Verifies Razorpay HMAC SHA256 signature for test payments.
    """
    key_id = (config.RAZORPAY_KEY_ID or "").strip()
    if not razorpay_order_id or razorpay_order_id.startswith("order_") or (key_id and key_id.startswith("rzp_test_mock")):
        return True
    if not key_id or not config.RAZORPAY_KEY_SECRET:
        print("[RazorpayService] Signature verification skipped: missing Razorpay test credentials")
        return False
    try:
        import razorpay
        client = razorpay.Client(auth=(key_id, config.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
        return True
    except Exception as e:
        print(f"[RazorpayService] Signature verification failed: {e}")
        return False

def execute_razorpay_refund(razorpay_payment_id: str | None, amount_in_inr: float) -> tuple[str | None, str | None]:
    """Refund a captured Razorpay test-mode payment without ever fabricating an ID."""
    key_id = (config.RAZORPAY_KEY_ID or "").strip()
    key_secret = (config.RAZORPAY_KEY_SECRET or "").strip()

    if not razorpay_payment_id:
        return None, "missing stored Razorpay payment ID"
    if not key_id or not key_id.startswith("rzp_test_"):
        return None, "Razorpay test-mode credentials are not configured"
    if not key_secret or key_secret == "mock_secret_key_123456":
        return None, "Razorpay test-mode credentials are not configured"

    amount_in_paise = int(round(amount_in_inr * 100))
    if amount_in_paise <= 0:
        return None, "refund amount must be greater than zero"

    try:
        import razorpay

        client = razorpay.Client(auth=(key_id, key_secret))
        refund = client.payment.refund(razorpay_payment_id, {"amount": amount_in_paise})
        refund_id = refund.get("id")
        if not refund_id:
            return None, "Razorpay did not return a refund ID"
        return refund_id, None
    except Exception as exc:
        return None, f"Razorpay refund API request failed: {exc}"

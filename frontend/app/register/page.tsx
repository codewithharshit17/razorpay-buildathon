"use client";
import { useState } from "react";
import { registerForEvent, verifyRazorpayPayment } from "@/lib/api";

const RAZORPAY_KEY_ID = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_TVuD8tJdcpXhUk";

function loadRazorpayScript() {
  return new Promise<void>((resolve, reject) => {
    if (typeof window === "undefined") {
      reject(new Error("Window is unavailable"));
      return;
    }
    if ((window as any).Razorpay) {
      resolve();
      return;
    }

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Razorpay Checkout.js"));
    document.body.appendChild(script);
  });
}

export default function RegisterPage() {
  const [form, setForm] = useState({ name: "", email: "", phone: "", event_id: "EVT-2026-WORKSHOP", amount: 500 });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>("");

  const update = (k: string, v: any) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await registerForEvent(form);
      setResult(data);

      if (data.payment_actor === "razorpay_mock_gateway") {
        setError("MOCKED — not a real payment. Set RAZORPAY_USE_MOCK=false and valid Razorpay test credentials to use a live checkout flow.");
        return;
      }

      await loadRazorpayScript();
      const razorpayOptions = {
        key: RAZORPAY_KEY_ID,
        amount: Math.round(Number(data.amount) * 100),
        currency: "INR",
        name: "Event KhataBook",
        description: `Registration for ${data.name}`,
        order_id: data.razorpay_order_id,
        handler: async function (response: any) {
          try {
            const verification = await verifyRazorpayPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            setResult({ ...data, payment_status: verification.status, razorpay_payment_id: verification.razorpay_payment_id, razorpay_signature: verification.razorpay_signature });
          } catch (verifyError: any) {
            setError(verifyError.message || "Payment verification failed");
          }
        },
        modal: {
          ondismiss: function () {
            setError("Razorpay checkout was closed before payment was completed.");
          }
        },
        prefill: {
          name: data.name,
          email: data.email,
          phone: data.phone,
        },
        theme: { color: "#1f8fff" },
      };

      const razorpay = new (window as any).Razorpay(razorpayOptions);
      razorpay.open();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Registration Desk</h1>
        <span className="page-subtitle">EVT-2026-WORKSHOP - AI & FULL-STACK WORKSHOP</span>
      </div>

      <div className="two-col" style={{ maxWidth: "900px" }}>
        {/* Registration Form */}
        <div style={{ border: "1px solid var(--border)", background: "var(--bg-card)", padding: "1.25rem" }}>
          <div className="section-title" style={{ marginBottom: "0.875rem" }}>New Entry</div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" value={form.name} onChange={e => update("name", e.target.value)} placeholder="Rahul Sharma" required />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" type="email" value={form.email} onChange={e => update("email", e.target.value)} placeholder="rahul@example.com" required />
            </div>
            <div className="form-group">
              <label className="form-label">Phone (with country code)</label>
              <input className="form-input font-mono" value={form.phone} onChange={e => update("phone", e.target.value)} placeholder="+919876543210" required />
            </div>
            <div className="form-group">
              <label className="form-label">Amount (₹)</label>
              <input className="form-input font-mono text-right" type="number" value={form.amount} onChange={e => update("amount", Number(e.target.value))} min={100} required />
            </div>
            <div className="form-group">
              <label className="form-label">Event ID</label>
              <input className="form-input font-mono" value={form.event_id} onChange={e => update("event_id", e.target.value)} required />
            </div>
            {error && <div style={{ color: "var(--status-error)", fontSize: "0.75rem", marginBottom: "0.75rem", fontFamily: "var(--font-mono)" }}>{error}</div>}
            <button className="btn btn-primary w-full" type="submit" disabled={loading}>
              {loading ? "POSTING ENTRY..." : "REGISTER + CREATE ORDER"}
            </button>
          </form>
        </div>

        {/* Result Panel */}
        <div style={{ border: "1px solid var(--border)", background: "var(--bg-card)", padding: "1.25rem" }}>
          <div className="section-title" style={{ marginBottom: "0.875rem" }}>Entry Output</div>
          {!result ? (
            <div className="empty-state" style={{ borderTop: "1px solid var(--border-subtle)" }}>POST A REGISTRATION ENTRY TO REVIEW ORDER OUTPUT AND DUPLICATE DETECTION.</div>
          ) : (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.375rem 0.875rem", fontSize: "0.78rem", marginBottom: "1rem" }}>
                <span className="text-muted">Reg ID</span>
                <span className="font-mono text-amber num-cell">{result.id}</span>
                <span className="text-muted">Status</span>
                <span className={`badge ${result.status === "flagged" ? "badge-error" : "badge-verified"}`}>{result.status}</span>
                <span className="text-muted">Order ID</span>
                <span className="font-mono num-cell" style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{result.razorpay_order_id}</span>
                <span className="text-muted">Amount</span>
                <span className="amount num-cell" style={{ color: "var(--status-refund)" }}>₹{result.amount?.toLocaleString("en-IN")}</span>
                <span className="text-muted">Name</span>
                <span>{result.name}</span>
                <span className="text-muted">Email</span>
                <span style={{ fontSize: "0.7rem" }}>{result.email}</span>
                <span className="text-muted">Phone</span>
                <span className="font-mono num-cell" style={{ fontSize: "0.72rem" }}>{result.phone}</span>
              </div>

              {result.is_flagged ? (
                <div className="notice-panel" style={{ background: "var(--amber-bg)", borderColor: "var(--amber-dim)", marginTop: "0.5rem" }}>
                  <div className="notice-title" style={{ color: "var(--amber)" }}>
                    Duplicate Flag Raised
                  </div>
                  <div className="notice-copy">
                    Flag ID: <span className="font-mono">{result.flag_id}</span>
                    <br />Potential duplicate detected. Move this entry to the flag queue for voice verification.
                  </div>
                  <div style={{ marginTop: "0.625rem" }}>
                    <a href="/flags" className="btn btn-call btn-sm" style={{ fontSize: "0.68rem" }}>
                      OPEN FLAG QUEUE
                    </a>
                  </div>
                </div>
              ) : (
                <div className="notice-panel" style={{ borderLeftColor: "var(--status-refund)", marginTop: "0.5rem" }}>
                  <div className="notice-title" style={{ color: "var(--status-refund)" }}>
                    Entry Cleared
                  </div>
                  <div className="notice-copy">
                    No duplicate pattern detected. Registration remains active in the ledger.
                  </div>
                </div>
              )}

              <div style={{ marginTop: "0.875rem", padding: "0.625rem 0.875rem", background: "var(--bg-base)", border: "1px solid var(--border-subtle)", fontSize: "0.72rem", color: "var(--text-muted)" }}>
                <strong style={{ color: "var(--text-secondary)" }}>Razorpay checkout:</strong> real payment is handled via the Razorpay Checkout.js modal using the order ID returned above. If the server is intentionally configured for a mock fallback, the UI will clearly label it as <span style={{ color: "var(--status-error)" }}>MOCKED — not a real payment</span>.
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

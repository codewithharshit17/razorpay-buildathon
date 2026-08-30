"use client";
import { useState } from "react";
import { registerForEvent } from "@/lib/api";

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
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Event Registration</h1>
        <span className="page-subtitle">EVT-2026-WORKSHOP — AI & Full-Stack Workshop</span>
      </div>

      <div className="two-col" style={{ maxWidth: "900px" }}>
        {/* Registration Form */}
        <div style={{ border: "1px solid var(--border)", background: "var(--bg-card)", padding: "1.25rem" }}>
          <div className="section-title" style={{ marginBottom: "0.875rem" }}>New Registration</div>
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
              <input className="form-input font-mono" type="number" value={form.amount} onChange={e => update("amount", Number(e.target.value))} min={100} required />
            </div>
            <div className="form-group">
              <label className="form-label">Event ID</label>
              <input className="form-input font-mono" value={form.event_id} onChange={e => update("event_id", e.target.value)} required />
            </div>
            {error && <div style={{ color: "var(--status-error)", fontSize: "0.75rem", marginBottom: "0.75rem" }}>⚠ {error}</div>}
            <button className="btn btn-primary w-full" type="submit" disabled={loading}>
              {loading ? "Registering…" : "Register & Create Order →"}
            </button>
          </form>
        </div>

        {/* Result Panel */}
        <div style={{ border: "1px solid var(--border)", background: "var(--bg-card)", padding: "1.25rem" }}>
          <div className="section-title" style={{ marginBottom: "0.875rem" }}>Registration Result</div>
          {!result ? (
            <div style={{ color: "var(--text-muted)", fontSize: "0.78rem", padding: "1.5rem 0" }}>
              Submit the form to see registration output and duplicate detection result.
            </div>
          ) : (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.375rem 0.875rem", fontSize: "0.78rem", marginBottom: "1rem" }}>
                <span className="text-muted">Reg ID</span>
                <span className="font-mono text-amber">{result.id}</span>
                <span className="text-muted">Status</span>
                <span className={`badge ${result.status === "flagged" ? "badge-error" : "badge-verified"}`}>{result.status}</span>
                <span className="text-muted">Order ID</span>
                <span className="font-mono" style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{result.razorpay_order_id}</span>
                <span className="text-muted">Amount</span>
                <span className="amount" style={{ color: "var(--status-refund)" }}>₹{result.amount?.toLocaleString("en-IN")}</span>
                <span className="text-muted">Name</span>
                <span>{result.name}</span>
                <span className="text-muted">Email</span>
                <span style={{ fontSize: "0.7rem" }}>{result.email}</span>
                <span className="text-muted">Phone</span>
                <span className="font-mono" style={{ fontSize: "0.72rem" }}>{result.phone}</span>
              </div>

              {result.is_flagged ? (
                <div style={{ background: "var(--amber-bg)", border: "1px solid var(--amber-dim)", borderLeft: "2px solid var(--amber)", padding: "0.75rem", marginTop: "0.5rem" }}>
                  <div style={{ fontWeight: 700, color: "var(--amber)", fontSize: "0.78rem", marginBottom: "0.25rem" }}>
                    ⚑ Duplicate Flag Raised
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)" }}>
                    Flag ID: <span className="font-mono">{result.flag_id}</span>
                    <br />AI detected a potential duplicate registration. Go to the Flag Queue to trigger voice verification.
                  </div>
                  <div style={{ marginTop: "0.625rem" }}>
                    <a href="/flags" className="btn btn-call btn-sm" style={{ fontSize: "0.68rem" }}>
                      → View Flag Queue
                    </a>
                  </div>
                </div>
              ) : (
                <div style={{ background: "var(--bg-base)", border: "1px solid #064e3b", borderLeft: "2px solid var(--status-refund)", padding: "0.75rem", marginTop: "0.5rem" }}>
                  <div style={{ fontWeight: 700, color: "var(--status-refund)", fontSize: "0.78rem" }}>
                    ✓ Registered Successfully
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                    No duplicate patterns detected. Registration is active.
                  </div>
                </div>
              )}

              {/* Mock Razorpay Checkout Note */}
              <div style={{ marginTop: "0.875rem", padding: "0.625rem 0.875rem", background: "var(--bg-base)", border: "1px solid var(--border-subtle)", fontSize: "0.72rem", color: "var(--text-muted)" }}>
                <strong style={{ color: "var(--text-secondary)" }}>Razorpay Test Mode:</strong> In production, use the{" "}
                <span className="font-mono">razorpay_order_id</span> ({result.razorpay_order_id}) with the Razorpay checkout SDK to collect payment. In test mode, payment capture is mocked automatically.
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

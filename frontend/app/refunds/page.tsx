"use client";
import { useState, useEffect, useCallback } from "react";
import { fetchFlags, requestRefund, resolveRefund } from "@/lib/api";

function formatCurrency(v: number) {
  return "₹" + v.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const POLICY_PRESETS = [
  { label: ">72h Before Event (Full Refund)", hours: 96, noShow: false, dupPay: false },
  { label: "<72h Before Event (50% Refund)", hours: 24, noShow: false, dupPay: false },
  { label: "No-Show (No Refund)", hours: 0, noShow: true, dupPay: false },
  { label: "Duplicate Payment (Refund Extra)", hours: 10, noShow: false, dupPay: true },
];

function getRecoClass(rec: string) {
  switch (rec) {
    case "full_refund": return "badge-refund";
    case "partial_50_percent": return "badge-open";
    case "no_refund": return "badge-error";
    case "refund_extra_only": return "badge-refund";
    default: return "badge-resolved";
  }
}

export default function RefundsPage() {
  const [flags, setFlags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPaymentId, setSelectedPaymentId] = useState<string>("");
  const [preset, setPreset] = useState(0);
  const [customReason, setCustomReason] = useState("Cannot attend the workshop.");
  const [customHours, setCustomHours] = useState(96);
  const [processing, setProcessing] = useState(false);
  const [refundResult, setRefundResult] = useState<any>(null);
  const [humanDecision, setHumanDecision] = useState<string>("");
  const [resolving, setResolving] = useState(false);
  const [resolveMsg, setResolveMsg] = useState<string>("");
  const [error, setError] = useState<string>("");

  const loadRegistrations = useCallback(async () => {
    setLoading(true);
    try {
      // Get all flags to find payment IDs (as a source of valid payments)
      const f = await fetchFlags("all");
      setFlags(f);
      if (f.length > 0 && f[0].payment_id) setSelectedPaymentId(f[0].payment_id);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRegistrations(); }, [loadRegistrations]);

  const p = POLICY_PRESETS[preset];

  const handleRefundRequest = async () => {
    if (!selectedPaymentId) { setError("SELECT A PAYMENT ID BEFORE EVALUATION."); return; }
    setProcessing(true);
    setError("");
    setRefundResult(null);
    setResolveMsg("");
    try {
      const data = await requestRefund(selectedPaymentId, {
        hours_before_event: preset === 3 ? customHours : p.hours,
        is_no_show: p.noShow,
        is_duplicate_payment: p.dupPay,
        reason: customReason,
      });
      setRefundResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleHumanDecision = async () => {
    if (!refundResult || !humanDecision) return;
    setResolving(true);
    try {
      await resolveRefund(refundResult.payment_id, humanDecision, "Organizer decision via dashboard");
      setResolveMsg(`Decision "${humanDecision}" applied and logged to audit trail.`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setResolving(false);
    }
  };

  const paymentIds = flags.filter(f => f.payment_id).map(f => f.payment_id);

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Refund Desk</h1>
        <span className="page-subtitle">4 POLICY CLAUSES LOCKED</span>
      </div>

      {/* Policy Reference Card */}
        <div style={{ border: "1px solid var(--border)", background: "var(--bg-card)", padding: "1rem 1.25rem", marginBottom: "1.25rem" }}>
        <div className="section-title" style={{ marginBottom: "0.5rem" }}>Fixed Refund Policy</div>
        <table className="ledger-table">
          <thead><tr><th>Clause</th><th>Condition</th><th>Refund Amount</th></tr></thead>
          <tbody>
            <tr><td className="font-mono text-muted num-cell" style={{ fontSize: "0.7rem" }}>§1</td><td>Cancellation &gt;72h before event</td><td className="amount num-cell" style={{ color: "var(--status-refund)" }}>100% (full refund)</td></tr>
            <tr><td className="font-mono text-muted num-cell" style={{ fontSize: "0.7rem" }}>§2</td><td>Cancellation &lt;72h before event</td><td className="amount num-cell" style={{ color: "var(--status-open)" }}>50% (partial refund)</td></tr>
            <tr><td className="font-mono text-muted num-cell" style={{ fontSize: "0.7rem" }}>§3</td><td>No-show on event day</td><td className="amount num-cell" style={{ color: "var(--status-error)" }}>0% (no refund)</td></tr>
            <tr><td className="font-mono text-muted num-cell" style={{ fontSize: "0.7rem" }}>§4</td><td>Duplicate payment</td><td className="amount num-cell" style={{ color: "var(--status-refund)" }}>100% of extra payment</td></tr>
          </tbody>
        </table>
      </div>

      <div className="two-col">
        {/* Refund Request Form */}
        <div style={{ border: "1px solid var(--border)", background: "var(--bg-card)", padding: "1rem 1.25rem" }}>
          <div className="section-title" style={{ marginBottom: "0.875rem" }}>Refund Request Entry</div>

          <div className="form-group">
              <label className="form-label">Payment ID</label>
              <select className="form-select" value={selectedPaymentId} onChange={e => setSelectedPaymentId(e.target.value)}>
                <option value="">SELECT PAYMENT ID...</option>
              {paymentIds.map(id => <option key={id} value={id}>{id}</option>)}
              <option value="PAY-101001">PAY-101001 (Seed #1)</option>
              <option value="PAY-101002">PAY-101002 (Seed #2)</option>
              <option value="PAY-101003">PAY-101003 (Seed #3)</option>
              <option value="PAY-101004">PAY-101004 (Seed #4)</option>
              <option value="PAY-101005">PAY-101005 (Seed #5)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Scenario (Policy Clause)</label>
            <select className="form-select" value={preset} onChange={e => setPreset(Number(e.target.value))}>
              {POLICY_PRESETS.map((p, i) => (
                <option key={i} value={i}>{p.label}</option>
              ))}
            </select>
          </div>

          {preset === 0 && (
            <div className="form-group">
              <label className="form-label">Hours Before Event</label>
              <input type="number" className="form-input" value={customHours} onChange={e => setCustomHours(Number(e.target.value))} min={0} />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Participant Reason</label>
            <textarea className="form-input" rows={2} style={{ resize: "none" }} value={customReason} onChange={e => setCustomReason(e.target.value)} />
          </div>

          {error && <div style={{ color: "var(--status-error)", fontSize: "0.75rem", marginBottom: "0.75rem", fontFamily: "var(--font-mono)" }}>{error}</div>}

          <button className="btn btn-primary" onClick={handleRefundRequest} disabled={processing || !selectedPaymentId}>
            {processing ? "EVALUATING..." : "EVALUATE REFUND"}
          </button>
        </div>

        {/* AI Refund Reasoner Result */}
        <div style={{ border: "1px solid var(--border)", background: "var(--bg-card)", padding: "1rem 1.25rem" }}>
          <div className="section-title" style={{ marginBottom: "0.875rem" }}>Refund Decision Output</div>

          {!refundResult ? (
            <div className="empty-state" style={{ borderTop: "1px solid var(--border-subtle)" }}>ENTER A PAYMENT ID AND CLAUSE INPUT TO OPEN THE REFUND DECISION LEDGER.</div>
          ) : (
            <>
              <div style={{ display: "grid", gap: "0.5rem", marginBottom: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span className="text-xs text-muted">Recommendation</span>
                  <span className={`badge ${getRecoClass(refundResult.ai_recommendation)}`}>
                    {refundResult.ai_recommendation.replace(/_/g, " ")}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span className="text-xs text-muted">Calculated Amount</span>
                  <span className="amount num-cell" style={{ color: "var(--status-refund)", fontSize: "1.25rem" }}>
                    {formatCurrency(refundResult.calculated_amount)}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span className="text-xs text-muted">Engine Actor</span>
                  <span className={`badge actor-badge ${refundResult.actor === "ai_refund_reasoner" ? "badge-ai" : "badge-fallback"}`}>
                    {refundResult.actor}
                  </span>
                </div>
              </div>

              <div style={{ background: "var(--bg-base)", border: "1px solid var(--border-subtle)", padding: "0.75rem", marginBottom: "0.875rem" }}>
                <div className="text-xs text-muted mb-1">Policy Clause</div>
                <div className="font-mono" style={{ fontSize: "0.72rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {refundResult.policy_clause}
                </div>
              </div>

              <div style={{ background: "var(--bg-base)", border: "1px solid var(--border-subtle)", padding: "0.75rem", marginBottom: "0.875rem" }}>
                <div className="text-xs text-muted mb-1">AI Explanation</div>
                <div style={{ fontSize: "0.76rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
                  {refundResult.explanation}
                </div>
              </div>

              {/* Organizer Decision */}
              <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "0.875rem" }}>
                <div className="text-xs text-muted mb-2">Organizer Decision</div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
                  <select className="form-select" style={{ fontSize: "0.72rem" }} value={humanDecision} onChange={e => setHumanDecision(e.target.value)}>
                    <option value="">SELECT DECISION...</option>
                    <option value="approved">APPROVE - USE RECOMMENDATION</option>
                    <option value="overridden">OVERRIDE - APPLY DIFFERENT AMOUNT</option>
                    <option value="rejected">REJECT - NO REFUND</option>
                  </select>
                  <button className="btn btn-primary btn-sm" onClick={handleHumanDecision} disabled={!humanDecision || resolving}>
                    {resolving ? "LOGGING..." : "APPLY + LOG"}
                  </button>
                </div>
                {resolveMsg && (
                  <div style={{ color: "var(--status-verified)", fontSize: "0.75rem", fontFamily: "var(--font-mono)" }}>
                    {resolveMsg}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

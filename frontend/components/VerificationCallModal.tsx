"use client";
import { useState } from "react";
import { simulateCall, triggerCallVerify, resolveFlag } from "@/lib/api";

interface Flag {
  id: string;
  registration_id: string;
  payment_id?: string;
  flag_type: string;
  ai_explanation: string;
  matched_fields: string[];
  status: string;
  registrant_name: string;
  registrant_email: string;
  registrant_phone: string;
  created_at: string;
}

interface Props {
  flag: Flag;
  onClose: () => void;
  onResolved: () => void;
}

const SAMPLE_TRANSCRIPTS = [
  "Yes, I think I registered twice by mistake. Please refund the extra payment.",
  "No, that's not me. It must be a different person with the same number.",
  "I'm not sure, maybe my friend also signed up using my phone.",
];

export default function VerificationCallModal({ flag, onClose, onResolved }: Props) {
  const [phase, setPhase] = useState<"idle" | "calling" | "simulating" | "result">("idle");
  const [transcript, setTranscript] = useState(SAMPLE_TRANSCRIPTS[0]);
  const [result, setResult] = useState<any>(null);
  const [callInfo, setCallInfo] = useState<any>(null);
  const [manualDecision, setManualDecision] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const handleRealCall = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await triggerCallVerify(flag.id);
      setCallInfo(data);
      setPhase("calling");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await simulateCall(flag.id, transcript);
      setResult(data);
      setPhase("result");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleManualResolve = async () => {
    if (!manualDecision) return;
    setLoading(true);
    try {
      await resolveFlag(flag.id, manualDecision, "Manual organizer decision from call modal");
      onResolved();
      onClose();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const intentColor = (intent: string) => {
    if (intent === "confirms_duplicate") return "badge-error";
    if (intent === "denies_duplicate") return "badge-verified";
    return "badge-resolved";
  };

  const outcomeLabel = (outcome: string) => {
    switch (outcome) {
      case "auto_resolved_refund_extra": return "↩ Auto-refunded extra payment";
      case "auto_resolved_kept": return "✓ Verified — registration kept";
      case "escalated_to_organizer": return "⚑ Escalated to organizer";
      default: return outcome;
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Voice Verification
            </div>
            <div className="hash-id" style={{ marginTop: "0.125rem" }}>
              Flag {flag.id} — {flag.registrant_name}
            </div>
          </div>
          <button onClick={onClose} className="btn btn-ghost btn-sm">✕</button>
        </div>

        <div className="modal-body">
          {/* Flag Context */}
          <div style={{ background: "var(--amber-bg)", border: "1px solid var(--amber-dim)", padding: "0.75rem", marginBottom: "1rem", borderLeft: "2px solid var(--amber)" }}>
            <div className="text-xs text-muted mb-1">AI Duplicate Explanation</div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-primary)", lineHeight: 1.5 }}>{flag.ai_explanation}</div>
            <div style={{ marginTop: "0.5rem" }}>
              {flag.matched_fields.map((f) => <span key={f} className="field-tag">{f}</span>)}
            </div>
          </div>

          {/* Participant Info */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginBottom: "1rem", fontSize: "0.75rem" }}>
            <div>
              <div className="text-xs text-muted">Phone</div>
              <div className="font-mono">{flag.registrant_phone}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Email</div>
              <div className="font-mono" style={{ fontSize: "0.7rem" }}>{flag.registrant_email}</div>
            </div>
          </div>

          {/* Action Phase: Idle */}
          {phase === "idle" && (
            <>
              {/* Real Call Section */}
              <div style={{ border: "1px solid var(--border)", padding: "0.875rem", marginBottom: "0.75rem" }}>
                <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.375rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  Live Twilio Call
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.625rem", lineHeight: 1.4 }}>
                  Places an actual outbound call to <span className="font-mono" style={{ color: "var(--text-primary)" }}>{flag.registrant_phone}</span> using Twilio Voice API. Requires TWILIO_* env vars.
                </div>
                <button className="btn btn-call" onClick={handleRealCall} disabled={loading}>
                  📞 Call to Verify
                </button>
              </div>

              {/* Simulate Section */}
              <div style={{ border: "1px solid var(--border)", padding: "0.875rem" }}>
                <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.375rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  ◈ Simulate Call <span className="badge badge-fallback" style={{ marginLeft: "0.375rem" }}>Demo Mode</span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.625rem", lineHeight: 1.4 }}>
                  Enter the participant's spoken response to test the Call Intent Parser agent.
                </div>
                <select
                  className="form-select w-full"
                  style={{ marginBottom: "0.5rem", fontSize: "0.78rem" }}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                >
                  {SAMPLE_TRANSCRIPTS.map((t) => (
                    <option key={t} value={t}>{t.substring(0, 60)}…</option>
                  ))}
                </select>
                <textarea
                  className="form-input w-full"
                  rows={2}
                  style={{ resize: "none", fontFamily: "var(--font-mono)", fontSize: "0.76rem" }}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Type participant's spoken response..."
                />
                <div style={{ marginTop: "0.5rem" }}>
                  <button className="btn btn-simulate" onClick={handleSimulateSubmit} disabled={loading || !transcript}>
                    ◈ Simulate Call &amp; Parse Intent
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Phase: Real Call In Progress */}
          {phase === "calling" && callInfo && (
            <div style={{ border: "1px solid var(--border)", padding: "1.25rem" }}>
              <div className="call-pulse" style={{ marginBottom: "0.75rem" }}>
                <div className="pulse-dot" />
                <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--status-call)" }}>Call in Progress</span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
                Twilio is calling <span className="font-mono" style={{ color: "var(--text-primary)" }}>{flag.registrant_phone}</span>. The participant will hear a scripted yes/no question and their spoken response will be sent to <span className="font-mono">/webhooks/twilio/gather</span>.
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.25rem 0.75rem", fontSize: "0.72rem" }}>
                <span className="text-muted">Call SID</span>
                <span className="font-mono" style={{ color: "var(--text-primary)" }}>{callInfo.twilio_call_sid}</span>
                <span className="text-muted">Actor</span>
                <span className={`badge actor-badge ${callInfo.actor === "twilio_voice" ? "badge-call" : "badge-fallback"}`}>{callInfo.actor}</span>
                <span className="text-muted">Question</span>
                <span style={{ color: "var(--text-secondary)", lineHeight: 1.4 }}>{callInfo.question_asked}</span>
              </div>
              <div style={{ marginTop: "1rem", fontSize: "0.72rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                When Twilio receives the spoken answer, it will POST to /webhooks/twilio/gather. The flag status will update automatically.
              </div>
            </div>
          )}

          {/* Phase: Simulated Call Result */}
          {phase === "result" && result && (
            <div style={{ border: "1px solid var(--border)", padding: "0.875rem" }}>
              <div style={{ fontSize: "0.72rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "0.625rem" }}>
                Call Intent Parse Result
              </div>
              <div style={{ fontSize: "0.75rem", marginBottom: "0.75rem", background: "var(--bg-base)", padding: "0.625rem 0.875rem", border: "1px solid var(--border-subtle)" }}>
                <span className="text-muted">Transcript: </span>
                <span className="font-mono" style={{ color: "var(--text-primary)", fontSize: "0.72rem" }}>"{result.transcript}"</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "0.375rem 0.875rem", fontSize: "0.75rem", marginBottom: "0.875rem" }}>
                <span className="text-muted">Intent</span>
                <span className={`badge ${intentColor(result.parsed_intent)}`}>{result.parsed_intent}</span>
                <span className="text-muted">Confidence</span>
                <span className="font-mono">{(result.confidence * 100).toFixed(0)}%</span>
                <span className="text-muted">Outcome</span>
                <span style={{ color: "var(--text-secondary)" }}>{outcomeLabel(result.outcome)}</span>
                <span className="text-muted">Actor</span>
                <span className={`badge actor-badge ${result.actor === "ai_intent_parser" ? "badge-ai" : "badge-fallback"}`}>{result.actor}</span>
                <span className="text-muted">Explanation</span>
                <span style={{ color: "var(--text-secondary)", lineHeight: 1.4 }}>{result.explanation}</span>
              </div>
              <div style={{ fontSize: "0.72rem", color: result.outcome === "escalated_to_organizer" ? "var(--status-open)" : "var(--status-verified)", fontWeight: 600 }}>
                {result.outcome === "escalated_to_organizer"
                  ? "⚑ Unclear intent — manual organizer decision required."
                  : "✓ Flag auto-resolved based on participant response."}
              </div>
            </div>
          )}

          {/* Manual Decision Fallback (always available) */}
          {flag.status !== "manually_approved" && flag.status !== "manually_rejected" && phase !== "calling" && (
            <div style={{ marginTop: "0.875rem", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.875rem" }}>
              <div className="text-xs text-muted mb-2">Manual Organizer Override</div>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <select className="form-select" style={{ fontSize: "0.72rem" }} value={manualDecision} onChange={(e) => setManualDecision(e.target.value)}>
                  <option value="">Select decision…</option>
                  <option value="approve_refund_extra">Approve — Refund Extra Payment</option>
                  <option value="approve_keep">Approve — Keep Both Registrations</option>
                  <option value="reject">Reject — Remove Duplicate</option>
                </select>
                <button className="btn btn-secondary btn-sm" onClick={handleManualResolve} disabled={!manualDecision || loading}>
                  Apply
                </button>
              </div>
            </div>
          )}

          {error && <div style={{ marginTop: "0.75rem", color: "var(--status-error)", fontSize: "0.75rem" }}>⚠ {error}</div>}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary btn-sm" onClick={onClose}>Close</button>
          {phase === "result" && (
            <button className="btn btn-primary btn-sm" onClick={() => { onResolved(); onClose(); }}>Done</button>
          )}
        </div>
      </div>
    </div>
  );
}

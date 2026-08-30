"use client";
import { useState, useEffect, useCallback } from "react";
import { fetchFlags } from "@/lib/api";
import VerificationCallModal from "@/components/VerificationCallModal";

const STATUS_TABS = ["all", "open", "resolving_via_call", "call_verified", "call_unclear", "manually_approved", "manually_rejected"];

function getStatusBadge(status: string) {
  const map: Record<string, string> = {
    open: "badge-open",
    resolving_via_call: "badge-call",
    call_verified: "badge-verified",
    call_denied: "badge-verified",
    call_unclear: "badge-open",
    manually_approved: "badge-verified",
    manually_rejected: "badge-resolved",
  };
  return map[status] ?? "badge-resolved";
}

function formatDt(ts: string) {
  const d = new Date(ts);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) + " " +
    d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
}

export default function FlagsPage() {
  const [tab, setTab] = useState("all");
  const [flags, setFlags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchFlags(tab);
      setFlags(data);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => { load(); }, [load]);

  return (
    <>
      {selected && (
        <VerificationCallModal flag={selected} onClose={() => setSelected(null)} onResolved={load} />
      )}

      <div className="page-header">
        <h1 className="page-title">Flag Queue</h1>
        <span className="page-subtitle">{flags.length} records</span>
      </div>

      <div className="tabs">
        {STATUS_TABS.map((s) => (
          <button key={s} className={`tab ${tab === s ? "active" : ""}`} onClick={() => setTab(s)}>
            {s === "all" ? "All" : s.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <div className="ledger-table-wrap">
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : flags.length === 0 ? (
          <div className="empty-state">No flags found for filter: <strong>{tab}</strong></div>
        ) : (
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Flag ID</th>
                <th>Registrant</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Type</th>
                <th>Matched Fields</th>
                <th>Status</th>
                <th>AI Explanation</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {flags.map((flag) => (
                <tr key={flag.id}>
                  <td>
                    <div className="audit-id">{flag.id}</div>
                    <div className="hash-id">{flag.registration_id}</div>
                  </td>
                  <td style={{ fontWeight: 500 }}>{flag.registrant_name}</td>
                  <td className="font-mono" style={{ fontSize: "0.72rem" }}>{flag.registrant_phone}</td>
                  <td className="font-mono" style={{ fontSize: "0.68rem", color: "var(--text-secondary)" }}>{flag.registrant_email}</td>
                  <td>
                    <span className={`badge ${flag.flag_type === "duplicate_payment" ? "badge-error" : "badge-open"}`}>
                      {flag.flag_type === "duplicate_payment" ? "dup pay" : "dup reg"}
                    </span>
                  </td>
                  <td>
                    {flag.matched_fields.map((f: string) => (
                      <span key={f} className="field-tag">{f}</span>
                    ))}
                  </td>
                  <td>
                    <span className={`badge ${getStatusBadge(flag.status)}`}>
                      {flag.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td style={{ maxWidth: "220px" }}>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                      {flag.ai_explanation.substring(0, 90)}{flag.ai_explanation.length > 90 ? "…" : ""}
                    </div>
                  </td>
                  <td className="hash-id" style={{ whiteSpace: "nowrap" }}>{formatDt(flag.created_at)}</td>
                  <td>
                    {(flag.status === "open" || flag.status === "call_unclear") && (
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                        <button className="btn btn-call btn-sm" onClick={() => setSelected(flag)} style={{ fontSize: "0.62rem" }}>
                          📞 Call to Verify
                        </button>
                        <button className="btn btn-simulate btn-sm" onClick={() => setSelected(flag)} style={{ fontSize: "0.62rem" }}>
                          ◈ Simulate Call
                        </button>
                      </div>
                    )}
                    {flag.status === "resolving_via_call" && (
                      <div className="call-pulse">
                        <div className="pulse-dot" />
                        <span style={{ fontSize: "0.65rem", color: "var(--status-call)" }}>calling…</span>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

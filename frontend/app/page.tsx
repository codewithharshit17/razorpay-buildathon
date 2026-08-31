"use client";
import { useState, useEffect, useCallback } from "react";
import { fetchDashboard, fetchFlags, fetchAuditLogs } from "@/lib/api";
import VerificationCallModal from "@/components/VerificationCallModal";

function formatCurrency(v: number) {
  return "₹" + v.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

function formatDate(ts: string) {
  const d = new Date(ts);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) + " " +
    d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
}

function getStatusClass(status: string) {
  switch (status) {
    case "open": return "flag-open";
    case "resolving_via_call": return "flag-call";
    case "call_verified": case "manually_approved": return "flag-verified";
    case "call_unclear": return "flag-open";
    default: return "flag-resolved";
  }
}

function getBadgeClass(status: string) {
  switch (status) {
    case "open": return "badge-open";
    case "resolving_via_call": return "badge-call";
    case "call_verified": case "manually_approved": case "auto_resolved_kept": return "badge-verified";
    case "call_denied": return "badge-verified";
    case "call_unclear": return "badge-open";
    case "manually_rejected": return "badge-resolved";
    default: return "badge-resolved";
  }
}

function getActorBadgeClass(actor: string) {
  if (actor.startsWith("ai_")) return "badge-ai";
  if (actor.startsWith("fallback_")) return "badge-fallback";
  if (actor === "twilio_voice") return "badge-call";
  if (actor === "simulated_call") return "badge-fallback";
  if (actor === "organizer") return "badge-open";
  return "badge-resolved";
}

function parsePayload(payload: string) {
  try {
    const p = typeof payload === "string" ? JSON.parse(payload) : payload;
    const keys = Object.keys(p).slice(0, 3);
    return keys.map(k => `${k}: ${String(p[k]).substring(0, 40)}`).join(" · ");
  } catch { return String(payload).substring(0, 80); }
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [flags, setFlags] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [selectedFlag, setSelectedFlag] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const load = useCallback(async () => {
    try {
      const [d, f, a] = await Promise.all([
        fetchDashboard(),
        fetchFlags("open"),
        fetchAuditLogs(undefined, 20),
      ]);
      setDashboard(d);
      setFlags(f);
      setAuditLogs(a);
      setLastRefresh(new Date());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 8000);
    return () => clearInterval(interval);
  }, [load]);

  const dm = dashboard?.demo_metrics;

  return (
    <>
      {selectedFlag && (
        <VerificationCallModal
          flag={selectedFlag}
          onClose={() => setSelectedFlag(null)}
          onResolved={load}
        />
      )}

      {/* Demo Metric Banner */}
      {dm && (
        <div className="metric-banner">
          <span className="metric-banner-label">Demo Run</span>
          <span className="metric-banner-stat">
            CAUGHT <strong>{Math.min(dm.detected_duplicates, 8)}/8</strong> PLANTED DUPLICATES
          </span>
          <span className="metric-banner-sep">|</span>
          <span className="metric-banner-stat">
            <strong>{dm.false_positives}</strong> FALSE POSITIVES
          </span>
          <span className="metric-banner-sep">|</span>
          <span className="metric-banner-stat">
            <strong>{dm.recall_percent}%</strong> RECALL · <strong>{dm.precision_percent}%</strong> PRECISION
          </span>
          <span className="metric-banner-sep">|</span>
          <span className="metric-banner-stat">
            <strong>{dm.audit_coverage_percent}%</strong> AUDIT COVERAGE
          </span>
          <span className="metric-banner-sep" style={{ marginLeft: "auto" }}>
            <span className="hash-id">REFRESHED {lastRefresh.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })}</span>
          </span>
        </div>
      )}

      {/* Stats Grid */}
      {dashboard && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Collected</div>
            <div className="stat-value green amount">{formatCurrency(dashboard.total_collected)}</div>
            <div className="stat-sub">{dashboard.total_registrations} ENTRIES</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Refunded</div>
            <div className="stat-value amount" style={{ color: "var(--status-open)" }}>
              {formatCurrency(dashboard.total_refunded)}
            </div>
            <div className="stat-sub">DISBURSED LEDGER</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Open Flags</div>
            <div className="stat-value amber">{dashboard.open_flags_count}</div>
            <div className="stat-sub">{dashboard.resolved_flags_count} CLOSED CASES</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Call Outcomes</div>
            <div className="stat-value blue">{dashboard.call_outcomes?.total_calls ?? 0}</div>
            <div className="stat-sub">
              {dashboard.call_outcomes?.auto_resolved_refund_extra ?? 0} AUTO-SETTLED
            </div>
          </div>
        </div>
      )}

      <div className="two-col" style={{ gap: "1.5rem" }}>
        {/* Open Flag Queue */}
        <div>
          <div className="section-header">
            <span className="section-title">Open Flag Ledger</span>
            <a href="/flags" style={{ fontSize: "0.7rem", color: "var(--amber)", textDecoration: "none" }}>All flags →</a>
          </div>
          <div className="ledger-table-wrap">
            {loading ? (
              <div className="empty-state">PULLING OPEN FLAG LEDGER...</div>
            ) : flags.length === 0 ? (
              <div className="empty-state">OPEN FLAG LEDGER CLEAR. NO UNSETTLED DUPLICATE CASES.</div>
            ) : (
              <table className="ledger-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Registrant</th>
                    <th>Match</th>
                    <th>Type</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {flags.slice(0, 8).map((flag) => (
                    <tr key={flag.id} className={getStatusClass(flag.status)}>
                      <td className="num-cell">
                        <div className="audit-id">{flag.id}</div>
                        <div className="hash-id" style={{ marginTop: "0.125rem" }}>{formatDate(flag.created_at)}</div>
                      </td>
                      <td>
                        <div style={{ fontSize: "0.78rem", fontWeight: 500 }}>{flag.registrant_name}</div>
                        <div className="hash-id" style={{ textAlign: "right" }}>{flag.registrant_phone}</div>
                      </td>
                      <td>
                        {flag.matched_fields.map((f: string) => (
                          <span key={f} className="field-tag">{f}</span>
                        ))}
                      </td>
                      <td>
                        <span className={`badge ${flag.flag_type === "duplicate_payment" ? "badge-error" : "badge-open"}`}>
                          {flag.flag_type === "duplicate_payment" ? "dup pay" : "dup reg"}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: "0.375rem", flexDirection: "column" }}>
                          <button
                            className="btn btn-call btn-sm"
                            onClick={() => setSelectedFlag(flag)}
                            style={{ fontSize: "0.65rem" }}
                          >
                            PLACE CALL
                          </button>
                          <button
                            className="btn btn-simulate btn-sm"
                            onClick={() => setSelectedFlag(flag)}
                            style={{ fontSize: "0.65rem" }}
                          >
                            SIMULATE
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Live Audit Feed */}
        <div>
          <div className="section-header">
            <span className="section-title">Live Audit Feed</span>
            <a href="/audit" style={{ fontSize: "0.7rem", color: "var(--amber)", textDecoration: "none" }}>Full log →</a>
          </div>
          <div className="ledger-table-wrap">
            {auditLogs.length === 0 ? (
              <div className="empty-state">AUDIT FEED EMPTY. NO ACTOR-ATTRIBUTED EVENTS LOGGED YET.</div>
            ) : (
              <div>
                {auditLogs.slice(0, 12).map((log) => (
                  <div key={log.id} className="audit-entry">
                    <div className="num-cell">
                      <div className="audit-id">{log.id}</div>
                      <div className="audit-timestamp">{formatTime(log.created_at)}</div>
                    </div>
                    <div>
                      <span className={`badge actor-badge ${getActorBadgeClass(log.actor)}`}>
                        {log.actor}
                      </span>
                    </div>
                    <div>
                      <div className="audit-action">{log.action}</div>
                      <div className="audit-payload">{parsePayload(log.payload)}</div>
                    </div>
                    <div className="hash-id text-right" style={{ fontSize: "0.65rem" }}>
                      {log.entity_id?.substring(0, 12)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

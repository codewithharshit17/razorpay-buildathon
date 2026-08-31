"use client";
import { useState, useEffect, useCallback } from "react";
import { fetchAuditLogs } from "@/lib/api";

const ACTORS = [
  "all",
  "ai_duplicate_detector",
  "fallback_duplicate_detector",
  "ai_intent_parser",
  "fallback_intent_parser",
  "ai_refund_reasoner",
  "fallback_rule_engine",
  "twilio_voice",
  "simulated_call",
  "organizer",
  "system",
  "razorpay_webhook",
  "seed_script",
];

function getActorBadgeClass(actor: string) {
  if (actor.startsWith("ai_")) return "badge-ai";
  if (actor.startsWith("fallback_")) return "badge-fallback";
  if (actor === "twilio_voice") return "badge-call";
  if (actor === "simulated_call") return "badge-fallback";
  if (actor === "organizer") return "badge-open";
  if (actor === "razorpay_webhook") return "badge-refund";
  return "badge-resolved";
}

function formatDt(ts: string) {
  return new Date(ts).toLocaleString("en-IN", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
  });
}

function PayloadDrawer({ payload, onClose }: { payload: string; onClose: () => void }) {
  let formatted = payload;
  try { formatted = JSON.stringify(JSON.parse(payload), null, 2); } catch {}
  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box" style={{ width: "min(680px, 96vw)" }}>
        <div className="modal-header">
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem", fontWeight: 600 }}>PAYLOAD JSON</span>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>CLOSE</button>
        </div>
        <div className="modal-body">
          <pre style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.72rem",
            color: "var(--text-primary)",
            background: "var(--bg-base)",
            padding: "0.875rem",
            border: "1px solid var(--border)",
            overflowX: "auto",
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word"
          }}>
            {formatted}
          </pre>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary btn-sm" onClick={onClose}>CLOSE</button>
        </div>
      </div>
    </div>
  );
}

export default function AuditPage() {
  const [actor, setActor] = useState("all");
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedPayload, setExpandedPayload] = useState<string | null>(null);
  const [limit, setLimit] = useState(100);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs(actor === "all" ? undefined : actor, limit);
      setLogs(data);
    } finally {
      setLoading(false);
    }
  }, [actor, limit]);

  useEffect(() => { load(); }, [load]);

  function parsePayloadSummary(payload: string) {
    try {
      const p = JSON.parse(payload);
      return Object.entries(p)
        .slice(0, 4)
        .map(([k, v]) => `${k}: ${String(v).substring(0, 35)}`)
        .join(" · ");
    } catch { return String(payload).substring(0, 100); }
  }

  return (
    <>
      {expandedPayload && (
        <PayloadDrawer payload={expandedPayload} onClose={() => setExpandedPayload(null)} />
      )}

      <div className="page-header">
        <h1 className="page-title">Audit Log</h1>
        <span className="page-subtitle">{logs.length} ENTRIES</span>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", marginBottom: "1rem" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
          {ACTORS.map((a) => (
            <button
              key={a}
              className={`tab ${actor === a ? "active" : ""}`}
              onClick={() => setActor(a)}
              style={{ fontSize: "0.68rem", padding: "0.25rem 0.5rem" }}
            >
              {a === "all" ? "ALL ACTORS" : a}
            </button>
          ))}
        </div>
        <select
          className="form-select"
          style={{ fontSize: "0.72rem", marginLeft: "auto", width: "auto" }}
          value={limit}
          onChange={e => setLimit(Number(e.target.value))}
        >
          <option value={50}>LAST 50</option>
          <option value={100}>LAST 100</option>
          <option value={200}>LAST 200</option>
        </select>
      </div>

      {/* Audit Log Table */}
      <div className="ledger-table-wrap">
        {loading ? (
          <div className="empty-state">PULLING AUDIT LOG...</div>
        ) : logs.length === 0 ? (
          <div className="empty-state">NO AUDIT ENTRIES MATCH ACTOR FILTER {actor.toUpperCase()}.</div>
        ) : (
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Audit ID</th>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Summary</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="num-cell">
                    <span className="audit-id">{log.id}</span>
                  </td>
                  <td className="num-cell">
                    <span className="font-mono" style={{ fontSize: "0.68rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                      {formatDt(log.created_at)}
                    </span>
                  </td>
                  <td>
                    <span className={`badge actor-badge ${getActorBadgeClass(log.actor)}`}>
                      {log.actor}
                    </span>
                  </td>
                  <td>
                    <span className="font-mono" style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                      {log.action}
                    </span>
                  </td>
                  <td className="num-cell">
                    <span className="hash-id">{log.entity_id}</span>
                  </td>
                  <td style={{ maxWidth: "300px" }}>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                      {parsePayloadSummary(log.payload)}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => setExpandedPayload(log.payload)}
                      style={{ fontSize: "0.65rem" }}
                    >
                      VIEW JSON
                    </button>
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

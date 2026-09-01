const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_BASE = NEXT_PUBLIC_API_URL;

export async function fetchDashboard() {
  const res = await fetch(`${API_BASE}/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

export async function fetchFlags(status?: string) {
  const url = status && status !== "all"
    ? `${API_BASE}/flags?status=${status}`
    : `${API_BASE}/flags`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch flags");
  return res.json();
}

export async function fetchAuditLogs(actor?: string, limit = 100) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (actor && actor !== "all") params.set("actor", actor);
  const res = await fetch(`${API_BASE}/dashboard/audit-logs?${params}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch audit logs");
  return res.json();
}

export async function triggerCallVerify(flagId: string) {
  const res = await fetch(`${API_BASE}/flags/${flagId}/call-verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "auto" }),
  });
  if (!res.ok) throw new Error("Failed to trigger call");
  return res.json();
}

export async function simulateCall(flagId: string, transcript: string) {
  const res = await fetch(`${API_BASE}/flags/${flagId}/simulate-call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ spoken_transcript: transcript }),
  });
  if (!res.ok) throw new Error("Failed to simulate call");
  return res.json();
}

export async function resolveFlag(flagId: string, decision: string, reason: string) {
  const res = await fetch(`${API_BASE}/flags/${flagId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, reason }),
  });
  if (!res.ok) throw new Error("Failed to resolve flag");
  return res.json();
}

export async function requestRefund(paymentId: string, data: {
  hours_before_event: number;
  is_no_show: boolean;
  is_duplicate_payment: boolean;
  reason: string;
}) {
  const res = await fetch(`${API_BASE}/payments/${paymentId}/refund-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to request refund");
  return res.json();
}

export async function resolveRefund(paymentId: string, decision: string, reason: string) {
  const res = await fetch(`${API_BASE}/payments/${paymentId}/resolve-refund`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, reason }),
  });
  if (!res.ok) throw new Error("Failed to resolve refund");
  return res.json();
}

export async function registerForEvent(data: {
  name: string;
  email: string;
  phone: string;
  event_id: string;
  amount: number;
}) {
  const res = await fetch(`${API_BASE}/events/${data.event_id}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to register");
  }
  return res.json();
}

export async function verifyRazorpayPayment(data: {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}) {
  const res = await fetch(`${API_BASE}/payments/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to verify payment");
  }
  return res.json();
}

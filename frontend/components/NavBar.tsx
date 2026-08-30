"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard", icon: "▤" },
  { href: "/flags", label: "Flag Queue", icon: "⚑" },
  { href: "/refunds", label: "Refunds", icon: "↩" },
  { href: "/audit", label: "Audit Log", icon: "☰" },
  { href: "/register", label: "Register", icon: "＋" },
];

export default function NavBar() {
  const pathname = usePathname();
  return (
    <>
      {/* Top bar — spans full width */}
      <header className="topbar" style={{ gridColumn: "1 / -1" }}>
        <span className="topbar-brand">TrustLayer</span>
        <span className="topbar-sub">/ razorpay buildathon</span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span className="hash-id">EVT-2026-WORKSHOP</span>
          <span className="badge badge-open">Test Mode</span>
        </div>
      </header>

      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-section">Navigation</div>
        {links.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className={`sidebar-link ${pathname === href ? "active" : ""}`}
          >
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", width: "16px" }}>{icon}</span>
            {label}
          </Link>
        ))}
      </nav>
    </>
  );
}

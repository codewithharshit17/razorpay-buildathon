"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/flags", label: "Flag Queue" },
  { href: "/refunds", label: "Refunds" },
  { href: "/audit", label: "Audit Log" },
  { href: "/register", label: "Register" },
];

export default function NavBar() {
  const pathname = usePathname();
  return (
    <>
      {/* Top bar — spans full width */}
      <header className="topbar" style={{ gridColumn: "1 / -1" }}>
        <span className="topbar-brand">Event KhataBook</span>
        <span className="topbar-sub">trust and audit layer for student event payments</span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span className="hash-id">EVT-2026-WORKSHOP</span>
          <span className="hash-id">SANDBOX LEDGER</span>
        </div>
      </header>

      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-wordmark">Event KhataBook</div>
        {links.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`sidebar-link ${pathname === href ? "active" : ""}`}
          >
            {label}
          </Link>
        ))}
      </nav>
    </>
  );
}

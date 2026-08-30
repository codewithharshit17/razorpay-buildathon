import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "TrustLayer — College Event Payments Audit",
  description: "AI-powered trust & audit layer for college workshop event registrations. Duplicate detection, Twilio voice verification, and policy-driven refunds.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* App shell uses CSS grid: topbar full-width, then sidebar + main */}
        <div className="app-layout">
          <NavBar />
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

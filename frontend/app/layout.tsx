import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Event KhataBook",
  description: "An AI-powered trust and audit layer for student event payments, built for duplicate detection, voice verification, refunds, and reconciliation.",
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

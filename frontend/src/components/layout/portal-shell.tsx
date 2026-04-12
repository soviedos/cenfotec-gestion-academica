"use client";

import { Navbar, Footer } from "@/components/layout";

/**
 * Minimal shell for the module‑portal / dashboard page.
 * Shows the top navbar and footer but **no** sidebar.
 */
export function PortalShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen bg-muted/30">
      <div className="flex min-h-screen flex-col">
        <Navbar onMenuClick={() => {}} />

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>

        <Footer />
      </div>
    </div>
  );
}

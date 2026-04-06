"use client";

import { useState } from "react";
import { Sidebar, Navbar, MobileSidebar, Footer } from "@/components/layout";
import { cn } from "@/lib/utils";

/**
 * Interactive dashboard shell (client component).
 *
 * Contains stateful sidebar toggle logic so that the parent layout
 * can remain a Server Component.
 */
export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="relative min-h-screen bg-muted/30">
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((prev) => !prev)}
        />
      </div>

      {/* Mobile sidebar (Sheet) */}
      <MobileSidebar open={mobileOpen} onOpenChange={setMobileOpen} />

      {/* Main area: offset by sidebar width */}
      <div
        className={cn(
          "flex min-h-screen flex-col transition-[margin-left] duration-200 ease-in-out",
          collapsed ? "lg:ml-[68px]" : "lg:ml-60",
        )}
      >
        <Navbar onMenuClick={() => setMobileOpen(true)} />

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>

        <Footer />
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Upload, FileText, BarChart3, GraduationCap } from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

const navItems = [
  {
    label: "Cargar PDFs",
    href: "/carga",
    icon: Upload,
  },
  {
    label: "Evaluaciones",
    href: "/evaluaciones",
    icon: FileText,
  },
  {
    label: "Reportes",
    href: "/reportes",
    icon: BarChart3,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-sidebar text-sidebar-foreground">
      {/* Brand */}
      <div className="flex h-16 items-center gap-2 px-6">
        <GraduationCap className="h-6 w-6 text-sidebar-primary" />
        <span className="text-lg font-semibold tracking-tight">
          Evaluaciones
        </span>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <Separator />

      {/* Footer */}
      <div className="px-6 py-4">
        <p className="text-xs text-muted-foreground">Sistema Interno v0.1.0</p>
      </div>
    </aside>
  );
}

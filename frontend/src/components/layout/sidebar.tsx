"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { GraduationCap, PanelLeftClose, PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { navigation } from "./navigation";

/* -------------------------------------------------- */
/*  Sidebar                                            */
/* -------------------------------------------------- */

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 flex flex-col border-r bg-sidebar text-sidebar-foreground transition-[width] duration-200 ease-in-out",
        collapsed ? "w-[68px]" : "w-60",
      )}
    >
      {/* Brand */}
      <div className="flex h-14 items-center justify-center px-4">
        <Link href="/dashboard">
          {collapsed ? (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
              <GraduationCap className="h-4 w-4" />
            </div>
          ) : (
            <Image
              src="/images/logo-cenfotc-Horizontal-Negro.png"
              alt="Universidad CENFOTEC"
              width={180}
              height={40}
              className="h-8 w-auto object-contain dark:invert"
              priority
            />
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {navigation.map((group) => (
          <div key={group.title} className="mb-4">
            {!collapsed && (
              <p className="mb-1.5 px-3 text-[11px] font-medium uppercase tracking-wider text-sidebar-foreground/40">
                {group.title}
              </p>
            )}
            {collapsed && <div className="mb-1.5" />}

            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" &&
                    pathname.startsWith(`${item.href}/`));

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
                        collapsed && "justify-center px-0",
                        isActive
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/60 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
                      )}
                    >
                      {/* Active indicator bar */}
                      {isActive && (
                        <span className="absolute inset-y-1 left-0 w-[3px] rounded-full bg-sidebar-primary" />
                      )}
                      <item.icon
                        className={cn(
                          "h-4 w-4 shrink-0",
                          isActive
                            ? "text-sidebar-primary"
                            : "text-sidebar-foreground/50 group-hover:text-sidebar-foreground/70",
                        )}
                      />
                      {!collapsed && (
                        <span className="truncate">{item.label}</span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer: collapse toggle */}
      <div className="border-t border-sidebar-border p-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className={cn(
            "w-full text-sidebar-foreground/50 hover:text-sidebar-foreground",
            collapsed && "px-0",
          )}
        >
          {collapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <>
              <PanelLeftClose className="mr-2 h-4 w-4" />
              <span className="text-xs">Colapsar</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}

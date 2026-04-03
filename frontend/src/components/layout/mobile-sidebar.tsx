"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { GraduationCap } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { navigation } from "./navigation";

interface MobileSidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MobileSidebar({ open, onOpenChange }: MobileSidebarProps) {
  const pathname = usePathname();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-64 p-0">
        <SheetHeader className="flex h-14 flex-row items-center gap-2.5 border-b px-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <GraduationCap className="h-4 w-4" />
          </div>
          <SheetTitle className="text-sm font-semibold tracking-tight">
            Evaluaciones
          </SheetTitle>
        </SheetHeader>

        <nav className="px-2 py-3">
          {navigation.map((group) => (
            <div key={group.title} className="mb-4">
              <p className="mb-1.5 px-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/60">
                {group.title}
              </p>
              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    pathname.startsWith(`${item.href}/`);

                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => onOpenChange(false)}
                        className={cn(
                          "group relative flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
                          isActive
                            ? "bg-accent text-accent-foreground"
                            : "text-foreground/60 hover:bg-accent/50 hover:text-accent-foreground",
                        )}
                      >
                        {isActive && (
                          <span className="absolute inset-y-1 left-0 w-[3px] rounded-full bg-primary" />
                        )}
                        <item.icon
                          className={cn(
                            "h-4 w-4 shrink-0",
                            isActive
                              ? "text-primary"
                              : "text-foreground/50 group-hover:text-foreground/70",
                          )}
                        />
                        <span className="truncate">{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </SheetContent>
    </Sheet>
  );
}

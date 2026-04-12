"use client";

import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface NavbarProps {
  onMenuClick: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background/80 px-4 backdrop-blur-sm sm:px-6">
      {/* Left: mobile menu + title */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onMenuClick}
          aria-label="Abrir menú"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <h1 className="text-sm font-medium text-muted-foreground">
          Gestión Académica
        </h1>
      </div>

      {/* Right: user placeholder */}
      <div className="flex items-center gap-3">
        <Separator orientation="vertical" className="hidden h-5 sm:block" />
        <span className="text-sm text-muted-foreground">Usuario</span>
      </div>
    </header>
  );
}

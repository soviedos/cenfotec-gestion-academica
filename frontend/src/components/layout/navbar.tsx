"use client";

import { Menu, Power } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/features/auth/hooks/useAuth";

interface NavbarProps {
  onMenuClick?: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background/80 px-4 backdrop-blur-sm sm:px-6">
      {/* Left: mobile menu + title */}
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onMenuClick}
            aria-label="Abrir menú"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}
        <h1 className="text-sm font-medium text-muted-foreground">
          Gestión Académica
        </h1>
      </div>

      {/* Right: user info */}
      <div className="flex items-center gap-3">
        {user && (
          <>
            <span className="text-sm text-muted-foreground">{user.nombre}</span>
            <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium uppercase text-muted-foreground">
              {user.role}
            </span>
            <Separator orientation="vertical" className="hidden h-5 sm:block" />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              aria-label="Cerrar sesión"
              className="gap-1.5 text-muted-foreground"
            >
              <Power className="h-4 w-4" />
              <span className="text-xs">Salir</span>
            </Button>
          </>
        )}
      </div>
    </header>
  );
}

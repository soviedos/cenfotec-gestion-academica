"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useModuleAccess } from "@/features/auth/hooks/useModuleAccess";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { modules } from "@/components/layout/navigation";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const { user } = useAuth();
  const { hasModule, hasPermission } = useModuleAccess();
  const visibleModules = modules.filter((m) => hasModule(m.modulo));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Bienvenido{user ? `, ${user.nombre}` : ""}
        </h2>
        <p className="text-muted-foreground">
          Selecciona un módulo para comenzar.
        </p>
      </div>

      {/* Module grid */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {visibleModules.map((mod) => {
          const canWrite = hasPermission(mod.modulo, "write");

          if (!mod.ready) {
            return (
              <Card
                key={mod.modulo}
                className="relative border-dashed opacity-70"
              >
                <CardHeader className="flex flex-row items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                    <mod.icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-base">{mod.label}</CardTitle>
                    <CardDescription className="text-xs">
                      {mod.description}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
                  <span className="inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                    Próximamente
                  </span>
                </CardContent>
              </Card>
            );
          }

          return (
            <Link key={mod.modulo} href={mod.href} className="group">
              <Card
                className={cn(
                  "transition-shadow group-hover:shadow-md",
                  canWrite && "border-primary/20",
                )}
              >
                <CardHeader className="flex flex-row items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <mod.icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-base">{mod.label}</CardTitle>
                    <CardDescription className="text-xs">
                      {mod.description}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="flex items-center justify-between">
                  <span className="text-sm font-medium text-primary group-hover:underline">
                    Ir al módulo &rarr;
                  </span>
                  {!canWrite && (
                    <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                      Solo lectura
                    </span>
                  )}
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Empty state */}
      {visibleModules.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-12">
          <p className="text-sm text-muted-foreground">
            No tienes acceso a ningún módulo.
          </p>
          <p className="text-xs text-muted-foreground/60">
            Contacta a un administrador para solicitar permisos.
          </p>
        </div>
      )}
    </div>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { modules } from "@/components/layout/navigation";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Vista general de la plataforma. Selecciona un módulo para comenzar.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map((mod) => (
          <Link key={mod.href} href={mod.href} className="group">
            <Card className="transition-shadow group-hover:shadow-md">
              <CardHeader className="flex flex-row items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <mod.icon className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base">{mod.label}</CardTitle>
                  <CardDescription className="text-xs">
                    {mod.description}
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <span className="text-sm font-medium text-primary group-hover:underline">
                  Ir al módulo &rarr;
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { GraduationCap, BarChart3, Shield, FileText } from "lucide-react";
import { useAuth, LoginButton, DevLoginForm } from "@/features/auth";
import { Separator } from "@/components/ui/separator";

export default function LoginPage() {
  const { status } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/dashboard");
    }
  }, [status, router]);

  if (status === "loading" || status === "authenticated") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </main>
    );
  }

  return (
    <main className="flex min-h-screen">
      {/* Left panel — branding */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-zinc-900 p-10 text-white lg:flex">
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-linear-to-br from-zinc-900 via-zinc-800 to-zinc-900" />
        {/* Decorative circles */}
        <div className="absolute -left-20 -top-20 h-72 w-72 rounded-full bg-white/5" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-white/5" />
        <div className="absolute bottom-40 left-20 h-40 w-40 rounded-full bg-white/3" />

        {/* Top: logos */}
        <div className="relative z-10 flex items-center gap-8">
          <Image
            src="/images/logo-cenfotec-Vertical-Negro.png"
            alt="Universidad CENFOTEC"
            width={80}
            height={100}
            className="brightness-0 invert"
          />
          <Separator orientation="vertical" className="h-16 bg-white/20" />
          <Image
            src="/images/logo-Software-Engineering-Negro.png"
            alt="Software Engineering"
            width={200}
            height={66}
            className="brightness-0 invert"
          />
        </div>

        {/* Center: value proposition */}
        <div className="relative z-10 space-y-8">
          <div>
            <h2 className="text-3xl font-bold leading-tight tracking-tight">
              Gestión Académica
            </h2>
            <p className="mt-2 max-w-md text-base text-zinc-400">
              Plataforma integral para la gestión, evaluación y análisis del
              desempeño académico universitario.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {[
              { icon: FileText, label: "Procesamiento de evaluaciones" },
              { icon: BarChart3, label: "Análisis estadístico" },
              { icon: GraduationCap, label: "Seguimiento docente" },
              { icon: Shield, label: "Alertas automáticas" },
            ].map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-3 rounded-lg bg-white/5 px-3 py-2.5"
              >
                <Icon className="h-4 w-4 shrink-0 text-zinc-400" />
                <span className="text-sm text-zinc-300">{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom: footer */}
        <p className="relative z-10 text-xs text-zinc-500">
          Universidad CENFOTEC &middot; Escuela de Ingeniería del Software —
          ESOFT
        </p>
      </div>

      {/* Right panel — login form */}
      <div className="flex w-full flex-col items-center justify-center px-6 lg:w-1/2">
        <div className="w-full max-w-sm space-y-8">
          {/* Mobile-only logo */}
          <div className="flex flex-col items-center gap-4 lg:hidden">
            <Image
              src="/images/logo-cenfotec-Vertical-Negro.png"
              alt="Universidad CENFOTEC"
              width={64}
              height={80}
            />
          </div>

          {/* Heading */}
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight">
              Iniciar sesión
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Ingresa tus credenciales para acceder a la plataforma
            </p>
          </div>

          {/* Google OAuth */}
          <LoginButton />

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <Separator className="w-full" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                o continuar con
              </span>
            </div>
          </div>

          {/* Dev login */}
          <DevLoginForm />
        </div>
      </div>
    </main>
  );
}

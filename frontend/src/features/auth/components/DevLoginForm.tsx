"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn, AlertCircle } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { requestDevToken } from "../lib/authApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function DevLoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("soviedo@ucenfotec.ac.cr");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await requestDevToken(email, password);
      await login(res.access_token);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Email */}
      <div className="space-y-1.5">
        <label htmlFor="dev-email" className="text-sm font-medium">
          Correo electrónico
        </label>
        <Input
          id="dev-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder="usuario@ucenfotec.ac.cr"
          className="h-10"
        />
      </div>

      {/* Password */}
      <div className="space-y-1.5">
        <label htmlFor="dev-password" className="text-sm font-medium">
          Contraseña
        </label>
        <Input
          id="dev-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          placeholder="••••••••"
          className="h-10"
        />
      </div>

      {/* Error */}
      {error && (
        <div
          className="flex items-center gap-2 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive"
          role="alert"
        >
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Submit */}
      <Button
        type="submit"
        disabled={loading}
        size="lg"
        className="w-full h-10"
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            Ingresando…
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <LogIn className="h-4 w-4" />
            Ingresar
          </span>
        )}
      </Button>

      {/* Dev mode badge */}
      <p className="text-center text-[11px] text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-amber-700">
          Modo desarrollo
        </span>
      </p>
    </form>
  );
}

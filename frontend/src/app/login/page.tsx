import { LoginButton } from "@/features/auth/components/LoginButton";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Gestión Académica</h1>
        <p className="mt-2 text-gray-600">
          Inicia sesión para acceder a la plataforma
        </p>
      </div>
      <LoginButton />
    </main>
  );
}

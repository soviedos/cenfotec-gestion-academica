import { Separator } from "@/components/ui/separator";

export function Navbar() {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-6">
      <div>
        <h1 className="text-sm font-medium text-muted-foreground">
          Plataforma de Análisis de Evaluaciones Docentes
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <Separator orientation="vertical" className="h-6" />
        <span className="text-sm text-muted-foreground">Usuario</span>
      </div>
    </header>
  );
}

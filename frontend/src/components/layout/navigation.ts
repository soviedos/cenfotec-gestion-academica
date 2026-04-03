import type { LucideIcon } from "lucide-react";
import {
  Home,
  Upload,
  Library,
  Users,
  BarChart3,
  Heart,
  Sparkles,
  FileBarChart,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const navigation: NavGroup[] = [
  {
    title: "Principal",
    items: [
      { label: "Inicio", href: "/inicio", icon: Home },
      { label: "Carga de PDFs", href: "/carga", icon: Upload },
      { label: "Biblioteca", href: "/biblioteca", icon: Library },
      { label: "Docentes", href: "/docentes", icon: Users },
    ],
  },
  {
    title: "Análisis",
    items: [
      { label: "Estadístico", href: "/estadisticas", icon: BarChart3 },
      { label: "Sentimiento", href: "/sentimiento", icon: Heart },
      { label: "Consultas IA", href: "/consultas-ia", icon: Sparkles },
      { label: "Reportes", href: "/reportes", icon: FileBarChart },
    ],
  },
];

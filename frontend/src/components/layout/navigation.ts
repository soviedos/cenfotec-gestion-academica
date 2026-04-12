import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  ClipboardCheck,
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
    title: "Plataforma",
    items: [{ label: "Dashboard", href: "/dashboard", icon: LayoutDashboard }],
  },
  {
    title: "Evaluación Docente",
    items: [
      {
        label: "Centro de Mando",
        href: "/evaluacion-docente/inicio",
        icon: Home,
      },
      {
        label: "Carga de PDFs",
        href: "/evaluacion-docente/carga",
        icon: Upload,
      },
      {
        label: "Biblioteca",
        href: "/evaluacion-docente/biblioteca",
        icon: Library,
      },
      {
        label: "Docentes",
        href: "/evaluacion-docente/docentes",
        icon: Users,
      },
      {
        label: "Estadístico",
        href: "/evaluacion-docente/estadisticas",
        icon: BarChart3,
      },
      {
        label: "Sentimiento",
        href: "/evaluacion-docente/sentimiento",
        icon: Heart,
      },
      {
        label: "Consultas IA",
        href: "/evaluacion-docente/consultas-ia",
        icon: Sparkles,
      },
      {
        label: "Reportes",
        href: "/evaluacion-docente/reportes",
        icon: FileBarChart,
      },
    ],
  },
];

/** Module metadata for the platform dashboard */
export interface ModuleInfo {
  label: string;
  href: string;
  icon: LucideIcon;
  description: string;
}

export const modules: ModuleInfo[] = [
  {
    label: "Evaluación Docente",
    href: "/evaluacion-docente/inicio",
    icon: ClipboardCheck,
    description:
      "Carga, análisis y monitoreo de evaluaciones docentes institucionales.",
  },
];

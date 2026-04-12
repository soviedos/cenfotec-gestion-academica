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
  ShieldCheck,
  RefreshCcw,
  CalendarRange,
  CalendarDays,
  Briefcase,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export interface NavGroup {
  title: string;
  /** Backend module key (null = always visible, e.g. Dashboard). */
  modulo: string | null;
  items: NavItem[];
}

export const navigation: NavGroup[] = [
  {
    title: "Plataforma",
    modulo: null,
    items: [{ label: "Dashboard", href: "/dashboard", icon: LayoutDashboard }],
  },
  {
    title: "Evaluación Docente",
    modulo: "evaluacion_docente",
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
  /** Backend module key for permission filtering. */
  modulo: string;
  label: string;
  href: string;
  icon: LucideIcon;
  description: string;
  /** Whether the module UI is implemented. False = "próximamente" badge. */
  ready: boolean;
}

export const modules: ModuleInfo[] = [
  {
    modulo: "evaluacion_docente",
    label: "Evaluación Docente",
    href: "/evaluacion-docente/inicio",
    icon: ClipboardCheck,
    description:
      "Carga, análisis y monitoreo de evaluaciones docentes institucionales.",
    ready: true,
  },
  {
    modulo: "control_docente",
    label: "Control Docente",
    href: "/control-docente",
    icon: ShieldCheck,
    description: "Seguimiento de cumplimiento y desempeño del cuerpo docente.",
    ready: false,
  },
  {
    modulo: "convalidaciones",
    label: "Convalidaciones",
    href: "/convalidaciones",
    icon: RefreshCcw,
    description:
      "Gestión de solicitudes de convalidación y equivalencias de cursos.",
    ready: false,
  },
  {
    modulo: "planificacion_cuatrimestral",
    label: "Planificación Cuatrimestral",
    href: "/planificacion-cuatrimestral",
    icon: CalendarRange,
    description: "Planificación de la oferta académica por cuatrimestre.",
    ready: false,
  },
  {
    modulo: "planificacion_mensual",
    label: "Planificación Mensual",
    href: "/planificacion-mensual",
    icon: CalendarDays,
    description:
      "Programación mensual de cursos, horarios y asignación de aulas.",
    ready: false,
  },
  {
    modulo: "planificacion_b2b",
    label: "Planificación B2B",
    href: "/planificacion-b2b",
    icon: Briefcase,
    description:
      "Coordinación de programas corporativos y convenios institucionales.",
    ready: false,
  },
];

# Frontend — Evaluaciones Docentes

> Aplicación web construida con Next.js 16 y TypeScript, usando App Router en formato MPA.

---

## Stack

| Tecnología                                      | Uso                               |
| ----------------------------------------------- | --------------------------------- |
| [Next.js 16](https://nextjs.org/)               | Framework React 19 con App Router |
| [TypeScript 6](https://www.typescriptlang.org/) | Tipado estático                   |
| [Tailwind CSS 4](https://tailwindcss.com/)      | Estilos utilitarios               |
| [ESLint 9](https://eslint.org/)                 | Linting (flat config)             |
| [Vitest](https://vitest.dev/)                   | Tests unitarios                   |
| [PostCSS](https://postcss.org/)                 | Procesamiento de CSS              |

---

## Estructura de Carpetas

```
frontend/
├── public/                          → Archivos estáticos
├── src/
│   ├── app/                         → App Router (páginas MPA)
│   │   ├── (auth)/                  → Grupo: autenticación
│   │   │   └── login/page.tsx
│   │   ├── (dashboard)/             → Grupo: panel principal
│   │   │   ├── carga/page.tsx       → Subida de PDFs
│   │   │   ├── evaluaciones/page.tsx→ Listado de evaluaciones
│   │   │   ├── reportes/page.tsx    → Reportes y métricas
│   │   │   └── layout.tsx           → Layout compartido del dashboard
│   │   ├── layout.tsx               → Layout raíz
│   │   └── page.tsx                 → Página de entrada (redirect)
│   ├── components/
│   │   ├── ui/                      → Componentes base (Button, Input, Card)
│   │   ├── evaluaciones/            → Componentes de dominio
│   │   ├── reportes/                → Componentes de reportes
│   │   └── layout/                  → Navbar, Sidebar, Footer
│   ├── hooks/                       → Custom hooks de React
│   ├── lib/
│   │   ├── api-client.ts            → Wrapper HTTP para el backend
│   │   ├── auth.ts                  → Utilidades de autenticación
│   │   └── utils.ts                 → Funciones utilitarias
│   ├── types/
│   │   └── index.ts                 → Tipos e interfaces compartidas
│   └── styles/
│       └── globals.css              → Estilos globales + Tailwind
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── postcss.config.mjs
├── package.json
├── Dockerfile
└── .env.local.example
```

---

## Desarrollo Local

### Requisitos

- Node.js 20+
- npm 10+ (o pnpm)

### Instalación

```bash
cd frontend

# Instalar dependencias
npm install

# Copiar variables de entorno
cp .env.local.example .env.local

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en `http://localhost:3000`.

### Variables de Entorno

| Variable              | Descripción                    | Ejemplo                 |
| --------------------- | ------------------------------ | ----------------------- |
| `NEXT_PUBLIC_API_URL` | URL base de la API del backend | `http://localhost:8000` |

---

## Scripts Disponibles

```bash
npm run dev       # Servidor de desarrollo con hot reload
npm run build     # Build de producción
npm run start     # Servir build de producción
npm run lint      # ESLint
npm run type-check# Verificación de tipos TypeScript
```

---

## Convenciones

- **Páginas**: Archivo `page.tsx` dentro de carpeta con nombre de ruta
- **Componentes**: `PascalCase` para archivos y exportaciones (`EvaluacionCard.tsx`)
- **Hooks**: Prefijo `use` en `camelCase` (`useEvaluaciones.ts`)
- **Tipos**: Definidos en `src/types/` e importados por alias
- **Estilos**: Tailwind CSS inline, sin archivos CSS por componente
- **Fetching**: Server Components donde sea posible; `api-client.ts` para Client Components

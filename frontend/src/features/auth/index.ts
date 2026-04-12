// Auth feature module — login flow, session management, route guards.
//
// Structure:
//   components/  → UI components (LoginButton, UserMenu, AuthGuard)
//   hooks/       → React hooks (useAuth, useSession, useRequireRole)
//   lib/         → API client helpers, token management
//   types/       → TypeScript interfaces for User, Session, Role

export { type User, type Session, Role } from "./types/auth";

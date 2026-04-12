/** Auth domain types — shared across the auth feature. */

export enum Role {
  ADMIN = "admin",
  COORDINADOR = "coordinador",
  CONSULTOR = "consultor",
}

export interface ModuloPermiso {
  modulo: string;
  permisos: string[];
}

export interface User {
  id: string;
  email: string;
  nombre: string;
  avatar_url: string | null;
  role: Role;
  activo: boolean;
  modulos: ModuloPermiso[];
}

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

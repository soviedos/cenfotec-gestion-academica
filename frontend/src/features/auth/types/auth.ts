/** Auth domain types — shared across the auth feature. */

export enum Role {
  ADMIN = "admin",
  COORDINADOR = "coordinador",
  CONSULTOR = "consultor",
}

export interface User {
  id: string;
  email: string;
  nombre: string;
  avatarUrl: string | null;
  role: Role;
  activo: boolean;
}

export interface Session {
  user: User;
  accessToken: string;
  expiresAt: number;
}

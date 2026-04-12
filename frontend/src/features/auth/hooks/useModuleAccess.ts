"use client";

import { useMemo } from "react";
import { useAuth } from "./useAuth";
import type { ModuloPermiso } from "../types/auth";

export function useModuleAccess() {
  const { user } = useAuth();

  const moduleMap = useMemo(() => {
    const map = new Map<string, Set<string>>();
    if (!user) return map;
    for (const m of user.modulos) {
      map.set(m.modulo, new Set(m.permisos));
    }
    return map;
  }, [user]);

  /** Check if the user has access to a module (any permission). */
  function hasModule(modulo: string): boolean {
    return moduleMap.has(modulo);
  }

  /** Check if the user has a specific permission for a module. */
  function hasPermission(modulo: string, permission: string): boolean {
    return moduleMap.get(modulo)?.has(permission) ?? false;
  }

  /** All accessible modules with their permissions. */
  const accessibleModules: ModuloPermiso[] = user?.modulos ?? [];

  return { hasModule, hasPermission, accessibleModules };
}

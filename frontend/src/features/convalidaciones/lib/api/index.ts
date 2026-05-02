// Barrel: re-exports todos los clientes API del módulo Convalidaciones.
//
// Import individual modules for tree-shaking, or this file for convenience:
//   import { listCasos, crearCaso } from "@/features/convalidaciones/lib/api";

export * from "./dashboard";
export * from "./carreras";
export * from "./casos";
export * from "./documentos";
export * from "./analisis";
export * from "./reportes";
export * from "./auditoria";
export { buildQuery } from "@/lib/query-builder";

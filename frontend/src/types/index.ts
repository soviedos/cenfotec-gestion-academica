// =============================================
// Documento (PDF subido)
// =============================================

export type DocumentoEstado = "subido" | "procesando" | "procesado" | "error";

export interface Documento {
  id: string;
  nombre_archivo: string;
  hash_sha256: string;
  estado: DocumentoEstado;
  storage_path: string;
  error_detalle: string | null;
  created_at: string;
  updated_at: string;
}

// =============================================
// Evaluación (datos extraídos y analizados)
// =============================================

export type EvaluacionEstado =
  | "pendiente"
  | "procesando"
  | "completado"
  | "error";

export interface Evaluacion {
  id: string;
  documento_id: string;
  docente_id: string;
  periodo: string;
  materia: string | null;
  puntaje_general: number | null;
  resumen_ia: string | null;
  estado: EvaluacionEstado;
  created_at: string;
  updated_at: string;
}

// =============================================
// Docente
// =============================================

export interface Docente {
  id: string;
  nombre: string;
  facultad: string | null;
  departamento: string | null;
}

// =============================================
// API Responses
// =============================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// =============================================
// Upload
// =============================================

export interface UploadResponse {
  documento_id: string;
  nombre_archivo: string;
  estado: DocumentoEstado;
  task_id: string;
}

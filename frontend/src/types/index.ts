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
  tamano_bytes: number | null;
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
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// =============================================
// Document Filters
// =============================================

export type DocumentoSortField =
  | "created_at"
  | "updated_at"
  | "nombre_archivo"
  | "estado"
  | "tamano_bytes";

export interface DocumentoFilterParams {
  page?: number;
  page_size?: number;
  sort_by?: DocumentoSortField;
  sort_order?: "asc" | "desc";
  estado?: DocumentoEstado;
  docente?: string;
  periodo?: string;
  nombre_archivo?: string;
}

// =============================================
// Upload
// =============================================

export interface DocumentoUploadResponse {
  id: string;
  nombre_archivo: string;
  hash_sha256: string;
  estado: DocumentoEstado;
  tamano_bytes: number | null;
  created_at: string;
  updated_at: string;
}

// =============================================
// Analytics / BI Dashboard
// =============================================

export interface ResumenGeneral {
  promedio_global: number;
  total_evaluaciones: number;
  total_docentes: number;
  total_periodos: number;
}

export interface DocentePromedio {
  docente_nombre: string;
  promedio: number;
  evaluaciones_count: number;
}

export interface DimensionPromedio {
  dimension: string;
  pct_estudiante: number | null;
  pct_director: number | null;
  pct_autoeval: number | null;
  pct_promedio: number | null;
}

export interface PeriodoMetrica {
  periodo: string;
  promedio: number;
  evaluaciones_count: number;
}

export interface RankingDocente {
  posicion: number;
  docente_nombre: string;
  promedio: number;
  evaluaciones_count: number;
}

// =============================================
// Qualitative / Sentiment Analysis
// =============================================

export interface ComentarioAnalisis {
  id: string;
  evaluacion_id: string;
  fuente: string;
  asignatura: string;
  tipo: string;
  texto: string;
  tema: string;
  tema_confianza: string;
  sentimiento: string | null;
  sent_score: number | null;
  procesado_ia: boolean;
}

export interface TemaDistribucion {
  tema: string;
  count: number;
  porcentaje: number;
}

export interface SentimientoDistribucion {
  sentimiento: string;
  count: number;
  porcentaje: number;
}

export interface TipoConteo {
  tipo: string;
  count: number;
}

export interface ResumenCualitativo {
  total_comentarios: number;
  por_tipo: TipoConteo[];
  por_sentimiento: SentimientoDistribucion[];
  temas_top: TemaDistribucion[];
  sentimiento_promedio: number | null;
}

export interface PalabraFrecuencia {
  text: string;
  value: number;
}

export interface NubePalabras {
  tipo: string;
  palabras: PalabraFrecuencia[];
}

export interface FiltrosCualitativos {
  periodos: string[];
  docentes: string[];
  asignaturas: string[];
  escuelas: string[];
}

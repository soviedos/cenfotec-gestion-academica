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
  content_fingerprint: string | null;
  posible_duplicado: boolean;
  created_at: string;
  updated_at: string;
}

// =============================================
// Duplicados probables
// =============================================

export type DuplicadoEstado = "pendiente" | "confirmado" | "descartado";

export interface DuplicadoDocumentoRef {
  id: string;
  nombre_archivo: string;
}

export interface DuplicadoRead {
  id: string;
  documento_id: string;
  documento_coincidente_id: string;
  documento_coincidente: DuplicadoDocumentoRef;
  fingerprint: string;
  score: number;
  criterios: Record<string, unknown>;
  estado: DuplicadoEstado;
  notas: string | null;
  created_at: string;
  updated_at: string;
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
  posible_duplicado?: boolean;
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
  modalidad?: string;
  año: number;
  periodo_orden: number;
  promedio: number;
  evaluaciones_count: number;
}

export interface PeriodoOption {
  periodo: string;
  modalidad: string;
  año: number;
  periodo_orden: number;
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

// =============================================
// Consultas IA (Query)
// =============================================

export interface QueryFilters {
  modalidad: Modalidad;
  periodo?: string;
  docente?: string;
  asignatura?: string;
  escuela?: string;
}

export interface QueryRequest {
  question: string;
  filters: QueryFilters;
}

export interface CommentSource {
  evaluacion_id: string;
  docente: string;
  periodo: string;
  asignatura: string;
  fuente: string;
}

export interface MetricSource {
  periodo: string | null;
  docente: string | null;
}

export interface CommentEvidence {
  type: "comment";
  texto: string;
  source: CommentSource;
  relevance_score: number | null;
}

export interface MetricEvidence {
  type: "metric";
  label: string;
  value: number;
  source: MetricSource;
}

export type QueryEvidence = CommentEvidence | MetricEvidence;

export interface QueryResponseMetadata {
  model: string;
  tokens_used: number;
  latency_ms: number;
  audit_log_id: string;
}

export interface QueryResponse {
  answer: string;
  confidence: number | null;
  evidence: QueryEvidence[];
  metadata: QueryResponseMetadata;
}

export interface QueryHistoryEntry {
  question: string;
  response: QueryResponse;
  timestamp: Date;
}

// =============================================
// Modalidad [BR-MOD-01]
// =============================================

export type Modalidad = "CUATRIMESTRAL" | "MENSUAL" | "B2B";

/**
 * Includes DESCONOCIDA for edge-case handling.
 * Most UI code should use Modalidad (without DESCONOCIDA).
 */
export type ModalidadConDesconocida = Modalidad | "DESCONOCIDA";

// =============================================
// Severidad [AL-20]
// =============================================

export type Severidad = "alta" | "media" | "baja";

// =============================================
// Alert lifecycle [AL-50]
// =============================================

export type AlertaEstado = "activa" | "revisada" | "resuelta" | "descartada";

// =============================================
// Tipo de alerta [AL-20–AL-23]
// =============================================

export type TipoAlerta = "BAJO_DESEMPEÑO" | "CAIDA" | "SENTIMIENTO" | "PATRON";

// =============================================
// Sentimiento [BR-CLAS-20]
// =============================================

export type Sentimiento = "positivo" | "negativo" | "mixto" | "neutro";

// =============================================
// Tema [BR-CLAS-10]
// =============================================

export type Tema =
  | "metodologia"
  | "dominio_tema"
  | "comunicacion"
  | "evaluacion"
  | "puntualidad"
  | "material"
  | "actitud"
  | "tecnologia"
  | "organizacion"
  | "otro";

// =============================================
// Tipo de comentario [BR-CLAS-01]
// =============================================

export type TipoComentario = "fortaleza" | "mejora" | "observacion";

// =============================================
// Alertas (real alert system)
// =============================================

export interface AlertaResponse {
  id: string;
  evaluacion_id: string | null;
  docente_nombre: string;
  curso: string;
  periodo: string;
  modalidad: Modalidad;
  tipo_alerta: TipoAlerta;
  metrica_afectada: string;
  valor_actual: number;
  valor_anterior: number | null;
  descripcion: string;
  severidad: Severidad;
  estado: AlertaEstado;
  created_at: string;
  updated_at: string;
}

export interface AlertaSummary {
  total_activas: number;
  por_severidad: Partial<Record<Severidad, number>>;
  por_tipo: Partial<Record<TipoAlerta, number>>;
  por_modalidad: Partial<Record<Modalidad, number>>;
  docentes_afectados: number;
}

export interface AlertFilters {
  modalidad?: Modalidad;
  anio?: number;
  periodo?: string;
  severidad?: Severidad;
  estado?: AlertaEstado;
  docente?: string;
  curso?: string;
  tipo_alerta?: TipoAlerta;
  page?: number;
  page_size?: number;
}

// =============================================
// Executive Dashboard
// =============================================

export interface DashboardKpis {
  documentos_procesados: number;
  docentes_evaluados: number;
  promedio_general: number;
  alertas_criticas: number;
}

export interface AlertaDocente {
  docente_nombre: string;
  promedio: number;
  evaluaciones_count: number;
  motivo: string;
}

export interface DocenteResumen {
  posicion: number;
  docente_nombre: string;
  promedio: number;
  evaluaciones_count: number;
}

export interface InsightItem {
  icono: string;
  texto: string;
}

export interface ActividadReciente {
  documento_nombre: string;
  estado: string;
  evaluaciones_extraidas: number;
  fecha: string;
}

export interface DashboardSummary {
  kpis: DashboardKpis;
  alertas: AlertaDocente[];
  tendencia: PeriodoMetrica[];
  top_docentes: DocenteResumen[];
  bottom_docentes: DocenteResumen[];
  insights: InsightItem[];
  actividad_reciente: ActividadReciente[];
}

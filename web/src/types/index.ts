// ==================== Project Types ====================

export type ProjectStatus = 'processing' | 'completed' | 'failed';

export interface ProjectMetadata {
  company?: string;
  period?: string;
  document_type?: string;
  publish_date?: string;
}

export interface Project {
  project_id: string;
  title: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  metadata: ProjectMetadata | null;
}

export interface ProjectDetail extends Project {
  pipeline: PipelineState;
  artifacts: ProjectArtifacts;
}

export interface ProjectArtifacts {
  report_md?: string;
  report_html?: string;
  analysis_json?: string;
  research_json?: string;
}

// ==================== Pipeline Types ====================

export type StageStatus = 'pending' | 'in_progress' | 'completed' | 'failed';
export type StageName = 'parsing' | 'analysis' | 'research' | 'generation';

export interface StageDetails {
  [key: string]: unknown;

  // Parsing stage
  pages_extracted?: number;
  total_pages?: number;
  figures_count?: number;
  tables_count?: number;

  // Analysis stage
  sections_completed?: number;
  total_sections?: number;
  current_section?: string;
  metrics_extracted?: number;

  // Research stage
  queries_completed?: number;
  total_queries?: number;
  current_query?: string;
  results_found?: number;

  // Generation stage
  report_url?: string;
}

export interface PipelineStage {
  name: StageName;
  status: StageStatus;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  details?: StageDetails;
}

export interface PipelineState {
  current_stage: StageName | 'completed';
  stages: PipelineStage[];
}

// ==================== WebSocket Message Types ====================

export interface WSProgressMessage {
  stage: StageName;
  status: StageStatus;
  progress: number;
  message: string;
  details?: StageDetails;
  timestamp: string;
  error?: {
    code: string;
    message: string;
    details?: string;
  };
}

// ==================== PDF Highlight Types ====================

export interface BoundingRect {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface PageDimensions {
  width: number;
  height: number;
}

export interface PDFHighlight {
  page_number: number;
  bounding_rect: BoundingRect;
  rects?: BoundingRect[];
  page_dimensions: PageDimensions;
}

// ==================== Citation Types ====================

export type CitationType = 'document' | 'chart' | 'web';

export interface BaseCitation {
  type: CitationType;
  pdf_highlight?: PDFHighlight;
  pdf_url?: string;
}

export interface DocumentCitation extends BaseCitation {
  type: 'document';
  id: string;
  location: string;
  source?: string;
}

export interface ChartCitation extends BaseCitation {
  type: 'chart';
  figure_id: string;
  figure_path: string;
  figure_url: string;
  figure_analysis?: {
    type: string;
    title?: string;
    analysis?: Record<string, string>;
  };
}

export interface WebCitation extends BaseCitation {
  type: 'web';
  title?: string;
  url: string;
  content?: string;
  published_date?: string;
  relevance_score?: number;
}

export type Citation = DocumentCitation | ChartCitation | WebCitation;

// ==================== Report Types ====================

export interface ReportContent {
  content: string;
  format: 'markdown' | 'html' | 'json';
  metadata: {
    title: string;
    generated_at: string;
    model: string;
  };
}

// ==================== API Response Types ====================

export interface AnalysisResponse {
  analysis_id: string;
  document_metadata: ProjectMetadata;
  content_summary: Array<Record<string, unknown>>;
  key_takeaways: Array<Record<string, unknown>>;
  supplementary_research_needs: Record<string, unknown>;
  charts_analysis: Array<Record<string, unknown>>;
}

export interface CreateProjectResponse {
  project_id: string;
  status: ProjectStatus;
  created_at: string;
  websocket_url: string;
}

export interface ProjectListResponse {
  total: number;
  items: Project[];
}

// ==================== UI State Types ====================

export type AnalysisMode = 'minimal' | 'no-research' | 'full';

export interface UploadState {
  file: File | null;
  userQuery: string;
  mode: AnalysisMode;
  isUploading: boolean;
  uploadProgress: number;
}

export interface AppState {
  currentProject: ProjectDetail | null;
  activeCitationId: string | null;
  isSidePanelOpen: boolean;
}

// ==================== QA Types ====================

export interface QAMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  context_used?: string[];
  timestamp: string;
}

export interface QASession {
  session_id: string;
  project_dir: string;
  target_name: string;
  created_at: string;
  messages: QAMessage[];
}

export interface QASessionResponse {
  status: 'success';
  session: QASession;
}

export interface QASessionListResponse {
  status: 'success';
  sessions: QASession[];
}

export interface QASuggestionsResponse {
  status: 'success';
  suggestions: string[];
}

export interface QAAnswerResponse {
  status: 'success';
  answer: string;
  citations: string[];
  context_used: string[];
}

export interface QAStreamChunk {
  type: 'text' | 'citation' | 'done' | 'error';
  content?: string;
  citation_id?: string;
  citations?: string[];
  context_used?: string[];
  error?: string;
}

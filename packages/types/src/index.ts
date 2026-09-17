/**
 * VisualNote AI — Shared Canonical Data Contracts
 * Corresponds to PWD §6 and apps/api/app/schemas/
 */

export type SourceType = 'youtube' | 'upload' | 'audio';

export type ProjectStatus =
  | 'DRAFT'
  | 'UPLOADING'
  | 'PROCESSING'
  | 'ANALYZING'
  | 'GENERATING'
  | 'READY'
  | 'FAILED'
  | 'ARCHIVED';

export type LearningLevel = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'EXAM';

export type OutputMode = 'QUICK' | 'STANDARD' | 'DETAILED' | 'EXAM';

export type VisualStyle = 'HANDWRITTEN' | 'ACADEMIC' | 'INFOGRAPHIC';

export type ConceptType =
  | 'definition'
  | 'process'
  | 'comparison'
  | 'formula'
  | 'timeline'
  | 'relationship'
  | 'example'
  | 'list'
  | 'general';

export type VisualType =
  | 'concept_card'
  | 'flowchart'
  | 'comparison_table'
  | 'formula_block'
  | 'timeline'
  | 'concept_map'
  | 'bullet_list'
  | 'example_card';

export type JobStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type PipelineStage =
  | 'created'
  | 'extracting'
  | 'transcribing'
  | 'analyzing'
  | 'planning'
  | 'rendering'
  | 'completed'
  | 'failed';

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export interface TranscriptResponse {
  id: string;
  project_id?: string | null;
  source_id?: string | null;
  language: string;
  content: string;
  duration?: number | null;
  segments?: TranscriptSegment[] | null;
  created_at?: string | null;
}

export interface CleanedTranscriptResponse {
  raw_text: string;
  cleaned_text: string;
  word_count: number;
  estimated_duration_sec: number;
  segments: TranscriptSegment[];
}

export interface ConceptStep {
  name: string;
  description: string;
}

export interface ConceptComparison {
  entities: string[];
  aspects: Record<string, string[]>;
}

export interface ConceptFormula {
  expression: string;
  variables: Record<string, string>;
  explanation: string;
}

export interface CanonicalConcept {
  id?: string | null;
  title: string;
  concept_type: ConceptType;
  importance_score: number; // 0.0 - 1.0
  source: {
    start: number;
    end: number;
  };
  explanation: string;
  visual_type: VisualType;
  confidence?: number;
  steps?: ConceptStep[] | null;
  comparison?: ConceptComparison[] | ConceptComparison | null;
  formula?: ConceptFormula | null;
  supporting_points?: string[];
  examples?: string[];
}

export interface VisualSectionPlan {
  id: string;
  concept_id: string;
  visual_type: VisualType;
  title: string;
  priority: number;
  theme: string;
  layout: Record<string, unknown>;
  content: CanonicalConcept;
  validation_status: string;
}

export interface VisualPlanResponse {
  id: string;
  page_title: string;
  theme: string;
  sections: VisualSectionPlan[];
  created_at?: string | null;
}

export interface RenderResponse {
  page_title: string;
  image_url?: string | null;
  html_url?: string | null;
  svg_content?: string | null;
  storage_path?: string | null;
  status: string;
}

export interface PipelineRunRequest {
  raw_text?: string;
  source_id?: string;
  project_id?: string;
  theme?: string;
  learning_level?: string;
  mock_mode?: boolean;
}

export interface PipelineRunResponse {
  job_id: string;
  project_id?: string | null;
  status: string;
  current_stage: PipelineStage;
  progress: number;
  transcript?: TranscriptResponse | null;
  concepts?: CanonicalConcept[] | null;
  visual_plan?: VisualPlanResponse | null;
  render_result?: RenderResponse | null;
  error?: string | null;
}

export interface JobDetailResponse {
  id: string;
  project_id?: string | null;
  job_type: string;
  status: string;
  current_stage: PipelineStage;
  progress: number;
  error_message?: string | null;
  result_data?: Record<string, unknown> | null;
  created_at?: string | null;
  completed_at?: string | null;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  api: string;
  database: string;
  redis: string;
  version: string;
  environment: string;
}

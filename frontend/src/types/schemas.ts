/**
 * Shared TypeScript definitions matching docs/SCHEMAS.md and docs/API.md.
 */

export type BrowserAction = 'navigate' | 'click' | 'input' | 'scroll' | 'wait';

export interface GoalSchema {
  goal_id: string;
  objective: string;
  constraints: string[];
  metadata?: Record<string, any>;
}

export interface PlanStep {
  step_id: number;
  action: BrowserAction;
  url?: string | null;
  selector?: string | null;
  input_value?: string | null;
  description: string;
}

export interface BrowserResult {
  step_id: number;
  status: 'success' | 'failed' | 'timeout';
  final_url: string;
  raw_html: string;
  screenshot_path?: string | null;
  error_message?: string | null;
}

export interface ProcessedPage {
  step_id: number;
  source_domain: string;
  cleaned_markdown: string;
  entities: Record<string, any>;
}

export interface SourceCitation {
  domain: string;
  url: string;
  screenshot_path: string;
}

export interface FinalReport {
  goal_id: string;
  summary: string;
  comparison_table: Array<Record<string, any>>;
  confidence_score: number;
  contradictions: string[];
  sources: SourceCitation[];
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  services: {
    database?: string;
    playwright?: string;
    llm_api?: string;
    [key: string]: string | undefined;
  };
}

export type PipelineStage = 1 | 2 | 3 | 4 | 5;

export type ExecutionStatus = 'idle' | 'planning' | 'running' | 'completed' | 'error';

export interface StepRecord {
  step: PlanStep;
  browserResult?: BrowserResult;
  processedPage?: ProcessedPage;
  status: 'pending' | 'running' | 'success' | 'failed' | 'timeout';
  durationMs?: number;
}

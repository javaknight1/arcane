// Auth
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface UserResponse {
  id: string;
  email: string;
  created_at: string;
}

// Projects
export interface ProjectCreate {
  name: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  roadmap_count: number;
}

export interface RoadmapSummary {
  id: string;
  name: string;
  status: "draft" | "generating" | "completed";
  created_at: string;
  updated_at: string;
  item_counts: {
    milestones: number;
    epics: number;
    stories: number;
    tasks: number;
  } | null;
  completion_percent: number | null;
  hours_completed: number | null;
  hours_total: number | null;
}

export interface ProjectDetail {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  roadmaps: RoadmapSummary[];
}

// Roadmaps
export interface RoadmapCreate {
  name: string;
  context?: Record<string, unknown> | null;
}

export interface RoadmapDetail {
  id: string;
  project_id: string;
  name: string;
  status: "draft" | "generating" | "completed";
  context: Record<string, unknown> | null;
  roadmap_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// Generation
export interface GenerationJobResponse {
  id: string;
  roadmap_id: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: Record<string, unknown> | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

// Item CRUD
export interface ItemUpdate {
  name?: string;
  description?: string;
  priority?: string;
  status?: string;
  labels?: string[];
  goal?: string;
  target_date?: string;
  estimated_hours?: number;
  acceptance_criteria?: string[];
  implementation_notes?: string;
  claude_code_prompt?: string;
  prerequisites?: string[];
}

export interface ItemCreateRequest {
  item_type: string;
  data: Record<string, unknown>;
}

export interface ReorderRequest {
  parent_id: string;
  item_ids: string[];
}

export interface ItemResponse {
  item_id: string;
  item_type: string;
  data: Record<string, unknown>;
}

export interface DeleteResponse {
  deleted_id: string;
  deleted_type: string;
  children_deleted: number;
}

// AI Edit
export interface AiEditResponse {
  item_id: string;
  item_type: string;
  original: Record<string, unknown>;
  edited: Record<string, unknown>;
}

// Roadmap Stats
export interface MilestoneStats {
  id: string;
  name: string;
  status: string;
  target_date: string | null;
  is_overdue: boolean;
  total_items: number;
  completed_items: number;
  hours_total: number;
  hours_completed: number;
  epic_count: number;
  story_count: number;
  task_count: number;
}

export interface RoadmapStats {
  hours_total: number;
  hours_completed: number;
  completion_percent: number;
  milestones: MilestoneStats[];
}

// Credentials
export interface CredentialCreate {
  service: string;
  credentials: Record<string, string>;
}

export interface CredentialResponse {
  id: string;
  service: string;
  created_at: string;
}

export interface CredentialValidateResponse {
  service: string;
  valid: boolean;
  message: string;
}

// Exports
export interface ExportRequest {
  service: string;
  workspace_params?: Record<string, string>;
}

export interface ExportJobResponse {
  id: string;
  roadmap_id: string;
  service: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface CSVExportResponse {
  csv_content: string;
  filename: string;
}

// API Errors
export interface ApiError {
  detail: string;
}

// =============================================================================
// User & Auth Types
// =============================================================================
export type UserRole = "admin" | "lead_analyst" | "analyst" | "viewer";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

// =============================================================================
// Target Types
// =============================================================================
export type TargetStatus = "pending" | "scanning" | "completed" | "error";

export interface Target {
  id: number;
  name: string;
  url: string;
  description?: string;
  status: TargetStatus;
  tags?: string[];
  created_by: number;
  last_scanned_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface TargetCreate {
  name: string;
  url: string;
  description?: string;
  tags?: string[];
}

// =============================================================================
// Scan Types
// =============================================================================
export type ScanStatus =
  | "pending"
  | "queued"
  | "running"
  | "paused"
  | "cancelled"
  | "completed"
  | "error"
  | "timeout";

export type ScanType = "quick" | "full" | "custom" | "scheduled";
export type ScanIntensity = "light" | "normal" | "aggressive";
export type VulnerabilitySeverity = "critical" | "high" | "medium" | "low" | "info";
export type VulnerabilityStatus =
  | "open"
  | "in_progress"
  | "fixed"
  | "false_positive"
  | "accepted_risk";

export interface ScanConfig {
  scan_type: ScanType;
  scanners: string[];
  intensity: ScanIntensity;
}

export interface ScanLog {
  id: number;
  scan_id: number;
  level: string;
  message: string;
  scanner?: string;
  created_at: string;
}

export interface Scan {
  id: number;
  target_id: number;
  name: string;
  description?: string;
  status: ScanStatus;
  progress: number;
  config: ScanConfig;
  started_at?: string;
  completed_at?: string;
  created_by: number;
  created_at: string;
  vulnerabilities: Vulnerability[];
  logs: ScanLog[];
}

export interface ScanCreate {
  target_id: number;
  name: string;
  description?: string;
  config: ScanConfig;
  scheduled_at?: string;
}

export interface Vulnerability {
  id: number;
  scan_id: number;
  title: string;
  description: string;
  severity: VulnerabilitySeverity;
  status: VulnerabilityStatus;
  cvss_score?: number;
  cve_id?: string;
  cwe_id?: string;
  remediation?: string;
  affected_component?: string;
  evidence?: Record<string, unknown>;
  scanner_source?: string;
  created_at: string;
}

// =============================================================================
// Report Types
// =============================================================================
export type ReportStatus = "pending" | "generating" | "completed" | "error";

export interface Report {
  id: number;
  scan_id: number;
  title: string;
  description?: string;
  status: ReportStatus;
  formats: Record<string, string>;
  generated_by: number;
  created_at: string;
  completed_at?: string;
}

export interface ReportCreate {
  scan_id: number;
  title: string;
  description?: string;
  formats: string[];
  include_screenshots: boolean;
  include_remediation: boolean;
  include_evidence: boolean;
}

// =============================================================================
// Dashboard Types
// =============================================================================
export interface SeverityCount {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface DashboardStats {
  total_scans: number;
  active_scans: number;
  completed_scans: number;
  total_targets: number;
  total_vulnerabilities: number;
  severity_distribution: SeverityCount;
  scan_success_rate: number;
  avg_scan_duration?: number;
}

// =============================================================================
// WebSocket Event Types
// =============================================================================
export interface WsScanProgress {
  scan_id: number;
  status: ScanStatus;
  progress: number;
  message?: string;
}

export interface WsVulnerabilityFound {
  scan_id: number;
  vulnerability: Vulnerability;
}

export interface WsScanLog {
  scan_id: number;
  level: string;
  message: string;
  scanner?: string;
  timestamp: string;
}

// =============================================================================
// API Response Types
// =============================================================================
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

/**
 * TypeScript domain type definitions matching Sentinel backend models and schemas.
 */

export type UserRole =
  | "analyst_tier_1"
  | "analyst_tier_2"
  | "incident_responder"
  | "detection_engineer"
  | "soc_manager"
  | "admin";

export type EventSeverity = "informational" | "low" | "medium" | "high" | "critical";

export type RuleSeverity = "low" | "medium" | "high" | "critical";

export type AlertStatus =
  | "new"
  | "triaged"
  | "investigating"
  | "escalated"
  | "closed_false_positive"
  | "closed_resolved";

export type IncidentSeverity =
  | "sev_1_critical"
  | "sev_2_high"
  | "sev_3_medium"
  | "sev_4_low";

export type IncidentStatus =
  | "open"
  | "containment"
  | "eradication"
  | "recovery"
  | "post_incident_review"
  | "closed";

export interface SubsystemHealth {
  status: "healthy" | "connected" | "degraded" | "disconnected" | "unknown";
  latency_ms?: number | null;
  error?: string | null;
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  environment: string;
  version: string;
  timestamp: string;
  subsystems: Record<string, SubsystemHealth>;
}

export interface TimeSeriesPoint {
  timestamp: string;
  count: number;
}

export interface SeverityDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
  informational: number;
  [key: string]: number;
}

export interface DashboardSummary {
  events_processed: number;
  active_alerts: number;
  open_incidents: number;
  critical_alerts: number;
  event_volume_timeseries: TimeSeriesPoint[];
  severity_distribution: SeverityDistribution;
  last_updated?: string | null;
}

export interface AlertItem {
  id: string;
  rule_id: string;
  rule_name?: string | null;
  rule_code?: string | null;
  title: string;
  description: string;
  severity: RuleSeverity;
  status: AlertStatus;
  source_ip?: string | null;
  deduplication_key: string;
  event_count: number;
  context_data?: Record<string, unknown>;
  assigned_to_id?: string | null;
  incident_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentItem {
  id: string;
  incident_number: string;
  title: string;
  summary: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  lead_analyst_id?: string | null;
  lead_analyst_name?: string | null;
  containment_details?: string | null;
  lessons_learned?: string | null;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type NavView =
  | "overview"
  | "events"
  | "alerts"
  | "incidents"
  | "sources"
  | "rules"
  | "reports"
  | "settings";

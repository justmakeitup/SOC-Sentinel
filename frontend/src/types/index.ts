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
  | "investigating"
  | "containment"
  | "eradication"
  | "recovery"
  | "resolved"
  | "post_incident_review"
  | "closed";

export type NoteType =
  | "analysis"
  | "containment_action"
  | "forensic_evidence"
  | "communication"
  | "general";

export interface InvestigationNoteItem {
  id: string;
  incident_id: string;
  author_id: string;
  author_name?: string | null;
  note_type: NoteType;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentTimelineItem {
  id: string;
  timestamp: string;
  event_type: string;
  title: string;
  description?: string | null;
  actor_name?: string | null;
  metadata?: Record<string, unknown>;
}

export interface IncidentDetail extends IncidentItem {
  alerts: AlertItem[];
  notes: InvestigationNoteItem[];
  timeline: IncidentTimelineItem[];
  linked_event_count: number;
}

export interface IncidentCreatePayload {
  title: string;
  summary: string;
  severity?: IncidentSeverity;
  status?: IncidentStatus;
  incident_number?: string;
  alert_ids?: string[];
  containment_details?: string;
}

export interface IncidentUpdatePayload {
  title?: string;
  summary?: string;
  severity?: IncidentSeverity;
  status?: IncidentStatus;
  lead_analyst_id?: string;
  containment_details?: string;
  lessons_learned?: string;
}

export type LogSourceType =
  | "syslog"
  | "windows_event_log"
  | "auditd"
  | "zeek_network"
  | "suricata_nids"
  | "cloudtrail"
  | "kubernetes"
  | "application_json"
  | "custom";

export type LogSourceStatus = "active" | "degraded" | "inactive" | "error";

export type IngestionJobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "partially_failed";

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

export interface NormalizedSecurityEventItem {
  id: string;
  log_source_id: string;
  log_source_name?: string | null;
  timestamp: string;
  ingested_at: string;
  event_type: string;
  event_action: string;
  severity: EventSeverity;
  source_ip?: string | null;
  source_port?: number | null;
  destination_ip?: string | null;
  destination_port?: number | null;
  protocol?: string | null;
  user_name?: string | null;
  host_name?: string | null;
  process_name?: string | null;
  process_path?: string | null;
  command_line?: string | null;
  raw_payload: string;
  event_hash: string;
  extra_fields?: Record<string, unknown> | null;
}

export interface LogSourceItem {
  id: string;
  name: string;
  source_type: LogSourceType;
  description?: string | null;
  ip_address?: string | null;
  hostname?: string | null;
  status: LogSourceStatus;
  retention_days: number;
  config_metadata?: Record<string, unknown> | null;
  total_events: number;
  total_jobs: number;
  created_at: string;
  updated_at: string;
}

export interface RejectedRecordItem {
  line_number: number;
  reason: string;
  raw_snippet?: string | null;
}

export interface IngestionJobItem {
  id: string;
  log_source_id: string;
  status: IngestionJobStatus;
  batch_identifier?: string | null;
  events_processed: number;
  events_failed: number;
  bytes_ingested: number;
  error_message?: string | null;
  rejected_records?: RejectedRecordItem[] | null;
  started_at: string;
  completed_at?: string | null;
}

export interface IngestionUploadResponse {
  job_id: string;
  status: IngestionJobStatus;
  source_id: string;
  source_name: string;
  events_processed: number;
  events_failed: number;
  bytes_ingested: number;
  is_duplicate_batch: boolean;
  message: string;
  rejected_summary?: RejectedRecordItem[] | null;
}

export interface SupportingEventSummary {
  id: string;
  timestamp: string;
  event_type: string;
  event_action: string;
  severity: string;
  source_ip?: string | null;
  destination_ip?: string | null;
  destination_port?: number | null;
  user_name?: string | null;
}

export interface AlertDetail extends AlertItem {
  supporting_events: SupportingEventSummary[];
}

export interface DetectionRuleDetail {
  id: string;
  rule_code: string;
  name: string;
  description: string;
  severity: RuleSeverity;
  rule_type: string;
  is_active: boolean;
  time_window_seconds: number;
  threshold_count: number;
  mitre_tactic?: string | null;
  mitre_technique?: string | null;
  remediation_guidance?: string | null;
  assumptions: string[];
  limitations: string[];
  expected_false_positives: string[];
  created_at: string;
  updated_at: string;
}

export interface ReplayResponse {
  start_time: string;
  end_time: string;
  events_evaluated: number;
  alerts_generated_or_updated: number;
  errors: Array<{ rule_code: string; error: string; timestamp: string }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RuleAlertCount {
  rule_code: string;
  rule_name: string;
  severity: string;
  count: number;
}

export interface MTTRMetric {
  mean_time_to_resolve_minutes: number | null;
  mean_time_to_resolve_hours: number | null;
  resolved_incidents_count: number;
  sample_description: string;
}

export interface TopAttackerIP {
  ip: string;
  event_count: number;
  alert_count: number;
}

export interface OperationalReport {
  start_date: string;
  end_date: string;
  event_category_filter?: string | null;
  log_source_filter?: string | null;
  total_events: number;
  total_alerts: number;
  total_incidents: number;
  event_volume_timeseries: TimeSeriesPoint[];
  alerts_by_severity: Record<string, number>;
  alerts_by_rule: RuleAlertCount[];
  incidents_by_status: Record<string, number>;
  mttr_metrics: MTTRMetric;
  top_source_ips: TopAttackerIP[];
  metric_definitions: Record<string, string>;
  generated_at: string;
}

export interface ReportFilterParams {
  startDate?: string;
  endDate?: string;
  eventCategory?: string;
  logSourceId?: string;
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

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

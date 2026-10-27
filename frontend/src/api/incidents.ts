/**
 * API service for SOC incident response case management, notes, and timelines.
 */

import { apiClient } from "./client";
import {
  IncidentDetail,
  IncidentItem,
  InvestigationNoteItem,
  PaginatedResponse,
  IncidentCreatePayload,
  IncidentUpdatePayload,
  NoteType,
} from "../types";
import { IncidentQueryParams } from "./dashboard";

export type { IncidentQueryParams };

/**
 * Lists paginated incidents with status, severity, and search term filters.
 */
export async function fetchIncidents(
  params: IncidentQueryParams = {},
  demoMode: boolean = false
): Promise<PaginatedResponse<IncidentItem>> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    // Return sample demo incidents
    return {
      items: [
        {
          id: "demo-inc-1",
          incident_number: "INC-2026-0001",
          title: "Suspected Kerberos Ticket Compromise",
          summary: "Abnormal TGS requests followed by administrative credential spray.",
          severity: "sev_1_critical",
          status: "containment",
          lead_analyst_name: "Alex Vance (Responder)",
          containment_details: "Compromised host isolated from VLAN 12.",
          created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: "demo-inc-2",
          incident_number: "INC-2026-0002",
          title: "Multi-Source Port Sweep Reconnaissance",
          summary: "Probes detected against internal database subnet.",
          severity: "sev_3_medium",
          status: "investigating",
          lead_analyst_name: "Morgan Chen",
          created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total_count: 2,
      page: 1,
      page_size: 10,
      total_pages: 1,
    };
  }

  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  if (params.status && params.status.toLowerCase() !== "all") {
    query.set("status", params.status);
  }
  if (params.severity && params.severity.toLowerCase() !== "all") {
    query.set("severity", params.severity);
  }

  const queryString = query.toString();
  const endpoint = queryString ? `api/v1/incidents?${queryString}` : "api/v1/incidents";
  return apiClient<PaginatedResponse<IncidentItem>>(endpoint);
}

/**
 * Fetches full incident case file with timeline, forensic notes, and linked alerts.
 */
export async function fetchIncidentDetail(
  incidentId: string,
  demoMode: boolean = false
): Promise<IncidentDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return {
      id: incidentId,
      incident_number: "INC-2026-0001",
      title: "Suspected Kerberos Ticket Compromise",
      summary: "Abnormal TGS requests followed by administrative credential spray.",
      severity: "sev_1_critical",
      status: "containment",
      lead_analyst_name: "Alex Vance (Responder)",
      containment_details: "Compromised host isolated from VLAN 12. Ticket cache purged.",
      lessons_learned: "Mandate AES256-only Kerberos encryption types across Active Directory domain.",
      created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
      updated_at: new Date().toISOString(),
      linked_event_count: 14,
      alerts: [
        {
          id: "demo-alt-1",
          rule_id: "rule-1",
          rule_code: "SEC-AUTH-001",
          rule_name: "Repeated Failed Authentication Attempts",
          title: "Excessive Failed Logins: admin (5 attempts)",
          description: "Multiple authentication failures detected within sliding window.",
          severity: "high",
          status: "escalated",
          source_ip: "192.168.1.100",
          deduplication_key: "SEC-AUTH-001:admin:2026102712",
          event_count: 5,
          created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      notes: [
        {
          id: "note-1",
          incident_id: incidentId,
          author_id: "user-1",
          author_name: "Alex Vance",
          note_type: "containment_action",
          content: "Enacted VLAN isolation on switch port Gi0/14. Active session revoked.",
          created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
          updated_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        },
      ],
      timeline: [
        {
          id: "tl-1",
          timestamp: new Date().toISOString(),
          event_type: "audit_event",
          title: "Action: Status Transitioned",
          description: "Transitioned from OPEN to CONTAINMENT",
          actor_name: "Alex Vance",
        },
        {
          id: "tl-2",
          timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
          event_type: "investigation_note",
          title: "Note: Containment Action",
          description: "Enacted VLAN isolation on switch port Gi0/14.",
          actor_name: "Alex Vance",
        },
      ],
    };
  }

  return apiClient<IncidentDetail>(`api/v1/incidents/${incidentId}`);
}

/**
 * Creates a new incident response case, optionally promoting one or more alerts.
 */
export async function createIncident(
  payload: IncidentCreatePayload,
  demoMode: boolean = false
): Promise<IncidentDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return fetchIncidentDetail("demo-new-inc", true);
  }

  return apiClient<IncidentDetail>("api/v1/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * Updates an incident's lifecycle status, containment details, or lead analyst.
 */
export async function updateIncident(
  incidentId: string,
  payload: IncidentUpdatePayload,
  demoMode: boolean = false
): Promise<IncidentDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const current = await fetchIncidentDetail(incidentId, true);
    return { ...current, ...payload };
  }

  return apiClient<IncidentDetail>(`api/v1/incidents/${incidentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * Adds an immutable investigation note to the incident journal.
 */
export async function addInvestigationNote(
  incidentId: string,
  payload: { note_type: NoteType; content: string },
  demoMode: boolean = false
): Promise<InvestigationNoteItem> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return {
      id: "demo-note-" + Date.now(),
      incident_id: incidentId,
      author_id: "demo-user",
      author_name: "SOC Analyst",
      note_type: payload.note_type,
      content: payload.content,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }

  return apiClient<InvestigationNoteItem>(`api/v1/incidents/${incidentId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * Links additional alerts to an active incident case.
 */
export async function linkAlertsToIncident(
  incidentId: string,
  alertIds: string[],
  demoMode: boolean = false
): Promise<IncidentDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return fetchIncidentDetail(incidentId, true);
  }

  return apiClient<IncidentDetail>(`api/v1/incidents/${incidentId}/alerts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ alert_ids: alertIds }),
  });
}

/**
 * Escalates a security alert into an incident case file.
 */
export async function escalateAlertToIncident(
  alertId: string,
  payload?: { title?: string; summary?: string; existing_incident_id?: string },
  demoMode: boolean = false
): Promise<IncidentDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return fetchIncidentDetail("demo-escalated-inc", true);
  }

  return apiClient<IncidentDetail>(`api/v1/alerts/${alertId}/escalate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
}

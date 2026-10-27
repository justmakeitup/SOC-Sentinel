/**
 * API service for security alert retrieval, triage updates, and evidence inspection.
 */

import { apiClient } from "./client";
import { AlertDetail, AlertStatus } from "../types";
import { fetchAlerts as fetchDashboardAlerts, AlertQueryParams } from "./dashboard";

export { fetchDashboardAlerts as fetchAlerts };
export type { AlertQueryParams };

/**
 * Fetches comprehensive alert details with supporting events and raw evidence artifacts.
 */
export async function fetchAlertDetail(
  alertId: string,
  demoMode: boolean = false
): Promise<AlertDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return {
      id: alertId,
      rule_id: "demo-rule-id",
      rule_code: "SEC-AUTH-001",
      rule_name: "Repeated Failed Authentication Attempts",
      title: "Excessive Failed Logins: admin (5 attempts)",
      description: "Observed 5 consecutive failed authentication attempts within 300s window.",
      severity: "high",
      status: "new",
      deduplication_key: `SEC-AUTH-001:admin:198.51.100.24:${new Date().toISOString().slice(0, 13)}`,
      event_count: 5,
      source_ip: "198.51.100.24",
      context_data: {
        evidence: {
          failed_attempts: 5,
          user_name: "admin",
          source_ip: "198.51.100.24",
          threshold: 5,
          time_window_seconds: 300,
        },
        affected_entities: {
          user_name: "admin",
          source_ip: "198.51.100.24",
        },
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      supporting_events: [
        {
          id: "demo-ev-1",
          timestamp: new Date().toISOString(),
          event_type: "authentication",
          event_action: "login_failed",
          severity: "low",
          source_ip: "198.51.100.24",
          user_name: "admin",
        },
      ],
    };
  }

  return apiClient<AlertDetail>(`api/v1/alerts/${alertId}`);
}

/**
 * Updates the triage lifecycle disposition of an alert.
 */
export async function updateAlertStatus(
  alertId: string,
  status: AlertStatus,
  demoMode: boolean = false
): Promise<AlertDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return fetchAlertDetail(alertId, true);
  }

  return apiClient<AlertDetail>(`api/v1/alerts/${alertId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

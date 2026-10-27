/**
 * API client and export utilities for SOC security reporting and analytics.
 */

import { apiClient, API_BASE_URL } from "./client";
import { OperationalReport, ReportFilterParams } from "../types";

export const DEMO_OPERATIONAL_REPORT: OperationalReport = {
  start_date: new Date(Date.now() - 7 * 86400000).toISOString().split("T")[0],
  end_date: new Date().toISOString().split("T")[0],
  event_category_filter: null,
  log_source_filter: null,
  total_events: 184520,
  total_alerts: 42,
  total_incidents: 6,
  event_volume_timeseries: [
    { timestamp: "2026-10-21", count: 24500 },
    { timestamp: "2026-10-22", count: 26800 },
    { timestamp: "2026-10-23", count: 23100 },
    { timestamp: "2026-10-24", count: 28900 },
    { timestamp: "2026-10-25", count: 31200 },
    { timestamp: "2026-10-26", count: 25400 },
    { timestamp: "2026-10-27", count: 24620 },
  ],
  alerts_by_severity: {
    critical: 4,
    high: 11,
    medium: 18,
    low: 9,
    informational: 0,
  },
  alerts_by_rule: [
    {
      rule_code: "RULE-AUTH-001",
      rule_name: "Repeated Failed Login Attempts",
      severity: "medium",
      count: 18,
    },
    {
      rule_code: "RULE-SCAN-001",
      rule_name: "Multi-Port Reconnaissance Sweep",
      severity: "high",
      count: 11,
    },
    {
      rule_code: "RULE-AUTH-002",
      rule_name: "Successful Authentication Following Failures",
      severity: "critical",
      count: 4,
    },
    {
      rule_code: "RULE-AUTH-003",
      rule_name: "Unusual Authentication Deviation",
      severity: "low",
      count: 9,
    },
  ],
  incidents_by_status: {
    open: 2,
    investigating: 1,
    containment: 1,
    resolved: 1,
    closed: 1,
  },
  mttr_metrics: {
    mean_time_to_resolve_minutes: 84.5,
    mean_time_to_resolve_hours: 1.41,
    resolved_incidents_count: 2,
    sample_description: "Calculated across 2 resolved/closed cases in timeframe",
  },
  top_source_ips: [
    { ip: "198.51.100.45", event_count: 1420, alert_count: 14 },
    { ip: "203.0.113.88", event_count: 890, alert_count: 9 },
    { ip: "192.168.1.105", event_count: 650, alert_count: 7 },
    { ip: "10.0.0.84", event_count: 410, alert_count: 5 },
    { ip: "172.16.5.99", event_count: 320, alert_count: 3 },
  ],
  metric_definitions: {
    total_events: "COUNT(*) of normalized_security_events within bounded time window",
    total_alerts: "COUNT(*) of security_alerts triggered within bounded time window",
    total_incidents: "COUNT(*) of incidents created within bounded time window",
    mean_time_to_resolve:
      "AVG(updated_at - created_at) strictly for incidents with status 'resolved' or 'closed'",
    csv_formula_sanitization:
      "CWE-1236 defense: cells prefixed with [=, +, -, @, \\t, \\r] are prepended with an apostrophe",
  },
  generated_at: new Date().toISOString(),
};

/**
 * Fetches aggregated operational metrics and telemetry from the backend.
 */
export async function fetchOperationalReport(
  params: ReportFilterParams = {},
  demoMode: boolean = false
): Promise<OperationalReport> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 200));
    return {
      ...DEMO_OPERATIONAL_REPORT,
      event_category_filter: params.eventCategory || null,
      log_source_filter: params.logSourceId || null,
      start_date: params.startDate || DEMO_OPERATIONAL_REPORT.start_date,
      end_date: params.endDate || DEMO_OPERATIONAL_REPORT.end_date,
    };
  }

  const query = new URLSearchParams();
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);
  if (params.eventCategory && params.eventCategory !== "all") {
    query.set("event_category", params.eventCategory);
  }
  if (params.logSourceId && params.logSourceId !== "all") {
    query.set("log_source_id", params.logSourceId);
  }

  const queryString = query.toString();
  const endpoint = `/api/v1/reports/summary${queryString ? `?${queryString}` : ""}`;
  return apiClient<OperationalReport>(endpoint);
}

/**
 * Triggers a download of sanitized CSV export data.
 */
export async function downloadReportCsv(
  exportType: "summary" | "events" | "alerts" | "incidents",
  params: ReportFilterParams = {},
  demoMode: boolean = false
): Promise<void> {
  if (demoMode) {
    // Generate mock CSV content for client demonstration
    const mockContent =
      `# Sentinel SOC Operational Export [DEMO MODE]\n` +
      `Export_Type,${exportType}\n` +
      `Generated_At,${new Date().toISOString()}\n` +
      `Status,Demo data preview\n`;
    triggerBlobDownload(mockContent, `sentinel_${exportType}_demo.csv`, "text/csv;charset=utf-8;");
    return;
  }

  const query = new URLSearchParams();
  query.set("export_type", exportType);
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);
  if (params.eventCategory && params.eventCategory !== "all") {
    query.set("event_category", params.eventCategory);
  }
  if (params.logSourceId && params.logSourceId !== "all") {
    query.set("log_source_id", params.logSourceId);
  }

  const url = `${API_BASE_URL.replace(/\/+$/, "")}/api/v1/reports/export?${query.toString()}`;
  const response = await fetch(url, { credentials: "include" });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Export failed (${response.status}): ${errorText}`);
  }

  const blob = await response.blob();
  const filename =
    response.headers.get("Content-Disposition")?.split("filename=")[1]?.replace(/"/g, "") ||
    `sentinel_${exportType}_export.csv`;

  triggerBlobDownload(blob, filename);
}

/**
 * Triggers a download of a complete Markdown incident forensic report dossier.
 */
export async function downloadIncidentDossier(
  incidentId: string,
  demoMode: boolean = false
): Promise<void> {
  if (demoMode) {
    const mockDossier =
      `# Sentinel Incident Forensic Report [DEMO]\n\n` +
      `**Incident ID**: ${incidentId}\n` +
      `**Exported**: ${new Date().toISOString()}\n\n` +
      `## Executive Summary\n` +
      `This is a synthetic demonstration dossier.\n`;
    triggerBlobDownload(
      mockDossier,
      `incident-${incidentId}-report-demo.md`,
      "text/markdown;charset=utf-8;"
    );
    return;
  }

  const url = `${API_BASE_URL.replace(/\/+$/, "")}/api/v1/reports/incidents/${incidentId}/export`;
  const response = await fetch(url, { credentials: "include" });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Incident dossier download failed (${response.status}): ${errorText}`);
  }

  const blob = await response.blob();
  const filename =
    response.headers.get("Content-Disposition")?.split("filename=")[1]?.replace(/"/g, "") ||
    `incident-${incidentId}-report.md`;

  triggerBlobDownload(blob, filename);
}

function triggerBlobDownload(content: Blob | string, filename: string, mimeType?: string) {
  const blob = typeof content === "string" ? new Blob([content], { type: mimeType }) : content;
  const downloadUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = downloadUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(downloadUrl);
}

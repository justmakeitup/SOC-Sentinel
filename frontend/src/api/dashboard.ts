/**
 * Dashboard, alerts, and incidents API service with live backend and explicit demo mode support.
 */

import { apiClient } from "./client";
import {
  DashboardSummary,
  AlertItem,
  IncidentItem,
  PaginatedResponse,
} from "../types";
import {
  DEMO_DASHBOARD_SUMMARY,
  getDemoFilteredAlerts,
  getDemoFilteredIncidents,
} from "./demoData";

export interface AlertQueryParams {
  page?: number;
  pageSize?: number;
  severity?: string;
  status?: string;
  search?: string;
}

export interface IncidentQueryParams {
  page?: number;
  pageSize?: number;
  status?: string;
  severity?: string;
}

/**
 * Fetches aggregated operational metrics from backend or demo data source.
 */
export async function fetchDashboardSummary(
  demoMode: boolean = false
): Promise<DashboardSummary> {
  if (demoMode) {
    // Artificial small delay for realistic UX testing
    await new Promise((resolve) => setTimeout(resolve, 150));
    return DEMO_DASHBOARD_SUMMARY;
  }
  return apiClient<DashboardSummary>("api/v1/dashboard/summary");
}

/**
 * Fetches paginated security alerts with search and filter parameters.
 */
export async function fetchAlerts(
  params: AlertQueryParams = {},
  demoMode: boolean = false
): Promise<PaginatedResponse<AlertItem>> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getDemoFilteredAlerts(params);
  }

  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  if (params.severity && params.severity.toLowerCase() !== "all") {
    query.set("severity", params.severity);
  }
  if (params.status && params.status.toLowerCase() !== "all") {
    query.set("status", params.status);
  }
  if (params.search && params.search.trim()) {
    query.set("search", params.search.trim());
  }

  const queryString = query.toString();
  const endpoint = queryString ? `api/v1/alerts?${queryString}` : "api/v1/alerts";
  return apiClient<PaginatedResponse<AlertItem>>(endpoint);
}

/**
 * Fetches paginated incident cases with status filtering.
 */
export async function fetchIncidents(
  params: IncidentQueryParams = {},
  demoMode: boolean = false
): Promise<PaginatedResponse<IncidentItem>> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getDemoFilteredIncidents(params);
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

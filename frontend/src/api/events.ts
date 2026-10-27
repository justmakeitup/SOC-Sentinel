/**
 * API service for normalized security events querying.
 */

import { apiClient } from "./client";
import { NormalizedSecurityEventItem, PaginatedResponse } from "../types";
import { getDemoFilteredEvents } from "./demoData";

export interface EventQueryParams {
  page?: number;
  pageSize?: number;
  sourceId?: string;
  eventType?: string;
  severity?: string;
  startTime?: string;
  endTime?: string;
  search?: string;
}

export async function fetchEvents(
  params: EventQueryParams = {},
  demoMode: boolean = false
): Promise<PaginatedResponse<NormalizedSecurityEventItem>> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getDemoFilteredEvents(params);
  }

  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  if (params.sourceId) query.set("source_id", params.sourceId);
  if (params.eventType && params.eventType.toLowerCase() !== "all") {
    query.set("event_type", params.eventType);
  }
  if (params.severity && params.severity.toLowerCase() !== "all") {
    query.set("severity", params.severity);
  }
  if (params.startTime) query.set("start_time", params.startTime);
  if (params.endTime) query.set("end_time", params.endTime);
  if (params.search && params.search.trim()) {
    query.set("search", params.search.trim());
  }

  const queryString = query.toString();
  const endpoint = queryString ? `api/v1/events?${queryString}` : "api/v1/events";
  return apiClient<PaginatedResponse<NormalizedSecurityEventItem>>(endpoint);
}

export async function fetchEventById(
  eventId: string,
  demoMode: boolean = false
): Promise<NormalizedSecurityEventItem> {
  if (demoMode) {
    const demo = getDemoFilteredEvents({}).items.find((e) => e.id === eventId);
    if (demo) return demo;
    return getDemoFilteredEvents({}).items[0];
  }
  return apiClient<NormalizedSecurityEventItem>(`api/v1/events/${eventId}`);
}

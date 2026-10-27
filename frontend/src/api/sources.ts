/**
 * API service for log sources, ingestion jobs, and log file uploads.
 */

import { apiClient, API_BASE_URL, ApiError } from "./client";
import {
  LogSourceItem,
  IngestionJobItem,
  IngestionUploadResponse,
  PaginatedResponse,
} from "../types";
import { getDemoLogSources, getDemoIngestionJobs } from "./demoData";

export async function fetchLogSources(
  page: number = 1,
  pageSize: number = 10,
  demoMode: boolean = false
): Promise<PaginatedResponse<LogSourceItem>> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getDemoLogSources(page, pageSize);
  }
  return apiClient<PaginatedResponse<LogSourceItem>>(
    `api/v1/sources?page=${page}&page_size=${pageSize}`
  );
}

export async function createLogSource(
  sourceData: {
    name: string;
    source_type: string;
    description?: string;
    ip_address?: string;
    hostname?: string;
    retention_days?: number;
  }
): Promise<LogSourceItem> {
  return apiClient<LogSourceItem>("api/v1/sources", {
    method: "POST",
    body: JSON.stringify(sourceData),
  });
}

export async function fetchIngestionJobs(
  page: number = 1,
  pageSize: number = 10,
  sourceId?: string,
  demoMode: boolean = false
): Promise<PaginatedResponse<IngestionJobItem>> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getDemoIngestionJobs(page, pageSize);
  }
  const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (sourceId) query.set("source_id", sourceId);
  return apiClient<PaginatedResponse<IngestionJobItem>>(`api/v1/ingestion/jobs?${query.toString()}`);
}

export async function uploadLogFile(
  file: File,
  parserType: string = "auto",
  sourceId?: string,
  fieldMappingJson?: string
): Promise<IngestionUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("parser_type", parserType);
  if (sourceId) formData.append("source_id", sourceId);
  if (fieldMappingJson) formData.append("field_mapping_json", fieldMappingJson);

  const url = `${API_BASE_URL.replace(/\/+$/, "")}/api/v1/ingestion/upload`;
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }
    const message =
      typeof errorData === "object" && errorData && "detail" in errorData
        ? String((errorData as { detail: string }).detail)
        : `Upload error (${response.status}): ${response.statusText}`;
    throw new ApiError(message, response.status, errorData);
  }

  return response.json() as Promise<IngestionUploadResponse>;
}

import { apiClient } from "./client";
import { HealthResponse } from "../types";

/**
 * Fetches real-time health and readiness status from the backend.
 */
export async function fetchSystemHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>("api/v1/health");
}

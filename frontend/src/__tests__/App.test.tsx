import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { App } from "../App";
import * as healthApi from "../api/health";
import { HealthResponse } from "../types";

describe("Sentinel Frontend Shell", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders platform header and core foundation cards", async () => {
    const mockHealth: HealthResponse = {
      status: "healthy",
      environment: "test",
      version: "0.1.0",
      timestamp: "2026-10-27T12:00:00Z",
      subsystems: {
        database: { status: "healthy", latency_ms: 1.2, error: null },
        ingestion_pipeline: { status: "healthy", latency_ms: 0.4, error: null },
        detection_engine: { status: "healthy", latency_ms: 0.2, error: null },
      },
    };

    vi.spyOn(healthApi, "fetchSystemHealth").mockResolvedValue(mockHealth);

    render(<App />);

    expect(screen.getByText("Sentinel")).toBeInTheDocument();
    expect(screen.getByText("Phase 1 Foundation")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL Core")).toBeInTheDocument();
    expect(screen.getByText("Detection Engine")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("API Online")).toBeInTheDocument();
    });
  });

  it("handles backend offline error gracefully with troubleshooting guidance", async () => {
    vi.spyOn(healthApi, "fetchSystemHealth").mockRejectedValue(
      new Error("Failed to connect to Sentinel API")
    );

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Backend Unreachable/i)).toBeInTheDocument();
      expect(screen.getByText("API Offline")).toBeInTheDocument();
    });
  });
});

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { App } from "../App";
import * as healthApi from "../api/health";
import * as dashboardApi from "../api/dashboard";
import * as eventsApi from "../api/events";
import * as sourcesApi from "../api/sources";
import {
  HealthResponse,
  DashboardSummary,
  PaginatedResponse,
  AlertItem,
  IncidentItem,
  NormalizedSecurityEventItem,
  LogSourceItem,
  IngestionJobItem,
} from "../types";

const mockHealth: HealthResponse = {
  status: "healthy",
  environment: "test",
  version: "0.1.0",
  timestamp: "2026-10-27T12:00:00Z",
  subsystems: {
    database: { status: "connected", latency_ms: 1.4, error: null },
    ingestion_pipeline: { status: "healthy", latency_ms: 0.4, error: null },
    detection_engine: { status: "healthy", latency_ms: 0.2, error: null },
  },
};

const mockSummaryEmpty: DashboardSummary = {
  events_processed: 0,
  active_alerts: 0,
  open_incidents: 0,
  critical_alerts: 0,
  event_volume_timeseries: [],
  severity_distribution: {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    informational: 0,
  },
  last_updated: "2026-10-27T12:00:00Z",
};

const mockAlertsEmpty: PaginatedResponse<AlertItem> = {
  items: [],
  total_count: 0,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const mockIncidentsEmpty: PaginatedResponse<IncidentItem> = {
  items: [],
  total_count: 0,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const mockEventsEmpty: PaginatedResponse<NormalizedSecurityEventItem> = {
  items: [],
  total_count: 0,
  page: 1,
  page_size: 15,
  total_pages: 1,
};

const mockSourcesEmpty: PaginatedResponse<LogSourceItem> = {
  items: [],
  total_count: 0,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const mockJobsEmpty: PaginatedResponse<IngestionJobItem> = {
  items: [],
  total_count: 0,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

describe("Sentinel Complete Frontend SOC Dashboard & Ingestion", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(healthApi, "fetchSystemHealth").mockResolvedValue(mockHealth);
    vi.spyOn(dashboardApi, "fetchDashboardSummary").mockResolvedValue(mockSummaryEmpty);
    vi.spyOn(dashboardApi, "fetchAlerts").mockResolvedValue(mockAlertsEmpty);
    vi.spyOn(dashboardApi, "fetchIncidents").mockResolvedValue(mockIncidentsEmpty);
    vi.spyOn(eventsApi, "fetchEvents").mockResolvedValue(mockEventsEmpty);
    vi.spyOn(sourcesApi, "fetchLogSources").mockResolvedValue(mockSourcesEmpty);
    vi.spyOn(sourcesApi, "fetchIngestionJobs").mockResolvedValue(mockJobsEmpty);
  });

  it("renders the SOC dashboard shell with all 4 summary KPI cards in empty state", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Sentinel").length).toBeGreaterThan(0);
      expect(screen.getByText("Security Operations Center Overview")).toBeInTheDocument();
    });

    expect(screen.getByText("Events Processed")).toBeInTheDocument();
    expect(screen.getByText("Active Alerts")).toBeInTheDocument();
    expect(screen.getByText("Open Incidents")).toBeInTheDocument();
    expect(screen.getByText("Critical Alerts")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("No Event Telemetry Ingested")).toBeInTheDocument();
      expect(screen.getByText("No Security Alerts Matching Filters")).toBeInTheDocument();
      expect(screen.getByText("No Active Case Files")).toBeInTheDocument();
    });
  });

  it("toggles development demo mode on and off cleanly with prominent banner", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Security Operations Center Overview")).toBeInTheDocument();
    });

    const demoButton = screen.getByTitle(
      /Toggle between live backend queries and development demo mock telemetry/i
    );
    expect(demoButton).toHaveTextContent(/Demo Mode \(OFF\)/i);

    fireEvent.click(demoButton);

    await waitFor(() => {
      expect(demoButton).toHaveTextContent(/Demo Mode \(ON\)/i);
      expect(
        screen.getByText(/DEVELOPMENT DEMO TELEMETRY ACTIVE/i)
      ).toBeInTheDocument();
    });

    const disableButton = screen.getByTitle(/Switch back to live backend data/i);
    fireEvent.click(disableButton);

    await waitFor(() => {
      expect(demoButton).toHaveTextContent(/Demo Mode \(OFF\)/i);
      expect(
        screen.queryByText(/DEVELOPMENT DEMO TELEMETRY ACTIVE/i)
      ).not.toBeInTheDocument();
    });
  });

  it("allows collapsing and expanding the sidebar", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Collapse sidebar/i)).toBeInTheDocument();
    });

    const collapseButton = screen.getByLabelText(/Collapse sidebar/i);
    fireEvent.click(collapseButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/Expand sidebar/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText(/Expand sidebar/i));
    await waitFor(() => {
      expect(screen.getByLabelText(/Collapse sidebar/i)).toBeInTheDocument();
    });
  });

  it("opens the global search palette when clicking search bar or pressing shortcut", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Search telemetry, rules, or press Ctrl\+K\.\.\./i)).toBeInTheDocument();
    });

    const searchTrigger = screen.getByText(/Search telemetry, rules, or press Ctrl\+K\.\.\./i);
    fireEvent.click(searchTrigger);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/Type a module, rule mnemonic, or command\.\.\./i)
      ).toBeInTheDocument();
    });

    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => {
      expect(
        screen.queryByPlaceholderText(/Type a module, rule mnemonic, or command\.\.\./i)
      ).not.toBeInTheDocument();
    });
  });

  it("navigates to Events view and shows Import Log File action", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Events").length).toBeGreaterThan(0);
    });

    const eventsButtons = screen.getAllByText("Events");
    fireEvent.click(eventsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Normalized Security Telemetry")).toBeInTheDocument();
      expect(screen.getByText("Import Log File")).toBeInTheDocument();
    });
  });

  it("navigates to Log Sources view and displays fleet management", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Log Sources").length).toBeGreaterThan(0);
    });

    const sourcesButtons = screen.getAllByText("Log Sources");
    fireEvent.click(sourcesButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Log Sources & Ingestion Pipeline")).toBeInTheDocument();
      expect(screen.getByText("Register Sensor")).toBeInTheDocument();
      expect(screen.getByText(/Ingestion Job History & Quarantine Audit/i)).toBeInTheDocument();
    });
  });
});

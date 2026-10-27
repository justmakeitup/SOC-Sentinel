import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { App } from "../App";
import * as healthApi from "../api/health";
import * as dashboardApi from "../api/dashboard";
import * as eventsApi from "../api/events";
import * as sourcesApi from "../api/sources";
import * as rulesApi from "../api/rules";
import * as alertsApi from "../api/alerts";
import * as incidentsApi from "../api/incidents";
import * as reportsApi from "../api/reports";
import {
  HealthResponse,
  DashboardSummary,
  PaginatedResponse,
  AlertItem,
  IncidentItem,
  NormalizedSecurityEventItem,
  LogSourceItem,
  IngestionJobItem,
  OperationalReport,
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

const mockReportSample: OperationalReport = {
  start_date: "2026-10-20",
  end_date: "2026-10-27",
  event_category_filter: null,
  log_source_filter: null,
  total_events: 184520,
  total_alerts: 42,
  total_incidents: 6,
  event_volume_timeseries: [
    { timestamp: "2026-10-21", count: 24500 },
    { timestamp: "2026-10-22", count: 26800 },
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
  ],
  incidents_by_status: {
    open: 2,
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
  ],
  metric_definitions: {
    total_events: "COUNT(*) of normalized_security_events",
  },
  generated_at: "2026-10-27T12:00:00Z",
};

describe("Sentinel Complete Frontend SOC Dashboard & Ingestion", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(reportsApi, "fetchOperationalReport").mockResolvedValue(mockReportSample);
    vi.spyOn(reportsApi, "downloadReportCsv").mockResolvedValue(undefined);
    vi.spyOn(healthApi, "fetchSystemHealth").mockResolvedValue(mockHealth);
    vi.spyOn(dashboardApi, "fetchDashboardSummary").mockResolvedValue(mockSummaryEmpty);
    vi.spyOn(dashboardApi, "fetchAlerts").mockResolvedValue(mockAlertsEmpty);
    vi.spyOn(dashboardApi, "fetchIncidents").mockResolvedValue(mockIncidentsEmpty);
    vi.spyOn(eventsApi, "fetchEvents").mockResolvedValue(mockEventsEmpty);
    vi.spyOn(sourcesApi, "fetchLogSources").mockResolvedValue(mockSourcesEmpty);
    vi.spyOn(sourcesApi, "fetchIngestionJobs").mockResolvedValue(mockJobsEmpty);
    vi.spyOn(rulesApi, "fetchDetectionRules").mockResolvedValue(rulesApi.DEMO_RULES);
    vi.spyOn(alertsApi, "fetchAlertDetail").mockResolvedValue({
      id: "alert-1",
      rule_id: "rule-1",
      rule_code: "SEC-AUTH-001",
      rule_name: "Repeated Failed Authentication Attempts",
      title: "Excessive Failed Logins: admin",
      description: "Observed 5 failed authentication attempts within 300s window.",
      severity: "high",
      status: "new",
      deduplication_key: "SEC-AUTH-001:admin:2026102712",
      event_count: 5,
      source_ip: "192.168.1.100",
      context_data: {
        evidence: { failed_attempts: 5 },
        affected_entities: { user_name: "admin", source_ip: "192.168.1.100" },
      },
      created_at: "2026-10-27T12:00:00Z",
      updated_at: "2026-10-27T12:00:00Z",
      supporting_events: [],
    });
    vi.spyOn(incidentsApi, "fetchIncidentDetail").mockResolvedValue({
      id: "inc-1",
      incident_number: "INC-2026-0001",
      title: "Active Data Exfiltration Investigation",
      summary: "Unauthorized large volume outbound transfer detected.",
      severity: "sev_1_critical",
      status: "containment",
      lead_analyst_name: "Alex Vance",
      containment_details: "Firewall egress rule 882 enabled.",
      lessons_learned: null,
      created_at: "2026-10-27T12:00:00Z",
      updated_at: "2026-10-27T12:30:00Z",
      linked_event_count: 8,
      alerts: [],
      notes: [],
      timeline: [
        {
          id: "time-1",
          timestamp: "2026-10-27T12:00:00Z",
          event_type: "case_created",
          title: "Incident Declared: INC-2026-0001",
          description: "Severity sev_1_critical case opened.",
          actor_name: "Alex Vance",
        },
      ],
    });
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

  it("navigates to Detection Rules view and renders the rule catalog with MITRE mapping", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Detection Rules").length).toBeGreaterThan(0);
    });

    const rulesButtons = screen.getAllByText("Detection Rules");
    fireEvent.click(rulesButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Detection Rules Catalog")).toBeInTheDocument();
      expect(screen.getByText(/MITRE ATT&CK Mapped/i)).toBeInTheDocument();
      expect(screen.getByText("SEC-AUTH-001")).toBeInTheDocument();
      expect(screen.getByText("Evaluate Recent Telemetry")).toBeInTheDocument();
    });
  });

  it("opens alert triage inspection modal when selecting an alert from queue", async () => {
    const mockAlertsPopulated: PaginatedResponse<AlertItem> = {
      items: [
        {
          id: "alert-1",
          rule_id: "rule-1",
          rule_code: "SEC-AUTH-001",
          rule_name: "Repeated Failed Authentication Attempts",
          title: "Excessive Failed Logins: admin",
          description: "Observed 5 failed authentication attempts within 300s window.",
          severity: "high",
          status: "new",
          source_ip: "192.168.1.100",
          deduplication_key: "SEC-AUTH-001:admin:2026102712",
          event_count: 5,
          created_at: "2026-10-27T12:00:00Z",
          updated_at: "2026-10-27T12:00:00Z",
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    };
    vi.spyOn(dashboardApi, "fetchAlerts").mockResolvedValue(mockAlertsPopulated);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Excessive Failed Logins: admin")).toBeInTheDocument();
    });

    // Click on alert row to open triage modal
    fireEvent.click(screen.getByText("Excessive Failed Logins: admin"));

    await waitFor(() => {
      expect(screen.getByText("Triage Disposition:")).toBeInTheDocument();
      expect(screen.getByText("Detection Rationale")).toBeInTheDocument();
    });
  });

  it("navigates to Incidents view and opens Declare Incident modal when button clicked", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Incidents").length).toBeGreaterThan(0);
    });

    const incidentsNavButtons = screen.getAllByText("Incidents");
    fireEvent.click(incidentsNavButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Declare Incident")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Declare Incident"));

    await waitFor(() => {
      expect(screen.getByText("Declare Security Incident Case")).toBeInTheDocument();
      expect(screen.getByText("NIST SP 800-61 Rev 2 Formal Investigation Dossier")).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Provide context regarding the attack vector/i)).toBeInTheDocument();
    });
  });

  it("opens Incident Case Detail Dossier modal when an incident row is clicked", async () => {
    const mockIncidentsPopulated: PaginatedResponse<IncidentItem> = {
      items: [
        {
          id: "inc-1",
          incident_number: "INC-2026-0001",
          title: "Active Data Exfiltration Investigation",
          summary: "Unauthorized large volume outbound transfer detected.",
          severity: "sev_1_critical",
          status: "containment",
          lead_analyst_name: "Alex Vance",
          containment_details: "Firewall egress rule 882 enabled.",
          created_at: "2026-10-27T12:00:00Z",
          updated_at: "2026-10-27T12:30:00Z",
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    };
    vi.spyOn(dashboardApi, "fetchIncidents").mockResolvedValue(mockIncidentsPopulated);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Active Data Exfiltration Investigation")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Active Data Exfiltration Investigation"));

    await waitFor(() => {
      expect(screen.getAllByText("INC-2026-0001").length).toBeGreaterThan(1);
      expect(screen.getByText("Executive Incident Summary")).toBeInTheDocument();
      expect(screen.getByText(/Chronological Case Activity & Audit History/i)).toBeInTheDocument();
      expect(screen.getByText("Incident Declared: INC-2026-0001")).toBeInTheDocument();
    });
  });

  it("navigates to Reports view, displays telemetry metrics, and toggles calculation rules", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText("Reports").length).toBeGreaterThan(0);
    });

    const reportsNavButtons = screen.getAllByText("Reports");
    fireEvent.click(reportsNavButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Operational Reports & Analytics")).toBeInTheDocument();
      expect(screen.getByText("Events Processed")).toBeInTheDocument();
      expect(screen.getByText("184,520")).toBeInTheDocument();
      expect(screen.getByText("Mean Time to Resolution")).toBeInTheDocument();
      expect(screen.getByText("1.4")).toBeInTheDocument();
      expect(screen.getByText("Detection Rule Attribution")).toBeInTheDocument();
      expect(screen.getByText("RULE-AUTH-001")).toBeInTheDocument();
      expect(screen.getByText("Top Source IPs (Observed Threats)")).toBeInTheDocument();
      expect(screen.getByText("198.51.100.45")).toBeInTheDocument();
    });

    // Test toggle of Methodology Panel
    expect(screen.queryByText(/CWE-1236 Formula Injection Defense/i)).not.toBeInTheDocument();
    const rulesBtn = screen.getByText("Calculation Rules");
    fireEvent.click(rulesBtn);

    await waitFor(() => {
      expect(screen.getByText(/CWE-1236 Formula Injection Defense/i)).toBeInTheDocument();
    });

    // Test Export trigger
    const exportSummaryBtn = screen.getByText("Summary");
    fireEvent.click(exportSummaryBtn);

    await waitFor(() => {
      expect(reportsApi.downloadReportCsv).toHaveBeenCalledWith(
        "summary",
        expect.any(Object),
        false
      );
    });
  });
});

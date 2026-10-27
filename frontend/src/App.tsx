import React, { useState, useEffect, useCallback } from "react";
import { Shell } from "./components/layout/Shell";
import { SummaryCard } from "./components/dashboard/SummaryCard";
import { EventVolumeChart } from "./components/dashboard/EventVolumeChart";
import { SeverityDistributionChart } from "./components/dashboard/SeverityDistributionChart";
import { AlertsTable } from "./components/dashboard/AlertsTable";
import { IncidentActivityPanel } from "./components/dashboard/IncidentActivityPanel";
import { GenericModuleView } from "./components/views/GenericModuleView";
import { fetchSystemHealth } from "./api/health";
import {
  fetchDashboardSummary,
  fetchAlerts,
  fetchIncidents,
  AlertQueryParams,
} from "./api/dashboard";
import {
  HealthResponse,
  DashboardSummary,
  AlertItem,
  IncidentItem,
  PaginatedResponse,
  NavView,
} from "./types";
import {
  Activity,
  ShieldAlert,
  FolderGit2,
  AlertOctagon,
  Layers,
  Radio,
  FileCode,
  FileSpreadsheet,
  Settings,
  RefreshCw,
} from "lucide-react";

export const App: React.FC = () => {
  // Navigation & Mode
  const [currentView, setCurrentView] = useState<NavView>("overview");
  const [demoMode, setDemoMode] = useState<boolean>(false);

  // Subsystem Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Operational Metrics
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Alerts Queue
  const [alertsResponse, setAlertsResponse] =
    useState<PaginatedResponse<AlertItem> | null>(null);
  const [alertsLoading, setAlertsLoading] = useState<boolean>(true);
  const [alertsError, setAlertsError] = useState<string | null>(null);
  const [alertFilters, setAlertFilters] = useState<AlertQueryParams>({
    page: 1,
    pageSize: 10,
    severity: "all",
    status: "all",
    search: "",
  });

  // Incidents Case Files
  const [incidentsResponse, setIncidentsResponse] =
    useState<PaginatedResponse<IncidentItem> | null>(null);
  const [incidentsLoading, setIncidentsLoading] = useState<boolean>(true);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);
  const [incidentStatusFilter, setIncidentStatusFilter] = useState<string>("all");

  // Selected entities for inspection modal or details
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);

  // 1. Health check
  const loadHealth = useCallback(async () => {
    try {
      const data = await fetchSystemHealth();
      setHealth(data);
      setHealthError(null);
    } catch (err) {
      setHealthError(err instanceof Error ? err.message : "API offline");
      setHealth(null);
    }
  }, []);

  // 2. Dashboard summary
  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const data = await fetchDashboardSummary(demoMode);
      setSummary(data);
    } catch (err) {
      setSummaryError(err instanceof Error ? err.message : "Failed to load summary");
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, [demoMode]);

  // 3. Alerts queue
  const loadAlerts = useCallback(async () => {
    setAlertsLoading(true);
    setAlertsError(null);
    try {
      const data = await fetchAlerts(alertFilters, demoMode);
      setAlertsResponse(data);
    } catch (err) {
      setAlertsError(err instanceof Error ? err.message : "Failed to load alerts");
      setAlertsResponse(null);
    } finally {
      setAlertsLoading(false);
    }
  }, [alertFilters, demoMode]);

  // 4. Incidents case list
  const loadIncidents = useCallback(async () => {
    setIncidentsLoading(true);
    setIncidentsError(null);
    try {
      const data = await fetchIncidents({ status: incidentStatusFilter }, demoMode);
      setIncidentsResponse(data);
    } catch (err) {
      setIncidentsError(err instanceof Error ? err.message : "Failed to load incidents");
      setIncidentsResponse(null);
    } finally {
      setIncidentsLoading(false);
    }
  }, [incidentStatusFilter, demoMode]);

  // Initial and reactive data loading
  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  const handleRefreshAll = () => {
    loadHealth();
    loadSummary();
    loadAlerts();
    loadIncidents();
  };

  const handleToggleDemoMode = () => {
    setDemoMode((prev) => !prev);
  };

  const backendOnline = !!health && !healthError;
  const dbLatency = health?.subsystems?.database?.latency_ms;

  return (
    <Shell
      backendOnline={backendOnline}
      environment={health?.environment || "connecting..."}
      latencyMs={dbLatency}
      demoMode={demoMode}
      onToggleDemoMode={handleToggleDemoMode}
      currentView={currentView}
      onNavigate={setCurrentView}
    >
      {/* View 1: Overview Dashboard */}
      {currentView === "overview" && (
        <div className="space-y-6">
          {/* Executive Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1E293B]">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-100">
                  Security Operations Center Overview
                </h1>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                  Live Telemetry
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Continuous event correlation, alert triage queue, and active incident response.
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={handleRefreshAll}
                disabled={summaryLoading || alertsLoading}
                className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono font-medium bg-[#121820] text-slate-200 border border-[#1E293B] hover:border-teal-700 hover:text-teal-300 transition-colors disabled:opacity-50"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 ${
                    summaryLoading || alertsLoading ? "animate-spin text-teal-400" : ""
                  }`}
                />
                <span>Refresh Live State</span>
              </button>
            </div>
          </div>

          {/* Error Banner if Summary Query Failed */}
          {summaryError && (
            <div className="p-3 rounded bg-rose-950/60 border border-rose-800 text-rose-200 text-xs font-mono flex items-center justify-between">
              <span>Failed to sync operational counters: {summaryError}</span>
              <button
                onClick={loadSummary}
                className="px-2 py-1 bg-rose-900 rounded text-rose-100 hover:bg-rose-800"
              >
                Retry
              </button>
            </div>
          )}

          {/* Top 4 KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              title="Events Processed"
              value={summary?.events_processed ?? 0}
              subtext="Total telemetry events indexed"
              icon={Activity}
              variant="teal"
              loading={summaryLoading}
            />
            <SummaryCard
              title="Active Alerts"
              value={summary?.active_alerts ?? 0}
              subtext="Requiring Tier-1 analyst triage"
              icon={ShieldAlert}
              variant="warning"
              loading={summaryLoading}
            />
            <SummaryCard
              title="Open Incidents"
              value={summary?.open_incidents ?? 0}
              subtext="Under active containment"
              icon={FolderGit2}
              variant="default"
              loading={summaryLoading}
            />
            <SummaryCard
              title="Critical Alerts"
              value={summary?.critical_alerts ?? 0}
              subtext="Immediate escalation SLA"
              icon={AlertOctagon}
              variant="critical"
              loading={summaryLoading}
            />
          </div>

          {/* Middle Row: Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <EventVolumeChart
                data={summary?.event_volume_timeseries || []}
                loading={summaryLoading}
                onEnableDemo={() => setDemoMode(true)}
              />
            </div>
            <div>
              <SeverityDistributionChart
                distribution={
                  summary?.severity_distribution || {
                    critical: 0,
                    high: 0,
                    medium: 0,
                    low: 0,
                    informational: 0,
                  }
                }
                loading={summaryLoading}
              />
            </div>
          </div>

          {/* Bottom Row: Alerts Table + Incident Activity Panel */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <AlertsTable
                alertsResponse={alertsResponse}
                loading={alertsLoading}
                error={alertsError}
                onRefresh={loadAlerts}
                onFilterChange={(newFilters) =>
                  setAlertFilters((prev) => ({ ...prev, ...newFilters }))
                }
                onSelectAlert={setSelectedAlert}
                onEnableDemo={() => setDemoMode(true)}
              />
            </div>
            <div>
              <IncidentActivityPanel
                incidentsResponse={incidentsResponse}
                loading={incidentsLoading}
                error={incidentsError}
                onRefresh={loadIncidents}
                onFilterChange={setIncidentStatusFilter}
                onSelectIncident={setSelectedIncident}
                onEnableDemo={() => setDemoMode(true)}
              />
            </div>
          </div>
        </div>
      )}

      {/* View 2: Alerts Dedicated View */}
      {currentView === "alerts" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#1E293B]">
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-100">
                Security Alerts Queue
              </h1>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Full triage workspace for alerts generated by detection rule correlation.
              </p>
            </div>
          </div>
          <AlertsTable
            alertsResponse={alertsResponse}
            loading={alertsLoading}
            error={alertsError}
            onRefresh={loadAlerts}
            onFilterChange={(newFilters) =>
              setAlertFilters((prev) => ({ ...prev, ...newFilters }))
            }
            onSelectAlert={setSelectedAlert}
            onEnableDemo={() => setDemoMode(true)}
          />
        </div>
      )}

      {/* View 3: Incidents Dedicated View */}
      {currentView === "incidents" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#1E293B]">
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-100">
                Incident Response Cases
              </h1>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Case file management following NIST SP 800-61 Rev 2 guidelines.
              </p>
            </div>
          </div>
          <IncidentActivityPanel
            incidentsResponse={incidentsResponse}
            loading={incidentsLoading}
            error={incidentsError}
            onRefresh={loadIncidents}
            onFilterChange={setIncidentStatusFilter}
            onSelectIncident={setSelectedIncident}
            onEnableDemo={() => setDemoMode(true)}
          />
        </div>
      )}

      {/* View 4: Events Telemetry View */}
      {currentView === "events" && (
        <GenericModuleView
          title="Normalized Security Events"
          subtitle="Unified ECS telemetry schema with cryptographic SHA-256 deduplication"
          icon={Layers}
          badge="Telemetry Schema"
          description="Security telemetry emitted by Syslog collectors, Windows Event Forwarders, Zeek sensors, and CloudTrail is harmonized into an Elastic Common Schema (ECS) representation. Every event is verified against an immutable SHA-256 hash preventing duplicate processing."
          architectureDetails={[
            { label: "Taxonomy", value: "ECS / OSSEM Standard" },
            { label: "Deduplication", value: "SHA-256 event_hash (Indexed)" },
            { label: "Index Strategy", value: "Compound (source_id, timestamp)" },
            { label: "Forensic Payload", value: "Preserved in raw_payload column" },
          ]}
          onBackToOverview={() => setCurrentView("overview")}
          demoMode={demoMode}
        />
      )}

      {/* View 5: Log Sources View */}
      {currentView === "sources" && (
        <GenericModuleView
          title="Log Sources & Collectors"
          subtitle="Sensor fleet registration, ingestion jobs, and parser health"
          icon={Radio}
          badge="Ingestion Subsystem"
          description="Register and manage network collectors (Syslog, Windows Event Forwarding, Suricata NIDS, Zeek). Each ingestion job tracks processed events, failed logs, byte volumes, and batch fingerprint identifiers to guarantee idempotency."
          architectureDetails={[
            { label: "Supported Types", value: "Syslog, WinEvent, Zeek, Suricata, Custom" },
            { label: "Batch Protection", value: "batch_identifier fingerprinting" },
            { label: "Retention Policy", value: "Configurable per source (default 90d)" },
            { label: "Parser Pipeline", value: "FastAPI Streaming & Ingestion Engine" },
          ]}
          onBackToOverview={() => setCurrentView("overview")}
          demoMode={demoMode}
        />
      )}

      {/* View 6: Detection Rules View */}
      {currentView === "rules" && (
        <GenericModuleView
          title="Detection Engineering"
          subtitle="MITRE ATT&CK mapped correlation rules and sliding threshold evaluations"
          icon={FileCode}
          badge="Detection Engine"
          description="Author, tune, and test detection rules against streaming and batch event telemetry. Supports threshold counts, sliding time windows, and correlation criteria with runbook remediation guidance for Tier-1 analysts."
          architectureDetails={[
            { label: "Framework", value: "MITRE Enterprise ATT&CK" },
            { label: "Execution Models", value: "Threshold, SQL Match, Behavioral" },
            { label: "Storm Protection", value: "deduplication_key hourly buckets" },
            { label: "Change Control", value: "Versioned rule tracking with audit logs" },
          ]}
          onBackToOverview={() => setCurrentView("overview")}
          demoMode={demoMode}
        />
      )}

      {/* View 7: Reports View */}
      {currentView === "reports" && (
        <GenericModuleView
          title="SOC Compliance & Executive Reports"
          subtitle="Scheduled summaries, MTTR metrics, and regulatory audit exports"
          icon={FileSpreadsheet}
          badge="Governance"
          description="Generate SOC 2, ISO 27001, and NIST CSF compliance reports detailing mean time to triage (MTTT), mean time to contain (MTTC), false-positive ratios, and audit logs of analyst operations."
          architectureDetails={[
            { label: "Audit Standard", value: "SOC 2 Type II / ISO 27001" },
            { label: "Metrics Tracked", value: "MTTD, MTTR, False Positive Rate" },
            { label: "Export Formats", value: "JSON, CSV, Structured PDF" },
            { label: "Non-Repudiation", value: "audit_events immutable ledger" },
          ]}
          onBackToOverview={() => setCurrentView("overview")}
          demoMode={demoMode}
        />
      )}

      {/* View 8: Settings View */}
      {currentView === "settings" && (
        <GenericModuleView
          title="Platform Configuration"
          subtitle="Database pooling, API base routes, CORS origins, and RBAC tiers"
          icon={Settings}
          badge="System State"
          description="Inspect active environment configuration, database connection pooling parameters, API prefixes, and role-based access control policies. Settings are loaded via Pydantic BaseSettings from .env and system variables."
          architectureDetails={[
            { label: "Environment", value: health?.environment || "development" },
            { label: "API Base URL", value: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000" },
            { label: "Database Pooling", value: "pool_size=10, max_overflow=20" },
            { label: "Platform Version", value: "v0.1.0" },
          ]}
          onBackToOverview={() => setCurrentView("overview")}
          demoMode={demoMode}
        />
      )}

      {/* Alert Triage Quick Drawer/Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121820] border border-[#1E293B] rounded-lg max-w-lg w-full p-5 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-teal-400" />
                <span className="text-xs font-bold text-slate-100 uppercase">
                  Alert Triage Detail
                </span>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-xs text-slate-400 hover:text-slate-200"
              >
                [Close]
              </button>
            </div>
            <div className="space-y-2 text-xs">
              <div className="text-sm font-semibold text-slate-200">{selectedAlert.title}</div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {selectedAlert.description}
              </p>
              <div className="pt-2 border-t border-[#1E293B] space-y-1 text-[11px] text-slate-300">
                <div>RULE: <span className="text-teal-400">{selectedAlert.rule_code}</span></div>
                <div>SOURCE ENTITY: <span className="text-slate-200">{selectedAlert.source_ip || "N/A"}</span></div>
                <div>DEDUP KEY: <span className="text-slate-400 text-[10px] break-all">{selectedAlert.deduplication_key}</span></div>
                <div>EVENT COUNT: <span className="text-teal-300 font-bold">{selectedAlert.event_count}</span></div>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-3 py-1.5 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                Dismiss Triage
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Incident Case Detail Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121820] border border-[#1E293B] rounded-lg max-w-lg w-full p-5 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
              <div className="flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-teal-400" />
                <span className="text-xs font-bold text-slate-100 uppercase">
                  Incident Case File: {selectedIncident.incident_number}
                </span>
              </div>
              <button
                onClick={() => setSelectedIncident(null)}
                className="text-xs text-slate-400 hover:text-slate-200"
              >
                [Close]
              </button>
            </div>
            <div className="space-y-2 text-xs">
              <div className="text-sm font-semibold text-slate-200">{selectedIncident.title}</div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {selectedIncident.summary}
              </p>
              {selectedIncident.containment_details && (
                <div className="p-2.5 rounded bg-[#0B0F14] border border-[#1E293B] space-y-1">
                  <div className="text-[10px] text-amber-400 font-bold uppercase">Containment Measures Taken:</div>
                  <div className="text-[11px] text-slate-300 leading-relaxed">
                    {selectedIncident.containment_details}
                  </div>
                </div>
              )}
              <div className="pt-2 border-t border-[#1E293B] space-y-1 text-[11px] text-slate-300">
                <div>LEAD ANALYST: <span className="text-teal-400">{selectedIncident.lead_analyst_name || "Unassigned"}</span></div>
                <div>LIFECYCLE STATUS: <span className="text-slate-200 uppercase">{selectedIncident.status}</span></div>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedIncident(null)}
                className="px-3 py-1.5 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                Close Case Review
              </button>
            </div>
          </div>
        </div>
      )}
    </Shell>
  );
};

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Shell } from "./components/layout/Shell";
import { SummaryCard } from "./components/dashboard/SummaryCard";
import { EventVolumeChart } from "./components/dashboard/EventVolumeChart";
import { SeverityDistributionChart } from "./components/dashboard/SeverityDistributionChart";
import { AlertsTable } from "./components/dashboard/AlertsTable";
import { IncidentActivityPanel } from "./components/dashboard/IncidentActivityPanel";
import { AlertInspectionModal } from "./components/dashboard/AlertInspectionModal";
import { IncidentDetailModal } from "./components/incidents/IncidentDetailModal";
import { CreateIncidentModal } from "./components/incidents/CreateIncidentModal";
import { GenericModuleView } from "./components/views/GenericModuleView";
import { EventsView } from "./components/views/EventsView";
import { LogSourcesView } from "./components/views/LogSourcesView";
import { DetectionRulesView } from "./components/views/DetectionRulesView";
import { ReportsView } from "./components/views/ReportsView";
import { API_BASE_URL } from "./api/client";
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
  Settings,
  RefreshCw,
  Plus,
} from "lucide-react";

export const App: React.FC = () => {
  // Navigation & Mode
  const [currentView, setCurrentView] = useState<NavView>("overview");
  const [demoMode, setDemoMode] = useState<boolean>(false);
  const [isCreateIncidentOpen, setIsCreateIncidentOpen] = useState<boolean>(false);

  // Subsystem Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const initialCheckDone = useRef<boolean>(false);

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
      // Auto-enable demo mode on first check if backend is unavailable (e.g. static portfolio hosting)
      if (!initialCheckDone.current) {
        setDemoMode(true);
      }
    } finally {
      initialCheckDone.current = true;
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

          {/* Backend Connectivity Failure Notice */}
          {healthError && !demoMode && (
            <div className="p-3.5 rounded bg-amber-950/70 border border-amber-800/80 text-amber-200 text-xs font-mono flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <AlertOctagon className="w-4 h-4 text-amber-400 shrink-0" />
                <span>
                  Backend API is unreachable (<span className="text-amber-300 font-semibold">{healthError}</span>).
                  Verify FastAPI is running on <code className="text-amber-300 bg-black/40 px-1 py-0.5 rounded">{API_BASE_URL}</code> or explore with demonstration telemetry.
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => setDemoMode(true)}
                  className="px-2.5 py-1 bg-amber-900/80 hover:bg-amber-800 text-amber-100 rounded text-[11px] font-semibold transition-colors"
                >
                  Enable Demo Mode
                </button>
                <button
                  onClick={loadHealth}
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] border border-slate-700 transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {/* Standalone Cloud Preview Notice */}
          {healthError && demoMode && (
            <div className="p-2.5 rounded bg-cyan-950/40 border border-cyan-800/60 text-cyan-200 text-xs font-mono flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shrink-0" />
                <span>
                  <strong className="text-cyan-300">Standalone Web Demo Active:</strong> Interactive telemetry loaded. To connect real-time database queries, run the local FastAPI service.
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={loadHealth}
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] border border-slate-700 transition-colors"
                >
                  Check Live Backend
                </button>
              </div>
            </div>
          )}

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
            <button
              onClick={() => setIsCreateIncidentOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold text-xs font-mono transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Declare Incident
            </button>
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
        <EventsView demoMode={demoMode} onEnableDemo={() => setDemoMode(true)} />
      )}

      {/* View 5: Log Sources View */}
      {currentView === "sources" && (
        <LogSourcesView demoMode={demoMode} onEnableDemo={() => setDemoMode(true)} />
      )}

      {/* View 6: Detection Rules View */}
      {currentView === "rules" && (
        <DetectionRulesView
          demoMode={demoMode}
          onEnableDemo={() => setDemoMode(true)}
          onAlertsTriggered={() => {
            loadAlerts();
            loadSummary();
          }}
        />
      )}

      {/* View 7: Reports View */}
      {currentView === "reports" && (
        <ReportsView
          demoMode={demoMode}
          onEnableDemo={() => setDemoMode(true)}
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

      {/* Alert Triage Inspection & Forensic Evidence Modal */}
      {selectedAlert && (
        <AlertInspectionModal
          alert={selectedAlert}
          demoMode={demoMode}
          onClose={() => setSelectedAlert(null)}
          onStatusUpdated={() => {
            loadAlerts();
            loadSummary();
          }}
          onEscalated={(incidentId) => {
            setSelectedAlert(null);
            loadAlerts();
            loadIncidents();
            loadSummary();
            setSelectedIncident({ id: incidentId } as any);
          }}
        />
      )}

      {/* Incident Case Detail Dossier Modal */}
      {selectedIncident && (
        <IncidentDetailModal
          incident={selectedIncident}
          demoMode={demoMode}
          onClose={() => setSelectedIncident(null)}
          onIncidentUpdated={() => {
            loadIncidents();
            loadSummary();
          }}
          onInspectAlert={(alertId) => {
            setSelectedIncident(null);
            setSelectedAlert({ id: alertId } as any);
          }}
        />
      )}

      {/* Create Incident Case Modal */}
      {isCreateIncidentOpen && (
        <CreateIncidentModal
          demoMode={demoMode}
          onClose={() => setIsCreateIncidentOpen(false)}
          onCreated={(newInc) => {
            setIsCreateIncidentOpen(false);
            loadIncidents();
            loadSummary();
            setSelectedIncident(newInc);
          }}
        />
      )}
    </Shell>
  );
};

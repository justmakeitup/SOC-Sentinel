import React, { useState, useEffect, useCallback } from "react";
import {
  FileSpreadsheet,
  Download,
  Calendar,
  Filter,
  RefreshCw,
  Clock,
  ShieldAlert,
  Activity,
  AlertTriangle,
  Layers,
  Info,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react";
import {
  fetchOperationalReport,
  downloadReportCsv,
} from "../../api/reports";
import { OperationalReport, TimeSeriesPoint } from "../../types";
import { SeverityBadge } from "../common/SeverityBadge";

interface ReportsViewProps {
  demoMode: boolean;
  onEnableDemo?: () => void;
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  demoMode,
  onEnableDemo,
}) => {
  // Preset or custom date range state
  const [datePreset, setDatePreset] = useState<"24h" | "7d" | "30d" | "custom">("7d");
  const [startDate, setStartDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState<string>(() => {
    return new Date().toISOString().split("T")[0];
  });

  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [report, setReport] = useState<OperationalReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Exporting state
  const [exportingType, setExportingType] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

  // Documentation drawer state
  const [showMethodology, setShowMethodology] = useState<boolean>(false);

  // Date preset helper
  const applyPreset = (preset: "24h" | "7d" | "30d") => {
    setDatePreset(preset);
    const now = new Date();
    const end = now.toISOString().split("T")[0];
    let startD = new Date();
    if (preset === "24h") {
      startD.setDate(now.getDate() - 1);
    } else if (preset === "7d") {
      startD.setDate(now.getDate() - 7);
    } else if (preset === "30d") {
      startD.setDate(now.getDate() - 30);
    }
    const start = startD.toISOString().split("T")[0];
    setStartDate(start);
    setEndDate(end);
  };

  const loadReport = useCallback(async () => {
    if (startDate > endDate) {
      setError("Start date cannot be later than end date.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await fetchOperationalReport(
        {
          startDate,
          endDate,
          eventCategory: categoryFilter !== "all" ? categoryFilter : undefined,
        },
        demoMode
      );
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report data");
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, categoryFilter, demoMode]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleExport = async (type: "summary" | "events" | "alerts" | "incidents") => {
    setExportingType(type);
    setExportSuccess(null);
    try {
      await downloadReportCsv(
        type,
        {
          startDate,
          endDate,
          eventCategory: categoryFilter !== "all" ? categoryFilter : undefined,
        },
        demoMode
      );
      setExportSuccess(`Export for ${type} generated and downloaded successfully.`);
      setTimeout(() => setExportSuccess(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to export ${type}`);
    } finally {
      setExportingType(null);
    }
  };

  // Helper for timeseries SVG rendering
  const renderTimeSeriesChart = (points: TimeSeriesPoint[]) => {
    if (!points || points.length === 0) {
      return (
        <div className="py-12 text-center text-slate-400 font-mono text-xs">
          No timeseries event telemetry available for selected window.
        </div>
      );
    }

    const width = 640;
    const height = 160;
    const padding = { top: 20, right: 20, bottom: 25, left: 45 };
    const innerWidth = width - padding.left - padding.right;
    const innerHeight = height - padding.top - padding.bottom;

    const maxVal = Math.max(...points.map((p) => p.count), 1);
    const minVal = 0;

    const getX = (idx: number) => {
      if (points.length <= 1) return padding.left + innerWidth / 2;
      return padding.left + (idx / (points.length - 1)) * innerWidth;
    };

    const getY = (count: number) => {
      const ratio = (count - minVal) / (maxVal - minVal || 1);
      return padding.top + innerHeight - ratio * innerHeight;
    };

    const pathD = points.reduce((acc, p, i) => {
      const x = getX(i);
      const y = getY(p.count);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, "");

    const areaD =
      points.length > 0
        ? `${pathD} L ${getX(points.length - 1)} ${padding.top + innerHeight} L ${getX(0)} ${
            padding.top + innerHeight
          } Z`
        : "";

    return (
      <div className="relative w-full">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-44 overflow-visible"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="reportGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={width - padding.right}
            y2={padding.top}
            stroke="#1e293b"
            strokeDasharray="3 3"
          />
          <line
            x1={padding.left}
            y1={padding.top + innerHeight / 2}
            x2={width - padding.right}
            y2={padding.top + innerHeight / 2}
            stroke="#1e293b"
            strokeDasharray="3 3"
          />
          <line
            x1={padding.left}
            y1={padding.top + innerHeight}
            x2={width - padding.right}
            y2={padding.top + innerHeight}
            stroke="#334155"
          />

          {/* Area and Line */}
          {areaD && <path d={areaD} fill="url(#reportGrad)" />}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="#06b6d4"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Data Points */}
          {points.map((p, i) => {
            const cx = getX(i);
            const cy = getY(p.count);
            return (
              <circle
                key={i}
                cx={cx}
                cy={cy}
                r={3.5}
                className="fill-cyan-400 stroke-[#0a0e14] stroke-2 hover:r-5 transition-all cursor-pointer"
              >
                <title>{`${p.timestamp}: ${p.count.toLocaleString()} events`}</title>
              </circle>
            );
          })}
        </svg>

        {/* Axis Labels */}
        <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 mt-1 px-2">
          <span>{points[0]?.timestamp || "Start"}</span>
          <span className="text-cyan-400/80 font-medium">Daily Event Volume (UTC)</span>
          <span>{points[points.length - 1]?.timestamp || "End"}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1E293B] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded bg-cyan-950/60 border border-cyan-800/80 text-cyan-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-slate-100 flex items-center gap-2">
                Operational Reports & Analytics
                {demoMode && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-950/80 text-amber-400 border border-amber-800">
                    Demo Mode Active
                  </span>
                )}
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Verifiable SOC telemetry, MTTR performance metrics, threat attribution, and formula-safe compliance exports
                {!demoMode && onEnableDemo && (
                  <button
                    onClick={onEnableDemo}
                    className="ml-2 text-cyan-400 hover:text-cyan-300 underline font-mono text-[11px]"
                  >
                    (Preview Demo Data)
                  </button>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Global actions: Refresh & Methodology Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowMethodology(!showMethodology)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700 text-xs font-mono transition-colors"
          >
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Calculation Rules</span>
            {showMethodology ? (
              <ChevronUp className="w-3 h-3 text-slate-400" />
            ) : (
              <ChevronDown className="w-3 h-3 text-slate-400" />
            )}
          </button>
          <button
            onClick={loadReport}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-mono transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Methodology Documentation Collapsible Panel */}
      {showMethodology && (
        <div className="p-4 rounded-lg bg-[#0F172A] border border-cyan-900/60 text-xs font-mono space-y-3">
          <div className="flex items-center gap-2 text-cyan-400 font-semibold uppercase tracking-wider">
            <Info className="w-4 h-4" />
            <span>Metric Methodology & Security Controls</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-slate-300">
            <div className="space-y-1.5 bg-[#090d13] p-3 rounded border border-slate-800">
              <span className="text-cyan-300 font-medium">Mean Time to Resolution (MTTR):</span>
              <p className="text-[11px] text-slate-400">
                Formula: <code className="text-teal-300">AVG(updated_at - created_at)</code> calculated exclusively over incidents with lifecycle status <code className="text-teal-300">RESOLVED</code> or <code className="text-teal-300">CLOSED</code>. If 0 incidents are resolved within the selected window, result evaluates to null with sample size transparency rather than an invented benchmark.
              </p>
            </div>
            <div className="space-y-1.5 bg-[#090d13] p-3 rounded border border-slate-800">
              <span className="text-cyan-300 font-medium">CWE-1236 Formula Injection Defense:</span>
              <p className="text-[11px] text-slate-400">
                All CSV exports enforce RFC 4180 cell sanitization. Values beginning with formula triggers (<code className="text-teal-300">=, +, -, @, \t, \r</code>) are automatically prepended with a single quote (<code className="text-teal-300">'</code>) to prevent DDE / command execution in Microsoft Excel and LibreOffice.
              </p>
            </div>
            <div className="space-y-1.5 bg-[#090d13] p-3 rounded border border-slate-800">
              <span className="text-cyan-300 font-medium">Telemetry Aggregation:</span>
              <p className="text-[11px] text-slate-400">
                Event volumes derive from indexed <code className="text-teal-300">normalized_security_events.timestamp</code> grouped by UTC calendar date. Deduplication ensures that idempotent re-ingestions do not skew historical volumes.
              </p>
            </div>
            <div className="space-y-1.5 bg-[#090d13] p-3 rounded border border-slate-800">
              <span className="text-cyan-300 font-medium">Access Control & Non-Repudiation:</span>
              <p className="text-[11px] text-slate-400">
                Reporting queries require authenticated analyst privileges. All analytical exports generate structured audit ledger entries in <code className="text-teal-300">audit_events</code> tracking the requesting analyst, IP, and timestamp.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Date Controls Bar */}
      <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Preset Buttons */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5 mr-1">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              Window:
            </span>
            {(["24h", "7d", "30d"] as const).map((preset) => (
              <button
                key={preset}
                onClick={() => applyPreset(preset)}
                className={`px-2.5 py-1 rounded text-xs font-mono uppercase transition-colors ${
                  datePreset === preset
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                    : "bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/60"
                }`}
              >
                {preset === "24h" ? "24 Hours" : preset === "7d" ? "7 Days" : "30 Days"}
              </button>
            ))}
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              Category:
            </span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-[#0b1017] border border-slate-700 text-slate-200 text-xs font-mono rounded px-2.5 py-1 focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Event Categories</option>
              <option value="authentication">Authentication</option>
              <option value="network_flow">Network Flow</option>
              <option value="system_audit">System Audit</option>
              <option value="threat_intel">Threat Intel</option>
            </select>
          </div>
        </div>

        {/* Custom Start / End Dates */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-mono text-slate-400">From:</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => {
                setDatePreset("custom");
                setStartDate(e.target.value);
              }}
              className="bg-[#0b1017] border border-slate-700 text-slate-200 text-xs font-mono rounded px-2 py-0.5 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">To:</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => {
                setDatePreset("custom");
                setEndDate(e.target.value);
              }}
              className="bg-[#0b1017] border border-slate-700 text-slate-200 text-xs font-mono rounded px-2 py-0.5 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* CSV Export Action Buttons */}
          <div className="ml-auto flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              Export CSV:
            </span>
            <button
              onClick={() => handleExport("summary")}
              disabled={exportingType !== null}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-200 disabled:opacity-50 transition-colors"
            >
              {exportingType === "summary" ? "Exporting..." : "Summary"}
            </button>
            <button
              onClick={() => handleExport("events")}
              disabled={exportingType !== null}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-200 disabled:opacity-50 transition-colors"
            >
              {exportingType === "events" ? "Exporting..." : "Events"}
            </button>
            <button
              onClick={() => handleExport("alerts")}
              disabled={exportingType !== null}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-200 disabled:opacity-50 transition-colors"
            >
              {exportingType === "alerts" ? "Exporting..." : "Alerts"}
            </button>
            <button
              onClick={() => handleExport("incidents")}
              disabled={exportingType !== null}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-200 disabled:opacity-50 transition-colors"
            >
              {exportingType === "incidents" ? "Exporting..." : "Incidents"}
            </button>
          </div>
        </div>
      </div>

      {/* Export feedback toast */}
      {exportSuccess && (
        <div className="flex items-center gap-2 p-3 rounded bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 text-xs font-mono">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{exportSuccess}</span>
        </div>
      )}

      {/* Error notification */}
      {error && (
        <div className="flex items-center justify-between p-3.5 rounded bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs font-mono">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadReport}
            className="px-2 py-0.5 rounded bg-rose-900/60 hover:bg-rose-900 text-rose-200 border border-rose-700 text-[11px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Top 4 KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Ingested Events */}
        <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wide">
              Events Processed
            </span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 text-2xl font-semibold font-mono text-slate-100">
            {loading ? (
              <div className="h-8 w-24 bg-slate-800/80 animate-pulse rounded" />
            ) : (
              report?.total_events.toLocaleString() ?? "0"
            )}
          </div>
          <p className="mt-1 text-[11px] text-slate-400 font-mono">
            Within {startDate} to {endDate}
          </p>
        </div>

        {/* Card 2: Total Alerts */}
        <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wide">
              Alerts Triggered
            </span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-semibold font-mono text-slate-100">
            {loading ? (
              <div className="h-8 w-16 bg-slate-800/80 animate-pulse rounded" />
            ) : (
              report?.total_alerts.toLocaleString() ?? "0"
            )}
          </div>
          <p className="mt-1 text-[11px] text-slate-400 font-mono">
            {report?.alerts_by_severity?.critical ?? 0} critical, {report?.alerts_by_severity?.high ?? 0} high
          </p>
        </div>

        {/* Card 3: Total Incidents */}
        <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wide">
              Incidents Escalated
            </span>
            <Layers className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-semibold font-mono text-slate-100">
            {loading ? (
              <div className="h-8 w-16 bg-slate-800/80 animate-pulse rounded" />
            ) : (
              report?.total_incidents.toLocaleString() ?? "0"
            )}
          </div>
          <p className="mt-1 text-[11px] text-slate-400 font-mono">
            {(report?.incidents_by_status?.resolved ?? 0) + (report?.incidents_by_status?.closed ?? 0)} resolved/closed
          </p>
        </div>

        {/* Card 4: Mean Time to Resolution (MTTR) */}
        <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wide">
              Mean Time to Resolution
            </span>
            <Clock className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2">
            {loading ? (
              <div className="h-8 w-24 bg-slate-800/80 animate-pulse rounded" />
            ) : report?.mttr_metrics?.mean_time_to_resolve_hours !== null &&
              report?.mttr_metrics?.mean_time_to_resolve_hours !== undefined ? (
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-semibold font-mono text-emerald-300">
                  {report.mttr_metrics.mean_time_to_resolve_hours.toFixed(1)}
                </span>
                <span className="text-xs font-mono text-slate-400">hours ({report.mttr_metrics.mean_time_to_resolve_minutes?.toFixed(0)}m)</span>
              </div>
            ) : (
              <div className="text-sm font-mono text-slate-400 font-medium">
                Insufficient Data
              </div>
            )}
          </div>
          <p className="mt-1 text-[11px] text-slate-400 font-mono truncate" title={report?.mttr_metrics?.sample_description}>
            {report?.mttr_metrics?.sample_description || "0 resolved cases in period"}
          </p>
        </div>
      </div>

      {/* Main Charts & Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Event Volume Timeseries */}
        <div className="lg:col-span-2 p-4 rounded-lg bg-[#121820] border border-[#1E293B] flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
                Event Volume Trend (Daily UTC Telemetry)
              </span>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Total Points: <span className="text-slate-200 font-semibold">{report?.event_volume_timeseries?.length ?? 0}</span>
            </span>
          </div>

          <div className="mt-4">
            {loading ? (
              <div className="h-44 w-full bg-slate-800/40 animate-pulse rounded flex items-center justify-center">
                <span className="text-xs font-mono text-slate-500">Aggregating database volume...</span>
              </div>
            ) : (
              renderTimeSeriesChart(report?.event_volume_timeseries || [])
            )}
          </div>
        </div>

        {/* Right Column (1 Col): Severity Distribution & Incident Lifecycle */}
        <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
                  Alerts By Severity
                </span>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Total: <span className="text-slate-200 font-semibold">{report?.total_alerts ?? 0}</span>
              </span>
            </div>

            <div className="mt-3 space-y-2 font-mono text-xs">
              {(["critical", "high", "medium", "low", "informational"] as const).map((sev) => {
                const count = report?.alerts_by_severity?.[sev] || 0;
                const total = report?.total_alerts || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={sev} className="space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="uppercase text-slate-300 font-medium">{sev}</span>
                      <span className="text-slate-400">{count} ({pct}%)</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          sev === "critical"
                            ? "bg-rose-500"
                            : sev === "high"
                            ? "bg-orange-500"
                            : sev === "medium"
                            ? "bg-amber-500"
                            : sev === "low"
                            ? "bg-teal-500"
                            : "bg-sky-500"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Incident Status Breakdown */}
          <div className="pt-3 border-t border-[#1E293B]">
            <span className="text-[11px] font-mono uppercase tracking-wide text-slate-400 block mb-2">
              Incident Lifecycle Distribution
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="bg-[#0b1017] p-2 rounded border border-slate-800">
                <span className="text-rose-400 text-[10px] block uppercase">Active Cases</span>
                <span className="text-base font-semibold text-slate-200">
                  {(report?.incidents_by_status?.open ?? 0) +
                    (report?.incidents_by_status?.investigating ?? 0) +
                    (report?.incidents_by_status?.containment ?? 0)}
                </span>
              </div>
              <div className="bg-[#0b1017] p-2 rounded border border-slate-800">
                <span className="text-emerald-400 text-[10px] block uppercase">Resolved / Closed</span>
                <span className="text-base font-semibold text-slate-200">
                  {(report?.incidents_by_status?.resolved ?? 0) +
                    (report?.incidents_by_status?.closed ?? 0)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Attribution Tables Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Table 1: Alerts Attributed to Detection Rules */}
        <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B]">
          <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
                Detection Rule Attribution
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Rules Active: {report?.alerts_by_rule?.length ?? 0}
            </span>
          </div>

          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="text-slate-400 border-b border-slate-800 text-[11px]">
                  <th className="py-2 pr-3">Rule Code</th>
                  <th className="py-2 pr-3">Rule Name</th>
                  <th className="py-2 pr-3">Severity</th>
                  <th className="py-2 text-right">Alerts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-slate-500">
                      Loading rule attribution...
                    </td>
                  </tr>
                ) : !report?.alerts_by_rule || report.alerts_by_rule.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-slate-500">
                      No rule triggers recorded in this timeframe.
                    </td>
                  </tr>
                ) : (
                  report.alerts_by_rule.map((r) => (
                    <tr key={r.rule_code} className="hover:bg-slate-800/40">
                      <td className="py-2.5 pr-3 text-cyan-400 font-semibold">{r.rule_code}</td>
                      <td className="py-2.5 pr-3 text-slate-200 truncate max-w-[200px]" title={r.rule_name}>
                        {r.rule_name}
                      </td>
                      <td className="py-2.5 pr-3">
                        <SeverityBadge severity={r.severity} size="sm" />
                      </td>
                      <td className="py-2.5 text-right font-semibold text-slate-200">
                        {r.count.toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Table 2: Top Attacking Source IPs */}
        <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B]">
          <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-rose-400" />
              <span className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
                Top Source IPs (Observed Threats)
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Top {report?.top_source_ips?.length ?? 0} Observed
            </span>
          </div>

          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="text-slate-400 border-b border-slate-800 text-[11px]">
                  <th className="py-2 pr-3">IP Address</th>
                  <th className="py-2 pr-3">Observed Events</th>
                  <th className="py-2 pr-3">Triggered Alerts</th>
                  <th className="py-2 text-right">Threat Ratio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-slate-500">
                      Aggregating source IP telemetry...
                    </td>
                  </tr>
                ) : !report?.top_source_ips || report.top_source_ips.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-4 text-center text-slate-500">
                      No distinct external source IPs logged in timeframe.
                    </td>
                  </tr>
                ) : (
                  report.top_source_ips.map((ip) => {
                    const ratio =
                      ip.event_count > 0
                        ? ((ip.alert_count / ip.event_count) * 100).toFixed(1)
                        : "0.0";
                    return (
                      <tr key={ip.ip} className="hover:bg-slate-800/40">
                        <td className="py-2.5 pr-3 text-cyan-300 font-medium">{ip.ip}</td>
                        <td className="py-2.5 pr-3 text-slate-300">
                          {ip.event_count.toLocaleString()}
                        </td>
                        <td className="py-2.5 pr-3 text-amber-300 font-semibold">
                          {ip.alert_count.toLocaleString()}
                        </td>
                        <td className="py-2.5 text-right text-slate-400">{ratio}%</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Incident Case Dossier Download Guidance */}
      <div className="p-4 rounded-lg bg-[#0d131a] border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded bg-slate-800/80 border border-slate-700 text-cyan-400 shrink-0">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-mono font-semibold text-slate-200 uppercase">
              Incident Case Forensic Dossier Export
            </h4>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Need a complete forensic dossier for a specific incident? Open any incident case file from the{" "}
              <span className="text-cyan-400 font-medium">Incidents</span> tab to export its comprehensive audit markdown dossier with chained alerts, investigation timeline, and supporting forensic evidence.
            </p>
          </div>
        </div>
        <button
          onClick={() => handleExport("incidents")}
          className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-mono text-xs font-medium transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export All Incidents</span>
        </button>
      </div>
    </div>
  );
};

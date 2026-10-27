import React, { useState } from "react";
import {
  ShieldAlert,
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { AlertItem, PaginatedResponse } from "../../types";
import { SeverityBadge } from "../common/SeverityBadge";
import { StatusBadge } from "../common/StatusBadge";

interface AlertsTableProps {
  alertsResponse: PaginatedResponse<AlertItem> | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onFilterChange: (filters: {
    search?: string;
    severity?: string;
    status?: string;
    page?: number;
  }) => void;
  onSelectAlert?: (alert: AlertItem) => void;
  onEnableDemo?: () => void;
}

export const AlertsTable: React.FC<AlertsTableProps> = ({
  alertsResponse,
  loading,
  error,
  onRefresh,
  onFilterChange,
  onSelectAlert,
  onEnableDemo,
}) => {
  const [searchInput, setSearchInput] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const alerts = alertsResponse?.items || [];
  const totalCount = alertsResponse?.total_count || 0;
  const currentPage = alertsResponse?.page || 1;
  const totalPages = alertsResponse?.total_pages || 1;

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({
      search: searchInput,
      severity: severityFilter,
      status: statusFilter,
      page: 1,
    });
  };

  const handleClearFilters = () => {
    setSearchInput("");
    setSeverityFilter("all");
    setStatusFilter("all");
    onFilterChange({ search: "", severity: "all", status: "all", page: 1 });
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toISOString().replace("T", " ").substring(0, 19) + " UTC";
    } catch {
      return isoString;
    }
  };

  return (
    <div className="rounded-lg bg-[#121820] border border-[#1E293B] overflow-hidden flex flex-col">
      {/* Table Header Controls */}
      <div className="p-4 border-b border-[#1E293B] space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-teal-400" />
            <h3 className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
              Recent Security Alerts Queue
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {totalCount.toLocaleString()} Total
            </span>
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="self-start sm:self-auto flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors disabled:opacity-50"
            title="Refresh alert queue"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-teal-400" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 pt-1">
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by rule code, title, IP..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-8 pr-16 py-1.5 text-xs font-mono bg-[#0B0F14] border border-[#1E293B] rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors"
            />
            <button
              type="submit"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 px-2 py-0.5 text-[10px] font-mono bg-teal-950 text-teal-300 border border-teal-800 rounded hover:bg-teal-900"
            >
              Filter
            </button>
          </form>

          <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
            {/* Severity Filter */}
            <div className="flex items-center gap-1 bg-[#0B0F14] border border-[#1E293B] px-2 py-1 rounded">
              <Filter className="w-3 h-3 text-slate-500" />
              <span className="text-slate-400 text-[11px]">SEV:</span>
              <select
                value={severityFilter}
                onChange={(e) => {
                  setSeverityFilter(e.target.value);
                  onFilterChange({
                    search: searchInput,
                    severity: e.target.value,
                    status: statusFilter,
                    page: 1,
                  });
                }}
                className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
              >
                <option value="all" className="bg-[#121820]">All Severities</option>
                <option value="critical" className="bg-[#121820]">Critical</option>
                <option value="high" className="bg-[#121820]">High</option>
                <option value="medium" className="bg-[#121820]">Medium</option>
                <option value="low" className="bg-[#121820]">Low</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1 bg-[#0B0F14] border border-[#1E293B] px-2 py-1 rounded">
              <span className="text-slate-400 text-[11px]">STATUS:</span>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  onFilterChange({
                    search: searchInput,
                    severity: severityFilter,
                    status: e.target.value,
                    page: 1,
                  });
                }}
                className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
              >
                <option value="all" className="bg-[#121820]">All Statuses</option>
                <option value="new" className="bg-[#121820]">New</option>
                <option value="triaged" className="bg-[#121820]">Triaged</option>
                <option value="investigating" className="bg-[#121820]">Investigating</option>
                <option value="escalated" className="bg-[#121820]">Escalated</option>
                <option value="closed_resolved" className="bg-[#121820]">Closed (Resolved)</option>
                <option value="closed_false_positive" className="bg-[#121820]">Closed (FP)</option>
              </select>
            </div>

            {(searchInput || severityFilter !== "all" || statusFilter !== "all") && (
              <button
                onClick={handleClearFilters}
                className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                title="Reset filters"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto min-h-[220px]">
        {error ? (
          <div className="py-12 px-4 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
            <div className="text-xs font-mono text-rose-300 font-semibold">
              Failed to Load Alerts from API
            </div>
            <p className="text-[11px] text-slate-400 max-w-md mx-auto">{error}</p>
            <button
              onClick={onRefresh}
              className="px-3 py-1 text-xs font-mono rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
            >
              Retry Connection
            </button>
          </div>
        ) : loading ? (
          <div className="p-4 space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 bg-slate-800/40 rounded animate-pulse" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <div className="py-12 px-4 text-center space-y-2">
            <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-xs font-mono text-slate-300 font-medium">
              No Security Alerts Matching Filters
            </div>
            <p className="text-[11px] text-slate-400 max-w-md mx-auto">
              No alert records exist in the current queue matching criteria. Active detection rules continuously scan ingestion telemetry.
            </p>
            {onEnableDemo && (
              <button
                onClick={onEnableDemo}
                className="mt-2 inline-flex items-center gap-1.5 text-xs font-mono text-teal-400 hover:text-teal-300 underline underline-offset-4"
              >
                Load demonstration alert stream →
              </button>
            )}
          </div>
        ) : (
          <table className="w-full text-left text-xs font-mono border-collapse" role="table">
            <thead>
              <tr className="bg-[#0E141D] text-slate-400 border-b border-[#1E293B] text-[11px]">
                <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Timestamp</th>
                <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Severity</th>
                <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Rule / Mnemonic</th>
                <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Title</th>
                <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Source Entity</th>
                <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Status</th>
                <th scope="col" className="py-2.5 px-4 font-semibold uppercase text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E293B]">
              {alerts.map((alert) => (
                <tr
                  key={alert.id}
                  className="hover:bg-slate-900/40 transition-colors group"
                >
                  <td className="py-2.5 px-4 text-slate-400 whitespace-nowrap text-[11px]">
                    {formatTimestamp(alert.created_at)}
                  </td>
                  <td className="py-2.5 px-4 whitespace-nowrap">
                    <SeverityBadge severity={alert.severity} size="sm" />
                  </td>
                  <td className="py-2.5 px-4 whitespace-nowrap">
                    <span className="text-teal-400 font-semibold mr-1">
                      {alert.rule_code || "RULE"}
                    </span>
                    <span className="text-slate-400 text-[10px] hidden lg:inline">
                      ({alert.rule_name || "Detection Logic"})
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-slate-200 max-w-xs truncate" title={alert.title}>
                    {alert.title}
                  </td>
                  <td className="py-2.5 px-4 text-slate-300 whitespace-nowrap">
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px]">
                      {alert.source_ip || "—"}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 whitespace-nowrap">
                    <StatusBadge
                      status={
                        alert.status === "new"
                          ? "critical"
                          : alert.status === "investigating"
                          ? "degraded"
                          : "healthy"
                      }
                      label={alert.status.replace("_", " ")}
                      size="sm"
                    />
                  </td>
                  <td className="py-2.5 px-4 text-right whitespace-nowrap">
                    <button
                      onClick={() => onSelectAlert?.(alert)}
                      className="px-2 py-1 rounded bg-slate-800/60 hover:bg-slate-700 text-teal-300 text-[10px] border border-slate-700 inline-flex items-center gap-1 transition-colors"
                      title="Inspect alert triage payload"
                    >
                      <span>Triage</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-[#1E293B] bg-[#0E141D] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-slate-400">
        <div>
          Showing Page <span className="text-slate-200 font-semibold">{currentPage}</span> of{" "}
          <span className="text-slate-200 font-semibold">{totalPages}</span> ({totalCount} entries)
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() =>
              onFilterChange({
                search: searchInput,
                severity: severityFilter,
                status: statusFilter,
                page: Math.max(1, currentPage - 1),
              })
            }
            disabled={currentPage <= 1 || loading}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-40 transition-colors"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>Prev</span>
          </button>

          <span className="px-2 py-0.5 rounded bg-[#0B0F14] border border-[#1E293B] text-teal-300">
            {currentPage}
          </span>

          <button
            onClick={() =>
              onFilterChange({
                search: searchInput,
                severity: severityFilter,
                status: statusFilter,
                page: Math.min(totalPages, currentPage + 1),
              })
            }
            disabled={currentPage >= totalPages || loading}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-40 transition-colors"
          >
            <span>Next</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

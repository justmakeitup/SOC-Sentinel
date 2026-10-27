import React, { useState, useEffect, useCallback } from "react";
import {
  Layers,
  Search,
  Filter,
  Upload,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Code,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { fetchEvents } from "../../api/events";
import { fetchLogSources } from "../../api/sources";
import {
  NormalizedSecurityEventItem,
  PaginatedResponse,
  LogSourceItem,
} from "../../types";
import { SeverityBadge } from "../common/SeverityBadge";
import { ImportLogModal } from "../ingestion/ImportLogModal";

interface EventsViewProps {
  demoMode: boolean;
  onEnableDemo?: () => void;
}

export const EventsView: React.FC<EventsViewProps> = ({
  demoMode,
  onEnableDemo,
}) => {
  const [eventsResponse, setEventsResponse] =
    useState<PaginatedResponse<NormalizedSecurityEventItem> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchInput, setSearchInput] = useState<string>("");
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Sources for import modal
  const [sources, setSources] = useState<LogSourceItem[]>([]);
  const [importModalOpen, setImportModalOpen] = useState<boolean>(false);
  const [selectedEvent, setSelectedEvent] =
    useState<NormalizedSecurityEventItem | null>(null);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvents(
        {
          page: currentPage,
          pageSize: 15,
          eventType: eventTypeFilter,
          severity: severityFilter,
          search: searchInput,
        },
        demoMode
      );
      setEventsResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load events");
      setEventsResponse(null);
    } finally {
      setLoading(false);
    }
  }, [currentPage, eventTypeFilter, severityFilter, searchInput, demoMode]);

  const loadSources = useCallback(async () => {
    try {
      const data = await fetchLogSources(1, 50, demoMode);
      setSources(data.items);
    } catch {
      // Ignore source load failure in background
    }
  }, [demoMode]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  useEffect(() => {
    loadSources();
  }, [loadSources]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadEvents();
  };

  const handleResetFilters = () => {
    setSearchInput("");
    setEventTypeFilter("all");
    setSeverityFilter("all");
    setCurrentPage(1);
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toISOString().replace("T", " ").substring(0, 19) + " UTC";
    } catch {
      return isoString;
    }
  };

  const events = eventsResponse?.items || [];
  const totalCount = eventsResponse?.total_count || 0;
  const totalPages = eventsResponse?.total_pages || 1;

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1E293B]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-slate-800/80 text-teal-400 border border-slate-700">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-100">
                Normalized Security Telemetry
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                ECS Taxonomy
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Cryptographically deduplicated event stream across all sensors and collectors.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setImportModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono font-medium bg-teal-950 text-teal-300 border border-teal-800 hover:bg-teal-900 transition-colors shadow-sm"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Import Log File</span>
          </button>
          <button
            onClick={loadEvents}
            disabled={loading}
            className="p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-[#1E293B]"
            title="Refresh events"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="rounded-lg bg-[#121820] border border-[#1E293B] overflow-hidden flex flex-col">
        {/* Search & Filter Toolbar */}
        <div className="p-4 border-b border-[#1E293B] flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 font-mono text-xs">
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by action, user, IP, or command..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-8 pr-16 py-1.5 text-xs bg-[#0B0F14] border border-[#1E293B] rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors"
            />
            <button
              type="submit"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 px-2 py-0.5 text-[10px] bg-teal-950 text-teal-300 border border-teal-800 rounded hover:bg-teal-900"
            >
              Filter
            </button>
          </form>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Event Type Filter */}
            <div className="flex items-center gap-1 bg-[#0B0F14] border border-[#1E293B] px-2 py-1 rounded">
              <Filter className="w-3 h-3 text-slate-500" />
              <span className="text-slate-400 text-[11px]">TYPE:</span>
              <select
                value={eventTypeFilter}
                onChange={(e) => {
                  setEventTypeFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
              >
                <option value="all" className="bg-[#121820]">All Types</option>
                <option value="authentication" className="bg-[#121820]">Authentication</option>
                <option value="network_flow" className="bg-[#121820]">Network Flow</option>
                <option value="process_execution" className="bg-[#121820]">Process Exec</option>
                <option value="generic_telemetry" className="bg-[#121820]">Generic</option>
              </select>
            </div>

            {/* Severity Filter */}
            <div className="flex items-center gap-1 bg-[#0B0F14] border border-[#1E293B] px-2 py-1 rounded">
              <span className="text-slate-400 text-[11px]">SEV:</span>
              <select
                value={severityFilter}
                onChange={(e) => {
                  setSeverityFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
              >
                <option value="all" className="bg-[#121820]">All Severities</option>
                <option value="critical" className="bg-[#121820]">Critical</option>
                <option value="high" className="bg-[#121820]">High</option>
                <option value="medium" className="bg-[#121820]">Medium</option>
                <option value="low" className="bg-[#121820]">Low</option>
                <option value="informational" className="bg-[#121820]">Informational</option>
              </select>
            </div>

            {(searchInput || eventTypeFilter !== "all" || severityFilter !== "all") && (
              <button
                onClick={handleResetFilters}
                className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                title="Reset filters"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Events Table Body */}
        <div className="overflow-x-auto min-h-[300px]">
          {error ? (
            <div className="py-14 px-4 text-center space-y-3 font-mono">
              <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
              <div className="text-xs text-rose-300 font-semibold">
                Failed to Query Security Events
              </div>
              <p className="text-[11px] text-slate-400 max-w-md mx-auto">{error}</p>
              <button
                onClick={loadEvents}
                className="px-3 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
              >
                Retry Query
              </button>
            </div>
          ) : loading ? (
            <div className="p-4 space-y-2">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-10 bg-slate-800/40 rounded animate-pulse" />
              ))}
            </div>
          ) : events.length === 0 ? (
            <div className="py-14 px-4 text-center space-y-3 font-mono">
              <Layers className="w-8 h-8 text-slate-600 mx-auto" />
              <div className="text-xs text-slate-300 font-semibold">
                No Normalized Events Recorded
              </div>
              <p className="text-[11px] text-slate-400 max-w-md mx-auto">
                No telemetry matching the selected filters exists. Import a CSV/JSON log file or toggle demo mode to explore telemetry features.
              </p>
              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setImportModalOpen(true)}
                  className="px-3 py-1.5 rounded text-xs bg-teal-950 text-teal-300 border border-teal-800 hover:bg-teal-900"
                >
                  Import Log File
                </button>
                {onEnableDemo && (
                  <button
                    onClick={onEnableDemo}
                    className="text-xs text-teal-400 hover:text-teal-300 underline underline-offset-4"
                  >
                    View Demo Stream →
                  </button>
                )}
              </div>
            </div>
          ) : (
            <table className="w-full text-left text-xs font-mono border-collapse" role="table">
              <thead>
                <tr className="bg-[#0E141D] text-slate-400 border-b border-[#1E293B] text-[11px]">
                  <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Timestamp (UTC)</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Type</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Action</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Network Endpoints</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Subject User</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Severity</th>
                  <th scope="col" className="py-2.5 px-4 font-semibold uppercase text-right">Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B]">
                {events.map((ev) => (
                  <tr
                    key={ev.id}
                    className="hover:bg-slate-900/40 transition-colors group"
                  >
                    <td className="py-2.5 px-4 text-slate-400 whitespace-nowrap text-[11px]">
                      {formatTimestamp(ev.timestamp)}
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-teal-400 text-[10px] font-semibold">
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-200 font-semibold whitespace-nowrap">
                      {ev.event_action}
                    </td>
                    <td className="py-2.5 px-4 text-slate-300 whitespace-nowrap text-[11px]">
                      {ev.source_ip ? (
                        <span>
                          {ev.source_ip}
                          {ev.source_port ? `:${ev.source_port}` : ""}
                          {ev.destination_ip ? ` → ${ev.destination_ip}` : ""}
                          {ev.destination_port ? `:${ev.destination_port}` : ""}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-slate-300 whitespace-nowrap">
                      {ev.user_name || <span className="text-slate-500">—</span>}
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      <SeverityBadge severity={ev.severity} size="sm" />
                    </td>
                    <td className="py-2.5 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => setSelectedEvent(ev)}
                        className="px-2 py-1 rounded bg-slate-800/80 hover:bg-slate-700 text-teal-300 text-[10px] border border-slate-700 inline-flex items-center gap-1 transition-colors"
                        title="View forensic raw payload"
                      >
                        <Code className="w-2.5 h-2.5" />
                        <span>Payload</span>
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
            <span className="text-slate-200 font-semibold">{totalPages}</span> ({totalCount} events)
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
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
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages || loading}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-40 transition-colors"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Forensic Payload Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121820] border border-[#1E293B] rounded-lg max-w-2xl w-full p-6 space-y-4 font-mono shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-teal-400" />
                <h3 className="text-sm font-bold text-slate-100 uppercase">
                  Forensic Raw Payload Inspector
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-200"
              >
                [Close]
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                  Cryptographic SHA-256 Event Fingerprint
                </div>
                <div className="p-2 rounded bg-[#0B0F14] border border-[#1E293B] text-[11px] text-teal-300 break-all select-all">
                  {selectedEvent.event_hash}
                </div>
              </div>

              <div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                  Sanitized Immutable Raw Log Line
                </div>
                <div className="p-3 rounded bg-[#0B0F14] border border-[#1E293B] text-slate-200 text-[11px] overflow-x-auto whitespace-pre-wrap select-all font-mono leading-relaxed">
                  {selectedEvent.raw_payload}
                </div>
              </div>

              {selectedEvent.extra_fields && Object.keys(selectedEvent.extra_fields).length > 0 && (
                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                    Normalized Dialect Fields
                  </div>
                  <pre className="p-3 rounded bg-[#0B0F14] border border-[#1E293B] text-teal-200 text-[10px] overflow-x-auto max-h-40">
                    {JSON.stringify(selectedEvent.extra_fields, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-[#1E293B]">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs border border-slate-700"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Log Modal Dialog */}
      <ImportLogModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onImportSuccess={() => {
          loadEvents();
          loadSources();
        }}
        sources={sources}
      />
    </div>
  );
};

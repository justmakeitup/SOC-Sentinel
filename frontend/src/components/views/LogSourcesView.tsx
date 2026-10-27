import React, { useState, useEffect, useCallback } from "react";
import {
  Radio,
  Plus,
  RefreshCw,
  Server,
  AlertCircle,
  Clock,
  AlertTriangle,
  X,
} from "lucide-react";
import { fetchLogSources, createLogSource, fetchIngestionJobs } from "../../api/sources";
import { LogSourceItem, IngestionJobItem } from "../../types";
import { StatusBadge } from "../common/StatusBadge";

interface LogSourcesViewProps {
  demoMode: boolean;
  onEnableDemo?: () => void;
}

export const LogSourcesView: React.FC<LogSourcesViewProps> = ({
  demoMode,
  onEnableDemo,
}) => {
  const [sources, setSources] = useState<LogSourceItem[]>([]);
  const [jobs, setJobs] = useState<IngestionJobItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState<boolean>(false);
  const [selectedJob, setSelectedJob] = useState<IngestionJobItem | null>(null);

  // New source form state
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("syslog");
  const [newDesc, setNewDesc] = useState("");
  const [newIp, setNewIp] = useState("");
  const [newHost, setNewHost] = useState("");
  const [newRetention, setNewRetention] = useState(90);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sourcesRes, jobsRes] = await Promise.all([
        fetchLogSources(1, 50, demoMode),
        fetchIngestionJobs(1, 20, undefined, demoMode),
      ]);
      setSources(sourcesRes.items);
      setJobs(jobsRes.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load log sources");
    } finally {
      setLoading(false);
    }
  }, [demoMode]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    setIsSubmitting(true);
    setCreateError(null);
    try {
      await createLogSource({
        name: newName.trim(),
        source_type: newType,
        description: newDesc.trim() || undefined,
        ip_address: newIp.trim() || undefined,
        hostname: newHost.trim() || undefined,
        retention_days: newRetention,
      });
      setCreateModalOpen(false);
      setNewName("");
      setNewDesc("");
      setNewIp("");
      setNewHost("");
      loadData();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to register source");
    } finally {
      setIsSubmitting(false);
    }
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
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1E293B]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-slate-800/80 text-teal-400 border border-slate-700">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-100">
                Log Sources & Ingestion Pipeline
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                Fleet Management
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Sensor collector registrations, batch idempotency records, and parser health metrics.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCreateModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono font-medium bg-teal-950 text-teal-300 border border-teal-800 hover:bg-teal-900 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Register Sensor</span>
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-[#1E293B]"
            title="Refresh sources"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-400" : ""}`} />
          </button>
        </div>
      </div>

      {error ? (
        <div className="p-5 rounded-lg bg-rose-950/40 border border-rose-800 text-center space-y-2 font-mono">
          <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
          <div className="text-xs text-rose-300 font-semibold">{error}</div>
          <button
            onClick={loadData}
            className="px-3 py-1 rounded bg-slate-800 text-slate-200 text-xs border border-slate-700 hover:bg-slate-700"
          >
            Retry Connection
          </button>
        </div>
      ) : loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-36 rounded-lg bg-slate-800/40 animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {/* Registered Log Sources Grid */}
          <div>
            <div className="flex items-center justify-between mb-3 font-mono text-xs text-slate-400">
              <span className="uppercase tracking-wider">Active Sensor Collectors ({sources.length})</span>
            </div>

            {sources.length === 0 ? (
              <div className="p-8 rounded-lg bg-[#121820] border border-[#1E293B] text-center space-y-2 font-mono">
                <Server className="w-8 h-8 text-slate-600 mx-auto" />
                <div className="text-xs text-slate-300 font-semibold">No Registered Sensors</div>
                <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
                  Click 'Register Sensor' or import a telemetry file to establish your first log collection feed.
                </p>
                {onEnableDemo && (
                  <button
                    onClick={onEnableDemo}
                    className="text-xs text-teal-400 hover:text-teal-300 underline underline-offset-4"
                  >
                    Load demo sensor fleet →
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sources.map((s) => (
                  <div
                    key={s.id}
                    className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] hover:border-slate-700 transition-colors space-y-3 font-mono"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-xs font-bold text-slate-100">{s.name}</div>
                        <div className="text-[10px] text-teal-400 uppercase tracking-wider">
                          {s.source_type}
                        </div>
                      </div>
                      <StatusBadge
                        status={s.status === "active" ? "connected" : "disconnected"}
                        size="sm"
                      />
                    </div>

                    {s.description && (
                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                        {s.description}
                      </p>
                    )}

                    <div className="pt-2 border-t border-[#1E293B] grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                      <div>
                        <span className="text-[10px] block">TOTAL EVENTS</span>
                        <span className="text-slate-200 font-bold">{s.total_events.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-[10px] block">RETENTION</span>
                        <span className="text-slate-200 font-bold">{s.retention_days} Days</span>
                      </div>
                      <div>
                        <span className="text-[10px] block">IP/HOST</span>
                        <span className="text-slate-300 truncate block">{s.ip_address || s.hostname || "—"}</span>
                      </div>
                      <div>
                        <span className="text-[10px] block">INGEST RUNS</span>
                        <span className="text-teal-300 font-bold">{s.total_jobs}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Ingestion Jobs Audit Table */}
          <div className="rounded-lg bg-[#121820] border border-[#1E293B] overflow-hidden flex flex-col font-mono text-xs">
            <div className="p-4 border-b border-[#1E293B] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-teal-400" />
                <span className="font-semibold uppercase tracking-wider text-slate-200">
                  Ingestion Job History & Quarantine Audit
                </span>
              </div>
              <span className="text-[11px] text-slate-400">{jobs.length} Runs Logged</span>
            </div>

            <div className="overflow-x-auto min-h-[160px]">
              {jobs.length === 0 ? (
                <div className="py-10 text-center text-slate-400 text-xs">
                  No ingestion jobs recorded yet.
                </div>
              ) : (
                <table className="w-full text-left border-collapse" role="table">
                  <thead>
                    <tr className="bg-[#0E141D] text-slate-400 border-b border-[#1E293B] text-[11px]">
                      <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Started At (UTC)</th>
                      <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Status</th>
                      <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Processed Events</th>
                      <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Quarantined / Rejected</th>
                      <th scope="col" className="py-2.5 px-4 font-semibold uppercase">Ingested Volume</th>
                      <th scope="col" className="py-2.5 px-4 font-semibold uppercase text-right">Audit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1E293B]">
                    {jobs.map((job) => (
                      <tr key={job.id} className="hover:bg-slate-900/40 transition-colors">
                        <td className="py-2.5 px-4 text-slate-400 whitespace-nowrap text-[11px]">
                          {formatTimestamp(job.started_at)}
                        </td>
                        <td className="py-2.5 px-4 whitespace-nowrap">
                          <StatusBadge
                            status={
                              job.status === "completed"
                                ? "healthy"
                                : job.status === "partially_failed"
                                ? "degraded"
                                : "error"
                            }
                            label={job.status.replace("_", " ")}
                            size="sm"
                          />
                        </td>
                        <td className="py-2.5 px-4 font-bold text-emerald-400 whitespace-nowrap">
                          {job.events_processed.toLocaleString()}
                        </td>
                        <td className="py-2.5 px-4 whitespace-nowrap">
                          {job.events_failed > 0 ? (
                            <span className="text-amber-400 font-bold">
                              {job.events_failed} Malformed Rows
                            </span>
                          ) : (
                            <span className="text-slate-500">0</span>
                          )}
                        </td>
                        <td className="py-2.5 px-4 text-slate-300 whitespace-nowrap">
                          {(job.bytes_ingested / 1024).toFixed(1)} KB
                        </td>
                        <td className="py-2.5 px-4 text-right whitespace-nowrap">
                          {job.rejected_records && job.rejected_records.length > 0 ? (
                            <button
                              onClick={() => setSelectedJob(job)}
                              className="px-2 py-1 rounded bg-amber-950/60 hover:bg-amber-900 text-amber-300 text-[10px] border border-amber-800 inline-flex items-center gap-1 transition-colors"
                            >
                              <AlertCircle className="w-2.5 h-2.5" />
                              <span>Inspect Rejections</span>
                            </button>
                          ) : (
                            <span className="text-[10px] text-slate-500">Clean Import</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}

      {/* Quarantined Records Detail Modal */}
      {selectedJob && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121820] border border-[#1E293B] rounded-lg max-w-xl w-full p-6 space-y-4 font-mono shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-slate-100 uppercase">
                  Quarantined Malformed Records Inspector
                </h3>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-200"
              >
                [Close]
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="text-slate-300 leading-relaxed text-[11px]">
                Job ID: <span className="text-teal-400">{selectedJob.id}</span> — {selectedJob.events_failed} rows failed validation during parsing and were safely isolated.
              </div>

              <div className="max-h-64 overflow-y-auto space-y-2 p-2 bg-[#0B0F14] border border-[#1E293B] rounded">
                {selectedJob.rejected_records?.map((rej, i) => (
                  <div key={i} className="p-2 rounded bg-slate-900 border border-slate-800 space-y-1">
                    <div className="text-amber-400 font-bold text-[11px]">
                      Line {rej.line_number}: {rej.reason}
                    </div>
                    {rej.raw_snippet && (
                      <div className="p-1.5 rounded bg-black/60 text-slate-300 text-[10px] overflow-x-auto whitespace-pre-wrap select-all">
                        {rej.raw_snippet}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#1E293B]">
              <button
                onClick={() => setSelectedJob(null)}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-200 text-xs hover:bg-slate-700 border border-slate-700"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Register Source Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121820] border border-[#1E293B] rounded-lg max-w-md w-full p-6 space-y-4 font-mono shadow-2xl text-xs">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-teal-400" />
                <h3 className="text-sm font-bold text-slate-100 uppercase">
                  Register New Log Source
                </h3>
              </div>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSource} className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  Source Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Core-FW-Edge-01"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  Collector Protocol / Type
                </label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 focus:outline-none focus:border-teal-500 cursor-pointer"
                >
                  <option value="syslog">Syslog Forwarder</option>
                  <option value="windows_event_log">Windows Event Forwarding (WEF)</option>
                  <option value="suricata_nids">Suricata NIDS Flow</option>
                  <option value="zeek_network">Zeek Network Telemetry</option>
                  <option value="cloudtrail">AWS CloudTrail Audit</option>
                  <option value="kubernetes">Kubernetes Audit API</option>
                  <option value="application_json">Application JSON Feed</option>
                  <option value="custom">Custom Sensor</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  IP Address (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 192.168.1.1"
                  value={newIp}
                  onChange={(e) => setNewIp(e.target.value)}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  Hostname / FQDN (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. fw01.sentinel.sec"
                  value={newHost}
                  onChange={(e) => setNewHost(e.target.value)}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  Retention Window (Days)
                </label>
                <input
                  type="number"
                  min="7"
                  max="3650"
                  value={newRetention}
                  onChange={(e) => setNewRetention(Number(e.target.value))}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Deployment subnet, sensor criticality..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 focus:outline-none focus:border-teal-500"
                />
              </div>

              {createError && (
                <div className="p-2.5 rounded bg-rose-950/60 border border-rose-800 text-rose-300 text-[11px]">
                  {createError}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1E293B]">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded bg-teal-950 hover:bg-teal-900 text-teal-300 border border-teal-800 font-semibold disabled:opacity-50"
                >
                  {isSubmitting ? "Registering..." : "Register Source"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from "react";
import { AlertItem, AlertDetail, AlertStatus } from "../../types";
import { fetchAlertDetail, updateAlertStatus } from "../../api/alerts";
import { SeverityBadge } from "../common/SeverityBadge";
import { StatusBadge } from "../common/StatusBadge";
import {
  ShieldAlert,
  X,
  User,
  Globe,
  Layers,
  Database,
  AlertCircle,
  FileText,
  Activity,
  FolderGit2,
} from "lucide-react";
import { escalateAlertToIncident } from "../../api/incidents";

interface AlertInspectionModalProps {
  alert: AlertItem;
  demoMode: boolean;
  onClose: () => void;
  onStatusUpdated?: (updated: AlertDetail) => void;
  onEscalated?: (incidentId: string) => void;
}

export const AlertInspectionModal: React.FC<AlertInspectionModalProps> = ({
  alert,
  demoMode,
  onClose,
  onStatusUpdated,
  onEscalated,
}) => {
  const [detail, setDetail] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState<boolean>(false);
  const [escalating, setEscalating] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"overview" | "evidence" | "events">("overview");

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAlertDetail(alert.id, demoMode);
        if (isMounted) setDetail(data);
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load alert details");
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, [alert.id, demoMode]);

  const handleStatusChange = async (newStatus: AlertStatus) => {
    if (!detail) return;
    setUpdatingStatus(true);
    try {
      const updated = await updateAlertStatus(detail.id, newStatus, demoMode);
      setDetail(updated);
      if (onStatusUpdated) onStatusUpdated(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update alert disposition");
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleEscalate = async () => {
    if (!currentAlert) return;
    setEscalating(true);
    try {
      const inc = await escalateAlertToIncident(currentAlert.id, undefined, demoMode);
      if (onEscalated) {
        onEscalated(inc.id);
      } else {
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to escalate alert");
    } finally {
      setEscalating(false);
    }
  };

  const currentAlert = detail || alert;
  const contextData = (currentAlert.context_data || {}) as Record<string, any>;
  const evidence = (contextData.evidence || {}) as Record<string, any>;
  const affected = (contextData.affected_entities || {}) as Record<string, any>;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-[#121820] border border-[#1E293B] rounded-lg shadow-2xl max-w-3xl w-full flex flex-col max-h-[90vh] overflow-hidden text-slate-100 font-sans">
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-[#1E293B] bg-[#0E131A] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-teal-950/40 border border-teal-800/40 text-teal-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-teal-400">
                  {currentAlert.rule_code || "RULE"}
                </span>
                <span className="text-slate-500">•</span>
                <SeverityBadge severity={currentAlert.severity} />
                <StatusBadge status={currentAlert.status} />
              </div>
              <h2 className="text-base font-semibold text-slate-100 mt-1 line-clamp-1">
                {currentAlert.title}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-[#1A2332] transition-colors"
            title="Close triage modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Triage Disposition Action Bar */}
        <div className="px-5 py-2.5 bg-[#0B0F14] border-b border-[#1E293B] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-mono text-slate-400 font-semibold uppercase text-[11px]">
              Triage Disposition:
            </span>
            <select
              value={currentAlert.status}
              disabled={updatingStatus}
              onChange={(e) => handleStatusChange(e.target.value as AlertStatus)}
              className="bg-[#121820] border border-[#2D3748] rounded px-2.5 py-1 text-slate-200 text-xs font-mono focus:outline-none focus:border-teal-500 cursor-pointer"
            >
              <option value="new">New (Unreviewed)</option>
              <option value="triaged">Triaged (Assessed)</option>
              <option value="investigating">Investigating (In Analysis)</option>
              <option value="closed_false_positive">Closed (False Positive)</option>
              <option value="closed_resolved">Closed (Resolved/Remediated)</option>
            </select>
            {updatingStatus && (
              <span className="text-[10px] text-teal-400 animate-pulse font-mono">
                Updating...
              </span>
            )}
            <button
              onClick={handleEscalate}
              disabled={escalating || currentAlert.status === "escalated"}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-teal-950/60 hover:bg-teal-900/60 border border-teal-700/60 text-teal-300 font-mono text-[11px] font-semibold transition-colors disabled:opacity-50"
            >
              <FolderGit2 className="w-3 h-3" />
              {escalating ? "Escalating..." : currentAlert.status === "escalated" ? "Escalated" : "Escalate to Incident"}
            </button>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 bg-[#121820] p-0.5 rounded border border-[#1E293B] font-mono text-xs">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === "overview"
                  ? "bg-[#1E293B] text-teal-300 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab("evidence")}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === "evidence"
                  ? "bg-[#1E293B] text-teal-300 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Evidence Artifacts
            </button>
            <button
              onClick={() => setActiveTab("events")}
              className={`px-3 py-1 rounded transition-colors ${
                activeTab === "events"
                  ? "bg-[#1E293B] text-teal-300 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Supporting Logs ({detail?.supporting_events?.length || currentAlert.event_count})
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {loading && (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400 font-mono text-xs">
              <Activity className="w-5 h-5 text-teal-400 animate-spin" />
              <span>Loading forensic evidence and supporting telemetry...</span>
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs flex items-center gap-2 font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!loading && activeTab === "overview" && (
            <div className="space-y-4">
              {/* Context Summary */}
              <div className="p-3.5 rounded bg-[#0B0F14] border border-[#1E293B]">
                <h3 className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-teal-400" />
                  Detection Rationale
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {currentAlert.description}
                </p>
              </div>

              {/* Entity Context Matrix */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded bg-[#0B0F14] border border-[#1E293B]">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 uppercase">
                    <Globe className="w-3.5 h-3.5 text-teal-400" />
                    Source Entity
                  </div>
                  <div className="mt-1 font-mono text-xs font-semibold text-slate-100">
                    {currentAlert.source_ip || affected.source_ip || "N/A"}
                  </div>
                </div>

                <div className="p-3 rounded bg-[#0B0F14] border border-[#1E293B]">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 uppercase">
                    <User className="w-3.5 h-3.5 text-teal-400" />
                    Target User
                  </div>
                  <div className="mt-1 font-mono text-xs font-semibold text-slate-100">
                    {affected.user_name || "—"}
                  </div>
                </div>

                <div className="p-3 rounded bg-[#0B0F14] border border-[#1E293B]">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 uppercase">
                    <Layers className="w-3.5 h-3.5 text-teal-400" />
                    Correlated Events
                  </div>
                  <div className="mt-1 font-mono text-xs font-semibold text-teal-400">
                    {currentAlert.event_count} events
                  </div>
                </div>
              </div>

              {/* Fingerprint & Deduplication Metadata */}
              <div className="p-3.5 rounded bg-[#0B0F14] border border-[#1E293B] space-y-2 font-mono text-xs">
                <div className="text-[11px] font-bold text-slate-400 uppercase">
                  Telemetry Metadata
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-500">Deduplication Key: </span>
                    <span className="text-slate-300 break-all">{currentAlert.deduplication_key}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">First Generated: </span>
                    <span className="text-slate-300">
                      {new Date(currentAlert.created_at).toLocaleString()}
                    </span>
                  </div>
                  {contextData.mitre_tactic && (
                    <div>
                      <span className="text-slate-500">MITRE Tactic: </span>
                      <span className="text-teal-400">{contextData.mitre_tactic}</span>
                    </div>
                  )}
                  {contextData.mitre_technique && (
                    <div>
                      <span className="text-slate-500">MITRE Technique: </span>
                      <span className="text-teal-400">{contextData.mitre_technique}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {!loading && activeTab === "evidence" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded bg-[#0B0F14] border border-[#1E293B] space-y-2">
                <div className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-teal-400" />
                  Extracted Evidence Artifacts
                </div>
                <p className="text-xs text-slate-400 font-sans">
                  Deterministic thresholds, sliding time window parameters, and calculated aggregates
                  recorded by the engine at detection time.
                </p>
                <pre className="p-3 bg-[#080B0F] border border-[#1A2332] rounded text-[11px] font-mono text-teal-300/90 overflow-x-auto leading-relaxed">
                  {JSON.stringify(evidence, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {!loading && activeTab === "events" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400 font-sans flex items-center justify-between">
                <span>Supporting events that satisfies rule criteria (immutable chain of custody):</span>
                <span className="font-mono text-teal-400 text-[11px]">
                  {detail?.supporting_events?.length || 0} Records
                </span>
              </div>

              {(!detail?.supporting_events || detail.supporting_events.length === 0) ? (
                <div className="py-8 text-center text-xs text-slate-500 font-mono bg-[#0B0F14] rounded border border-[#1E293B]">
                  No supporting events loaded from archive for this alert instance.
                </div>
              ) : (
                <div className="border border-[#1E293B] rounded overflow-hidden">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#0B0F14] text-[11px] text-slate-400 border-b border-[#1E293B]">
                      <tr>
                        <th className="py-2 px-3">Timestamp (UTC)</th>
                        <th className="py-2 px-3">Action</th>
                        <th className="py-2 px-3">Source IP</th>
                        <th className="py-2 px-3">Dst Port</th>
                        <th className="py-2 px-3">User</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1A2332] bg-[#0E131A]">
                      {detail.supporting_events.map((ev) => (
                        <tr key={ev.id} className="hover:bg-[#141B24]">
                          <td className="py-2 px-3 text-slate-300 text-[11px]">
                            {new Date(ev.timestamp).toISOString().slice(11, 19)}
                          </td>
                          <td className="py-2 px-3 text-slate-200">
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">
                              {ev.event_action}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-teal-400">{ev.source_ip || "—"}</td>
                          <td className="py-2 px-3 text-slate-300">{ev.destination_port ?? "—"}</td>
                          <td className="py-2 px-3 text-slate-300">{ev.user_name || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-[#1E293B] bg-[#0E131A] flex items-center justify-between">
          <div className="text-[11px] text-slate-500 font-mono">
            ID: <span className="text-slate-400">{currentAlert.id}</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-mono font-medium rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
};

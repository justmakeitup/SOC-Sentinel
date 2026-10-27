import React, { useState, useEffect } from "react";
import {
  IncidentItem,
  IncidentDetail,
  IncidentStatus,
  NoteType,
} from "../../types";
import {
  fetchIncidentDetail,
  updateIncident,
  addInvestigationNote,
} from "../../api/incidents";
import { SeverityBadge } from "../common/SeverityBadge";
import { StatusBadge } from "../common/StatusBadge";
import {
  FolderGit2,
  X,
  ShieldAlert,
  AlertCircle,
  Plus,
  Send,
  Lock,
  History,
  CheckCircle2,
} from "lucide-react";

interface IncidentDetailModalProps {
  incident: IncidentItem;
  demoMode: boolean;
  onClose: () => void;
  onIncidentUpdated?: (updated: IncidentDetail) => void;
  onInspectAlert?: (alertId: string) => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incident,
  demoMode,
  onClose,
  onIncidentUpdated,
  onInspectAlert,
}) => {
  const [detail, setDetail] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"timeline" | "alerts" | "containment" | "add_note">("timeline");

  // New Note State
  const [noteType, setNoteType] = useState<NoteType>("analysis");
  const [noteContent, setNoteContent] = useState<string>("");
  const [submittingNote, setSubmittingNote] = useState<boolean>(false);

  // Containment & Lessons Learned Form State
  const [containmentText, setContainmentText] = useState<string>("");
  const [lessonsText, setLessonsText] = useState<string>("");
  const [savingNarrative, setSavingNarrative] = useState<boolean>(false);
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  // Status Change Confirmation Dialog
  const [pendingStatus, setPendingStatus] = useState<IncidentStatus | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchIncidentDetail(incident.id, demoMode);
        if (isMounted) {
          setDetail(data);
          setContainmentText(data.containment_details || "");
          setLessonsText(data.lessons_learned || "");
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load incident dossier");
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, [incident.id, demoMode]);

  const current = detail || (incident as IncidentDetail);

  const handleStatusChangeRequest = (newStatus: IncidentStatus) => {
    if (newStatus === "resolved" || newStatus === "closed") {
      setPendingStatus(newStatus);
    } else {
      executeStatusUpdate(newStatus);
    }
  };

  const executeStatusUpdate = async (newStatus: IncidentStatus) => {
    setPendingStatus(null);
    setUpdating(true);
    try {
      const updated = await updateIncident(
        current.id,
        { status: newStatus },
        demoMode
      );
      setDetail(updated);
      if (onIncidentUpdated) onIncidentUpdated(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    } finally {
      setUpdating(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteContent.trim()) return;

    setSubmittingNote(true);
    try {
      await addInvestigationNote(
        current.id,
        { note_type: noteType, content: noteContent.trim() },
        demoMode
      );
      setNoteContent("");
      // Reload detail to refresh timeline
      const refreshed = await fetchIncidentDetail(current.id, demoMode);
      setDetail(refreshed);
      setActiveTab("timeline");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record investigation note");
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleSaveNarrative = async () => {
    setSavingNarrative(true);
    try {
      const updated = await updateIncident(
        current.id,
        {
          containment_details: containmentText.trim() || undefined,
          lessons_learned: lessonsText.trim() || undefined,
        },
        demoMode
      );
      setDetail(updated);
      if (onIncidentUpdated) onIncidentUpdated(updated);
      setSavedNotice("Containment details and post-mortem notes updated successfully.");
      setTimeout(() => setSavedNotice(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save containment narrative");
    } finally {
      setSavingNarrative(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-[#121820] border border-[#1E293B] rounded-lg shadow-2xl max-w-4xl w-full flex flex-col max-h-[92vh] overflow-hidden text-slate-100 font-sans">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#1E293B] bg-[#0E131A] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded bg-teal-950/60 border border-teal-800/60 text-teal-400">
              <FolderGit2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-teal-400">
                  {current.incident_number}
                </span>
                <span className="text-slate-500">•</span>
                <span className="px-2 py-0.5 rounded font-mono text-[10px] uppercase font-bold bg-slate-800 text-slate-200 border border-slate-700">
                  {current.severity.replace("sev_", "SEV-")}
                </span>
                <StatusBadge status={current.status} />
              </div>
              <h2 className="text-base font-semibold text-slate-100 mt-1 line-clamp-1">
                {current.title}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-[#1A2332] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Controls & Navigation Tabs */}
        <div className="px-5 py-2.5 bg-[#0B0F14] border-b border-[#1E293B] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-mono text-slate-400 font-semibold uppercase text-[11px]">
              Lifecycle Phase:
            </span>
            <select
              value={current.status}
              disabled={updating}
              onChange={(e) => handleStatusChangeRequest(e.target.value as IncidentStatus)}
              className="bg-[#121820] border border-[#2D3748] rounded px-2.5 py-1 text-slate-200 text-xs font-mono focus:outline-none focus:border-teal-500 cursor-pointer"
            >
              <option value="open">Open (Verification)</option>
              <option value="investigating">Investigating (In Analysis)</option>
              <option value="containment">Containment (Isolated)</option>
              <option value="eradication">Eradication (Cleaned)</option>
              <option value="recovery">Recovery (Restoring)</option>
              <option value="resolved">Resolved (Remediated)</option>
              <option value="closed">Closed (Post-Mortem Complete)</option>
            </select>
            {updating && (
              <span className="text-[10px] text-teal-400 animate-pulse font-mono">
                Transitioning...
              </span>
            )}
          </div>

          <div className="flex items-center gap-1 bg-[#121820] p-0.5 rounded border border-[#1E293B] font-mono text-xs">
            <button
              onClick={() => setActiveTab("timeline")}
              className={`px-3 py-1 rounded transition-colors flex items-center gap-1.5 ${
                activeTab === "timeline"
                  ? "bg-[#1E293B] text-teal-300 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Timeline ({detail?.timeline?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("alerts")}
              className={`px-3 py-1 rounded transition-colors flex items-center gap-1.5 ${
                activeTab === "alerts"
                  ? "bg-[#1E293B] text-teal-300 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              Alerts ({detail?.alerts?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("containment")}
              className={`px-3 py-1 rounded transition-colors flex items-center gap-1.5 ${
                activeTab === "containment"
                  ? "bg-[#1E293B] text-teal-300 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Lock className="w-3.5 h-3.5" />
              Containment
            </button>
            <button
              onClick={() => setActiveTab("add_note")}
              className={`px-3 py-1 rounded transition-colors flex items-center gap-1.5 ${
                activeTab === "add_note"
                  ? "bg-[#1E293B] text-teal-300 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Plus className="w-3.5 h-3.5" />
              Add Note
            </button>
          </div>
        </div>

        {/* Confirmation Modal for Resolved / Closed */}
        {pendingStatus && (
          <div className="p-4 bg-amber-950/40 border-b border-amber-800/60 flex items-center justify-between text-xs font-mono text-amber-200">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>
                Confirm transition to <strong>{pendingStatus.toUpperCase()}</strong>? Associated security alerts will be preserved.
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => executeStatusUpdate(pendingStatus)}
                className="px-3 py-1 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold"
              >
                Confirm
              </button>
              <button
                onClick={() => setPendingStatus(null)}
                className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {error && (
            <div className="p-3.5 rounded bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {savedNotice && (
            <div className="p-3.5 rounded bg-teal-950/40 border border-teal-800/60 text-teal-300 text-xs font-mono flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{savedNotice}</span>
            </div>
          )}

          {/* Tab 1: Chronological Timeline */}
          {activeTab === "timeline" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded bg-[#0B0F14] border border-[#1E293B] space-y-2">
                <div className="text-[11px] font-mono text-slate-400 uppercase font-semibold">
                  Executive Incident Summary
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {current.summary}
                </p>
                <div className="pt-2 border-t border-[#1E293B] grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono text-slate-400">
                  <div>
                    LEAD: <span className="text-teal-400">{current.lead_analyst_name || "Unassigned"}</span>
                  </div>
                  <div>
                    CREATED: <span className="text-slate-300">{new Date(current.created_at).toLocaleDateString()}</span>
                  </div>
                  <div>
                    LINKED ALERTS: <span className="text-teal-300 font-bold">{detail?.alerts?.length || 0}</span>
                  </div>
                  <div>
                    TOTAL EVENTS: <span className="text-teal-300 font-bold">{detail?.linked_event_count || 0}</span>
                  </div>
                </div>
              </div>

              {/* Timeline Feed */}
              <div className="space-y-3 font-mono">
                <div className="text-[11px] uppercase font-bold text-slate-400">
                  Chronological Case Activity & Audit History
                </div>

                {loading ? (
                  <div className="py-8 text-center text-xs text-slate-500">
                    Loading chronological activity ledger...
                  </div>
                ) : !detail?.timeline || detail.timeline.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-500 bg-[#0B0F14] rounded border border-[#1E293B]">
                    No historical events recorded for this case.
                  </div>
                ) : (
                  <div className="relative border-l-2 border-[#1E293B] ml-3 pl-4 space-y-4">
                    {detail.timeline.map((item) => (
                      <div key={item.id} className="relative group">
                        <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-[#121820] border-2 border-teal-500" />
                        <div className="p-3 rounded bg-[#0B0F14] border border-[#1E293B] space-y-1">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-bold text-teal-400">{item.title}</span>
                            <span className="text-slate-500 text-[10px]">
                              {new Date(item.timestamp).toLocaleString()}
                            </span>
                          </div>
                          {item.description && (
                            <p className="text-xs text-slate-300 font-sans leading-relaxed">
                              {item.description}
                            </p>
                          )}
                          <div className="text-[10px] text-slate-500">
                            Operator: <span className="text-slate-400">{item.actor_name || "System"}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Linked Alerts */}
          {activeTab === "alerts" && (
            <div className="space-y-3 font-mono text-xs">
              <div className="text-slate-400 text-[11px]">
                Security alerts escalated into this incident case file:
              </div>

              {!detail?.alerts || detail.alerts.length === 0 ? (
                <div className="py-8 text-center text-slate-500 bg-[#0B0F14] rounded border border-[#1E293B]">
                  No security alerts currently linked to this incident.
                </div>
              ) : (
                <div className="border border-[#1E293B] rounded overflow-hidden">
                  <table className="w-full text-left">
                    <thead className="bg-[#0B0F14] text-[11px] text-slate-400 border-b border-[#1E293B]">
                      <tr>
                        <th className="py-2.5 px-3">Severity</th>
                        <th className="py-2.5 px-3">Title</th>
                        <th className="py-2.5 px-3">Source Entity</th>
                        <th className="py-2.5 px-3">Events</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1A2332] bg-[#0E131A]">
                      {detail.alerts.map((alt) => (
                        <tr key={alt.id} className="hover:bg-[#141B24]">
                          <td className="py-2.5 px-3">
                            <SeverityBadge severity={alt.severity} size="sm" />
                          </td>
                          <td className="py-2.5 px-3 text-slate-200">{alt.title}</td>
                          <td className="py-2.5 px-3 text-teal-400">
                            {alt.source_ip || (alt.context_data?.affected_entities as any)?.source_ip || "—"}
                          </td>
                          <td className="py-2.5 px-3 text-slate-300 font-bold">{alt.event_count}</td>
                          <td className="py-2.5 px-3 text-right">
                            <button
                              onClick={() => onInspectAlert?.(alt.id)}
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-teal-300 text-[10px] border border-slate-700"
                            >
                              Inspect Alert
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Containment & Remediation Narrative */}
          {activeTab === "containment" && (
            <div className="space-y-4 font-sans text-xs">
              <div className="space-y-1.5">
                <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
                  Containment & Mitigation Actions Taken:
                </label>
                <textarea
                  rows={4}
                  value={containmentText}
                  onChange={(e) => setContainmentText(e.target.value)}
                  placeholder="Document switch port isolations, firewall drop rules, credential revocations, or host quarantines..."
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-3 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
                  Post-Mortem Lessons Learned & Remediation:
                </label>
                <textarea
                  rows={4}
                  value={lessonsText}
                  onChange={(e) => setLessonsText(e.target.value)}
                  placeholder="Document architectural gaps, policy updates, or rule tuning items to mitigate future recurrence..."
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-3 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleSaveNarrative}
                  disabled={savingNarrative}
                  className="px-4 py-1.5 rounded bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold font-mono text-xs transition-colors"
                >
                  {savingNarrative ? "Saving Narrative..." : "Save Containment Chronicle"}
                </button>
              </div>
            </div>
          )}

          {/* Tab 4: Add Investigation Note Form */}
          {activeTab === "add_note" && (
            <form onSubmit={handleAddNote} className="space-y-4 font-sans text-xs">
              <div className="p-3 rounded bg-[#0B0F14] border border-[#1E293B] space-y-3">
                <div className="flex items-center justify-between">
                  <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
                    Forensic Classification:
                  </label>
                  <select
                    value={noteType}
                    onChange={(e) => setNoteType(e.target.value as NoteType)}
                    className="bg-[#121820] border border-[#2D3748] rounded px-2.5 py-1 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
                  >
                    <option value="analysis">Analysis (Host/Network telemetry)</option>
                    <option value="containment_action">Containment Action (Quarantine/Block)</option>
                    <option value="forensic_evidence">Forensic Evidence (Hashes/Memory dumps)</option>
                    <option value="communication">Communication (Stakeholder update)</option>
                    <option value="general">General Observation</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
                    Forensic Journal Content:
                  </label>
                  <textarea
                    rows={5}
                    value={noteContent}
                    onChange={(e) => setNoteContent(e.target.value)}
                    placeholder="Enter commands run, IOC hashes, host observations, or containment findings..."
                    className="w-full bg-[#121820] border border-[#1E293B] rounded p-3 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
                    required
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={submittingNote || !noteContent.trim()}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold font-mono text-xs transition-colors disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {submittingNote ? "Recording Note..." : "Record Forensic Note"}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-[#1E293B] bg-[#0E131A] flex items-center justify-between">
          <div className="text-[11px] text-slate-500 font-mono">
            CASE ID: <span className="text-slate-400">{current.id}</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-mono font-medium rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
          >
            Close Case Review
          </button>
        </div>
      </div>
    </div>
  );
};

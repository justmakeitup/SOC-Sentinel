import React, { useState } from "react";
import { IncidentSeverity, IncidentDetail } from "../../types";
import { createIncident } from "../../api/incidents";
import { FolderGit2, X, Plus, AlertCircle } from "lucide-react";

interface CreateIncidentModalProps {
  demoMode: boolean;
  initialAlertId?: string;
  onClose: () => void;
  onCreated: (incident: IncidentDetail) => void;
}

export const CreateIncidentModal: React.FC<CreateIncidentModalProps> = ({
  demoMode,
  initialAlertId,
  onClose,
  onCreated,
}) => {
  const [title, setTitle] = useState<string>("");
  const [summary, setSummary] = useState<string>("");
  const [severity, setSeverity] = useState<IncidentSeverity>("sev_3_medium");
  const [containment, setContainment] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !summary.trim()) {
      setError("Title and executive narrative summary are required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const created = await createIncident(
        {
          title: title.trim(),
          summary: summary.trim(),
          severity,
          containment_details: containment.trim() || undefined,
          alert_ids: initialAlertId ? [initialAlertId] : undefined,
        },
        demoMode
      );
      onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to provision incident case");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-[#121820] border border-[#1E293B] rounded-lg shadow-2xl max-w-xl w-full p-6 text-slate-100 font-sans space-y-5">
        <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded bg-teal-950/60 border border-teal-800/60 text-teal-400">
              <FolderGit2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">
                Declare Security Incident Case
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                NIST SP 800-61 Rev 2 Formal Investigation Dossier
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded bg-rose-950/30 border border-rose-900/60 text-rose-300 text-xs font-mono flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
          <div className="space-y-1">
            <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
              Incident Case Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Active Directory Kerberoasting Compromise"
              className="w-full bg-[#0B0F14] border border-[#1E293B] rounded px-3 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
                Severity Impact Rating *
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value as IncidentSeverity)}
                className="w-full bg-[#0B0F14] border border-[#1E293B] rounded px-3 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
              >
                <option value="sev_1_critical">Sev-1 Critical (Enterprise Compromise)</option>
                <option value="sev_2_high">Sev-2 High (Lateral Movement/Priv Escalation)</option>
                <option value="sev_3_medium">Sev-3 Medium (Contained Malware/Unauthorized Access)</option>
                <option value="sev_4_low">Sev-4 Low (Policy Violation/Suspicious Probe)</option>
              </select>
            </div>

            {initialAlertId && (
              <div className="space-y-1">
                <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
                  Linked Trigger Alert
                </label>
                <div className="w-full bg-[#0B0F14] border border-[#1E293B] rounded px-3 py-2 text-teal-400 font-mono text-xs truncate">
                  ID: {initialAlertId}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-1">
            <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
              Executive Incident Summary *
            </label>
            <textarea
              rows={3}
              required
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="Provide context regarding the attack vector, affected systems, and business impact..."
              className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-3 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="space-y-1">
            <label className="font-mono text-[11px] text-slate-400 font-bold uppercase">
              Immediate Containment Actions (Optional)
            </label>
            <textarea
              rows={2}
              value={containment}
              onChange={(e) => setContainment(e.target.value)}
              placeholder="e.g., VLAN isolation, user token revocation, firewall drop..."
              className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-3 text-slate-200 font-mono text-xs focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-[#1E293B]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold font-mono text-xs disabled:opacity-50"
            >
              <Plus className="w-3.5 h-3.5" />
              {submitting ? "Declaring Case..." : "Declare Incident"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

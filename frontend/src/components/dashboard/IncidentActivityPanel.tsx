import React, { useState } from "react";
import {
  FolderGit2,
  UserCheck,
  Clock,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";
import { IncidentItem, PaginatedResponse } from "../../types";
import { SeverityBadge } from "../common/SeverityBadge";

interface IncidentActivityPanelProps {
  incidentsResponse: PaginatedResponse<IncidentItem> | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onFilterChange: (statusFilter: string) => void;
  onSelectIncident?: (incident: IncidentItem) => void;
  onEnableDemo?: () => void;
}

export const IncidentActivityPanel: React.FC<IncidentActivityPanelProps> = ({
  incidentsResponse,
  loading,
  error,
  onRefresh,
  onFilterChange,
  onSelectIncident,
  onEnableDemo,
}) => {
  const [activeTab, setActiveTab] = useState<string>("all");

  const incidents = incidentsResponse?.items || [];

  const handleTabClick = (tab: string) => {
    setActiveTab(tab);
    onFilterChange(tab);
  };

  const formatNistStatus = (status: string) => {
    const formatted = status.replace(/_/g, " ").toUpperCase();
    let badgeColor = "bg-slate-800 text-slate-300 border-slate-700";

    if (status === "open") {
      badgeColor = "bg-rose-950/60 text-rose-300 border-rose-800/80";
    } else if (status === "containment") {
      badgeColor = "bg-amber-950/60 text-amber-300 border-amber-800/80";
    } else if (status === "eradication" || status === "recovery") {
      badgeColor = "bg-teal-950/60 text-teal-300 border-teal-800/80";
    } else if (status === "closed") {
      badgeColor = "bg-emerald-950/60 text-emerald-300 border-emerald-800/80";
    }

    return (
      <span
        className={`px-1.5 py-0.5 text-[10px] font-mono rounded border ${badgeColor} font-medium`}
      >
        {formatted}
      </span>
    );
  };

  const formatTimeAgo = (isoString: string) => {
    try {
      const diffMs = Date.now() - new Date(isoString).getTime();
      const mins = Math.floor(diffMs / 60000);
      if (mins < 1) return "Just now";
      if (mins < 60) return `${mins}m ago`;
      const hours = Math.floor(mins / 60);
      if (hours < 24) return `${hours}h ago`;
      const days = Math.floor(hours / 24);
      return `${days}d ago`;
    } catch {
      return isoString;
    }
  };

  return (
    <div className="rounded-lg bg-[#121820] border border-[#1E293B] overflow-hidden flex flex-col justify-between">
      {/* Header and Filter Tabs */}
      <div className="p-4 border-b border-[#1E293B] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FolderGit2 className="w-4 h-4 text-teal-400" />
            <h3 className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
              Incident Response Case Files
            </h3>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-teal-300 border border-slate-700">
            NIST SP 800-61
          </span>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center gap-1 font-mono text-[11px] border-b border-[#1E293B] pb-1">
          {[
            { id: "all", label: "All Cases" },
            { id: "containment", label: "Containment" },
            { id: "recovery", label: "Recovery" },
            { id: "closed", label: "Closed" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`px-2.5 py-1 rounded transition-colors ${
                activeTab === tab.id
                  ? "bg-teal-950 text-teal-300 border border-teal-800 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Case List Body */}
      <div className="p-3 divide-y divide-[#1E293B] min-h-[220px]">
        {error ? (
          <div className="py-10 text-center space-y-2">
            <AlertTriangle className="w-6 h-6 text-rose-500 mx-auto" />
            <div className="text-xs font-mono text-rose-300">
              Failed to query incidents
            </div>
            <button
              onClick={onRefresh}
              className="px-2.5 py-1 text-xs font-mono rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
            >
              Retry
            </button>
          </div>
        ) : loading ? (
          <div className="space-y-3 py-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-slate-800/40 rounded animate-pulse" />
            ))}
          </div>
        ) : incidents.length === 0 ? (
          <div className="py-10 text-center space-y-2">
            <FolderGit2 className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-xs font-mono text-slate-300 font-medium">
              No Active Case Files
            </div>
            <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
              Incidents are declared when critical alerts or correlated threat chains require coordinated response and containment.
            </p>
            {onEnableDemo && (
              <button
                onClick={onEnableDemo}
                className="mt-2 inline-flex items-center gap-1.5 text-xs font-mono text-teal-400 hover:text-teal-300 underline underline-offset-4"
              >
                Inspect sample incident cases →
              </button>
            )}
          </div>
        ) : (
          incidents.map((inc) => (
            <div
              key={inc.id}
              onClick={() => onSelectIncident?.(inc)}
              className="py-3 px-2 hover:bg-slate-900/40 rounded transition-colors cursor-pointer group space-y-2"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-teal-400">
                    {inc.incident_number}
                  </span>
                  <SeverityBadge severity={inc.severity} size="sm" />
                </div>
                {formatNistStatus(inc.status)}
              </div>

              <div className="text-xs font-semibold text-slate-200 group-hover:text-teal-300 transition-colors line-clamp-1">
                {inc.title}
              </div>

              <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                {inc.summary}
              </p>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1">
                <div className="flex items-center gap-1.5 text-slate-300">
                  <UserCheck className="w-3 h-3 text-teal-500" />
                  <span>{inc.lead_analyst_name || "Unassigned"}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <span>{formatTimeAgo(inc.updated_at)}</span>
                  <ChevronRight className="w-3 h-3 text-slate-600 group-hover:text-teal-400 ml-1 transition-colors" />
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-[#1E293B] bg-[#0E141D] text-[11px] font-mono text-slate-400 flex items-center justify-between">
        <span>INVESTIGATION PLAYBOOKS:</span>
        <span className="text-teal-400 font-medium">CONTAINMENT READY</span>
      </div>
    </div>
  );
};

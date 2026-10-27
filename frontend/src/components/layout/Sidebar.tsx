import React from "react";
import {
  Activity,
  Radio,
  FileCode,
  ShieldAlert,
  FolderGit2,
  ScrollText,
  Layers,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: React.FC<{ className?: string }>;
  badge?: string;
  status: "active" | "planned";
}

const NAV_ITEMS: NavItem[] = [
  { id: "overview", label: "System Health & Foundation", icon: Activity, status: "active" },
  { id: "ingestion", label: "Log Sources & Ingestion", icon: Radio, badge: "Phase 2", status: "planned" },
  { id: "events", label: "Normalized Telemetry", icon: Layers, badge: "Phase 2", status: "planned" },
  { id: "rules", label: "Detection Engineering", icon: FileCode, badge: "Phase 3", status: "planned" },
  { id: "alerts", label: "Security Alerts", icon: ShieldAlert, badge: "Phase 3", status: "planned" },
  { id: "incidents", label: "Incident Management", icon: FolderGit2, badge: "Phase 4", status: "planned" },
  { id: "audit", label: "Governance & Audit Trail", icon: ScrollText, badge: "Phase 4", status: "planned" },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-[#1E293B] bg-[#0E141D] flex flex-col justify-between select-none">
      <div className="p-3 space-y-1">
        <div className="px-3 py-2 text-[11px] font-mono tracking-wider text-slate-400 uppercase">
          SOC Navigation
        </div>
        <nav className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = item.status === "active";

            return (
              <div
                key={item.id}
                className={`flex items-center justify-between px-3 py-2 rounded text-xs transition-colors ${
                  isActive
                    ? "bg-teal-950/60 text-teal-300 font-medium border border-teal-800/40"
                    : "text-slate-400 opacity-60 cursor-not-allowed hover:bg-slate-900/40"
                }`}
                title={
                  isActive
                    ? "Active Foundation Module"
                    : `Scheduled for implementation in ${item.badge}`
                }
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 ${isActive ? "text-teal-400" : "text-slate-400"}`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800/80 text-slate-400 border border-slate-700">
                    {item.badge}
                  </span>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Architecture Status Footer */}
      <div className="p-3 border-t border-[#1E293B] text-[11px] font-mono text-slate-400 space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span>PIPELINE:</span>
          <span className="text-teal-400">NORMALIZED</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span>SCHEMA:</span>
          <span className="text-slate-300">V1 (ALEMBIC)</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span>TAXONOMY:</span>
          <span className="text-slate-300">ECS / OSSEM</span>
        </div>
      </div>
    </aside>
  );
};

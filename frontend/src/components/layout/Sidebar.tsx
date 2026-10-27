import React from "react";
import {
  Activity,
  Layers,
  ShieldAlert,
  FolderGit2,
  Radio,
  FileCode,
  FileSpreadsheet,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { NavView } from "../../types";

interface NavItem {
  id: NavView;
  label: string;
  icon: React.FC<{ className?: string }>;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "events", label: "Events", icon: Layers, badge: "Live" },
  { id: "alerts", label: "Alerts", icon: ShieldAlert, badge: "Queue" },
  { id: "incidents", label: "Incidents", icon: FolderGit2, badge: "Cases" },
  { id: "sources", label: "Log Sources", icon: Radio },
  { id: "rules", label: "Detection Rules", icon: FileCode },
  { id: "reports", label: "Reports", icon: FileSpreadsheet },
  { id: "settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  currentView: NavView;
  onNavigate: (view: NavView) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onNavigate,
  collapsed,
  onToggleCollapse,
}) => {
  return (
    <aside
      className={`border-r border-[#1E293B] bg-[#0E141D] flex flex-col justify-between transition-all duration-300 select-none ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      <div className="p-3 space-y-1">
        {/* Collapse Toggle Bar */}
        <div className="flex items-center justify-between px-2 py-1 mb-2">
          {!collapsed && (
            <span className="text-[11px] font-mono tracking-wider text-slate-400 uppercase">
              Operations Center
            </span>
          )}
          <button
            onClick={onToggleCollapse}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors mx-auto"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4 text-teal-400" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-slate-400" />
            )}
          </button>
        </div>

        {/* Navigation Item List */}
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center rounded text-xs transition-colors group relative ${
                  collapsed ? "justify-center p-2.5" : "justify-between px-3 py-2"
                } ${
                  isActive
                    ? "bg-teal-950/70 text-teal-300 font-semibold border border-teal-800/60"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive
                        ? "text-teal-400"
                        : "text-slate-400 group-hover:text-slate-200"
                    }`}
                  />
                  {!collapsed && <span>{item.label}</span>}
                </div>

                {!collapsed && item.badge && (
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                      isActive
                        ? "bg-teal-900/60 text-teal-200 border-teal-700"
                        : "bg-slate-800 text-slate-400 border-slate-700"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}

                {/* Collapsed Tooltip */}
                {collapsed && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-slate-900 border border-slate-700 text-slate-200 text-xs font-mono rounded opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 whitespace-nowrap shadow-lg">
                    {item.label}
                  </div>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Subsystem Status (hidden when collapsed) */}
      {!collapsed ? (
        <div className="p-3 border-t border-[#1E293B] text-[11px] font-mono text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>PIPELINE:</span>
            <span className="text-teal-400 font-medium">ECS / OSSEM</span>
          </div>
          <div className="flex items-center justify-between">
            <span>DEDUPLICATION:</span>
            <span className="text-slate-300">ACTIVE (SHA-256)</span>
          </div>
          <div className="flex items-center justify-between">
            <span>FRAMEWORK:</span>
            <span className="text-slate-300">NIST SP 800-61</span>
          </div>
        </div>
      ) : (
        <div className="p-2 border-t border-[#1E293B] flex justify-center text-teal-500 text-xs font-mono">
          <div className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" title="Pipeline Active" />
        </div>
      )}
    </aside>
  );
};

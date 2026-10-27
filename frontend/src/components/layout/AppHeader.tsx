import React, { useState, useEffect, useRef } from "react";
import {
  Shield,
  Clock,
  Search,
  ChevronDown,
  Menu,
  ToggleLeft,
  ToggleRight,
  Check,
} from "lucide-react";
import { StatusBadge } from "../common/StatusBadge";
import { API_BASE_URL } from "../../api/client";

interface AppHeaderProps {
  backendOnline: boolean;
  environment: string;
  latencyMs?: number | null;
  demoMode: boolean;
  onToggleDemoMode: () => void;
  onOpenSearch: () => void;
  onToggleMobileSidebar: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  backendOnline,
  environment,
  latencyMs,
  demoMode,
  onToggleDemoMode,
  onOpenSearch,
  onToggleMobileSidebar,
}) => {
  const [utcTime, setUtcTime] = useState<string>("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Close user menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="h-14 border-b border-[#1E293B] bg-[#0E141D] px-4 flex items-center justify-between select-none z-30 relative">
      {/* Left: Mobile Toggle + Brand */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="md:hidden p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          aria-label="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded bg-teal-950/80 border border-teal-700/60 flex items-center justify-center text-teal-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-wide text-slate-100 uppercase">
                Sentinel
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                SOC v0.1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono leading-none hidden sm:block">
              Security Monitoring & Incident Response Platform
            </p>
          </div>
        </div>
      </div>

      {/* Center: Global Search Trigger */}
      <div className="hidden lg:flex items-center flex-1 max-w-md mx-6">
        <button
          onClick={onOpenSearch}
          className="w-full flex items-center justify-between px-3 py-1.5 rounded bg-[#0B0F14] border border-[#1E293B] hover:border-slate-700 text-slate-400 text-xs font-mono transition-colors"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <span>Search telemetry, rules, or press Ctrl+K...</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-slate-300">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* UTC Clock */}
        <div className="hidden xl:flex items-center gap-1.5 text-xs font-mono text-slate-400">
          <Clock className="w-3.5 h-3.5 text-teal-500" />
          <span>{utcTime || "SYNCHRONIZING..."}</span>
        </div>

        {/* Development Demo Mode Toggle */}
        <div className="flex items-center gap-1.5 font-mono text-xs">
          <button
            onClick={onToggleDemoMode}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border transition-colors ${
              demoMode
                ? "bg-amber-950/80 text-amber-300 border-amber-600/80 font-bold"
                : "bg-slate-800/60 text-slate-400 border-slate-700 hover:text-slate-200"
            }`}
            title="Toggle between live backend queries and development demo mock telemetry"
          >
            {demoMode ? (
              <ToggleRight className="w-4 h-4 text-amber-400" />
            ) : (
              <ToggleLeft className="w-4 h-4 text-slate-500" />
            )}
            <span className="text-[11px] uppercase tracking-wider">
              {demoMode ? "Demo Mode (ON)" : "Demo Mode (OFF)"}
            </span>
          </button>
        </div>

        {/* Backend Connectivity Status */}
        <div className="hidden sm:flex items-center gap-1.5">
          <StatusBadge
            status={backendOnline ? "connected" : "disconnected"}
            label={backendOnline ? (latencyMs ? `${latencyMs}ms` : "API Live") : "Offline"}
            size="sm"
          />
        </div>

        {/* User Profile Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setUserMenuOpen((prev) => !prev)}
            className="flex items-center gap-2 p-1 pl-2 rounded hover:bg-slate-800/80 border border-transparent hover:border-slate-700 transition-colors"
            aria-haspopup="true"
            aria-expanded={userMenuOpen}
          >
            <div className="w-6 h-6 rounded-full bg-teal-950 border border-teal-700 flex items-center justify-center text-teal-300 text-xs font-mono font-bold">
              AM
            </div>
            <div className="text-left hidden md:block leading-tight">
              <div className="text-xs font-semibold text-slate-200">Alex Mercer</div>
              <div className="text-[10px] text-teal-400 font-mono">Tier-1 Analyst</div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* Dropdown Menu */}
          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-[#121820] border border-[#1E293B] rounded-lg shadow-xl p-3 space-y-2 z-50 font-mono text-xs">
              <div className="border-b border-[#1E293B] pb-2">
                <div className="font-semibold text-slate-100">Alex Mercer</div>
                <div className="text-slate-400 text-[11px]">analyst@sentinel.sec</div>
                <div className="flex items-center gap-1.5 mt-1 text-[10px] text-teal-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                  <span>Active Shift (08:00 - 16:00 UTC)</span>
                </div>
              </div>

              <div className="space-y-1 text-slate-300 text-[11px]">
                <div className="flex items-center justify-between py-1">
                  <span>RBAC Role:</span>
                  <span className="text-teal-400">ANALYST_TIER_1</span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span>MFA Status:</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <Check className="w-3 h-3" /> Hardware Token
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span>Target API:</span>
                  <span className="text-slate-400 truncate max-w-[120px]" title={API_BASE_URL}>
                    {API_BASE_URL}
                  </span>
                </div>
              </div>

              <div className="border-t border-[#1E293B] pt-2 flex items-center justify-between text-[11px]">
                <span className="text-slate-400">Env: {environment}</span>
                <span className="text-teal-400">Sentinel SOC</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

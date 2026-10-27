import React, { useState, useEffect } from "react";
import { Shield, Clock, Server } from "lucide-react";
import { StatusBadge } from "../common/StatusBadge";
import { API_BASE_URL } from "../../api/client";

interface AppHeaderProps {
  backendOnline: boolean;
  environment: string;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  backendOnline,
  environment,
}) => {
  const [utcTime, setUtcTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-[#1E293B] bg-[#0E141D] px-4 flex items-center justify-between select-none">
      {/* Brand & Platform Identity */}
      <div className="flex items-center gap-3">
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
          <p className="text-[11px] text-slate-400 font-mono leading-none">
            Security Monitoring & Incident Response Platform
          </p>
        </div>
      </div>

      {/* Center Operational Metadata */}
      <div className="hidden md:flex items-center gap-4 text-xs font-mono text-slate-400">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-teal-500" />
          <span>{utcTime || "SYNCHRONIZING..."}</span>
        </div>
        <div className="h-3 w-[1px] bg-slate-800" />
        <div className="flex items-center gap-1.5" title={`API URL: ${API_BASE_URL}`}>
          <Server className="w-3.5 h-3.5 text-teal-500" />
          <span className="text-slate-300">API:</span>
          <span className="text-slate-400 max-w-[200px] truncate">{API_BASE_URL}</span>
        </div>
      </div>

      {/* Right Status Badges */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-slate-400 hidden sm:inline">ENV:</span>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800/80 text-teal-300 border border-slate-700 uppercase">
          {environment}
        </span>
        <StatusBadge
          status={backendOnline ? "connected" : "disconnected"}
          label={backendOnline ? "API Online" : "API Offline"}
          size="sm"
        />
      </div>
    </header>
  );
};

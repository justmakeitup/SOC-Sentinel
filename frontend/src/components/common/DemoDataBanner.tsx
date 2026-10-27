import React from "react";
import { AlertCircle, X } from "lucide-react";

interface DemoDataBannerProps {
  onDisable: () => void;
}

export const DemoDataBanner: React.FC<DemoDataBannerProps> = ({ onDisable }) => {
  return (
    <div
      role="alert"
      className="bg-amber-950/60 border border-amber-600/60 text-amber-200 px-4 py-2 rounded-lg flex items-center justify-between gap-3 text-xs font-mono"
    >
      <div className="flex items-center gap-2.5">
        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
        <div>
          <span className="font-bold text-amber-300 mr-2 uppercase tracking-wide">
            [DEVELOPMENT DEMO TELEMETRY ACTIVE]
          </span>
          <span className="text-amber-200/90 hidden sm:inline">
            Rendering demonstration metrics, sample alerts, and simulated case files for UI inspection.
          </span>
        </div>
      </div>
      <button
        onClick={onDisable}
        className="flex items-center gap-1 px-2 py-1 rounded bg-amber-900/60 hover:bg-amber-800 text-amber-100 border border-amber-700/80 transition-colors text-[11px]"
        title="Switch back to live backend data"
      >
        <span>Disable Demo Mode</span>
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};

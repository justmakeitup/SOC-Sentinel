import React from "react";
import { LucideIcon, ArrowLeft } from "lucide-react";

interface GenericModuleViewProps {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  badge: string;
  description: string;
  architectureDetails: { label: string; value: string }[];
  onBackToOverview: () => void;
  demoMode: boolean;
}

export const GenericModuleView: React.FC<GenericModuleViewProps> = ({
  title,
  subtitle,
  icon: Icon,
  badge,
  description,
  architectureDetails,
  onBackToOverview,
}) => {
  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1E293B]">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToOverview}
            className="p-1.5 rounded bg-slate-800 text-slate-300 hover:text-teal-300 border border-slate-700 transition-colors"
            title="Back to Overview"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="p-2 rounded bg-slate-800/80 text-teal-400 border border-slate-700">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-100">{title}</h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
                {badge}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">{subtitle}</p>
          </div>
        </div>
      </div>

      {/* Description Card */}
      <div className="p-5 rounded-lg bg-[#121820] border border-[#1E293B] space-y-4">
        <p className="text-sm text-slate-300 leading-relaxed font-sans">{description}</p>

        {/* Architecture Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
          {architectureDetails.map((detail, idx) => (
            <div
              key={idx}
              className="p-3 rounded bg-[#0B0F14] border border-[#1E293B] font-mono text-xs space-y-1"
            >
              <div className="text-[10px] text-slate-400 uppercase tracking-wider">{detail.label}</div>
              <div className="text-teal-300 font-semibold">{detail.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

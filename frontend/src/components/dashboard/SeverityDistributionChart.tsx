import React from "react";
import { PieChart, ShieldAlert } from "lucide-react";
import { SeverityDistribution } from "../../types";

interface SeverityDistributionChartProps {
  distribution: SeverityDistribution;
  loading?: boolean;
}

export const SeverityDistributionChart: React.FC<SeverityDistributionChartProps> = ({
  distribution,
  loading = false,
}) => {
  const tiers = [
    { key: "critical", label: "Critical", color: "bg-rose-500", text: "text-rose-400" },
    { key: "high", label: "High", color: "bg-orange-500", text: "text-orange-400" },
    { key: "medium", label: "Medium", color: "bg-amber-500", text: "text-amber-400" },
    { key: "low", label: "Low", color: "bg-teal-500", text: "text-teal-400" },
    { key: "informational", label: "Informational", color: "bg-sky-500", text: "text-sky-400" },
  ];

  const total = tiers.reduce((acc, t) => acc + (distribution[t.key] || 0), 0);

  return (
    <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] flex flex-col justify-between">
      <div className="flex items-center justify-between pb-3 border-b border-[#1E293B]">
        <div className="flex items-center gap-2">
          <PieChart className="w-4 h-4 text-teal-400" />
          <span className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
            Alert Severity Profile
          </span>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Total: <span className="text-slate-200 font-semibold">{total.toLocaleString()}</span>
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {loading ? (
          <div className="space-y-3 py-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="space-y-1">
                <div className="h-3 w-full bg-slate-800/60 animate-pulse rounded" />
              </div>
            ))}
          </div>
        ) : total === 0 ? (
          <div className="py-8 text-center space-y-2">
            <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-xs font-mono text-slate-300 font-medium">
              No Active Alerts Recorded
            </p>
            <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
              Severity breakdown will populate automatically once correlation rules trigger triage alerts.
            </p>
          </div>
        ) : (
          tiers.map((t) => {
            const count = distribution[t.key] || 0;
            const percentage = total > 0 ? Math.round((count / total) * 100) : 0;

            return (
              <div key={t.key} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${t.color}`} />
                    <span className="text-slate-300 capitalize">{t.label}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="text-slate-400">{percentage}%</span>
                    <span className={`font-semibold ${t.text}`}>{count.toLocaleString()}</span>
                  </div>
                </div>
                {/* Visual Progress Bar */}
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${t.color} rounded-full transition-all duration-500`}
                    style={{ width: `${percentage}%` }}
                    role="progressbar"
                    aria-valuenow={count}
                    aria-valuemin={0}
                    aria-valuemax={total}
                    aria-label={`${t.label} alerts`}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Aggregate Ratio Footer */}
      <div className="mt-4 pt-3 border-t border-[#1E293B] text-[11px] font-mono text-slate-400 flex items-center justify-between">
        <span>CRITICAL/HIGH RATIO:</span>
        <span className="text-rose-400 font-medium">
          {total > 0
            ? `${Math.round(
                (((distribution.critical || 0) + (distribution.high || 0)) / total) * 100
              )}%`
            : "0%"}
        </span>
      </div>
    </div>
  );
};

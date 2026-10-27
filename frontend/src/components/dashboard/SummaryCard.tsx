import React from "react";
import { LucideIcon } from "lucide-react";

interface SummaryCardProps {
  title: string;
  value: number | string;
  subtext?: string;
  icon: LucideIcon;
  variant?: "default" | "critical" | "warning" | "teal";
  loading?: boolean;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  subtext,
  icon: Icon,
  variant = "default",
  loading = false,
}) => {
  const variantStyles = {
    default: {
      border: "border-[#1E293B]",
      iconBg: "bg-slate-800/80 text-slate-300 border-slate-700",
      glow: "hover:border-slate-700",
      accent: "text-slate-100",
    },
    critical: {
      border: "border-rose-900/60",
      iconBg: "bg-rose-950/80 text-rose-400 border-rose-800/80",
      glow: "hover:border-rose-700",
      accent: "text-rose-300",
    },
    warning: {
      border: "border-amber-900/60",
      iconBg: "bg-amber-950/80 text-amber-400 border-amber-800/80",
      glow: "hover:border-amber-700",
      accent: "text-amber-300",
    },
    teal: {
      border: "border-teal-900/60",
      iconBg: "bg-teal-950/80 text-teal-400 border-teal-800/80",
      glow: "hover:border-teal-700",
      accent: "text-teal-300",
    },
  }[variant];

  return (
    <div
      className={`p-4 rounded-lg bg-[#121820] border ${variantStyles.border} ${variantStyles.glow} transition-colors flex flex-col justify-between`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono font-medium tracking-wide text-slate-400 uppercase">
          {title}
        </span>
        <div className={`p-2 rounded border ${variantStyles.iconBg}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-3">
        {loading ? (
          <div className="h-8 w-24 bg-slate-800/60 animate-pulse rounded my-1" />
        ) : (
          <div
            className={`text-2xl font-bold font-mono tracking-tight ${variantStyles.accent}`}
          >
            {typeof value === "number" ? value.toLocaleString() : value}
          </div>
        )}
        {subtext && (
          <p className="text-[11px] text-slate-400 font-mono mt-1 flex items-center gap-1.5">
            {subtext}
          </p>
        )}
      </div>
    </div>
  );
};

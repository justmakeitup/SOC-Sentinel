import React from "react";
import { RuleSeverity, IncidentSeverity } from "../../types";

interface SeverityBadgeProps {
  severity: RuleSeverity | IncidentSeverity | string;
  size?: "sm" | "md";
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  size = "md",
}) => {
  const norm = severity.toLowerCase().replace("sev_", "").replace(/_\d_/, "_");

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
  let dotColor = "bg-slate-400";
  let label = severity;

  if (norm.includes("critical") || norm.includes("1_critical")) {
    colorClasses = "bg-rose-950/70 text-rose-300 border-rose-800/80";
    dotColor = "bg-rose-500";
    label = "CRITICAL";
  } else if (norm.includes("high") || norm.includes("2_high")) {
    colorClasses = "bg-orange-950/70 text-orange-300 border-orange-800/80";
    dotColor = "bg-orange-400";
    label = "HIGH";
  } else if (norm.includes("medium") || norm.includes("3_medium")) {
    colorClasses = "bg-amber-950/70 text-amber-300 border-amber-800/80";
    dotColor = "bg-amber-400";
    label = "MEDIUM";
  } else if (norm.includes("low") || norm.includes("4_low")) {
    colorClasses = "bg-teal-950/70 text-teal-300 border-teal-800/80";
    dotColor = "bg-teal-400";
    label = "LOW";
  } else if (norm.includes("info")) {
    colorClasses = "bg-sky-950/70 text-sky-300 border-sky-800/80";
    dotColor = "bg-sky-400";
    label = "INFO";
  }

  const sizeClasses =
    size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-medium rounded border ${colorClasses} ${sizeClasses} select-none`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />
      <span className="uppercase tracking-wider">{label}</span>
    </span>
  );
};

import React from "react";
import { AlertStatus } from "../../types";

export type BaseSystemStatus =
  | "healthy"
  | "connected"
  | "degraded"
  | "disconnected"
  | "error"
  | "operational"
  | "critical";

interface StatusBadgeProps {
  status: BaseSystemStatus | AlertStatus | string;
  label?: string;
  size?: "sm" | "md";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = "md",
}) => {
  const s = status.toLowerCase();

  let colorStyles = "bg-slate-800 text-slate-300 border-slate-700";
  let dotStyles = "bg-slate-400";

  if (s === "healthy" || s === "connected" || s === "operational" || s === "closed_resolved") {
    colorStyles = "bg-emerald-950/60 text-emerald-300 border-emerald-800/80";
    dotStyles = "bg-emerald-400";
  } else if (s === "degraded" || s === "new") {
    colorStyles = "bg-amber-950/60 text-amber-300 border-amber-800/80";
    dotStyles = "bg-amber-400";
  } else if (s === "triaged" || s === "investigating") {
    colorStyles = "bg-teal-950/60 text-teal-300 border-teal-800/80";
    dotStyles = "bg-teal-400";
  } else if (s === "escalated" || s === "critical" || s === "error" || s === "disconnected") {
    colorStyles = "bg-rose-950/60 text-rose-300 border-rose-800/80";
    dotStyles = "bg-rose-400";
  } else if (s === "closed_false_positive") {
    colorStyles = "bg-slate-900 text-slate-400 border-slate-700";
    dotStyles = "bg-slate-500";
  }

  const sizeStyles = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-medium rounded border ${colorStyles} ${sizeStyles}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotStyles}`} />
      <span className="uppercase tracking-wider">{label || status}</span>
    </span>
  );
};

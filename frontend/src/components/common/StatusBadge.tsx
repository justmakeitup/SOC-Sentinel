import React from "react";

interface StatusBadgeProps {
  status: "healthy" | "connected" | "degraded" | "disconnected" | "error" | "operational" | "critical";
  label?: string;
  size?: "sm" | "md";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = "md",
}) => {
  const isGood = status === "healthy" || status === "connected" || status === "operational";
  const isWarn = status === "degraded";

  const colorStyles = isGood
    ? "bg-emerald-950/60 text-emerald-300 border-emerald-800/80"
    : isWarn
    ? "bg-amber-950/60 text-amber-300 border-amber-800/80"
    : "bg-rose-950/60 text-rose-300 border-rose-800/80";

  const dotStyles = isGood
    ? "bg-emerald-400"
    : isWarn
    ? "bg-amber-400"
    : "bg-rose-400";

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

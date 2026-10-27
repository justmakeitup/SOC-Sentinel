import React, { useState } from "react";
import { Activity, Clock } from "lucide-react";
import { TimeSeriesPoint } from "../../types";

interface EventVolumeChartProps {
  data: TimeSeriesPoint[];
  loading?: boolean;
  onEnableDemo?: () => void;
}

export const EventVolumeChart: React.FC<EventVolumeChartProps> = ({
  data,
  loading = false,
  onEnableDemo,
}) => {
  const [activeRange, setActiveRange] = useState<"1h" | "6h" | "24h" | "7d">("24h");
  const [hoveredPoint, setHoveredPoint] = useState<{
    x: number;
    y: number;
    point: TimeSeriesPoint;
  } | null>(null);

  // SVG dimensions
  const width = 640;
  const height = 180;
  const padding = { top: 20, right: 24, bottom: 30, left: 45 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const points = data || [];
  const maxVal = Math.max(...points.map((p) => p.count), 10);
  const minVal = 0;

  // Coordinate mapping
  const getX = (index: number) => {
    if (points.length <= 1) return padding.left + innerWidth / 2;
    return padding.left + (index / (points.length - 1)) * innerWidth;
  };

  const getY = (val: number) => {
    const ratio = (val - minVal) / (maxVal - minVal || 1);
    return padding.top + innerHeight - ratio * innerHeight;
  };

  // Generate SVG path for line and closed area gradient
  const pathD = points.reduce((acc, p, i) => {
    const x = getX(i);
    const y = getY(p.count);
    return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, "");

  const areaD =
    points.length > 0
      ? `${pathD} L ${getX(points.length - 1)} ${padding.top + innerHeight} L ${getX(0)} ${
          padding.top + innerHeight
        } Z`
      : "";

  const totalEventsInWindow = points.reduce((acc, p) => acc + p.count, 0);

  return (
    <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] flex flex-col justify-between">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#1E293B]">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-teal-400" />
          <span className="text-xs font-mono font-medium tracking-wide text-slate-200 uppercase">
            Security Event Volume Timeline
          </span>
          {points.length > 0 && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800">
              {totalEventsInWindow.toLocaleString()} Events
            </span>
          )}
        </div>

        {/* Timeframe selector */}
        <div className="flex items-center gap-1 font-mono text-[11px]">
          {(["1h", "6h", "24h", "7d"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setActiveRange(r)}
              className={`px-2 py-0.5 rounded transition-colors uppercase ${
                activeRange === r
                  ? "bg-teal-950 text-teal-300 border border-teal-800 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Body */}
      <div className="relative mt-3 min-h-[180px] flex items-center justify-center">
        {loading ? (
          <div className="w-full h-full flex flex-col items-center justify-center py-10 space-y-2">
            <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-mono text-slate-400">
              Aggregating event telemetry...
            </span>
          </div>
        ) : points.length === 0 ? (
          <div className="py-8 px-4 text-center space-y-2">
            <Clock className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-xs font-mono text-slate-300 font-medium">
              No Event Telemetry Ingested
            </p>
            <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
              The normalized security events table is currently empty. Telemetry will graph in real-time as ingestion jobs process sensor feeds.
            </p>
            {onEnableDemo && (
              <button
                onClick={onEnableDemo}
                className="mt-2 inline-flex items-center gap-1.5 text-xs font-mono text-teal-400 hover:text-teal-300 underline underline-offset-4"
              >
                View with development demo data →
              </button>
            )}
          </div>
        ) : (
          <div className="w-full overflow-x-auto">
            <svg
              viewBox={`0 0 ${width} ${height}`}
              className="w-full h-auto select-none"
              role="img"
              aria-label={`Security event volume chart showing ${points.length} intervals`}
              onMouseLeave={() => setHoveredPoint(null)}
            >
              <defs>
                <linearGradient id="tealGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0D9488" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#0D9488" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Gridlines */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                const y = padding.top + innerHeight * (1 - ratio);
                const labelVal = Math.round(minVal + ratio * (maxVal - minVal));
                return (
                  <g key={ratio}>
                    <line
                      x1={padding.left}
                      y1={y}
                      x2={padding.left + innerWidth}
                      y2={y}
                      stroke="#1E293B"
                      strokeDasharray="3 3"
                    />
                    <text
                      x={padding.left - 8}
                      y={y + 3}
                      fill="#64748B"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="end"
                    >
                      {labelVal >= 1000 ? `${(labelVal / 1000).toFixed(1)}k` : labelVal}
                    </text>
                  </g>
                );
              })}

              {/* Area Gradient */}
              <path d={areaD} fill="url(#tealGradient)" />

              {/* Main Line */}
              <path
                d={pathD}
                fill="none"
                stroke="#14B8A6"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Interactive Dots and Crosshair */}
              {points.map((p, i) => {
                const cx = getX(i);
                const cy = getY(p.count);
                const isHovered = hoveredPoint?.point === p;

                return (
                  <g key={i}>
                    {/* Hover hotspot */}
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isHovered ? "5" : "3"}
                      fill={isHovered ? "#2DD4BF" : "#0D9488"}
                      stroke="#0B0F14"
                      strokeWidth="1.5"
                      className="cursor-pointer transition-all"
                      onMouseEnter={() => setHoveredPoint({ x: cx, y: cy, point: p })}
                    />
                  </g>
                );
              })}

              {/* X Axis Time Labels */}
              {points
                .filter((_, i) => i % Math.ceil(points.length / 6) === 0 || i === points.length - 1)
                .map((p, i, arr) => {
                  const origIdx = points.indexOf(p);
                  return (
                    <text
                      key={i}
                      x={getX(origIdx)}
                      y={height - 8}
                      fill="#64748B"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor={i === 0 ? "start" : i === arr.length - 1 ? "end" : "middle"}
                    >
                      {p.timestamp}
                    </text>
                  );
                })}

              {/* Tooltip on Hover */}
              {hoveredPoint && (
                <g>
                  {/* Vertical Crosshair Line */}
                  <line
                    x1={hoveredPoint.x}
                    y1={padding.top}
                    x2={hoveredPoint.x}
                    y2={padding.top + innerHeight}
                    stroke="#14B8A6"
                    strokeWidth="1"
                    strokeDasharray="2 2"
                    opacity="0.8"
                  />
                  {/* Tooltip Box */}
                  <rect
                    x={Math.min(Math.max(hoveredPoint.x - 50, padding.left), width - 110)}
                    y={Math.max(hoveredPoint.y - 38, 5)}
                    width="100"
                    height="28"
                    rx="4"
                    fill="#1E293B"
                    stroke="#0D9488"
                    strokeWidth="1"
                  />
                  <text
                    x={Math.min(Math.max(hoveredPoint.x, padding.left + 50), width - 60)}
                    y={Math.max(hoveredPoint.y - 20, 23)}
                    fill="#F1F5F9"
                    fontSize="10"
                    fontFamily="monospace"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    {hoveredPoint.point.count.toLocaleString()} eps
                  </text>
                </g>
              )}
            </svg>
          </div>
        )}
      </div>
    </div>
  );
};

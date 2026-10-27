import React, { useState, useEffect, useCallback } from "react";
import { Shell } from "./components/layout/Shell";
import { StatusBadge } from "./components/common/StatusBadge";
import { fetchSystemHealth } from "./api/health";
import { API_BASE_URL } from "./api/client";
import { HealthResponse } from "./types";
import {
  Activity,
  Database,
  Radio,
  FileCode,
  ShieldAlert,
  FolderGit2,
  ScrollText,
  RefreshCw,
  Server,
  Layers,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const loadHealth = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const data = await fetchSystemHealth();
      setHealth(data);
      setLastCheck(new Date());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to connect to Sentinel API"
      );
      setHealth(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  const backendOnline = !!health && !error;
  const currentEnvironment = health?.environment || "connecting...";

  return (
    <Shell backendOnline={backendOnline} environment={currentEnvironment}>
      {/* Platform Title & Executive Status Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-[#1E293B]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              Platform Health & Subsystem Readiness
            </h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-950/80 text-teal-300 border border-teal-800/80">
              Phase 1 Foundation
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time backend connectivity verification, database schema status, and system topology.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {loading && (
            <span className="text-xs font-mono text-teal-400">
              Initializing telemetry link...
            </span>
          )}
          {lastCheck && !loading && (
            <span className="text-xs font-mono text-slate-400">
              Synced: {lastCheck.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={loadHealth}
            disabled={refreshing || loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono font-medium bg-[#121820] text-slate-200 border border-[#1E293B] hover:border-teal-700/80 hover:text-teal-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-teal-400" : ""}`} />
            <span>{refreshing ? "Querying..." : "Refresh Status"}</span>
          </button>
        </div>
      </div>

      {/* Connection State Alert */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/80 text-rose-200 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="text-sm font-semibold">Backend Unreachable at {API_BASE_URL}</div>
            <p className="text-xs text-rose-300 leading-relaxed">{error}</p>
            <p className="text-[11px] font-mono text-rose-400 mt-2">
              Troubleshooting: Ensure the FastAPI server is running with{" "}
              <code className="bg-rose-950 px-1 py-0.5 rounded border border-rose-800">
                uvicorn app.main:app --reload
              </code>
            </p>
          </div>
        </div>
      )}

      {/* Subsystem Readiness Matrix */}
      <div>
        <h2 className="text-xs font-mono tracking-wider text-slate-400 uppercase mb-3">
          Core Subsystems
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Database Subsystem */}
          <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-slate-800/80 text-teal-400 border border-slate-700">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-200">PostgreSQL Core</div>
                  <div className="text-[11px] text-slate-400 font-mono">Persistence & State</div>
                </div>
              </div>
              <StatusBadge
                status={
                  health?.subsystems?.database?.status === "connected"
                    ? "connected"
                    : health
                    ? "degraded"
                    : "disconnected"
                }
                size="sm"
              />
            </div>
            <div className="pt-2 border-t border-[#1E293B] text-xs font-mono text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>LATENCY:</span>
                <span className="text-slate-300">
                  {health?.subsystems?.database?.latency_ms !== undefined &&
                  health.subsystems.database.latency_ms !== null
                    ? `${health.subsystems.database.latency_ms} ms`
                    : "N/A"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>DIALECT:</span>
                <span className="text-teal-400">PostgreSQL 16+</span>
              </div>
            </div>
          </div>

          {/* Ingestion Pipeline Subsystem */}
          <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-slate-800/80 text-cyan-400 border border-slate-700">
                  <Radio className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-200">Ingestion Pipeline</div>
                  <div className="text-[11px] text-slate-400 font-mono">Telemetry Parser</div>
                </div>
              </div>
              <StatusBadge
                status={backendOnline ? "healthy" : "disconnected"}
                label={backendOnline ? "Ready" : "Offline"}
                size="sm"
              />
            </div>
            <div className="pt-2 border-t border-[#1E293B] text-xs font-mono text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>DEDUPLICATION:</span>
                <span className="text-teal-400">SHA-256 Fingerprint</span>
              </div>
              <div className="flex justify-between">
                <span>SUPPORTED SENSORS:</span>
                <span className="text-slate-300">Syslog, WinEvent, Zeek</span>
              </div>
            </div>
          </div>

          {/* Detection Engine Subsystem */}
          <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded bg-slate-800/80 text-teal-400 border border-slate-700">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-200">Detection Engine</div>
                  <div className="text-[11px] text-slate-400 font-mono">Sliding Correlator</div>
                </div>
              </div>
              <StatusBadge
                status={backendOnline ? "healthy" : "disconnected"}
                label={backendOnline ? "Standby" : "Offline"}
                size="sm"
              />
            </div>
            <div className="pt-2 border-t border-[#1E293B] text-xs font-mono text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>RULE TAXONOMY:</span>
                <span className="text-slate-300">MITRE ATT&CK</span>
              </div>
              <div className="flex justify-between">
                <span>EVAL WINDOW:</span>
                <span className="text-teal-400">Sliding Time Window</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Database Schema Architecture Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-mono tracking-wider text-slate-400 uppercase">
            Data Architecture & Entity Design (Alembic Migration 0001)
          </h2>
          <span className="text-[11px] font-mono text-teal-400">
            7 Core Security Domain Entities
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              title: "Users & RBAC",
              table: "users",
              desc: "Tier-1/2 Analysts, Responders, Engineers with MFA & audit links.",
              icon: Server,
              badge: "Identity",
            },
            {
              title: "Log Sources & Jobs",
              table: "log_sources / ingestion_jobs",
              desc: "Collectors, retention rules, batch hashes & ingestion runs.",
              icon: Radio,
              badge: "Telemetry",
            },
            {
              title: "Normalized Events",
              table: "normalized_security_events",
              desc: "ECS/OSSEM taxonomy with SHA-256 cryptographic deduplication.",
              icon: Layers,
              badge: "Telemetry",
            },
            {
              title: "Detection Rules",
              table: "detection_rules",
              desc: "Threshold & SQL conditions mapped to MITRE ATT&CK tactics.",
              icon: FileCode,
              badge: "Detection",
            },
            {
              title: "Security Alerts",
              table: "security_alerts",
              desc: "Aggregated alerts with deduplication keys to prevent storms.",
              icon: ShieldAlert,
              badge: "Response",
            },
            {
              title: "Incidents",
              table: "incidents",
              desc: "NIST SP 800-61 lifecycle (Containment, Eradication, Recovery).",
              icon: FolderGit2,
              badge: "Response",
            },
            {
              title: "Investigation Notes",
              table: "investigation_notes",
              desc: "Forensic audit journal, evidence logging & analyst actions.",
              icon: ScrollText,
              badge: "Investigation",
            },
            {
              title: "Audit Events",
              table: "audit_events",
              desc: "Immutable compliance trail (SOC 2, ISO 27001) with state diffs.",
              icon: CheckCircle2,
              badge: "Governance",
            },
          ].map((entity) => {
            const Icon = entity.icon;
            return (
              <div
                key={entity.table}
                className="p-3.5 rounded-lg bg-[#121820] border border-[#1E293B] hover:border-slate-700 transition-colors space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-teal-400" />
                    <span className="text-xs font-semibold text-slate-200">
                      {entity.title}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {entity.badge}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-teal-500/90 truncate">
                  {entity.table}
                </div>
                <p className="text-[11px] text-slate-400 leading-normal">
                  {entity.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Technical Summary Panel */}
      <div className="p-4 rounded-lg bg-[#121820] border border-[#1E293B] text-xs font-mono space-y-2">
        <div className="text-slate-300 font-semibold uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4 text-teal-400" />
          <span>Foundation Integrity Verification</span>
        </div>
        <div className="text-slate-400 leading-relaxed text-[11px]">
          Backend FastAPI service, Pydantic validation schemas, SQLAlchemy ORM models, and
          Alembic migrations are configured. Database deduplication rules prevent duplicate ingestion
          via SHA-256 event fingerprinting and sliding window alert keys. Ready for Phase 2 implementation.
        </div>
      </div>
    </Shell>
  );
};

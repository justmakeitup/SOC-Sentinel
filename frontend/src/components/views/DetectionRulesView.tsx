import React, { useState, useEffect, useCallback } from "react";
import { DetectionRuleDetail } from "../../types";
import {
  fetchDetectionRules,
  updateDetectionRule,
  triggerEngineEvaluation,
} from "../../api/rules";
import { SeverityBadge } from "../common/SeverityBadge";
import {
  CheckCircle2,
  AlertTriangle,
  Play,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Info,
} from "lucide-react";

interface DetectionRulesViewProps {
  demoMode: boolean;
  onEnableDemo?: () => void;
  onAlertsTriggered?: () => void;
}

export const DetectionRulesView: React.FC<DetectionRulesViewProps> = ({
  demoMode,
  onAlertsTriggered,
}) => {
  const [rules, setRules] = useState<DetectionRuleDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [evalResult, setEvalResult] = useState<string | null>(null);
  const [expandedRule, setExpandedRule] = useState<string | null>("SEC-AUTH-001");

  const loadRules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDetectionRules(false, demoMode);
      setRules(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load detection rules");
    } finally {
      setLoading(false);
    }
  }, [demoMode]);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  const handleToggleActive = async (rule: DetectionRuleDetail) => {
    try {
      const updated = await updateDetectionRule(
        rule.rule_code,
        { is_active: !rule.is_active },
        demoMode
      );
      setRules((prev) =>
        prev.map((r) => (r.rule_code === rule.rule_code ? updated : r))
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to toggle rule state");
    }
  };

  const handleTriggerEvaluation = async () => {
    setEvaluating(true);
    setEvalResult(null);
    try {
      const generated = await triggerEngineEvaluation(demoMode);
      setEvalResult(
        `Engine evaluation completed: ${generated.length} alert(s) generated or updated.`
      );
      if (onAlertsTriggered) onAlertsTriggered();
    } catch (err) {
      setEvalResult(
        err instanceof Error ? `Evaluation error: ${err.message}` : "Evaluation failed"
      );
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="space-y-6 text-slate-100 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1E293B] gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              Detection Rules Catalog
            </h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-teal-950/60 border border-teal-800/60 text-teal-300">
              MITRE ATT&CK Mapped
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Deterministic, rule-based correlation engine plugins with sliding threshold windows.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadRules}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#121820] hover:bg-[#1A2332] border border-[#1E293B] text-slate-300 hover:text-slate-100 text-xs font-mono transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-teal-400" : ""}`} />
            Refresh
          </button>
          <button
            onClick={handleTriggerEvaluation}
            disabled={evaluating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-teal-600 hover:bg-teal-500 text-slate-950 font-bold text-xs font-mono transition-colors disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${evaluating ? "animate-pulse" : ""}`} />
            {evaluating ? "Evaluating Stream..." : "Evaluate Recent Telemetry"}
          </button>
        </div>
      </div>

      {/* Eval Result Notification */}
      {evalResult && (
        <div className="p-3.5 rounded bg-[#0B0F14] border border-teal-800/40 text-teal-300 font-mono text-xs flex items-center justify-between">
          <span>{evalResult}</span>
          <button
            onClick={() => setEvalResult(null)}
            className="text-slate-500 hover:text-slate-300 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 rounded bg-rose-950/20 border border-rose-900/40 text-rose-300 font-mono text-xs">
          {error}
        </div>
      )}

      {/* Rules List */}
      <div className="space-y-4">
        {loading && rules.length === 0 ? (
          <div className="py-16 text-center font-mono text-xs text-slate-400">
            Loading detection rules catalog...
          </div>
        ) : (
          rules.map((rule) => {
            const isExpanded = expandedRule === rule.rule_code;
            return (
              <div
                key={rule.rule_code}
                className="bg-[#121820] border border-[#1E293B] rounded-lg overflow-hidden transition-all duration-150"
              >
                {/* Rule Summary Header Row */}
                <div
                  onClick={() =>
                    setExpandedRule(isExpanded ? null : rule.rule_code)
                  }
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-[#161F2C] select-none"
                >
                  <div className="flex items-center gap-3">
                    <button className="text-slate-400 hover:text-teal-400">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-teal-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-teal-400">
                          {rule.rule_code}
                        </span>
                        <span className="text-slate-500">•</span>
                        <SeverityBadge severity={rule.severity} />
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                          {rule.rule_type.toUpperCase()}
                        </span>
                        {rule.mitre_technique && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-950/40 border border-indigo-800/40 text-indigo-300 hidden sm:inline-block">
                            {rule.mitre_technique}
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-semibold text-slate-100 mt-1">
                        {rule.name}
                      </h3>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="hidden md:flex items-center gap-3 font-mono text-xs text-slate-400">
                      <div>
                        Threshold:{" "}
                        <span className="text-slate-200 font-semibold">
                          {rule.threshold_count}
                        </span>
                      </div>
                      <div>
                        Window:{" "}
                        <span className="text-slate-200 font-semibold">
                          {rule.time_window_seconds}s
                        </span>
                      </div>
                    </div>

                    {/* Active toggle */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleActive(rule);
                      }}
                      className={`px-2.5 py-1 rounded text-[11px] font-mono font-medium transition-colors ${
                        rule.is_active
                          ? "bg-teal-950/60 text-teal-300 border border-teal-800/60 hover:bg-teal-900/40"
                          : "bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700"
                      }`}
                    >
                      {rule.is_active ? "ACTIVE" : "DISABLED"}
                    </button>
                  </div>
                </div>

                {/* Expanded Documentation & Transparency Details */}
                {isExpanded && (
                  <div className="p-5 border-t border-[#1E293B] bg-[#0E131A] space-y-4">
                    <div className="space-y-1">
                      <div className="text-[11px] font-mono font-semibold text-slate-400 uppercase">
                        Description & Threat Scenario
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-sans">
                        {rule.description}
                      </p>
                    </div>

                    {/* Operational Documentation Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-sans text-xs">
                      {/* Assumptions */}
                      <div className="p-3.5 rounded bg-[#080B0F] border border-[#1A2332] space-y-2">
                        <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-teal-400 uppercase">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Assumptions
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px] leading-relaxed">
                          {rule.assumptions.map((a, idx) => (
                            <li key={idx}>{a}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Limitations */}
                      <div className="p-3.5 rounded bg-[#080B0F] border border-[#1A2332] space-y-2">
                        <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-amber-400 uppercase">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          Limitations
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px] leading-relaxed">
                          {rule.limitations.map((lim, idx) => (
                            <li key={idx}>{lim}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Expected False Positives */}
                      <div className="p-3.5 rounded bg-[#080B0F] border border-[#1A2332] space-y-2">
                        <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-slate-400 uppercase">
                          <Info className="w-3.5 h-3.5 text-teal-400" />
                          Expected False Positives
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px] leading-relaxed">
                          {rule.expected_false_positives.map((fp, idx) => (
                            <li key={idx}>{fp}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Remediation Runbook */}
                    {rule.remediation_guidance && (
                      <div className="p-3.5 rounded bg-[#080B0F] border border-[#1A2332] space-y-2">
                        <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-teal-400 uppercase">
                          <BookOpen className="w-3.5 h-3.5" />
                          Triage & Remediation Guidance
                        </div>
                        <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                          {rule.remediation_guidance}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

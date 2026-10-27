/**
 * API service for detection engineering rules, threshold configuration, and telemetry replay.
 */

import { apiClient } from "./client";
import { DetectionRuleDetail, ReplayResponse, AlertItem, RuleSeverity } from "../types";

export interface RuleUpdatePayload {
  is_active?: boolean;
  threshold_count?: number;
  time_window_seconds?: number;
  severity?: RuleSeverity;
}

export const DEMO_RULES: DetectionRuleDetail[] = [
  {
    id: "demo-rule-1",
    rule_code: "SEC-AUTH-001",
    name: "Repeated Failed Authentication Attempts",
    description: "Detects a high volume of failed authentication events targeting an account or originating from a single host within a configurable time window.",
    severity: "high",
    rule_type: "threshold",
    is_active: true,
    time_window_seconds: 300,
    threshold_count: 5,
    mitre_tactic: "Credential Access",
    mitre_technique: "T1110 - Brute Force",
    remediation_guidance: "1. Identify whether username is human or service account.\n2. Check source IP reputation.\n3. Temporarily restrict source IP at perimeter firewall.",
    assumptions: [
      "Authentication sources emit 'login_failed' actions reliably.",
      "Timestamps accurately represent UTC generation time.",
    ],
    limitations: [
      "Slow-and-low brute force attacks (e.g. 1 attempt per 10 min) stay below window.",
    ],
    expected_false_positives: [
      "Users with expired passwords whose Outlook or mobile client retries automatically.",
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "demo-rule-2",
    rule_code: "SEC-AUTH-002",
    name: "Successful Login Following Repeated Failures",
    description: "Correlates multiple failed logins followed by a successful login for the same account within a configured correlation window.",
    severity: "medium",
    rule_type: "correlation",
    is_active: true,
    time_window_seconds: 600,
    threshold_count: 3,
    mitre_tactic: "Credential Access",
    mitre_technique: "T1110.001 - Password Guessing",
    remediation_guidance: "1. Compare source IP of failed attempts with source IP of successful login.\n2. Inspect post-login user activity.",
    assumptions: [
      "Authentication telemetry preserves causal order between failures and success.",
    ],
    limitations: [
      "Cannot distinguish in isolation between user recovering Caps Lock vs. adversary guessing credentials.",
    ],
    expected_false_positives: [
      "Legitimate employees mistyping their password multiple times before entering correctly.",
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "demo-rule-3",
    rule_code: "SEC-NET-001",
    name: "Port-Scan-Like Multi-Port Sweep",
    description: "Detects a single source IP attempting connection to multiple distinct destination ports on a target host within a sliding time window.",
    severity: "medium",
    rule_type: "threshold",
    is_active: true,
    time_window_seconds: 60,
    threshold_count: 5,
    mitre_tactic: "Discovery",
    mitre_technique: "T1046 - Network Service Discovery",
    remediation_guidance: "1. Check if source IP belongs to authorized scanner.\n2. Review firewall actions (drop/reject/allow).\n3. Apply perimeter ingress drop rules if malicious.",
    assumptions: [
      "Network sensors record source IP, destination IP, and destination port.",
    ],
    limitations: [
      "Distributed port scans (each port probed from different IP) will not match single source threshold.",
    ],
    expected_false_positives: [
      "Enterprise vulnerability scanners (Nessus, Qualys) conducting scheduled sweeps.",
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "demo-rule-4",
    rule_code: "SEC-AUTH-003",
    name: "Unusual Authentication Pattern Deviation",
    description: "Detects transparent authentication anomalies: multi-source IP velocity targeting a single account within a short window, or privileged off-hours authentication.",
    severity: "medium",
    rule_type: "anomaly",
    is_active: true,
    time_window_seconds: 900,
    threshold_count: 3,
    mitre_tactic: "Initial Access",
    mitre_technique: "T1078 - Valid Accounts",
    remediation_guidance: "1. For multi-IP: Verify if user was using VPN or mobile data.\n2. For off-hours: Confirm active maintenance window or on-call ticket.",
    assumptions: [
      "Authentication telemetry accurately captures client source IP.",
      "Privileged accounts can be matched by naming convention or policy.",
    ],
    limitations: [
      "Off-hours baseline is based on UTC; global teams may have differing local shifts.",
    ],
    expected_false_positives: [
      "On-call engineers responding to an overnight incident between 00:00 and 05:00 UTC.",
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export async function fetchDetectionRules(
  activeOnly: boolean = false,
  demoMode: boolean = false
): Promise<DetectionRuleDetail[]> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return activeOnly ? DEMO_RULES.filter((r) => r.is_active) : DEMO_RULES;
  }
  const url = activeOnly ? "api/v1/rules?active_only=true" : "api/v1/rules";
  return apiClient<DetectionRuleDetail[]>(url);
}

export async function updateDetectionRule(
  ruleCode: string,
  payload: RuleUpdatePayload,
  demoMode: boolean = false
): Promise<DetectionRuleDetail> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const found = DEMO_RULES.find((r) => r.rule_code === ruleCode);
    if (!found) throw new Error("Rule not found in demo mode");
    return { ...found, ...payload } as DetectionRuleDetail;
  }
  return apiClient<DetectionRuleDetail>(`api/v1/rules/${ruleCode}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function triggerEngineEvaluation(
  demoMode: boolean = false
): Promise<AlertItem[]> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return [];
  }
  return apiClient<AlertItem[]>("api/v1/rules/evaluate", {
    method: "POST",
  });
}

export async function triggerReplay(
  startTime: string,
  endTime: string,
  demoMode: boolean = false
): Promise<ReplayResponse> {
  if (demoMode) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return {
      start_time: startTime,
      end_time: endTime,
      events_evaluated: 120,
      alerts_generated_or_updated: 3,
      errors: [],
    };
  }
  return apiClient<ReplayResponse>("api/v1/rules/replay", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start_time: startTime, end_time: endTime }),
  });
}

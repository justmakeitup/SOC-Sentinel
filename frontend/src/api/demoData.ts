/**
 * Development demonstration data for UI inspection and review.
 * 
 * STRICT COMPLIANCE NOTE:
 * These records are strictly utilized for development evaluation when explicitly
 * enabled via the "Demo Mode" toggle in the header. They are NEVER mixed with live
 * production backend responses.
 */

import {
  DashboardSummary,
  AlertItem,
  IncidentItem,
  PaginatedResponse,
} from "../types";

export const DEMO_TIMESERIES_24H = [
  { timestamp: "12:00", count: 420 },
  { timestamp: "13:00", count: 560 },
  { timestamp: "14:00", count: 810 },
  { timestamp: "15:00", count: 1240 },
  { timestamp: "16:00", count: 980 },
  { timestamp: "17:00", count: 1450 },
  { timestamp: "18:00", count: 2100 },
  { timestamp: "19:00", count: 1890 },
  { timestamp: "20:00", count: 2450 },
  { timestamp: "21:00", count: 3200 },
  { timestamp: "22:00", count: 2980 },
  { timestamp: "23:00", count: 1950 },
  { timestamp: "00:00", count: 1420 },
  { timestamp: "01:00", count: 1100 },
  { timestamp: "02:00", count: 940 },
  { timestamp: "03:00", count: 870 },
  { timestamp: "04:00", count: 910 },
  { timestamp: "05:00", count: 1040 },
  { timestamp: "06:00", count: 1380 },
  { timestamp: "07:00", count: 2150 },
  { timestamp: "08:00", count: 2840 },
  { timestamp: "09:00", count: 3410 },
  { timestamp: "10:00", count: 3120 },
  { timestamp: "11:00", count: 2790 },
];

export const DEMO_DASHBOARD_SUMMARY: DashboardSummary = {
  events_processed: 142850,
  active_alerts: 19,
  open_incidents: 3,
  critical_alerts: 4,
  event_volume_timeseries: DEMO_TIMESERIES_24H,
  severity_distribution: {
    critical: 4,
    high: 8,
    medium: 12,
    low: 24,
    informational: 48,
  },
  last_updated: new Date().toISOString(),
};

export const DEMO_ALERTS: AlertItem[] = [
  {
    id: "alt-001",
    rule_id: "rule-auth-001",
    rule_code: "SEC-AUTH-001",
    rule_name: "SSH Brute Force Velocity Exceeded",
    title: "Sustained SSH authentication failures on bastion host",
    description: "More than 50 failed root/admin logins detected within 300 seconds originating from external IP.",
    severity: "critical",
    status: "investigating",
    source_ip: "198.51.100.24",
    deduplication_key: "SEC-AUTH-001:198.51.100.24:20261027",
    event_count: 84,
    created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
  },
  {
    id: "alt-002",
    rule_id: "rule-net-003",
    rule_code: "SEC-NET-003",
    rule_name: "Outbound Port Scan / Host Discovery",
    title: "Suspicious lateral TCP SYN scan detected across /24 subnet",
    description: "Internal workstation attempting connections to TCP ports 445, 139, 3389 across 64 adjacent IP addresses.",
    severity: "high",
    status: "new",
    source_ip: "10.0.4.88",
    deduplication_key: "SEC-NET-003:10.0.4.88:20261027",
    event_count: 64,
    created_at: new Date(Date.now() - 1000 * 60 * 28).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 28).toISOString(),
  },
  {
    id: "alt-003",
    rule_id: "rule-proc-007",
    rule_code: "SEC-PROC-007",
    rule_name: "PowerShell Encoded Script Execution",
    title: "Encoded Base64 PowerShell command executed by service account",
    description: "powershell.exe executed with -EncodedCommand parameter spawning cmd.exe in background.",
    severity: "critical",
    status: "escalated",
    source_ip: "10.0.2.14",
    deduplication_key: "SEC-PROC-007:10.0.2.14:20261027",
    event_count: 3,
    created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
  },
  {
    id: "alt-004",
    rule_id: "rule-dns-002",
    rule_code: "SEC-DNS-002",
    rule_name: "High Entropy Domain Generation Algorithm (DGA)",
    title: "Anomalous DNS query volume to suspected C2 domain",
    description: "Host queried 14 domains matching Shannon entropy threshold > 4.2 within 60 seconds.",
    severity: "medium",
    status: "triaged",
    source_ip: "172.16.10.42",
    deduplication_key: "SEC-DNS-002:172.16.10.42:20261027",
    event_count: 14,
    created_at: new Date(Date.now() - 1000 * 60 * 82).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 50).toISOString(),
  },
  {
    id: "alt-005",
    rule_id: "rule-priv-005",
    rule_code: "SEC-PRIV-005",
    rule_name: "Unusual Sudoers File Access",
    title: "Read access to /etc/sudoers by non-administrative user",
    description: "Web server daemon account attempted direct cat read on sudoers configuration file.",
    severity: "high",
    status: "new",
    source_ip: "10.0.3.50",
    deduplication_key: "SEC-PRIV-005:10.0.3.50:20261027",
    event_count: 1,
    created_at: new Date(Date.now() - 1000 * 60 * 115).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 115).toISOString(),
  },
  {
    id: "alt-006",
    rule_id: "rule-cloud-001",
    rule_code: "SEC-CLOUD-001",
    rule_name: "Root Account Cloud Console Login Without MFA",
    title: "AWS Root credential login observed without MFA verification",
    description: "Root console login detected from IP address not in corporate VPN range without hardware token.",
    severity: "critical",
    status: "investigating",
    source_ip: "203.0.113.8",
    deduplication_key: "SEC-CLOUD-001:203.0.113.8:20261027",
    event_count: 1,
    created_at: new Date(Date.now() - 1000 * 60 * 160).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
  },
  {
    id: "alt-007",
    rule_id: "rule-pol-002",
    rule_code: "SEC-POL-002",
    rule_name: "Unauthorized USB Storage Device Attached",
    title: "Mass storage USB insertion on engineering CAD workstation",
    description: "Removable media mounted violating enterprise endpoint hardware isolation policy.",
    severity: "low",
    status: "closed_resolved",
    source_ip: "10.0.8.22",
    deduplication_key: "SEC-POL-002:10.0.8.22:20261027",
    event_count: 1,
    created_at: new Date(Date.now() - 1000 * 60 * 240).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
  },
  {
    id: "alt-008",
    rule_id: "rule-net-009",
    rule_code: "SEC-NET-009",
    rule_name: "Tor Exit Node Communication",
    title: "Outbound HTTPS connection to known Tor relay node",
    description: "Workstation established TLS session to known Tor directory exit authority.",
    severity: "medium",
    status: "closed_false_positive",
    source_ip: "10.0.5.19",
    deduplication_key: "SEC-NET-009:10.0.5.19:20261027",
    event_count: 6,
    created_at: new Date(Date.now() - 1000 * 60 * 360).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 300).toISOString(),
  },
];

export const DEMO_INCIDENTS: IncidentItem[] = [
  {
    id: "inc-001",
    incident_number: "INC-2026-0042",
    title: "Active Kerberoasting & Lateral Movement Attempt",
    summary: "Service ticket extraction followed by SMB port exploration across Finance segment servers.",
    severity: "sev_1_critical",
    status: "containment",
    lead_analyst_name: "Alex Mercer",
    containment_details: "Host 10.0.4.88 isolated via EDR API; Krbtgt ticket cache invalidated on primary DC.",
    created_at: new Date(Date.now() - 1000 * 60 * 55).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
  },
  {
    id: "inc-002",
    incident_number: "INC-2026-0041",
    title: "Perimeter Bastion SSH Credential Stuffing",
    summary: "Distributed dictionary attack against external bastion from 18 distinct IPs.",
    severity: "sev_2_high",
    status: "eradication",
    lead_analyst_name: "Elena Rostova",
    containment_details: "Geo-blocking applied at edge firewall; public key requirement enforced.",
    created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 42).toISOString(),
  },
  {
    id: "inc-003",
    incident_number: "INC-2026-0039",
    title: "Unsanctioned Cloud S3 Bucket Public Access Exposure",
    summary: "Marketing analytics test bucket misconfigured with public read ACL containing log exports.",
    severity: "sev_3_medium",
    status: "recovery",
    lead_analyst_name: "Marcus Vance",
    containment_details: "Bucket policy reset to private; IAM credential rotated.",
    created_at: new Date(Date.now() - 1000 * 60 * 420).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 95).toISOString(),
  },
  {
    id: "inc-004",
    incident_number: "INC-2026-0036",
    title: "Phishing Campaign Targeting Payroll Accounts",
    summary: "12 credential harvesting emails quarantined by secure mail gateway.",
    severity: "sev_4_low",
    status: "closed",
    lead_analyst_name: "Elena Rostova",
    containment_details: "Domain blocklist updated; sender IP banned across gateway.",
    created_at: new Date(Date.now() - 1000 * 60 * 1400).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 600).toISOString(),
  },
];

export function getDemoFilteredAlerts(params: {
  page?: number;
  pageSize?: number;
  severity?: string;
  status?: string;
  search?: string;
}): PaginatedResponse<AlertItem> {
  const { page = 1, pageSize = 10, severity, status, search } = params;

  let filtered = [...DEMO_ALERTS];

  if (severity && severity.toLowerCase() !== "all") {
    filtered = filtered.filter(
      (a) => a.severity.toLowerCase() === severity.toLowerCase()
    );
  }

  if (status && status.toLowerCase() !== "all") {
    filtered = filtered.filter(
      (a) => a.status.toLowerCase() === status.toLowerCase()
    );
  }

  if (search && search.trim()) {
    const term = search.toLowerCase().trim();
    filtered = filtered.filter(
      (a) =>
        a.title.toLowerCase().includes(term) ||
        (a.rule_name && a.rule_name.toLowerCase().includes(term)) ||
        (a.rule_code && a.rule_code.toLowerCase().includes(term)) ||
        (a.source_ip && a.source_ip.toLowerCase().includes(term))
    );
  }

  const totalCount = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const offset = (page - 1) * pageSize;
  const items = filtered.slice(offset, offset + pageSize);

  return {
    items,
    total_count: totalCount,
    page,
    page_size: pageSize,
    total_pages: totalPages,
  };
}

export function getDemoFilteredIncidents(params: {
  status?: string;
}): PaginatedResponse<IncidentItem> {
  const { status } = params;
  let filtered = [...DEMO_INCIDENTS];

  if (status && status.toLowerCase() !== "all") {
    filtered = filtered.filter(
      (i) => i.status.toLowerCase() === status.toLowerCase()
    );
  }

  return {
    items: filtered,
    total_count: filtered.length,
    page: 1,
    page_size: 10,
    total_pages: 1,
  };
}

/**
 * Development demonstration data for UI inspection and review.
 *
 * STRICT COMPLIANCE NOTE:
 * These records are strictly utilized for development evaluation when explicitly
 * enabled via the "Demo Mode" toggle in the header. They are NEVER mixed with live
 * production backend responses.
 */

import {
  AlertItem,
  DashboardSummary,
  IncidentItem,
  IngestionJobItem,
  LogSourceItem,
  NormalizedSecurityEventItem,
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
];

export const DEMO_EVENTS: NormalizedSecurityEventItem[] = [
  {
    id: "ev-001",
    log_source_id: "src-001",
    log_source_name: "Core-Firewall-Primary",
    timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    ingested_at: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    event_type: "network_flow",
    event_action: "connection_blocked",
    severity: "medium",
    source_ip: "198.51.100.24",
    source_port: 51240,
    destination_ip: "10.0.1.5",
    destination_port: 22,
    protocol: "TCP",
    user_name: "root",
    host_name: "bastion.internal.corp",
    raw_payload: "Oct 27 15:40:12 fw01 kernel: DROP IN=eth0 OUT=eth1 SRC=198.51.100.24 DST=10.0.1.5 PROTO=TCP SPT=51240 DPT=22",
    event_hash: "3a9f0e1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
  },
  {
    id: "ev-002",
    log_source_id: "src-002",
    log_source_name: "AD-Domain-Controller-01",
    timestamp: new Date(Date.now() - 1000 * 60 * 7).toISOString(),
    ingested_at: new Date(Date.now() - 1000 * 60 * 6).toISOString(),
    event_type: "authentication",
    event_action: "login_failed",
    severity: "high",
    source_ip: "10.0.4.88",
    source_port: 49152,
    destination_ip: "10.0.0.1",
    destination_port: 88,
    protocol: "TCP",
    user_name: "svc_backup",
    host_name: "DC01.sentinel.sec",
    raw_payload: "EventID=4625 LogonType=3 Status=0xC000006A User=svc_backup Host=DC01 CallerIP=10.0.4.88",
    event_hash: "1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c",
  },
  {
    id: "ev-003",
    log_source_id: "src-003",
    log_source_name: "Host-Agent-Workstation",
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    ingested_at: new Date(Date.now() - 1000 * 60 * 14).toISOString(),
    event_type: "process_execution",
    event_action: "process_spawned",
    severity: "critical",
    source_ip: "10.0.2.14",
    user_name: "jdoe",
    host_name: "WS-ENG-042",
    process_name: "powershell.exe",
    process_path: "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    command_line: "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command [REDACTED]",
    raw_payload: "Sysmon EventID=1 Image=powershell.exe User=WS-ENG-042\\jdoe CommandLine=powershell.exe -NoProfile -ExecutionPolicy Bypass",
    event_hash: "4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f",
  },
];

export const DEMO_LOG_SOURCES: LogSourceItem[] = [
  {
    id: "src-001",
    name: "Core-Firewall-Primary",
    source_type: "suricata_nids",
    description: "Perimeter NIDS & firewall traffic collector",
    ip_address: "192.168.1.1",
    hostname: "fw01.sentinel.sec",
    status: "active",
    retention_days: 90,
    total_events: 84120,
    total_jobs: 14,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "src-002",
    name: "AD-Domain-Controller-01",
    source_type: "windows_event_log",
    description: "Kerberos & Windows Security Event Forwarding",
    ip_address: "10.0.0.1",
    hostname: "dc01.sentinel.sec",
    status: "active",
    retention_days: 180,
    total_events: 51240,
    total_jobs: 22,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "src-003",
    name: "Cloud-Kube-Audit",
    source_type: "kubernetes",
    description: "Kubernetes API server audit stream",
    ip_address: "10.244.0.1",
    hostname: "k8s-control.sentinel.sec",
    status: "active",
    retention_days: 60,
    total_events: 7490,
    total_jobs: 8,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const DEMO_INGESTION_JOBS: IngestionJobItem[] = [
  {
    id: "job-001",
    log_source_id: "src-001",
    status: "completed",
    batch_identifier: "batch-auth-daily-20261027",
    events_processed: 450,
    events_failed: 0,
    bytes_ingested: 65420,
    error_message: null,
    rejected_records: [],
    started_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    completed_at: new Date(Date.now() - 1000 * 60 * 44).toISOString(),
  },
  {
    id: "job-002",
    log_source_id: "src-002",
    status: "partially_failed",
    batch_identifier: "batch-fw-sample-20261027",
    events_processed: 120,
    events_failed: 3,
    bytes_ingested: 21450,
    error_message: "3 malformed or invalid records quarantined during validation.",
    rejected_records: [
      { line_number: 14, reason: "Invalid IP address format: '999.999.999.999'", raw_snippet: "2026-10-27T10:00:00Z,user,ALLOW,999.999.999.999" },
      { line_number: 28, reason: "Port number 88888 out of range 1-65535", raw_snippet: "2026-10-27T10:05:00Z,admin,BLOCK,10.0.0.1,88888" },
      { line_number: 42, reason: "Missing required timestamp field", raw_snippet: ",guest,DENY,10.0.0.2,443" },
    ],
    started_at: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    completed_at: new Date(Date.now() - 1000 * 60 * 89).toISOString(),
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
    filtered = filtered.filter((a) => a.severity.toLowerCase() === severity.toLowerCase());
  }
  if (status && status.toLowerCase() !== "all") {
    filtered = filtered.filter((a) => a.status.toLowerCase() === status.toLowerCase());
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

  return { items, total_count: totalCount, page, page_size: pageSize, total_pages: totalPages };
}

export function getDemoFilteredIncidents(params: {
  status?: string;
}): PaginatedResponse<IncidentItem> {
  const { status } = params;
  let filtered = [...DEMO_INCIDENTS];

  if (status && status.toLowerCase() !== "all") {
    filtered = filtered.filter((i) => i.status.toLowerCase() === status.toLowerCase());
  }

  return { items: filtered, total_count: filtered.length, page: 1, page_size: 10, total_pages: 1 };
}

export function getDemoFilteredEvents(params: {
  page?: number;
  pageSize?: number;
  eventType?: string;
  severity?: string;
  search?: string;
}): PaginatedResponse<NormalizedSecurityEventItem> {
  const { page = 1, pageSize = 10, eventType, severity, search } = params;
  let filtered = [...DEMO_EVENTS];

  if (eventType && eventType.toLowerCase() !== "all") {
    filtered = filtered.filter((e) => e.event_type.toLowerCase() === eventType.toLowerCase());
  }
  if (severity && severity.toLowerCase() !== "all") {
    filtered = filtered.filter((e) => e.severity.toLowerCase() === severity.toLowerCase());
  }
  if (search && search.trim()) {
    const term = search.toLowerCase().trim();
    filtered = filtered.filter(
      (e) =>
        e.event_action.toLowerCase().includes(term) ||
        (e.user_name && e.user_name.toLowerCase().includes(term)) ||
        (e.source_ip && e.source_ip.toLowerCase().includes(term)) ||
        (e.destination_ip && e.destination_ip.toLowerCase().includes(term)) ||
        (e.host_name && e.host_name.toLowerCase().includes(term))
    );
  }

  const totalCount = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const offset = (page - 1) * pageSize;
  return { items: filtered.slice(offset, offset + pageSize), total_count: totalCount, page, page_size: pageSize, total_pages: totalPages };
}

export function getDemoLogSources(page: number = 1, pageSize: number = 10): PaginatedResponse<LogSourceItem> {
  return { items: DEMO_LOG_SOURCES, total_count: DEMO_LOG_SOURCES.length, page, page_size: pageSize, total_pages: 1 };
}

export function getDemoIngestionJobs(page: number = 1, pageSize: number = 10): PaginatedResponse<IngestionJobItem> {
  return { items: DEMO_INGESTION_JOBS, total_count: DEMO_INGESTION_JOBS.length, page, page_size: pageSize, total_pages: 1 };
}

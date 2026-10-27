"""Complete, repeatable demonstration data seeding script for Sentinel SOC Platform.

Provisions realistic, verifiable security telemetry across all platform subsystems:
1. Operational SOC users across all standard RBAC tiers (Admin, Responder, Engineer, Analyst, Manager)
2. Log sources representing heterogeneous enterprise sensors (AD DC, Perimeter Firewall, Zeek, Auditd)
3. Synchronized detection rules (RULE-AUTH-001, RULE-AUTH-002, RULE-SCAN-001, RULE-AUTH-003)
4. Normalized security events spanning failed auth clusters, port sweeps, and baseline benign telemetry
5. Engine-evaluated security alerts with evidence linkage and cryptographic deduplication
6. NIST SP 800-61 Rev 2 incident investigation dossiers with chained alerts and chronological notes

Usage:
    python backend/scripts/seed_demo_data.py [--reset]
"""

import argparse
import hashlib
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure backend directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import SessionLocal, engine
from app.engine.correlator import default_engine
from app.models.alert import AlertStatus, SecurityAlert
from app.models.base import Base
from app.models.event import EventSeverity, NormalizedSecurityEvent
from app.models.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    InvestigationNote,
    NoteType,
)
from app.models.log_source import LogSource, LogSourceStatus, LogSourceType
from app.models.user import User, UserRole, UserStatus

DEFAULT_DEMO_PASSWORD = os.getenv("SENTINEL_DEMO_PASSWORD", "Sentinel@Demo2026!")

DEMO_USERS = [
    {
        "username": "admin",
        "email": "admin@sentinel.org",
        "full_name": "Chief Security Architect (Admin)",
        "role": UserRole.ADMIN,
        "env_var": "INITIAL_ADMIN_PASSWORD",
    },
    {
        "username": "lead_responder",
        "email": "lead_responder@sentinel.org",
        "full_name": "Alex Vance (Incident Responder)",
        "role": UserRole.INCIDENT_RESPONDER,
        "env_var": "INITIAL_RESPONDER_PASSWORD",
    },
    {
        "username": "det_engineer",
        "email": "det_engineer@sentinel.org",
        "full_name": "Elena Rostova (Detection Engineer)",
        "role": UserRole.DETECTION_ENGINEER,
        "env_var": "INITIAL_ENGINEER_PASSWORD",
    },
    {
        "username": "tier1_analyst",
        "email": "tier1_analyst@sentinel.org",
        "full_name": "Robin Miller (Tier 1 Triage)",
        "role": UserRole.ANALYST_TIER_1,
        "env_var": "INITIAL_ANALYST_PASSWORD",
    },
    {
        "username": "soc_manager",
        "email": "soc_manager@sentinel.org",
        "full_name": "Morgan Chen (SOC Operations Manager)",
        "role": UserRole.SOC_MANAGER,
        "env_var": "INITIAL_MANAGER_PASSWORD",
    },
]

DEMO_SOURCES = [
    {
        "name": "Corp Active Directory Domain Controller",
        "source_type": LogSourceType.WINDOWS_EVENT_LOG,
        "description": "Primary identity provider emitting Kerberos & NTLM logon telemetry (Event IDs 4624, 4625)",
        "ip_address": "10.0.1.10",
        "hostname": "dc01.corp.sentinel.internal",
        "status": LogSourceStatus.ACTIVE,
    },
    {
        "name": "Perimeter Edge Firewall",
        "source_type": LogSourceType.APPLICATION_JSON,
        "description": "Egress/Ingress stateful edge firewall inspection engine",
        "ip_address": "198.51.100.1",
        "hostname": "fw-edge-01.perimeter.sentinel.internal",
        "status": LogSourceStatus.ACTIVE,
    },
    {
        "name": "Zeek Network Security Monitor",
        "source_type": LogSourceType.ZEEK_NETWORK,
        "description": "VLAN 10 Core switch span port packet telemetry and protocol metadata",
        "ip_address": "10.0.2.50",
        "hostname": "zeek-sensor-vlan10",
        "status": LogSourceStatus.ACTIVE,
    },
    {
        "name": "Linux Production Host Auditd Sensor",
        "source_type": LogSourceType.AUDITD,
        "description": "Linux audit framework capturing privileged execve invocations and file modifications",
        "ip_address": "10.0.3.15",
        "hostname": "app-srv-prod-01",
        "status": LogSourceStatus.ACTIVE,
    },
]


def make_hash(source_id: str, ts: datetime, payload: str) -> str:
    raw = f"{source_id}:{ts.isoformat()}:{payload}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def seed_database(reset: bool = False):
    print("=" * 76)
    print("  Sentinel SOC Platform — Comprehensive Synthetic Data Seeder")
    print("=" * 76)

    try:
        db: Session = SessionLocal()
        db.execute(text("SELECT 1"))
        if reset:
            print("[*] Rebuilding database schema (--reset requested)...")
            Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"[!] Database connection failed: {exc}")
        print("    Ensure PostgreSQL or SQLite DATABASE_URL is configured.")
        return

    try:
        # 1. Provision Users
        print("\n[+] 1. Provisioning baseline SOC accounts...")
        user_map = {}
        for u in DEMO_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            pwd = os.getenv(u["env_var"]) or DEFAULT_DEMO_PASSWORD
            if not existing:
                new_user = User(
                    username=u["username"],
                    email=u["email"],
                    full_name=u["full_name"],
                    role=u["role"],
                    status=UserStatus.ACTIVE,
                    hashed_password=hash_password(pwd),
                )
                db.add(new_user)
                db.flush()
                user_map[u["username"]] = new_user
                print(f"    • Created user: {u['username']:<15} (Role: {u['role'].value:<18}) Pass: {pwd}")
            else:
                user_map[u["username"]] = existing
                print(f"    • Existing user verified: {u['username']:<15}")

        # 2. Provision Log Sources
        print("\n[+] 2. Provisioning telemetry log sources...")
        source_map = {}
        for s in DEMO_SOURCES:
            existing = db.query(LogSource).filter(LogSource.name == s["name"]).first()
            if not existing:
                new_source = LogSource(**s)
                db.add(new_source)
                db.flush()
                source_map[s["name"]] = new_source
                print(f"    • Added sensor: {s['name']:<42} ({s['source_type'].value})")
            else:
                source_map[s["name"]] = existing
                print(f"    • Verified sensor: {s['name']:<42}")

        # 3. Synchronize Detection Rules
        print("\n[+] 3. Synchronizing detection rules into engine registry...")
        synced_rules = default_engine.sync_rules(db)
        for code, r in synced_rules.items():
            print(f"    • Rule active: {code:<16} | {r.name:<45} (Sev: {r.severity.value})")

        # 4. Generate Synthetic Telemetry Events
        print("\n[+] 4. Generating realistic normalized security telemetry...")
        now = datetime.now(timezone.utc)
        dc_source = source_map["Corp Active Directory Domain Controller"]
        fw_source = source_map["Perimeter Edge Firewall"]
        zeek_source = source_map["Zeek Network Security Monitor"]
        audit_source = source_map["Linux Production Host Auditd Sensor"]

        events_to_insert = []

        # Attack Cluster A: Repeated Failed Logins (RULE-AUTH-001) against svc_finance & admin
        attacker_ip = "198.51.100.45"
        for i in range(8):
            evt_time = now - timedelta(hours=3, minutes=10) + timedelta(seconds=i * 12)
            raw = f"dc01 Security Event 4625: Logon failure user=svc_finance src_ip={attacker_ip} port=52341 reason=bad_password"
            h = make_hash(str(dc_source.id), evt_time, raw)
            if not db.query(NormalizedSecurityEvent).filter(NormalizedSecurityEvent.event_hash == h).first():
                events_to_insert.append(
                    NormalizedSecurityEvent(
                        log_source_id=dc_source.id,
                        timestamp=evt_time,
                        event_type="authentication",
                        event_action="login_failed",
                        severity=EventSeverity.LOW,
                        source_ip=attacker_ip,
                        source_port=52341 + i,
                        destination_ip="10.0.1.10",
                        destination_port=88,
                        protocol="TCP",
                        user_name="svc_finance",
                        host_name="dc01.corp.sentinel.internal",
                        raw_payload=raw,
                        event_hash=h,
                        extra_fields={"logon_type": 3, "status_code": "0xC000006A"},
                    )
                )

        # Attack Cluster B: Credential Stuffing Success following failures (RULE-AUTH-002)
        # 6 failed admin attempts followed by 1 successful login
        for i in range(6):
            evt_time = now - timedelta(hours=2, minutes=45) + timedelta(seconds=i * 15)
            raw = f"dc01 Security Event 4625: Logon failure user=admin src_ip={attacker_ip} port=52400 reason=bad_password"
            h = make_hash(str(dc_source.id), evt_time, raw)
            if not db.query(NormalizedSecurityEvent).filter(NormalizedSecurityEvent.event_hash == h).first():
                events_to_insert.append(
                    NormalizedSecurityEvent(
                        log_source_id=dc_source.id,
                        timestamp=evt_time,
                        event_type="authentication",
                        event_action="login_failed",
                        severity=EventSeverity.LOW,
                        source_ip=attacker_ip,
                        source_port=52400 + i,
                        destination_ip="10.0.1.10",
                        destination_port=88,
                        protocol="TCP",
                        user_name="admin",
                        host_name="dc01.corp.sentinel.internal",
                        raw_payload=raw,
                        event_hash=h,
                        extra_fields={"logon_type": 3, "status_code": "0xC000006A"},
                    )
                )

        success_time = now - timedelta(hours=2, minutes=43)
        success_raw = f"dc01 Security Event 4624: An account was successfully logged on user=admin src_ip={attacker_ip} port=52410"
        success_hash = make_hash(str(dc_source.id), success_time, success_raw)
        if not db.query(NormalizedSecurityEvent).filter(NormalizedSecurityEvent.event_hash == success_hash).first():
            events_to_insert.append(
                NormalizedSecurityEvent(
                    log_source_id=dc_source.id,
                    timestamp=success_time,
                    event_type="authentication",
                    event_action="login_success",
                    severity=EventSeverity.INFORMATIONAL,
                    source_ip=attacker_ip,
                    source_port=52410,
                    destination_ip="10.0.1.10",
                    destination_port=88,
                    protocol="TCP",
                    user_name="admin",
                    host_name="dc01.corp.sentinel.internal",
                    raw_payload=success_raw,
                    event_hash=success_hash,
                    extra_fields={"logon_type": 3, "elevated_token": True},
                )
            )

        # Attack Cluster C: Reconnaissance Port Sweep (RULE-SCAN-001)
        scanner_ip = "203.0.113.88"
        scan_target_ip = "10.0.1.55"
        probe_ports = [21, 22, 23, 80, 443, 1433, 3306, 3389, 5432, 8080, 8443, 9000]
        for idx, port in enumerate(probe_ports):
            evt_time = now - timedelta(hours=1, minutes=20) + timedelta(seconds=idx * 2)
            raw = f"zeek_conn ts={evt_time.isoformat()} src={scanner_ip} dst={scan_target_ip} port={port} state=REJ proto=tcp"
            h = make_hash(str(zeek_source.id), evt_time, raw)
            if not db.query(NormalizedSecurityEvent).filter(NormalizedSecurityEvent.event_hash == h).first():
                events_to_insert.append(
                    NormalizedSecurityEvent(
                        log_source_id=zeek_source.id,
                        timestamp=evt_time,
                        event_type="network_flow",
                        event_action="connection_denied",
                        severity=EventSeverity.LOW,
                        source_ip=scanner_ip,
                        source_port=49152 + idx,
                        destination_ip=scan_target_ip,
                        destination_port=port,
                        protocol="TCP",
                        raw_payload=raw,
                        event_hash=h,
                        extra_fields={"conn_state": "REJ", "bytes_sent": 0},
                    )
                )

        # Attack Cluster D: Unusual Off-Hours Auth Velocity (RULE-AUTH-003)
        velocity_user = "sec_svc_backup"
        for idx, ip_addr in enumerate(["10.0.0.84", "172.16.5.99", "192.168.1.105"]):
            evt_time = now - timedelta(minutes=45) + timedelta(seconds=idx * 30)
            raw = f"auditd type=USER_AUTH user={velocity_user} addr={ip_addr} res=success"
            h = make_hash(str(audit_source.id), evt_time, raw)
            if not db.query(NormalizedSecurityEvent).filter(NormalizedSecurityEvent.event_hash == h).first():
                events_to_insert.append(
                    NormalizedSecurityEvent(
                        log_source_id=audit_source.id,
                        timestamp=evt_time,
                        event_type="authentication",
                        event_action="login_success",
                        severity=EventSeverity.INFORMATIONAL,
                        source_ip=ip_addr,
                        destination_ip="10.0.3.15",
                        destination_port=22,
                        protocol="SSH",
                        user_name=velocity_user,
                        host_name="app-srv-prod-01",
                        raw_payload=raw,
                        event_hash=h,
                        extra_fields={"terminal": "pts/0"},
                    )
                )

        # Benign Baseline Activity (spanning past 5 days)
        for d in range(1, 6):
            base_day = now - timedelta(days=d)
            for j in range(6):
                evt_time = base_day + timedelta(hours=8 + j * 2, minutes=15)
                raw = "fw-edge-01 ACCEPT flow src=10.0.1.200 dst=8.8.8.8 port=53 proto=udp bytes=142"
                h = make_hash(str(fw_source.id), evt_time, f"{raw}-{d}-{j}")
                if not db.query(NormalizedSecurityEvent).filter(NormalizedSecurityEvent.event_hash == h).first():
                    events_to_insert.append(
                        NormalizedSecurityEvent(
                            log_source_id=fw_source.id,
                            timestamp=evt_time,
                            event_type="network_flow",
                            event_action="connection_allowed",
                            severity=EventSeverity.INFORMATIONAL,
                            source_ip="10.0.1.200",
                            source_port=53530 + j,
                            destination_ip="8.8.8.8",
                            destination_port=53,
                            protocol="UDP",
                            raw_payload=raw,
                            event_hash=h,
                            extra_fields={"rule_matched": "ALLOW_OUTBOUND_DNS"},
                        )
                    )

        if events_to_insert:
            db.add_all(events_to_insert)
            db.commit()
            print(f"    • Seeded {len(events_to_insert)} new verifiable security events.")
        else:
            print("    • Verifiable events already present in database.")

        # 5. Evaluate Events through Detection Engine to produce real Alerts
        print("\n[+] 5. Evaluating telemetry with Correlation Detection Engine...")
        all_events = db.query(NormalizedSecurityEvent).all()
        generated_alerts = default_engine.evaluate_events(all_events, db)
        db.commit()
        print(f"    • Detection engine produced/updated {len(generated_alerts)} security alerts.")
        for a in generated_alerts:
            print(f"      - [{a.severity.value.upper():<8}] {a.title:<50} (Events: {a.event_count})")

        # 6. Provision Incidents and Investigation Dossiers
        print("\n[+] 6. Provisioning NIST SP 800-61 Rev 2 incident investigation dossiers...")
        resp_user = user_map.get("lead_responder") or db.query(User).filter(User.username == "lead_responder").first()
        tier1_user = user_map.get("tier1_analyst") or db.query(User).filter(User.username == "tier1_analyst").first()

        # Incident 1: Credential Compromise & Lateral Movement
        inc1 = db.query(Incident).filter(Incident.incident_number == "INC-2026-0001").first()
        if not inc1:
            inc1 = Incident(
                incident_number="INC-2026-0001",
                title="Suspected Credential Stuffing & Post-Auth Lateral Movement",
                summary=(
                    "External IP 198.51.100.45 launched multi-account authentication brute-force against dc01, "
                    "culminating in an anomalous successful Kerberos authentication under domain administrator context."
                ),
                severity=IncidentSeverity.SEV_1_CRITICAL,
                status=IncidentStatus.CONTAINMENT,
                lead_analyst_id=resp_user.id if resp_user else None,
                containment_details=(
                    "Targeted domain administrator account session revoked; temporary password reset enforced; "
                    "ingress IP 198.51.100.45 null-routed on perimeter border gateway."
                ),
                lessons_learned=(
                    "Mandate MFA enforcement across all externally accessible authentication gateways; "
                    "tune detection thresholds for consecutive failed login attempts."
                ),
            )
            db.add(inc1)
            db.flush()

            # Link alerts 1 and 2 to this incident
            target_alerts = db.query(SecurityAlert).filter(
                SecurityAlert.title.ilike("%admin%") | SecurityAlert.title.ilike("%login%")
            ).limit(2).all()
            for al in target_alerts:
                al.incident_id = inc1.id
                al.status = AlertStatus.ESCALATED

            # Investigation Notes
            db.add_all([
                InvestigationNote(
                    incident_id=inc1.id,
                    author_id=resp_user.id if resp_user else None,
                    note_type=NoteType.ANALYSIS,
                    content=(
                        "Correlated 14 authentication failures across svc_finance and admin within 180 seconds. "
                        "Subsequent login originating from identical non-corporate IP indicates successful credential compromise."
                    ),
                ),
                InvestigationNote(
                    incident_id=inc1.id,
                    author_id=resp_user.id if resp_user else None,
                    note_type=NoteType.CONTAINMENT_ACTION,
                    content=(
                        "Invoked active directory session revocation script. Egress network logs for dc01 confirm "
                        "no subsequent outbound lateral movement or large data transfers occurred prior to host isolation."
                    ),
                ),
                InvestigationNote(
                    incident_id=inc1.id,
                    author_id=resp_user.id if resp_user else None,
                    note_type=NoteType.FORENSIC_EVIDENCE,
                    content=(
                        "Supporting forensic records verified: Event hashes recorded in audit trail. "
                        "Perimeter firewall dropped subsequent probe traffic from 198.51.100.45."
                    ),
                ),
            ])
            print("    • Created Incident INC-2026-0001 (SEV-1 Critical | Status: Containment)")
        else:
            print("    • Incident INC-2026-0001 already provisioned.")

        # Incident 2: Port Sweep Reconnaissance (Resolved)
        inc2 = db.query(Incident).filter(Incident.incident_number == "INC-2026-0002").first()
        if not inc2:
            inc2 = Incident(
                incident_number="INC-2026-0002",
                title="Internal Subnet Multi-Port Reconnaissance Sweep",
                summary="Systematic TCP SYN probes detected contacting 12 distinct database and administrative ports on 10.0.1.55.",
                severity=IncidentSeverity.SEV_3_MEDIUM,
                status=IncidentStatus.RESOLVED,
                lead_analyst_id=tier1_user.id if tier1_user else None,
                containment_details="Verified source IP 203.0.113.88 as an authorized external penetration test by client SecOps audit team.",
                lessons_learned="Maintain centralized registry of scheduled vulnerability scans to prevent false-positive incident declarations.",
                closed_at=now - timedelta(hours=1),
            )
            db.add(inc2)
            db.flush()

            scan_alerts = db.query(SecurityAlert).filter(
                SecurityAlert.title.ilike("%port%") | SecurityAlert.title.ilike("%scan%")
            ).all()
            for al in scan_alerts:
                al.incident_id = inc2.id
                al.status = AlertStatus.CLOSED_RESOLVED

            db.add_all([
                InvestigationNote(
                    incident_id=inc2.id,
                    author_id=tier1_user.id if tier1_user else None,
                    note_type=NoteType.ANALYSIS,
                    content="Analyzed TCP SYN sweep across ports 21 through 9000. Verified matching ticket SEC-SCAN-889 in Change Management.",
                ),
                InvestigationNote(
                    incident_id=inc2.id,
                    author_id=tier1_user.id if tier1_user else None,
                    note_type=NoteType.CONTAINMENT_ACTION,
                    content="Added scanner IP to SIEM maintenance window exemption list. Incident resolved without incident escalation.",
                ),
            ])
            print("    • Created Incident INC-2026-0002 (SEV-3 Medium | Status: Resolved)")
        else:
            print("    • Incident INC-2026-0002 already provisioned.")

        db.commit()

        # Final Summary
        total_users = db.query(User).count()
        total_sources = db.query(LogSource).count()
        total_events = db.query(NormalizedSecurityEvent).count()
        total_alerts = db.query(SecurityAlert).count()
        total_incidents = db.query(Incident).count()

        print("\n" + "=" * 76)
        print("  Sentinel SOC Platform — Seeding Complete & Verified")
        print("=" * 76)
        print(f"  • Users in Database:       {total_users}")
        print(f"  • Log Sources Registered:  {total_sources}")
        print(f"  • Normalized Events:       {total_events}")
        print(f"  • Security Alerts:         {total_alerts}")
        print(f"  • NIST Incidents:          {total_incidents}")
        print("\n  Demonstration Login Credentials:")
        print(f"    - Admin Account:          admin          / {os.getenv('INITIAL_ADMIN_PASSWORD') or DEFAULT_DEMO_PASSWORD}")
        print(f"    - Incident Responder:     lead_responder / {os.getenv('INITIAL_RESPONDER_PASSWORD') or DEFAULT_DEMO_PASSWORD}")
        print(f"    - Detection Engineer:     det_engineer   / {os.getenv('INITIAL_ENGINEER_PASSWORD') or DEFAULT_DEMO_PASSWORD}")
        print(f"    - Tier 1 Analyst:         tier1_analyst  / {os.getenv('INITIAL_ANALYST_PASSWORD') or DEFAULT_DEMO_PASSWORD}")
        print(f"    - SOC Manager:            soc_manager    / {os.getenv('INITIAL_MANAGER_PASSWORD') or DEFAULT_DEMO_PASSWORD}")
        print("=" * 76 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel SOC Platform Data Seeder")
    parser.add_argument("--reset", action="store_true", help="Wipes and recreates schema before seeding")
    args = parser.parse_args()
    seed_database(reset=args.reset)

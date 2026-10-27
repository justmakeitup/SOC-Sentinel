"""Rule SEC-NET-001: Port-Scan-Like Multi-Port Sweep Detection."""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.engine.base import BaseDetectionRule, DetectionResult, RuleContext
from app.models.event import NormalizedSecurityEvent
from app.models.rule import RuleSeverity, RuleType


class PortScanRule(BaseDetectionRule):
    """Detects multi-port sweep reconnaissance against internal or external endpoints.

    This rule identifies synthetic scan traffic or unauthorized reconnaissance tools
    (e.g., Nmap, masscan, custom probe scripts) attempting to query multiple distinct
    destination ports on a target host within a short sliding time window.
    """

    rule_code = "SEC-NET-001"
    name = "Port-Scan-Like Multi-Port Sweep"
    description = (
        "Detects a single source IP attempting connection to multiple distinct destination "
        "ports on a target host within a sliding time window."
    )
    severity = RuleSeverity.MEDIUM
    rule_type = RuleType.THRESHOLD
    mitre_tactic = "Discovery"
    mitre_technique = "T1046 - Network Service Discovery"
    time_window_seconds = 60  # 60-second sliding window
    threshold_count = 5  # At least 5 distinct destination ports
    remediation_guidance = (
        "1. Check if the source IP belongs to an authorized vulnerability scanner or asset discovery tool.\n"
        "2. Review firewall actions (were the probes dropped, rejected, or allowed?).\n"
        "3. If unauthorized and persistent, apply host-level or perimeter ingress drop rules.\n"
        "4. Correlate with subsequent exploit attempts against any exposed open ports."
    )

    assumptions = [
        "Network flow or firewall telemetry records source IP, destination IP, and destination port.",
        "Probing events are delivered with reliable timestamp sequencing.",
    ]
    limitations = [
        "Distributed port scans (each port probed from a different IP) will not match a single-source threshold.",
        "Very slow stealth scans (e.g., one port probed per hour) bypass the short sliding window.",
    ]
    expected_false_positives = [
        "Enterprise vulnerability management scanners (Nessus, Qualys, Rapid7) conducting scheduled scans.",
        "IT monitoring tools performing host health checks or SNMP/WMI asset discovery sweeps.",
    ]

    def __init__(
        self,
        threshold_count: int = 5,
        time_window_seconds: int = 60,
    ) -> None:
        self.threshold_count = threshold_count
        self.time_window_seconds = time_window_seconds

    def evaluate(
        self,
        events: List[NormalizedSecurityEvent],
        context: Optional[RuleContext] = None,
    ) -> List[DetectionResult]:
        """Evaluates network connection attempts against unique destination port threshold."""
        window_sec = context.time_window_seconds if context else self.time_window_seconds
        threshold = (
            context.custom_params.get("threshold_count", self.threshold_count)
            if context and context.custom_params
            else self.threshold_count
        )

        # 1. Filter events with valid source IP, destination IP, and destination port
        network_events = [
            e
            for e in events
            if e.source_ip
            and e.destination_ip
            and e.destination_port is not None
        ]

        if not network_events:
            return []

        # 2. Group events by (source_ip, destination_ip)
        grouped: Dict[tuple, List[NormalizedSecurityEvent]] = defaultdict(list)
        for e in network_events:
            grouped[(e.source_ip, e.destination_ip)].append(e)

        results: List[DetectionResult] = []

        # 3. For each pair, evaluate sliding window for distinct destination ports
        for (src_ip, dst_ip), pair_events in grouped.items():
            sorted_events = sorted(pair_events, key=lambda ev: ev.timestamp)
            n = len(sorted_events)
            if n < threshold:
                continue

            i = 0
            while i < n:
                window_start = sorted_events[i].timestamp
                # Collect events in window
                window_events = [
                    ev
                    for ev in sorted_events[i:]
                    if (ev.timestamp - window_start).total_seconds() <= window_sec
                ]

                # Calculate unique ports contacted in this window
                distinct_ports = {ev.destination_port for ev in window_events if ev.destination_port is not None}

                if len(distinct_ports) >= threshold:
                    # Select representative supporting events (one per distinct port contacted)
                    supporting_evs: List[NormalizedSecurityEvent] = []
                    seen_ports = set()
                    for ev in window_events:
                        if ev.destination_port not in seen_ports:
                            seen_ports.add(ev.destination_port)
                            supporting_evs.append(ev)

                    first_ev = window_events[0]
                    last_ev = window_events[-1]
                    hour_bucket = last_ev.timestamp.strftime("%Y%m%d%H")
                    dedup_key = f"{self.rule_code}:{src_ip}:{dst_ip}:{hour_bucket}"

                    sorted_ports = sorted(list(distinct_ports))
                    evidence: Dict[str, Any] = {
                        "distinct_ports_contacted": len(distinct_ports),
                        "scanned_ports": sorted_ports[:50],
                        "threshold": threshold,
                        "time_window_seconds": window_sec,
                        "source_ip": src_ip,
                        "destination_ip": dst_ip,
                        "total_events_in_window": len(window_events),
                        "first_seen": first_ev.timestamp.isoformat(),
                        "last_seen": last_ev.timestamp.isoformat(),
                    }

                    results.append(
                        DetectionResult(
                            rule_code=self.rule_code,
                            title=f"Port Scan Detected: {src_ip} -> {dst_ip} ({len(distinct_ports)} ports)",
                            description=(
                                f"Source host '{src_ip}' probed {len(distinct_ports)} distinct destination "
                                f"ports on target '{dst_ip}' within {window_sec}s, exceeding threshold of {threshold}. "
                                f"Sample ports: {', '.join(str(p) for p in sorted_ports[:10])}."
                            ),
                            severity=self.severity,
                            deduplication_key=dedup_key,
                            affected_entities={
                                "source_ip": src_ip,
                                "destination_ip": dst_ip,
                            },
                            supporting_event_ids=[ev.id for ev in supporting_evs],
                            evidence=evidence,
                        )
                    )

                    # Advance index past this window
                    i += len(window_events)
                else:
                    i += 1

        return results

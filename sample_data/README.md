# Synthetic Demonstration Datasets

This directory contains synthetic security telemetry files for testing the Sentinel Log Ingestion Subsystem and Detection Engine.

## Files

1. **`synthetic_auth_bruteforce.csv`**:
   - Simulates 6 failed login attempts against `svc_finance` from `198.51.100.45`, followed by 6 failed attempts against `admin` and a subsequent successful authentication (`0x0`).
   - Triggers:
     - `RULE-AUTH-001` (Repeated Failed Logins)
     - `RULE-AUTH-002` (Login Following Multiple Failures)

2. **`synthetic_firewall_probes.json`**:
   - Simulates a TCP SYN multi-port sweep from `203.0.113.88` contacting 10 distinct destination ports on database host `10.0.1.55`.
   - Triggers:
     - `RULE-SCAN-001` (Port-Scan-Like Reconnaissance Sweep)

## How to Import via the Web Interface

1. Start both the backend and frontend servers.
2. In the Sentinel Web UI, navigate to the **Events** or **Log Sources** tab.
3. Click the **Import Logs** button in the top right.
4. Select a target log source (e.g. *Corp Active Directory Domain Controller* or *Perimeter Edge Firewall*).
5. Drag and drop or browse to select `synthetic_auth_bruteforce.csv` or `synthetic_firewall_probes.json`.
6. Click **Import & Normalize**.
7. Observe the events indexed in the **Events** table and the correlated findings generated in the **Alerts** queue.

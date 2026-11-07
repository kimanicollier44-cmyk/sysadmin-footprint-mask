"""🧠 Brains — HOLD gates.

A masked session on your OWN machine is the whole point of this tool.
Anything that crosses into someone else's system, a shared system's
audit trail, or hiding harmful activity is a HOLD — and no advisor,
flow, or Carbon 4 decision can override a HOLD.

Covered triggers:
  wipe_system_logs      deleting /var/log or a system audit trail
  disable_system_audit  stopping / disabling auditd or equivalent
  not_own_system        running against a system the user does not own
  remote_tamper         altering a remote system without its owner
  hide_malware          using the mask to hide malware / intrusion
  exfiltration          using the mask to exfiltrate data
  host_root_mount       mounting the host root or docker socket in
                        the sandbox (root-equivalent escape)
  history_to_disk       forcing shell history back onto persistent
                        disk inside a masked session
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Gate:
    trigger: str
    reason: str


def evaluate(request: dict) -> list[Gate]:
    """Return HOLD gates for a request; empty list = clear."""
    gates: list[Gate] = []
    action = str(request.get("action", "")).lower()
    purpose = str(request.get("purpose", "")).lower()
    target = str(request.get("target_path", "")).lower()

    if action in ("wipe_system_logs", "wipe_logs") or \
            target.startswith("/var/log"):
        gates.append(Gate(
            "wipe_system_logs",
            "Deleting system logs destroys an audit trail that is not "
            "yours to erase. This tool cleans only its own volatile "
            "/tmp workspace."))
    if action in ("disable_system_audit", "stop_auditd"):
        gates.append(Gate(
            "disable_system_audit",
            "A masked session is not a disabled audit daemon. Stopping "
            "system auditing is out of scope."))
    if request.get("own_system") is False:
        gates.append(Gate(
            "not_own_system",
            "The mask is for systems you own and administer. Running "
            "it on someone else's system is a HOLD."))
    if request.get("remote") and not request.get("remote_owner_consent"):
        gates.append(Gate(
            "remote_tamper",
            "Remote work needs the remote system owner's consent."))
    if purpose in ("malware", "hide_malware", "intrusion"):
        gates.append(Gate(
            "hide_malware",
            "Using a footprint mask to hide malware or an intrusion "
            "is a HOLD, permanently."))
    if purpose in ("exfiltration", "exfiltrate"):
        gates.append(Gate(
            "exfiltration",
            "Using a masked session to exfiltrate data is a HOLD."))
    if request.get("mount_host_root") or request.get("mount_docker_socket"):
        gates.append(Gate(
            "host_root_mount",
            "Mounting the host root filesystem or the Docker socket "
            "is root-equivalent escape from the sandbox."))
    if request.get("history_to_disk"):
        gates.append(Gate(
            "history_to_disk",
            "Forcing history onto persistent disk defeats the mask: "
            "history in a masked session is volatile-only."))
    return gates

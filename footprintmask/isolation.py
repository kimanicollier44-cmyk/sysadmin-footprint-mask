"""🔒 Secure execution wrapper — the Python model of bin/secure-exec.

Backend preference, exactly as supplied: Linux namespaces via
``unshare`` first, a rootless ``podman`` container second, and an
honest failure (no backend = no launch) when neither exists.
"""
from __future__ import annotations

NAMESPACES = ("ipc", "uts", "mount", "pid")
SANDBOX_HOSTNAME = "localhost"

BACKEND_ORDER = ("unshare", "podman")


def choose(available) -> dict:
    """Pick an isolation backend from the tools available on the host."""
    available = set(available)
    if "unshare" in available:
        return {"backend": "unshare", "held": False,
                "namespaces": list(NAMESPACES),
                "hostname": SANDBOX_HOSTNAME,
                "network": "loopback-up-inside-namespace",
                "argv": ["unshare", "--ipc", "--uts", "--mount",
                         "--fork", "--pid", "bash"]}
    if "podman" in available:
        return {"backend": "podman", "held": False,
                "namespaces": ["container"],
                "hostname": "container",
                "network": "none",
                "argv": ["podman", "run", "--rm", "-it", "--network=none",
                         "-v", "$(pwd):/opt/bin:ro", "alpine:latest", "sh"]}
    return {"backend": None, "held": True,
            "namespaces": [], "hostname": None, "network": None,
            "argv": [],
            "reason": "Neither unshare nor podman is available — "
                      "no isolated launch is possible."}

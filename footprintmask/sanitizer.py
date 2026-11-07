"""🧹 Environment sanitizer — the Python model of bin/sanitize-env.

Purges identifying / tracking environment variables, then installs a
sanitized baseline. Pure and deterministic: the input mapping is never
mutated, and the same input always produces the same clean environment.
Local, own-session use only — see brains.py for the HOLD gates.
"""
from __future__ import annotations

# Variables purged by bin/sanitize-env, in the supplied order.
PURGE_VARS = (
    "HISTFILE",
    "SSH_CLIENT",
    "SSH_CONNECTION",
    "SSH_TTY",
    "SUDO_USER",
    "SUDO_UID",
    "SUDO_GID",
    "USER",
    "LOGNAME",
)

WORKSPACE = "/tmp/secure-workspace"

BASELINE = {
    "USER": "root",
    "LOGNAME": "root",
    "HOME": WORKSPACE,
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "PS1": r"\[\033[01;31m\][secure-sysadmin] \w \$ ",
}

# Variables that must never survive sanitizing (a leak check list).
LEAK_VARS = PURGE_VARS + ("HISTFILE",)


def sanitize(env: dict) -> dict:
    """Return {clean_env, purged, workspace} for an environment mapping."""
    purged = [name for name in PURGE_VARS if name in env]
    clean = {k: v for k, v in env.items() if k not in PURGE_VARS}
    clean.update(BASELINE)
    return {"clean_env": clean, "purged": purged, "workspace": WORKSPACE,
            "workspace_mode": "0700"}


def leaks(env: dict) -> list[str]:
    """Names from LEAK_VARS still present with a non-baseline value."""
    found = []
    for name in PURGE_VARS:
        if name in env and env[name] != BASELINE.get(name):
            if name not in ("USER", "LOGNAME"):
                found.append(name)
            elif env[name] != BASELINE[name]:
                found.append(name)
    if "HISTFILE" in env:
        found.append("HISTFILE")
    return sorted(set(found))


def is_sanitized(env: dict) -> bool:
    """True when an env matches the sanitized baseline exactly on the
    controlled keys and carries no HISTFILE."""
    if "HISTFILE" in env:
        return False
    return all(env.get(k) == v for k, v in BASELINE.items())

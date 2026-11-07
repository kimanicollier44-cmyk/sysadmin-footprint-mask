"""📜 Shell profile rules — the model of configs/profile.d/footprint-mask.sh.

The profile keeps shell history in volatile memory only: history is
unset and sized to zero, core dumps are off, and new files are created
with a strict umask.
"""
from __future__ import annotations

RULES = {
    "HISTFILE": "unset",
    "HISTSIZE": "0",
    "HISTFILESIZE": "0",
    "core_dumps": "ulimit -c 0",
    "umask": "077",
}

_REQUIRED_TOKENS = (
    "unset HISTFILE",
    "HISTSIZE=0",
    "HISTFILESIZE=0",
    "ulimit -c 0",
    "umask 077",
)


def check_profile(text: str) -> dict:
    """Check a footprint-mask.sh text against every required rule."""
    missing = [t for t in _REQUIRED_TOKENS if t not in text]
    return {"ok": not missing, "missing": missing,
            "rules": dict(RULES)}

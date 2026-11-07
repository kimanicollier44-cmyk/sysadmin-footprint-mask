"""🧠 Gemini Carbon 4 Extended Thinking — merged brain layer.

"Gemini Carbon 4" is Darion's name for this 4-phase thinking
structure (same pattern as the YachtX Captain and the Shor-Rev-Engine
Carbon 4 layer); the engine underneath is Gemini 2.5 Pro extended
thinking. Applied to a completed masked-session plan:

  MAP    (front)  — map the session surface: which variables were
                    present, which were purged, the workspace, the
                    profile state
  MODEL  (middle) — model the isolation: backend, namespaces,
                    network posture, and the predicted leak list
  STRESS (middle) — stress the mask with negative controls: a leaky
                    environment (SSH_CLIENT put back) must be caught,
                    a history-on profile must fail its check, and a
                    host with no isolation backend must be held
  DECIDE (master) — combine with the brains verdict

Rules that never bend:
  - The deterministic offline structure is authoritative. Without a
    GEMINI_API_KEY present the layer still decides, in offline mode,
    and says so — the mode is never faked. The key is detected by
    NAME / PRESENCE ONLY; its value is never read out or stored.
  - Verdict strictness is HOLD > PROCEED. Carbon can only TIGHTEN:
    a brains PASS plus a failed stress check is a HOLD, and a brains
    HOLD stays HOLD — Carbon can NEVER override a brains HOLD.
"""
from __future__ import annotations

import os

from . import isolation as isolation_mod
from . import profile as profile_mod
from . import sanitizer as sanitizer_mod

NAME = "Gemini Carbon 4 Extended Thinking"
ENGINE_MODEL = "gemini-2.5-pro"
MODEL_ID = "google/gemini-carbon-4-extended-pro-thinking"
KEY_NAME = "GEMINI_API_KEY"

THINKING_TIERS = {"standard": 2048, "deep": 8192, "extended": 32768}
DEFAULT_TIER = "extended"

PHASES = ("MAP", "MODEL", "STRESS", "DECIDE")
PHASE_OWNERS = {"MAP": "front", "MODEL": "middle", "STRESS": "middle",
                "DECIDE": "master"}

_STRICTNESS = {"PROCEED": 0, "HOLD": 1}


def carbon_status() -> dict:
    present = KEY_NAME in os.environ
    return {"name": NAME, "engine": ENGINE_MODEL, "model_id": MODEL_ID,
            "key_name": KEY_NAME, "key_present": present,
            "mode": "live-key-present" if present else "offline",
            "thinking_tiers": dict(THINKING_TIERS),
            "thinking_budget": THINKING_TIERS[DEFAULT_TIER],
            "default_tier": DEFAULT_TIER, "can_override_hold": False}


def stricter(a: str, b: str) -> str:
    return a if _STRICTNESS[a] >= _STRICTNESS[b] else b


def run(report: dict) -> dict:
    """Run all 4 Carbon 4 phases over a masked-session report.

    report keys: env (original mapping), available (isolation tools),
    profile_text (footprint-mask.sh text), brain_verdict (PASS = clear).
    """
    status = carbon_status()
    env = report.get("env") or {}
    available = report.get("available") or []
    profile_text = report.get("profile_text") or ""
    brain_verdict = report.get("brain_verdict", "PASS")
    brain_decision = "PROCEED" if brain_verdict == "PASS" else "HOLD"
    phases = []

    # MAP (front)
    cleaned = sanitizer_mod.sanitize(env)
    map_out = {"purged": cleaned["purged"],
               "workspace": cleaned["workspace"],
               "present_before": sorted(env.keys())}
    phases.append({"phase": "MAP", "owner": PHASE_OWNERS["MAP"],
                   "output": (f"purged {len(map_out['purged'])} vars "
                              f"{map_out['purged']}; workspace "
                              f"{map_out['workspace']}"),
                   "detail": map_out})

    # MODEL (middle)
    iso = isolation_mod.choose(available)
    model_out = {"backend": iso["backend"], "held": iso["held"],
                 "namespaces": iso["namespaces"],
                 "predicted_leaks": sanitizer_mod.leaks(
                     cleaned["clean_env"])}
    phases.append({"phase": "MODEL", "owner": PHASE_OWNERS["MODEL"],
                   "output": (f"backend={iso['backend']}, namespaces="
                              f"{iso['namespaces']}, predicted leaks="
                              f"{model_out['predicted_leaks']}"),
                   "detail": model_out})

    # STRESS (middle) — negative controls
    checks = []
    leaky = dict(cleaned["clean_env"])
    leaky["SSH_CLIENT"] = "203.0.113.9 51234 22"
    checks.append({"name": "leaky_env_caught",
                   "ok": "SSH_CLIENT" in sanitizer_mod.leaks(leaky)
                   and "SSH_CLIENT" in sanitizer_mod.sanitize(leaky)[
                       "purged"]})
    bad_profile = profile_text.replace("HISTSIZE=0", "HISTSIZE=500")
    checks.append({"name": "history_on_profile_fails",
                   "ok": not profile_mod.check_profile(bad_profile)["ok"]})
    checks.append({"name": "good_profile_passes",
                   "ok": profile_mod.check_profile(profile_text)["ok"]})
    checks.append({"name": "no_backend_is_held",
                   "ok": isolation_mod.choose([])["held"] is True})
    checks.append({"name": "clean_env_is_sanitized",
                   "ok": sanitizer_mod.is_sanitized(cleaned["clean_env"])})
    stress_ok = all(c["ok"] for c in checks)
    phases.append({"phase": "STRESS", "owner": PHASE_OWNERS["STRESS"],
                   "output": (f"{sum(c['ok'] for c in checks)}/"
                              f"{len(checks)} stress checks passed"),
                   "detail": {"checks": checks, "ok": stress_ok}})

    # DECIDE (master) — can only tighten
    carbon_decision = "PROCEED" if stress_ok else "HOLD"
    decision = stricter(brain_decision, carbon_decision)
    phases.append({"phase": "DECIDE", "owner": PHASE_OWNERS["DECIDE"],
                   "output": (f"brains={brain_decision}, carbon="
                              f"{carbon_decision} -> {decision}"),
                   "detail": {"brain_decision": brain_decision,
                              "carbon_decision": carbon_decision,
                              "decision": decision}})
    return {"name": NAME, "status": status, "phases": phases,
            "decision": decision, "stress_ok": stress_ok}

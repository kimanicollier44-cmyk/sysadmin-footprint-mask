#!/usr/bin/env python3
"""sysadmin-footprint-mask — ONE interface.

    python3 main.py                    # full self-check (CHECKS n/n)
    python3 main.py --flows            # all merged Google flows + plan
    python3 main.py --carbon           # Gemini Carbon 4 decision
    python3 main.py --sanitize         # demo: sanitize a sample env
    python3 main.py --wipe-system-logs # HOLD demo (exit 2)
    python3 main.py --disable-audit    # HOLD demo (exit 2)

Zero dependencies. Local, own-system use only — see the HOLD gates.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

from footprintmask import carbon4, flows, isolation, profile, sandbox
from footprintmask import sanitizer
from footprintmask.blackbox import BlackBox
from footprintmask.brains import evaluate
from footprintmask.freeai import MUSE_MODELS, SEATS, detected

BOX = BlackBox()

SAMPLE_ENV = {
    "HISTFILE": "/home/operator/.bash_history",
    "SSH_CLIENT": "203.0.113.9 51234 22",
    "SSH_CONNECTION": "203.0.113.9 51234 192.0.2.10 22",
    "SUDO_USER": "operator",
    "USER": "operator",
    "LOGNAME": "operator",
    "HOME": "/home/operator",
    "PATH": "/custom/bin:/usr/bin",
    "EDITOR": "vim",
}


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def session_report() -> dict:
    gates = evaluate({"own_system": True})
    return {"env": dict(SAMPLE_ENV), "available": ["unshare", "podman"],
            "profile_text": _read("configs/profile.d/footprint-mask.sh"),
            "brain_verdict": "PASS" if not gates else "HOLD"}


def checks() -> tuple[int, int]:
    results: list[tuple[str, bool]] = []

    def check(name: str, cond: bool) -> None:
        results.append((name, bool(cond)))

    original = dict(SAMPLE_ENV)
    cleaned = sanitizer.sanitize(SAMPLE_ENV)
    check("sanitizer purges every present tracking var",
          set(cleaned["purged"]) >= {"HISTFILE", "SSH_CLIENT",
                                     "SSH_CONNECTION", "SUDO_USER",
                                     "USER", "LOGNAME"})
    check("sanitized env matches the baseline",
          sanitizer.is_sanitized(cleaned["clean_env"]))
    check("sanitizer never mutates its input", SAMPLE_ENV == original)
    check("workspace is the volatile /tmp/secure-workspace (0700)",
          cleaned["workspace"] == "/tmp/secure-workspace"
          and cleaned["workspace_mode"] == "0700")
    leaky = dict(cleaned["clean_env"])
    leaky["SSH_CLIENT"] = "203.0.113.9 51234 22"
    check("a leaked SSH_CLIENT is caught", "SSH_CLIENT" in sanitizer.leaks(leaky))
    check("the clean env has no leaks",
          sanitizer.leaks(cleaned["clean_env"]) == [])

    check("isolation prefers unshare over podman",
          isolation.choose(["podman", "unshare"])["backend"] == "unshare")
    pod = isolation.choose(["podman"])
    check("podman fallback is rootless with network none",
          pod["backend"] == "podman" and pod["network"] == "none")
    check("no isolation backend is an honest hold",
          isolation.choose([])["held"] is True)

    profile_text = _read("configs/profile.d/footprint-mask.sh")
    check("shipped profile passes every rule",
          profile.check_profile(profile_text)["ok"])
    check("a history-on profile fails the check",
          not profile.check_profile(
              profile_text.replace("HISTSIZE=0", "HISTSIZE=500"))["ok"])

    sandbox_text = _read("Dockerfile.sandbox")
    val = sandbox.validate_sandbox(sandbox_text)
    check("shipped Dockerfile.sandbox validates", val["ok"])
    check("sandbox is alpine:3.20, 7 packages, operator user",
          val["parsed"]["base_image"] == "alpine:3.20"
          and len(val["parsed"]["packages"]) == 7
          and val["parsed"]["runs_as_operator"])

    sanitize_sh = _read("bin/sanitize-env")
    check("bin/sanitize-env unsets every purge var on disk",
          all(f"unset {name}" in sanitize_sh
              for name in sanitizer.PURGE_VARS))
    exec_sh = _read("bin/secure-exec")
    check("bin/secure-exec offers unshare, then podman, then errors",
          "unshare" in exec_sh and "podman" in exec_sh
          and "exit 1" in exec_sh)

    check("all four Google flows are registered",
          flows.FLOW_IDS == ("gemini_flowx",
                             "google_workspace_studio_flows",
                             "google_flow_filmmaking",
                             "google_flow_engine"))
    plan = flows.flowx_plan()
    check("FlowX recommends the widest level (3 agents, queue wait 0)",
          plan["recommended_agents"] == 3 and plan["widest_level"] == 3
          and plan["queue_wait_ms_at_recommended"] == 0)
    check("FlowX critical path beats sequential",
          plan["critical_path_ms"] < plan["sequential_ms"])
    trig = flows.workspace_trigger("gmail")
    check("Workspace starter maps Gmail to email_trigger + chat step",
          trig["ok"] and trig["starter"] == "email_trigger"
          and "send_chat_message" in trig["steps"])
    check("an unknown starter kind is honestly not ok",
          flows.workspace_trigger("smoke_signal")["ok"] is False)
    board = flows.script_to_storyboard(["a", "b", "c", "d"])
    tl = flows.timeline()
    check("Filmmaking timeline is ordered setup/sanitize/exec/teardown",
          tl["ordered"] and board["frame_count"] == 4)
    route = flows.route_engine("workflow")
    check("Google Flow engine routes workflow as its primary capability",
          route["routable"] and route["primary"])
    merged = flows.merged_plan()
    check("the merged plan uses ALL four Google flows",
          merged["all_flows_used"])

    check("wiping system logs is a HOLD",
          any(g.trigger == "wipe_system_logs"
              for g in evaluate({"action": "wipe_system_logs"})))
    check("disabling the system audit daemon is a HOLD",
          any(g.trigger == "disable_system_audit"
              for g in evaluate({"action": "disable_system_audit"})))
    check("running on a system you do not own is a HOLD",
          any(g.trigger == "not_own_system"
              for g in evaluate({"own_system": False})))
    check("hiding malware is a HOLD",
          any(g.trigger == "hide_malware"
              for g in evaluate({"purpose": "malware"})))
    check("mounting the host root / docker socket is a HOLD",
          any(g.trigger == "host_root_mount"
              for g in evaluate({"mount_docker_socket": True})))
    check("a clean own-system session passes the brains",
          evaluate({"own_system": True}) == [])

    carbon = carbon4.run(session_report())
    check("Carbon 4 runs MAP/MODEL/STRESS/DECIDE in order",
          [p["phase"] for p in carbon["phases"]] ==
          ["MAP", "MODEL", "STRESS", "DECIDE"])
    check("Carbon 4 PROCEEDs a clean masked session",
          carbon["decision"] == "PROCEED" and carbon["stress_ok"])
    held = carbon4.run({**session_report(), "brain_verdict": "HOLD"})
    check("Carbon 4 can never override a brains HOLD",
          held["decision"] == "HOLD")
    bad = carbon4.run({**session_report(),
                       "profile_text": profile_text.replace(
                           "umask 077", "umask 022")})
    check("Carbon 4 HOLDs when a stress control fails",
          bad["decision"] == "HOLD" and not bad["stress_ok"])

    check("Muse seat is registered names-only (MODEL_API_KEY)",
          SEATS.get("muse") == "MODEL_API_KEY" and len(MUSE_MODELS) == 2)
    check("freeai detection returns seat names, never values",
          all(s in SEATS for s in detected()))
    for ev in ("session", "flows", "carbon"):
        BOX.log(ev, {"ok": True})
    check("blackbox hash chain verifies", BOX.verify())

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return passed, len(results)


def main(argv: list[str]) -> int:
    args = argv[1:]
    if "--wipe-system-logs" in args:
        for g in evaluate({"action": "wipe_system_logs"}):
            print(f"HOLD [{g.trigger}] {g.reason}")
        print("VERDICT: HOLD")
        return 2
    if "--disable-audit" in args:
        for g in evaluate({"action": "disable_system_audit"}):
            print(f"HOLD [{g.trigger}] {g.reason}")
        print("VERDICT: HOLD")
        return 2
    if "--flows" in args:
        for f in flows.FLOWS:
            print(f"{f['id']:34s} {f['kind']:8s} {f['name']} "
                  f"<- {f['source']}")
        merged = flows.merged_plan()
        print(f"merged plan uses all flows: {merged['all_flows_used']}")
        print(f"FlowX recommended agents: "
              f"{merged['flowx']['recommended_agents']}")
        return 0
    if "--carbon" in args:
        carbon = carbon4.run(session_report())
        for p in carbon["phases"]:
            print(f"{p['phase']:7s} ({p['owner']}) {p['output']}")
        print(f"DECISION: {carbon['decision']} "
              f"(mode: {carbon['status']['mode']})")
        return 0 if carbon["decision"] == "PROCEED" else 2
    if "--sanitize" in args:
        cleaned = sanitizer.sanitize(dict(SAMPLE_ENV))
        print(f"purged: {cleaned['purged']}")
        for k, v in cleaned["clean_env"].items():
            print(f"  {k}={v}")
        return 0

    print("sysadmin-footprint-mask — local SysAdmin mask + footprint sanitizer")
    print("Own-system, local, educational. System logs / audit = HOLD.")
    print(f"Google flows merged: {len(flows.FLOWS)} "
          f"({', '.join(flows.FLOW_IDS)})")
    print("Running checks:")
    passed, total = checks()
    print(f"CHECKS {passed}/{total} {'PASS' if passed == total else 'FAIL'}")
    print(f"VERDICT: {'PROCEED' if passed == total else 'HOLD'}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

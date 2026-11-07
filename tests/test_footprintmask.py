"""Tests for sysadmin-footprint-mask."""
from pathlib import Path

from footprintmask import carbon4, flows, isolation, profile, sandbox
from footprintmask import sanitizer
from footprintmask.blackbox import BlackBox
from footprintmask.brains import evaluate
from footprintmask.freeai import SEATS, detected

ROOT = Path(__file__).resolve().parent.parent

ENV = {"HISTFILE": "/home/o/.bash_history", "SSH_CLIENT": "x",
       "SUDO_USER": "o", "USER": "o", "LOGNAME": "o", "EDITOR": "vim"}


def test_sanitize_purges_and_baselines():
    out = sanitizer.sanitize(dict(ENV))
    assert "SSH_CLIENT" in out["purged"]
    assert sanitizer.is_sanitized(out["clean_env"])
    assert out["clean_env"]["EDITOR"] == "vim"


def test_sanitize_does_not_mutate():
    env = dict(ENV)
    sanitizer.sanitize(env)
    assert env == ENV


def test_leaks_catch_put_back_var():
    clean = sanitizer.sanitize(dict(ENV))["clean_env"]
    clean["SSH_CLIENT"] = "x"
    assert "SSH_CLIENT" in sanitizer.leaks(clean)


def test_isolation_prefers_unshare():
    assert isolation.choose(["podman", "unshare"])["backend"] == "unshare"


def test_isolation_podman_fallback_network_none():
    plan = isolation.choose(["podman"])
    assert plan["backend"] == "podman" and plan["network"] == "none"


def test_isolation_no_backend_held():
    assert isolation.choose([])["held"] is True


def test_profile_shipped_ok():
    text = (ROOT / "configs/profile.d/footprint-mask.sh").read_text()
    assert profile.check_profile(text)["ok"]


def test_profile_history_on_fails():
    text = (ROOT / "configs/profile.d/footprint-mask.sh").read_text()
    assert not profile.check_profile(
        text.replace("HISTSIZE=0", "HISTSIZE=9"))["ok"]


def test_sandbox_shipped_validates():
    text = (ROOT / "Dockerfile.sandbox").read_text()
    val = sandbox.validate_sandbox(text)
    assert val["ok"] and len(val["parsed"]["packages"]) == 7


def test_bash_scripts_carry_the_spec():
    s = (ROOT / "bin/sanitize-env").read_text()
    assert all(f"unset {v}" in s for v in sanitizer.PURGE_VARS)
    e = (ROOT / "bin/secure-exec").read_text()
    assert "unshare" in e and "podman" in e and "exit 1" in e


def test_all_four_google_flows_registered():
    assert flows.FLOW_IDS == ("gemini_flowx",
                              "google_workspace_studio_flows",
                              "google_flow_filmmaking",
                              "google_flow_engine")


def test_flowx_recommends_widest_level():
    plan = flows.flowx_plan()
    assert plan["recommended_agents"] == plan["widest_level"] == 3
    assert plan["queue_wait_ms_at_recommended"] == 0
    assert plan["critical_path_ms"] < plan["sequential_ms"]


def test_workspace_starters():
    assert flows.workspace_trigger("gmail")["starter"] == "email_trigger"
    assert flows.workspace_trigger("google_forms")["starter"] == \
        "form_trigger"
    assert flows.workspace_trigger("webhook")["starter"] == \
        "webhook_listener"
    assert flows.workspace_trigger("nope")["ok"] is False


def test_filmmaking_timeline_and_storyboard():
    assert flows.timeline()["ordered"]
    assert flows.script_to_storyboard(["a", "b"])["frame_count"] == 2


def test_google_flow_engine_routes_workflow_primary():
    route = flows.route_engine("workflow")
    assert route["routable"] and route["primary"]


def test_merged_plan_uses_all_flows():
    assert flows.merged_plan()["all_flows_used"]


def test_brains_hold_gates():
    assert any(g.trigger == "wipe_system_logs"
               for g in evaluate({"action": "wipe_system_logs"}))
    assert any(g.trigger == "wipe_system_logs"
               for g in evaluate({"target_path": "/var/log/auth.log"}))
    assert any(g.trigger == "disable_system_audit"
               for g in evaluate({"action": "stop_auditd"}))
    assert any(g.trigger == "not_own_system"
               for g in evaluate({"own_system": False}))
    assert any(g.trigger == "hide_malware"
               for g in evaluate({"purpose": "intrusion"}))
    assert any(g.trigger == "exfiltration"
               for g in evaluate({"purpose": "exfiltration"}))
    assert any(g.trigger == "host_root_mount"
               for g in evaluate({"mount_host_root": True}))
    assert any(g.trigger == "history_to_disk"
               for g in evaluate({"history_to_disk": True}))


def test_brains_clean_session_clear():
    assert evaluate({"own_system": True}) == []


def _report(**overrides):
    report = {"env": dict(ENV), "available": ["unshare"],
              "profile_text": (
                  ROOT / "configs/profile.d/footprint-mask.sh").read_text(),
              "brain_verdict": "PASS"}
    report.update(overrides)
    return report


def test_carbon_phases_and_proceed():
    out = carbon4.run(_report())
    assert [p["phase"] for p in out["phases"]] == list(carbon4.PHASES)
    assert out["decision"] == "PROCEED" and out["stress_ok"]


def test_carbon_never_overrides_brains_hold():
    assert carbon4.run(_report(brain_verdict="HOLD"))["decision"] == "HOLD"


def test_carbon_holds_on_failed_stress():
    bad = (ROOT / "configs/profile.d/footprint-mask.sh").read_text() \
        .replace("umask 077", "umask 022")
    out = carbon4.run(_report(profile_text=bad))
    assert out["decision"] == "HOLD" and not out["stress_ok"]


def test_carbon_status_names_only():
    status = carbon4.carbon_status()
    assert status["model_id"] == \
        "google/gemini-carbon-4-extended-pro-thinking"
    assert status["thinking_budget"] == 32768
    assert status["can_override_hold"] is False


def test_freeai_names_only():
    assert SEATS["muse"] == "MODEL_API_KEY"
    assert all(s in SEATS for s in detected())


def test_blackbox_chain():
    box = BlackBox()
    box.log("a", {"ok": True})
    box.log("b", {"ok": True})
    assert box.verify()

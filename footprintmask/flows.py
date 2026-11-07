"""🌊 All the Google flows, merged — one registry, one merged plan.

Four Google flow systems from Darion's own repos / merge trees, merged
into this project:

  1. gemini_flowx — Gemini-FlowX, from ddkellar01/Google-FlowX.
     Gemini Pro Thinking multi-agent orchestration: a task is
     decomposed into a subtask graph and the planner recommends the
     zero-latency agent count (the widest parallel level).
  2. google_workspace_studio_flows — Google Workspace Studio Flows,
     from the google-workspace-studio-flows tree in the Intuition
     merge. Workspace Add-on flows: starters (Gmail, Forms, webhook),
     steps, and UI cards for step configuration.
  3. google_flow_filmmaking — Google Flow Filmmaking, from the
     google-flow-filmmaking tree in the Intuition merge. A timeline
     engine: multi-track editing, script-to-storyboard planning.
     Here the tracks are the phases of one masked session.
  4. google_flow_engine — Google Flow, the engine seat in
     ddkellar01/DataX (engine_id google_flow, capabilities workflow /
     automation / reasoning, primary workflow): the workflow / ADK
     loop orchestration router that dispatches the merged plan.

Seat rules (same as every merged project): the Gemini key name is
GEMINI_API_KEY, detected by NAME / PRESENCE ONLY — its value is never
read out, printed, or stored. The deterministic offline planners are
authoritative; a live call could only tighten a plan, never loosen
a gate.
"""
from __future__ import annotations

import os

KEY_NAME = "GEMINI_API_KEY"
MODEL = "gemini-2.5-pro"
THINKING_BUDGET = 32768

# ---------------------------------------------------------------- 1. FlowX
# Subtask graph for ONE masked session: [name, duration_ms_est, [deps]].
GRAPH = [
    ["start-session", 100, []],
    ["sanitize-env", 200, ["start-session"]],
    ["load-profile", 100, ["start-session"]],
    ["check-isolation", 150, ["start-session"]],
    ["launch-isolated-exec", 300, ["check-isolation", "sanitize-env"]],
    ["mount-volatile-workspace", 200, ["sanitize-env", "load-profile"]],
    ["run-admin-task", 400, ["launch-isolated-exec",
                             "mount-volatile-workspace"]],
    ["capture-lineage", 100, ["run-admin-task"]],
    ["teardown-workspace", 150, ["run-admin-task"]],
    ["report", 100, ["capture-lineage", "teardown-workspace"]],
]

ROLES = ["starter", "sanitizer", "isolation", "operator", "reporter"]


def seat_status() -> dict:
    present = KEY_NAME in os.environ
    return {"provider": "google-gemini", "model": MODEL,
            "key_name": KEY_NAME, "key_present": present,
            "mode": "live-key-present" if present else "offline",
            "thinking_budget": THINKING_BUDGET,
            "offline_authoritative": True, "live_can_loosen": False}


def levels_of(graph: list) -> list:
    done: dict = {}
    levels: list = []
    remaining = list(graph)
    while remaining:
        ready = [t for t in remaining if all(d in done for d in t[2])]
        if not ready:
            raise ValueError("dependency cycle or missing dependency")
        for t in ready:
            done[t[0]] = len(levels)
        levels.append(ready)
        remaining = [t for t in remaining if t not in ready]
    return levels


def flowx_plan(graph: list | None = None) -> dict:
    """Gemini-FlowX plan: recommended agents = widest parallel level."""
    graph = GRAPH if graph is None else graph
    levels = levels_of(graph)
    widest = max(len(level) for level in levels)
    sequential = sum(t[1] for t in graph)
    critical = sum(max(t[1] for t in level) for level in levels)
    roster = []
    for li, level in enumerate(levels):
        for i, t in enumerate(level):
            roster.append({"agent": f"agent-{li}-{i + 1}",
                           "role": ROLES[(li + i) % len(ROLES)],
                           "subtask": t[0], "level": li,
                           "duration_ms_est": t[1]})
    return {"subtasks": [t[0] for t in graph],
            "levels": [[t[0] for t in level] for level in levels],
            "levels_count": len(levels),
            "widest_level": widest,
            "recommended_agents": widest,
            "sequential_ms": sequential,
            "critical_path_ms": critical,
            "wall_clock_ms_at_recommended": critical,
            "queue_wait_ms_at_recommended": 0,
            "speedup_vs_1_agent": round(sequential / critical, 2)
            if critical else 0,
            "extra_agents_beyond_recommended_buy":
                "nothing - width is the parallel limit",
            "roster": roster, "seat": seat_status()}


# ------------------------------------------- 2. Workspace Studio Flows
STARTERS = {
    "gmail": "email_trigger",
    "google_forms": "form_trigger",
    "webhook": "webhook_listener",
}
STEPS = ("send_chat_message", "card_layout")
WORKSPACE_FILES = (
    "manifest.json", "studio_config.json",
    "starters/email_trigger.ts", "starters/form_trigger.ts",
    "starters/webhook_listener.ts", "steps/send_chat_message.ts",
    "card_layout.ts",
)


def workspace_trigger(kind: str, detail: str = "") -> dict:
    """Map an event kind to its Workspace Studio starter + steps."""
    starter = STARTERS.get(kind)
    if starter is None:
        return {"ok": False, "starter": None, "steps": [],
                "reason": f"no Workspace starter for kind {kind!r}"}
    message = (f"[footprint-mask] {starter}: masked session requested"
               + (f" — {detail}" if detail else ""))
    return {"ok": True, "starter": starter, "steps": list(STEPS),
            "chat_message": message,
            "card": {"title": "footprint-mask session",
                     "starter": starter, "configurable": True}}


# --------------------------------------------- 3. Flow Filmmaking flow
# The filmmaking timeline's tracks, mapped to a masked session.
TRACKS = ("setup", "sanitize", "exec", "teardown")


def timeline(frames: list | None = None) -> dict:
    """A multi-track timeline for one masked session run."""
    frames = frames or [
        {"track": "setup", "shot": "start-session + load-profile"},
        {"track": "sanitize", "shot": "sanitize-env purges + baseline"},
        {"track": "exec", "shot": "secure-exec in isolated namespace"},
        {"track": "teardown", "shot": "purge volatile workspace"},
    ]
    return {"tracks": list(TRACKS),
            "frames": frames,
            "ordered": [f["track"] for f in frames] == list(TRACKS)}


def script_to_storyboard(runbook: list[str]) -> dict:
    """Script-to-storyboard: each runbook line becomes one frame."""
    frames = []
    for i, line in enumerate(runbook):
        track = TRACKS[min(i, len(TRACKS) - 1)] if i < len(TRACKS) \
            else TRACKS[-1]
        frames.append({"frame": i + 1, "track": track, "shot": line})
    return {"frames": frames, "frame_count": len(frames)}


# ------------------------------------------------- 4. Google Flow engine
ENGINE = {"engine_id": "google_flow", "name": "Google Flow",
          "env_var": "GOOGLE_FLOW_API_KEY",
          "capabilities": ("workflow", "automation", "reasoning"),
          "primary_capabilities": ("workflow",),
          "priority": 5, "timeout_s": 25.0,
          "description": "Workflow / ADK loop orchestration."}


def route_engine(task_kind: str) -> dict:
    """Route a task kind through the DataX Google Flow engine seat."""
    primary = task_kind in ENGINE["primary_capabilities"]
    return {"engine_id": ENGINE["engine_id"],
            "task_kind": task_kind,
            "primary": primary,
            "routable": task_kind in ENGINE["capabilities"],
            "env_var": ENGINE["env_var"]}


# ------------------------------------------------------------ the registry
FLOWS = (
    {"id": "gemini_flowx", "name": "Gemini-FlowX (Google-FlowX)",
     "source": "ddkellar01/Google-FlowX", "kind": "planner"},
    {"id": "google_workspace_studio_flows",
     "name": "Google Workspace Studio Flows",
     "source": "google-workspace-studio-flows (Intuition merge tree)",
     "kind": "starter"},
    {"id": "google_flow_filmmaking", "name": "Google Flow Filmmaking",
     "source": "google-flow-filmmaking (Intuition merge tree)",
     "kind": "timeline"},
    {"id": "google_flow_engine", "name": "Google Flow (DataX engine)",
     "source": "ddkellar01/DataX engine google_flow", "kind": "router"},
)

FLOW_IDS = tuple(f["id"] for f in FLOWS)


def merged_plan(trigger_kind: str = "webhook",
                runbook: list[str] | None = None) -> dict:
    """Run ALL four Google flows over one masked-session request.

    Workspace starter fires -> FlowX sizes the agent pool -> the
    Filmmaking timeline sequences the session -> the Google Flow
    engine routes the workflow task. Every flow contributes; a plan
    missing any flow is not a merged plan.
    """
    runbook = runbook or [
        "start the masked session and load the profile",
        "sanitize the environment and mount the volatile workspace",
        "run the admin task inside the isolated namespace",
        "tear down and purge the volatile workspace",
    ]
    starter = workspace_trigger(trigger_kind)
    plan = flowx_plan()
    board = script_to_storyboard(runbook)
    tl = timeline(board["frames"] and [
        {"track": f["track"], "shot": f["shot"]} for f in board["frames"]])
    route = route_engine("workflow")
    used = [f["id"] for f in FLOWS]
    return {"flows_used": used, "all_flows_used": set(used) == set(FLOW_IDS),
            "starter": starter, "flowx": plan, "storyboard": board,
            "timeline": tl, "route": route}

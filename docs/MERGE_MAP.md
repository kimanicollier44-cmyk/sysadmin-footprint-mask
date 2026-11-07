# 🔀 Merge map — all the Google flows + Gemini Carbon 4

## 🌊 The four Google flows, and where each one lives

| # | Flow | Source | Where it landed |
|---|------|--------|-----------------|
| 1 | 🌀 Gemini-FlowX (Google-FlowX) | `ddkellar01/Google-FlowX` | `footprintmask/flows.py` — `flowx_plan()`, subtask `GRAPH`, recommended agents = widest level (3) |
| 2 | 🏢 Google Workspace Studio Flows | `google-workspace-studio-flows/` tree (Intuition merge) | `footprintmask/flows.py` — `STARTERS`, `STEPS`, `workspace_trigger()`, `WORKSPACE_FILES` |
| 3 | 🎬 Google Flow Filmmaking | `google-flow-filmmaking/` tree (Intuition merge) | `footprintmask/flows.py` — `TRACKS`, `timeline()`, `script_to_storyboard()` |
| 4 | ⚙️ Google Flow engine | `ddkellar01/DataX`, engine `google_flow` | `footprintmask/flows.py` — `ENGINE`, `route_engine()` |

`merged_plan()` runs all four over one request: the Workspace starter
fires → FlowX sizes the agent pool → the Filmmaking timeline sequences
the session → the Google Flow engine routes the workflow task. The
self-check proves `all_flows_used` is true.

## 🧠 Gemini Carbon 4 Extended Thinking

- Where: `footprintmask/carbon4.py`
- Pattern: MAP (front) → MODEL (middle) → STRESS (middle) → DECIDE
  (master), the same structure as the YachtX Captain and the
  Shor-Rev-Engine Carbon 4 layer.
- Engine underneath: Gemini 2.5 Pro; model id
  `google/gemini-carbon-4-extended-pro-thinking`; thinking tiers
  2048 / 8192 / 32768 (extended is the default).
- Rules: deterministic offline structure is authoritative; the key
  (`GEMINI_API_KEY`) is detected by name/presence only; Carbon can
  only tighten a verdict (HOLD > PROCEED) and can never override a
  brains HOLD.

## 🤖 The Muse seat

`footprintmask/freeai.py` keeps the provider seat registry
names-only, with the Meta Muse seat (`MODEL_API_KEY`, models
`muse-spark-1.1` / `muse-wonder-1.0`) as a must-plug advisor that
never overrides a HOLD.

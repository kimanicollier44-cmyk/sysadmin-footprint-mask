# 📋 Spec as supplied

Source: Darion's 7.5-second screen video (2026-11-05) of a Gemini Auto
conversation titled "Create repo mask local SysAdmin, digital
footprint Cover For educational purposes".

## What the video showed, in order

- Title: an enterprise-grade repository template and execution
  framework for a local **System Administration Mask and Digital
  Footprint Sanitizer**.
- Purpose line: establish an isolated, low-telemetry operational
  workspace; strip identifying environment variables; manage volatile
  session histories via tmpfs; wrap administrative routines in
  containerized or namespace-isolated boundaries to minimize local
  leakage during systems auditing and infrastructure management.
- Tree: `sysadmin-footprint-mask/` with `bin/sanitize-env`,
  `bin/secure-exec`, `configs/profile.d/footprint-mask.sh`,
  `configs/audit.rules`, `Dockerfile.sandbox`, `Makefile`,
  `README.md`.
- Five components, each with a code block:
  1. Environment Sanitizer (`bin/sanitize-env`)
  2. Secure Execution Wrapper (`bin/secure-exec`)
  3. Shell Profile Configuration (`configs/profile.d/footprint-mask.sh`)
  4. Ephemeral Docker Sandbox (`Dockerfile.sandbox`)
  5. Automation Lifecycle (`Makefile`)
- Implementation instructions: create the tree, populate the files,
  `chmod +x bin/sanitize-env bin/secure-exec`, run
  `./bin/sanitize-env bash`.
- Gemini's closing question offered automated log wiping / proxy
  tunneling as an expansion, with "Yes" selected in the video.

## ⚠️ Mismatches / completions, flagged separately (not hidden)

- Several code lines were cut off at the right edge of the phone
  frame (long `export PATH=...`, the `PS1=...` string, the
  `unshare ...` line, the `podman run ...` line, and the Makefile
  recipes). Those scripts are completed to working form in this repo
  using the visible fragments and the component descriptions; every
  completion is a faithful finish of the visible line, not a redesign.
- `configs/audit.rules` appeared in the tree only — no content was
  visible. This repo ships it as a commented template, never installed.
- The offered "automated log wiping" expansion is **not** built:
  deleting system logs is a HOLD gate here (`wipe_system_logs`), and
  disabling system audit is a HOLD gate too (`disable_system_audit`).
  This tool cleans only its own volatile `/tmp/secure-workspace`.

"""🐳 Ephemeral Docker sandbox — the model of Dockerfile.sandbox."""
from __future__ import annotations

BASE_IMAGE = "alpine:3.20"
PACKAGES = ("bash", "curl", "iproute2", "iptables", "openssh-client",
            "git", "coreutils")
OPERATOR_UID = 1000
ENTRYPOINT = "/bin/bash"


def parse_sandbox(text: str) -> dict:
    """Extract the facts that matter from a Dockerfile.sandbox text."""
    return {
        "base_image": BASE_IMAGE if f"FROM {BASE_IMAGE}" in text else None,
        "packages": [p for p in PACKAGES if p in text],
        "operator_uid": OPERATOR_UID if "-u 1000" in text else None,
        "runs_as_operator": "USER operator" in text,
        "entrypoint": ENTRYPOINT if ENTRYPOINT in text else None,
    }


def validate_sandbox(text: str) -> dict:
    parsed = parse_sandbox(text)
    problems = []
    if parsed["base_image"] is None:
        problems.append("base image is not alpine:3.20")
    if len(parsed["packages"]) != len(PACKAGES):
        problems.append("package list is incomplete")
    if not parsed["runs_as_operator"]:
        problems.append("sandbox does not drop to USER operator")
    if "USER root" in text:
        problems.append("sandbox explicitly runs as root")
    return {"ok": not problems, "problems": problems, "parsed": parsed}

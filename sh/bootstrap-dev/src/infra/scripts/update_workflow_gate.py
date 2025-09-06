# scripts/update_workflow_gates.py
from __future__ import annotations
from pathlib import Path
import sys
import shutil
from datetime import datetime
import glob

# Prefer ruamel.yaml for round-tripping; fall back to pyyaml
try:
    from ruamel.yaml import YAML  # type: ignore
    YAML_LIB = "ruamel"
except Exception:  # pragma: no cover
    import yaml  # type: ignore
    YAML_LIB = "pyyaml"

MAIN = Path(".github/workflows/ai_guardrails_on_commit.yaml")

def discover_gate_workflows():
    """Discover gate workflow files from plugins and return gate job names."""
    gate_workflows = []
    gate_jobs = []

    # Search for workflow files in plugin directories
    plugin_patterns = [
        "src/plugins/*/.github/workflows/*.yml",
        "src/plugins/*/.github/workflows/*.yaml",
        "src/plugins/*/templates/.github/workflows/*.yml",
        "src/plugins/*/templates/.github/workflows/*.yaml"
    ]

    for pattern in plugin_patterns:
        for workflow_path in glob.glob(pattern):
            workflow_file = Path(workflow_path)
            # Skip the main workflow to avoid circular dependencies
            if "ai_guardrails_on_commit" in workflow_file.name or "ai-guardrails-full" in workflow_file.name:
                continue

            # Extract workflow name for gate job
            workflow_name = workflow_file.stem.replace("-", "_").replace(" ", "_")
            gate_job_name = f"gate_{workflow_name}"

            # Determine the relative path for reusable workflow call
            relative_path = f"./.github/workflows/{workflow_file.name}"

            gate_workflows.append({
                "job_name": gate_job_name,
                "workflow_path": relative_path,
                "source_file": workflow_file
            })
            gate_jobs.append(gate_job_name)

    return gate_workflows, gate_jobs

GATE_WORKFLOWS, GATES = discover_gate_workflows()

def load_yaml(path: Path):
    if YAML_LIB == "ruamel":
        y = YAML()
        y.preserve_quotes = True
        y.indent(mapping=2, sequence=4, offset=2)
        with path.open("r", encoding="utf-8") as f:
            data = y.load(f) or {}
        return y, data
    else:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return None, data

def dump_yaml(path: Path, loader, data):
    if YAML_LIB == "ruamel":
        loader.dump(data, path.open("w", encoding="utf-8"))
    else:
        path.write_text(
            # default_flow_style=False gives block YAML; sort_keys=False preserves order best-effort
            yaml.safe_dump(data, sort_keys=False),
            encoding="utf-8",
        )

def ensure_gate_calls(data: dict) -> None:
    """Ensure gate jobs exist as reusable workflow calls."""
    jobs = data.setdefault("jobs", {})

    for gate_workflow in GATE_WORKFLOWS:
        job_name = gate_workflow["job_name"]
        workflow_path = gate_workflow["workflow_path"]

        if job_name not in jobs:
            jobs[job_name] = {
                "uses": workflow_path,
                "secrets": "inherit",
            }

def merge_needs(existing, extra: list[str]):
    if existing is None:
        return list(dict.fromkeys(extra))
    if isinstance(existing, str):
        existing = [existing]
    merged = list(dict.fromkeys([*existing, *extra]))
    return merged

def add_needs_to_jobs(data: dict) -> int:
    jobs = data.setdefault("jobs", {})
    changed = 0
    for name, job in jobs.items():
        if name in GATES:
            continue  # don’t add needs to the gates themselves
        # Only add needs to real jobs (dict with steps/uses/runs-on)
        if not isinstance(job, dict):
            continue
        old = job.get("needs")
        new = merge_needs(old, GATES)
        if new != old:
            job["needs"] = new
            changed += 1
    return changed

def main() -> int:
    if not MAIN.exists():
        print(f"ERROR: {MAIN} not found. Run this from the repo root.", file=sys.stderr)
        return 2

    # Show discovered gate workflows
    if not GATE_WORKFLOWS:
        print("WARNING: No gate workflows discovered in src/plugins/*/(.github|templates/.github)/workflows/")
        print("Expected workflow files like commit-message.yml, root-hygiene.yml, etc.")
        return 1

    print(f"Discovered {len(GATE_WORKFLOWS)} gate workflows:")
    for gw in GATE_WORKFLOWS:
        print(f"  - {gw['job_name']} -> {gw['workflow_path']} (from {gw['source_file']})")

    # Backup once per run
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = MAIN.with_suffix(MAIN.suffix + f".bak.{ts}")
    shutil.copy2(MAIN, backup)
    print(f"Backup written: {backup}")

    loader, data = load_yaml(MAIN)

    # Ensure top-level scaffolding
    data.setdefault("name", "AI Guardrails (Full)")
    data.setdefault("on", {"pull_request": {"types": ["opened", "edited", "synchronize", "reopened"]}, "push": None})
    data.setdefault("permissions", {"contents": "read", "pull-requests": "read"})

    ensure_gate_calls(data)
    changed = add_needs_to_jobs(data)

    dump_yaml(MAIN, loader, data)
    print(f"Updated {MAIN} (needs added/merged on {changed} job(s)).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
